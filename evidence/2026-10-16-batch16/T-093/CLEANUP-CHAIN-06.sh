#!/bin/bash
# 只清理主控 #98/#100 指定的 source-home 残留，不读取认证正文。
set -eu
repo=${1:?usage: script REPO NEW_OUTPUT_JSON}
output=${2:?new output file directly under /private/tmp required}
exec /usr/bin/python3 -I -S -B "$repo/workbench/tests/cleanup_t093_retained_fixture.py" \
  --root /private/tmp/t093-chain-e189ndt0 --output "$output"
