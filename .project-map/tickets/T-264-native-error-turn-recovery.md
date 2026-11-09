---
id: T-264
title: Codex 额度错误结束回合后受管会话仍显示运行中
type: build
status: open
blocked_by: []
claimed_by:
supersedes:
ready: no
ready_by: executor
ready_rev: 1
---

## 真实故障与范围

2026-11-09 原生 Codex 0.167.0 的 T-249 worker、T-262 reviewer 在额度耗尽时写入 `task_complete`，携带 `error.codex_error_info=usage_limit_exceeded`，没有发 Stop。用户随后明确回复“我已使用重置卡”。工作台仍保留原 active turn、busy 和排队输入；不是权限弹窗或 CLI 进程退出。证据在 `evidence/2026-11-09-batch35/T-264/controller/native-errors.json` 及 `pre-recovery-events.json`。

`PaneManager.readNative` 当前处理 root `task_started`，不处理带错误的 `task_complete`。普通 worker 可以在真实窗口 Esc、确认空输入后放行；reviewer 窗口保持只读且无此按钮。审查员在额度错误前保存了 MCP review_submit 草稿，但门禁尚未收到结论，不能把草稿当作通过。T-249 恢复后另触及配置的六次自动投递上限，这是另一条明确的队列原因；经现有工作台人工输入继续的动作应保留为人工介入，不能伪装自动派发。

授权：本轮用户“修复现在 enchanted故障并继续”“主线是完成主要的两个面板的任务以及 bug 修复”。先查明现有接口能支持的最小恢复路径，再将本票标就绪。不得因为本票扩大额度监控、自动重试、修改账户或开启审查员自由输入。

## Acceptance

- [ ] 用原生可信日志的错误结束记录复现 busy 滞留；拒绝 foreign session、旧 turn、辅助进程日志以及未完成行。
- [ ] 错误结束显示准确状态，保持 task/attempt/session/fence 和交付请求事实；不得借错误结算正常 Stop、执行待提交请求或接受审查草稿。
- [ ] 用户或主控明确续接后可以经正常门禁恢复，输入不重复；审查员保持独立只读，真实新回合结论重新核对。
- [ ] 正常 Stop、正在工作、额度未恢复、自动投递上限、重启后的旧身份分别有反例；真实 Codex 隔离复现和独立审查齐全。

## 当前结论

INCOMPLETE。根因入口已定位，错误信号与安全恢复动作之间的接口仍需核对；目前没有修改产品。T-249 的原生工作已通过窗口续接，T-262 将保留旧审查证据并经受控生命周期恢复。不得手改正式数据库或直接向 hc 注入输入。
