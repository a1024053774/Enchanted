#!/bin/zsh
set -eu
cd /Users/luckye/Documents/Code/a2a-wt-t108
export LC_ALL=C
unset GIT_DIR GIT_WORK_TREE
# Approved by controller #13: one Claude root only, no retry or second input.
# Requires the successful current-version probe; version drift refuses before input.
ELECTRON_DIST=${ELECTRON_OVERRIDE_DIST_PATH:-/Users/luckye/Documents/Code/a2a/workbench/node_modules/electron/dist}
/usr/bin/python3 -B workbench/tests/run_t108_real.py \
  --probe "${1:-/private/tmp/t108-version-probe-01.json}" \
  --summary "${2:-/private/tmp/t108-real-01.summary.json}" \
  --claude /Users/luckye/.local/bin/claude --electron-dist "$ELECTRON_DIST"
