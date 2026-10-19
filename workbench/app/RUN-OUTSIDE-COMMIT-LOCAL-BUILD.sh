#!/bin/bash
# 主控确认本轮真实打包成功后运行；使用当前 worker 的原启动绑定，不手写尾注。
set -euo pipefail
cd /Users/luckye/Documents/Code/a2a-wt-t102
test "$(git branch --show-current)" = exec/t102
test "$(git rev-parse HEAD)" = 1f5856f2b9826188fd918c4340951154313ff580
git diff --cached --quiet
git diff --check
export A2A_PROJECT=a2a A2A_TASK=T-102 A2A_ATTEMPT=a2 A2A_ROLE=worker
export A2A_SESSION=f6caedda-1ea1-4345-84df-efc8e4ed1d94
export A2A_LAUNCH=launch-8343ffbef3274434ab0d956e8c0beb80
export A2A_LAUNCHES=/Users/luckye/Documents/Code/a2a/records/launches.jsonl
export CODEX_THREAD_ID=01a15354-f762-73e3-aa78-c8c1c909260e
export GIT_CONFIG_COUNT=1 GIT_CONFIG_KEY_0=core.hooksPath
export GIT_CONFIG_VALUE_0=/Users/luckye/Documents/Code/a2a/scripts/git-hooks
git add --sparse -- \
  workbench/.npmrc workbench/README.md workbench/check-cache.mjs \
  workbench/package.json workbench/package-lock.json \
  workbench/app/build.mjs workbench/app/package.mjs \
  workbench/app/RUN-OUTSIDE-LOCAL-PACKAGE.sh \
  workbench/app/RUN-OUTSIDE-COMMIT-LOCAL-BUILD.sh \
  workbench/tests/test_install_cache.mjs
git diff --cached --check
git commit -m 'build(T-102): build locally and clean packaging intermediates'
git log -1 --format=fuller
git status --short --branch
python3 /Users/luckye/Documents/SKILLS/project-map-skill/project-map/scripts/project_map.py status --root .
