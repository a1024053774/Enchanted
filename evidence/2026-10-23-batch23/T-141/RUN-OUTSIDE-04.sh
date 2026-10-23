#!/bin/zsh
# Run from this worker checkout. All model traffic uses local scripted endpoints.
# Raw fixtures remain under /tmp; the controller archives them under T-088.
set -u
set -o pipefail
cd "${0:A:h}/../../.." || exit 1
[[ -f workbench/tests/test_t141_loosened_limits_e2e.py ]] || { print -u2 'T-141 repository entry is missing'; exit 1; }
OUT="$(mktemp -d "$PWD/evidence/2026-10-23-batch23/T-141/outside04-XXXXXXXX")"
print -r -- "Evidence: $OUT"
git rev-parse HEAD > "$OUT/candidate.txt"
git status --short > "$OUT/worktree.txt"
run() {
  local name="$1"
  shift
  print -r -- "RUN $name: $*"
  "$@" > "$OUT/$name.log" 2>&1
  local result=$?
  print -r -- "$result" > "$OUT/$name.exit"
  print -r -- "$name exit=$result"
  return 0
}
run launch-contract node workbench/tests/test_t141_launch_contract.mjs "$OUT/launch-contract.json"
run reviewer-contract node workbench/tests/test_t141_reviewer_contract.mjs "$OUT/reviewer-contract.json"
run startup-contract node workbench/tests/test_t141_startup_signal.mjs "$OUT/startup-contract.json"
run mcp-load-probe python3 -B workbench/tests/t141_probe_claude_mcp.py --summary "$OUT/mcp-load-probe.json"
run red python3 -B workbench/tests/test_t141_loosened_limits_e2e.py --revision 3f8813b0e --summary "$OUT/red.json"
run green python3 -B workbench/tests/test_t141_loosened_limits_e2e.py --summary "$OUT/green.json"
run network-closed python3 -B workbench/tests/test_t141_loosened_limits_e2e.py --mutant network-closed --summary "$OUT/network-closed.json"
run answer-dropped python3 -B workbench/tests/test_t141_loosened_limits_e2e.py --mutant answer-dropped --summary "$OUT/answer-dropped.json"
run shared-temp-writable python3 -B workbench/tests/test_t141_loosened_limits_e2e.py --mutant shared-temp-writable --summary "$OUT/shared-temp-writable.json"
run native-tools-unrestricted python3 -B workbench/tests/test_t141_loosened_limits_e2e.py --mutant native-tools-unrestricted --summary "$OUT/native-tools-unrestricted.json"
# T-127/T-140: only isolated demo-repo trust configuration changed by explicit authorization.
# All assertions, check names, expected values and timeouts remain unchanged.
run t127 python3 -B workbench/tests/test_t127_codex_home_e2e.py --summary "$OUT/t127.json"
run t140 python3 -B workbench/tests/test_t140_extra_dirs_e2e.py --summary "$OUT/t140.json"
run t131 python3 -B workbench/tests/test_t131_parallel_workers_e2e.py --summary "$OUT/t131.json"
run t132 python3 -B workbench/tests/test_t132_issues_panel_e2e.py --summary "$OUT/t132.json"
python3 - "$OUT" <<'PY'
import json, pathlib, sys
root = pathlib.Path(sys.argv[1])
rows = []
expected = {'red': 'codex_no_network_denial_in_argv', 'network-closed': 'codex_no_network_denial_in_argv',
            'answer-dropped': 'worker continues after controller reply', 'shared-temp-writable': 'codex_shared_temp_roots_denied',
            'native-tools-unrestricted': 'claude_native_file_tool_boundary'}
for name in ['launch-contract', 'reviewer-contract', 'startup-contract', 'mcp-load-probe', 'red', 'green', 'network-closed', 'answer-dropped', 'shared-temp-writable', 'native-tools-unrestricted', 't127', 't140', 't131', 't132']:
    path = root / (name + '.json')
    result = json.loads(path.read_text(encoding='utf-8')) if path.exists() else {}
    code = int((root / (name + '.exit')).read_text())
    ok = (code != 0 and expected[name] in result.get('error', '')) if name in expected else code == 0 and result.get('status') == 'PASS'
    rows.append(dict(case=name, status='PASS' if ok else 'INCOMPLETE', exit_code=code,
                     observed_status=result.get('status'), error=result.get('error'), fixture=result.get('fixture'),
                     external_fixture=result.get('external_fixture')))
report = dict(status='PASS' if all(row['status']=='PASS' for row in rows) else 'INCOMPLETE', cases=rows,
              raw_evidence=str(root), archive_owner='executor; archive raw fixtures/logs under T-088 before cleanup')
(root/'matrix.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(report,ensure_ascii=False,indent=2))
sys.exit(0 if report['status']=='PASS' else 1)
PY
