use {
    std::{
        marker::PhantomData,
        path::PathBuf,
        pin::Pin,
    },
    futures::future::{
        Future,
        FutureExt as _,
    },
    iced::{
        Element,
        widget::{
            Row,
            Text,
            button::{
                self,
                Button,
            },
            text_input::{
                self,
                TextInput,
            },
        },
    },
    itertools::Itertools as _,
    rfd::AsyncFileDialog,
};

pub(crate) trait Kind {
    type Data;

    fn parse(path_str: String) -> Option<Self::Data>;
    fn format(data: &Option<Self::Data>) -> String;
    fn pick() -> Pin<Box<dyn Future<Output = Option<Self::Data>> + Send>>;
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

    fn pick() -> Pin<Box<dyn Future<Output = Option<PathBuf>> + Send>> {
        Box::pin(AsyncFileDialog::new().pick_file()
            .map(|handle| handle.map(|handle| handle.path().to_owned())))
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

    fn pick() -> Pin<Box<dyn Future<Output = Option<Vec<PathBuf>>> + Send>> {
        Box::pin(AsyncFileDialog::new().pick_files()
            .map(|handles| handles.map(|handles| handles.into_iter().map(|handle| handle.path().to_owned()).collect())))
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

    fn pick() -> Pin<Box<dyn Future<Output = Option<PathBuf>> + Send>> {
        Box::pin(AsyncFileDialog::new().pick_folder()
            .map(|handle| handle.map(|handle| handle.path().to_owned())))
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

    fn pick() -> Pin<Box<dyn Future<Output = Option<PathBuf>> + Send>> {
        Box::pin(AsyncFileDialog::new().save_file()
            .map(|handle| handle.map(|handle| handle.path().to_owned())))
    }
}

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

    pub(crate) fn set(&mut self, path_str: String) {
        self.data = K::parse(path_str);
    }

    pub(crate) fn view(&mut self) -> Element<'_, M> {
        Row::new()
            .push(TextInput::new(&mut self.text_state, &self.placeholder, &K::format(&self.data), self.on_text_change).padding(5).style(crate::TextInputStyle))
            .push(Button::new(&mut self.browse_btn, Text::new("Browse…")).on_press(self.browse_msg.clone()))
            .spacing(16)
            .into()
    }
}
