#!/bin/zsh
# 主控 #5 的两项修复与真实入口补证；只向本票外置盘新目录写原始产物。
set -eu
cd /Users/luckye/Documents/Code/a2a-wt-t089
python3 -B workbench/tests/run_evidence_archive_checks.py --external --output evidence/2026-10-16-batch16/T-089/reclaim-external-green-01.json
python3 -B evidence/2026-10-16-batch16/T-089/check_s3_main.py --output evidence/2026-10-16-batch16/T-089/s3-main-02.json
python3 -B evidence/2026-10-16-batch16/T-089/replay_t086.py --external --output evidence/2026-10-16-batch16/T-089/t086-external-02.json
