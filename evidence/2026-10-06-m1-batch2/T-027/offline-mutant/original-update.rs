//! Local version and installation metadata. Muster does not self-update.
use std::{
    env,
    path::{Path, PathBuf},
};
const MISE_INSTALLS_DIR_ENV: &str = "MISE_INSTALLS_DIR";
pub(crate) const WINDOWS_INSTALLER: &str = include_str!("../distribution/install.ps1");

/// Parsed semver version for comparison.
#[derive(Debug, Clone, PartialEq, Eq, PartialOrd, Ord)]
pub struct Version {
    pub major: u32,
    pub minor: u32,
    pub patch: u32,
}

impl Version {
    pub fn parse(s: &str) -> Option<Self> {
        let s = s.strip_prefix('v').unwrap_or(s);
        let parts: Vec<&str> = s.split('.').collect();
        if parts.len() != 3 {
            return None;
        }
        Some(Self {
            major: parts[0].parse().ok()?,
            minor: parts[1].parse().ok()?,
            patch: parts[2].parse().ok()?,
        })
    }

    pub fn current() -> Self {
        Self::parse(crate::build_info::BASE_VERSION).expect("invalid CARGO_PKG_VERSION")
    }
}

impl std::fmt::Display for Version {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(f, "{}.{}.{}", self.major, self.minor, self.patch)
    }
}

#[cfg(unix)]
pub(crate) fn is_package_manager_managed_exe_path(path: &Path) -> bool {
    is_homebrew_managed_exe_path_following_links(path)
        || is_mise_managed_exe_path_following_links(path)
        || is_nix_store_exe_path_following_links(path)
}

#[cfg(not(unix))]
pub(crate) fn is_package_manager_managed_exe_path(_path: &Path) -> bool {
    false
}

fn is_homebrew_managed_exe_path_following_links(path: &Path) -> bool {
    if is_homebrew_managed_exe_path(path) {
        return true;
    }

    path.canonicalize()
        .is_ok_and(|path| is_homebrew_managed_exe_path(&path))
}

fn is_nix_store_exe_path_following_links(path: &Path) -> bool {
    if is_nix_store_exe_path(path) {
        return true;
    }

    path.canonicalize()
        .is_ok_and(|path| is_nix_store_exe_path(&path))
}

fn is_mise_managed_exe_path_following_links(path: &Path) -> bool {
    if is_mise_managed_exe_path(path) {
        return true;
    }

    path.canonicalize()
        .is_ok_and(|path| is_mise_managed_exe_path(&path))
}

fn is_nix_store_exe_path(path: &Path) -> bool {
    path.starts_with("/nix/store")
}

fn is_mise_managed_exe_path(path: &Path) -> bool {
    mise_install_root(path).is_some()
}

fn mise_install_root(path: &Path) -> Option<PathBuf> {
    if let Some(root) = mise_install_root_under_configured_installs_dir(path) {
        return Some(root);
    }

    mise_install_root_under_named_installs_dir(path)
}

fn mise_install_root_under_configured_installs_dir(path: &Path) -> Option<PathBuf> {
    let installs_dir = env::var_os(MISE_INSTALLS_DIR_ENV)
        .map(PathBuf::from)
        .filter(|path| !path.as_os_str().is_empty())?;
    let version_dir = mise_tool_version_dir(path)?;
    let tool_dir = version_dir.parent()?;
    paths_match(tool_dir.parent()?, &installs_dir).then_some(version_dir.to_path_buf())
}

fn mise_install_root_under_named_installs_dir(path: &Path) -> Option<PathBuf> {
    let version_dir = mise_tool_version_dir(path)?;
    let tool_dir = version_dir.parent()?;
    let installs_dir = tool_dir.parent()?;
    if installs_dir.file_name()? != "installs" {
        return None;
    }
    Some(version_dir.to_path_buf())
}

fn mise_tool_version_dir(path: &Path) -> Option<&Path> {
    if path.file_name()? != "muster" {
        return None;
    }
    let bin_dir = path.parent()?;
    if bin_dir.file_name()? != "bin" {
        return None;
    }
    let version_dir = bin_dir.parent()?;
    let tool_dir = version_dir.parent()?;
    if tool_dir.file_name()? != "muster" {
        return None;
    }
    Some(version_dir)
}

fn paths_match(left: &Path, right: &Path) -> bool {
    if left == right {
        return true;
    }

    let Ok(left) = left.canonicalize() else {
        return false;
    };
    let Ok(right) = right.canonicalize() else {
        return false;
    };
    left == right
}

fn is_homebrew_managed_exe_path(path: &Path) -> bool {
    homebrew_cellar_keg_root(path).is_some()
}

fn homebrew_cellar_keg_root(path: &Path) -> Option<PathBuf> {
    if path.file_name()? != "muster" {
        return None;
    }
    let bin_dir = path.parent()?;
    if bin_dir.file_name()? != "bin" {
        return None;
    }
    let version_dir = bin_dir.parent()?;
    let formula_dir = version_dir.parent()?;
    if formula_dir.file_name()? != "muster" {
        return None;
    }
    let cellar_dir = formula_dir.parent()?;
    if cellar_dir.file_name()? != "Cellar" {
        return None;
    }
    Some(version_dir.to_path_buf())
}

pub(crate) fn update_install_command() -> &'static str {
    "build Muster from the local source"
}
pub(crate) fn update_install_instruction(_command: &str) -> String {
    "Online updates are disabled; build Muster from the local source.".to_string()
}
