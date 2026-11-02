#!/bin/bash
# T-237 相关回归：复盘端到端（T-136）、复盘到点计算单元测试（T-223）。
cd "$(dirname "$0")/../../.."
E=evidence/2026-11-02-batch30/T-237
export ENCHANTED_HC_CACHE_DIR="$(pwd)/../hc-cache"
for z in America/New_York America/Nuuk America/Scoresbysund; do n=$(echo $z | tr / -); TZ=$z TMPDIR=/private/tmp node workbench/tests/test_t223_retrospective_due.ts . $E/reg-t223-$n.json $z > $E/reg-t223-$n.log 2>&1; echo "t223 $z exit $?"; done
python3 workbench/tests/test_t136_retrospective_e2e.py --summary $E/reg-t136.json | tail -1 | cut -c1-300
pgrep -fl /private/tmp/t136- || echo "no t136 fixture processes"
