#!/bin/zsh
set -u
ROOT=${0:A:h:h:h:h}
cd "$ROOT" || exit 2
OUT=$(mktemp -d "$ROOT/evidence/2026-10-23-batch23/T-152/outside-04-XXXXXXXX") || exit 2
REV=$(git rev-parse HEAD) || exit 2
TOTAL=0
python3 -B evidence/2026-10-23-batch23/T-152/run_suite.py --revision "$REV" --case tracer_review_copy --summary "$OUT/tracer.json" || TOTAL=1
python3 -B evidence/2026-10-23-batch23/T-152/read_tracer_flow.py --run-summary "$OUT/tracer.json" --summary "$OUT/SUMMARY.json" --revision "$REV" || TOTAL=1
exit "$TOTAL"
