#!/bin/zsh
set -euo pipefail

TASK_ROOT=/Users/luckye/Documents/Code/a2a-wt-t115
cd "$TASK_ROOT"
unset GIT_DIR GIT_WORK_TREE GIT_COMMON_DIR GIT_INDEX_FILE
export LC_ALL=C

test "$(git branch --show-current)" = "exec/t115" || {
  print -u2 -- "Expected branch exec/t115"
  exit 2
}
if ! git diff --cached --quiet; then
  print -u2 -- "Refusing to commit: the index already contains staged changes"
  exit 2
fi

files=(
  evidence/2026-10-20-batch18/T-115/RESULTS.md
  evidence/2026-10-20-batch18/T-115/RUN-OUTSIDE-REPEAT-01.sh
  evidence/2026-10-20-batch18/T-115/RUN-OUTSIDE-COMMIT-01.sh
)
for file in "${files[@]}"; do
  test -f "$file" || {
    print -u2 -- "Missing expected file: $file"
    exit 2
  }
done

git add --sparse "${files[@]}"

expected=$(printf '%s\n' "${files[@]}" | sort)
actual=$(git diff --cached --name-only | sort)
test "$actual" = "$expected" || {
  print -u2 -- "Refusing to commit: staged paths differ from the T-115 evidence allowlist"
  print -u2 -- "$actual"
  exit 2
}

git diff --cached --check
git commit -m "evidence: add T-115 repeated foreground badge probe"
git status --short --branch
