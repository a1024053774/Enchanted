#!/bin/zsh
set -u
cd /Users/luckye/Documents/Code/a2a-wt-t144 || exit 1
OUT=$(mktemp -d "$PWD/evidence/2026-10-23-batch23/T-144/outside-02-$(date -u +%Y%m%dT%H%M%SZ)-XXXXXX") || exit 1
print -r -- "输出：$OUT"
git rev-parse HEAD > "$OUT/candidate.txt"
git status --short > "$OUT/worktree.txt"
node --version > "$OUT/node-version.txt"
claude --version > "$OUT/claude-version.txt"
python3 - "$OUT" <<'PY'
from pathlib import Path
import sys
import tempfile
sys.path.insert(0, 'workbench/tests')
from scripted_claude import source_tree
source = source_tree(Path(tempfile.mkdtemp(prefix='t144-contract-baseline-', dir='/private/tmp')),
                     revision='6af6e3028cbca2d1868e32eda85eeb932b91ef17')
(Path(sys.argv[1]) / 'baseline-source.txt').write_text(str(source) + '\n', encoding='utf-8')
PY
if [[ $? -ne 0 ]]; then exit 1; fi
BASE_SOURCE=$(< "$OUT/baseline-source.txt")
run() {
  local label=$1
  shift
  "$@" > "$OUT/$label.log" 2>&1
  local code=$?
  print -r -- "$label $code" >> "$OUT/exit-codes.txt"
  print -r -- "$label exit=$code"
}
# Both runs use the newly authorized test file; only production sources change.
run t111-base node workbench/tests/test_t111_flow.mjs "$OUT/t111-base.json" "$BASE_SOURCE"
run t146-ended-base node workbench/tests/test_t146_ended_projection.mjs "$OUT/t146-ended-base.json" "$BASE_SOURCE"
run t111-candidate node workbench/tests/test_t111_flow.mjs "$OUT/t111-candidate.json"
run t146-ended-candidate node workbench/tests/test_t146_ended_projection.mjs "$OUT/t146-ended-candidate.json"
run green python3 workbench/tests/test_t144_flow_page_e2e.py --summary "$OUT/green.json"
python3 - "$OUT" <<'PY'
import json
from pathlib import Path
import sys
out = Path(sys.argv[1])
codes = {line.split()[0]: int(line.split()[1]) for line in (out / 'exit-codes.txt').read_text().splitlines()}
def read(label):
    path = out / (label + '.json')
    return json.loads(path.read_text(encoding='utf-8')) if path.exists() else {}
checks = {label: codes.get(label) == 0 and read(label).get('status') == 'PASS'
          for label in ('t111-candidate', 't146-ended-candidate', 'green')}
for label, location, expected in (('t111-base', 'test_t111_flow.mjs:36:', 'controller'),
                                  ('t146-ended-base', 'test_t146_ended_projection.mjs:65:', 'ended')):
    result = read(label)
    checks[label + '_rejects_behavior'] = (codes.get(label) == 1 and result.get('status') != 'PASS'
        and location in result.get('stack', '') and expected in result.get('error', ''))
summary = dict(status='PASS' if all(checks.values()) else 'INCOMPLETE', checks=checks,
               baseline='6af6e3028cbca2d1868e32eda85eeb932b91ef17',
               baseline_source=(out / 'baseline-source.txt').read_text().strip(),
               note='PASS 只表示此脚本的合同对照与真实绿态；独立审查由主控另行执行。原始现场由主控按 T-088 归档。')
(out / 'RUN-SUMMARY.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps(summary, ensure_ascii=False))
sys.exit(0 if all(checks.values()) else 1)
PY
