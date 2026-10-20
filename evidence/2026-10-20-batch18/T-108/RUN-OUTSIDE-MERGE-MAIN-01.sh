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
# Merge first. Never rebase, reset, abort or discard a conflicting scene.
test "$(git branch --show-current)" = exec/t108
test "$(git rev-parse HEAD)" = 93fe03dcd54535bc3b48d58e30a6244bf697fca1
test "$(git rev-parse main)" = 12190c32f2cee01dcef3654b2e90860887eabee6
git merge-base --is-ancestor e00f4d6de main
git diff --quiet
git diff --cached --quiet
test ! -e "$(git rev-parse --git-path MERGE_HEAD)"
MERGE_RUN=$(mktemp -d /private/tmp/t108-main-merge-01-XXXXXX)
print -r -- "Merge evidence: $MERGE_RUN"
set +e
git -c merge.conflictStyle=merge merge --no-commit main
MERGE_RC=$?
set -e
if test "$MERGE_RC" -ne 1; then
  print -u2 'Expected reviewed conflicts were not produced; preserve scene and stop.'
  exit 1
fi
/usr/bin/python3 -B - <<'CHECK'
import os, subprocess
expected=['workbench/src/panes.ts','workbench/tests/test_t091_pane_ipc.mjs']
actual=subprocess.check_output(['git','diff','--name-only','--diff-filter=U'],env=dict(os.environ,LC_ALL='C'),text=True).splitlines()
assert sorted(actual)==expected, ('Unexpected conflict set; preserve scene',actual)
CHECK
/usr/bin/python3 -B evidence/2026-10-20-batch18/T-108/resolve_main_merge_01.py .
git add --sparse -- workbench/src/panes.ts workbench/tests/test_t091_pane_ipc.mjs
if test -n "$(git diff --name-only --diff-filter=U)"; then
  print -u2 'Unresolved conflicts remain; preserve scene and stop.'
  exit 1
fi
# No models or credentials: retain both branches' contracts before committing.
node workbench/tests/test_t108_questions.mjs "$MERGE_RUN/questions.json"
node --experimental-vm-modules workbench/tests/test_t091_pane_ipc.mjs "$MERGE_RUN/ipc.json"
node workbench/tests/test_t107_sidebar.mjs "$MERGE_RUN/sidebar.json"
node workbench/tests/test_t109_hierarchy.mjs "$MERGE_RUN/hierarchy.json"
node workbench/tests/test_t111_flow.mjs "$MERGE_RUN/flow.json"
git add --sparse -- \
  evidence/2026-10-20-batch18/T-108/RUN-OUTSIDE-MERGE-MAIN-01.sh \
  evidence/2026-10-20-batch18/T-108/resolve_main_merge_01.py \
  evidence/2026-10-20-batch18/T-108/MERGE-MAIN-01.md \
  evidence/2026-10-20-batch18/T-108/project-map-merge-prep-01.txt \
  evidence/2026-10-20-batch18/T-108/merge-main-01.ipc-preview.summary.json
git diff --cached --check
git commit -m 'merge main into exec/t108 preserving questions hierarchy and flow'
git show --no-patch --format=full HEAD
print -r -- "Merge evidence: $MERGE_RUN"
