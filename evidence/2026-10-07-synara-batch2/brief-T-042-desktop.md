# 任务书：T-042 第一部分——隔离桌面版到达任务窗口并截图（Codex GUI + Computer Use）

你是 a2a 的执行 agent，由用户在 Codex GUI 中直接操作，用 Computer Use 操作桌面界面。只做本任务书范围；结论与需要决定的事直接报告给用户。

## 先读
- `~/Documents/Code/a2a`：`AGENTS.md`、`CONTEXT.md`、`.project-map/tickets/T-042-desktop-task-window.md`（验收以它为准，本任务只做第 2 项）、`.project-map/tickets/T-038-task-window-ui.md` 的 Resolution。
- T-038 证据：`evidence/2026-10-07-synara-batch2/T-038/RESULTS.md`、`post-review-electron.md`、`round6/RESULTS.md`，以及其中启动隔离服务、Vite、Electron 与夹具（`cycle2/fixture.json`、`runtime-start.json`、`desktop-final-proof*.json`）的完整命令。复用这些命令，不重新发明启动方式。

## 范围与禁止
- 代码在 worktree `~/Documents/Code/synara-t038`（分支 `a2a-t038`，`ad13b72`）。不要碰 `~/Documents/Code/synara`（另一个 worker 正在用），不合并分支，不 push。
- 只用隔离数据目录、独立 profile 和 T-038 的 `desktop-home` 方式启动；不读写用户的 Synara 数据、浏览器 profile、`~/.codex`、Herdr。不做真实模型调用。
- 内置盘几乎满了：所有安装、构建、下载缓存都走 `a2a/scripts/bun` 入口（外置盘 `/Volumes/WD-Elements`，未挂载就报错，不回退内置盘）。不要在内置盘新建大目录；临时文件放外置盘。
- Computer Use 只操作本任务启动的 Electron 窗口；看到用户自己的其他窗口不要点。遇到系统权限对话框、登录、付款、或任何需要输入密码的界面：停下告诉用户。
- 不改上游 Synara 代码。若确认是 a2a 自己代码的缺陷（`apps/web/src/a2a/**`、membership、a2a 路由），先保存修复前的失败现场再修，修完重跑；改动前先告诉用户。

## 要做的
1. 按 T-038 的命令启动隔离服务与 Electron，准备夹具：一个项目下至少两个任务，其中一个任务含 worker 与 reviewer 两个会话，并有门禁状态。
2. 用 Computer Use 在 Electron 里操作：关闭导入弹窗（试 Not now、Escape、右上角关闭等），然后通过界面进入任务窗口。T-038 记录过：Not now 点了不关；直达 `/a2a` 时出现 WebSocket 帧头异常和连接被拒绝。先观察是否复现，再查原因（服务是否已就绪、端口、启动顺序），区分环境/启动方式/上游缺陷/a2a 缺陷。
3. 到达任务窗口后截图：能看到项目下两个任务、一个任务里 worker 与 reviewer 两个会话、门禁状态。
4. 到不了就保存现场截图、日志与原因，结论写 INCOMPLETE，不要拿根页面截图充数。

## 证据与交付
- 证据目录：`~/Documents/Code/a2a/evidence/2026-10-07-synara-batch2/T-042/desktop/`。保存每一步的确切命令、截图、日志，以及 `RESULTS.md`（中文）：结论用 PASS / INCOMPLETE / BLOCKED，写明原因、复现命令、与 T-038 现象的对照。
- 结束时停止你启动的所有进程（只停你启动的），确认端口无监听。
- a2a 仓库只提交 `T-042/desktop/` 下你自己的文件（`git add -- <路径>`），不改 MAP.md、ticket、AGENTS.md；不 push。
- 最后给用户一段简短中文总结：结论、截图路径、未解决的问题。
