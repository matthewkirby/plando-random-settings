use {
    std::{
        collections::{
            BTreeMap,
            BTreeSet,
        },
        convert::TryInto as _,
        ops::{
            Add,
            AddAssign,
        },
    },
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
};

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
    setting: String,
    conditions: Vec<Json>,
    values: BTreeMap<String, u64>,
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

#[derive(Debug, Clone, Deserialize)]
#[serde(deny_unknown_fields, rename_all = "camelCase")]
pub struct Weights {
    pub hash: [HashIcon; 2],
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
