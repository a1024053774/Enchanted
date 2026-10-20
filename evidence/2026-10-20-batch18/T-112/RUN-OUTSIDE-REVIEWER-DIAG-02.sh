#!/bin/zsh
set -euo pipefail
cd /Users/luckye/Documents/Code/a2a-wt-t112
unset GIT_DIR GIT_WORK_TREE GIT_COMMON_DIR GIT_INDEX_FILE
export LC_ALL=C PYTHONDONTWRITEBYTECODE=1
python3 -B workbench/tests/diagnose_t112_reviewer.py \
  --summary evidence/2026-10-20-batch18/T-112/outside-reviewer-diag-02.json
