#!/bin/zsh
# 主控 #2 已裁定组合基线；仅基线通过后，worker 才应用抽取补丁。
set -eu
cd /Users/luckye/Documents/Code/a2a-wt-t089
python3 -B evidence/2026-10-16-batch16/T-089/check_s3.py baseline --rebased --output evidence/2026-10-16-batch16/T-089/s3-rebased-baseline-01
python3 -B evidence/2026-10-16-batch16/T-089/check_s3_archive.py baseline --output evidence/2026-10-16-batch16/T-089/s3-archive-baseline-01.json
