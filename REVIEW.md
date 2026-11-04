# REVIEW.md

审查本仓库的改动时先读这里；流程与验收规则以 AGENTS.md 为准。

## Acceptance surfaces

实现期间冻结：改了就是改需求，应撤回改动或先问项目所有者。任务卡的验收文件（`oracle_paths`）由门禁逐票保护，不在这里重复列出。

- `acceptance/**`

## Sensitive paths

改到这里走高档审查：两个审查 skill 都要跑，再由项目所有者读证据后批准。写明“中……的代码”的条目，只在改到那部分时适用。

- `workbench/src/credentials.ts`、`workbench/src/desktopCredentials.ts`、`workbench/src/claudeLogin*`、`workbench/src/claudeForwarder*` — 失败表现：凭据或 OAuth 令牌进了仓库、命令记录或截图；Claude 登录动到用户真实 HOME 下的 `.claude`、`.claude.json` 或钥匙串。
- `workbench/src/roleRequests.ts`、`workbench/src/gates/rolePermissions.ts` — 失败表现：角色申请没经用户在界面批准就生效，或终端关闭后角色仍有效；签发给角色的能力超出默认值或用户在设置里保存的选择。
- `workbench/src/claudeLaunch.ts`、`workbench/terminal/plugin/*/hooks/**`，以及 `workbench/src/panes.ts` 中写 agy 信任的代码 — 失败表现：写了用户的 `~/.claude`、`~/.codex` 等全局配置；agy 信任没核对信任框就确认，或 `settings.json` 除了多出本会话目录还有别的变化。
- `workbench/app/build.mjs`、`workbench/app/package.mjs`、`workbench/app/RUN-OUTSIDE-*.sh`、`workbench/src/hcDistribution.mjs` — 失败表现：构建或清理沿链接删掉源码与依赖（2026-10-08 曾误删 6,186 个受控文件），或安装包里的 hc 不是固定版本。
- `workbench/src/store.ts`、`workbench/src/relay.ts`、`workbench/src/gates/membership.ts`、`workbench/src/gates/core.ts` 中改表结构、迁移旧数据或删除 worktree 与目录的代码 — 失败表现：用户已有的数据目录（`a2a-orchestrator`）打不开、被改坏或丢数据；回收或清理删掉未提交的改动、失败现场或证据。

## What matters

全仓通用：提示词管判断，脚本管事实（T-070）；用户文字的含义交给模型识别，不用正则或关键词规则。

- `workbench/src/gates/`、`workbench/src/contracts/` — 失败表现：没过检查串的交付被集成，或集成后 push；验收、集成与清理没绑定原 attempt，被新的执行者接管；操作锁、fence、CAS 或中断恢复失效。
- `workbench/src/daemon.ts`、`workbench/src/panes.ts`、`workbench/src/hc.ts`、`workbench/src/paneRecovery.ts`、`workbench/src/transport.ts` — 失败表现：关掉界面或后台重启后 agent 被杀，或接回了错的 attempt；动到用户自己 Herdr 的 core、别的项目或别的会话；回合状态判错，提前回收 worker，或把模型自报当成完成；后台服务没脱离调用者的进程组，随命令结束被一并回收。
- `workbench/app/` — 失败表现：界面显示的任务、会话与回合状态和后台不符（如 T-235 的窗格标题栏落后于后台）；界面自己改任务状态，或另做一套门禁。
- `workbench/src/panes.ts`、`workbench/terminal/bin/` 中拼钩子、沙箱与可写目录参数的代码 — 失败表现：钩子与权限不经每会话的启动参数传入；可写目录超出派发时批准的范围（未指定额外目录时不给）。
- `workbench/src/panes.ts` 中启动会话的代码、`workbench/src/terminalClis.ts`、`workbench/terminal/bin/`、`workbench/terminal/zdotdir/` — 失败表现：启动记录缺了完整启动参数（含模型与思考强度），报不出的模型与强度没记成 `unknown`，或按 CLI 版本拒绝；shim 改了用户传给 CLI 的参数；窗格 shell 没加载用户自己的启动文件，或历史没写回用户自己的目录。
- `workbench/hooks/` — 失败表现：agent 会话的提交漏了提交尾注（会被当成用户本人的提交），或尾注记错任务、attempt、启动记录与模型。
- `workbench/roles/`、`.project-map/roles/`、`workbench/terminal/plugin/*/skills/`、`workbench/terminal/orientation/` — 失败表现：让角色做权限外的事（如审查员交付或集成、worker 扩大范围、monitor 宣布成功）；把能机械核对的事实留给提示词判断。
- `workbench/tests/` — 失败表现：期望值取自实现自己的输出；新测试在已知坏实现上不失败；`workbench/tests/HISTORICAL.md` 标为历史的测试被当成当前 main 的通过证据。
- `evidence/`、`records/`、`.project-map/inbox/` — 失败表现：改写已有记录；删除 run/fixtures 目录前没留简要状态；把未通过、未运行的检查写成 PASS；大文件、凭据或账号邮箱进了仓库。
- `scripts/` — 失败表现：Herdr 期的派发、启动脚本重新成为日常派发入口，与工作台门禁双写。
- `README.md`、`workbench/README.md`、`CONTEXT.md`、`AGENTS.md`、`intent.md`、`.project-map/`、`findings/`、`docs/` — 失败表现：与代码或证据不符；把用户没确认的说成“可用”；同一概念出现两个名字；改写日期记录，或报告另出英文副本；产品页连上后台或调用模型。

## Skip

- `workbench/package-lock.json`
- `evidence/**/*.log`、`evidence/**/*.jsonl`、`records/*.jsonl` — 机器追加的原始记录，不逐行审；删改已有行按上面 `evidence/` 一条处理。
