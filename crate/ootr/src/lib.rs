#![deny(rust_2018_idioms, unused, unused_import_braces, unused_qualifications, unused_crate_dependencies, warnings)]

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
    pyo3::prelude::*,
    quote::quote,
    zip::ZipArchive,
};

const REPO_NAME: &str = "OoT-Randomizer";
const LEAGUE_COMMIT_HASH: &str = "b670183e9aff520c20ac2ee65aa55e3740c5f4b4";
const LEAGUE_VERSION: &str = "5.2.117 R-1";

#[proc_macro]
pub fn uses(_: TokenStream) -> TokenStream {
    let py_version = Python::with_gil(|py| py.version().to_owned());
    TokenStream::from(quote! {
        const REPO_NAME: &str = #REPO_NAME;
        const LEAGUE_COMMIT_HASH: &str = #LEAGUE_COMMIT_HASH;
        const LEAGUE_VERSION: &str = #LEAGUE_VERSION;
        const MAX_WORLDS: u8 = 255; //TODO pull from SettingsList.py
        const PY_VERSION: &str = #py_version;
    })
}

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

fn starting_item_list(attr_name: &str) -> TokenStream {
    let items = Python::with_gil(|py| {
        PyResult::Ok(import(py, "StartingItems")?.get(attr_name)?.iter()?.map(|elt| elt.and_then(|elt| elt.extract())).collect::<PyResult<Vec<String>>>()?)
    }).expect("failed to read starting items from Python");
    quote!(vec![#(#items,)*]).into()
}

#[proc_macro] pub fn inventory(_: TokenStream) -> TokenStream { starting_item_list("inventory") }
#[proc_macro] pub fn songs(_: TokenStream) -> TokenStream { starting_item_list("songs") }
#[proc_macro] pub fn equipment(_: TokenStream) -> TokenStream { starting_item_list("equipment") }
