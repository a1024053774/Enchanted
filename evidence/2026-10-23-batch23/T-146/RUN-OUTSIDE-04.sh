#!/bin/zsh
set -u
cd /Users/luckye/Documents/Code/a2a-wt-t146 || exit 1
OUT="evidence/2026-10-23-batch23/T-146/outside04-$(date -u +%Y%m%dT%H%M%SZ)-$$"
mkdir "$OUT" || exit 1
python3 workbench/tests/test_t146_session_state_e2e.py --revision ebbae7bd0 --summary "$OUT/red.json" > "$OUT/red.log" 2>&1
RED_RC=$?
python3 workbench/tests/test_t146_session_state_e2e.py --summary "$OUT/green.json" > "$OUT/green.log" 2>&1
GREEN_RC=$?
python3 workbench/tests/test_t146_session_state_e2e.py --mutant reflect-lifecycle --summary "$OUT/mutant.json" > "$OUT/mutant.log" 2>&1
MUTANT_RC=$?
python3 workbench/tests/test_t146_cli_exit_probe.py --revision ebbae7bd0 --summary "$OUT/native-red.json" > "$OUT/native-red.log" 2>&1
NATIVE_RED_RC=$?
python3 workbench/tests/test_t146_cli_exit_probe.py --summary "$OUT/native-green.json" > "$OUT/native-green.log" 2>&1
NATIVE_GREEN_RC=$?
node workbench/tests/test_t111_flow.mjs "$OUT/t111.json" . > "$OUT/t111.log" 2>&1
FLOW_RC=$?
python3 workbench/tests/test_t137_reflect_e2e.py --summary "$OUT/t137.json" > "$OUT/t137.log" 2>&1
REFLECT_RC=$?
node workbench/tests/test_t146_session_end.mjs "$OUT/session-end.json" . > "$OUT/session-end.log" 2>&1
SESSION_END_RC=$?
node workbench/tests/test_t146_reviewer_hooks.mjs "$OUT/reviewer-hooks.json" . > "$OUT/reviewer-hooks.log" 2>&1
REVIEWER_HOOKS_RC=$?
python3 - "$OUT" "$RED_RC" "$GREEN_RC" "$MUTANT_RC" "$NATIVE_RED_RC" "$NATIVE_GREEN_RC" "$FLOW_RC" "$REFLECT_RC" "$SESSION_END_RC" "$REVIEWER_HOOKS_RC" <<'PY'
import json,sys
from pathlib import Path
out=Path(sys.argv[1])
names=['red','green','mutant','native-red','native-green','t111','t137','session-end','reviewer-hooks']
codes=dict(zip(names,map(int,sys.argv[2:])))
reports={name:json.loads((out/(name+'.json')).read_text(encoding='utf-8')) if (out/(name+'.json')).exists()
         else {'status':'INCOMPLETE','error':'summary missing'} for name in names}
counterexamples=all(codes[name]==1 and reports[name].get('error','').startswith('AssertionError: reflect_idle:')
                    for name in ['red','mutant'])
native_red=codes['native-red']==1 and reports['native-red'].get('error','').startswith('AssertionError: CLI exited with live zsh:')
green=all(codes[name]==0 and reports[name].get('status')=='PASS' for name in ['green','native-green','t111','t137','session-end','reviewer-hooks'])
summary={'status':'PASS' if counterexamples and native_red and green else 'INCOMPLETE','exit_codes':codes,
         'counterexamples_rejected_for_expected_reason':counterexamples,'native_red_is_cli_exit_defect':native_red,
         'errors':{name:report.get('error') for name,report in reports.items()},'output':str(out)}
with (out/'run-results.json').open('x',encoding='utf-8') as f:
    f.write(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(summary,ensure_ascii=False))
sys.exit(0 if summary['status']=='PASS' else 1)
PY
