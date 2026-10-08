---
id: T-043
title: 任务窗口外观整理
type: build
status: open
blocked_by: []
claimed_by:
supersedes:
---

## What to build

用户审阅 T-042 截图后的意见（2026-10-08）：任务状态行与"人工输入记录器"在任务顶部和 worker 栏重复出现；"查看人工介入记录"展开块像邮件，与 Synara 其他界面格格不入。重做任务窗口的视觉：状态只在任务顶部出现一次；人工介入改为对话流中那条人类消息上的标记，栏标题只保留计数；全部沿用 Synara 自身的主题、组件与间距，参考 good-css.com 的 CSS 写法。会话栏数量不限（3 个以上横向排开要好看）。浅色与深色主题都要可用。

## Acceptance

- [ ] 状态行与人工输入记录器只出现一次；人工介入在对应人类消息上标记，栏标题有计数；不再有独立的展开记录块。
- [ ] 隔离 dev 环境的浅色、深色截图各一组，含一个任务下 3 个会话、一条人工介入标记（可用标明为夹具的事件数据）、一次失败原因显示。
- [ ] 只改 a2a 自己的界面文件；typecheck、lint 通过；T-038 的 membership 与界面相关测试仍通过。
- [ ] 外观由用户判断。

## Resolution

Worker 交付（Claude Code，2026-10-08）：待主控关闭；第 1–3 项已有证据，第 4 项待用户判断外观。fork `a2a` 分支提交 `d3b5bcc61`，只改 `apps/web/src/a2a/**`。栏内重复的门禁行根因是上游 `ChatView` 为每个 thread 渲染 `GateStatus`；改用 context 在任务窗口内让其静默，不改上游。人工介入改为对话流中人类消息上的标记（以事件 `message_id` 为键的限定作用域 CSS），删除展开记录块，栏标题只留计数；门禁区合并为一行 `GateBar`。证据与取舍、夹具口径、失败记录见 [RESULTS](../../evidence/2026-10-08-batch3/T-043/RESULTS.md)；改后浅色/深色截图 `after-light-main.png`、`after-dark-main.png`（3 个会话、1 条人工介入标记、一次真实 oracle 失败原因），fmt、lint、typecheck 与 T-038 相关 web 测试通过。未解决：上游空会话页脚在窄栏重叠（需改上游才能修，已请主控决定）。
