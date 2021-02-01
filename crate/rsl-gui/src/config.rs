use {
    std::{
        fmt,
        io,
        sync::Arc,
    },
    serde::{
        Deserialize,
        Serialize,
    },
    tokio::fs,
    rsl::from_arc,
};

#[derive(Debug, Clone)]
pub(crate) enum Error {
    Io(Arc<io::Error>),
    Json(Arc<serde_json::Error>),
    #[cfg(feature = "self-update")]
    MissingHomeDir,
}

from_arc! {
    io::Error => Error, Io,
    serde_json::Error => Error, Json,
}

impl fmt::Display for Error {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Error::Io(e) => write!(f, "I/O error: {}", e),
            Error::Json(e) => write!(f, "JSON error: {}", e),
            #[cfg(feature = "self-update")]
            Error::MissingHomeDir => write!(f, "failed to locate home directory"),
        }
    }
}

#[derive(Debug, Default, Clone, Copy, Deserialize, Serialize)]
#[serde(deny_unknown_fields, rename_all = "camelCase")]
pub(crate) struct Config {
    pub(crate) auto_update_check: Option<bool>,
}

impl Config {
    pub(crate) async fn new() -> Config {
        let cache_dir = match rsl::cache_dir() { //TODO use config dir instead
            Some(cache_dir) => cache_dir,
            None => return Config::default(),
        };
        let config_path = cache_dir.join("config.json");
        let buf = match fs::read_to_string(config_path).await {
            Ok(buf) => buf,
            Err(_) => return Config::default(),
        };
        serde_json::from_str(&buf).unwrap_or_default() //TODO async-json
    }

    #[cfg(feature = "self-update")]
    pub(crate) async fn save(&self) -> Result<(), Error> {
        let cache_dir = rsl::cache_dir().ok_or(Error::MissingHomeDir)?; //TODO use config dir instead
        let config_path = cache_dir.join("config.json");
        let mut buf = serde_json::to_vec_pretty(self)?; //TODO async-json
        buf.push(b'\n');
        fs::create_dir_all(cache_dir).await?;
        fs::write(config_path, &buf).await?;
        Ok(())
    }
}
