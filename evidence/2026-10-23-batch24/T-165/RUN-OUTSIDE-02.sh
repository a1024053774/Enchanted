#!/bin/zsh
set -u

# 修正全局 request 关联；放开屏障后显式触发一次真实进程/转录采集。
# 两次计划内独立运行，不覆盖 01，不改产品。
task_root="${0:A:h:h:h:h}"
run_dir="$(mktemp -d /private/tmp/t165-outside-02.XXXXXX)" || exit 2
print -r -- "RUN_DIR=$run_dir"
cd "$task_root" || exit 2
git rev-parse HEAD > "$run_dir/checkout.txt"
for scenario in red-1 red-2; do
  python3 -B workbench/tests/test_t165_queued_stop_e2e.py \
    --revision f2756ea2030d8ce0bddf9980d3f36d1825201d3a \
    --summary "$run_dir/$scenario.json" > "$run_dir/$scenario.log" 2>&1
  print -r -- "$scenario TEST_EXIT=$? SUMMARY=$run_dir/$scenario.json"
done
python3 - "$run_dir" <<'PY'
import json
from pathlib import Path
import sys
root = Path(sys.argv[1])
checks = []
for name in ('red-1', 'red-2'):
    path = root / (name + '.json')
    report = json.loads(path.read_text(encoding='utf-8')) if path.exists() else {}
    checks.append(dict(name=name, passed=report.get('red_reproduced') is True and not report.get('errors'),
                       summary=str(path), errors=report.get('errors')))
result = dict(status='PASS' if all(c['passed'] for c in checks) else 'INCOMPLETE',
              claim='仅修前确定红态复现，不是产品通过', checks=checks, vendor_model_turns=0)
with (root / 'RESULT.json').open('x', encoding='utf-8') as stream:
    json.dump(result, stream, ensure_ascii=False, indent=2)
    stream.write('\n')
print(json.dumps(result, ensure_ascii=False, indent=2))
raise SystemExit(0 if result['status'] == 'PASS' else 1)
PY
