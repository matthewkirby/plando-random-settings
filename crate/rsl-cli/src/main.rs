#![deny(rust_2018_idioms, unused, unused_crate_dependencies, unused_import_braces, unused_qualifications, warnings)]
#![forbid(unsafe_code)]

use {
    std::{
        fmt,
        fs::File,
        io,
        path::PathBuf,
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
    base_rom: PathBuf,
    output_dir: PathBuf,
    #[structopt(short, long)]
    preset: Option<Preset>,
    #[structopt(short, long)]
    weights: Option<PathBuf>,
    #[structopt(long)]
    no_standard_tricks: bool,
    #[structopt(long)]
    no_rsl_tricks: bool,
    #[structopt(long)]
    no_random_starting_items: bool,
    #[structopt(short = "n", long, default_value = "1")]
    world_count: u8,
}

#[derive(From)]
enum Error {
    Gen(GenError),
    Io(io::Error),
    Json(serde_json::Error),
    PresetAndWeights,
    WorldCount,
}

impl fmt::Display for Error {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Error::Gen(e) => e.fmt(f),
            Error::Io(e) => write!(f, "I/O error: {}", e),
            Error::Json(e) => write!(f, "JSON error: {}", e),
            Error::PresetAndWeights => write!(f, "the `--preset` and `--weights` options are mutually exclusive"),
            Error::WorldCount => write!(f, "`--world-count` must be at least 1 and at most 255"),
        }
    }
}

#[wheel::main]
async fn main(args: Args) -> Result<(), Error> {
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
        (None, Some(weights_path)) => GenOptions::Custom(serde_json::from_reader(File::open(weights_path)?)?),
        (None, None) => GenOptions::League,
    };
    rsl::generate(args.base_rom, args.output_dir, options).await?;
    Ok(())
}
