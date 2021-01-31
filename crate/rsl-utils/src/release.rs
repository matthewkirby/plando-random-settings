#![deny(rust_2018_idioms, unused, unused_import_braces, unused_lifetimes, unused_qualifications, warnings)]
#![forbid(unsafe_code)]

use {
    std::{
        fmt,
        io,
        process::ExitStatus,
    },
    async_trait::async_trait,
    derive_more::From,
    structopt::StructOpt,
    tokio::{
        fs,
        process::Command,
    },
};
#[cfg(windows)] use {
    std::{
        cmp::Ordering::*,
        env,
        path::Path,
        process::Stdio,
        time::Duration,
    },
    dir_lock::DirLock,
    itertools::Itertools as _,
    semver::{
        SemVerError,
        Version,
    },
    serde::Deserialize,
    tempfile::NamedTempFile,
    crate::github::{
        Release,
        Repo,
    },
};

#[cfg(windows)] mod github;

#[derive(Debug, From)]
enum Error {
    CommandExit(&'static str, ExitStatus),
    #[cfg(windows)]
    DirLock(dir_lock::Error),
    #[cfg(windows)]
    EmptyReleaseNotes,
    #[cfg(windows)]
    InvalidHeaderValue(reqwest::header::InvalidHeaderValue),
    Io(io::Error),
    #[cfg(windows)]
    Json(serde_json::Error),
    #[cfg(windows)]
    MissingEnvar(&'static str),
    #[cfg(windows)]
    Reqwest(reqwest::Error),
    #[cfg(windows)]
    SameVersion,
    #[cfg(windows)]
    SemVer(SemVerError),
    #[cfg(windows)]
    VersionRegression,
}

impl fmt::Display for Error {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "{:?}", self)
    }
}

#[async_trait]
trait CommandOutputExt {
    async fn check(&mut self, name: &'static str, verbose: bool) -> Result<ExitStatus, Error>;
}

#[async_trait]
impl CommandOutputExt for Command {
    async fn check(&mut self, name: &'static str, verbose: bool) -> Result<ExitStatus, Error> {
        let status = if verbose {
            self.status().await?
        } else {
            self.output().await?.status
        };
        if status.success() {
            Ok(status)
        } else {
            Err(Error::CommandExit(name, status))
        }
    }
}

#[cfg(target_os = "macos")]
trait IoResultExt {
    fn exist_ok(self) -> Self;
}

#[cfg(target_os = "macos")]
impl IoResultExt for io::Result<()> {
    fn exist_ok(self) -> io::Result<()> {
        match self {
            Err(e) if e.kind() == io::ErrorKind::AlreadyExists => Ok(()),
            _ => self,
        }
    }
}

#[cfg(windows)] fn default_release_notes_editor() -> String { format!("C:\\Program Files\\Microsoft VS Code\\bin\\code.cmd") }
#[cfg(windows)] fn default_repo_owner() -> String { format!("matthewkirby") }
#[cfg(windows)] fn default_repo_name() -> String { format!("plando-random-settings") }

#[cfg(windows)]
#[derive(Deserialize)]
#[serde(rename_all = "camelCase")]
struct Config {
    github_token: String,
    mac_hostname: String,
    mac_repo_path: String,
    #[serde(default = "default_release_notes_editor")]
    release_notes_editor: String,
    #[serde(default = "default_repo_owner")]
    repo_owner: String,
    #[serde(default = "default_repo_name")]
    repo_name: String,
}

#[cfg(windows)]
impl Config {
    async fn open() -> Result<Config, Error> {
        let buf = fs::read_to_string("assets/release-config.json").await?;
        Ok(serde_json::from_str(&buf)?) //TODO async-json
    }
}

#[cfg(windows)]
async fn release_client(config: &Config) -> Result<reqwest::Client, Error> {
    let mut headers = reqwest::header::HeaderMap::new();
    headers.insert(reqwest::header::AUTHORIZATION, reqwest::header::HeaderValue::from_str(&format!("token {}", config.github_token))?);
    headers.insert(reqwest::header::USER_AGENT, reqwest::header::HeaderValue::from_static(concat!("rsl-release/", env!("CARGO_PKG_VERSION"))));
    Ok(reqwest::Client::builder().default_headers(headers).timeout(Duration::from_secs(600)).build()?)
}

#[cfg(windows)]
#[derive(Deserialize)]
struct Plist {
    #[serde(rename = "CFBundleShortVersionString")]
    bundle_short_version_string: Version,
}

#[cfg(windows)]
async fn check_cli_version(package: &str, version: &Version) {
    let cli_output = String::from_utf8(Command::new("cargo").arg("run").arg(format!("--package={}", package)).arg("--").arg("--version").stdout(Stdio::piped()).output().await.expect("failed to run CLI with --version").stdout).expect("CLI version output is invalid UTF-8");
    let (cli_name, cli_version) = cli_output.split(' ').collect_tuple().expect("no space in CLI version output");
    assert_eq!(cli_name, package);
    assert_eq!(*version, cli_version.parse().expect("failed to parse CLI version"));
}

#[cfg(windows)]
async fn version() -> Version {
    let version = Version::parse(env!("CARGO_PKG_VERSION")).expect("failed to parse current version");
    assert_eq!(version, plist::from_file::<_, Plist>("assets/macos/RSL.app/Contents/Info.plist").expect("failed to read plist for version check").bundle_short_version_string);
    assert_eq!(version, ootr::version!());
    assert_eq!(version, rsl::version());
    check_cli_version("rsl-cli", &version).await;
    check_cli_version("rsl-gui", &version).await;
    version
}

#[cfg(windows)]
async fn setup(config: &Config, verbose: bool) -> Result<(reqwest::Client, Repo), Error> {
    eprintln!("creating reqwest client");
    let client = release_client(config).await?;
    //TODO make sure working dir is clean and on default branch and up to date with remote and remote is up to date
    let repo = Repo::new(&config.repo_owner, &config.repo_name);
    eprintln!("checking version");
    if let Some(latest_release) = repo.latest_release(&client).await? {
        let remote_version = latest_release.version()?;
        match version().await.cmp(&remote_version) {
            Less => return Err(Error::VersionRegression),
            Equal => return Err(Error::SameVersion),
            Greater => {}
        }
    }
    eprintln!("waiting for Rust lock");
    let lock_dir = Path::new(&env::var_os("TEMP").ok_or(Error::MissingEnvar("TEMP"))?).join("syncbin-startup-rust.lock");
    let lock = DirLock::new(&lock_dir).await?;
    eprintln!("updating Rust for x86_64");
    Command::new("rustup").arg("update").arg("stable").check("rustup", verbose).await?;
    lock.drop_async().await?;
    Ok((client, repo))
}

#[cfg(windows)]
async fn build_windows(client: &reqwest::Client, repo: &Repo, release: &Release, verbose: bool) -> Result<(), Error> {
    eprintln!("building rsl-win64.exe");
    Command::new("cargo").arg("build").arg("--release").arg("--package=rsl-gui").check("cargo build --package=rsl-gui", verbose).await?;
    eprintln!("uploading rsl-win64.exe");
    repo.release_attach(client, release, "rsl-win64.exe", "application/vnd.microsoft.portable-executable", fs::read("target/release/rsl-gui.exe").await?).await?;
    Ok(())
}

#[cfg(windows)]
async fn build_macos(config: &Config, client: &reqwest::Client, repo: &Repo, release: &Release, verbose: bool) -> Result<(), Error> {
    eprintln!("updating repo on Mac");
    Command::new("ssh").arg(&config.mac_hostname).arg("zsh").arg("-c").arg(format!("'cd {} && git pull --ff-only'", shlex::quote(&config.mac_repo_path))).check("ssh", verbose).await?;
    eprintln!("running build script on Mac");
    Command::new("ssh").arg(&config.mac_hostname).arg(format!("{}/assets/release.sh", shlex::quote(&config.mac_repo_path))).arg(if verbose { "--verbose" } else { "" }).check("ssh", true).await?;
    eprintln!("downloading rsl-mac.dmg from Mac");
    Command::new("scp").arg(format!("{}:{}/assets/rsl-mac.dmg", config.mac_hostname, config.mac_repo_path)).arg("assets/rsl-mac.dmg").check("scp", verbose).await?;
    eprintln!("uploading rsl-mac.dmg");
    repo.release_attach(client, release, "rsl-mac.dmg", "application/x-apple-diskimage", fs::read("assets/rsl-mac.dmg").await?).await?;
    Ok(())
}

#[cfg(windows)]
async fn write_release_notes(config: &Config, verbose: bool) -> Result<String, Error> {
    eprintln!("editing release notes");
    let mut release_notes_file = tempfile::Builder::new()
        .prefix("rsl-release-notes")
        .suffix(".md")
        .tempfile()?;
    Command::new(&config.release_notes_editor).arg("--wait").arg(release_notes_file.path()).check("editor", verbose).await?;
    let mut buf = String::default();
    <NamedTempFile as io::Read>::read_to_string(&mut release_notes_file, &mut buf)?;
    if buf.is_empty() { return Err(Error::EmptyReleaseNotes) }
    Ok(buf)
}

#[derive(StructOpt)]
struct Args {
    #[cfg(windows)]
    /// Create the GitHub release as a draft
    #[structopt(long)]
    no_publish: bool,
    /// Show output of build commands
    #[structopt(short, long)]
    verbose: bool,
}

#[cfg(target_os = "macos")]
#[wheel::main]
async fn main(args: Args) -> Result<(), Error> {
    eprintln!("building rsl-mac.app for x86_64");
    Command::new("cargo").arg("build").arg("--release").arg("--target=x86_64-apple-darwin").arg("--package=rsl-gui").check("cargo", args.verbose).await?;
    eprintln!("building rsl-mac.app for aarch64");
    Command::new("cargo").arg("build").arg("--release").arg("--target=aarch64-apple-darwin").arg("--package=rsl-gui").check("cargo", args.verbose).await?;
    eprintln!("creating Universal macOS binary");
    fs::create_dir("assets/macos/RSL.app/Contents/MacOS").await.exist_ok()?;
    Command::new("lipo").arg("-create").arg("target/aarch64-apple-darwin/release/rsl-gui").arg("target/x86_64-apple-darwin/release/rsl-gui").arg("-output").arg("assets/macos/RSL.app/Contents/MacOS/rsl-gui").check("lipo", args.verbose).await?;
    eprintln!("packing rsl-mac.dmg");
    Command::new("hdiutil").arg("create").arg("assets/rsl-mac.dmg").arg("-volname").arg("RSL").arg("-srcfolder").arg("assets/macos").arg("-ov").check("hdiutil", args.verbose).await?;
    Ok(())
}

#[cfg(windows)]
#[wheel::main]
async fn main(args: Args) -> Result<(), Error> {
    let config = Config::open().await?;
    let ((client, repo), release_notes) = if args.verbose {
        (
            setup(&config, args.verbose).await?,
            write_release_notes(&config, args.verbose).await?,
        )
    } else {
        let (setup_res, release_notes) = tokio::join!(
            setup(&config, args.verbose),
            write_release_notes(&config, args.verbose),
        );
        (setup_res?, release_notes?)
    };
    eprintln!("creating release");
    let release = repo.create_release(&client, version().await.to_string(), format!("v{}", version().await), release_notes).await?;
    if args.verbose {
        build_windows(&client, &repo, &release, args.verbose).await?;
        build_macos(&config, &client, &repo, &release, args.verbose).await?;
    } else {
        let (build_windows_res, build_macos_res) = tokio::join!(
            build_windows(&client, &repo, &release, args.verbose),
            build_macos(&config, &client, &repo, &release, args.verbose),
        );
        let () = build_windows_res?;
        let () = build_macos_res?;
    }
    if !args.no_publish {
        eprintln!("publishing release");
        repo.publish_release(&client, release).await?;
    }
    Ok(())
}
