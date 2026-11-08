# T-257 v2：恢复复现与修前证据

2026-11-08，状态 INCOMPLETE（候选尚未修复）。旧 RESULTS.md 与其他 v1 记录保持原样；本文开始记录 v2，旧环境阻塞不再作为停止实现的条件。

基线 `ebd155141668da18cb2dc09238c5312e1804223a`；task `a2a+T-257-1`，attempt `bd5eb7a7-618f-4cef-b096-b76f14280b17`，session `26392ed1-cc92-4bcf-a2c1-71cd2e289e05`，fence 2，spec_rev 2。请求配置 Codex / gpt-6-astra / xhigh，不据此证明供应商层级。额外可写目录为空，没有额外目录改动。

按卡从 `5c7df3a93019cea1a690194773d967bebb69a4ef..e9e9f2db8ce6f2c50b453a868c8bcaa026e9fa8b` 生成只含指定 Python 测试与 worker 证据的 binary diff，以 git apply 移植；没有 cherry-pick 旧身份提交，没有修改 controller 证据。工作区起始干净。project-map status：Problems 0、Stale living docs 0，退出 0。

REALITY GATE: PASS（因果与最小修复方向）。主控保存的 `../controller/red-controller-diagnostic-02.json` 在已知坏版本 `5c7df3a93019cea1a690194773d967bebb69a4ef` 运行真实后台、门禁、交互 Codex 0.167.0 和本地 Responses 模型：10 个前提成立，5 项预期行为失败，defect_reproduced=true，退出 1。初始工作中与续跑工作中的 reclaim 均返回 worker_working；原生结束后仍 busy、排队未发、reclaim 仍 worker_working。此证据来自主控，不能记为本 worker 亲自执行。首次多余 Stop 标志导致的 INCOMPLETE 保留，未覆盖。

实测关键顺序：后台 seq 141 提交回执（12:29:31.821Z），首 Stop hook_release 为 12:29:31.909060Z；续跑 UPS seq 147，第二 Stop seq 174，原生 task_complete seq 181。同一 session/turn，只有一次 task_started。第二 Stop 的 stop_hook_active=false。

行为位于 panes.ts：drain 为回执建立 nativeTurn=null 的 active；scan 只在 task_started 绑定 active.nativeTurn；signal 中已认领派发的 UPS 分支只记 turn_start_signal，第二 Stop 依赖 active.nativeTurn 因而不匹配。daemon.ts 的 signal 处理器调用 panes.signal，settleInboxFeedback/sendGateFeedback 排队和投递，signal socket 关闭后 drain。observeThread 的 running 被回收门禁读取。无须改 daemon、hook 或门禁。

本次修正开发测试：第二 Stop 按相同 session/turn 且后台 seq 晚于续跑 UPS 识别，不限定 stop_hook_active 值；该值仍写证据。hook 跨进程按 UTC 排序，后台按 seq 排序，monotonic_ns 仅保留作进程内时长。Acceptance、REVIEW.md、T-252 未改。

后续最小修复：已通过 hook envelope 校验且认领本方派发的 Codex UPS，将 native turn 绑定到当前提交。保留 existing Stop/身份/中断拒绝。以任务卡新增 Python 为 Tracer bullet 的完整入口，另对真实 Panes 模块做有界调度检查；后者不能替代真实验收。Deep modules：留在现有 signal 入口，不新建包装 API。Ubiquitous language：沿用 active/submission、原生 turn、attempt、回收等项目术语。

隔离检查的不变式与失败方式在 Python 文件开头和旧 RESULTS.md 已先记录。当前 worker 不再重复运行已知无法创建 /private/tmp 夹具的真实入口；候选完成后主控与门禁运行同一测试并保留新摘要。集成仍需规定的独立审查及用户证据批准。

**Works**：修前真实失败及因果前提已由主控保存，本 worker 已核对；修复绿态未取得。

**No regression**：此提交不改生产行为；静态解析将另存记录，产品回归未运行。

**Risk / undo**：测试不是验收通过证明。保留全部旧证据；撤销新增开发测试可回退本次测试改动，无生产状态需要回退。
