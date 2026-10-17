#!/bin/zsh
# 主控运行；不卸载外置盘，不接触真实已提交的历史批次。
set -eu
cd /Users/luckye/Documents/Code/a2a-wt-t089
python3 -B workbench/tests/run_evidence_archive_checks.py --external --output evidence/2026-10-16-batch16/T-089/external-checks-01.json
python3 -B evidence/2026-10-16-batch16/T-089/replay_t086.py --external --output evidence/2026-10-16-batch16/T-089/t086-external-01.json
