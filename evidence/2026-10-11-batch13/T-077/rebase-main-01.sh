#!/bin/bash
set -euo pipefail

# 主控 #101：在沙箱外执行。只操作本 worker worktree 的 exec/t077。
# 不 stash、不 reset、不 abort；冲突时保留进行中的 rebase。
cd /Users/luckye/Documents/Code/a2a-wt-t077
[[ "$(git branch --show-current)" == 'exec/t077' ]]
[[ "$(git rev-parse HEAD)" == '863e8b8afe272530b3c5bddc130a2d684f2a9b85' ]]
[[ "$(git rev-parse main)" == '7a1ecae84121b4dc43ddf79b595d6ff4917ab6c9' ]]
git diff --exit-code
git diff --cached --exit-code
git -C /Users/luckye/Documents/Code/a2a-wt-t077 rebase main
