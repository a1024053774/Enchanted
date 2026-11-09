# 仅由主控在沙箱外逐条运行。worker 本轮未启动应用、后台、ps 或构建。
# 外层 cwd：/Users/luckye/Library/Application Support/a2a-orchestrator/worktrees/a2a/T-262-1-a2
# 本次 attempt：64d48cf7-0cfc-4078-8a13-6f0067297990，fence 2，spec_rev 2。
# 旧 controller-runs-04.command / RESTART-HANDOFF-04.md 只留作历史，不再执行。
# 第一条应完成两个业务断言并 FAIL，选择事件应为 input/change；INCOMPLETE 不算红态检出。
# 第二条无 --smoke，要求完整场景 PASS；随后四个变异逐条执行，各应业务 FAIL / 非零。
# 不要整文件一口气执行或并发启动。先核对前一条退出码、摘要、cleanup.removed、core_cleanup 和诊断。
# 每轮采用独立夹具与标准构建，不操作 T-249 的窗口或其他现有 Test App。
# 摘要与 diagnostics 已存在时换新编号，禁止覆盖。JSON 及同名 .diagnostics.jsonl 一起保留。
# 原生 select 键盘另由主控 Computer Use 验收；脚本只证明标准表单选择，details 仍用真实 Enter。
env -u A2A_REQUEST_DIR /usr/bin/python3 workbench/tests/test_t262_records_e2e.py --revision f80d5cdbf0e1b62de864300eff7bb4497f8c4c70 --smoke --summary '/Users/luckye/Documents/Code/a2a/evidence/2026-11-08-batch34/T-262/controller/red-outside-05.json'
env -u A2A_REQUEST_DIR /usr/bin/python3 workbench/tests/test_t262_records_e2e.py --summary '/Users/luckye/Documents/Code/a2a/evidence/2026-11-08-batch34/T-262/controller/green-outside-02.json'
env -u A2A_REQUEST_DIR /usr/bin/python3 workbench/tests/test_t262_records_e2e.py --mutant no-sort --summary '/Users/luckye/Documents/Code/a2a/evidence/2026-11-08-batch34/T-262/controller/mutant-no-sort-02.json'
env -u A2A_REQUEST_DIR /usr/bin/python3 workbench/tests/test_t262_records_e2e.py --mutant receipt-task --summary '/Users/luckye/Documents/Code/a2a/evidence/2026-11-08-batch34/T-262/controller/mutant-receipt-task-02.json'
env -u A2A_REQUEST_DIR /usr/bin/python3 workbench/tests/test_t262_records_e2e.py --mutant ignore-session --summary '/Users/luckye/Documents/Code/a2a/evidence/2026-11-08-batch34/T-262/controller/mutant-ignore-session-02.json'
env -u A2A_REQUEST_DIR /usr/bin/python3 workbench/tests/test_t262_records_e2e.py --mutant no-full-receipt --summary '/Users/luckye/Documents/Code/a2a/evidence/2026-11-08-batch34/T-262/controller/mutant-no-full-receipt-02.json'
