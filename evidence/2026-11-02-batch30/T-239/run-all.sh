#!/bin/bash
# T-239 red/green set. Run from the repository root: bash evidence/2026-11-02-batch30/T-239/run-all.sh
set -u
E=evidence/2026-11-02-batch30/T-239
T=workbench/tests/test_t239_pane_invalid_utf8_e2e.py
export ENCHANTED_HC_CACHE_DIR=${ENCHANTED_HC_CACHE_DIR:-/Users/luckye/Documents/Code/hc-cache}
python3 $T --revision 635eb1bbc --summary $E/red-baseline.json
for m in fatal no-stream; do python3 $T --mutant $m --summary $E/red-$m.json; done
for i in 1 2 3; do python3 $T --summary $E/green-$i.json; done
