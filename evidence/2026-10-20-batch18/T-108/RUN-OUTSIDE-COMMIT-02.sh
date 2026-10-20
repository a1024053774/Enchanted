#!/bin/zsh
set -eu
cd /Users/luckye/Documents/Code/a2a-wt-t108
export LC_ALL=C
unset GIT_DIR GIT_WORK_TREE
# Exact public worker identity; the existing hook validates its launch record.
# No manual trailers, Git config writes, hook changes, submit or push.
export A2A_PROJECT=a2a
export A2A_TASK=T-108
export A2A_ATTEMPT=a1
export A2A_SESSION=d07960e3-56d6-4b80-9f31-cc10605b69c8
export A2A_ROLE=worker
export A2A_LAUNCH=launch-eb74ca1d5e8e4cfc877a2819bc0afe76
export A2A_LAUNCHES=/Users/luckye/Documents/Code/a2a/records/launches.jsonl
export CODEX_THREAD_ID=01a157cc-f9c2-70d3-849e-42883fe1e09c
export GIT_CONFIG_COUNT=1
export GIT_CONFIG_KEY_0=core.hooksPath
export GIT_CONFIG_VALUE_0=/Users/luckye/Documents/Code/a2a/scripts/git-hooks
test "$(git branch --show-current)" = exec/t108
git merge-base --is-ancestor 16b412964 HEAD
if ! git diff --cached --quiet; then
  print -u2 'Existing staged changes: preserve them and stop.'
  exit 1
fi
git diff --check
git add --sparse -- \
  workbench/README.md \
  workbench/src/claudeLaunch.ts workbench/src/claudeLogin.ts workbench/src/claudeLoginSession.py \
  workbench/tests/prepare_t108_real.py workbench/tests/run_t108_real.py \
  workbench/tests/probe_t093_normal_login.py workbench/tests/test_t093_launch_profile.ts \
  workbench/tests/test_t093_session_once.ts workbench/tests/test_t093_prepare_failure.py \
  workbench/tests/test_t093_forwarder_port_policy.py workbench/tests/test_t093_session_cleanup.py \
  workbench/tests/test_t096_restore.mjs evidence/2026-10-20-batch18/T-108
git diff --cached --check
git commit -m 'fix(workbench): observe installed Claude version for normal login'
git show --no-patch --format=full HEAD
