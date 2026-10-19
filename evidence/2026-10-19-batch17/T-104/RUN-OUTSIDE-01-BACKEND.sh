#!/bin/bash
# 主控在沙箱外运行。只起隔离后台和 zsh，不起 Electron 或模型。
set -euo pipefail
ROOT=$(cd "$(dirname "$0")/../../.." && pwd -P)
cd "$ROOT"
LABEL=${1:?用法：bash RUN-OUTSIDE-01-BACKEND.sh 新运行编号，例如 backend-01}
case "$LABEL" in *[!A-Za-z0-9_-]*|'') exit 2;; esac
python3 -c 'import os; assert os.path.ismount("/Volumes/WD-Elements"), "外置盘未挂载，不回退"'
RUN="/Volumes/WD-Elements/a2a-evidence/2026-10-19-batch17/T-104/$LABEL"
mkdir -p "$(dirname "$RUN")"
mkdir "$RUN"
export npm_config_cache=/Volumes/WD-Elements/a2a-t075-npm-cache
export electron_config_cache=/Volumes/WD-Elements/a2a-electron-cache
mkdir "$RUN/npm-tmp"
export TMPDIR="$RUN/npm-tmp"
export TMP="$TMPDIR"
export TEMP="$TMPDIR"
python3 - "$ROOT" "$RUN" <<'PY'
import json, os, pathlib, shutil, subprocess, sys
root, run = map(pathlib.Path, sys.argv[1:])
deps = root / 'workbench/node_modules'
before = int(subprocess.check_output(['du','-sk',str(root)]).split()[0])
installed = not deps.exists()
if installed:
    with (run/'npm-ci.log').open('x') as log:
        subprocess.run(['npm','ci','--cache','/Volumes/WD-Elements/a2a-t075-npm-cache'],
                       cwd=root/'workbench', stdout=log, stderr=subprocess.STDOUT, check=True)
assert deps.is_dir() and not deps.is_symlink(), 'node_modules 必须是普通目录'
after = int(subprocess.check_output(['du','-sk',str(root)]).split()[0])
size = int(subprocess.check_output(['du','-sk',str(deps)]).split()[0])
report = dict(status='PASS', installed=installed, checkout_before_KiB=before, checkout_after_KiB=after,
              checkout_delta_KiB=after-before, node_modules_KiB=size,
              node=subprocess.check_output(['node','--version'],text=True).strip(),
              npm=subprocess.check_output(['npm','--version'],text=True).strip())
(run/'dependencies.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print(json.dumps(report))
PY
python3 evidence/2026-10-19-batch17/T-104/RUN-SUITE.py "$LABEL"
