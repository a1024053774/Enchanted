#!/bin/zsh
set -u
cd /Users/luckye/Documents/Code/a2a-wt-t144 || exit 1
OUT=$(mktemp -d "$PWD/evidence/2026-10-23-batch23/T-144/outside-$(date -u +%Y%m%dT%H%M%SZ)-XXXXXX") || exit 1
print -r -- "输出：$OUT"
git rev-parse HEAD > "$OUT/candidate.txt"
git status --short > "$OUT/worktree.txt"
node --version > "$OUT/node-version.txt"
claude --version > "$OUT/claude-version.txt"
run() {
  local label=$1
  shift
  "$@" > "$OUT/$label.log" 2>&1
  local code=$?
  print -r -- "$label $code" >> "$OUT/exit-codes.txt"
  print -r -- "$label exit=$code"
}
run red python3 workbench/tests/test_t144_flow_page_e2e.py --revision 6af6e3028cbca2d1868e32eda85eeb932b91ef17 --summary "$OUT/red.json"
run green python3 workbench/tests/test_t144_flow_page_e2e.py --summary "$OUT/green.json"
run uuid-title python3 workbench/tests/test_t144_flow_page_e2e.py --mutant uuid-title --summary "$OUT/uuid-title.json"
run terminal-task python3 workbench/tests/test_t144_flow_page_e2e.py --mutant terminal-task --summary "$OUT/terminal-task.json"
run projection node workbench/tests/test_t144_flow_projection.mjs "$OUT/projection.json"
run t146 python3 workbench/tests/test_t146_session_state_e2e.py --summary "$OUT/t146.json"
run t137 python3 workbench/tests/test_t137_reflect_e2e.py --summary "$OUT/t137.json"
# These two legacy contracts require controllers to remain unassigned.
# Preserve their results for the controller's decision; do not edit their oracle.
run t111 node workbench/tests/test_t111_flow.mjs "$OUT/t111.json"
run t146-ended node workbench/tests/test_t146_ended_projection.mjs "$OUT/t146-ended.json"
python3 - "$OUT" <<'PY'
import json
from pathlib import Path
import sys
out = Path(sys.argv[1])
def read(label):
    path = out / (label + '.json')
    return json.loads(path.read_text(encoding='utf-8')) if path.exists() else {}
checks = {}
for label in ('green', 'projection', 't146', 't137'):
    checks[label] = read(label).get('status') == 'PASS'
for label, expected in (('red', '_worker_title'), ('uuid-title', '_worker_title'), ('terminal-task', '_isolated_members')):
    result = read(label)
    checks[label + '_rejects_behavior'] = result.get('status') != 'PASS' and any(
        failure['name'].endswith(expected) for failure in result.get('failures', []))
summary = dict(status='INCOMPLETE', checks=checks,
    behavioral_checks='PASS' if all(checks.values()) else 'INCOMPLETE',
    legacy_contracts={label: read(label) for label in ('t111', 't146-ended')},
    note='旧合同冲突待主控裁定；原始 fixtures 留在摘要列出的 /private/tmp 目录，按 T-088 由主控归档。')
(out / 'RUN-SUMMARY.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps(dict(status=summary['status'], behavioral_checks=summary['behavioral_checks'], checks=checks), ensure_ascii=False))
sys.exit(0 if all(checks.values()) else 1)
PY
