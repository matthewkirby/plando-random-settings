use {
    proc_macro::TokenStream,
    pyo3::prelude::*,
    quote::quote,
};

fn import<'p>(py: Python<'p>, module: &str) -> PyResult<&'p PyModule> {
    let sys = py.import("sys")?;
    sys.get("path")?.call_method1("append", (format!("C:\\Users\\Fenhl\\git\\github.com\\fenhl\\OoT-Randomizer\\stage"),))?; //TODO refresh and use cached rando like in GUI
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
