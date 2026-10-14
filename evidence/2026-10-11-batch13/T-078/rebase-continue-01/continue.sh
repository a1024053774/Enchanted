#!/bin/bash
set -euo pipefail
cd /Users/luckye/Documents/Code/a2a-wt-t078
base=evidence/2026-10-11-batch13/T-078/rebase-continue-01
# Fixed HEAD/REBASE_HEAD, exact six unmerged paths, frozen resolved bytes,
# no conflict markers, and syntax checks must all pass before staging.
python3 -B "$base/check.py"
mkdir "$base/execution"
git add -- workbench/src/daemon.ts workbench/src/gates/core.ts workbench/src/panes.ts workbench/src/relay.ts workbench/src/store.ts workbench/tests/daemon_acceptance_host.ts
# Use the same non-session-hook environment as the controller's initial rebase.
# Do not install/disable hooks, auto-resolve the next stop, skip, abort or clean.
if git -c core.editor=true rebase --continue > "$base/execution/stdout.txt" 2> "$base/execution/stderr.txt"; then
  printf 'PASS: all remaining commits replayed\n' > "$base/execution/status.txt"
else
  printf 'INCOMPLETE: replay stopped; retain the next conflict state\n' > "$base/execution/status.txt"
fi
git rev-parse HEAD > "$base/execution/head.txt"
git rev-parse -q --verify REBASE_HEAD > "$base/execution/rebase-head.txt" || test ! -d "$(git rev-parse --git-path rebase-merge)"
git diff --name-only --diff-filter=U > "$base/execution/conflicts.txt"
git status --porcelain=v1 > "$base/execution/worktree-status.txt"
cat "$base/execution/status.txt" "$base/execution/conflicts.txt"
