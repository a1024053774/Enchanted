#!/bin/zsh
set -u

# First checkpoint: run BEFORE changing product instructions.
# Real isolated daemon, PTY and Electron; interactive Claude CLI uses only the local scripted API.
# No user HOME/config, vendor calls, overlap override, main integration, or push.
cd /Users/luckye/Documents/Code/a2a-wt-t158 || exit 2
run_dir=$(mktemp -d /private/tmp/t158-outside-01.XXXXXX) || exit 2
tag=${run_dir:t}
evidence=evidence/2026-10-23-batch24/T-158
print -r -- "RUN_DIR=$run_dir"

python3 workbench/tests/test_t158_revise_retry_e2e.py --check flow --revision c01742804961214ed025b6c9fb9924a1ea49ee2d --summary "$evidence/$tag-flow-baseline.json" > "$run_dir/flow-baseline.log" 2>&1
flow_rc=$?
cat "$run_dir/flow-baseline.log"

python3 workbench/tests/test_t158_revise_retry_e2e.py --check instructions --revision c01742804961214ed025b6c9fb9924a1ea49ee2d --summary "$evidence/$tag-instructions-red.json" > "$run_dir/instructions-red.log" 2>&1
instructions_rc=$?
cat "$run_dir/instructions-red.log"

print -r -- "FLOW_EXIT=$flow_rc INSTRUCTIONS_EXIT=$instructions_rc"
print -r -- "SUMMARIES=$evidence/$tag-flow-baseline.json $evidence/$tag-instructions-red.json"
print -r -- 'Expected: flow exit 0; instructions exit 1 with five named discoverability failures and errors=[].'
print -r -- 'A setup/cleanup failure is INCOMPLETE, not the intended red. Preserve fixture paths from summaries for controller archiving.'
if (( flow_rc != 0 || instructions_rc != 1 )); then
  exit 1
fi
