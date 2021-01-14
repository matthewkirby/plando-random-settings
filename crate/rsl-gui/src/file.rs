use {
    std::{
        marker::PhantomData,
        path::PathBuf,
    },
    iced::{
        Element,
        widget::{
            Row,
            button,
            text_input::{
                self,
                TextInput,
            },
        },
    },
    itertools::Itertools as _,
    rfd::DialogOptions,
};
#[cfg(not(target_os = "macos"))] use iced::widget::{
    Button,
    Text,
};

pub(crate) trait Kind {
    type Data;

    fn parse(path_str: String) -> Option<Self::Data>;
    fn format(data: &Option<Self::Data>) -> String;
    fn pick<'a>(opt: impl Into<Option<DialogOptions<'a>>>) -> Option<Self::Data>;
}

pub(crate) enum File {}

impl Kind for File {
    type Data = PathBuf;

    fn parse(path_str: String) -> Option<PathBuf> {
        if path_str.is_empty() {
            None
        } else {
            Some(PathBuf::from(path_str))
        }
    }

    fn format(data: &Option<PathBuf>) -> String {
        data.as_ref().map(|data| format!("{}", data.display())).unwrap_or_default()
    }

    fn pick<'a>(opt: impl Into<Option<DialogOptions<'a>>>) -> Option<PathBuf> {
        rfd::pick_file(opt)
    }
}

pub(crate) enum Files {}

impl Kind for Files {
    type Data = Vec<PathBuf>;

    fn parse(path_str: String) -> Option<Vec<PathBuf>> {
        if path_str.is_empty() {
            None
        } else {
            Some(path_str.split(',').map(PathBuf::from).collect())
        }
    }

    fn format(data: &Option<Vec<PathBuf>>) -> String {
        data.iter().flatten().map(|path| path.display()).join(",")
    }

    fn pick<'a>(opt: impl Into<Option<DialogOptions<'a>>>) -> Option<Vec<PathBuf>> {
        rfd::pick_files(opt)
    }
}

pub(crate) enum Folder {}

impl Kind for Folder {
    type Data = PathBuf;

    fn parse(path_str: String) -> Option<PathBuf> {
        if path_str.is_empty() {
            None
        } else {
            Some(PathBuf::from(path_str))
        }
    }

    fn format(data: &Option<PathBuf>) -> String {
        data.as_ref().map(|data| format!("{}", data.display())).unwrap_or_default()
    }

    fn pick<'a>(opt: impl Into<Option<DialogOptions<'a>>>) -> Option<PathBuf> {
        rfd::pick_folder(opt)
    }
}

pub(crate) enum Save {}

impl Kind for Save {
    type Data = PathBuf;

    fn parse(path_str: String) -> Option<PathBuf> {
        if path_str.is_empty() {
            None
        } else {
            Some(PathBuf::from(path_str))
        }
    }

    fn format(data: &Option<PathBuf>) -> String {
        data.as_ref().map(|data| format!("{}", data.display())).unwrap_or_default()
    }

    fn pick<'a>(opt: impl Into<Option<DialogOptions<'a>>>) -> Option<PathBuf> {
        rfd::save_file(opt)
    }
}

#[cfg_attr(target_os = "macos", allow(unused))]
pub(crate) struct FilePicker<K: Kind, M: Clone + 'static> {
    _phantom: PhantomData<K>,
    pub(crate) data: Option<K::Data>,
    text_state: text_input::State,
    placeholder: String,
    on_text_change: fn(String) -> M,
    browse_btn: button::State,
    browse_msg: M,
}

impl<K: Kind, M: Clone + 'static> FilePicker<K, M> {
    pub(crate) fn new(placeholder: String, on_text_change: fn(String) -> M, browse_msg: M) -> Self {
        FilePicker {
            placeholder, on_text_change, browse_msg,
            _phantom: PhantomData::default(),
            data: None,
            text_state: text_input::State::default(),
            browse_btn: button::State::default(),
        }
    }

    pub(crate) fn browse(&mut self) {
        if let Some(data) = K::pick(None) { self.data = Some(data) } //TODO allow options?
    }

    pub(crate) fn set(&mut self, path_str: String) {
        self.data = K::parse(path_str);
    }

    pub(crate) fn view(&mut self) -> Element<'_, M> {
        let row = Row::new().push(TextInput::new(&mut self.text_state, &self.placeholder, &K::format(&self.data), self.on_text_change));
        // rfd currently hangs on macOS
        #[cfg(not(target_os = "macos"))] let row = row.push(Button::new(&mut self.browse_btn, Text::new("Browse…")).on_press(self.browse_msg.clone()));
        row.spacing(16).into()
    }
}
