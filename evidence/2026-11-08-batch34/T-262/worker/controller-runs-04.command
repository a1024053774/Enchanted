# 主控在沙箱外逐条执行；worker 未执行这些真实入口命令。
# 外层 cwd：/Users/luckye/Library/Application Support/a2a-orchestrator/worktrees/a2a/T-262-1-a1
# 第一条核对修正后的真实键盘驱动：父版排序/筛选应 FAIL，驱动环境错误仍为 INCOMPLETE。
# 第二条为候选完整验收，只有该条全绿后再逐条执行其余四个变异。
env -u A2A_REQUEST_DIR /usr/bin/python3 workbench/tests/test_t262_records_e2e.py --revision f80d5cdbf0e1b62de864300eff7bb4497f8c4c70 --smoke --summary /Users/luckye/Documents/Code/a2a/evidence/2026-11-08-batch34/T-262/controller/red-outside-04.json
env -u A2A_REQUEST_DIR /usr/bin/python3 workbench/tests/test_t262_records_e2e.py --summary /Users/luckye/Documents/Code/a2a/evidence/2026-11-08-batch34/T-262/controller/green-outside-01.json
env -u A2A_REQUEST_DIR /usr/bin/python3 workbench/tests/test_t262_records_e2e.py --mutant no-sort --summary /Users/luckye/Documents/Code/a2a/evidence/2026-11-08-batch34/T-262/controller/mutant-no-sort-01.json
env -u A2A_REQUEST_DIR /usr/bin/python3 workbench/tests/test_t262_records_e2e.py --mutant receipt-task --summary /Users/luckye/Documents/Code/a2a/evidence/2026-11-08-batch34/T-262/controller/mutant-receipt-task-01.json
env -u A2A_REQUEST_DIR /usr/bin/python3 workbench/tests/test_t262_records_e2e.py --mutant ignore-session --summary /Users/luckye/Documents/Code/a2a/evidence/2026-11-08-batch34/T-262/controller/mutant-ignore-session-01.json
env -u A2A_REQUEST_DIR /usr/bin/python3 workbench/tests/test_t262_records_e2e.py --mutant no-full-receipt --summary /Users/luckye/Documents/Code/a2a/evidence/2026-11-08-batch34/T-262/controller/mutant-no-full-receipt-01.json
