#!/bin/zsh
set -eu
cd /Users/luckye/Documents/Code/a2a-wt-t108
export LC_ALL=C
unset GIT_DIR GIT_WORK_TREE
RUN=$(mktemp -d /private/tmp/t108-review05-recheck-XXXXXX)
print -r -- "Evidence: $RUN"
# No CLI/model/login or Git writes. Red proof uses a fresh plain dependency copy.
python3 -B evidence/2026-10-20-batch18/T-108/replay_review05_red.py "$RUN/red-proof.json"
node workbench/tests/test_t108_driver.mjs "$RUN/driver.json" > "$RUN/driver.log" 2>&1
node workbench/tests/test_t108_questions.mjs "$RUN/questions.json" > "$RUN/local-9.log" 2>&1
node --experimental-vm-modules workbench/tests/test_t091_pane_ipc.mjs "$RUN/ipc.json" > "$RUN/local-10.log" 2>&1
node workbench/tests/test_t107_sidebar.mjs "$RUN/sidebar.json" > "$RUN/local-11.log" 2>&1
node workbench/tests/test_t109_hierarchy.mjs "$RUN/hierarchy.json" > "$RUN/local-12.log" 2>&1
node workbench/tests/test_t111_flow.mjs "$RUN/flow.json" > "$RUN/local-13.log" 2>&1
node workbench/tests/test_t078_claude_signals.ts "$RUN/claude-signals" > "$RUN/local-14.log" 2>&1
node workbench/tests/test_t078_pane_runtime.ts "$RUN/pane-runtime" > "$RUN/local-15.log" 2>&1
git show HEAD:evidence/2026-10-20-batch18/T-108/native-hook-samples.json > "$RUN/native-hooks.json"
node workbench/tests/test_t108_hook_replay.mjs --samples "$RUN/native-hooks.json" --summary "$RUN/codex.json" > "$RUN/local-17.log" 2>&1
node --experimental-vm-modules workbench/tests/test_t107_daemon_readonly.mjs "$RUN/readonly.json" . readonly > "$RUN/local-18.log" 2>&1
node --experimental-vm-modules workbench/tests/test_t107_daemon_readonly.mjs "$RUN/identity.json" . identity > "$RUN/local-19.log" 2>&1
# #30: replay the original normal question, its own PermissionRequest,
# answer, native confirmation and matched Stop. No new CLI/model is started.
node evidence/2026-10-20-batch18/T-108/replay_permission_same_question.mjs \
  "${1:-/private/tmp/t108-native-e2e-03.json}" "$RUN/same-question.json"
print -r -- "Local checks complete: $RUN; GUI/CLI complete-entry run and independent acceptance are separate. No commit."
