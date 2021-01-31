#![deny(rust_2018_idioms, unused, unused_crate_dependencies, unused_import_braces, unused_qualifications, warnings)]
#![forbid(unsafe_code)]

use {
    std::{
        fs::{
            self,
            File,
        },
        io::{
            Cursor,
            prelude::*,
        },
    },
    directories::ProjectDirs,
    proc_macro::TokenStream,
    pyo3::{
        prelude::*,
        types::PyDict,
    },
    quote::quote,
    zip::ZipArchive,
};

const REPO_NAME: &str = "OoT-Randomizer";
const LEAGUE_COMMIT_HASH: &str = "b670183e9aff520c20ac2ee65aa55e3740c5f4b4";
const LEAGUE_VERSION: &str = "5.2.117 R-1";

fn import<'p>(py: Python<'p>, module: &str) -> PyResult<&'p PyModule> {
    let project_dirs = ProjectDirs::from("net", "Fenhl", "RSL").expect("missing home directory");
    let cache_dir = project_dirs.cache_dir();
    // ensure the correct randomizer version is installed
    let rando_path = cache_dir.join("ootr-league");
    if rando_path.join("version.py").exists() {
        let mut version_string = String::default();
        File::open(rando_path.join("version.py"))?.read_to_string(&mut version_string)?;
        if version_string.trim() != format!("__version__ = '{}'", LEAGUE_VERSION) {
            // wrong version for RSL season 2
            fs::remove_dir_all(&rando_path)?;
        }
    }
    if !rando_path.exists() {
        let rando_download = reqwest::blocking::get(&format!("https://github.com/Roman971/{}/archive/{}.zip", REPO_NAME, LEAGUE_COMMIT_HASH))
            .expect("failed to download OoTR")
            .error_for_status()
            .expect("failed to download OoTR")
            .bytes()
            .expect("failed to download OoTR");
        ZipArchive::new(Cursor::new(rando_download)).expect("failed to extract OoTR repo").extract(&cache_dir).expect("failed to extract OoTR repo");
        fs::rename(cache_dir.join(format!("{}-{}", REPO_NAME, LEAGUE_COMMIT_HASH)), &rando_path)?;
    }
    let sys = py.import("sys")?;
    sys.get("path")?.call_method1("append", (rando_path.display().to_string(),))?;
    py.import(module)
}

fn starting_item_list(attr_name: &str) -> proc_macro2::TokenStream {
    let items = Python::with_gil(|py| {
        PyResult::Ok(import(py, "StartingItems")?.get(attr_name)?.iter()?.map(|elt| elt.and_then(|elt| elt.extract())).collect::<PyResult<Vec<String>>>()?)
    }).expect("failed to read starting items from Python");
    quote!(&[#(#items,)*]).into()
}

#[proc_macro]
pub fn uses(_: TokenStream) -> TokenStream {
    let (py_version, locations, tricks) = Python::with_gil(|py| {
        let v = py.version_info();
        let location_table = import(py, "Location")?.get("location_table")?;
        let mut locations = Vec::default();
        for loc in location_table.call_method0("items")?.iter()? {
            let (loc_name, (_, _, _, _, categories)) = loc?.extract::<(String, (&PyAny, &PyAny, &PyAny, &PyAny, Option<&PyAny>))>()?;
            if categories.is_some() {
                locations.push(loc_name);
            }
        }
        let logic_tricks = import(py, "SettingsList")?.get("logic_tricks")?;
        let mut tricks = Vec::default();
        for trick in logic_tricks.call_method0("items")?.iter()? {
            let (_ /*display_name*/, data) = trick?.extract::<(String, &PyDict)>()?;
            let name = data.get_item("name").expect("missing trick name").extract::<String>()?;
            tricks.push(name);
        }
        PyResult::Ok((
            format!("{}.{}.{}", v.major, v.minor, v.patch),
            locations,
            tricks,
        ))
    }).expect("failed to get data from Python");
    let inventory = starting_item_list("inventory");
    let songs = starting_item_list("songs");
    let equipment = starting_item_list("equipment");
    TokenStream::from(quote! {
        const REPO_NAME: &str = #REPO_NAME;
        const LEAGUE_COMMIT_HASH: &str = #LEAGUE_COMMIT_HASH;
        const LEAGUE_VERSION: &str = #LEAGUE_VERSION;
        const MAX_WORLDS: u8 = 255; //TODO pull from SettingsList.py
        const LOCATIONS: &[&str] = &[#(#locations,)*];
        const TRICKS: &[&str] = &[#(#tricks,)*];
        const PY_VERSION: &str = #py_version;
        const INVENTORY: &[&str] = #inventory;
        const SONGS: &[&str] = #songs;
        const EQUIPMENT: &[&str] = #equipment;
    })
}

#[proc_macro]
pub fn version(_: TokenStream) -> TokenStream {
    let version = env!("CARGO_PKG_VERSION");
    TokenStream::from(quote! {
        ::semver::Version::parse(#version).expect("failed to parse current version")
    })
}
