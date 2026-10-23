#!/bin/zsh
# Run from this worker checkout. All model traffic uses local scripted endpoints.
# Raw fixtures remain under /tmp; the controller archives them under T-088.
set -u
set -o pipefail
cd "${0:A:h}/../../.." || exit 1
[[ -f workbench/tests/test_t141_loosened_limits_e2e.py ]] || { print -u2 'T-141 repository entry is missing'; exit 1; }
OUT="$(mktemp -d "$PWD/evidence/2026-10-23-batch23/T-141/outside05-XXXXXXXX")"
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
run t127-oracle-contract python3 -B workbench/tests/test_t141_t127_oracle.py --summary "$OUT/t127-oracle-contract.json"
run mcp-load-probe python3 -B workbench/tests/t141_probe_claude_mcp.py --summary "$OUT/mcp-load-probe.json"
run red python3 -B workbench/tests/test_t141_loosened_limits_e2e.py --revision 3f8813b0e --summary "$OUT/red.json"
run green python3 -B workbench/tests/test_t141_loosened_limits_e2e.py --summary "$OUT/green.json"
run network-closed python3 -B workbench/tests/test_t141_loosened_limits_e2e.py --mutant network-closed --summary "$OUT/network-closed.json"
run answer-dropped python3 -B workbench/tests/test_t141_loosened_limits_e2e.py --mutant answer-dropped --summary "$OUT/answer-dropped.json"
run shared-temp-writable python3 -B workbench/tests/test_t141_loosened_limits_e2e.py --mutant shared-temp-writable --summary "$OUT/shared-temp-writable.json"
run native-tools-unrestricted python3 -B workbench/tests/test_t141_loosened_limits_e2e.py --mutant native-tools-unrestricted --summary "$OUT/native-tools-unrestricted.json"
# T-127: four worker predicates and four stale mutation locators changed by user ruling.
# Reviewer isolation checks and all timeouts retained; T-140 has only its approved trust fixture change.
run t127 python3 -B workbench/tests/test_t127_codex_home_e2e.py --summary "$OUT/t127.json"
run t127-worker-trust-red python3 -B workbench/tests/test_t127_codex_home_e2e.py --revision 3f8813b0e --summary "$OUT/t127-worker-trust-red.json"
run t127-no-untrusted python3 -B workbench/tests/test_t127_codex_home_e2e.py --mutant untrusted-config-missing --summary "$OUT/t127-no-untrusted.json"
run t127-trusted-copy python3 -B workbench/tests/test_t127_codex_home_e2e.py --mutant project-trusted --summary "$OUT/t127-trusted-copy.json"
run t127-restricted-unanswered python3 -B workbench/tests/test_t127_codex_home_e2e.py --mutant restricted-unanswered --summary "$OUT/t127-restricted-unanswered.json"
run t127-trust-other-folder python3 -B workbench/tests/test_t127_codex_home_e2e.py --reviewer-case trust-other-folder --summary "$OUT/t127-trust-other-folder.json"
run t127-session-folder-differs python3 -B workbench/tests/test_t127_codex_home_e2e.py --reviewer-case session-folder-differs --summary "$OUT/t127-session-folder-differs.json"
run t127-resume-worker-in-argv python3 -B workbench/tests/test_t127_codex_home_e2e.py --reviewer-case resume-worker-in-argv --summary "$OUT/t127-resume-worker-in-argv.json"
run t127-resume-worker-hidden python3 -B workbench/tests/test_t127_codex_home_e2e.py --reviewer-case resume-worker-hidden --summary "$OUT/t127-resume-worker-hidden.json"
run t127-gate-trust-unchecked python3 -B workbench/tests/test_t127_codex_home_e2e.py --reviewer-case trust-other-folder --mutant gate-trust-unchecked --summary "$OUT/t127-gate-trust-unchecked.json"
run t127-folder-runtime-unbound python3 -B workbench/tests/test_t127_codex_home_e2e.py --reviewer-case session-folder-differs --mutant reviewer-folder-unbound --summary "$OUT/t127-folder-runtime-unbound.json"
run t127-gate-folder-unchecked python3 -B workbench/tests/test_t127_codex_home_e2e.py --reviewer-case session-folder-differs --mutant reviewer-folder-unbound gate-folder-unchecked --summary "$OUT/t127-gate-folder-unchecked.json"
run t127-unbound-unrecorded python3 -B workbench/tests/test_t127_codex_home_e2e.py --reviewer-case session-folder-differs --mutant unbound-unrecorded --summary "$OUT/t127-unbound-unrecorded.json"
run t127-scan-any-folder python3 -B workbench/tests/test_t127_codex_home_e2e.py --mutant scan-any-folder --summary "$OUT/t127-scan-any-folder.json"
# This variant records functional behavior/timing only; it is not negative performance evidence.
run t127-scan-whole-home python3 -B workbench/tests/test_t127_codex_home_e2e.py --mutant scan-whole-home --summary "$OUT/t127-scan-whole-home.json"
run t140 python3 -B workbench/tests/test_t140_extra_dirs_e2e.py --summary "$OUT/t140.json"
run t131 python3 -B workbench/tests/test_t131_parallel_workers_e2e.py --summary "$OUT/t131.json"
run t132 python3 -B workbench/tests/test_t132_issues_panel_e2e.py --summary "$OUT/t132.json"
python3 - "$OUT" <<'PYMATRIX'
import json, pathlib, re, sys
root = pathlib.Path(sys.argv[1])
rows = []
expected = {'red': 'codex_no_network_denial_in_argv', 'network-closed': 'codex_no_network_denial_in_argv',
            'answer-dropped': 'worker continues after controller reply', 'shared-temp-writable': 'codex_shared_temp_roots_denied',
            'native-tools-unrestricted': 'claude_native_file_tool_boundary',
            't127-worker-trust-red': 'trusted_worker_starts_directly',
            't127-gate-trust-unchecked': 'reviewer_launch_refused_trust_other_folder',
            't127-gate-folder-unchecked': 'reviewer_result_refused_session_folder_differs',
            't127-unbound-unrecorded': 'reviewer_elsewhere_unbound_recorded',
            't127-scan-any-folder': 'foreign_session_in_home_ignored'}
cases = ['launch-contract', 'reviewer-contract', 'startup-contract', 't127-oracle-contract', 'mcp-load-probe',
         'red', 'green', 'network-closed', 'answer-dropped', 'shared-temp-writable', 'native-tools-unrestricted', 't127',
         't127-worker-trust-red', 't127-no-untrusted', 't127-trusted-copy', 't127-restricted-unanswered',
         't127-trust-other-folder', 't127-session-folder-differs', 't127-resume-worker-in-argv', 't127-resume-worker-hidden',
         't127-gate-trust-unchecked', 't127-folder-runtime-unbound', 't127-gate-folder-unchecked',
         't127-unbound-unrecorded', 't127-scan-any-folder', 't127-scan-whole-home', 't140', 't131', 't132']
for name in cases:
    path = root / (name + '.json')
    result = json.loads(path.read_text(encoding='utf-8')) if path.exists() else {}
    code = int((root / (name + '.exit')).read_text())
    kind = 'behavioral_scenario'
    if name in expected:
        ok = code != 0 and expected[name] in result.get('error', '')
        kind = 'known_bad_rejected'
        if name == 't127-gate-trust-unchecked':
            ok = ok and result.get('verify', {}).get('ok') is True
        if name == 't127-gate-folder-unchecked':
            ok = ok and result.get('review', {}).get('state') == 'passed'
    elif name in ('t127-no-untrusted', 't127-trusted-copy'):
        ok = code != 0 and result.get('verify', {}).get('error') == 'review_launch_boundary'
        kind = 'known_bad_rejected'
    elif name == 't127-restricted-unanswered':
        # Require the native dialog as well as the startup failure. An unrelated
        # timeout or a mutation that failed to apply is not counterfactual evidence.
        fixture = pathlib.Path(result['fixture']) if result.get('fixture') else None
        screens = [re.sub(r'\x1b\[[0-?]*[ -/]*[@-~]|\s+', '', p.read_text(encoding='utf-8', errors='replace'))
                   for p in (fixture / 'state/traces').glob('*/pty.raw')] if fixture else []
        ok = (code != 0 and '超时：审查结束' in result.get('error', '') and any('Openrestricted' in s for s in screens) and
              any(row.get('type') == 'worker_startup_unrecognised' and 'native_ready_signal_missing' in row.get('data', {}).get('error', '')
                  for row in result.get('failures', [])))
        kind = 'known_bad_rejected'
    else:
        ok = code == 0 and result.get('status') == 'PASS'
        if name == 't127-scan-whole-home':
            kind = 'functional_variant_no_performance_claim'
    rows.append(dict(case=name, status='PASS' if ok else 'INCOMPLETE', evidence_kind=kind, exit_code=code,
                     observed_status=result.get('status'), error=result.get('error'), fixture=result.get('fixture'),
                     external_fixture=result.get('external_fixture')))
report = dict(status='PASS' if all(row['status']=='PASS' for row in rows) else 'INCOMPLETE', cases=rows,
              raw_evidence=str(root), archive_owner='executor; archive raw fixtures/logs under T-088 before cleanup')
(root/'matrix.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(report,ensure_ascii=False,indent=2))
sys.exit(0 if report['status']=='PASS' else 1)
PYMATRIX
