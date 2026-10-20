#!/bin/zsh
set -eu
cd /Users/luckye/Documents/Code/a2a-wt-t108
export LC_ALL=C
unset GIT_DIR GIT_WORK_TREE
# Verify full session/debug path, process start time and argv before each signal.
# Only the exact two test PIDs; retain fixture/logs and refuse PID reuse.
/usr/bin/python3 -B workbench/tests/t108_cleanup.py --summary "${1:-/private/tmp/t108-cleanup-01.json}"
