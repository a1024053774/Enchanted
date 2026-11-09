# T-264 构建结果（2026-11-09）

范围：侧栏状态。受管 Codex 会话的当前根回合以带 `error` 的 `task_complete` 结束（如 `usage_limit_exceeded`）、窗格仍 busy 时，显示“回合出错结束”，不再显示“运行中”。不结算回合、不自动续接；恢复仍走现有“Esc → 确认输入框为空 → 放行”。

改动：`src/sidebar.ts`（新状态 `turn_error`、聚合优先级、事件查询纳入 `task_complete`），界面图标与文字（`app/renderer.tsx`、`app/FlowPage.tsx`、`app/style.css`）。

证据（命令：`node workbench/tests/test_t264_turn_error.mjs [sidebar 模块]`；期望值取自真实记录 `../controller/terra-a5-quota-error.json` 的形状）：

- 绿态 `green-01.json`：11 项通过，含反例——正常 `task_complete` 无错误、仍在工作、旧回合的错误后开始新回合、辅助进程日志、别的 turn id、放行后 idle、foreign session。
- 红态 `red-parent-01.txt`：父版本 `sidebar.ts` 对额度错误回合返回 `running`。
- 回归：`tests/test_t107_sidebar.mjs` 12 项通过。

没做：真实 Codex 隔离复现与独立审查（用户 2026-11-09：“不用 codex 了,你自己做完这些部分结束”）；额度恢复检测、自动续接、审查员会话的恢复按钮都不在本次范围。
