#!/bin/zsh
set -u
ROOT=${0:A:h:h:h:h}
cd "$ROOT" || exit 2
OUT=$(mktemp -d "$ROOT/evidence/2026-10-23-batch23/T-152/outside-01-XXXXXXXX") || exit 2
REV=$(git rev-parse HEAD) || exit 2
RUNNER=evidence/2026-10-23-batch23/T-152/run_suite.py
TOTAL=0
# First prove the retained checks reject each bad implementation, then run green.
for MUTANT in no-end-check nonempty-workspace omit-shared-refs false-copy-removed readonly-argv wrong-workspace network-disabled tmp-writable; do
  python3 -B "$RUNNER" --revision "$REV" --mutant "$MUTANT" --summary "$OUT/$MUTANT.json" || TOTAL=1
done
python3 -B "$RUNNER" --revision "$REV" --summary "$OUT/green.json" || TOTAL=1
# Direct inheritor: worker HEAD/branch/dirty boundaries share ReviewBoundary.
python3 -B "$RUNNER" --revision "$REV" --worker-regression --summary "$OUT/t090.json" || TOTAL=1
# Existing launch-contract regression independently covers both CLI argv shapes.
node workbench/tests/test_t141_reviewer_contract.mjs "$OUT/t141-reviewer.json" "$ROOT" > "$OUT/t141.stdout.txt" 2> "$OUT/t141.stderr.txt" || TOTAL=1
python3 - "$OUT" "$REV" "$TOTAL" <<'PY'
import json
from pathlib import Path
import sys
out = Path(sys.argv[1])
rows = {p.name: json.loads(p.read_text(encoding='utf-8'))['status'] for p in out.glob('*.json')}
with (out / 'SUMMARY.json').open('x', encoding='utf-8') as stream:
    json.dump({'status': 'PASS' if sys.argv[3] == '0' and len(rows) == 11 and all(s == 'PASS' for s in rows.values()) else 'INCOMPLETE',
               'source_revision': sys.argv[2], 'checks': rows,
               'raw_artifacts': 'Each case JSON lists retained /private/tmp artifact_root and fixture_root; controller archives under T-088.'}, stream, ensure_ascii=False, indent=2)
    stream.write('\n')
print(out)
PY
exit "$TOTAL"
