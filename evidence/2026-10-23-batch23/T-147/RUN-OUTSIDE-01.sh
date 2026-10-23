#!/bin/zsh
set -u
cd /Users/luckye/Documents/Code/a2a-wt-t147 || exit 1
OUT=$(mktemp -d evidence/2026-10-23-batch23/T-147/outside-$(date -u +%Y%m%dT%H%M%SZ)-XXXXXX) || exit 1
git rev-parse HEAD > "$OUT/revision.txt" || exit 1
git status --short > "$OUT/worktree.txt" || exit 1

# 本次只改 T-121 的一个断言；完整 T-121 同时覆盖身份拒绝等既有回归。
python3 workbench/tests/test_t121_role_request_e2e.py --summary "$OUT/green.json" > "$OUT/green.log" 2>&1
GREEN_RC=$?
python3 workbench/tests/test_t121_role_request_e2e.py --revision 045e8cfb1 --summary "$OUT/old-behavior-red.json" > "$OUT/old-behavior-red.log" 2>&1
RED_RC=$?
print -r -- "候选退出码=$GREEN_RC；旧行为退出码=$RED_RC；证据目录=$OUT"

# 只把目标断言的失败计作反例证据，环境或其他检查失败仍为 INCOMPLETE。
python3 - "$OUT" "$GREEN_RC" "$RED_RC" <<'PY'
import json
from pathlib import Path
import sys

out = Path(sys.argv[1])
green_rc, red_rc = map(int, sys.argv[2:])
green = json.loads((out / 'green.json').read_text(encoding='utf-8'))
red = json.loads((out / 'old-behavior-red.json').read_text(encoding='utf-8'))
target = 'sidebar_drops_closed_controller'
identity = 'closed_terminal_identity_refused'
passed = (green_rc == 0 and green['status'] == 'PASS' and
          target in green['checks'] and identity in green['checks'] and
          red_rc == 1 and red['status'] == 'INCOMPLETE' and
          red.get('error') == f'AssertionError: {target}: None' and
          identity in red['checks'] and target not in red['checks'])
result = dict(status='PASS' if passed else 'INCOMPLETE', green_exit=green_rc,
              old_behavior_exit=red_rc, old_behavior_error=red.get('error'),
              revision=(out / 'revision.txt').read_text(encoding='utf-8').strip(),
              commands=[f'python3 workbench/tests/test_t121_role_request_e2e.py --summary {out}/green.json',
                        f'python3 workbench/tests/test_t121_role_request_e2e.py --revision 045e8cfb1 --summary {out}/old-behavior-red.json'])
(out / 'run.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps(result, ensure_ascii=False))
sys.exit(0 if passed else 1)
PY
