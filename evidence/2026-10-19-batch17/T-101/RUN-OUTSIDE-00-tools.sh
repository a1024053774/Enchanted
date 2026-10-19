#!/bin/sh
set -eu
python3 -c 'import os; from pathlib import Path; p=Path("/Volumes/WD-Elements"); assert p.is_dir() and not p.is_symlink() and p.resolve()==p and os.path.ismount(p), "NO_GO 外置盘未挂载"'
base=/Volumes/WD-Elements/a2a-backup-pre-slim
python3 -c 'from pathlib import Path; p=Path("/Volumes/WD-Elements/a2a-backup-pre-slim"); assert not any(q.is_symlink() for q in (p,*p.parents)), "NO_GO 拒绝符号链接"'
test ! -e "$base/tools"
test ! -L "$base/tools"
test ! -e "$base/tool-docs"
test ! -L "$base/tool-docs"
test ! -e "$base/tool-tmp"
test ! -L "$base/tool-tmp"
test ! -e "$base/tool-cache"
test ! -L "$base/tool-cache"
mkdir -p "$base/tool-tmp" "$base/tool-cache" "$base/tool-docs"
export TMPDIR="$base/tool-tmp"
curl --fail --location --max-time 60 https://raw.githubusercontent.com/newren/git-filter-repo/main/INSTALL.md --output "$base/tool-docs/INSTALL.md"
curl --fail --location --max-time 60 https://raw.githubusercontent.com/newren/git-filter-repo/main/Documentation/git-filter-repo.txt --output "$base/tool-docs/git-filter-repo.txt"
python3 -m venv "$base/tools"
"$base/tools/bin/python" -m pip --isolated --disable-pip-version-check install --no-input --index-url https://pypi.org/simple --cache-dir "$base/tool-cache" git-filter-repo
"$base/tools/bin/python" -m pip freeze > "$base/tool-docs/installed.txt"
"$base/tools/bin/git-filter-repo" -h > "$base/tool-docs/installed-help.txt"
printf '%s\n' 'PASS 工具仅安装到外置盘 venv；未运行历史改写'
