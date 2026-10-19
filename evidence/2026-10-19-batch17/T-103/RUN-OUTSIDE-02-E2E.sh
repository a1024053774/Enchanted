#!/bin/bash
set -euo pipefail
cd /Users/luckye/Documents/Code/a2a-wt-t103
/usr/bin/python3 -B -c 'import os; assert os.path.ismount("/Volumes/WD-Elements"), "外置盘未挂载，停止验证"'
test -d workbench/node_modules
source_root="$PWD"
electron_dist="$source_root/workbench/node_modules/electron/dist"
stamp=$(date -u +%Y%m%dT%H%M%SZ)
base="/Volumes/WD-Elements/a2a-evidence/2026-10-19-batch17/T-103/baseline-$stamp"
mkdir -p "$(dirname "$base")"
mkdir "$base" # 新时间戳目录；已存在则退出，保留旧副本。
node --experimental-vm-modules workbench/tests/test_t103_driver_startup.mjs "$base/driver-startup.json" \
  /Volumes/WD-Elements/a2a-evidence/2026-10-19-batch17/T-103/run-20261019T051645Z/source-snapshot/workbench/tests/t103_picker_driver.mjs
node workbench/tests/test_t103_keyboard_entry.mjs "$base/keyboard-entry.json" \
  /Volumes/WD-Elements/a2a-evidence/2026-10-19-batch17/T-103/run-20261019T060557Z/source-snapshot/workbench/tests/t103_picker_driver.mjs
bash "$source_root/evidence/2026-10-19-batch17/T-103/RUN-OUTSIDE-04-ELECTRON.sh" \
  "$source_root/workbench" "$base/worktree-electron"
git archive cc18d93dbbcf2ee641dc92befe68e5b0609b4807 workbench | tar -x -C "$base"
(
  cd "$base/workbench"
  electron_config_cache=/Volumes/WD-Elements/a2a-electron-cache npm ci --cache /Volumes/WD-Elements/a2a-t075-npm-cache
  helper=node_modules/node-pty/prebuilds/darwin-arm64/spawn-helper
  before_helper_mode=$(stat -f '%Lp' "$helper")
  # 执行主控 #8 明确授权；仅处理本次新建的基线测试副本。
  chmod 755 "$helper"
  /usr/bin/python3 -B - "$base" "$stamp" "$before_helper_mode" "$electron_dist" <<'PY'
import json, os, stat, sys
from pathlib import Path
base, stamp, before = Path(sys.argv[1]), sys.argv[2], sys.argv[3]
dist = Path(sys.argv[4]).resolve(strict=True)
assert not dist.is_relative_to('/Volumes'), 'Electron 必须从内置盘执行'
installed = json.loads((base / 'workbench/node_modules/electron/package.json').read_text(encoding='utf-8'))
project = json.loads((base / 'workbench/package.json').read_text(encoding='utf-8'))
lock = json.loads((base / 'workbench/package-lock.json').read_text(encoding='utf-8'))
internal = json.loads((dist.parent / 'package.json').read_text(encoding='utf-8'))
prepared = json.loads((base / 'worktree-electron/result.json').read_text(encoding='utf-8'))
expected = project['dependencies']['electron']
assert prepared['status'] == 'PASS'
assert installed['version'] == internal['version'] == lock['packages']['node_modules/electron']['version'] == expected
assert (dist / 'version').read_text(encoding='utf-8').strip().removeprefix('v') == expected
assert prepared['binary_probe']['stdout'].strip() == expected
relative = (dist.parent / 'path.txt').read_text(encoding='utf-8')
assert relative == 'Electron.app/Contents/MacOS/Electron'
executable = (dist / relative).resolve(strict=True)
assert os.access(executable, os.X_OK)
# Electron's existing override resolves this platform-relative metadata against
# the selected internal dist. Do not download or run an external Electron.
path_file = base / 'workbench/node_modules/electron/path.txt'
with path_file.open('x', encoding='utf-8') as stream:
    stream.write(relative)
assert not (base / 'workbench/node_modules/electron/dist').exists()
helper = base / 'workbench/node_modules/node-pty/prebuilds/darwin-arm64/spawn-helper'
value = {'baseline': str(base), 'stamp': stamp, 'mode': '新时间戳目录，不复用旧副本',
         'reason': '按 README:319 处理测试副本',
         'authorization': '执行主控 #8：npm ci 后只对基线副本此文件 chmod 755',
         'argv': ['chmod', '755', str(helper)], 'before_mode': before,
         'after_mode': format(stat.S_IMODE(helper.stat().st_mode), 'o'),
         'electron_runtime': {'authorization': '执行主控 #13：红态和绿态统一使用同一个内置盘 Electron',
             'baseline_package_version': installed['version'], 'candidate_package_version': internal['version'],
             'version': expected, 'dist': str(dist), 'executable': str(executable),
             'binary_probe_version': prepared['binary_probe']['stdout'].strip(),
             'baseline_dist_installed': False, 'baseline_path_txt': str(path_file),
             'baseline_path_txt_content': relative, 'ELECTRON_OVERRIDE_DIST_PATH': str(dist)}}
assert value['after_mode'] == '755'
with (base / 'baseline-install.json').open('x', encoding='utf-8') as stream:
    json.dump(value, stream, ensure_ascii=False, indent=2)
    stream.write('\n')
print(json.dumps(value, ensure_ascii=False))
PY
)
ELECTRON_OVERRIDE_DIST_PATH="$electron_dist" /usr/bin/python3 -B workbench/tests/run_t103_picker.py \
  --source "$PWD" --baseline "$base" --electron-dist "$electron_dist" \
  --output "/Volumes/WD-Elements/a2a-evidence/2026-10-19-batch17/T-103/run-$stamp"
