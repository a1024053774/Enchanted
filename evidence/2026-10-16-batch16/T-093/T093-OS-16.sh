#!/bin/bash
# 主控沙箱外逐场执行；只用合成 auth、编译假 CLI、本地假 U:443。
# 无真实供应商 CLI、真实上游或模型；每个输出均须全新。
set -eu
mode=${1:?MODE REPO FULL_FROZEN_SHA NEW_OUTPUT [RESULTS...]}
repo=${2:?repo};candidate=${3:?candidate};output=${4:?new output}
case "$mode" in
 compile)
  exec /usr/bin/python3 -I -S -B "$repo/evidence/2026-10-16-batch16/T-093/compile-profiles-16.py" --source "$repo" --candidate "$candidate" --output "$output";;
 primary|green)
  exec /usr/bin/python3 -I -S -B "$repo/workbench/tests/run_t093_login_chain.py" --source-revision "$candidate" --output "$output" --rehearsal "$mode";;
 none|home-references-empty|scanner-zero|counts-always-match|drop-first-record|empty-credential-cases)
  exec /usr/bin/python3 -I -S -B "$repo/workbench/tests/run_t093_login_chain.py" --source-revision "$candidate" --output "$output" --mutation "$mode";;
 verify-six|verify-rehearsal|verify-counts)
  shift 4
  set -- --output "$output" "$@"
  case "$mode" in verify-rehearsal) set -- --rehearsal "$@";;verify-counts) set -- --counts-only "$@";;esac
  exec /usr/bin/python3 -I -S -B "$repo/workbench/tests/check_t093_chain_results.py" --candidate "$candidate" "$@";;
 *) echo 'unknown T093 OS verification mode' >&2;exit 2;;
esac
