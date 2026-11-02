#!/bin/bash
# T-237 第 2 轮：候选三次绿态、修前基线与变异红态、相关回归。在仓库根目录运行：bash evidence/2026-11-02-batch30/T-237/r2/run-all.sh
cd "$(dirname "$0")/../../../.."
E=evidence/2026-11-02-batch30/T-237/r2
T=workbench/tests/test_t237_retrospective_end_e2e.py
export TMPDIR=/private/tmp ENCHANTED_HC_CACHE_DIR="$(pwd)/../hc-cache"
for n in 1 2 3; do [ -e $E/green-$n.json ] || python3 $T --summary $E/green-$n.json | cut -c1-160; done
[ -e $E/red-baseline.json ] || python3 $T --revision 82e747f4a --summary $E/red-baseline.json | cut -c1-160
for m in no-end-check no-grace gone-is-running end-before-import missing-is-gone job-control-only unknown-not-recorded unknown-every-check no-recheck core-restart-unconfirmed ui-revert; do
  [ -e $E/red-$m.json ] || { echo "== $m"; python3 $T --mutant $m --summary $E/red-$m.json | python3 -c "import json,sys;r=json.loads(sys.stdin.read());print(r['status'],r.get('error','')[:200])"; }
done
for z in America/New_York America/Nuuk America/Scoresbysund; do n=$(echo $z | tr / -); TZ=$z node workbench/tests/test_t223_retrospective_due.ts . $E/reg-t223-$n.json $z > $E/reg-t223-$n.log 2>&1; echo "t223 $z exit $?"; done
python3 workbench/tests/test_t136_retrospective_e2e.py --summary $E/reg-t136.json | tail -1 | cut -c1-200
python3 workbench/tests/test_t212_shell_hc_e2e.py --output $E/reg-t212-shell.json > $E/reg-t212-shell.log 2>&1; echo "t212 shell exit $?"
python3 workbench/tests/test_t212_shell_hc_e2e.py --core-crash --output $E/reg-t212-core-crash.json > $E/reg-t212-core-crash.log 2>&1; echo "t212 core-crash exit $?"
pgrep -fl '/private/tmp/t237-|/private/tmp/t136-|/private/tmp/t212' || echo "no fixture processes left"
