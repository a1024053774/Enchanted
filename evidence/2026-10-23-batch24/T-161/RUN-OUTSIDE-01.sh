#!/bin/zsh
set -u
# 只运行隔离真实 Electron 红态；保留当前产品源码，禁止模型调用。
cd /Users/luckye/Documents/Code/a2a-wt-t161 || exit 2
stamp=$(date -u +%Y%m%dT%H%M%SZ)
out="evidence/2026-10-23-batch24/T-161/red-${stamp}"
python3 workbench/tests/test_t161_readonly_role_e2e.py --revision 3c56f743f --summary "${out}.json" > "${out}.log" 2>&1
result=$?
print "exit=${result} summary=${out}.json log=${out}.log"
exit "$result"
