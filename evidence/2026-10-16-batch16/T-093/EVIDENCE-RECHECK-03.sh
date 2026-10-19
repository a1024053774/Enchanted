#!/bin/bash
# 一次只执行一个受保护场景；exec 后不保留无保护的脚本监督进程。
# 仅合成凭据、编译夹具和本地假上游。没有供应商 CLI 或模型回合。
set -eu
repo=${1:?usage: script REPO FULL_FROZEN_SHA NEW_OUTPUT_JSON MUTATION}
candidate=${2:?full frozen source revision required}
output=${3:?new output file under /private/tmp required}
mutation=${4:-none}
exec /usr/bin/python3 -I -S -B "$repo/workbench/tests/run_t093_login_chain.py" \
  --source-revision "$candidate" --output "$output" --mutation "$mutation"
