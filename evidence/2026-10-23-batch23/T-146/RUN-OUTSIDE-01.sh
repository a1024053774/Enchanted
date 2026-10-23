#!/bin/zsh
set -u
cd /Users/luckye/Documents/Code/a2a-wt-t146 || exit 1
OUT="evidence/2026-10-23-batch23/T-146/outside-$(date -u +%Y%m%dT%H%M%SZ)-$$"
mkdir "$OUT" || exit 1
python3 workbench/tests/test_t146_session_state_e2e.py --revision ebbae7bd0 --summary "$OUT/red.json" > "$OUT/red.log" 2>&1
RED_RC=$?
print -r -- "修前退出码=$RED_RC；summary=$OUT/red.json；log=$OUT/red.log"
# 独立记录既有回归。修复与展示规则尚待裁定，此处不将修前失败算作产品红态。
node workbench/tests/test_t111_flow.mjs "$OUT/t111.json" . > "$OUT/t111.log" 2>&1
FLOW_RC=$?
python3 workbench/tests/test_t137_reflect_e2e.py --summary "$OUT/t137.json" > "$OUT/t137.log" 2>&1
REFLECT_RC=$?
print -r -- "T-111=$FLOW_RC T-137=$REFLECT_RC；证据目录=$OUT"
print -r -- "请回传 red.json 的 observed/error 与回归结果；真实 fixture 留在 summary.fixture 指向的 /private/tmp 目录。"
# 此脚本用于收集待裁定前的证据，缺陷红态须由具体断言与 DOM 观察确认。
exit 0
