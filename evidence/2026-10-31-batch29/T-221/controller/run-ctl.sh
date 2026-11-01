#!/bin/zsh
# T-221 主控独立复跑：日期扫描单测、固定日历时钟检查及其固定偏移变异、T-136/T-137 完整 E2E。
# 用法：zsh run-ctl.sh   （结果写进本目录，汇总在 runs.log）
set -u
W=/Users/luckye/Documents/Code/a2a-worktrees/T-221
C=/Users/luckye/Documents/Code/a2a-worktrees/T-221-controller
export TMPDIR=/private/tmp
run() {
  local name=$1; shift
  print -r -- "== $name $(date +%T) $*" >> $C/runs.log
  "$@" > $C/$name.log 2>&1
  print -r -- "== $name exit=$? $(date +%T)" >> $C/runs.log
}
cd $W
TZ=America/New_York run scan-days node workbench/tests/test_t221_codex_scan_days.ts . $C/scan-days.json
cd $W/workbench/tests
run calendar-clocks python3 test_t221_calendar_clocks.py

# 变异：测试时钟退回无参数 astimezone()（固定偏移），应有四组夏令时用例失败。
M=$(mktemp -d /private/tmp/t221-ctl-mutant-XXXXXX)
cp local_calendar.py test_t221_calendar_clocks.py $M/
python3 -I - $M/local_calendar.py <<'PY'
import sys
p = sys.argv[1]; t = open(p, encoding='utf-8').read()
old = 'return datetime.now(ZoneInfo(name))'
assert t.count(old) == 1, 'mutation anchor'
open(p, 'w', encoding='utf-8').write(t.replace(old, 'return datetime.now().astimezone()'))
PY
diff -u local_calendar.py $M/local_calendar.py > $C/mutant-fixed-offset.diff
cd $M
run mutant-fixed-offset python3 test_t221_calendar_clocks.py
cd $W
rm -rf $M

run t136 python3 workbench/tests/test_t136_retrospective_e2e.py --summary $C/t136.json
run t137 python3 workbench/tests/test_t137_reflect_e2e.py --summary $C/t137.json
print -r -- "== all done $(date +%T)" >> $C/runs.log
