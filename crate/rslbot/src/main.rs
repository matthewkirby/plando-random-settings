#![deny(rust_2018_idioms, unused, unused_crate_dependencies, unused_import_braces, unused_qualifications, warnings)]
#![forbid(unsafe_code)]

use {
    std::{
        collections::HashMap,
        convert::Infallible as Never,
        ffi::OsString,
        path::Path,
    },
    async_trait::async_trait,
    collect_mac::collect,
    glob::glob,
    itertools::Itertools as _,
    lazy_static::lazy_static,
    racetime::{
        Bot,
        handler::{
            Error,
            RaceHandler,
            RaceInfoPos,
            WsSink,
        },
        model::*,
    },
    serde::Deserialize,
    structopt::StructOpt,
    tokio::{
        fs,
        sync::Mutex,
    },
    rsl::{
        GenOptions,
        HashIcon,
        Preset,
        PresetOptions,
    },
};

const BASE_ROM_PATH: &str = "/usr/local/share/fenhl/rslbot/oot-ntscu-1.0.z64";
const BASE_URI: &str = "https://ootr.fenhl.net/seed/";
const TEMP_OUTPUT_DIR: &str = "/usr/local/share/fenhl/rslbot/output";
const WEB_OUTPUT_DIR: &str = "/var/www/ootr.fenhl.net/seed";

lazy_static! {
    static ref CLIENT: reqwest::Client = reqwest::Client::builder().user_agent(concat!("rslbot/", env!("CARGO_PKG_VERSION"))).build().expect("failed to build HTTP client");
    static ref GEN_LOCK: Mutex<()> = Mutex::default();
}

#[derive(Deserialize)]
struct SpoilerLog {
    file_hash: [HashIcon; 5],
}

struct RslHandler {
    data: RaceData,
    sender: WsSink,
    fpa: bool,
    locked: bool,
    seed_rolled: bool,
    spoiler_log: Option<OsString>,
    spoiler_sent: bool,
}

impl RslHandler {
    fn presets(&self) -> HashMap<&'static str, GenOptions> {
        collect![
            "league" => GenOptions::League,
            "solo" => GenOptions::Preset { preset: Preset::Solo, options: PresetOptions::default() },
            "coop" => GenOptions::Preset { preset: Preset::CoOp, options: PresetOptions::default() },
            //TODO multiworld (need to handle .zpfz files and second argument for world count)
        ]
    }

    fn race_in_progress(&self) -> bool {
        matches!(self.data.status.value, RaceStatusValue::Pending | RaceStatusValue::InProgress)
    }
}

#[async_trait]
impl RaceHandler for RslHandler {
    fn new(data: RaceData, sender: WsSink) -> Result<RslHandler, Error> {
        Ok(RslHandler {
            data, sender,
            fpa: false,
            locked: false,
            seed_rolled: false,
            spoiler_log: None,
            spoiler_sent: false,
        })
    }

    fn should_handle(race_data: &RaceData) -> Result<bool, Error> {
        Ok(
            race_data.goal.name == "Random settings league"
            && !race_data.goal.custom
            && !matches!(race_data.status.value, RaceStatusValue::Finished | RaceStatusValue::Cancelled)
        )
    }

    fn data(&mut self) -> Result<&mut RaceData, Error> { Ok(&mut self.data) }
    fn sender(&mut self) -> Result<&mut WsSink, Error> { Ok(&mut self.sender) }

    async fn command(&mut self, cmd: &str, args: Vec<&str>, is_moderator: bool, is_monitor: bool, message: &ChatMessage) -> Result<(), Error> {
        match (cmd, is_monitor) {
            ("lock", true) => {
                self.locked = true;
                self.send_message("Lock initiated. I will now only roll seeds for race monitors.").await?;
            }
            ("unlock", true) => if !self.race_in_progress() {
                self.locked = false;
                self.send_message("Lock released. Anyone may now roll a seed.").await?;
            },
            ("lock", false) | ("unlock", false) => self.send_message(&format!("Sorry {}, only race monitors can do that.", message.user.as_ref().map_or("friend", |user| &user.name))).await?,
            ("seed", _) => if !self.race_in_progress() { //TODO !spoilerseed
                if self.locked && !is_monitor {
                    self.send_message(&format!("Sorry {}, seed rolling is locked. Only race monitors may roll a seed for this race.", message.user.as_ref().map_or("friend", |user| &user.name))).await?;
                } else if self.seed_rolled && !is_moderator {
                    self.send_message("Well excuuuuuse me princess, but I already rolled a seed. Don't get greedy!").await?;
                } else {
                    let options = match &args[..] {
                        [] => GenOptions::default(),
                        [preset] => match self.presets().get(preset) {
                            Some(options) => options.clone(),
                            None => {
                                self.send_message(&format!("Sorry {}, I don't recognize that preset. Use !presets to see what is available.", message.user.as_ref().map_or("friend", |user| &user.name))).await?;
                                return Ok(())
                            }
                        },
                        [_, _, ..] => {
                            self.send_message("too many !roll arguments").await?;
                            return Ok(())
                        }
                    };
                    self.send_message("Rolling seed…").await?;
                    let lock = GEN_LOCK.lock().await; // multiple seeds being generated simultaneously may lead to errors such as the same settings being used for both
                    rsl::generate(&CLIENT, BASE_ROM_PATH, TEMP_OUTPUT_DIR, options).await.map_err(|e| format!("error generating seed: {}", e))?;
                    let mut patch_files = glob(&format!("{}/*.zpf", TEMP_OUTPUT_DIR)).map_err(|e| format!("error locating patch file: {}", e))?.fuse(); //TODO get filename from `generate` return value
                    let patch_file = match (patch_files.next(), patch_files.next()) {
                        (None, None) => {
                            self.send_message(&format!("Sorry {}, something went wrong while generating the seed. (Patch file not found)", message.user.as_ref().map_or("friend", |user| &user.name))).await?;
                            return Ok(())
                        }
                        (Some(patch_file), None) => patch_file.map_err(|e| format!("error locating patch file: {}", e))?,
                        (_, Some(_)) => {
                            self.send_message(&format!("Sorry {}, something went wrong while generating the seed. (Multiple patch files found)", message.user.as_ref().map_or("friend", |user| &user.name))).await?;
                            return Ok(())
                        }
                    };
                    let file_name = patch_file.file_name().expect("patch file path has no name");
                    let file_stem = patch_file.file_stem().expect("patch file path has no name");
                    let mut dist_file_name = file_stem.to_owned();
                    dist_file_name.push("_Distribution.json");
                    let mut spoiler_file_name = file_stem.to_owned();
                    spoiler_file_name.push("_Spoiler.json");
                    fs::rename(&patch_file, Path::new(WEB_OUTPUT_DIR).join(file_name)).await?;
                    fs::remove_file(Path::new(TEMP_OUTPUT_DIR).join(dist_file_name)).await?;
                    let seed_uri = format!("{}{}", BASE_URI, file_name.to_str().ok_or_else(|| Error::Other(format!("patch file name is not valid UTF-8")))?);
                    self.send_message(&format!("{}, here is your seed: {}", message.user.as_ref().map_or("Okay", |user| &user.name), seed_uri)).await?;
                    self.set_raceinfo(&seed_uri, RaceInfoPos::Prefix).await?;
                    let spoiler_log = fs::read_to_string(Path::new(TEMP_OUTPUT_DIR).join(&spoiler_file_name)).await?;
                    let spoiler_log = serde_json::from_str::<SpoilerLog>(&spoiler_log)?; //TODO async-json
                    self.send_message(&format!("The hash is {}.", spoiler_log.file_hash.iter().join(", "))).await?;
                    self.seed_rolled = true;
                    self.spoiler_log = Some(spoiler_file_name);
                    drop(lock);
                }
            },
            ("presets", _) => if !self.race_in_progress() {
                self.send_message("Available presets:").await?;
                for (name, _) in self.presets() {
                    if name == "league" {
                        self.send_message("league (default)").await?;
                    } else {
                        self.send_message(name).await?;
                    }
                }
            },
            ("fpa", _) => match &args[..] {
                [] => if self.fpa {
                    if self.race_in_progress() {
                        self.send_message(&format!("@everyone FPA has been invoked by {}.", message.user.as_ref().map_or("unknown", |user| &user.name))).await?;
                    } else {
                        self.send_message("FPA cannot be invoked before the race starts.").await?;
                    }
                } else {
                    self.send_message("Fair play agreement is not active. Race monitors may enable FPA for this race with !fpa on").await?;
                },
                ["on"] | ["off"] => if !is_monitor {
                    self.send_message(&format!("Sorry {}, only race monitors can do that.", message.user.as_ref().map_or("friend", |user| &user.name))).await?;
                } else if matches!(&args[..], ["on"]) {
                    if self.fpa {
                        self.send_message("Fair play agreement is already activated.").await?;
                    } else {
                        self.fpa = true;
                        self.send_message("Fair play agreement is now active. @entrants may use the !fpa command during the race to notify of a crash. Race monitors should enable notifications using the bell 🔔 icon below chat.").await?;
                    }
                } else {
                    if !self.fpa {
                        self.send_message("Fair play agreement is not active.").await?;
                    } else {
                        self.fpa = false;
                        self.send_message("Fair play agreement is now deactivated.").await?;
                    }
                },
                _ => self.send_message("unknown !fpa subcommand").await?,
            },
            (_, _) => {}
        }
        Ok(())
    }

    async fn begin(&mut self) -> Result<(), Error> {
        if let Some(info_suffix) = self.data.info.strip_prefix(BASE_URI) {
            self.spoiler_log = Some(format!("{}_Spoiler.json", info_suffix.split(".zpf").next().expect("split always yields at least one item")).into());
        } else if !self.race_in_progress() {
            self.send_message("Welcome to the OoTR Random Settings League! Create a seed with !seed <preset>").await?;
            self.send_message("If no preset is selected, default RSL weights will be used.").await?; //TODO !spoilerseed
            self.send_message("For a list of presets, use !presets").await?;
        }
        Ok(())
    }

    async fn race_data(&mut self, race_data: RaceData) -> Result<(), Error> {
        self.data = race_data;
        if matches!(self.data.status.value, RaceStatusValue::Finished | RaceStatusValue::Cancelled) {
            if !self.spoiler_sent {
                if let Some(ref spoiler_file_name) = self.spoiler_log {
                    fs::rename(Path::new(TEMP_OUTPUT_DIR).join(spoiler_file_name), Path::new(WEB_OUTPUT_DIR).join(spoiler_file_name)).await?;
                    let msg = format!("Here is the spoiler log: {}{}", BASE_URI, spoiler_file_name.to_str().ok_or_else(|| Error::Other(format!("spoiler file name is not valid UTF-8")))?);
                    self.send_message(&msg).await?;
                    self.spoiler_sent = true;
                }
            }
        }
        Ok(())
    }
}

#[derive(StructOpt)]
struct Args {}

#[wheel::main]
async fn main(Args {}: Args) -> Result<Never, racetime::bot::Error> {
    Bot::new(
        "ootr",
        "DGgAUaeDds43ctuoGMeFiOVUM7W5g2bkmlOKoKqo",
        &fs::read_to_string("assets/racetime-client-secret.txt").await?,
    ).await?.run::<RslHandler>().await
}
