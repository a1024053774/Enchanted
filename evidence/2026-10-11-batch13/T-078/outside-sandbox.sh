#!/bin/bash
set -eu
# Controller-run rebase only. The worker commits in its own session first.
task_root=/Users/luckye/Documents/Code/a2a-wt-t078
evidence_root=/Users/luckye/Documents/Code/a2a-wt-t078/evidence/2026-10-11-batch13/T-078
run_label="${1:-outside-rebase-01}"
cd "$task_root"
test -f "$evidence_root/$run_label/frozen-commit.json"
test ! -e "$evidence_root/$run_label/rebase.stdout.txt"
test ! -e "$evidence_root/$run_label/rebase.stderr.txt"
set +e
git -C /Users/luckye/Documents/Code/a2a-wt-t078 rebase main > "$evidence_root/$run_label/rebase.stdout.txt" 2> "$evidence_root/$run_label/rebase.stderr.txt"
rebase_exit=$?
set -e
python3 "$evidence_root/freeze_candidate.py" rebased "$run_label" "$rebase_exit"
# A conflict remains intact for the worker to resolve. No abort, retry or tests.
exit "$rebase_exit"
