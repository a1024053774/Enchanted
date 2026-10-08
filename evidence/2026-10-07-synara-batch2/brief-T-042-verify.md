# 任务书：T-042 第二部分——合并后复验与真实人工介入显示（Codex GUI + Computer Use）

你是 a2a 的执行 agent，由用户在 Codex GUI 中直接操作，用 Computer Use 操作桌面界面。只做本任务书范围；结论与需要决定的事直接报告给用户。

## 先读
- `~/Documents/Code/a2a`：`AGENTS.md`、`CONTEXT.md`、`.project-map/tickets/T-042-desktop-task-window.md`（本任务做第 1、3 项；第 2 项已完成，第 4 项由用户判断）。
- `evidence/2026-10-07-synara-batch2/T-042/merge/MERGE.md`（合并记录）、`T-042/desktop/RESULTS.md`（上次桌面截图的启动方式，复用它）。
- 人工介入与 observer 接口：`evidence/2026-10-07-synara-batch2/T-037/human-intervention-event.md`、`T-037/observer-status.md`。
- 复验命令：`T-037/RESULTS.md` 的"复现与交接"（18 项、17 项）；`T-038/RESULTS.md` 中 membership 的 HTTP 场景脚本。

## 范围与禁止
- 代码在 `~/Documents/Code/synara`，分支 `a2a`，合并提交 `3566ef4`。不改产品代码；若复验失败，保存现场后停下告诉用户，不自行修。不 push。不要动 `~/Documents/Code/synara-t038`。
- 只用新的隔离数据目录与独立 profile（放外置盘 `/Volumes/WD-Elements/dev-cache/synara/instances/` 下的新目录）；不读写用户的 Synara 数据、浏览器 profile、`~/.codex`、Herdr。
- 内置盘几乎满了：安装、构建、缓存都走 `a2a/scripts/bun`；临时文件放外置盘。
- 不做真实模型调用。若发现必须让 provider 真正运行才能产生人工介入事件，停下问用户。
- Computer Use 只操作本任务启动的 Electron 窗口。遇到系统权限、登录、密码、付款界面：停下问用户。

## 要做的
1. 第 1 项：在合并后的 `a2a`（`3566ef4`）上运行 `lint`；用 T-037 的命令重跑 18 项编排与 17 项交付/恢复；重跑 T-038 的 membership HTTP 场景。每项保存完整命令、日志与退出码。
2. 第 3 项：按 T-042/desktop 的方式启动隔离 Electron（经界面点"任务窗口"，地址是 `/#/a2a`）。准备一个受管任务，使其 worker 会话是门禁 dispatch 的受管 thread。
   - 截图任务窗口中 observer 状态（应为 healthy，不能是"未安装"）。
   - 在受管 worker 会话的输入框中由你（代表人）输入并发送一条短消息，例如"人工介入测试"。然后截图任务窗口中该 thread 的人工介入标记，并用门禁 `events` 命令读回对应的 `human_intervention` 事件（核对 thread_id、message_id、dispatch_origin=user）。
   - 再在一个非受管会话中发一条消息，确认不产生人工介入事件（反例）。
   - 若 provider 关闭导致消息无法发送或不产生事件，记录现场与原因后停下问用户，不要启用 provider 或调用模型。
3. 不满足的项写 INCOMPLETE 并说明原因，不用夹具或旧截图充数。

## 证据与交付
- 证据目录：`~/Documents/Code/a2a/evidence/2026-10-07-synara-batch2/T-042/verify/`，中文 `RESULTS.md`，结论用 PASS / INCOMPLETE / BLOCKED。
- 结束时停止你启动的所有进程，确认端口无监听。
- a2a 仓库只提交 `T-042/verify/` 下你自己的文件，不改 MAP.md、ticket、AGENTS.md；不 push。
- 最后给用户一段简短中文总结：每项结论、截图路径、未解决的问题。
