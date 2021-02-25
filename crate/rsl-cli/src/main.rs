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
    },
};

ootr::uses!();

#[derive(StructOpt)]
struct Args {
    /// The path to the base OoT rom
    base_rom: PathBuf,
    /// The path where the patch file and spoiler log will be saved
    output_dir: PathBuf,
    /// A preset from which to generate the seed: `league-preview`, `ddr`, or `coop`. If not specified, a league seed will be generated.
    #[structopt(short, long)]
    preset: Option<Preset>,
    /// Use the `multiworld` preset and generate a seed for the number of worlds (players)
    #[structopt(short = "n", long)]
    world_count: Option<u8>,
    /// A custom weights JSON file from which to generate the seed
    #[structopt(short, long)]
    weights: Option<PathBuf>,
}

#[derive(From)]
enum Error {
    Gen(GenError),
    Io(io::Error),
    Json(serde_json::Error),
    PresetAndWorldCount,
    PresetAndWeights,
    WorldCountAndWeights,
    Reqwest(reqwest::Error),
    WorldCount,
}

impl fmt::Display for Error {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Error::Gen(e) => e.fmt(f),
            Error::Io(e) => write!(f, "I/O error: {}", e),
            Error::Json(e) => write!(f, "JSON error: {}", e),
            Error::PresetAndWorldCount => write!(f, "the `--preset` and `--world-count` options are mutually exclusive"),
            Error::PresetAndWeights => write!(f, "the `--preset` and `--weights` options are mutually exclusive"),
            Error::WorldCountAndWeights => write!(f, "the `--world-count` and `--weights` options are mutually exclusive"),
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
    let options = match (args.preset, args.world_count, args.weights) {
        (None, None, None) => GenOptions::League,
        (Some(preset), None, None) => GenOptions::Preset(preset),
        (None, Some(world_count), None) => if (2..=MAX_WORLDS).contains(&world_count) {
            GenOptions::Multiworld(world_count)
        } else {
            return Err(Error::WorldCount)
        },
        (None, None, Some(weights_path)) => {
            let file = if weights_path == Path::new("-") {
                Box::new(stdin()) as Box<dyn Read>
            } else {
                Box::new(File::open(weights_path)?)
            };
            GenOptions::Custom(serde_json::from_reader(file)?)
        },
        (Some(_), Some(_), _) => return Err(Error::PresetAndWorldCount),
        (Some(_), _, Some(_)) => return Err(Error::PresetAndWeights),
        (_, Some(_), Some(_)) => return Err(Error::WorldCountAndWeights),
    };
    rsl::generate(&client, args.base_rom, args.output_dir, options).await?;
    Ok(())
}
