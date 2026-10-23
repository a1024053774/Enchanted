#!/bin/zsh
# 沙箱外运行：真实后台、Electron、Claude Code；本地脚本化 Messages 接口。
set -u
set -o pipefail
ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
cd "$ROOT" || exit 2
OUT="$(mktemp -d "$ROOT/evidence/2026-10-23-batch23/T-146-a4/outside-XXXXXXXX")" || exit 2
export PYTHONDONTWRITEBYTECODE=1
failures=0
print "证据：$OUT；Node $(node --version)；候选 $(git rev-parse HEAD)"
git rev-parse HEAD >"$OUT/candidate.txt"
git diff -- workbench/src/sidebar.ts workbench/src/reflect.ts workbench/src/flow.ts >"$OUT/candidate.diff"
run_green() {
  local name="$1"
  shift
  "$@" --summary "$OUT/$name.json" >"$OUT/$name.log" 2>&1
  local code=$?
  print "$name exit=$code"
  if (( code != 0 )); then failures=$((failures + 1)); fi
}
run_node() {
  local name="$1"
  local test="$2"
  node "$test" "$OUT/$name.json" >"$OUT/$name.log" 2>&1
  local code=$?
  print "$name exit=$code"
  if (( code != 0 )); then failures=$((failures + 1)); fi
}
# 起点同时是“交回角色后仍保留主控”的已知坏实现。不接受启动错误作红态。
python3 workbench/tests/test_t133_t107_terminal_controller_e2e.py \
  --revision 6af6e3028cbca2d1868e32eda85eeb932b91ef17 \
  --summary "$OUT/t133-t107-red.json" >"$OUT/t133-t107-red.log" 2>&1
code=$?
python3 - "$OUT/t133-t107-red.json" "$code" <<'PY'
import json, sys
from pathlib import Path
r = json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
assert int(sys.argv[2]) != 0 and r['status'] != 'PASS'
assert r['revision'] == '6af6e3028cbca2d1868e32eda85eeb932b91ef17'
assert r['error'] == 'AssertionError: 超时：身份已放弃', r.get('error')
assert 'answered_issue_no_longer_waits' in r['checks'], r['checks']
results = r['api_snapshot']['results']['ideation']
roles = []
for item in results:
    try:
        value = json.loads(item.get('text', ''))
    except json.JSONDecodeError:
        continue
    if isinstance(value, dict) and value.get('ok') and isinstance(value.get('role_request'), dict):
        roles.append(value['role_request'])
assert any(row['state'] == 'ended' and row['ended_reason'] == 'released' for row in roles), roles
print('PASS: 交回成功后，原有真实入口在主控条目移除断言超时；投影红态另存实际条目')
PY
if (( $? != 0 )); then failures=$((failures + 1)); fi
run_green t133-t107-green python3 workbench/tests/test_t133_t107_terminal_controller_e2e.py
run_green t146-green python3 workbench/tests/test_t146_session_state_e2e.py
# 另一反例：终端关闭后把主控降回普通终端，必须被已有 B 合同拒绝。
python3 workbench/tests/test_t146_session_state_e2e.py --mutant controller-becomes-shell \
  --summary "$OUT/t146-mutant-controller.json" >"$OUT/t146-mutant-controller.log" 2>&1
code=$?
python3 evidence/2026-10-23-batch23/T-146-a3/red_verdict.py \
  "$OUT/t146-mutant-controller.json" "$code" controller >"$OUT/t146-mutant-verdict.log" 2>&1
if (( $? != 0 )); then failures=$((failures + 1)); fi
run_node released-projection workbench/tests/test_t146_released_projection.mjs
run_node ended-projection workbench/tests/test_t146_ended_projection.mjs
run_node t111 workbench/tests/test_t111_flow.mjs
run_green t107 python3 workbench/tests/test_t107_live_sidebar_e2e.py
run_green t139-t143 python3 workbench/tests/test_t139_t143_views_perf_e2e.py
run_green t137 python3 workbench/tests/test_t137_reflect_e2e.py
# 截图入本次证据目录；fixtures 与大日志由主控按 T-088 归档。
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
if (( $? != 0 )); then failures=$((failures + 1)); fi
print "证据：$OUT；未通过检查数：$failures"
(( failures == 0 ))
