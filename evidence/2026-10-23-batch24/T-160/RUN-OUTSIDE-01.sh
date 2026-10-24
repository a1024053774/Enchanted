#!/bin/zsh
# 修前真实 Electron 红态；本地脚本化 Messages，不调用供应商模型。
set -u
ROOT=${0:A:h:h:h:h}
cd "$ROOT" || exit 2
RUN=$(mktemp -d /private/tmp/t160-red-outside-XXXXXX) || exit 2
SUMMARY="$ROOT/evidence/2026-10-23-batch24/T-160/red-$(date -u +%Y%m%dT%H%M%SZ)-${RUN:t}.json"
python3 workbench/tests/test_t160_review_recovery_e2e.py \
  --revision 3aea74368a020109027c6113a161f32db8614102 \
  --summary "$SUMMARY" > "$RUN/console.log" 2>&1
RC=$?
python3 - "$SUMMARY" "$RC" <<'PY'
import json
from pathlib import Path
import shutil
import sys
p = Path(sys.argv[1])
r = json.loads(p.read_text(encoding='utf-8'))
expected = {'fenced_output_rejected', 'raw_preserved', 'failed_review_cannot_integrate'}
assert sys.argv[2] == '1', r
assert expected <= set(r['checks']), r
assert r.get('error', '').startswith('AssertionError: recovery_guidance_visible:'), r
image = p.with_suffix('.png')
assert not image.exists()
shutil.copyfile(r['screenshot'], image)
print('PASS：已取得指定缺陷的修前红态；产品修复与绿态仍为 INCOMPLETE。')
print('SUMMARY=' + str(p))
print('SCREENSHOT=' + str(image))
print('FIXTURE=' + r['fixture'])
PY
CHECK=$?
print -r -- "CONSOLE=$RUN/console.log"
exit "$CHECK"
