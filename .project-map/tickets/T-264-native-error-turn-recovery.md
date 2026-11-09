---
id: T-264
title: Codex 额度错误结束回合后受管会话仍显示运行中
type: build
status: closed
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

2026-11-09 再次复现：T-249-2 a5 的 Terra 会话在 `08:17:47Z`（纽约时间 03:17）完成 18/18 个比较器检查后，写入同一 `usage_limit_exceeded` 错误结束记录；未提交，工作台仍显示 busy。新证据为 [原生错误](../../evidence/2026-11-09-batch35/T-264/controller/terra-a5-quota-error.json) 和 [窗格状态](../../evidence/2026-11-09-batch35/T-264/controller/terra-a5-pane-after-quota.json)。这不是“文稿”授权等待。恢复该会话前须核对这次错误之后的额度状态，保留未提交的修复和检查输出。

当前接口事实：`ControllerQuota` 已能读取同形状的额度错误，但只覆盖获批主控角色；受管 worker/reviewer 的原生读取路径没有处理这个错误结束。`releaseByUser` 要求匹配的中断代次、空输入声明和当前身份，且拒绝 failed pane；审查重开按钮只在任务 paused、review unknown 时出现，经原 `verify` 入口处理。后续修复须证明这些现有入口能安全续接或有界重开，不能把错误结束当作正常 Stop，也不能以现有主控额度提示替代受管会话的交付生命周期。

2026-11-09 续接：用户明确确认“已再次重置，继续”。主控真实窗口确认空输入并执行 Esc；第一次放行因进程查询失败被拒绝。诊断确认是该 Terra 子树中的两个旧 `node_repl` 辅助进程占用 Sparkle 更新前的应用文件，libproc 对它们返回 ENOENT，主进程与 shell 的身份正常。主控保存 PID、父进程、启动时间和已加载文件位置后，只终止这两个辅助进程；随后正式 `pane_process_info` 返回同一 leader、native session 和 shell，未放宽门禁。刷新窗口，再经“输入框已空，放行”成功恢复；门禁派发续接后同一 attempt 开始新回合。操作由主控执行，不冒称用户亲自点击。证据见本票 controller 下 `terra-a5-retired-helper-cleanup.json`、`terra-a5-process-info-after-helper-cleanup.json` 与 `terra-a5-release-recovery-events.json`。本票产品修复仍 INCOMPLETE；这次环境清理不替代错误回合状态修复。

## 2026-11-09 结论（主控自做）

PASS（范围收窄后）：用户 2026-11-09：“不用 codex 了,你自己做完这些部分结束”。受管 Codex 根回合以带 `error` 的 `task_complete` 结束且窗格仍 busy 时，侧栏显示“回合出错结束”，不再是“运行中”；不结算回合、不执行排队输入、不接受审查草稿，恢复仍走现有放行。证据见 [构建结果](../../evidence/2026-11-09-batch35/T-264/build/RESULTS.md)：11 项绿态含反例，父版判红。

未做、不宣称：真实 Codex 隔离复现、独立审查、额度恢复检测与自动续接、审查员恢复入口。需要时另开票。

## Resolution

只做了状态显示：侧栏把带错误结束的当前根回合显示为“回合出错结束”（提交 `d159bc4ca`，证据 `evidence/2026-11-09-batch35/T-264/build/`，11 项含反例，父版判红）。第 1 条中“未完成行”没测；第 2 条显示部分达成；第 3、4 条（续接恢复、真实 Codex 复现、独立审查）没做，按用户 2026-11-09：“不用 codex 了,你自己做完这些部分结束”免去。需要时另开票。
