#!/bin/zsh
# T-138-1 / a1：只取修前真实 Electron 红态；无红态时禁止推进修复。
set -u
cd /Users/luckye/Documents/Code/a2a-wt-t138 || exit 2
OUT="evidence/2026-10-23-batch23/T-138/outside-01-$(date +%Y%m%d-%H%M%S)-$$"
mkdir "$OUT" || exit 2
python3 workbench/tests/test_t138_ime_e2e.py \
  --revision b99f4869bbe087946017716a5a8479c0cb47e6c8 \
  --summary "$OUT/red.json" > "$OUT/red.log" 2>&1
run_status=$?
print -r -- "exit=$run_status summary=$OUT/red.json log=$OUT/red.log"
python3 - "$OUT/red.json" <<'PY'
import json
import sys
from pathlib import Path
report = json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
print('status:', report['status'], 'defect_reproduced:', report['defect_reproduced'])
for case in report['cases']:
    print(case['name'], 'screen_reader=', case['screen_reader'],
          'expected=', repr(case['expected']), 'actual=', repr(case['actual']),
          'selection_before=', case['before'])
if report.get('error'):
    print(report['error'])
print('请回传 summary 路径；截图留在该目录，由主控归档。')
PY
exit "$run_status"
