# 任务书：T-042 第三部分——真实人工介入显示（Codex GUI + Computer Use，允许真实模型调用）

你是 a2a 的执行 agent，由用户在 Codex GUI 中直接操作，用 Computer Use 操作桌面界面。只做 T-042 第 3 项；结论与需要决定的事直接报告给用户。

## 授权
用户于 2026-10-08 在主控对话中选择方案 A：允许在隔离环境中启用 Codex provider，并为本项做真实模型调用，上限 2 次短 turn（受管 worker 1 次、非受管会话 1 次）。超出上限、或需要其他 provider，先停下问用户。

## 先读
- `~/Documents/Code/a2a`：`AGENTS.md`（尤其隔离 CODEX_HOME 规则与新增的"不得移动或链接构建输出目录"规则）、`.project-map/tickets/T-042-desktop-task-window.md`。
- 上一轮：`evidence/2026-10-07-synara-batch2/T-042/verify/recovery-01/RESULTS.md`（启动方式、受管 worker 的 dispatch 与 membership 绑定、发送被拦的现场）。沿用它的脚本与方式。
- 真实 Codex 的隔离做法：`evidence/2026-10-07-synara-batch2/T-039/repair-03/FINAL-RESULTS.md`（只复制 auth.json、信任夹具根、两条 git 规则、结束删除整个 home）。
- 事件形状：`T-037/human-intervention-event.md`、`T-037/observer-status.md`。

## 范围与禁止
- 代码在 `~/Documents/Code/synara`，分支 `a2a`，合并提交 `3566ef4`。不改产品代码，不重新构建到非标准目录，不移动、替换或链接 `apps/*/dist`、`node_modules` 等目录。不 push。
- 新隔离根放外置盘新目录。隔离 CODEX_HOME：只复制 `~/.codex/auth.json`，只信任本次夹具仓库根，只有 `git add`、`git commit` 两条 allow 规则，不装 hook；副本不入证据或 Git；结束后删除整个 home 并记录删除检查。只在隔离 settings 中启用 Codex provider，模型 gpt-6.1-sol，fastMode，runtimeMode 沿用 T-039（full-access）。
- 不读写用户的 Synara 数据、浏览器 profile、`~/.codex`（auth.json 只读复制一次）、Herdr。开始和结束各记录一次 `~/.codex` 下 config.toml、rules/ 的大小与修改时间，以及 `herdr status` 的只读输出。
- Computer Use 只操作本任务启动的 Electron 窗口。遇到系统权限、登录、密码、付款界面：停下问用户。

## 要做的
1. 启动隔离 Electron，经界面点"任务窗口"进入 `/#/a2a`。准备受管任务：worker 会话由门禁 dispatch 创建并经 membership 绑定。
2. 正例：在受管 worker 会话的输入框中，以人的身份输入并发送一条短消息（例如"人工介入复验：请只回复 OK，不要修改文件"）。截图任务窗口中该 thread 的人工介入标记；用门禁 `events` 读回 `human_intervention` 事件，核对 task、attempt、thread_id、message_id、dispatch_origin=user、text；确认任务业务状态没有因此推进。
3. 反例：在一个不属于任何受管任务的普通会话中发送一条短消息，确认门禁没有新增 human_intervention 事件。
4. 收尾：模型回复完成或期限到后，经门禁 reclaim 回收受管 worker（绑定原 attempt），停止你启动的所有进程，删除隔离 home。

## 证据与交付
- 证据目录：`~/Documents/Code/a2a/evidence/2026-10-07-synara-batch2/T-042/intervention/`，中文 `RESULTS.md`，结论用 PASS / INCOMPLETE / BLOCKED；保存每步命令、截图、事件原文、模型调用次数与用户数据前后核对。
- a2a 仓库只提交 `T-042/intervention/` 下你自己的文件；不改 MAP.md、ticket、AGENTS.md；不 push。
- 最后给用户一段简短中文总结。
