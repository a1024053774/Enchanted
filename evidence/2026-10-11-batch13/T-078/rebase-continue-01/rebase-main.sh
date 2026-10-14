#!/bin/bash
set -euo pipefail
cd /Users/luckye/Documents/Code/a2a-wt-t078
test "$(git branch --show-current)" = exec/t078
test -z "$(git status --porcelain=v1)" || { echo 'BLOCKED: worktree is dirty; no stash/reset/clean' >&2; exit 1; }
test ! -d "$(git rev-parse --git-path rebase-merge)" && test ! -d "$(git rev-parse --git-path rebase-apply)" || { echo 'BLOCKED: rebase already in progress' >&2; exit 1; }
before=$(git rev-parse HEAD)
target=$(git rev-parse main)
base=$(git merge-base "$before" "$target")
backup="backup/t078-before-09a3-main-${before:0:12}"
if git show-ref --verify --quiet "refs/heads/$backup"; then echo 'BLOCKED: backup already exists; retain it and inspect the earlier run' >&2; exit 1; fi
git branch "$backup" "$before"
log=$(mktemp -d /private/tmp/t078-rebase-09a3-XXXXXX)
printf '%s\n' "$before" > "$log/before.txt"
printf '%s\n' "$target" > "$log/target.txt"
printf '%s\n' "$base" > "$log/merge-base.txt"
printf '%s\n' "$backup" > "$log/backup-ref.txt"
git log --reverse --format='%H %s' "$base..$before" > "$log/before-commits.txt"
# Keep the caller's per-session hooks and identity. Do not change Git config,
# disable hooks, stash work, auto-resolve conflicts, or abort a failed rebase.
if git -c core.editor=true -c sequence.editor=true rebase "$target" > "$log/rebase.stdout.txt" 2> "$log/rebase.stderr.txt"; then
  git rev-parse HEAD > "$log/after.txt"
  git log --reverse --format='%H %s' "$target..HEAD" > "$log/after-commits.txt"
  printf 'PASS: rebase finished; log=%s backup=%s\n' "$log" "$backup"
else
  printf 'INCOMPLETE: rebase stopped; conflicts retained; log=%s backup=%s\n' "$log" "$backup"
  git diff --name-only --diff-filter=U > "$log/conflicts.txt"
  cat "$log/conflicts.txt"
fi
git status --porcelain=v1 > "$log/worktree-status.txt"
