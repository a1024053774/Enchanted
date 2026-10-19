#!/bin/bash
set -euo pipefail
cd /Users/luckye/Documents/Code/a2a-wt-t103
stamp=$(date -u +%Y%m%dT%H%M%SZ)
/usr/bin/python3 -B evidence/2026-10-19-batch17/T-103/compare_startup.py \
  --output "/Volumes/WD-Elements/a2a-evidence/2026-10-19-batch17/T-103/startup-compare-$stamp"
