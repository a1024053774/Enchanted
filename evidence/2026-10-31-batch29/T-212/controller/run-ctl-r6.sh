#!/bin/zsh
# T-212 第六轮主控复跑（最终候选）：尺寸错配、原画面、连续改尺寸各一次，
# trace 写入失败的 resize 与初次 attach 两种情况各一次；
# 再在临时副本里让 paint 处理不再捕获 trace 写入错误，确认 resize 情况会失败。
# 用法：zsh run-ctl-r6.sh   （结果写进本目录 r6-*，汇总在 r6-runs.log）
set -u
W=/Users/luckye/Documents/Code/a2a-worktrees/T-212
C=/Users/luckye/Documents/Code/a2a-worktrees/T-212-controller
export TMPDIR=/private/tmp
run() {
  local name=$1; shift
  print -r -- "== $name $(date +%T) $*" >> $C/r6-runs.log
  "$@" > $C/$name.log 2>&1
  print -r -- "== $name exit=$? $(date +%T)" >> $C/r6-runs.log
}
cd $W
run r6-mismatched-01 python3 workbench/tests/test_t212_shell_hc_e2e.py --electron-screen --mismatched-screen --output $C/r6-mismatched-01
run r6-screen-01 python3 workbench/tests/test_t212_shell_hc_e2e.py --electron-screen --output $C/r6-screen-01
run r6-burst-01 python3 workbench/tests/test_t212_shell_hc_e2e.py --electron-screen --resize-burst --output $C/r6-burst-01
run r6-trace-resize-01 python3 workbench/tests/test_t212_trace_failure_e2e.py --case resize --output $C/r6-trace-resize-01
run r6-trace-initial-01 python3 workbench/tests/test_t212_trace_failure_e2e.py --case initial --output $C/r6-trace-initial-01

# 两个变异，各在临时副本里只改 panes.ts 一处，再跑 trace 失败的 resize 情况，都应失败：
#   no-catch：paint 处理不再捕获 trace 写入错误（回到第五轮写法）；
#   no-check：resize 之后不再检查窗格是否已失败，照常返回重绘偏移。
mutant() {
  local name=$1 old=$2 new=$3
  local M=$(mktemp -d /private/tmp/t212-ctl-mutant-XXXXXX)
  mkdir -p $M/repo
  rsync -a --exclude node_modules $W/workbench $M/repo/
  ln -s $W/workbench/node_modules $M/repo/workbench/node_modules
  mkdir -p $M/hc-cache && cp $W/../hc-cache/herdr-core-0.1.15-macos-aarch64.tar.gz $M/hc-cache/
  OLD=$old NEW=$new python3 -I - $M/repo/workbench/src/panes.ts <<'PY'
import os, sys
p = sys.argv[1]; t = open(p, encoding='utf-8').read()
old, new = os.environ['OLD'], os.environ['NEW']
assert t.count(old) == 1, 'mutation anchor'
open(p, 'w', encoding='utf-8').write(t.replace(old, new))
PY
  diff -u $W/workbench/src/panes.ts $M/repo/workbench/src/panes.ts > $C/r6-mutant-$name.diff
  cd $M/repo
  run r6-mutant-$name-01 python3 workbench/tests/test_t212_trace_failure_e2e.py --case resize --output $C/r6-mutant-$name-01
  cd $W
  print -r -- "== r6-mutant-$name mutant copy kept at $M" >> $C/r6-runs.log
}
mutant no-catch '      try {
        const offset = statSync(trace).size;
        appendFileSync(trace, "\x1bc");
        pane.shellPaintOffset = offset;
      } catch (error) { this.recordFailure(pane, "trace_write_failed", error); }' '      pane.shellPaintOffset = statSync(trace).size;
      appendFileSync(trace, "\x1bc");'
mutant no-check '      await pane.pty.resize(cols, rows);
      check(!pane.failed, "pane_unavailable");' '      await pane.pty.resize(cols, rows);'
print -r -- "== all done $(date +%T)" >> $C/r6-runs.log
