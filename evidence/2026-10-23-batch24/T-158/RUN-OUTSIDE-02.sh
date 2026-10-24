#!/bin/zsh
set -u

# No automatic retries. Every run gets a fresh fixture and a new summary.
cd /Users/luckye/Documents/Code/a2a-wt-t158 || exit 2
run_dir=$(mktemp -d /private/tmp/t158-outside-02.XXXXXX) || exit 2
tag=${run_dir:t}
evidence=evidence/2026-10-23-batch24/T-158
print -r -- "RUN_DIR=$run_dir"

python3 workbench/tests/test_t158_revise_retry_e2e.py --check flow --revision c01742804961214ed025b6c9fb9924a1ea49ee2d --summary "$evidence/$tag-flow-baseline.json" > "$run_dir/flow-baseline.log" 2>&1
baseline_rc=$?
cat "$run_dir/flow-baseline.log"
if (( baseline_rc != 0 )); then
  print -r -- 'Corrected fixture baseline failed. Preserve its summary; no further runtime runs.'
  exit 1
fi

python3 workbench/tests/test_t158_revise_retry_e2e.py --summary "$evidence/$tag-candidate.json" > "$run_dir/candidate.log" 2>&1
candidate_rc=$?
cat "$run_dir/candidate.log"
if (( candidate_rc != 0 )); then
  print -r -- 'Candidate failed. Preserve its summary; no mutant or regression runs.'
  exit 1
fi

python3 workbench/tests/test_t158_revise_retry_e2e.py --check flow --mutant release-before-reclaim --summary "$evidence/$tag-release-before-reclaim.json" > "$run_dir/release-before-reclaim.log" 2>&1
release_rc=$?
cat "$run_dir/release-before-reclaim.log"
python3 workbench/tests/test_t158_revise_retry_e2e.py --check flow --mutant retain-after-reclaim --summary "$evidence/$tag-retain-after-reclaim.json" > "$run_dir/retain-after-reclaim.log" 2>&1
retain_rc=$?
cat "$run_dir/retain-after-reclaim.log"

python3 workbench/tests/test_t121_role_request_e2e.py --summary "$evidence/$tag-t121.json" > "$run_dir/t121.log" 2>&1
regression_rc=$?
cat "$run_dir/t121.log"

python3 - "$evidence/$tag" <<'PY'
import json,sys
from pathlib import Path
prefix=sys.argv[1]
for suffix in ['flow-baseline','candidate','t121']:
    value=json.loads(Path(prefix+'-'+suffix+'.json').read_text(encoding='utf-8'))
    assert value['status']=='PASS', (suffix,value)
for suffix,target,required in [
    ('release-before-reclaim','unreclaimed_attempt_still_reserves_paths',['revise_revokes_candidate_and_keeps_ready_task']),
    ('retain-after-reclaim','one_dispatch_after_reclaim_without_overlap_reason',['unreclaimed_attempt_still_reserves_paths',
         'explicit_historical_reclaim_succeeds','dirty_evidence_preserved_after_reclaim'])]:
    value=json.loads(Path(prefix+'-'+suffix+'.json').read_text(encoding='utf-8'))
    assert not value['errors'], (suffix,value['errors'])
    assert value.get('target_failure')==target, (suffix,value.get('target_failure'))
    checks={row['name']:row['passed'] for row in value['checks']}
    assert checks.get(target) is False and all(checks.get(name) is True for name in required), (suffix,checks)
print('PASS: baseline/candidate/T-121; both mutants rejected at the intended behavioral assertion')
PY
validation_rc=$?
print -r -- "BASELINE=$baseline_rc CANDIDATE=$candidate_rc RELEASE_MUTANT=$release_rc RETAIN_MUTANT=$retain_rc T121=$regression_rc VALIDATION=$validation_rc"
print -r -- "SUMMARY_PREFIX=$evidence/$tag"
print -r -- 'Preserve fixture directories from all summaries for controller archiving; no old outputs were overwritten.'
if (( release_rc != 1 || retain_rc != 1 || regression_rc != 0 || validation_rc != 0 )); then
  exit 1
fi
