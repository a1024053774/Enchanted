#!/bin/zsh
# Run from this worker checkout. All model traffic uses local scripted endpoints.
# Raw fixtures remain under /tmp; the controller archives them under T-088.
set -u
set -o pipefail
cd "${0:A:h}/../../.." || exit 1
[[ -f workbench/tests/test_t141_loosened_limits_e2e.py ]] || { print -u2 'T-141 repository entry is missing'; exit 1; }
OUT="$(mktemp -d "$PWD/evidence/2026-10-23-batch23/T-141/outside06-XXXXXXXX")"
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
run t127 python3 -B workbench/tests/test_t127_codex_home_e2e.py --summary "$OUT/t127.json"
run t127-no-untrusted python3 -B workbench/tests/test_t127_codex_home_e2e.py --mutant untrusted-config-missing --summary "$OUT/t127-no-untrusted.json"
run t127-trusted-copy python3 -B workbench/tests/test_t127_codex_home_e2e.py --mutant project-trusted --summary "$OUT/t127-trusted-copy.json"
run t127-folder-runtime-unbound python3 -B workbench/tests/test_t127_codex_home_e2e.py --reviewer-case session-folder-differs --mutant reviewer-folder-unbound --summary "$OUT/t127-folder-runtime-unbound.json"
run t127-gate-folder-unchecked python3 -B workbench/tests/test_t127_codex_home_e2e.py --reviewer-case session-folder-differs --mutant reviewer-folder-unbound gate-folder-unchecked --summary "$OUT/t127-gate-folder-unchecked.json"
python3 - "$OUT" <<'PYMATRIX'
import json, pathlib, sqlite3, subprocess, sys
root = pathlib.Path(sys.argv[1])
rows = []

def has_error(value, expected):
    if isinstance(value, dict):
        return value.get('error') == expected or any(has_error(child, expected) for child in value.values())
    return isinstance(value, list) and any(has_error(child, expected) for child in value)

for name in ['t127', 't127-no-untrusted', 't127-trusted-copy', 't127-folder-runtime-unbound', 't127-gate-folder-unchecked']:
    path = root / (name + '.json')
    result = json.loads(path.read_text(encoding='utf-8')) if path.exists() else {}
    code = int((root / (name + '.exit')).read_text())
    trust_proof, expected_layer, observed_layer = None, None, None
    if name in ('t127-no-untrusted', 't127-trusted-copy'):
        trust_proof = dict(status='INCOMPLETE')
        if code != 0 and result.get('verify', {}).get('error') == 'review_launch_boundary':
            try:
                database = pathlib.Path(result['fixture']) / 'state/state.sqlite3'
                # The test process has ended and daemon_stop ran. Immutable reads
                # this checkpointed snapshot without trying to create WAL sidecars.
                # Never ignore a nonempty WAL that could contain newer evidence.
                wal = database.with_name(database.name + '-wal')
                if wal.exists() and wal.stat().st_size:
                    raise ValueError('uncheckpointed_fixture_database')
                with sqlite3.connect('file:' + str(database) + '?mode=ro&immutable=1', uri=True) as connection:
                    saved = [(kind, json.loads(data)) for kind, data in connection.execute(
                        "SELECT type,details FROM events WHERE type IN ('review_requested','review_lifecycle_failed') ORDER BY seq")]
                failed = next(data for kind, data in reversed(saved) if kind == 'review_lifecycle_failed' and
                              data.get('details', {}).get('error') == 'review_launch_boundary')
                requested = next(data['review'] for kind, data in saved if kind == 'review_requested' and
                                 data['review']['review_id'] == failed['review_id'])
                facts = failed['details']['details']
                context = dict(review=dict(requested, launch_id=facts['launch']['id']), launch=facts['launch'], live=facts['live'])
                proof_input, proof_output = root / (name + '.trust-input.json'), root / (name + '.trust-proof.json')
                with proof_input.open('x', encoding='utf-8') as stream:
                    stream.write(json.dumps(context, ensure_ascii=False, indent=2)+'\n')
                replay = subprocess.run(['node', 'workbench/tests/t141_review_trust_rejection.mjs', str(proof_input),
                    'missing' if name == 't127-no-untrusted' else 'trusted', str(proof_output)], capture_output=True, text=True)
                trust_proof = json.loads(proof_output.read_text(encoding='utf-8')) if proof_output.exists() else dict(
                    status='INCOMPLETE', error=replay.stderr)
                trust_proof['replay_exit_code'] = replay.returncode
            except (OSError, sqlite3.Error, ValueError, KeyError, StopIteration) as error:
                trust_proof = dict(status='INCOMPLETE', error=f'{type(error).__name__}: {error}')
        ok = (trust_proof.get('status') == 'PASS' and trust_proof.get('restored_trust_only_launch_accepted') is True and
              trust_proof.get('replay_exit_code') == 0)
        expected_layer = 'review_launch_boundary/trust_only_counterfactual'
        observed_layer = result.get('verify', {}).get('error')
        if ok: observed_layer = 'review_launch_boundary/trust_only_counterfactual_validated'
    elif name == 't127-folder-runtime-unbound':
        ok = (code == 0 and result.get('status') == 'PASS' and result.get('review', {}).get('state') != 'passed' and
              has_error(result.get('refusals'), 'review_native_session_folder'))
        expected_layer = 'review_native_session_folder'
        if has_error(result.get('refusals'), 'review_native_session_folder'): observed_layer = 'review_native_session_folder'
    elif name == 't127-gate-folder-unchecked':
        ok = (code != 0 and 'reviewer_result_refused_session_folder_differs' in result.get('error', '') and
              result.get('review', {}).get('state') == 'passed')
        expected_layer = 'missing_review_native_session_folder_guard_exposed_by_behavior_assertion'
        if result.get('review', {}).get('state') == 'passed': observed_layer = 'review_passed'
    else:
        ok = code == 0 and result.get('status') == 'PASS'
        observed_layer = result.get('review', {}).get('state')
    rows.append(dict(case=name, status='PASS' if ok else 'INCOMPLETE', exit_code=code, expected_boundary=expected_layer, observed_gate_result=observed_layer,
        observed_status=result.get('status'), error=result.get('error'), fixture=result.get('fixture'), trust_rejection_proof=trust_proof))
report = dict(status='PASS' if all(row['status']=='PASS' for row in rows) else 'INCOMPLETE', cases=rows,
    raw_evidence=str(root), archive_owner='executor; archive raw fixtures/logs under T-088 before cleanup')
(root/'matrix.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(report,ensure_ascii=False,indent=2))
sys.exit(0 if report['status']=='PASS' else 1)
PYMATRIX
