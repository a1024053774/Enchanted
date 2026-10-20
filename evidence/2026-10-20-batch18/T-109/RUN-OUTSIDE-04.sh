#!/bin/zsh
set -euo pipefail
TASK_ROOT=/Users/luckye/Documents/Code/a2a-wt-t109
TASK_DIST=${T109_ELECTRON_DIST:-/Users/luckye/Documents/Code/a2a/workbench/node_modules/electron/dist}
cd "$TASK_ROOT"
unset GIT_DIR GIT_WORK_TREE GIT_COMMON_DIR GIT_INDEX_FILE
export LC_ALL=C PYTHONDONTWRITEBYTECODE=1
python3 workbench/tests/run_t109_hierarchy.py \
  --source "$TASK_ROOT" --electron-dist "$TASK_DIST" \
  --summary evidence/2026-10-20-batch18/T-109/outside-04.json
