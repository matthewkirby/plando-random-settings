#![deny(rust_2018_idioms, unused, unused_import_braces, unused_qualifications, unused_crate_dependencies, warnings)]

use {
    std::{
        collections::{
            BTreeMap,
            BTreeSet,
        },
        convert::TryInto as _,
        fmt,
        io::{
            self,
            Cursor,
        },
        ops::{
            Add,
            AddAssign,
        },
        path::PathBuf,
        process::Stdio,
        str::FromStr,
        sync::Arc,
    },
    derive_more::From,
    directories::ProjectDirs,
    enum_iterator::IntoEnumIterator,
    rand::{
        distributions::WeightedError,
        prelude::*,
    },
    rand_distr::{
        Distribution as _,
        StandardGeometric,
    },
    serde::{
        Deserialize,
        Serialize,
    },
    serde_json::{
        Value as Json,
        json,
    },
    smart_default::SmartDefault,
    structopt::StructOpt,
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
};

ootr::uses!();

pub const NUM_RANDO_RANDO_TRIES: u8 = 20;
pub const NUM_TRIES_PER_SETTINGS: u8 = 3;

#[derive(Debug, Clone, Copy, IntoEnumIterator, Deserialize, Serialize)]
pub enum HashIcon {
    #[serde(rename = "Deku Stick")]
    DekuStick,
    #[serde(rename = "Deku Nut")]
    DekuNut,
    Bow,
    Slingshot,
    #[serde(rename = "Fairy Ocarina")]
    FairyOcarina,
    Bombchu,
    Longshot,
    Boomerang,
    #[serde(rename = "Lens of Truth")]
    LensOfTruth,
    Beans,
    #[serde(rename = "Megaton Hammer")]
    MegatonHammer,
    #[serde(rename = "Bottled Fish")]
    BottledFish,
    #[serde(rename = "Bottled Milk")]
    BottledMilk,
    #[serde(rename = "Mask of Truth")]
    MaskOfTruth,
    #[serde(rename = "SOLD OUT")]
    SoldOut,
    Cucco,
    Mushroom,
    Saw,
    Frog,
    #[serde(rename = "Master Sword")]
    MasterSword,
    #[serde(rename = "Mirror Shield")]
    MirrorShield,
    #[serde(rename = "Kokiri Tunic")]
    KokiriTunic,
    #[serde(rename = "Hover Boots")]
    HoverBoots,
    #[serde(rename = "Silver Gauntlets")]
    SilverGauntlets,
    #[serde(rename = "Gold Scale")]
    GoldScale,
    #[serde(rename = "Stone of Agony")]
    StoneOfAgony,
    #[serde(rename = "Skull Token")]
    SkullToken,
    #[serde(rename = "Heart Container")]
    HeartContainer,
    #[serde(rename = "Boss Key")]
    BossKey,
    Compass,
    Map,
    #[serde(rename = "Big Magic")]
    BigMagic,
}

impl HashIcon {
    pub fn random(rng: &mut impl Rng) -> HashIcon {
        HashIcon::into_enum_iter().choose(rng).expect("no HashIcons available")
    }
}

#[derive(Debug, Clone, Deserialize)]
#[serde(deny_unknown_fields, rename_all = "camelCase")]
pub struct Conditional {
    pub setting: String,
    pub conditions: Vec<Json>,
    pub values: BTreeMap<String, u64>,
}

#[derive(Debug, Clone, Copy, Deserialize)]
#[serde(rename_all = "camelCase")]
pub enum Distribution {
    Uniform,
    Geometric,
}

#[derive(Debug, Clone, Deserialize)]
#[serde(untagged, deny_unknown_fields, rename_all = "camelCase")]
pub enum WeightsRule {
    Simple {
        setting: String,
        values: BTreeMap<String, u64>,
    },
    Conditional {
        setting: String,
        conditionals: Vec<Conditional>,
        default: BTreeMap<String, u64>,
    },
    Range {
        setting: String,
        distribution: Distribution,
        min: u64,
        max: u64,
    },
}

impl WeightsRule {
    fn setting(&self) -> &str {
        match self {
            WeightsRule::Simple { setting, .. }
            | WeightsRule::Conditional { setting, .. }
            | WeightsRule::Range { setting, .. }
            => setting,
        }
    }
}

fn one() -> u8 { 1 }

#[derive(Debug, Clone, Deserialize)]
#[serde(deny_unknown_fields, rename_all = "camelCase")]
pub struct Weights {
    pub hash: [HashIcon; 2],
    #[serde(default = "one")]
    pub world_count: u8,
    pub disabled_locations: Option<Vec<String>>,
    pub allowed_tricks: Option<Vec<String>>,
    pub random_starting_items: bool,
    pub starting_items: Option<BTreeSet<String>>,
    pub starting_songs: Option<BTreeSet<String>>,
    pub starting_equipment: Option<BTreeSet<String>>,
    pub weights: Vec<WeightsRule>,
}

impl Weights {
    fn draw_choices_from_pool(rng: &mut impl Rng, pool: &[&str]) -> Json {
        let n = StandardGeometric.sample(rng).min(pool.len().try_into().expect("too many items")) as usize;
        json!(pool.choose_multiple(rng, n).collect::<Vec<_>>())
    }

    fn resolve_simple(rng: &mut impl Rng, values: &BTreeMap<String, u64>) -> Result<Json, WeightedError> {
        let keys = values.keys().collect::<Vec<_>>();
        let val_str = *keys.choose_weighted(rng, |&value| values.get(value).copied().unwrap_or_default())?;
        Ok(if val_str == "false" {
            json!(false)
        } else if val_str == "true" {
            json!(true)
        } else if let Ok(n) = val_str.parse::<u64>() {
            json!(n)
        } else {
            json!(val_str)
        })
    }

    pub fn gen(&self, rng: &mut impl Rng) -> Result<Plando, WeightedError> {
        let mut settings = BTreeMap::default();
        settings.insert(format!("world_count"), json!(self.world_count));
        if let Some(ref disabled_locations) = self.disabled_locations {
            settings.insert(format!("disabled_locations"), json!(disabled_locations));
        }
        if let Some(ref allowed_tricks) = self.allowed_tricks {
            settings.insert(format!("allowed_tricks"), json!(allowed_tricks));
        }
        if self.random_starting_items {
            settings.insert(format!("starting_items"), Weights::draw_choices_from_pool(rng, &ootr::inventory!()));
            settings.insert(format!("starting_songs"), Weights::draw_choices_from_pool(rng, &ootr::songs!()));
            settings.insert(format!("starting_equipment"), Weights::draw_choices_from_pool(rng, &ootr::equipment!()));
        }
        if let Some(ref starting_items) = self.starting_items { settings.entry(format!("starting_items")).or_default().as_array_mut().expect("starting_items setting was not an array").extend(starting_items.iter().map(|item| json!(item))) }
        if let Some(ref starting_songs) = self.starting_songs { settings.entry(format!("starting_songs")).or_default().as_array_mut().expect("starting_songs setting was not an array").extend(starting_songs.iter().map(|item| json!(item))) }
        if let Some(ref starting_equipment) = self.starting_equipment { settings.entry(format!("starting_equipment")).or_default().as_array_mut().expect("starting_equipment setting was not an array").extend(starting_equipment.iter().map(|item| json!(item))) }
        for rule in &self.weights {
            match rule {
                WeightsRule::Simple { setting, values } => {
                    settings.insert(setting.to_owned(), Weights::resolve_simple(rng, values)?);
                }
                WeightsRule::Conditional { setting, conditionals, default } => {
                    if let Some(Conditional { values, .. }) = conditionals.iter().find(|Conditional { setting, conditions, .. }| settings.get(setting).map_or(false, |value| conditions.contains(value))) {
                        settings.insert(setting.to_owned(), Weights::resolve_simple(rng, values)?);
                    } else {
                        settings.insert(setting.to_owned(), Weights::resolve_simple(rng, default)?);
                    }
                }
                WeightsRule::Range { distribution: Distribution::Uniform, setting, min, max } => {
                    settings.insert(setting.to_owned(), json!(rng.gen_range(*min..=*max)));
                }
                WeightsRule::Range { distribution: Distribution::Geometric, setting, min, max } => {
                    settings.insert(setting.to_owned(), json!(min + StandardGeometric.sample(rng).min(*max)));
                }
            }
        }
        Ok(Plando {
            settings,
            file_hash: [
                self.hash[0],
                self.hash[1],
                HashIcon::random(rng),
                HashIcon::random(rng),
                HashIcon::random(rng),
            ],
        })
    }
}

#[derive(Debug, Clone, Serialize)]
pub struct Plando {
    file_hash: [HashIcon; 5],
    settings: BTreeMap<String, Json>,
}

#[derive(Debug, Clone, Deserialize)]
#[serde(deny_unknown_fields, rename_all = "camelCase")]
pub struct Override {
    pub starting_items: Option<BTreeSet<String>>,
    pub starting_songs: Option<BTreeSet<String>>,
    pub starting_equipment: Option<BTreeSet<String>>,
    pub weights: Vec<WeightsRule>,
}

impl AddAssign<Override> for Weights {
    fn add_assign(&mut self, mut rhs: Override) {
        if let Some(starting_items) = rhs.starting_items { self.starting_items = Some(starting_items) }
        if let Some(starting_songs) = rhs.starting_songs { self.starting_songs = Some(starting_songs) }
        if let Some(starting_equipment) = rhs.starting_equipment { self.starting_equipment = Some(starting_equipment) }
        for rule in &mut self.weights {
            if let Some(new_rule_pos) = rhs.weights.iter().position(|new_rule| rule.setting() == new_rule.setting()) {
                *rule = rhs.weights.remove(new_rule_pos);
            }
        }
        self.weights.extend_from_slice(&rhs.weights);
    }
}

impl Add<Override> for Weights {
    type Output = Weights;

    fn add(mut self, rhs: Override) -> Weights {
        self += rhs;
        self
    }
}

#[derive(Debug, StructOpt, Clone, Copy, PartialEq, Eq)]
#[structopt(rename_all = "kebab")]
pub enum Preset {
    Solo,
    CoOp,
    Multiworld,
}

#[derive(Debug, Clone, Copy)]
pub struct PresetParseError;

impl fmt::Display for PresetParseError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "unknown preset")
    }
}

impl FromStr for Preset {
    type Err = PresetParseError;

    fn from_str(s: &str) -> Result<Preset, PresetParseError> {
        match s {
            "solo" => Ok(Preset::Solo),
            "coop" | "co-op" => Ok(Preset::CoOp),
            "multiworld" => Ok(Preset::Multiworld),
            _ => Err(PresetParseError),
        }
    }
}

#[derive(Debug, SmartDefault, Clone, Copy)]
pub struct PresetOptions {
    #[default = true]
    pub standard_tricks: bool,
    #[default = true]
    pub rsl_tricks: bool,
    #[default = true]
    pub random_starting_items: bool,
    #[default = 1]
    pub world_count: u8,
}

#[derive(Debug, SmartDefault, Clone)]
pub enum GenOptions {
    #[default]
    League,
    Preset {
        preset: Preset,
        options: PresetOptions,
    },
    Custom(Weights),
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
pub enum GenError {
    Io(Arc<io::Error>),
    Json(Arc<serde_json::Error>),
    MissingHomeDir,
    PyNotFound,
    PyVersionStatus,
    Reqwest(Arc<reqwest::Error>),
    TriesExceeded,
    #[from]
    Weights(WeightedError),
    Zip(Arc<ZipError>),
}

#[macro_export] macro_rules! from_arc {
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
            GenError::PyNotFound => write!(f, "Python not found"),
            GenError::PyVersionStatus => write!(f, "failed to check Python version"),
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

pub fn cache_dir() -> Option<PathBuf> {
    let project_dirs = ProjectDirs::from("net", "Fenhl", "RSL")?;
    Some(project_dirs.cache_dir().to_owned())
}

pub async fn generate(base_rom: impl Into<PathBuf>, output_dir: impl Into<PathBuf>, options: GenOptions) -> Result<(), GenError> {
    let cache_dir = cache_dir().ok_or(GenError::MissingHomeDir)?;
    let distribution_path = cache_dir.join("plando.json");
    // ensure the correct randomizer version is installed
    let rando_path = cache_dir.join(if let GenOptions::League = options { "ootr-league" } else { "ootr-latest" });
    let repo_ref = if let GenOptions::League = options { LEAGUE_COMMIT_HASH } else { "Dev-R" };
    if rando_path.join("version.py").exists() {
        let mut version_string = String::default();
        File::open(rando_path.join("version.py")).await?.read_to_string(&mut version_string).await?;
        if let GenOptions::League = options {
            if version_string.trim() != format!("__version__ = '{}'", LEAGUE_VERSION) {
                tokio::fs::remove_dir_all(&rando_path).await?;
            }
        } else {
            //TODO check and warn for outdated versions
        }
    }
    if !rando_path.exists() {
        let rando_download = reqwest::get(&format!("https://github.com/Roman971/{}/archive/{}.zip", REPO_NAME, repo_ref)).await?
            .bytes().await?;
        ZipArchive::new(Cursor::new(rando_download))?.extract(&cache_dir)?; //TODO async
        tokio::fs::rename(cache_dir.join(format!("{}-{}", REPO_NAME, repo_ref)), &rando_path).await?;
    }
    // write base rando settings to a file to be used as parameter later
    let buf = serde_json::to_vec_pretty(&RandoSettings::new(base_rom, &distribution_path, output_dir))?; //TODO async-json
    let settings_path = cache_dir.join("settings.json");
    File::create(&settings_path).await?.write_all(&buf).await?;
    // generate seed
    let weights = match options {
        GenOptions::League => serde_json::from_str(include_str!("../../../assets/weights/rsl.json"))?,
        GenOptions::Preset { preset, options } => {
            let mut weights = serde_json::from_str::<Weights>(include_str!("../../../assets/weights/rsl.json"))?;
            match preset {
                Preset::Solo => {}
                Preset::CoOp => weights += serde_json::from_str(include_str!("../../../assets/weights/override-coop.json"))?,
                Preset::Multiworld => weights += serde_json::from_str(include_str!("../../../assets/weights/override-multiworld.json"))?,
            }
            match (options.standard_tricks, options.rsl_tricks) {
                (true, true) => {}
                (true, false) => weights.allowed_tricks = Some(serde_json::from_str(include_str!("../../../assets/weights/tricks-standard.json"))?),
                (false, true) => weights.allowed_tricks = Some(serde_json::from_str(include_str!("../../../assets/weights/tricks-rsl.json"))?),
                (false, false) => weights.allowed_tricks = Some(Vec::default()),
            }
            if !options.random_starting_items { weights.random_starting_items = false }
            weights.world_count = options.world_count;
            weights
        }
        GenOptions::Custom(weights) => weights,
    };
    #[cfg(unix)] let python = "python3";
    #[cfg(all(windows, debug_assertions))] let python = "python";
    #[cfg(all(windows, not(debug_assertions)))] let python = "pythonw";
    match tokio::process::Command::new(python).arg("--version").stdout(Stdio::null()).current_dir(&rando_path).status().await {
        Ok(status) => if !status.success() { return Err(GenError::PyVersionStatus) },
        Err(e) => return Err(if e.kind() == io::ErrorKind::NotFound { GenError::PyNotFound } else { e.into() }),
    }
    for _ in 0..NUM_RANDO_RANDO_TRIES {
        let buf = serde_json::to_vec_pretty(&weights.gen(&mut thread_rng())?)?; //TODO async-json
        File::create(&distribution_path).await?.write_all(&buf).await?;
        for _ in 0..NUM_TRIES_PER_SETTINGS {
            if tokio::process::Command::new(python).arg("OoTRandomizer.py").arg("--settings").arg(&settings_path).current_dir(&rando_path).status().await?.success() { return Ok(()) }
        }
    }
    Err(GenError::TriesExceeded)
}
