#!/bin/zsh
# T-160 当前候选：真实 Electron 绿态、三个已知坏实现、现行回归、真实 Haiku 3 次。
# 不自动重试；只有最后一个测试会请求真实模型，总计上限 9 个原生输入回合。
set -u
ROOT=${0:A:h:h:h:h}
cd "$ROOT" || exit 2
RUN=$(mktemp -d /private/tmp/t160-verify-outside-XXXXXX) || exit 2
TAG="$(date -u +%Y%m%dT%H%M%SZ)-${RUN:t}"
EVIDENCE="$ROOT/evidence/2026-10-23-batch24/T-160"

run_case() {
  local name="$1" expected="$2"
  shift 2
  local summary="$EVIDENCE/${name}-${TAG}.json"
  python3 "$@" --summary "$summary" > "$RUN/${name}.log" 2>&1
  local case_rc=$?
  python3 - "$summary" "$case_rc" "$expected" <<'PY'
import json
from pathlib import Path
import shutil
import sys
p = Path(sys.argv[1])
r = json.loads(p.read_text(encoding='utf-8'))
rc, expected = int(sys.argv[2]), sys.argv[3]
if expected == 'PASS':
    assert rc == 0 and r['status'] == 'PASS', (p, rc, r.get('error'), r.get('cleanup_errors'))
elif expected.startswith('STATE:'):
    assert rc == 1 and r['status'] == 'INCOMPLETE', (p, rc, r)
    case = expected.split(':', 1)[1]
    assert any(c['name'] == case and c['status'] == 'INCOMPLETE' and c.get('error', '').startswith('AssertionError')
               for c in r.get('checks', [])), (p, r)
else:
    assert rc == 1 and r['status'] == 'INCOMPLETE', (p, rc, r)
    assert r.get('error', '').startswith('AssertionError: ' + expected + ':'), (p, r.get('error'))
if 'fixture' in r:
    for image in (Path(r['fixture']) / 'out').glob('*.png'):
        target = p.with_name(p.stem + '-' + image.name)
        assert not target.exists()
        shutil.copyfile(image, target)
if 'real_turn_limit' in r:
    assert r['real_turn_limit'] == 9 and r['real_turns_observed'] <= 9, r
    assert len(r['trials']) == 3 and r.get('copied_login_removed') is True, r
print(('PASS' if expected == 'PASS' else 'PASS known_bad_rejected=' + expected) + ' SUMMARY=' + str(p))
PY
  local check_rc=$?
  print -r -- "CONSOLE=$RUN/${name}.log"
  return "$check_rc"
}

run_case idle-red STATE:matched_parser_failure_reclaimable workbench/tests/test_t160_protocol_idle.py --revision 3aea74368a020109027c6113a161f32db8614102 || exit $?
run_case idle-green PASS workbench/tests/test_t160_protocol_idle.py || exit $?
run_case idle-mutant-any-unknown STATE:unmatched_stop_not_reclaimable workbench/tests/test_t160_protocol_idle.py --mutant any-unknown || exit $?
run_case idle-mutant-ignore-submission STATE:different_submission_not_reclaimable workbench/tests/test_t160_protocol_idle.py --mutant ignore-submission || exit $?

run_case green PASS workbench/tests/test_t160_review_recovery_e2e.py || exit $?
run_case mutant-accept-fenced fenced_output_rejected workbench/tests/test_t160_review_recovery_e2e.py --mutant accept-fenced || exit $?
run_case mutant-unbound-review unbound_recovery_rejected workbench/tests/test_t160_review_recovery_e2e.py --mutant unbound-review || exit $?
run_case mutant-reuse-failed same_delivery_new_review workbench/tests/test_t160_review_recovery_e2e.py --mutant reuse-failed-review || exit $?

# 现行脚本化原生 CLI + Electron 回归：问题页读写/关闭/读失败，和正常审查回收/评分集成。
# 历史 controlled-quality host 不在当前候选混跑。
run_case regression-issues PASS workbench/tests/test_t132_issues_panel_e2e.py || exit $?
run_case regression-review-integration PASS workbench/tests/test_t137_reflect_e2e.py || exit $?

# 真实登录在隔离 HOME 中预检；不写用户配置。3 个真实 worker 各至多 2 回合（含交付 ACK），
# 3 个独立真实 reviewer 各 1 回合。拒绝后只核对页面恢复入口，不自动再起真实 reviewer。
run_case real-haiku-3 PASS workbench/tests/test_t160_real_reviewers.py || exit $?
print -r -- "PASS：脚本各项完成；请将 SUMMARY 路径交回 worker 核对并更新 RESULTS。"
