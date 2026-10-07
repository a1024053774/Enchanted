"""Reproducible namespace/online-feature changes after the upstream red run."""
from pathlib import Path
import re

root = Path('muster/engine')


def replace_file(relative, transform):
    path = root / relative
    old = path.read_text(encoding='utf-8')
    path.write_text(transform(old), encoding='utf-8')


def span(text, first, following, replacement=''):
    start = text.index(first)
    end = text.index(following, start)
    return text[:start] + replacement + text[end:]


# Third-party vendored sources and licenses retain their original attribution.
# Historical changelogs and upstream governance files are source records.
for path in root.rglob('*'):
    if not path.is_file() or 'vendor' in path.relative_to(root).parts:
        continue
    if path.name in ['LICENSE', 'AGENTS.md', 'CONTRIBUTING.md', 'CHANGELOG.md']:
        continue
    try:
        old = path.read_text(encoding='utf-8')
    except UnicodeDecodeError:
        continue
    new = old.replace('HERDR', 'MUSTER').replace('Herdr', 'Muster').replace('herdr', 'muster')
    if new != old:
        path.write_text(new, encoding='utf-8')
for path in sorted(root.rglob('*'), key=lambda p: len(p.parts), reverse=True):
    if 'vendor' in path.relative_to(root).parts:
        continue
    new_name = path.name.replace('herdr', 'muster')
    if new_name != path.name:
        path.rename(path.with_name(new_name))

replace_file('src/config/io.rs', lambda s: span(s, 'pub fn app_dir_name()', 'pub fn config_dir()',
    'pub fn app_dir_name() -> &\'static str {\n    \"muster\"\n}\n\n'))
replace_file('Cargo.toml', lambda s: re.sub(r'^homepage = .*\n', '', s, flags=re.M))
replace_file('build.rs', lambda s: span(s, '    println!(\n        "cargo:warning=', '\n}', ''))
replace_file('src/main.rs', lambda s: span(s, '    if args.get(1).map(|s| s.as_str()) == Some("update") {',
    '    if args.iter().any(|a| a == "--help"',
    '    if args.get(1).map(String::as_str) == Some("update") {\n'
    '        eprintln!("Muster online updates are disabled; build from the local source.");\n'
    '        std::process::exit(1);\n    }\n\n'))
renamed_upstream_host = 'muster' + '.dev'
replace_file('src/main.rs', lambda s: s.replace('        println!("Home:   https://' + renamed_upstream_host + '");\n', '')
    .replace('# Check ' + renamed_upstream_host + ' for new Muster versions in the background.', '# Online version checks are disabled in this fork.')
    .replace('# Check ' + renamed_upstream_host + ' for remote agent-detection manifest updates in the background.', '# Online detection manifest checks are disabled in this fork.')
    .replace('# version_check = true', '# version_check = false').replace('# manifest_check = true', '# manifest_check = false')
    .replace('Download and install the latest version', 'Online updates are disabled in this fork')
    .replace('Choose the stable or preview update channel', 'Online release channels are disabled in this fork')
    .replace('Manage the stable or preview update channel', 'Online release channels are disabled in this fork'))
replace_file('src/cli.rs', lambda s: span(s, 'pub(crate) const AGENT_HELP_FOOTER:', 'pub(crate) fn parse_token_assignment',
    'pub(crate) const AGENT_HELP_FOOTER: &str = "Control Muster panes and agents: run muster --skill.";\n\n'))
replace_file('src/cli.rs', lambda s: span(s, 'fn run_channel_command(', 'fn run_config_command(',
    'fn run_channel_command(_args: &[String]) -> std::io::Result<i32> {\n'
    '    eprintln!("Muster online release channels are disabled.");\n    Ok(1)\n}\n\n'))
# These upstream tests describe removed release-channel behavior.
replace_file('src/cli.rs', lambda s: span(s, '    #[test]\n    fn parses_channel_set_argument()',
                                        '    #[test]\n    fn session_name_parser_accepts_option_terminator()'))

# Keep local semver and local installation-path recognition. Remove all HTTP,
# binary replacement, remote release-note and announcement acquisition code.
source = (root / 'src/update.rs').read_text(encoding='utf-8')
version = source[source.index('/// Parsed semver'):source.index('// ---------------------------------------------------------------------------\n// Update manifest')]
paths = source[source.index('#[cfg(unix)]\npub(crate) fn is_package_manager_managed_exe_path'):source.index('// ---------------------------------------------------------------------------\n// Public API')]
(root / 'src/update.rs').write_text(
    '//! Local version and installation metadata. Muster does not self-update.\n'
    'use std::{env, path::{Path, PathBuf}};\n'
    'const MISE_INSTALLS_DIR_ENV: &str = "MISE_INSTALLS_DIR";\n'
    'pub(crate) const WINDOWS_INSTALLER: &str = include_str!("../distribution/install.ps1");\n\n'
    + version + paths + '\npub(crate) fn update_install_command() -> &\'static str {\n'
    '    "build Muster from the local source"\n}\n'
    'pub(crate) fn update_install_instruction(_command: &str) -> String {\n'
    '    "Online updates are disabled; build Muster from the local source.".to_string()\n}\n', encoding='utf-8')

source = (root / 'src/detect/manifest_update.rs').read_text(encoding='utf-8')
local_types = source[source.index('#[derive(Debug, Clone)]'):source.index('#[derive(Debug, Deserialize)]')]
load_status = source[source.index('pub(crate) fn load_status()'):source.index('fn save_status(')]
cache_paths = source[source.index('pub(crate) fn status_path()'):source.index('fn commit_remote_manifest(')]
state_root = source[source.index('fn state_root()'):source.index('fn catalog_url()')]
version_tests = source[source.index('    #[test]\n    fn manifest_version_compares'):source.index('    #[test]\n    fn process_agent_manifest_commits')]
(root / 'src/detect/manifest_update.rs').write_text(
    '//! Local detection-cache metadata; online catalog acquisition is disabled.\n'
    'use std::{cmp::Ordering, collections::BTreeMap, fmt, fs, path::PathBuf};\n'
    'use serde::{Deserialize, Serialize};\nuse super::{agent_label, Agent};\n'
    'pub(crate) const MANIFEST_ENGINE_VERSION: u32 = 3;\n\n'
    + local_types + load_status + cache_paths + state_root +
    '\npub(crate) fn check_and_update() -> Result<(), String> {\n'
    '    Err("Muster online detection manifest updates are disabled.".to_string())\n}\n'
    '\n#[cfg(test)]\nmod tests {\n    use super::*;\n' + version_tests + '}\n', encoding='utf-8')

replace_file('src/app/mod.rs', lambda s: span(s, 'fn auto_updates_enabled(', 'fn load_plugin_registry(',
    '// Online release and catalog checks cannot be enabled by configuration.\n'
    'fn background_update_check_enabled(_background_updates: bool, _check_enabled: bool) -> bool {\n    false\n}\n\n'))
replace_file('src/app/mod.rs', lambda s: span(s, '        if version_check_enabled {', '        let last_focus'))
replace_file('src/app/runtime.rs', lambda s: span(s, '    pub(crate) fn run_auto_update_check(',
    '    pub(crate) fn next_headless_loop_deadline_with_git_refresh(',
    '    pub(crate) fn run_auto_update_check(&mut self) {\n        self.next_auto_update_check = None;\n    }\n\n'
    '    pub(crate) fn run_agent_manifest_update_check(&mut self) {\n        self.next_agent_manifest_update_check = None;\n    }\n\n'))
replace_file('src/app/runtime.rs', lambda s: s.replace('    background_update_check_enabled, App, AUTO_UPDATE_CHECK_INTERVAL, MIN_RENDER_INTERVAL,',
                                                       '    App, MIN_RENDER_INTERVAL,'))
replace_file('src/config.rs', lambda s: s.replace('        UpdateChannelConfig, MAX_TOAST_DELAY_SECONDS,', '        MAX_TOAST_DELAY_SECONDS,'))
replace_file('src/platform/mod.rs', lambda s: s.replace('begin_cli_output, end_cli_output, forward_remote_bridge_stdio', 'begin_cli_output, forward_remote_bridge_stdio'))
replace_file('src/config/model.rs', lambda s: s.replace('version_check: true,', 'version_check: false,')
    .replace('manifest_check: true,', 'manifest_check: false,')
    .replace('assert!(default_config.update.version_check);', 'assert!(!default_config.update.version_check);')
    .replace('assert!(default_config.update.manifest_check);', 'assert!(!default_config.update.manifest_check);'))

# Remote attach can still use a supplied local binary; it cannot fetch releases.
replace_file('src/remote/attach.rs', lambda s: re.sub(r'^const (STABLE|PREVIEW)_UPDATE_MANIFEST_URL:.*\n', '', s, flags=re.M))
replace_file('src/remote/attach.rs', lambda s: span(s, 'fn download_release_asset(', 'fn remote_asset_info(',
    'fn download_release_asset(_platform: &RemotePlatform) -> io::Result<InstallSource> {\n'
    '    Err(io::Error::other("Muster online binary downloads are disabled; supply a local binary."))\n}\n\n'))
replace_file('src/remote/attach.rs', lambda s: span(s, 'fn remote_release_asset(', 'fn private_download_dir('))
replace_file('src/noninteractive_process.rs', lambda s: s[:s.index('\npub(crate) fn curl_command()')])
(root / 'distribution/install.ps1').write_text('Write-Error "Muster online installation is disabled. Build from local source."\nexit 1\n', encoding='utf-8')
(root / 'distribution/install.sh').write_text('#!/bin/sh\necho "Muster online installation is disabled. Build from local source." >&2\nexit 1\n', encoding='utf-8')

Path('muster/Cargo.lock').write_text(Path('muster/Cargo.lock').read_text().replace('name = "herdr"', 'name = "muster"'))
(root / 'NOTICE').write_text('Muster 引擎派生自 Herdr 0.9.3。\n'
    '上游：https://github.com/herdrdev/herdr\n'
    '固定提交：c4653a4f10502601ac110b12b2c45a5f7134082b（c4653a4）\n'
    '上游许可：Apache-2.0；原始 LICENSE 和第三方 vendor 许可保留。\n'
    '导入方式：git archive；本地变更包括 Cargo workspace、Muster 命名空间及禁用在线发布/检测清单下载。\n'
    'AGENTS.md、CONTRIBUTING.md、CHANGELOG.md 是保留的上游治理/历史记录；a2a 根规则和当前任务书优先。\n'
    '上游图像素材仅作为导入来源保留，不用于 Muster 的界面或产品说明。\n', encoding='utf-8')
(root / 'README.md').write_text('# Muster 引擎\n\n'
    '这是 Muster 工作台的终端引擎，代码来源、固定提交和许可见 [NOTICE](NOTICE) 与 [LICENSE](LICENSE)。\n\n'
    '从 a2a 根目录执行 `MUSTER_BUILD_SLOT=worker-t027 ./scripts/build build --locked --manifest-path muster/Cargo.toml`。'
    '构建入口要求外置盘；不直接调用 Cargo 或 Zig。\n\n'
    '可执行文件为 `muster`，配置目录为 `~/.config/muster`；环境变量以 `MUSTER_` 开头。'
    '用 `muster --session NAME server` 启动独立后台会话，控制命令见 `muster --help`。'
    '本切片保留 CLI 的 workspace/tab 字段，分别对应项目/任务。\n\n'
    '在线自更新、预览通道、公告和检测清单下载已禁用；检测清单来自本地源码。'
    '集成安装会写目标 agent 配置；本地验收通过独立 `CODEX_HOME` 安装，不修改用户已有 hook。\n', encoding='utf-8')

# Preserve published wire identifiers and independently supplied fixed test inputs.
replace_file('src/api/schema/panes.rs', lambda s: s.replace('    #[default]\n    Muster,',
    '    // Generation 1 freezes this wire value; rename it only in a newly negotiated generation.\n'
    '    // CLI spelling and display remain Muster (T-027); there is one serialized value, no alias.\n'
    '    #[default]\n    #[serde(rename = "herdr")]\n    Muster,', 1))
replace_file('src/checksum.rs', lambda s: s.replace('fs::write(&path, b"muster")', 'fs::write(&path, b"herdr")'))
replace_file('src/ui/text.rs', lambda s: s.replace('提交 muster 的反馈', '提交 herdr 的反馈').replace('提交 muster 的反…', '提交 herdr 的反…'))
for schema in (root / 'docs').rglob('muster-api.schema.json'):
    text = schema.read_text().replace('"muster",\n            "pane"', '"herdr",\n            "pane"').replace('"default": "muster"', '"default": "herdr"')
    schema.write_text(text)
replace_file('src/app/actions.rs', lambda s: s.replace('detach, run `muster update`, then run Muster again to reconnect', 'Online updates are disabled; build Muster from the local source.').replace('detach, run `brew update && brew upgrade muster`, then run Muster again to reconnect', 'Online updates are disabled; build Muster from the local source.'))
replace_file('src/ui/release_notes.rs', lambda s: s.replace(' detach, run muster update, then run Muster again to reconnect', ' Online updates are disabled; build Muster from the local source.').replace('        assert_eq!(lines[1].spans[2].content.as_ref(), "muster update");\n        assert_eq!(lines[1].spans[2].style.fg, Some(palette.accent));\n        assert_eq!(lines[1].spans[2].style.bg, Some(palette.surface0));', '        assert!(!line_text(&lines[1]).contains("muster update"));'))
replace_file('src/client/shell/tests/startup_overlays.rs', lambda s: s.replace('assert!(text.contains("detach, run muster update"));', 'assert!(text.contains("Online updates are disabled"));'))

replace_file('src/cli/spec.rs', lambda s: s.replace('Download and install the latest version', 'Online updates are disabled in this fork').replace('Manage stable and preview update channels', 'Online release channels are disabled in this fork').replace('Fetch and reload agent detection manifests', 'Online detection manifest updates are disabled'))

replace_file('src/server/headless/tests/mod.rs', lambda s: s.replace('Some(\"detach, run `muster update`, then run Muster again to reconnect\")', 'Some(\"Online updates are disabled; build Muster from the local source.\")'))

replace_file('Cargo.toml', lambda s: s.replace('repository = \"https://github.com/herdrdev/herdr\"\n', ''))

# The Letta capture fixture's first execution must finish before its one-second hook probe.
# This local test preparation is retained in src/integration/tests.rs; see test-isolation.md.

# Product spelling does not change upstream URLs.
for original_file in root.rglob('*'):
    if 'zig-pkg' in original_file.parts or not original_file.is_file():
        continue
    try:
        original_text = original_file.read_text(encoding='utf-8')
    except UnicodeDecodeError:
        continue
    revised_text = original_text.replace('muster' + 'dev/muster', 'herdrdev/herdr').replace('muster' + '.dev', 'herdr.dev')
    if revised_text != original_text:
        original_file.write_text(revised_text, encoding='utf-8')
replace_file('Cargo.toml', lambda s: s.replace('license = "Apache-2.0"', 'license = "Apache-2.0"\nrepository = "https://github.com/a1024053774/a2a"') if 'repository =' not in s else s)
