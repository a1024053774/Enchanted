# T-042：隔离 Electron 任务窗口截图（2026-10-08）

**PASS，仅限任务书指定的桌面截图项。** [桌面原图](04-task-window.jpg) 同时显示项目“分页桌面夹具”、两个任务“分页交付”“审查笔记”，以及“分页交付”内并列的 worker、reviewer 两个 agent 会话。门禁当前状态为 `ready`；`claimed / submitted / verified / accepted` 是阶段标签，不表示任务已通过这些阶段。[完整可访问性记录](04-task-window-full.txt) 与截图相符。

没有修改 Synara 或 a2a 产品源码，没有合并、push、真实模型调用、发送消息或人工介入实验。两个会话为空的既有夹具会话；本次关闭所有 provider，所以截图明确显示 provider disabled。人工输入记录器显示“未安装”，不属于本次验收。T-039 后的合并、真实 observer/人工介入复验以及外观判断仍未完成，不能将本报告当作 T-042 整体通过。

## 候选、输入与隔离

- 唯一源码 checkout：`/Users/luckye/Documents/Code/synara-t038`，分支 `a2a-t038`，前后均为 `ad13b72c5faeb5fb601c3d40b7090d746f4f2758`。前后只有原有未跟踪 `.grok/` 和 `apps/server/.grok/`，未处理它们。
- 任务书：[brief-T-042-desktop.md](../../brief-T-042-desktop.md)，提交来源为用户指定的 `3075e22`；验收源为 `.project-map/tickets/T-042-desktop-task-window.md` 第 2 项。本轮执行身份为当前 Codex GUI 聊天，未创建业务 attempt、claim 或 fence；夹具本身 `spec_rev=1`、`fence=0`、`current_attempt=null`。
- 复用 T-038 的 `start-dev.py`、`electron-final-web.json` 和 `desktop-final-proof.mjs` 中的启动方式：`dev:web`、offset 2038、Electron 43.4.1、已构建的 `dist-electron/main.js`，Electron 自行启动后端。无需另起 5811 后端。
- 新隔离根目录：`/Volumes/WD-Elements/dev-cache/synara/instances/t042-desktop`。从 T-038 的 `desktop-home/dev` 用 SQLite backup 复制 `state.sqlite`，复制 `a2a-gates`，复制 settings 后关闭 provider 和 provider 更新检查。没有复制 auth、secrets、codex overlay 或浏览器 profile。旧门禁 oracle 路径保留，本轮只读取门禁，不执行它。
- 独立的 desktop-home、profile/profile-02、HOME、XDG 目录、CODEX_HOME 和 CLAUDE_CONFIG_DIR 均在外置盘；启动日志确认 homeDir、workspace、state、profile 都指向隔离路径。未访问用户 Synara/浏览器数据或 `~/.codex`，未操作 Herdr。所有 Bun/Node 启动通过 fork 的 `a2a/scripts/bun`；未安装、下载或构建。
- fixture 的两任务与角色归属来自既有隔离输入；[门禁及 membership 只读导出](fixture-gate-membership.json) 保留其原始事件，旧事件不是本次执行记录。

## 实际过程与 T-038 对照

1. 先运行 project-map status，Problems 与 stale 均为 0；读取任务书、项目地图、术语、intent、两 ticket 和 T-038 记录。
2. 运行 `start.py`：新建隔离夹具，先运行 dev runner dry-run，再启动 Vite；[dry-run](dry-run.log) 确认端口 7771，[就绪记录](renderer-ready.json) 为 HTTP 200。启动前 5811/7771 均无监听。
3. 首轮 Electron PID 2240、后端端口 50932。Computer Use 按完整路径绑定；启动早期两次出现身份未就绪/歧义，未操作另一 Electron。成功绑定后看到 Synara Cua，然后自动打开 Developer Tools。保存 [初始截图](01-initial.png)。点击开发工具关闭按钮报 elementHasNoFrame，随后尝试 Cmd+W。其后检查发现进程已退出；不能确定退出是否由快捷键、异常还是其他原因导致。日志同时记录 GPU 异常退出（512）、后端最大约 239 秒停顿，不据此断言根因。
4. 首轮退出后使用同一候选和 `profile-02` 重试，PID 4531、后端端口 51898。Computer Use 关闭自动打开的开发工具，看到 [主窗口公告](02-root-loading.png)。依次点击 Safari 导入提示的 Not now、项目导入的 Not now、AppSnap 的 Not now，再点击 Skip tour；均成功关闭。没有打开系统设置、授予权限、导入登录信息或导入项目。这些是应用公告，不是系统权限对话框。
5. 点击真正的“任务窗口”链接，进入 `http://localhost:7771/#/a2a`，保存原始 Electron 截图和完整 AX 文本。一次点击使用了已变化的元素索引，工具拒绝为 invalid element ID；刷新状态、关闭随后出现的导览，再从新索引点击成功。没有用 DevTools 注入状态、浏览器自动化替代界面操作或修改业务响应。
6. T-038 的“Not now 不关闭”在本轮成功路径未复现。源码 `apps/web/src/appNavigation.ts` 为 Electron 选择 hash history，界面真实链接是 `/#/a2a`，不同于 round6 直接导航的 `/a2a`。本轮没有重试该错误形式，也未抓取完整网络帧；因此不能宣称修复或彻底解释原 WebSocket 帧头异常。本轮只证明经正常 UI 可到达任务窗口。

## 复现与清理

所有脚本及命令记录都在本目录。初次准备命令（从 a2a 仓库执行）：

```sh
python3 evidence/2026-10-07-synara-batch2/T-042/desktop/start.py
```

`start.py` 拒绝覆盖现有外置根目录；重新运行必须选新的隔离目录和证据路径，保留本轮记录。Electron 启动使用 `isolation.json` 的 env，通过以下 argv（cwd 为 synara-t038）：

```sh
./a2a/scripts/bun run node /Users/luckye/Documents/Code/a2a/evidence/2026-10-07-synara-batch2/T-042/desktop/launch-electron.cjs
./a2a/scripts/bun run node /Users/luckye/Documents/Code/a2a/evidence/2026-10-07-synara-batch2/T-042/desktop/launch-electron-02.cjs
```

实际 env、argv、PID/进程组及退出码分别见 `isolation.json`、`vite-start.json`、`electron*-command.json`、`electron*-start.json`。UI 操作顺序见上节，所有输入经 `mcp__cua_repl`；截图取自 `app.getAXStateAndScreenshot()`，原始图像未裁切、未修改；工具返回实际为 JPEG，最初误用 .png 扩展名，原文件保留，另提供同字节 .jpg 副本。

结束运行 `python3 evidence/2026-10-07-synara-batch2/T-042/desktop/finish.py`。该脚本只终止启动记录对应的进程组。[清理记录](cleanup.json) 确认没有剩余进程，50932、51898、5811、7771 均无监听。[结束状态](project-map-status.txt) Problems 0、stale 0。没有改 MAP、ticket 或 AGENTS。

没有运行产品测试或再构建：本次无产品代码变更，验收是实际 Electron 导航、原始截图、AX 记录与夹具只读核对。首轮失败证据保留；这一成功样本不证明稳定性或性能提升。

独立只读核对对本次截图声明返回 PASS，见 [审查原文及文件核对说明](independent-review.md)。其结论不覆盖通用性或真实模型工作流。
