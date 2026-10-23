#!/bin/zsh
# 沙箱外：真实 Electron/后台/Claude CLI；脚本化模型，无供应商调用。
set -u
set -o pipefail
ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
cd "$ROOT" || exit 2
OUT="$ROOT/evidence/2026-10-23-batch23/T-146-a3/outside-$(date -u +%Y%m%dT%H%M%SZ)-$$"
mkdir "$OUT" || exit 2
export PYTHONDONTWRITEBYTECODE=1
failures=0
node_version="$(node --version)"
print "Node $node_version；起点 bf932d499；证据 $OUT"
python3 workbench/tests/test_t146_red_verdict.py "$OUT/red-verdict-checks.json" >"$OUT/red-verdict-checks.log" 2>&1 || failures=$((failures + 1))
run_green() {
  local name="$1"
  shift
  "$@" --summary "$OUT/$name.json" >"$OUT/$name.log" 2>&1
  local code=$?
  print "$name exit=$code"
  if (( code != 0 )); then failures=$((failures + 1)); fi
}
run_red() {
  local name="$1"
  local kind="$2"
  shift 2
  "$@" --summary "$OUT/$name.json" >"$OUT/$name.log" 2>&1
  local code=$?
  python3 "$ROOT/evidence/2026-10-23-batch23/T-146-a3/red_verdict.py" "$OUT/$name.json" "$code" "$kind"
  local checked=$?
  print "$name exit=$code contract_check=$checked"
  if (( checked != 0 )); then failures=$((failures + 1)); fi
}
# 隔离投影、受保护 T-111 的新旧合同、T-091 与起点的同错误比较。
BASE="$(mktemp -d /private/tmp/t146-a3-baseline.XXXXXX)" || exit 2
git archive bf932d499 workbench/src workbench/app workbench/tests/test_t111_flow.mjs | tar -x -C "$BASE" || exit 2
ln -s "$ROOT/workbench/node_modules" "$BASE/workbench/node_modules" || exit 2
node workbench/tests/test_t146_ended_projection.mjs "$OUT/projection.json" >"$OUT/projection.log" 2>&1 || failures=$((failures + 1))
node workbench/tests/test_t111_flow.mjs "$OUT/t111-green.json" >"$OUT/t111-green.log" 2>&1 || failures=$((failures + 1))
node workbench/tests/test_t111_flow.mjs "$OUT/t111-red.json" "$BASE" >"$OUT/t111-red.log" 2>&1
node "$BASE/workbench/tests/test_t111_flow.mjs" "$OUT/t111-old-on-candidate.json" "$ROOT" >"$OUT/t111-old-on-candidate.log" 2>&1
node --experimental-vm-modules workbench/tests/test_t091_pane_ipc.mjs "$OUT/t091-baseline.json" --source "$BASE" >"$OUT/t091-baseline.log" 2>&1
node --experimental-vm-modules workbench/tests/test_t091_pane_ipc.mjs "$OUT/t091-candidate.json" >"$OUT/t091-candidate.log" 2>&1
python3 - "$OUT" <<'PY'
import json, sys
from pathlib import Path
out = Path(sys.argv[1])
read = lambda name: json.loads((out / (name + '.json')).read_text(encoding='utf-8'))
for name in ('t111-red', 't111-old-on-candidate'):
    r = read(name)
    assert r['status'] != 'PASS' and 'ended' in r.get('error', ''), r
a, b = read('t091-baseline'), read('t091-candidate')
assert a['status'] == b['status'] and a.get('error') == b.get('error') and a['checks'] == b['checks'], (a, b)
print('PASS: T-111 新旧合同互拒，T-091 与起点同样（不冒称 T-091 通过）')
PY
if (( $? != 0 )); then failures=$((failures + 1)); fi
node workbench/tests/test_t146_session_end.mjs "$OUT/session-end.json" >"$OUT/session-end.log" 2>&1 || failures=$((failures + 1))
run_red t146-red baseline python3 workbench/tests/test_t146_session_state_e2e.py --revision bf932d49940104ec099023aa957d06fe95116e92
run_green t146-green python3 workbench/tests/test_t146_session_state_e2e.py
run_red t146-mutant-flow flow python3 workbench/tests/test_t146_session_state_e2e.py --mutant flow-hide-ended
run_red t146-mutant-controller controller python3 workbench/tests/test_t146_session_state_e2e.py --mutant controller-becomes-shell
run_green t139-t143 python3 workbench/tests/test_t139_t143_views_perf_e2e.py
run_green t140 python3 workbench/tests/test_t140_extra_dirs_e2e.py
run_green t137 python3 workbench/tests/test_t137_reflect_e2e.py
run_green t107 python3 workbench/tests/test_t107_live_sidebar_e2e.py
run_green t145 python3 workbench/tests/test_t145_mouse_reports_e2e.py
# 将截图复制到本次证据目录；run/fixtures 留原处，按 T-088 由主控归档。
python3 - "$OUT" <<'PY'
import json, shutil, sys
from pathlib import Path
out = Path(sys.argv[1])
for summary in out.glob('*.json'):
    report = json.loads(summary.read_text(encoding='utf-8'))
    if report.get('fixture'):
        for image in (Path(report['fixture']) / 'out').glob('*.png'):
            shutil.copy2(image, out / (summary.stem + '-' + image.name))
PY
print "证据：$OUT；未通过检查数：$failures"
(( failures == 0 ))
