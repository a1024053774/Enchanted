# T-095-1 准备阶段（主控 #87 确认后）

**INCOMPLETE。** 本阶段获准先做 `scripts/agent-status` 的入口、身份核对、unknown、普通活动与退出后的重读。真实提问面板规则必须等真实红态原件；合成读数不算 ticket 红态或绿态。`dispatch` 不改，不启动额外 Codex。

验收预期来自任务卡和主控 #87 的确认，不从待实现代码读取。测试走实际命令入口，Herdr 是显式替身；这里只证明命令边界与给定读数的处理。另保留现有 worker 的普通活动读屏，来源见 `ordinary-working-source.json`，没有新增模型回合。

本轮先写下的失败方式：

- 启动记录不存在、未成功启动、损坏、被更新的同 pane 启动取代，或 native-session 行偷换 agent/pane。
- live worker、pane、terminal、revision、cwd、已绑定原生身份不符，或两次读取之间身份/状态代次变化。
- 只凭 Herdr 的 working 值判忙；把正文中引用的 UI 标记当作活动或提问。
- 画面缺失、截断、存在草稿、模型栏不符、visible 与 detection 相互矛盾，或 Herdr 调用失败。
- 新的未核对面板布局被误报成 working；退出面板后仍沿用上次状态。
- 忽略 launch 输入、硬编码 worker 身份、总返回 unknown 或直接透传 Herdr 状态。
- 状态入口写记录、加锁、派发、按键或执行其他变更命令。

普通 working 的机械依据限定为已观察的 Codex 底部结构：计时活动行、可选的 Tip 子行、空闲输入框外形、模型栏和快捷键栏，同时两次 live 身份稳定且 Herdr 原值为 working。可选后台终端计数后缀来自本次原件。正文内容不用于猜测意图。未知尾部结构保持 unknown；这条准备规则仍须接受真实折叠面板的反证检验。

启动记录没有绑定原生会话时，只核对记录中的 terminal/revision 与当前两次一致的原生身份，输出明确的 `native_binding` 来源；不把观察到的原生身份回写启动记录。已经绑定时必须相等。该只读监视投影不替代门禁的运行时身份校验。

后续：先由主控在有名额时采红态；worker 核对两种面板的原件后才实现 `waiting_controller_answer`。完整验收与独立审查均未完成。
