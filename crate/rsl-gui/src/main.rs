#![deny(rust_2018_idioms, unused, unused_import_braces, unused_qualifications, warnings)]

#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use {
    std::{
        fmt,
        io::{
            self,
            Cursor,
        },
        path::PathBuf,
        sync::Arc,
    },
    derive_more::From,
    directories::ProjectDirs,
    iced::{
        Application,
        Command,
        Element,
        Settings,
        widget::{
            Column,
            Row,
            Text,
            button::{
                self,
                Button,
            },
        },
    },
    rand::{
        distributions::WeightedError,
        prelude::*,
    },
    serde::Serialize,
    smart_default::SmartDefault,
    tokio::{
        fs::File,
        io::{
            AsyncReadExt,
            AsyncWriteExt,
        },
    },
    zip::{
        ZipArchive,
        result::ZipError,
    },
    rsl::{
        NUM_RANDO_RANDO_TRIES,
        NUM_TRIES_PER_SETTINGS,
        Weights,
    },
    crate::file::FilePicker,
};

mod file;

ootr::uses!();

#[derive(Debug, Clone)]
enum Message {
    BrowseBaseRom,
    BrowseOutputDir,
    ChangeBaseRom(String),
    ChangeOutputDir(String),
    GenError(GenError),
    Generate,
    SeedDone,
    UpdateCheckComplete(bool),
}

#[derive(SmartDefault)]
enum UpdateCheckState {
    #[default]
    Checking,
    UpdateAvailable,
    NoUpdateAvailable,
}

impl fmt::Display for UpdateCheckState {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            UpdateCheckState::Checking => write!(f, "checking for updates…"),
            UpdateCheckState::UpdateAvailable => write!(f, "update available"),
            UpdateCheckState::NoUpdateAvailable => write!(f, "up to date"),
        }
    }
}

#[derive(SmartDefault)]
enum GenState {
    #[default]
    Idle(button::State),
    Generating,
    Error {
        e: GenError,
        reset_btn: button::State,
    },
}

impl GenState {
    fn view(&mut self, disabled_reason: Option<&str>) -> Element<'_, Message> {
        match self {
            GenState::Idle(gen_btn) => if let Some(disabled_reason) = disabled_reason {
                Row::new().push(Button::new(gen_btn, Text::new("Generate Seed"))).push(Text::new(format!(" ({})", disabled_reason))).into()
            } else {
                Button::new(gen_btn, Text::new("Generate Seed")).on_press(Message::Generate).into()
            },
            GenState::Generating => Text::new("Generating…").into(),
            GenState::Error { e, reset_btn } => Row::new()
                .push(Text::new(format!("error generating seed: {}", e)))
                .push(Button::new(reset_btn, Text::new("Dismiss")).on_press(Message::SeedDone))
                .into(),
        }
    }
}

#[derive(SmartDefault)]
struct App {
    update_check: UpdateCheckState,
    #[default(FilePicker::new(format!("Base ROM"), Message::ChangeBaseRom, Message::BrowseBaseRom))]
    base_rom: FilePicker<file::File, Message>,
    #[default(FilePicker::new(format!("Output Directory"), Message::ChangeOutputDir, Message::BrowseOutputDir))]
    output_dir: FilePicker<file::Folder, Message>,
    gen: GenState,
}

impl Application for App {
    type Executor = iced::executor::Default;
    type Message = Message;
    type Flags = ();

    fn new((): ()) -> (App, Command<Message>) { (App::default(), check_for_updates().into()) }
    fn title(&self) -> String { format!("Ocarina of Time Randomizer — Random Settings Generator") }

    fn update(&mut self, msg: Message) -> Command<Message> {
        match msg {
            Message::BrowseBaseRom => self.base_rom.browse(),
            Message::BrowseOutputDir => self.output_dir.browse(),
            Message::ChangeBaseRom(path_str) => self.base_rom.set(path_str),
            Message::ChangeOutputDir(path_str) => self.output_dir.set(path_str),
            Message::GenError(e) => self.gen = GenState::Error {
                e,
                reset_btn: button::State::default(),
            },
            Message::Generate => {
                self.gen = GenState::Generating;
                let base_rom = self.base_rom.data.as_ref().expect("generate button should be disabled if no base rom is given").clone();
                let output_dir = self.output_dir.data.as_ref().expect("generate button should be disabled if no output dir is given").clone();
                return async move {
                    match generate(base_rom, output_dir).await {
                        Ok(()) => Message::SeedDone,
                        Err(e) => Message::GenError(e),
                    }
                }.into()
            }
            Message::SeedDone => self.gen = GenState::default(),
            Message::UpdateCheckComplete(true) => self.update_check = UpdateCheckState::UpdateAvailable,
            Message::UpdateCheckComplete(false) => self.update_check = UpdateCheckState::NoUpdateAvailable,
        }
        Command::none()
    }

    fn view(&mut self) -> Element<'_, Message> {
        let disabled_reason = if self.base_rom.data.is_none() {
            Some("base ROM is required")
        } else if self.output_dir.data.is_none() {
            Some("output directory is required")
        } else {
            None
        };
        Column::new()
            .push(Text::new(format!("version {} — {}", env!("CARGO_PKG_VERSION"), self.update_check)))
            .push(self.base_rom.view())
            .push(self.output_dir.view())
            //TODO options
            .push(self.gen.view(disabled_reason))
            .into()
    }
}

async fn check_for_updates() -> Message {
    Message::UpdateCheckComplete(false) //TODO
}

#[derive(Serialize)]
enum CompressRom {
    Patch,
}

#[derive(Serialize)]
struct RandoSettings {
    rom: PathBuf,
    output_dir: PathBuf,
    enable_distribution_file: bool,
    distribution_file: PathBuf,
    create_spoiler: bool,
    create_cosmetics_log: bool,
    compress_rom: CompressRom,
}

impl RandoSettings {
    fn new(rom_path: impl Into<PathBuf>, distribution_path: impl Into<PathBuf>, output_dir: impl Into<PathBuf>) -> RandoSettings {
        RandoSettings {
            rom: rom_path.into(),
            output_dir: output_dir.into(),
            enable_distribution_file: true,
            distribution_file: distribution_path.into(),
            create_spoiler: true,
            create_cosmetics_log: false,
            compress_rom: CompressRom::Patch,
        }
    }
}

#[derive(Debug, From, Clone)]
enum GenError {
    Io(Arc<io::Error>),
    Json(Arc<serde_json::Error>),
    MissingHomeDir,
    Reqwest(Arc<reqwest::Error>),
    TriesExceeded,
    #[from]
    Weights(WeightedError),
    Zip(Arc<ZipError>),
}

macro_rules! from_arc {
    ($($from:ty => $to:ty, $variant:ident,)*) => {
        $(
            impl From<$from> for $to {
                fn from(e: $from) -> $to {
                    <$to>::$variant(Arc::new(e))
                }
            }
        )*
    };
}

from_arc! {
    io::Error => GenError, Io,
    serde_json::Error => GenError, Json,
    reqwest::Error => GenError, Reqwest,
    ZipError => GenError, Zip,
}

impl fmt::Display for GenError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            GenError::Io(e) => write!(f, "I/O error: {}", e),
            GenError::Json(e) => write!(f, "JSON error: {}", e),
            GenError::MissingHomeDir => write!(f, "failed to locate home directory"),
            GenError::Reqwest(e) => if let Some(url) = e.url() {
                write!(f, "HTTP error at {}: {}", url, e)
            } else {
                write!(f, "HTTP error: {}", e)
            },
            GenError::TriesExceeded => write!(f, "{} settings each tried {} times, all failed", NUM_RANDO_RANDO_TRIES, NUM_TRIES_PER_SETTINGS),
            GenError::Weights(e) => e.fmt(f),
            GenError::Zip(e) => e.fmt(f),
        }
    }
}

async fn generate(base_rom: impl Into<PathBuf>, output_dir: impl Into<PathBuf>) -> Result<(), GenError> {
    let project_dirs = ProjectDirs::from("net", "Fenhl", "RSL").ok_or(GenError::MissingHomeDir)?;
    let cache_dir = project_dirs.cache_dir();
    let distribution_path = cache_dir.join("plando.json");
    // ensure the correct randomizer version is installed
    let rando_path = cache_dir.join("ootr-rsl");
    if rando_path.join("version.py").exists() {
        let mut version_string = String::default();
        File::open(rando_path.join("version.py")).await?.read_to_string(&mut version_string).await?;
        if version_string != "__version = '5.2.117 R-1'" {
            // wrong version for RSL season 2
            //TODO only do this version check when generating a League seed, only warn for outdated versions otherwise
            tokio::fs::remove_dir_all(&rando_path).await?;
        }
    }
    if !rando_path.exists() {
        let rando_download = reqwest::get(&format!("https://github.com/Roman971/{}/archive/{}.zip", REPO_NAME, LEAGUE_COMMIT_HASH)).await? //TODO replace with Dev-R.zip if not generating a League seed
            .bytes().await?;
        ZipArchive::new(Cursor::new(rando_download))?.extract(&cache_dir)?; //TODO async
        tokio::fs::rename(cache_dir.join(format!("{}-{}", REPO_NAME, LEAGUE_COMMIT_HASH)), &rando_path).await?; //TODO replace with OoT-Randomizer-Dev-R if not generating a League seed
    }
    // write base rando settings to a file to be used as parameter later
    let buf = serde_json::to_vec_pretty(&RandoSettings::new(base_rom, &distribution_path, output_dir))?; //TODO async-json
    let settings_path = cache_dir.join("settings.json");
    File::create(&settings_path).await?.write_all(&buf).await?;
    // generate seed
    let weights = serde_json::from_str::<Weights>(include_str!("../../../assets/weights/rsl.json"))?; //TODO allow other presets or custom weights
    #[cfg(unix)] let python = "python3";
    #[cfg(windows)] let python = "py";
    for _ in 0..NUM_RANDO_RANDO_TRIES {
        let buf = serde_json::to_vec_pretty(&weights.gen(&mut thread_rng())?)?; //TODO async-json
        File::create(&distribution_path).await?.write_all(&buf).await?;
        for _ in 0..NUM_TRIES_PER_SETTINGS {
            if tokio::process::Command::new(python).arg("OoTRandomizer.py").arg("--settings").arg(&settings_path).current_dir(&rando_path).status().await?.success() { return Ok(()) }
        }
    }
    Err(GenError::TriesExceeded)
}

fn main() -> iced::Result {
    App::run(Settings::default())
}
