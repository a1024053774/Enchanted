# 主控 #353：C-I1 START 在成功提交后误调初始 release

状态：**诊断 PASS；原 START 仍 INCOMPLETE，09C 尚未完成，续行待主控裁定**。本轮只读 SQLite 的一致 SELECT 事务、原文件与门禁 `pane_status`/完整 `pane_output`。没有 dispatch、release、initialize、业务 send/stop、HTTP 请求、按键或重试；未改产品、driver、冻结包或原失败结果。

## 当前并非一条未放行队列

[只读原件](result.json)、[窗格状态](pane-status.json)、[登记行](registered-dispatch.json)、[事件](relevant-events.json) 表明：

| 事实 | 实际记录 |
| --- | --- |
| 唯一 ideation 登记 | dispatch `0e15f303-ece9-46e6-b19e-d0da8440a676`，全局 seq 2 |
| 初始化 | 两角色各一条 `executor_action/action=initial_release`，seq 88、91 |
| 送达 | dispatch_queued 98 → paste_intent 99 → paste_written 100 → turn_submit_intent 101 → turn_submitted 102 |
| Claude 接收 | UPS/turn_start_signal 108，prompt 精确等于登记标记加规范化正文；native prompt `52c2ed18-90ed-4f6e-9337-b76bc9571350` |
| 实际许可 | PermissionRequest/permission_wait 112，Bash.command 为本场 C_SEND_STOP，tool_use 已由实际 API 登记 |
| 当前状态 | ideation busy、active 为该 dispatch、queued=[]、failed=null；executor idle、active=null、queued=[] |
| HTTP | ideation 1 请求/1 响应、阶段 C-I1/tool_use、无 error；executor 0 请求 |
| 尚未发生 | 未按工具许可 Enter、未有 tool_result/Stop、无本场 stop 条目、clock-origin 不存在、目标 delta 空 |

当前原屏已完整读取 **16,074 字节**，原件 [current-permission-screen.bin](current-permission-screen.bin) 与 [capture](current-permission-capture.json) 保留，offset0 连续至固定 total 并确认 EOF。本轮没有把“出现 PermissionRequest”代替主控对原屏命令及一次性 `❯ 1. Yes` 的核对。

## 根因归于驱动，不改产品初始放行契约

`workbench/tests/t078_09c_driver.py:424` 的 initialize 校验两角色首启/readiness/零 POST、unknown/空队列后，于 433 行各做一次初始 release。`start_first_turn` 187–190 行又明确要求两个窗格已经 idle、空 active/队列且零 POST，因此 initialize 的初始放行是 start 的现有前置；不能只删除 initialize 的 release 而保持其余代码不变。

产品 `workbench/src/panes.ts:526` 的 dispatch 先登记入队，再于 538 行直接 await drain；559 行的 drain 在 idle 且无占用时自然贴入、发送 CR、置 busy/active，582 行记 turn_submitted。当前实况正是这条路径。产品 `release` 642 行只接受 unknown 且无 active/failed 的首次放行；它不是“每派一条后都必须再调用”的操作。

驱动 195 行 dispatch 已经成功送达；随后保存了原 `window-stop-action-0e15f303…json`，201 行却再调 pane_release。此时 pane 已 busy/active，正确收到 initial_release_only。原 [start-01/result.json](../09c-c1-b1-ideation-p1-01/phases/C-I1/start-01/result.json) 的堆栈也精确指向该行。错误发生在有效副作用之后，返回非零不能推断“没有发出输入”。这是测试驱动顺序缺陷，没有证据表明产品派发或放行回归。下一个驱动修订的最小改动是删掉 start 中这次多余 release，保留 initialize；本轮仅诊断，不在运行中修改冻结源码。

## 最小续行：不再送任何输入，直接观察同一许可

**无需为此驱动错误重建现场**，前提是主控继续时仍读到同一 active dispatch/PermissionRequest、1 个 POST、无 stop/clock-origin。已用 ideation 1 root/1 POST，尚余 3 roots/6 POST（包括本 C-I1 的第二条），executor 尚余 1 root/1 POST，完整计划仍能在原预算内完成。120 秒以真实 stop.created_at 为起点；目前工具尚未执行，无 stop 条目，等待诊断没有消耗这条业务计时。不能据此豁免未来实际 created_at/monotonic/150 秒条件。

1. 不重跑 START、INITIALIZE、pane_dispatch 或 pane_release，不另建 stop-body/action ID，也不发 Enter“探测”。保留 start-01 的 INCOMPLETE，不能重写成成功。
2. 主控裁定续行后，运行 [CONTINUE-READONLY-COMMAND.txt](CONTINUE-READONLY-COMMAND.txt)。它就是原冻结 driver 的 C-I1 `--mode observe`，只读实际 bound dispatch/事件和完整原屏，写全新 `phases/C-I1/dispatch-01/`；没有新派发或按键。路径已核对，输出当前不存在。应得到 READY_FOR_PERMISSION，并关联同一 dispatch/seq/prompt/permission_event。
3. 之后按原 C-I1 的 screen/cmp → 生成未签 permission → 主控逐项核对命令、实际 target、许可事件与原屏并签字 → check-only → 一个 awaited Enter 的既有流程。任何身份、原屏、计数或状态变化即停，不复用本次只读快照冒充后续的按键前校验。工具执行成功并经实际 Stop/relay 产生 stop 后，才建立 clock-origin 并继续 C-I2/C-I3。

本诊断允许主控评估继续原已发生回合，不是新的运行批准，也不把场次或整票上调为 PASS。若后续读回发生未知提交、额外 POST、工具已执行或许可身份改变，应停并另报，不能重复发送来“修复”证据。
