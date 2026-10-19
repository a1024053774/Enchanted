#!/bin/bash
set -euo pipefail
cd /Users/luckye/Documents/Code/a2a-wt-t103
python3 -c 'import os; assert os.path.ismount("/Volumes/WD-Elements"), "外置盘未挂载，停止安装"'
test ! -e workbench/node_modules
before=$(du -sk workbench | cut -f1)
cd workbench
electron_config_cache=/Volumes/WD-Elements/a2a-electron-cache npm ci --cache /Volumes/WD-Elements/a2a-t075-npm-cache
npm ls --depth=0
after=$(du -sk . | cut -f1)
printf '内置盘 workbench 新增 KiB: %s\n' "$((after-before))"
du -sk node_modules
