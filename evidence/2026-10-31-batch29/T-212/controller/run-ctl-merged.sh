#!/bin/zsh
# T-212 合入 main 后（8006f37ea，含 T-221 对 panes.ts 的改动）复跑：
# T-221 按日扫描检查一次，T-212 最难的尺寸错配场景、连续改尺寸、trace 失败两种情况各一次。
# 用法：zsh run-ctl-merged.sh   （结果写进本目录 m-*，汇总在 m-runs.log）
set -u
M=/Users/luckye/Documents/Code/a2a
C=/Users/luckye/Documents/Code/a2a-worktrees/T-212-controller
export TMPDIR=/private/tmp
# main 不在 a2a-worktrees 下，默认的 ../../../hc-cache 不存在；指向已有的固定版本归档，不联网下载。
export ENCHANTED_HC_CACHE_DIR=/Users/luckye/Documents/Code/a2a-worktrees/hc-cache
run() {
  local name=$1; shift
  print -r -- "== $name $(date +%T) $*" >> $C/m-runs.log
  "$@" > $C/$name.log 2>&1
  print -r -- "== $name exit=$? $(date +%T)" >> $C/m-runs.log
}
cd $M
print -r -- "== head $(git rev-parse HEAD)" >> $C/m-runs.log
TZ=America/New_York run m-scan-days node workbench/tests/test_t221_codex_scan_days.ts . $C/m-scan-days.json
run m-mismatched-01 python3 workbench/tests/test_t212_shell_hc_e2e.py --electron-screen --mismatched-screen --output $C/m-mismatched-01
run m-burst-01 python3 workbench/tests/test_t212_shell_hc_e2e.py --electron-screen --resize-burst --output $C/m-burst-01
run m-trace-resize-01 python3 workbench/tests/test_t212_trace_failure_e2e.py --case resize --output $C/m-trace-resize-01
run m-trace-initial-01 python3 workbench/tests/test_t212_trace_failure_e2e.py --case initial --output $C/m-trace-initial-01
print -r -- "== all done $(date +%T)" >> $C/m-runs.log
