STATUS: FAIL
TARGET: 9b07f2591906228e0ed122b15193c6c227f7d1e3
EVIDENCE:
- 一次有界独立复核，结束时 HEAD 仍为候选。
- 实际 main.ts、真实 OrchestrationStore 和后台原 validateArrangement 的探针确认：任务两 agent 的重命名、关闭和明确重开登记通过；项目终端重命名被拒绝。
- 原始结果：/private/tmp/t139-review-real-store-03-9b07f259.json；复跑脚本：/private/tmp/t139-review-real-store-03.mjs。
FINDINGS:
- [P2] workbench/app/main.ts:75：项目查询的 saved.panes 还包含任务 agent，重建项目布局时未过滤，导致终端重命名失败 invalid_pane_arrangement；关闭共用同路径。应筛出 task===null。
- [P2] workbench/tests/test_t139_selection.mjs:32：项目查询替身只返回 shell，漏掉真实 store 的任务 agent，掩盖该错误。
COUNTEREXAMPLE:
- 同一项目已有任务 agent 与普通终端；单独打开普通终端再重命名，真实 store/校验拒绝此候选。
LIMITATIONS:
- 仍无真实 Electron、截图、真实性输入与凭据边界、性能及指定回归的完整证据。
- 复核时 README 有 stale；未修改地图。
RULE:
- 项目布局检查应使用真实 store 的项目查询集合，并经过真实布局校验。

后续处置记录：worker 已将该探针保留为 test_t139_layout_store.mjs，添加第二个普通终端，
扩大为项目重命名、关闭与任务 agent 不被关闭的反例；store-layout-red-02.json 在上述候选准确失败。
生产代码现按 task===null 过滤项目打开集，store-layout-green-01.json 的 10 项通过；轻量选择检查 selection-final-01.json 也通过。
这些是修复后运行证据，不改变本报告对旧候选的 FAIL 结论；未再发起第三轮审查。
