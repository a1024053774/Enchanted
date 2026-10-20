#!/bin/zsh
set -euo pipefail
cd /Users/luckye/Documents/Code/a2a-wt-t110
export LC_ALL=C PYTHONDONTWRITEBYTECODE=1
unset GIT_DIR GIT_WORK_TREE GIT_COMMON_DIR GIT_INDEX_FILE
# Pass every completed outside summary. Preserve originals; copy regular
# files, record native symlinks as text, and verify file counts plus bytes.
LABEL=${1:?Pass a fresh archive label}
MANIFEST=${2:?Pass a fresh manifest ending in .archive.json}
shift 2
SUMMARIES=(--summary evidence/2026-10-20-batch18/T-110/questions-green-01.json)
for summary in "$@"; do SUMMARIES+=(--summary "$summary"); done
/usr/bin/python3 -B evidence/2026-10-20-batch18/T-110/archive_fixtures.py \
  --label "$LABEL" --manifest "$MANIFEST" "${SUMMARIES[@]}"
