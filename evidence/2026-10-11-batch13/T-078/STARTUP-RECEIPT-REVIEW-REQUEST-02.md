# T-078：首启收据完成条件的新独立审查请求

状态 **INCOMPLETE，待主控开启全新审查**。原审查 `independent-review-startup-01.md` 的 NO_GO 不改，不改写为 PASS。

基线为主控提交 `9c0d8be258cff44c6e645594ac0c51933a87030d`，新候选为本次 `test(T-078): reject startup key receipts as inbox delivery` 冻结提交（以实际提交号绑定）。产品 workbench/src 必须与基线逐字相同；差异仅在完成条件、领域输入条目、运行器与证据。主控 #309 的副本缺 bin/inbox 失败、修复预检、entry-02 原始通过输出也随交付原样留存。

请从 #312 的要求重建 oracle：每个首启控制键之后、release 之前，必须通过会执行 readWakeDelivery 的真实刷新方法查询原 stop，断言 queued、历史没有 delivered、原 I2 没有登记或派发。不得只查尚未刷新的 SQLite 行。

作者已实跑旧冻结测试在 M5 下存活 15/15，以及新领域候选 15/15、M5 两项正例在新刷新断言处失败。候选保存七个逐时点观测；M5 的错误历史为 queued→delivered，且仍 unknown、一条队列、仅 ArrowUp 字节。请核对该拒绝确为新增业务断言，不是入口/身份/夹具错误。

真实入口复验脚本为 `run-startup-receipt-checks.py --suite entry`，确切命令在 `STARTUP-RECEIPT-ENTRY-COMMAND-01.txt`。它复用经 #309 修正的副本装配与真实 inbox 加载预检，不另写业务入口；M5 与候选均跑同一个已补强的真实 CLI/daemon/Stop/relay 排练。交付时此项只完成无服务预检，完整结果由主控沙箱外回传。未取得该边界证据时不能授予新完成条件审查 PASS。

审查范围不包括真实 Claude 新实例、A14 续行、供应商模型或整张 T078 完成；不得操作仍保留的 A14。保留精确 M5 与 probe.diff，其他四项旧变异的旧拒绝结论不冒充本候选的新独立运行。
