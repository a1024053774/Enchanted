#!/bin/zsh
# T-223 第三轮主控复跑。三组时区各自显式设定 TZ：
#   green       当前候选；
#   base-red    完整基线 76f969963 导出的 workbench/src；
#   round2-red  基线导出，换上审查目录里冻结的第二轮 retrospective.ts（已知坏实现）；
#   mutant-slot-rollback  主控变异：回退一周改为从已构造的 slot 的日期减 7，而不是从数字日期减；
# 再跑主控的 Nuuk 探针、T-136、T-137 当前日期端到端。
# 用法：zsh run-ctl-r3.sh（结果写进本目录 r3/，汇总在 r3/runs.log）
set -u
W=/Users/luckye/Documents/Code/a2a-worktrees/T-223
C=/Users/luckye/Documents/Code/a2a-worktrees/T-223-controller
O=$C/r3
R2=/Users/luckye/Documents/Code/a2a-review/T-223-r1/candidate/workbench/src/retrospective.ts
BASE=76f969963f6ee582460d357c317cb30b203bebe6
ZONES=(America/New_York America/Nuuk America/Scoresbysund)
export TMPDIR=/private/tmp
mkdir -p $O
run() {
  local name=$1; shift
  print -r -- "== $name $(date +%T) $*" >> $O/runs.log
  "$@" > $O/$name.log 2>&1
  print -r -- "== $name exit=$? $(date +%T)" >> $O/runs.log
}
due_all() {
  local label=$1 product=$2 zone
  for zone in $ZONES; do
    TZ=$zone run $label-${zone:t} node $W/workbench/tests/test_t223_retrospective_due.ts $product $O/$label-${zone:t}.json $zone
  done
}
cd $W
due_all green .
B=$(mktemp -d /private/tmp/t223-ctl3-base-XXXXXX)
git archive $BASE workbench/src | tar -x -C $B
print -r -- "== base copy at $B" >> $O/runs.log
due_all base-red $B
K=$(mktemp -d /private/tmp/t223-ctl3-round2-XXXXXX)
git archive $BASE workbench/src | tar -x -C $K
cp $R2 $K/workbench/src/retrospective.ts
print -r -- "== round2 copy at $K" >> $O/runs.log
due_all round2-red $K
M=$(mktemp -d /private/tmp/t223-ctl3-mutant-XXXXXX)
mkdir -p $M/workbench && cp -R $W/workbench/src $M/workbench/
python3 -I - $M/workbench/src/retrospective.ts <<'PY'
import sys
p = sys.argv[1]; t = open(p, encoding='utf-8').read()
old = 'if (slot > now) slot = new Date(year, month, day - 7, schedule.hour, schedule.minute, 0, 0);'
new = 'if (slot > now) slot = new Date(slot.getFullYear(), slot.getMonth(), slot.getDate() - 7, schedule.hour, schedule.minute, 0, 0);'
assert t.count(old) == 1, 'mutation anchor'
open(p, 'w', encoding='utf-8').write(t.replace(old, new))
PY
diff -u $W/workbench/src/retrospective.ts $M/workbench/src/retrospective.ts > $O/mutant-slot-rollback.diff
print -r -- "== mutant copy at $M" >> $O/runs.log
due_all mutant-slot-rollback $M
cd /private/tmp
TZ=America/Nuuk run nuuk-probe-candidate node $C/nuuk-probe.ts $W
cd $W
run t136 python3 workbench/tests/test_t136_retrospective_e2e.py --summary $O/t136-summary.json
run t137 python3 workbench/tests/test_t137_reflect_e2e.py --summary $O/t137-summary.json
print -r -- "== all done $(date +%T)" >> $O/runs.log
