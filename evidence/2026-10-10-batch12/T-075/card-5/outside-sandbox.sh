#!/bin/bash
# T-075-5：入口红态 → 8/9/18 绿态 → CAS 补充 → 三个业务变异体。
set -euo pipefail
task_card_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
task_repo="$(cd -- "${task_card_dir}/../../../.." && pwd)"
cd -- "$task_repo"
exec python3 -B workbench/tests/run_daemon_acceptance.py --validation --label "${1:-outside-full-01}"
