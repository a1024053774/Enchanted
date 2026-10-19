#!/bin/bash
# 主控在沙箱外执行；不读取 auth，不启动供应商 CLI，不连接真实上游。
set -eu
repo=${1:?usage: script REPO FULL_FROZEN_SHA NEW_OUTPUT_JSON}
candidate=${2:?full frozen SHA required}
output=${3:?new output path under /private/tmp required}
actual=$(git -C "$repo" rev-parse HEAD)
if [ "$actual" != "$candidate" ]; then
  echo 'INCOMPLETE: The source revision does not match the frozen revision.' >&2
  exit 2
fi
git -C "$repo" diff --quiet HEAD -- \
  workbench/tests/probe_t093_parallel_profiles.py \
  workbench/tests/t093_profile_endpoint.mjs \
  workbench/tests/probe_t093_parent_sandbox.py \
  workbench/src/claudeLoginFiles.py
exec /usr/bin/python3 -I -S -B "$repo/workbench/tests/probe_t093_parallel_profiles.py" \
  --output "$output" --source-revision "$candidate"
