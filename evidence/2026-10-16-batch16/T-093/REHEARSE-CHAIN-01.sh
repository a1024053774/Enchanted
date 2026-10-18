#!/bin/bash
# 沙箱外使用；exec 后全部长期进程仍受各自的单层 OS profile 约束。
# primary 故意在两个 hook/Stop 完成后抛错；green 不注入错误。
set -eu
repo=${1:?usage: script REPO FULL_FROZEN_SHA NEW_OUTPUT_JSON primary|green}
candidate=${2:?full frozen source revision required}
output=${3:?new output file under /private/tmp required}
rehearsal=${4:?primary or green required}
case "$rehearsal" in primary|green) ;; *) exit 2 ;; esac
exec /usr/bin/python3 -I -S -B "$repo/workbench/tests/run_t093_login_chain.py" \
  --source-revision "$candidate" --output "$output" --rehearsal "$rehearsal"
