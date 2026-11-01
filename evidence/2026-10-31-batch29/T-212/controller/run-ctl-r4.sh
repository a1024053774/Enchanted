#!/bin/zsh
# T-212 第四轮主控复跑：最终候选的尺寸错配与原画面场景，各一次；
# 再在临时副本里去掉 resize 后的重新 attach，确认尺寸错配场景会失败。
# 用法：zsh run-ctl-r4.sh   （结果写进本目录 r4-*，汇总在 r4-runs.log）
set -u
W=/Users/luckye/Documents/Code/a2a-worktrees/T-212
C=/Users/luckye/Documents/Code/a2a-worktrees/T-212-controller
export TMPDIR=/private/tmp
run() {
  local name=$1; shift
  print -r -- "== $name $(date +%T) $*" >> $C/r4-runs.log
  "$@" > $C/$name.log 2>&1
  print -r -- "== $name exit=$? $(date +%T)" >> $C/r4-runs.log
}
cd $W
run r4-mismatched-01 python3 workbench/tests/test_t212_shell_hc_e2e.py --electron-screen --mismatched-screen --output $C/r4-mismatched-01
run r4-screen-01 python3 workbench/tests/test_t212_shell_hc_e2e.py --electron-screen --output $C/r4-screen-01

# 变异：hc.ts 的 resize 只发 RESIZE，不重新 attach（回到第三轮的行为）。
M=$(mktemp -d /private/tmp/t212-ctl-mutant-XXXXXX)
mkdir -p $M/repo
rsync -a --exclude node_modules $W/workbench $M/repo/
ln -s $W/workbench/node_modules $M/repo/workbench/node_modules
mkdir -p $M/hc-cache && cp $W/../hc-cache/herdr-core-0.1.15-macos-aarch64.tar.gz $M/hc-cache/
python3 -I - $M/repo/workbench/src/hc.ts <<'PY'
import sys
p = sys.argv[1]; t = open(p, encoding='utf-8').read()
old = '    await this.attach();\n  }\n  async kill()'
assert t.count(old) == 1, 'mutation anchor'
open(p, 'w', encoding='utf-8').write(t.replace(old, '  }\n  async kill()'))
PY
diff -u $W/workbench/src/hc.ts $M/repo/workbench/src/hc.ts > $C/r4-mutant-no-reattach.diff
cd $M/repo
run r4-mutant-no-reattach-01 python3 workbench/tests/test_t212_shell_hc_e2e.py --electron-screen --mismatched-screen --output $C/r4-mutant-no-reattach-01
cd $C
rm -rf $M
print -r -- "== all done $(date +%T)" >> $C/r4-runs.log
