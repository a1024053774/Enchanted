#!/bin/zsh
set -u
set -C

# 真实 Electron 红态；不启动模型、不修改产品代码，不申请提权。
cd "${0:A:h}/../../.." || exit 2
run_id="$(date -u +%Y%m%dT%H%M%SZ)-${RANDOM}"
prefix="evidence/2026-10-23-batch24/T-162/red-${run_id}"
summary="${prefix}.json"
python3 workbench/tests/test_t162_role_records_metrics_e2e.py \
  --revision c01742804 --summary "$summary" > "${prefix}.log" 2>&1
test_rc=$?

# 只有缺陷断言失败才确认红态；环境失败、清理失败或夹具失败都不算红态。
python3 - "$summary" "$test_rc" "$prefix" <<'PY'
import json
from pathlib import Path
import sys

path, rc, prefix = Path(sys.argv[1]), int(sys.argv[2]), Path(sys.argv[3])
if not path.is_file():
    raise SystemExit('INCOMPLETE: 没有 summary，检查 ' + str(prefix) + '.log')
report = json.loads(path.read_text(encoding='utf-8'))
checks = {item['name']: item['status'] for item in report['checks']}
expected = ['two_explicit_decisions_are_user_inputs', 'controller_without_native_count_is_unknown']
red = rc == 1 and report['status'] == 'NO_GO' and not report.get('error') and not report.get('cleanup_error') and all(checks.get(name) == 'FAIL' for name in expected)
if report.get('fixture'):
    for name in ('01-role-records.png', '02-metrics-unknown.png', 'failure.png'):
        source = Path(report['fixture']) / 'out' / name
        if source.is_file():
            destination = Path(str(prefix) + '-' + name)
            with destination.open('xb') as target:
                target.write(source.read_bytes())
print(('PASS: 修前缺陷红态已复现；产品仍为 NO_GO' if red else 'INCOMPLETE: 尚未取得所需红态') + '\nSUMMARY=' + str(path))
print('FIXTURE=' + str(report.get('fixture', '未完成初始化')))
raise SystemExit(0 if red else 1)
PY
