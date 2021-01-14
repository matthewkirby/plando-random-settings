#![deny(rust_2018_idioms, unused, unused_import_braces, unused_qualifications, unused_crate_dependencies, warnings)]

#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use iced::{TextInput, text_input};

use {
    std::{
        fmt,
        io,
        sync::Arc,
    },
    enum_iterator::IntoEnumIterator,
    iced::{
        Application,
        Command,
        Element,
        Length,
        Settings,
        widget::{
            Checkbox,
            Column,
            Radio,
            Row,
            Space,
            Text,
            button::{
                self,
                Button,
            },
            slider::{
                self,
                Slider,
            },
        },
        window,
    },
    smart_default::SmartDefault,
    tokio::{
        fs::File,
        io::AsyncWriteExt,
        stream::StreamExt,
    },
    rsl::{
        GenError,
        GenOptions,
        Preset,
        PresetOptions,
        cache_dir,
        from_arc,
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
    #[cfg(windows)]
    InstallPython,
    PyInstallError(PyInstallError),
    SeedDone,
    SetWorldCount(u8),
    SetWorldCountStr(String),
    Tab(Tab),
    ToggleRandomStartingItems(bool),
    ToggleRslTricks(bool),
    ToggleStandardTricks(bool),
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

#[derive(Debug, SmartDefault, Clone, Copy, IntoEnumIterator, PartialEq, Eq)]
enum Tab {
    #[default]
    League,
    Solo,
    CoOp,
    Multiworld,
}

impl Tab {
    fn view(&self) -> Element<'_, Message> {
        Row::with_children(Tab::into_enum_iter().map(|tab|
            Radio::new(tab, tab.to_string(), Some(*self), Message::Tab).into()
        ).collect()).spacing(16).into()
    }
}

impl fmt::Display for Tab {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Tab::League => write!(f, "League"),
            Tab::Solo => write!(f, "Solo"),
            Tab::CoOp => write!(f, "Co-Op"),
            Tab::Multiworld => write!(f, "Multiworld"),
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
    PyNotFound {
        install_btn: button::State,
        reset_btn: button::State,
    },
    PyInstallError {
        e: PyInstallError,
        reset_btn: button::State,
    },
}

impl GenState {
    fn view(&mut self, disabled_reason: Option<&str>) -> Element<'_, Message> {
        match self {
            GenState::Idle(gen_btn) => if let Some(disabled_reason) = disabled_reason {
                Row::new()
                    .push(Button::new(gen_btn, Text::new("Generate Seed")))
                    .push(Text::new(format!("({})", disabled_reason)))
                    .spacing(16)
                    .into()
            } else {
                Button::new(gen_btn, Text::new("Generate Seed")).on_press(Message::Generate).into()
            },
            GenState::Generating => Text::new("Generating…").into(),
            GenState::Error { e, reset_btn } => Row::new()
                .push(Text::new(format!("error generating seed: {}", e)))
                .push(Button::new(reset_btn, Text::new("Dismiss")).on_press(Message::SeedDone))
                .spacing(16)
                .into(),
            GenState::PyNotFound { install_btn, reset_btn } => {
                let mut row = Row::new().push(Text::new("Python not found"));
                #[cfg(windows)] {
                    row = row.push(Button::new(install_btn, Text::new("Install")).on_press(Message::InstallPython));
                }
                row = row.push(Button::new(reset_btn, Text::new("Dismiss")).on_press(Message::SeedDone));
                row.spacing(16).into()
            }
            GenState::PyInstallError { e, reset_btn } => Row::new()
                .push(Text::new(format!("error installing Python: {}", e)))
                .push(Button::new(reset_btn, Text::new("Dismiss")).on_press(Message::SeedDone))
                .spacing(16)
                .into(),
        }
    }
}

#[derive(Debug, Clone)]
enum PyInstallError {
    InstallerExit,
    Io(Arc<io::Error>),
    MissingHomeDir,
    Reqwest(Arc<reqwest::Error>),
}

from_arc! {
    io::Error => PyInstallError, Io,
    reqwest::Error => PyInstallError, Reqwest,
}

impl fmt::Display for PyInstallError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            PyInstallError::InstallerExit => write!(f, "the installer exited with an error status"),
            PyInstallError::Io(e) => write!(f, "I/O error: {}", e),
            PyInstallError::MissingHomeDir => write!(f, "failed to locate home directory"),
            PyInstallError::Reqwest(e) => if let Some(url) = e.url() {
                write!(f, "HTTP error at {}: {}", url, e)
            } else {
                write!(f, "HTTP error: {}", e)
            },
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
    tab: Tab,
    #[default(PresetOptions { world_count: 2, ..PresetOptions::default() })]
    options: PresetOptions,
    worlds_slider: slider::State,
    worlds_text: text_input::State,
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
            Message::GenError(e) => self.gen = if let GenError::PyNotFound = e {
                GenState::PyNotFound {
                    install_btn: button::State::default(),
                    reset_btn: button::State::default(),
                }
            } else {
                GenState::Error {
                    e,
                    reset_btn: button::State::default(),
                }
            },
            Message::Generate => {
                self.gen = GenState::Generating;
                let base_rom = self.base_rom.data.as_ref().expect("generate button should be disabled if no base rom is given").clone();
                let output_dir = self.output_dir.data.as_ref().expect("generate button should be disabled if no output dir is given").clone();
                let options = match self.tab {
                    Tab::League => GenOptions::League,
                    Tab::Solo => GenOptions::Preset { preset: Preset::Solo, options: PresetOptions { world_count: 1, ..self.options } },
                    Tab::CoOp => GenOptions::Preset { preset: Preset::CoOp, options: PresetOptions { world_count: 1, ..self.options } },
                    Tab::Multiworld => GenOptions::Preset { preset: Preset::Multiworld, options: self.options },
                };
                return async move {
                    match rsl::generate(base_rom, output_dir, options).await {
                        Ok(()) => Message::SeedDone, //TODO button to open output dir
                        Err(e) => Message::GenError(e),
                    }
                }.into()
            }
            #[cfg(windows)] //TODO macOS/Linux support?
            Message::InstallPython => return async {
                match install_python().await {
                    Ok(()) => Message::Generate,
                    Err(e) => Message::PyInstallError(e),
                }
            }.into(),
            Message::PyInstallError(e) => self.gen = GenState::PyInstallError {
                e,
                reset_btn: button::State::default(),
            },
            Message::SeedDone => self.gen = GenState::default(),
            Message::SetWorldCount(world_count) => self.options.world_count = world_count,
            Message::SetWorldCountStr(world_count_str) => if let Ok(world_count) = world_count_str.parse() {
                if (2..=MAX_WORLDS).contains(&world_count) { self.options.world_count = world_count }
            },
            Message::Tab(tab) => self.tab = tab,
            Message::ToggleRandomStartingItems(checked) => self.options.random_starting_items = checked,
            Message::ToggleRslTricks(checked) => self.options.rsl_tricks = checked,
            Message::ToggleStandardTricks(checked) => self.options.standard_tricks = checked,
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
            .push(self.tab.view())
            .push(match self.tab {
                Tab::League => Element::from(Text::new("This will generate a seed with the Random Settings League's season 2 tournament weights. It will use version 5.2.117 R-1 of the randomizer. You can use the tabs above to switch to the latest version and use different weights.")), //TODO after s2, update description
                Tab::Solo | Tab::CoOp | Tab::Multiworld => {
                    let mut col = Column::new()
                        .push(Checkbox::new(self.options.standard_tricks, "Standard Tricks", Message::ToggleStandardTricks))
                        .push(Checkbox::new(self.options.rsl_tricks, "RSL Tricks", Message::ToggleRslTricks))
                        //TODO conditionals toggle?
                        .push(Checkbox::new(self.options.random_starting_items, "Randomize Starting Items", Message::ToggleRandomStartingItems));
                    if let Tab::Multiworld = self.tab {
                        col = col.push(Row::new()
                            .push(Text::new("Player Count:"))
                            .push(Slider::new(&mut self.worlds_slider, 2..=MAX_WORLDS, self.options.world_count, Message::SetWorldCount))
                            .push(TextInput::new(&mut self.worlds_text, "", &self.options.world_count.to_string(), Message::SetWorldCountStr).width(Length::Units(32)))
                            .spacing(16)
                        );
                    }
                    col.spacing(16).into()
                }
            })
            .push(Space::with_height(Length::Fill))
            .push(self.gen.view(disabled_reason))
            .spacing(16)
            .padding(16)
            .into()
    }
}

async fn check_for_updates() -> Message {
    Message::UpdateCheckComplete(false) //TODO
}

async fn install_python() -> Result<(), PyInstallError> {
    #[cfg(target_arch = "x86")] let arch_suffix = "";
    #[cfg(target_arch = "x86_64")] let arch_suffix = "-amd64";
    let response = reqwest::get(&format!("https://www.python.org/ftp/python/{0}/python-{0}{1}.exe", PY_VERSION, arch_suffix)).await?;
    let installer_path = cache_dir().ok_or(PyInstallError::MissingHomeDir)?.join("python-installer.exe");
    {
        let mut data = response.bytes_stream();
        let mut installer_file = File::create(&installer_path).await?;
        while let Some(chunk) = data.try_next().await? {
            installer_file.write_all(chunk.as_ref()).await?;
        }
    }
    if !tokio::process::Command::new(installer_path).arg("/passive").arg("PrependPath=1").status().await?.success() {
        return Err(PyInstallError::InstallerExit)
    }
    Ok(())
}

fn main() -> iced::Result {
    App::run(Settings {
        window: window::Settings {
            size: (512, 396),
            //TODO icon
            ..window::Settings::default()
        },
        ..Settings::default()
    })
}
