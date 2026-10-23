#!/bin/zsh
set -u
ROOT=${0:A:h:h:h:h}
cd "$ROOT" || exit 2
OUT=$(mktemp -d "$ROOT/evidence/2026-10-23-batch23/T-152/outside-05-XXXXXXXX") || exit 2
REV=$(git rev-parse HEAD) || exit 2
RUNNER=evidence/2026-10-23-batch23/T-152/run_suite.py
READER=evidence/2026-10-23-batch23/T-152/read_tracer_flow.py
TOTAL=0
python3 -B "$RUNNER" --revision "$REV" --case tracer_review_copy --summary "$OUT/tracer.json" || TOTAL=1
python3 -B "$READER" --revision "$REV" --run-summary "$OUT/tracer.json" --summary "$OUT/tracer-flow.json" || TOTAL=1
if [[ "$TOTAL" -ne 0 ]]; then
  python3 - "$OUT" "$REV" <<'PY'
import json
from pathlib import Path
import sys
out = Path(sys.argv[1])
with (out / 'SUMMARY.json').open('x', encoding='utf-8') as stream:
    json.dump({'status': 'INCOMPLETE', 'source_revision': sys.argv[2], 'phase': 'normal_tracer_preflight',
               'evidence': ['tracer.json', 'tracer-flow.json'],
               'not_run': ['8 mutants', 'all normal cases', 'T-090', 'T-141'],
               'reason': 'Stop at the first incomplete real flow; inspect the retained failure before expanding.'}, stream, ensure_ascii=False, indent=2)
    stream.write('\n')
print(out / 'SUMMARY.json')
PY
  exit 1
fi
for MUTANT in no-end-check nonempty-workspace omit-shared-refs false-copy-removed readonly-argv wrong-workspace network-disabled tmp-writable; do
  python3 -B "$RUNNER" --revision "$REV" --mutant "$MUTANT" --summary "$OUT/$MUTANT.json" || TOTAL=1
done
# Full normal suite after the counterfactuals, then the direct inheritor and argv contract.
python3 -B "$RUNNER" --revision "$REV" --summary "$OUT/green.json" || TOTAL=1
python3 -B "$RUNNER" --revision "$REV" --worker-regression --summary "$OUT/t090.json" || TOTAL=1
node workbench/tests/test_t141_reviewer_contract.mjs "$OUT/t141-reviewer.json" "$ROOT" > "$OUT/t141.stdout.txt" 2> "$OUT/t141.stderr.txt" || TOTAL=1
python3 - "$OUT" "$REV" "$TOTAL" <<'PY'
import json
from pathlib import Path
import subprocess
import sys
out = Path(sys.argv[1])
names = ['tracer.json', 'tracer-flow.json', 'no-end-check.json', 'nonempty-workspace.json',
         'omit-shared-refs.json', 'false-copy-removed.json', 'readonly-argv.json', 'wrong-workspace.json',
         'network-disabled.json', 'tmp-writable.json', 'green.json', 't090.json', 't141-reviewer.json']
record = {'status': 'INCOMPLETE', 'source_revision': sys.argv[2], 'checks': {},
          'raw_artifacts': 'Each runner JSON lists retained artifact_root and fixture_root; controller archives under T-088.'}
try:
    for name in names:
        value = json.loads((out / name).read_text(encoding='utf-8'))
        record['checks'][name] = value['status']
        if name != 't141-reviewer.json' and value['source_revision'] != sys.argv[2]:
            raise RuntimeError('Source revision mismatch in ' + name)
    record['ending_revision'] = subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip()
    record['status'] = 'PASS' if sys.argv[3] == '0' and record['ending_revision'] == sys.argv[2] and all(s == 'PASS' for s in record['checks'].values()) else 'INCOMPLETE'
except Exception as error:
    record['error'] = repr(error)
with (out / 'SUMMARY.json').open('x', encoding='utf-8') as stream:
    json.dump(record, stream, ensure_ascii=False, indent=2)
    stream.write('\n')
print(json.dumps({'status': record['status'], 'summary': str(out / 'SUMMARY.json')}))
raise SystemExit(0 if record['status'] == 'PASS' else 1)
PY
if [[ $? -ne 0 ]]; then TOTAL=1; fi
exit "$TOTAL"
