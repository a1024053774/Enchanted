#!/bin/zsh
# 只重跑真实 Haiku 段；已通过的产品绿态、变异与回归不再运行。
set -u
ROOT=${0:A:h:h:h:h}
cd "$ROOT" || exit 2
EVIDENCE="$ROOT/evidence/2026-10-23-batch24/T-160"
RUN=$(mktemp -d /private/tmp/t160-real-outside-XXXXXX) || exit 2
SUMMARY="$EVIDENCE/real-haiku-3-$(date -u +%Y%m%dT%H%M%SZ)-${RUN:t}.json"

# 本次仍预留完整 9 回合。已有真实消耗或观察未知时不得重复跑整段。
python3 - "$EVIDENCE" > "$RUN/budget-preflight.log" 2>&1 <<'PY'
import json
from pathlib import Path
import sys
observed = {}
for path in Path(sys.argv[1]).glob('real-haiku-3-*.json'):
    row = json.loads(path.read_text(encoding='utf-8'))
    assert not row.get('turn_observation_error'), '历史回合观察未知，交主控核对：' + str(path)
    count = row.get('real_turns_observed')
    assert type(count) is int and count >= 0, '历史回合数未知：' + str(path)
    key = row.get('fixture', str(path))
    observed[key] = max(observed.get(key, 0), count)
assert sum(observed.values()) == 0, '已有真实回合消耗，不得再预留整段 9 回合：' + str(observed)
print('PASS prior_real_turns=0 reserved_this_run=9')
PY
RC=$?
if (( RC != 0 )); then
  print -r -- "BUDGET=$RUN/budget-preflight.log"
  exit "$RC"
fi

python3 workbench/tests/test_t160_real_reviewers.py --summary "$SUMMARY" > "$RUN/real-haiku-3.log" 2>&1
RC=$?
python3 - "$SUMMARY" "$RC" <<'PY'
import json
from pathlib import Path
import shutil
import sys
p = Path(sys.argv[1])
r = json.loads(p.read_text(encoding='utf-8'))
print('SUMMARY=' + str(p))
print('FIXTURE=' + str(r.get('fixture')))
print('REAL_TURNS=' + str(r.get('real_turns_observed')))
assert int(sys.argv[2]) == 0 and r['status'] == 'PASS', (r.get('error'), r.get('cleanup_errors'))
assert len(r['trials']) == 3 and r['real_turn_limit'] == 9 and r['real_turns_observed'] <= 9
assert r.get('copied_login_removed') is True
for image in (Path(r['fixture']) / 'out').glob('*.png'):
    target = p.with_name(p.stem + '-' + image.name)
    assert not target.exists()
    shutil.copyfile(image, target)
print('PASS：真实 Haiku 段完成；请交回 SUMMARY 核对最终结果。')
PY
CHECK=$?
print -r -- "CONSOLE=$RUN/real-haiku-3.log"
exit "$CHECK"
