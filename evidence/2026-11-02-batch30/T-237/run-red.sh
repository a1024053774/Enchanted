#!/bin/bash
# T-237 红态：修前基线与已知坏实现，各跑一次。
cd "$(dirname "$0")/../../.."
E=evidence/2026-11-02-batch30/T-237
python3 workbench/tests/test_t237_retrospective_end_e2e.py --summary $E/red-baseline.json --revision 2b3b12dac | tail -1
for m in no-end-check no-grace gone-is-running end-before-import; do
  python3 workbench/tests/test_t237_retrospective_end_e2e.py --summary $E/red-$m.json --mutant $m | tail -1
done
pgrep -fl /private/tmp/t237- || echo "no fixture processes left"
