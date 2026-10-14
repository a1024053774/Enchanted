# 09A-3 实现与入口证据

2026-10-14，主控 #130／#131。本轮授权以当前派工和 [disposition](../../../.project-map/inbox/20261014T124540Z-executor-disposition-001.md) 为准。原 BLOCKED 报告、失败方式清单、slot 材料、静态检查和 RESULTS 修改已由主控原样保存，提交 `c80cecd6cd4cc7dfdf816022db02c0f600f253d5`；更早已提交的清单和 slot 材料未改写。

**入口修复局部 PASS，真实 Claude／Electron 场景及整票验收 INCOMPLETE。** 真实模型、vendor CLI、假 API、Electron 和构建启动均为 0；没有额外 Codex 或子代理，没有改 gates/core.ts，没有启动或处置旧 09A-2 slot。

## 行为

**Tracer bullet** 仍是 Esc → 用户自行处理草稿 → 声明输入框已空 → 放行 → 第二个独立 prompt。**Deep modules**：Panes 持有中断收据、窗格级输入代次和串行 PTY 通路，daemon 核对窗口身份，main/preload 只转发声明；没有新增门禁入口。**Ubiquitous language**：动作文字固定为“用户声明输入框已空”，只说明观察到用户作了声明，不声称机器读取了编辑框。

- Esc 实际写入事件的 seq 是中断引用。声明还绑定 launch、当前 window_id 和窗格输入代次。无声明、错引用、旧窗口或 launch、新键入／粘贴／二进制输入／组合输入、等待身份检查期间的新输入均拒绝，不删除用户字节。记录动作和释放前再次核对；窗口在最后一次身份等待期间关闭也拒绝。
- main 保持请求发送顺序，但放行等待不会藏住同窗口的新输入；实际 PTY 写入仍串行。陈旧声明属于已知拒绝，后续用户字节继续按原顺序处理；未知调用失败仍停止发送，不重投。窗口关闭等候输入与未决放行的结果。
- UserPromptSubmit 只在当前 active 指向结构化登记注入且实际正文错配时返回 JSON block。原 prompt、期望正文、prompt_id、dispatch、submission 和原因追加记录；不裁剪、不容忍拼接、不自动重送。没有当前登记注入的提交，包括含旧标记的手打文字，允许继续；prompt ID 和 native 身份诊断保持。Stop 的逻辑和 hook 输出／退出码不改。
- 未包裹为 bracketed paste 的 C0／DEL 或终端转义输入记 terminal-key action；Ctrl+C/U/S 与方向键原字节保留，不记 message，也不据这些键推断空框。二进制沿用 base64 action。

hook 采用 exit 0 的 `decision: block` stdout，依据 [官方 UserPromptSubmit 决定控制](https://code.claude.com/docs/en/hooks#userpromptsubmit-decision-control)。这里只证明真实 hook CLI 已输出该 JSON；供应商 2.1.296 的实际阻断与 API 请求数仍须新夹具验证。

## 红态与绿态

独立预期来自 [用户答复](20261014T120839Z-ideation-answer-001.md) 和未改写的 [FAILURE-MODES](FAILURE-MODES-09A3.md)。探针经过生产 daemon、窗口凭据、Unix socket、SQLite 和子进程 hook CLI；vendor 身份与 PTY 是 spy，main 的实际发送闭包被测试载入，未运行 Electron。

| 检查 | 已知坏结果 | 当前结果 |
| --- | --- | --- |
| 原始声明／控制／拼接／手打条件 | [red-04](empty-declaration-entry-red-04-09a3/results.json)：14 项按预期失败，Stop 契约正例通过 | [final-02](empty-declaration-entry-final-02-09a3/results.json)：17/17 PASS，含保存的 SQLite 和原始 hooks |
| 同窗口新键入被 main 队列藏住 | [main-concurrency-red-02](main-concurrency-red-02-09a3/results.json)：放行错误成功 | 同一个探针当前拒绝并保留新键入 |
| 最后一次身份 await 时窗口关闭 | [window-revocation-red](window-revocation-red-09a3/results.json)：放行错误成功 | 同一个探针当前拒绝，无新增 PTY 写入 |
| 相关既有状态／关联 | 不复用旧候选通过结论 | [窗格 11/11](pane-runtime-green-09a3/results.json)、[Claude 关联 7/7](claude-epochs-green-02-09a3/results.json)、[窗口身份 5/5](controller-window-green-09a3/results.json)、[窗口绑定 8/8](window-binding-green-09a3/results.json) |

复跑使用新的、尚不存在的输出目录：

```sh
node workbench/tests/test_t078_empty_declaration_entry.ts /绝对路径/新入口证据目录
node workbench/tests/test_t078_pane_runtime.ts /绝对路径/新窗格证据目录
node workbench/tests/test_t078_claude_epochs.ts /绝对路径/新关联证据目录 evidence/2026-10-11-batch13/T-078/hook-payloads-08e
node workbench/tests/test_t078_controller_window.ts /绝对路径/新身份证据目录
node workbench/tests/test_t078_window_binding.mjs /绝对路径/新绑定证据目录
```

首轮 red-09a3 的 hook trace 目录错误、red-02 的 Stop 请求目录缺失、claude-epochs 错路径、main 并发探针的顶层 return 设置错误均保留，不能当对应行为的红态。main 设置错误留下的本地 Node helper 为 PID 74270；沙箱拒绝 kill，主控运行 [精确停止脚本](stop-local-probe-09a3.sh)，不涉及 vendor 或用户进程。修正后的有限重跑目录与结果另存。

## 交接边界

Python／shell／Node 语法、renderer 的 Vite/Oxc 内存转换与 diff 检查已通过；未构建、未安装依赖、未写外置盘。门禁 8/9/18 全套本轮未重跑，不冒称通过；真实 IME、实际供应商阻断、API 0 增量和两主控仍未知。

`behavioral-acceptance-review` 要求 “Review one frozen candidate snapshot in a fresh, read-only context”，见 [SKILL.md](/Users/luckye/.agents/skills/behavioral-acceptance-review/SKILL.md)。用户本轮禁止额外代理，因此不自称独立审查 PASS；冻结提交交主控另开只读 reviewer。这也覆盖 `design-integrity-review` 对本次 acceptance 表面变更的路由要求。材料准备与实验启动是两道独立步骤，先冻结代码，再生成两个新根、ID 和来源快照，交逐次 launch 审批。

本会话工具环境只提供旧 `A2A_TASK=T-078-1`，缺 attempt/session/fence/state。提交由主控按真实启动身份及钩子进行；worker 不据继承标识冒充当前门禁 ownership，也不对整票作 submit／验收／集成。完整 task/attempt/session/fence 绑定须由主控在需要受管交付时核对；本轮交的是实验准备材料。
