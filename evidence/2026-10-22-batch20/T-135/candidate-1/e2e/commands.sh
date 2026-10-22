#!/bin/zsh
# T-135 candidate 1 (0383b3cb1), run from a clean detached worktree of that commit:
# git worktree add --detach /private/tmp/a2a-t135-c1b 0383b3cb1, with workbench/node_modules linked to the main checkout's.
# probe-green-01..02 were tries of the test while it was written (01 waited for a second turn end, which the gate's
# receipt turn reached first); kept as found.
set -u
W=/private/tmp/a2a-t135-c1b
E=/Users/luckye/Documents/Code/a2a/evidence/2026-10-22-batch20/T-135/candidate-1/e2e
T=$W/workbench/tests/test_t135_trajectory_archive_e2e.py
run() { local name=$1; shift; python3 "$@" --summary $E/$name.json > $E/$name.log 2>&1; echo "$name exit=$?" >> $E/exits.txt; }
run green $T &
run red-parent $T --revision e4d45c511 &
run mutant-partial-line-copied $T --mutant partial-line-copied &
wait
run mutant-not-incremental $T --mutant not-incremental &
run t122-green $W/workbench/tests/test_t122_claude_worker_e2e.py &
wait
