---
id: T-122
title: 主控用 a2a 派发 worker，可选 CLI；worker 与 reviewer 启动即定身份，自动挂到侧栏
type: build
status: open
blocked_by: [T-121]
claimed_by:
supersedes:
ready: yes
ready_by: ideation
ready_rev: 1
---

## What to build

来源：[T-119](T-119-herdr-style-terminals-claimed-roles.md)、[spec](../specs/herdr-style-claimed-roles-2026-10-21.md)。用户 2026-10-21 逐字：“现在只有主控能被我批准后认领,其他的 worker,reviewer 怎么认领呢?这些系统应该让模型通过 a2a 指令运行其他 cli 后自动识别放到侧边吧”。

已批准的执行主控用 `a2a` 派发：指定 CLI（Claude Code 或 Codex）、模型、强度和任务卡。后台在新窗格里带着 worker 角色的权限参数启动该 CLI：不弹批准窗口而越界即拒、可写路径限制、回合信号、会话可续接。每家 CLI 用一个启动适配提供这组能力。

worker 和 reviewer 不申请角色：后台启动时就把角色、任务、attempt 和派发它的主控写进启动记录。侧栏据此把 worker 挂在派发它的主控下面，reviewer 挂在对应任务下面，不需要用户批准，也不从终端文字推断。交付、独立审查、集成沿用现有门禁检查串。

T-121 独立审查指出、属于本票的两点（evidence/2026-10-21-batch19/T-121/review-01.md）：

- 经角色申请成为主控的项目终端不是已登记的会话线程，发给它的收件箱条目会停在 `role_session_missing`，收不到唤醒。
- 终端发起的门禁调用没有父 launch，它派出的 worker 在侧栏里会显示为“未归属”。本票要把派发关系记到这个终端上。

T-121 第 5 轮界面验收发现、属于本票的一点（evidence/2026-10-21-batch19/T-121/ui-05/ui-driver.json 的 final_screen）：

- 刚在工作台打开、还没有任务的项目，`inbox_ready` 返回 `unknown_project`。原因：门禁只经已有任务的 `project_id` 找项目仓库（`workbench/src/gates/core.ts` 的 `inboxCall`），不认工作台的 `project_open` 登记。主控在新项目里第一步就会卡住；本票要让门禁按已打开项目找到仓库。

实现期间的事实与用户决定（2026-10-21，证据 `evidence/2026-10-21-batch19/T-122/probe-01`～`probe-04`、独立审查 `review-01.md`）：

- 写入边界：Claude worker 以 `--permission-mode dontAsk` 启动，只允许 `Edit(//<worktree>/**)`、`Bash`、`Read`，开 shell 沙箱并禁止沙箱外命令；探针证实文件工具与 shell 都写不出 worktree。审查 01 发现 linked worktree 里 Claude 自己把主仓库整个 `.git` 设为可写，worker 能移动 `main`（probe-04 复现）；改为用 denyWrite 收回除本 attempt 分支外的已有 ref、packed-refs、HEAD 与其他 worktree。仍可新建分支名，`$TMPDIR` 仍可写（收回会让每条 shell 命令失败），记为限制。
- 不加载用户自己的 Claude 设置：用户的钩子（含 PreToolUse、PermissionRequest、Stop）会干扰权限与回合结束，worker 用 `--strict-mcp-config`，登录照常。设置来源原为 `local`；probe-04 证实 `local` 会加载主 checkout 的 `.claude/settings.local.json`，改为 `--setting-sources ""`，不加载任何设置文件。
- 信任对话框：worktree 不在用户信任过的目录下，Claude 启动必弹“是否信任此文件夹”。用户选“后台代按确认 (Recommended)”：只对 a2a 新建的 worktree、worker 还没收到任务时，后台代按信任并记事件；a2a 不写 `~/.claude.json`。
- 真实入口验收的 Claude worker 用 Haiku：用户选“Haiku (Recommended)”（此前用户原话：“然后真实的 claude 界面测试用 haiku 模型就行了”），与下方验收写的 Sonnet 不同，证据注明。
- 审查者（D24“默认与 worker 同为 Codex 同模型，项目设置可换模型或 CLI”）：Claude worker 的审查者也用 Claude Code，模型、强度、Fast 取该 worker 启动记录；reviewer 角色设置对 Claude 审查者暂不生效（审查 01 第 9 条，记为限制）。任务卡写 Claude Code 而派发不带模型时，以卡上的 executor 模型与强度为默认（worker 的出厂设置是 Codex 模型）。
- 打包的工作台以空的启动配置起后台（`workbench/app/desktop.mjs` 的 `startDaemon(state, {})`），产品里任何 worker 都起不来；本票补上产品的 worker 启动配置。

## Acceptance

- [ ] 真实入口：打包测试版里，T-121 经角色申请批准的真实 Claude Code 执行主控派发一个 Claude Code（Sonnet 5.5、medium）worker 到夹具仓库，经交付、独立审查、集成到夹具工作分支。截图、后台库事件读回、Git 引用读回、重现命令留证。
- [ ] 同一流程派发 Codex worker 仍然可用（回归）。
- [ ] 侧栏自动显示：worker 在派发它的主控下面，reviewer 在任务下面，角色、CLI、模型来自启动记录。
- [ ] Claude Code worker 的权限是强制的：越过任务卡路径的写入被拒并留下记录；启动 argv 完整记入启动记录。
- [ ] 没有已批准角色的会话、worker 自己都不能派发；修前版本（任务卡执行者只能是 Codex）跑同一入口失败。
- [ ] `project_map.py status` 0 问题。
