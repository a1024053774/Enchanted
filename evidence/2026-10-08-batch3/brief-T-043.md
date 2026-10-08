# Worker 任务书：T-043 任务窗口外观整理（build，Claude Code Sonnet 5.5 high）

你是 a2a 的界面 worker（Claude Code）。主控是 Claude Code（Herdr pane wF:pM）。只做 T-043（`.project-map/tickets/T-043-task-window-polish.md`，验收以它为准）。用户认为你的审美更好，请认真设计，而不是只做最小改动。

## 先读
- a2a：`AGENTS.md`、`CONTEXT.md`、T-043、T-042 ticket 与截图 `evidence/2026-10-07-synara-batch2/T-042/desktop/04-task-window.jpg`（浅色）、`T-042/intervention/03-managed-expanded.jpg`（深色，展示了重复的状态行与"像邮件"的人工介入块）。
- T-038 交付记录 `evidence/2026-10-07-synara-batch2/T-038/RESULTS.md`（membership、界面结构、Playwright 截图脚本与隔离 dev 启动方式）。
- 人工介入与 observer 接口：`T-037/human-intervention-event.md`、`T-037/observer-status.md`。
- fork 的 `AGENTS.md`、`CLAUDE.md`，以及 Synara 自身的主题、Button、Badge、消息气泡、侧栏等组件——新界面必须看起来是 Synara 原生的一部分。
- 用 `frontend-less-ai-tone`、`same-visual-family` skill。参考 https://good-css.com 的 CSS 写法（只读参考，不复制其品牌）。

## 设计要求（用户意见）
- 任务状态行与"人工输入记录器"只在任务顶部出现一次，worker/reviewer 栏里不重复。
- 删除独立的"查看人工介入记录"展开块。人工介入改为：对话流中那条人类消息上的小标记（沿用 Synara 消息与徽章样式）；栏标题只保留计数。observer failed 时的说明要清楚但不刺眼。
- 会话栏数量不限：3 个以上横向排开要好看（宽度、分隔、标题栏、滚动）。
- 浅色、深色主题都要协调。文案简短、不带"AI 味"。

## 范围与禁止
- fork `~/Documents/Code/synara`，分支 `a2a`（当前 `3566ef4`）。只改 `apps/web/src/a2a/**` 及其测试；需要改上游组件或其他文件先停下问主控。不 push。不要动 `~/Documents/Code/synara-t038`。
- 严禁移动、替换或链接 `apps/*/dist`、`node_modules` 等构建输出或依赖目录（见 AGENTS.md，曾误删 6,186 个文件）。Bun/Node 只经 `a2a/scripts/bun`；缓存与临时文件放外置盘。
- 截图：用 fork 现有的 Playwright 依赖操作隔离 dev 实例（复用 T-038 的方式），不用用户浏览器 profile，不新增依赖；需要下载浏览器先问主控。不做真实模型调用；人工介入与失败原因可用明确标注为夹具的 events 数据，不自造字段。
- 只停你启动的进程，只删你创建的文件。不读写用户 Synara 数据、`~/.codex`、Herdr。

## 交付
- 证据目录 `evidence/2026-10-08-batch3/T-043/`：改前截图（复现两处问题）、改后浅色/深色截图（一个任务 3 个会话、一条人工介入标记、一次失败原因），截图脚本与命令，中文 `RESULTS.md`（设计取舍说明、改动文件清单、检查结果）。
- typecheck、lint 通过；T-038 的 membership 与界面相关测试仍通过。
- fork 在 `a2a` 分支提交你的改动；a2a 仓库只提交你的证据与 T-043 ticket 的 Resolution（ticket 保持 open，写"待主控关闭"）；不 push。
- 遇到权限请求或需要用户决定的事，停下说明。最后终端回复一行：`T-043 DONE <PASS|INCOMPLETE|BLOCKED> <a2a commit> <fork commit>`。
