#!/bin/zsh
# 起点两项 PASS 且 worker 已应用抽取补丁后运行。
set -eu
cd /Users/luckye/Documents/Code/a2a-wt-t089
python3 -B evidence/2026-10-16-batch16/T-089/check_s3.py candidate --rebased --output evidence/2026-10-16-batch16/T-089/s3-rebased-candidate-01
python3 -B evidence/2026-10-16-batch16/T-089/check_s3_archive.py candidate --output evidence/2026-10-16-batch16/T-089/s3-archive-candidate-01.json
# 只归档本票的新验证输出；仓库只留 check.json 摘要与清单。
python3 -B workbench/tests/archive_evidence.py evidence/2026-10-16-batch16/T-089 --timeout 120 --replay zsh evidence/2026-10-16-batch16/T-089/controller_s3_candidate.sh
