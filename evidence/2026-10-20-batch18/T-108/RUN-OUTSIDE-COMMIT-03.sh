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
test "$(git rev-parse HEAD)" = afcc78b0d856680491f0e99410b7ff9acec54dab
if ! git diff --cached --quiet; then
  print -u2 'Existing staged changes: preserve them and stop.'
  exit 1
fi
git diff --check
git add --sparse -- \
  workbench/README.md \
  workbench/src/panes.ts workbench/src/questions.ts workbench/tests/test_t108_questions.mjs \
  evidence/2026-10-20-batch18/T-108/F1-RESULTS.md \
  evidence/2026-10-20-batch18/T-108/f1-local.summary.json \
  evidence/2026-10-20-batch18/T-108/RUN-OUTSIDE-COMMIT-03.sh
git diff --cached --check
git commit -m 'fix(workbench): reject incomplete native tool hook envelopes'
git show --no-patch --format=full HEAD
