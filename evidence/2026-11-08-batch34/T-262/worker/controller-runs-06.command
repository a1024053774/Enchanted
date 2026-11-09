# 主控 #104：父版 red-outside-05 与候选 green-outside-02 已运行，禁止重跑或覆盖。
# 本轮只由主控在沙箱外逐条执行下列完整候选及四个变异，不并发启动。
# 外层 cwd：/Users/luckye/Library/Application Support/a2a-orchestrator/worktrees/a2a/T-262-1-a2
# attempt：64d48cf7-0cfc-4078-8a13-6f0067297990；fence 2；spec_rev 2。
# 先要求完整候选 PASS，再逐条运行四个变异（各需业务 FAIL / 非零）。
# 确认 native_window 含原生 900x700 尺寸、窗口/进程身份和内容尺寸读回。
# INCOMPLETE 不是业务检出；逐条保存退出码、摘要、diagnostics，并核对 cleanup.removed / core_cleanup。
# 已有输出就换新编号，不能覆盖。原生 select 键盘仍由主控另做 Computer Use。
env -u A2A_REQUEST_DIR /usr/bin/python3 workbench/tests/test_t262_records_e2e.py --summary '/Users/luckye/Documents/Code/a2a/evidence/2026-11-08-batch34/T-262/controller/green-outside-03.json'
env -u A2A_REQUEST_DIR /usr/bin/python3 workbench/tests/test_t262_records_e2e.py --mutant no-sort --summary '/Users/luckye/Documents/Code/a2a/evidence/2026-11-08-batch34/T-262/controller/mutant-no-sort-03.json'
env -u A2A_REQUEST_DIR /usr/bin/python3 workbench/tests/test_t262_records_e2e.py --mutant receipt-task --summary '/Users/luckye/Documents/Code/a2a/evidence/2026-11-08-batch34/T-262/controller/mutant-receipt-task-03.json'
env -u A2A_REQUEST_DIR /usr/bin/python3 workbench/tests/test_t262_records_e2e.py --mutant ignore-session --summary '/Users/luckye/Documents/Code/a2a/evidence/2026-11-08-batch34/T-262/controller/mutant-ignore-session-03.json'
env -u A2A_REQUEST_DIR /usr/bin/python3 workbench/tests/test_t262_records_e2e.py --mutant no-full-receipt --summary '/Users/luckye/Documents/Code/a2a/evidence/2026-11-08-batch34/T-262/controller/mutant-no-full-receipt-03.json'
