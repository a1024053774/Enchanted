# 用户 #108：只由主控在沙箱外逐条执行；worker 不启动后台、窗口、ps 或构建。
# 外层 cwd：/Users/luckye/Library/Application Support/a2a-orchestrator/worktrees/a2a/T-262-1-a2
# attempt 64d48cf7-0cfc-4078-8a13-6f0067297990 / fence 2 / spec_rev 2。
# 父版 red-outside-05 已有有效排序/筛选红态，不重跑；保留 green-outside-03 的原 FAIL。
# 先要求新的完整候选 PASS，再逐条运行四个既有变异；各需业务 FAIL / 非零，INCOMPLETE 不算检出。
# navigation 记录每次 project_ready / records_ready 的真实页面与选中身份。
# 若失败，读 diagnostics.before_cleanup.page（或 page_capture_error），区分终端页/记录读取失败。
# 同时核对 native_window、transport、core_cleanup、cleanup.removed；保留退出码和同名 diagnostics。
# 不并发，不覆盖既有输出；如文件存在换新编号。原生 select 键盘 CU、独立审查仍由主控完成。
env -u A2A_REQUEST_DIR /usr/bin/python3 workbench/tests/test_t262_records_e2e.py --summary '/Users/luckye/Documents/Code/a2a/evidence/2026-11-08-batch34/T-262/controller/green-outside-04.json'
env -u A2A_REQUEST_DIR /usr/bin/python3 workbench/tests/test_t262_records_e2e.py --mutant no-sort --summary '/Users/luckye/Documents/Code/a2a/evidence/2026-11-08-batch34/T-262/controller/mutant-no-sort-04.json'
env -u A2A_REQUEST_DIR /usr/bin/python3 workbench/tests/test_t262_records_e2e.py --mutant receipt-task --summary '/Users/luckye/Documents/Code/a2a/evidence/2026-11-08-batch34/T-262/controller/mutant-receipt-task-04.json'
env -u A2A_REQUEST_DIR /usr/bin/python3 workbench/tests/test_t262_records_e2e.py --mutant ignore-session --summary '/Users/luckye/Documents/Code/a2a/evidence/2026-11-08-batch34/T-262/controller/mutant-ignore-session-04.json'
env -u A2A_REQUEST_DIR /usr/bin/python3 workbench/tests/test_t262_records_e2e.py --mutant no-full-receipt --summary '/Users/luckye/Documents/Code/a2a/evidence/2026-11-08-batch34/T-262/controller/mutant-no-full-receipt-04.json'
