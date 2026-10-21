# T-121 结果：在项目终端里申请主控角色

日期：2026-10-21。实现与验收：Claude Code（Opus 5.5）。用户原话见 T-121 票。审查：每轮新开的只读 Claude 子会话（用户说“codex 太慢了”之后改用 Claude）。

**总状态：PASS**（最终候选 48a4f130b；第 7 轮复审结论见文末）。

## 候选与审查

| 候选 | 提交 | 审查 | 结论与处理 |
| --- | --- | --- | --- |
| 1 | b5feeae24 | `review-01.md` | 不可合并：B1（主控命令不限项目）等 |
| 2 | fa3ee8c67 | `review-02.md` | NO_GO：请求里加本项目的 `task` 字段可绕过项目限制；`create` 写成允许实际不可用；撤回只靠可捕获信号 |
| 3 | 99c3c9fba | `review-03.md` | NO_GO（范围小）：还不存在的任务 id 没有项目归属，可读写、抢占别项目的任务卡草稿 |
| 4 | 06276f2a8 | `review-04.md` | 可合并，前提是补齐 RESULTS 与两处测试缺口；同时用户提出同角色多申请的冲突要解决 |
| 5 | 6147b4678 | `review-05.md` | 可合并；授予须申请方确认才生效，确认回执丢失的窗口只缩小、未消除（照实写入下文） |
| 6 | 44220954e | `review-06.md` | 可合并；应修 S1（失效提示在同终端重新获批后仍误报） |
| 7 | 48a4f130b | `review-07.md` | 见文末 |

用户在实现期间的决定（逐字见 T-123、T-124、T-125 票）：任务卡冲突要按项目各自独立并迁数据（T-123）；同角色多个申请的冲突要解决（本票候选 5～7）；主控身份结束后已派出的工作继续做完（T-124）；凭据存放选 A（T-125 → T-126）。

## 验收条目与证据

| 验收条目 | 证据 | 结果 |
| --- | --- | --- |
| 真实入口：打包测试版里真实 Claude Code 按 skill 申请执行主控，界面批准后侧栏显示“执行主控”，`a2a` 报出的身份一致 | `ui-11/`（最终候选 48a4f130b 构建 t121-test-11，Haiku 5.5） | PASS |
| 未批准、被拒绝的申请与没有角色的终端调用主控操作都被拒绝，并留下拒绝记录 | `e2e-green-19.json`：`controller_command_refused_without_role`、`pending_request_has_no_authority`、`rejected_terminal_has_no_authority`、`role_refusals_recorded`、`rejection_recorded`、`grant_needs_confirmation` | PASS |
| 角色、窗格、项目由后台核对，窗格不能替别的窗格申请；同一项目同一主控角色只有一个已批准会话 | 同上：`forged_and_borrowed_tokens_refused`、`anonymous_request_refused`、`closed_terminal_identity_refused`、`role_held_by_one_terminal_per_project`、`one_role_per_terminal`、`approved_role_limited_to_its_project`、`commands_without_project_refused`、`task_field_does_not_widen_scope`、`other_project_task_and_repo_refused`、`other_project_draft_refused`、`other_terminal_draft_refused`、`confirmed_grant_settles_rivals` | PASS |
| 不写 `~/.claude`、`~/.codex` 和用户项目仓库 | 后台级：`user_startup_files_unchanged`、`nothing_written_into_app_resources`；真实入口：`ui-11/user-config-compare.txt` = same，`ui-11/project-repo-after.txt` 只有 init 提交、工作区与忽略文件为空 | PASS |
| 修前版本跑同一入口失败 | `e2e-red-01/02.json`（48d4da01b，失败于 `a2a_command_first_on_path`）；此后每个候选都在下一版测试上失败：`e2e-red-candidate-01`、`-candidate2-08`、`-candidate3-10`、`-candidate4-13`、`-candidate5-18`、`-candidate6-19` | PASS |
| `project_map.py status` 0 问题 | 关票提交前运行，Problems 0、Stale 0 | PASS |

## 后台级端到端

真实后台、socket、zsh 经 ZDOTDIR 引导、`a2a` 命令；夹具 claude 只记录参数，不调用模型。

重跑：`python3 workbench/tests/test_t121_role_request_e2e.py --summary <新路径>.json`；变异体加 `--mutant <名字>`，修前版本加 `--revision <提交>`。

最终候选：`e2e-green-19.json` **PASS，48 项**。13 个变异体（`e2e-mutant-<名字>-19.json`）全部 INCOMPLETE：

| 变异体 | 改坏的地方 | 失败于 |
| --- | --- | --- |
| pending-authority | 待批准即有权限 | `pending_request_has_no_authority` |
| grant-has-authority | 授予（未确认）即有权限 | `grant_needs_confirmation` |
| expiry-unrecorded | 未确认的授予不写作废事件 | `grant_needs_confirmation`（迟到的确认仍成功） |
| stale-notice | 失效提示不因同终端再次申请而撤下 | `grant_needs_confirmation`（提示筛选） |
| rivals-left-pending | 确认生效时不拒绝同角色对手 | `confirmed_grant_settles_rivals` |
| refusal-unrecorded | 拒绝不写事件 | `role_refusals_recorded` |
| task-widens-scope | `task` 字段放宽项目边界 | `task_field_does_not_widen_scope` |
| drafts-unowned | 草稿不记归属 | `other_project_draft_refused` |
| foreign-owned-save | 可写别的终端已拥有的草稿 | `other_terminal_draft_refused` |
| history-in-zdotdir | 删掉 HISTFILE 修正 | `history_goes_to_user_home` |
| zdotdir-dropped | 不恢复用户 ZDOTDIR | `user_zdotdir_kept` |
| no-withdraw | 申请方断开不撤回 | 前置断言“后台没有出现待批准的申请” |
| approved-not-ended | 已授予的申请方断开不结束 | 前置断言“后台没有出现待批准的申请” |

如实说明：

- no-withdraw 与 approved-not-ended 不是在具名检查上失败，而是被杀的申请残留，导致后面的场景等不到新的待批准申请。它们确实被拦下，但失败点不直接指向变异处。
- `e2e-mutant-foreign-owned-save-13.json` 在 7 个测试并行、负载很高时失败于无关的 `request_command_returns_after_approval`（时间相关）；单独重跑的 `-14` 失败于 `other_terminal_draft_refused`。此后变异体分两批跑，没有再出现。
- `e2e-mutant-01.json` 曾误报 PASS（测试缺陷：变异源码在 `cli` 路径确定后才设置），保留作证据，已修。
- 早期运行发现：macOS `/etc/zshrc` 按 `ZDOTDIR` 推出 `HISTFILE`，终端历史被写进 `workbench/terminal/zdotdir/.zsh_history`（只有测试命令，已删除）。现由 Enchanted 的 `.zshrc` 改回用户目录。

历次绿态、变异与红态文件按轮次编号保留在本目录（green-01～19、mutant-*、red-*），每个文件记录当时的检查清单与错误。

### 回归

最终候选：`regress-t107-08`（12 项）、`regress-t109-08`（9 项）、`regress-t111-08`（6 项）、`regress-t118-08`（2 项）全部 PASS。T-107 用 `LC_ALL=C` 运行：该测试断言英文的 `ahead 1, behind 1`，中文 locale 下 git 输出“领先 1, 落后 1”（`regress-t107.json`、`-t107b.json`，测试自身的 locale 依赖，修前版本同样如此）。`regress-t111-03.json` 失败：当时的实现用了 T-111 测试 vm 环境里没有的 `AbortController`，已改为普通回调对象，`-04` 起 PASS。

## 真实入口：打包的 Enchanted Test + 真实 Claude Code

重跑：

```
node workbench/app/package.mjs --slot <槽> --variant test
zsh evidence/2026-10-21-batch19/T-121/t121run.sh "<构建目录>/Enchanted Test.app" <端口> <输出目录> claude-haiku-5-5
```

应用数据隔离在 `/private/tmp`；终端里是用户自己的 claude 与正常登录。驱动 `t121drive.mjs` 扮演用户：在信任目录提示里选 “Yes, I trust this folder”，输入“你去做这个项目的执行主控。”，等批准按钮可点后点“批准”，Claude 回合结束后输入 `!a2a whoami`。用户 2026-10-21 要求真实 Claude 界面测试用 Haiku，ui-09 起改用 `claude-haiku-5-5`。

| 目录 | 模型 | 结果 |
| --- | --- | --- |
| `ui-01/` | Sonnet | 作废：驱动在信任提示里直接回车，默认选中 “No, exit” |
| `ui-02/` | Sonnet | 失败：点“批准”报 `Invalid role request decision`（主进程参数名改名时误改） |
| `ui-03/`～`ui-08/` | Sonnet | PASS（中间候选；ui-05 起记录项目仓库读回） |
| `ui-09/` | Haiku | PASS（候选 5 + 窗格标签居中） |
| `ui-10/` | Haiku | **不完整**：候选 6。横幅、标签、侧栏、事件 PASS；`whoami` 没有核对，原因是驱动只认 ASCII 的回合结束词，没认出 “Sautéed for 1m 8s”，也没把漏掉记为失败。驱动已修（认任意字母，漏核对记为失败），不改写本轮结论 |
| `ui-11/` | Haiku | **PASS，最终候选 48a4f130b**：见下 |

`ui-11` 的事实：

- Claude Code 自己加载 `enchanted-a2a:a2a` skill，执行 `a2a request executor`。
- 横幅“demo 的第 1 个窗格里的 claude 申请成为执行主控”，编号 1；申请窗格的标签“申请 1 · 执行主控”与之一致。
- 点批准后侧栏为“执行主控 · 项目终端 · claude · 未知”；`!a2a whoami` 输出 `"project": "demo"`、`"role": "executor"`。
- 后台库读回（`readback.json`）：`role_requested`、`role_request_decided`、`role_request_confirmed`，同一申请。
- 用户配置前后一致（`user-config-compare.txt` = same）；测试项目仓库只有 init 提交。

## 已知边界

- **确认回执窗口（review-05/06）**：确认生效后、`a2a request` 打印结果前进程被杀，角色仍有效而 agent 没看到输出。没有回执的协议无法消除这一段；`a2a whoami` 随时可查实际身份。确认表示“这个终端认了”，同一终端里的其他进程也能代发确认。
- **授予期间的申请**：授予前已在等待的同角色申请保持待批准（再批准返回 `role_taken`），确认生效时被拒绝（`role_given_to_other`）；授予期间新来的同角色申请当场返回 `role_taken`，授予作废后也不会回来，需要重新申请。
- **作废记录**：未确认的授予由后台进程内定时器写 `role_request_ended(not_confirmed)`；终端关闭、后台重启导致的结束只按终端是否存活推导为 `terminal_gone`，不写事件，审计时结合 `shell_closed`、`daemon_started` 看。失效提示按墙钟显示 5 分钟，只影响界面显示。
- **凭据可读**：操作员凭据文件在终端能推出的数据目录里，有意绕过的 agent 能读到并批准自己。用户已选 T-125 的 A，落地是 T-126：挡住顺着路径读取与按说明误用，挡不住有意搜索磁盘。
- **任务卡按全局 id 存**：用“首次保存的终端项目拥有该草稿”挡住越界读写，一个项目先占的 id 另一个项目用不了。用户决定按项目独立并迁数据：T-123。
- **四个门禁命令不对终端开放**：`answer_issue`、`answer_issues`、`attach`、`run` 返回 `role_command_not_scoped`。T-124 开放它们，回答按调用者记录，主控身份结束后已派出的工作照常做完。
- 新项目还没有任务时 `inbox_ready` 返回 `unknown_project`（ui-05 与 ui-10、ui-11 里 Claude 都如实报告了）：T-122。
- 已批准的主控没有结构化回合信号，侧栏状态显示“未知”。
- Codex 主控的挂法只在 T-120 探针里验证过，没有跑 GUI 全流程；workspace-write 沙箱下 Codex 不能连 Unix socket（T-075 实测）。
- 用户绕开包装、直接调用 CLI 的真实路径时读不到说明，只剩 `a2a help`；嵌套 zsh 不经 Enchanted 引导，包装可能排到 PATH 后面。
- 界面改动只在 ui-11 的单申请流程里实跑；多申请编号、“等待确认”行、失效提示、按钮暂停由后台快照字段的端到端检查与代码审查覆盖，没有 GUI 截图。

## 审查

- `review-01.md`～`review-06.md`：结论见上表，各轮探针在 `review-0N-probe/`。
- `review-07.md`：（待填）
