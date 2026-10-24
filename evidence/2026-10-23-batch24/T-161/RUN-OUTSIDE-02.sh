#!/bin/zsh
set -u
# 修正受控 PTY 的 hook envelope 和回合完成等待；原缺陷断言保持不变。
cd /Users/luckye/Documents/Code/a2a-wt-t161 || exit 2
stamp=$(date -u +%Y%m%dT%H%M%SZ)
out="evidence/2026-10-23-batch24/T-161/red02-${stamp}"
python3 workbench/tests/test_t161_readonly_role_e2e.py --revision 3c56f743f --summary "${out}.json" > "${out}.log" 2>&1
result=$?
print "exit=${result} summary=${out}.json log=${out}.log"
exit "$result"
