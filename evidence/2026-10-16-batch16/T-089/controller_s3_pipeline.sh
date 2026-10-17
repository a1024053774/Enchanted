#!/bin/zsh
# 主控 #2 已授权的完整 S3 流程；任何一步失败立即停止、保留现场。
set -eu
cd /Users/luckye/Documents/Code/a2a-wt-t089
zsh evidence/2026-10-16-batch16/T-089/controller_s3_baseline.sh
git apply --check evidence/2026-10-16-batch16/T-089/s3-extraction.patch
git apply evidence/2026-10-16-batch16/T-089/s3-extraction.patch
zsh evidence/2026-10-16-batch16/T-089/controller_s3_candidate.sh
