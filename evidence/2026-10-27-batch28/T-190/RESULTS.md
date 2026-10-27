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

## 装进 /Applications（2026-10-27，用户："装新版到 /Applications、重启后台，然后删掉 /private/tmp/a2a-lcu-demo 空仓库。正在跑的会话被打断没关系。"）

- 构建：`python3 build.py r1`（复制自 T-188，浅克隆已提交的 `e39357ae6`，`npm ci` + `npm run package:mac`），PASS；日志与 `build-r1.json` 在 `/Volumes/WD-Elements/a2a-evidence/2026-10-27-batch28/T-190/`。版本号仍是 0.1.5，未发 Release；包内 `a2a.revision` 为 `e39357ae6…`。
- 替换前运行情况：`install-before-ps.txt`。Enchanted 下有两个 Claude Code 终端（pid 6476、87938）和一个 agy worker（pid 91293）；按用户原话 SIGTERM 应用（6012）与后台（6142），它们随之结束。
- 替换：旧包移到 `/private/tmp/Enchanted-0.1.5-d68a5d50e.app` 暂存（可回退），新包 ditto 进 `/Applications`；`codesign --verify --deep --strict` 通过（ad-hoc）。`env -i /usr/bin/open -a` 启动，新后台 argv 的 `code_revision` 为 `e39357ae6…`，安装包内 `gates/core.ts` 含 T-190 的跳过。窗口显示“后台已连接”，原有项目都在。
- 删空仓库：删前核对 `/private/tmp/a2a-lcu-demo` 只有 `.git`、无提交、无 worktree（80K），然后删除。界面中 a2a-lcu-demo 行随即显示“目录不存在”。

没有做：在用户真实状态里发起认领来复验“已删仓库不再拖垮认领”（会在用户项目里留下真实任务）；这一点只有隔离后台的红态、绿态证据。

## 第 4 轮：真实验收（2026-10-27，用户：“真实验证,用 codex,然后开工后面的”）

测试版 Enchanted Test 从 c754067a1 打包（后台 argv 的 code_revision 相同），状态目录仍是 `/private/tmp/t190/state`。新夹具仓库 `/private/tmp/t190/zeta`，三张卡分别派给真实 worker：

- T-5 Codex（gpt-6.1-sol high，用户自己的 `~/.codex`）：Codex 0.164 对未信任的 zeta 显示“Trust this folder?”，后台按 T-141 不代答，记 `codex_folder_trust_requested`（事件 6805），worker 停在信任框。属设计行为，不是缺陷；我撤销（`round4-probe/T5-revoke.json`）、结束这个测试进程后经门禁回收（`T5-reclaim.json`）。
- T-6 agy、T-7 opencode（`opencode/glm-5.3-flash-free`）：都交付到 `submitted`，后台记 `pane_idle`。

界面验收由 Codex `gpt-6.1-terra` high 用 Computer Use 操作（`ui-check-round4/BRIEF.md`、`REPORT.md`；截图可能含 agy 账户信息，只存 WD，见 `ui-check-round4.archive.json`）：

| 项 | 结果 |
| --- | --- |
| 四家 CLI 的 worker 行图标与名称（T-5 Codex、T-6 agy、T-7 opencode、lcu T-2 Claude Code） | PASS |
| agy、opencode worker 交付后侧栏为空闲 | PASS |
| zeta 带两个未回收 attempt 移除：弹窗列出 T-6、T-7，选“回收并移除”后 zeta 离开侧栏 | PASS |
| 普通终端里 agy、opencode 回合进行中转圈 | Codex 未截到（回合约 3～4 秒）；opencode 的 `-m` 是 opencode 自己不认的参数，说明写错 |

门禁核对：T-6、T-7 各有 `reclaim_intent` → `reclaimed`，任务回到 `ready`、current_attempt 为空；`project_removed` 的 `kept_attempts` 为空。

普通终端回合状态改用后台入口探针补证（`round4-probe/probe.py`：开项目终端 → 启动 CLI → 发问 → 每 0.3 秒读 `sidebar_snapshot` 的终端行与 `pane_status`；原始采样只存 WD，见 `round4-probe.archive.json`）：

- agy：发问后终端行 `running`（cli_turn `working`）13 个采样，随后 `idle`（`done`）。
- opencode：`running` 10 个采样，随后 `idle`。
- 长回合（agy，五段话）：`running` 89 个采样后 `idle`；回合进行中给 Enchanted Test 截图，侧栏为“普通终端 agy 运行中”并转圈（WD `round4-probe/ui-agy-running.jpg`）。

旁证：探针第一次在 beta 跑 agy 时，beta 还没被 agy 信任，我发的回车答了 agy 的信任框（写入用户 `~/.gemini` 的 trustedWorkspaces，属 T-187 用户批准的唯一全局配置例外）；那次采样只有信任框与空闲，未计入结论。

结论：T-190 三条验收 PASS；T-191 两条验收 PASS，普通终端回合状态 PASS。
