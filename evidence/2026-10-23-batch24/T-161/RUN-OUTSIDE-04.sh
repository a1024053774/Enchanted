#!/bin/zsh
set -u
# 仅重跑修前红态。测试 exit=1 是预期；另核对仅六条缺陷断言失败且无运行错误。
cd /Users/luckye/Documents/Code/a2a-wt-t161 || exit 2
stamp=$(date -u +%Y%m%dT%H%M%SZ)
out="evidence/2026-10-23-batch24/T-161/red04-${stamp}"
python3 workbench/tests/test_t161_readonly_role_e2e.py --revision 3c56f743f --summary "${out}.json" > "${out}.log" 2>&1
result=$?
print "exit=${result} summary=${out}.json log=${out}.log"
python3 - "${out}.json" <<'PY'
import json, sys
from pathlib import Path
report = json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
expected = {
    'reviewer_view_has_no_input_error', 'reviewer_no_requested_input_focus',
    'history_view_has_no_input_error', 'history_no_requested_input_focus',
    'confirmed_executor_header_with_sidebar_hidden', 'renamed_controller_keeps_carrier_and_role',
}
failed = {check['name'] for check in report['checks'] if not check['passed']}
controls = {check['name']: check['passed'] for check in report['checks']}
complete = (failed == expected and not report.get('error') and not report.get('cleanup_errors') and
            controls.get('real_input_failure_still_visible') is True and controls.get('zero_model_requests') is True)
print('RED / ' + ('PASS' if complete else 'INCOMPLETE'))
if not complete:
    raise SystemExit(2)
PY
verdict=$?
if (( verdict != 0 )); then exit "$verdict"; fi
exit "$result"
