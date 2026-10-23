# T-146 边界与验收冲突

状态：INCOMPLETE。尚未修改产品行为。

1. `workbench/src/daemon.ts:409` 只向 `reflectTree` 传 `panes.status(record.thread).lifecycle`。要和侧栏共用包含空闲、等待回答、未恢复等状态的完整来源，最小修复需要改这一入口（让 Reflect 消费同一次 sidebarSnapshot 的 agents，或传入相同状态依赖）。daemon.ts 不在任务卡允许清单。请授权此处的最小入口改动，或指定其他方案；不需要改 renderer.tsx/main.ts。
2. `workbench/src/flow.ts:47,53` 过滤 ended；受保护的 `workbench/tests/test_t111_flow.mjs:44,47` 也要求 ended 不出现在泳道或未归属。这与任务卡“三处都显示已结束”冲突。侧栏 `sidebar.ts:184` 也只展示 approved 的角色申请，关闭后该主控消失。请裁定：沿用既有隐藏规则，仅保证展示时状态同源；还是修改展示规则并由主控更新 oracle/边界。
3. `roleRequests.ts:59-63` 已对关闭终端的 approved 角色返回 ended，Reflect 对该角色也会返回 ended。因此“关闭后仍运行中”的精确失败尚需真实入口核对；已找到确定的不一致是 Reflect 对 managed 会话使用 lifecycle，侧栏使用 agentState，空闲也会被 Reflect 标为运行中。

建议先跑真实 Electron 诊断，保留关闭终端、CLI 退出、仍运行与空闲的三处原始观察，再按裁定修复。测试准备与诊断不阻塞，产品行为修改待裁定。
