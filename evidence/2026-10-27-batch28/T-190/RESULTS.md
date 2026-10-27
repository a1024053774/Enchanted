# T-190 红态与绿态（隔离后台，真实入口）

入口：`workbench/src/gates/cli.ts`（门禁命令）与 `src/transport.ts` 的 `request`（界面用的同一条后台请求），数据目录 `/private/tmp/t190/state`，与用户的后台无关。

步骤：两个仓库 alpha、beta 各建一张卡并建任务；认领 alpha+T-1；删掉 alpha 仓库目录；认领 beta+T-1。

- 红态（修前代码）：`red-claim-beta.json`，`command_unavailable`，`git -C /private/tmp/t190/alpha rev-parse … --git-common-dir`，`spawn git ENOENT`。与用户 2026-10-27 第二次使用的报错相同。
- 绿态（`gates/core.ts` 跳过已不存在的仓库后，重启同一后台）：`green-claim-beta.json`，`ok: true`。
- 移除：`remove-alpha-ask.json` 列出未回收 attempt；`remove-alpha-keep.json` 保留并移除成功；`remove-beta-reclaim.json` 回收失败如实返回（夹具 attempt 没有绑定会话，`no_bound_thread`），不移除；`sidebar-after-remove.txt` 只剩 beta；`reopen-beta.json` 与 `sidebar-after-reopen.txt`：移除后重新打开同一目录，项目号与 1 个任务都回来。

没有覆盖：真实会话绑定的 attempt 经“回收并移除”成功的正例；界面操作由 Codex Computer Use 另做（见同目录 UI 验收记录）。

重跑：`bash g.sh daemon_start` 后按上面步骤调用 `g.sh card_save/create/claim` 与 `node call.ts '<json>'`。

## 界面验收（Codex `gpt-6.1-terra` high，Computer Use，打包的 Enchanted Test）

- 第 1 轮：对未打包的 Electron 开发版，Computer Use 读不到窗口（无障碍树为空，连接超时），BLOCKED；报告被我清空目录时删掉，结论见会话终端输出。之后改用 `node app/package.mjs --slot … --variant test` 打包。
- 第 2 轮（`ui-check-round2/`）：INCOMPLETE。1～5、7 项 PASS（gamma 显示“目录不存在”；空终端为空闲；移除 epsilon 提示先关终端；beta、gamma 列出 T-1 后“保留并移除”；重新打开 beta 后 T-1 仍在；浅色深色截图）。第 6 项 FAIL：终端行副标题“项目终端 · opencode”被截成“op…”。已改为终端行只显示 CLI 名。
- 第 3 轮（`ui-check-round3/`）：BLOCKED。名称完整显示 PASS；深色下 opencode 图标可见。opencode 本轮没有可用模型（“Connect an integration”），没能发出回合，所以“运行中 → 空闲”的切换没有验证。

未验证：普通终端里 agy、opencode 回合进行中时侧栏转圈、结束后回到空闲；真实会话绑定的 attempt 经“回收并移除”成功的正例。
