#!/bin/zsh
set -euo pipefail
TASK_ROOT=/Users/luckye/Documents/Code/a2a-wt-t111
TASK_DIST=${T111_ELECTRON_DIST:-/Users/luckye/Documents/Code/a2a/workbench/node_modules/electron/dist}
cd "$TASK_ROOT"
unset GIT_DIR GIT_WORK_TREE GIT_COMMON_DIR GIT_INDEX_FILE
export LC_ALL=C PYTHONDONTWRITEBYTECODE=1
node workbench/tests/test_t111_flow.mjs evidence/2026-10-20-batch18/T-111/contract-outside-03.json
node --experimental-vm-modules workbench/tests/test_t107_daemon_readonly.mjs \
  evidence/2026-10-20-batch18/T-111/daemon-outside-03.json "$TASK_ROOT" flow
python3 workbench/tests/test_t111_counterfactuals.py --daemon \
  --summary evidence/2026-10-20-batch18/T-111/counterfactuals-outside-03.json
python3 workbench/tests/run_t111_flow.py --source "$TASK_ROOT" --electron-dist "$TASK_DIST" \
  --summary evidence/2026-10-20-batch18/T-111/electron-outside-03.json
