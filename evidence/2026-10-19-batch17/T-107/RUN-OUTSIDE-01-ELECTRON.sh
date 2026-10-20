#!/bin/bash
# 主控在沙箱外运行；只使用隔离 fixture，不调用模型、不截图、不操作原生对话框。
set -euo pipefail
cd /Users/luckye/Documents/Code/a2a-wt-t107
label="${1:-electron-$(date +%Y%m%dT%H%M%S)}"
case "$label" in *[!A-Za-z0-9_-]*|'') exit 2 ;; esac
python3 workbench/tests/run_t107_sidebar.py \
  --source "$PWD" \
  --dependencies /Users/luckye/Documents/Code/a2a/workbench/node_modules \
  --electron-dist /Users/luckye/Documents/Code/a2a/workbench/node_modules/electron/dist \
  --summary "evidence/2026-10-19-batch17/T-107/$label-summary.json"
