#![deny(rust_2018_idioms, unused, unused_crate_dependencies, unused_import_braces, unused_qualifications, warnings)]
#![forbid(unsafe_code)]

use {
    std::{
        fmt,
        fs::File,
        io::{
            self,
            Read,
            stdin,
        },
        path::{
            Path,
            PathBuf,
        },
    },
    derive_more::From,
    structopt::StructOpt,
    rsl::{
        GenError,
        GenOptions,
        Preset,
        PresetOptions,
    },
};

ootr::uses!();

#[derive(StructOpt)]
struct Args {
    /// The path to the base OoT rom
    base_rom: PathBuf,
    /// The path where the patch file and spoiler log will be saved
    output_dir: PathBuf,
    /// A preset from which to generate the seed: `solo`, `co-op`, or `multiworld`. If not specified, a league seed will be generated.
    #[structopt(short, long)]
    preset: Option<Preset>,
    /// A custom weights JSON file from which to generate the seed
    #[structopt(short, long)]
    weights: Option<PathBuf>,
    /// When using a preset, logically disable Standard tricks. No effect on league or custom weights.
    #[structopt(long)]
    no_standard_tricks: bool,
    /// When using a preset, logically disable RSL tricks. No effect on league or custom weights.
    #[structopt(long)]
    no_rsl_tricks: bool,
    /// When using a preset, don't add random starting items. No effect on league or custom weights.
    #[structopt(long)]
    no_random_starting_items: bool,
    /// When using the `multiworld` preset, the number of worlds (players)
    #[structopt(short = "n", long, default_value = "1")]
    world_count: u8,
}

#[derive(From)]
enum Error {
    Gen(GenError),
    Io(io::Error),
    Json(serde_json::Error),
    PresetAndWeights,
    Reqwest(reqwest::Error),
    WorldCount,
}

impl fmt::Display for Error {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Error::Gen(e) => e.fmt(f),
            Error::Io(e) => write!(f, "I/O error: {}", e),
            Error::Json(e) => write!(f, "JSON error: {}", e),
            Error::PresetAndWeights => write!(f, "the `--preset` and `--weights` options are mutually exclusive"),
            Error::Reqwest(e) => if let Some(url) = e.url() {
                write!(f, "HTTP error at {}: {}", url, e)
            } else {
                write!(f, "HTTP error: {}", e)
            },
            Error::WorldCount => write!(f, "`--world-count` must be at least 1 and at most 255"),
        }
    }
}

#[wheel::main]
async fn main(args: Args) -> Result<(), Error> {
    let client = reqwest::Client::builder()
        .user_agent(concat!("rsl/", env!("CARGO_PKG_VERSION")))
        .build()?;
    let options = match (args.preset, args.weights) {
        (Some(_), Some(_)) => return Err(Error::PresetAndWeights),
        (Some(preset), None) => GenOptions::Preset {
            preset,
            options: PresetOptions {
                standard_tricks: !args.no_standard_tricks,
                rsl_tricks: !args.no_rsl_tricks,
                random_starting_items: !args.no_random_starting_items,
                world_count: if (1..=MAX_WORLDS).contains(&args.world_count) { args.world_count } else { return Err(Error::WorldCount) },
            },
        },
        (None, Some(weights_path)) => {
            let file = if weights_path == Path::new("-") {
                Box::new(stdin()) as Box<dyn Read>
            } else {
                Box::new(File::open(weights_path)?)
            };
            GenOptions::Custom(serde_json::from_reader(file)?)
        }
        (None, None) => GenOptions::League,
    };
    rsl::generate(&client, args.base_rom, args.output_dir, options).await?;
    Ok(())
}
