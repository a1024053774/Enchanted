#!/bin/zsh
# T-223 主控复跑：候选绿态、完整基线红态、主控自己的变异（回退一周改用固定 168 小时毫秒减法），
# 以及 T-136、T-137 当前日期端到端。用法：zsh run-ctl.sh（结果写进本目录，汇总在 runs.log）
set -u
W=/Users/luckye/Documents/Code/a2a-worktrees/T-223
C=/Users/luckye/Documents/Code/a2a-worktrees/T-223-controller
BASE=76f969963f6ee582460d357c317cb30b203bebe6
export TMPDIR=/private/tmp
run() {
  local name=$1; shift
  print -r -- "== $name $(date +%T) $*" >> $C/runs.log
  "$@" > $C/$name.log 2>&1
  print -r -- "== $name exit=$? $(date +%T)" >> $C/runs.log
}
cd $W
TZ=America/New_York run green node workbench/tests/test_t223_retrospective_due.ts . $C/green.json
# 基线：从完整基线导出 workbench/src，用候选里的同一份测试去测。
B=$(mktemp -d /private/tmp/t223-ctl-base-XXXXXX)
git archive $BASE workbench/src | tar -x -C $B
print -r -- "== base copy at $B" >> $C/runs.log
TZ=America/New_York run base-red node workbench/tests/test_t223_retrospective_due.ts $B $C/base-red.json
# 变异：回退一周不用 setDate/setHours，改成减去 7×24 小时的毫秒数。
M=$(mktemp -d /private/tmp/t223-ctl-mutant-XXXXXX)
mkdir -p $M/workbench && cp -R $W/workbench/src $M/workbench/
python3 -I - $M/workbench/src/retrospective.ts <<'PY'
import sys
p = sys.argv[1]; t = open(p, encoding='utf-8').read()
old = '''      slot.setDate(slot.getDate() - 7);
      slot.setHours(schedule.hour, schedule.minute, 0, 0);'''
new = '''      slot.setTime(slot.getTime() - 7 * 24 * 60 * 60 * 1000);'''
assert t.count(old) == 1, 'mutation anchor'
open(p, 'w', encoding='utf-8').write(t.replace(old, new))
PY
diff -u $W/workbench/src/retrospective.ts $M/workbench/src/retrospective.ts > $C/mutant-fixed-168h.diff
print -r -- "== mutant copy at $M" >> $C/runs.log
TZ=America/New_York run mutant-fixed-168h node workbench/tests/test_t223_retrospective_due.ts $M $C/mutant-fixed-168h.json
run t136 python3 workbench/tests/test_t136_retrospective_e2e.py --summary $C/t136-summary.json
run t137 python3 workbench/tests/test_t137_reflect_e2e.py --summary $C/t137-summary.json
print -r -- "== all done $(date +%T)" >> $C/runs.log
