#!/bin/bash
# 主控在沙箱外执行已授权的合并；保留冲突，不提交、不 push、不 rebase。
set -eu
repo=/Users/luckye/Documents/Code/a2a-wt-t093
cd "$repo"
test "$(git branch --show-current)" = exec/t093
test "$(git rev-parse HEAD)" = 630291ca7a07086d231e38a15fe1f1c9e6411bf0
git diff --quiet
git diff --cached --quiet
test ! -f "$(git rev-parse --git-path MERGE_HEAD)"
set +e
git merge --no-commit --no-ff 0e92f78ec6824265cdfcbb9387ba4b454d7eee7f
result=$?
set -e
git status --short
git diff --name-only --diff-filter=U
exit "$result"
