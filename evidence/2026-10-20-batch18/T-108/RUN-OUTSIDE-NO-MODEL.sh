#!/bin/zsh
set -eu
cd /Users/luckye/Documents/Code/a2a-wt-t108
export LC_ALL=C
unset GIT_DIR GIT_WORK_TREE
# Own worktree dependencies; never link another checkout's node_modules.
test -d workbench/node_modules
chmod 755 workbench/node_modules/node-pty/prebuilds/darwin-arm64/spawn-helper
ELECTRON_DIST=${ELECTRON_OVERRIDE_DIST_PATH:-/Users/luckye/Documents/Code/a2a/workbench/node_modules/electron/dist}
SUMMARY=${1:?Pass a new absolute summary JSON path}
/usr/bin/python3 -B workbench/tests/run_t108_native_e2e.py --summary "$SUMMARY" --electron-dist "$ELECTRON_DIST"
