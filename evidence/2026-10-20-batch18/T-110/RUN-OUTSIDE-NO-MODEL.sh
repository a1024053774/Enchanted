#!/bin/zsh
set -euo pipefail
cd /Users/luckye/Documents/Code/a2a-wt-t110
export LC_ALL=C PYTHONDONTWRITEBYTECODE=1
unset GIT_DIR GIT_WORK_TREE GIT_COMMON_DIR GIT_INDEX_FILE
TASK_DIST=${T110_ELECTRON_DIST:-/Users/luckye/Documents/Code/a2a/workbench/node_modules/electron/dist}
SUMMARY=${1:?Pass a fresh absolute summary JSON path}
# npm ci --ignore-scripts installed this worktree's own dependencies.
# The runner copies them and only chmods its private spawn-helper copy.
test -d workbench/node_modules
/usr/bin/python3 -B workbench/tests/run_t110_notifications.py --summary "$SUMMARY" --electron-dist "$TASK_DIST"
