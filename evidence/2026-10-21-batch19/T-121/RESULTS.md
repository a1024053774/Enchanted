# T-121 结果：在项目终端里申请主控角色

日期：2026-10-21。实现与验收：Claude Code（Opus 5.5）。用户原话见 T-121 票。审查：新开的只读 Claude 子会话（用户说“codex 太慢了”之后改用 Claude）。

**总状态：待复审**（复审结论见文末“审查”一节）

候选：fa3ee8c67（第 2 版，处理 review-01），其后只加了一项测试检查（`role_refusals_recorded`）及其变异体，产品代码未变。

## 验收条目与证据

| 验收条目 | 证据 | 结果 |
| --- | --- | --- |
| 真实入口：打包测试版里真实 Claude Code 按 skill 申请执行主控，界面批准后侧栏显示“执行主控”，`a2a` 报出的身份一致 | `ui-05/`（最终代码构建 t121-test-05） | PASS |
| 未批准、被拒绝的申请与没有角色的终端调用主控操作都被拒绝，并留下拒绝记录 | `e2e-green-06.json`：`controller_command_refused_without_role`、`pending_request_has_no_authority`、`rejected_terminal_has_no_authority`、`role_refusals_recorded`、`rejection_recorded` | PASS |
| 角色、窗格、项目由后台核对，窗格不能替别的窗格申请；同一项目同一主控角色只有一个已批准会话 | `forged_and_borrowed_tokens_refused`、`anonymous_request_refused`、`closed_terminal_identity_refused`、`role_held_by_one_terminal_per_project`、`one_role_per_terminal`、`approved_role_limited_to_its_project`、`commands_without_project_refused`、`unknown_task_refused_before_gate` | PASS |
| 不写 `~/.claude`、`~/.codex` 和用户项目仓库 | 后台级：`user_startup_files_unchanged`、`nothing_written_into_app_resources`（夹具 HOME）；真实入口：`ui-05/user-config-before.txt` 与 `-after.txt` 一致（`user-config-compare.txt` = same）；项目仓库读回 `ui-05/project-repo-after.txt`：只有 init 提交，工作区与忽略文件均为空 | PASS |
| 修前版本跑同一入口失败 | `e2e-red-01/02.json`（48d4da01b，失败于 `a2a_command_first_on_path`）；`e2e-red-candidate-01.json`（第 1 版候选 b5feeae24，失败于 `commands_without_project_refused`，即 review-01 的 B1） | PASS |
| `project_map.py status` 0 问题 | 2026-10-21 收尾时运行：Problems 0、Stale 0 | PASS |

## 后台级端到端（真实后台、socket、zsh 经 ZDOTDIR 引导、`a2a` 命令；夹具 claude 只记录参数，不调用模型）

重跑：`python3 workbench/tests/test_t121_role_request_e2e.py --summary <新路径>.json`；变异体加 `--mutant <名字>`，修前版本加 `--revision <提交>`。

| 文件 | 对象 | 结果 |
| --- | --- | --- |
| `e2e-red-01.json`、`e2e-red-02.json` | 修前版本 48d4da01b | 失败于 `a2a_command_first_on_path`：用户的 `userbin` 排第一，`ELECTRON_RUN_AS_NODE=1` 漏进终端 |
| `e2e-green-01.json` | 第一版实现 | 后台起不来：Node 类型剥离不支持构造函数参数属性；已改 |
| `e2e-green-02.json` | 改名前实现 | PASS，27 项 |
| `e2e-mutant-01.json` | 变异体 pending-authority | **误报 PASS**：测试缺陷，变异源码在 `cli` 路径确定之后才设置，实际跑的是真实代码。保留作证据，已修 |
| `e2e-mutant-02.json`、`-03.json` | 同上，修正测试后 | 拦下 |
| `e2e-green-03.json` | 术语改名后 | 失败：`a2a request` 输出字段仍为驼峰；被拒时错误码引用了错变量；已改 |
| `e2e-green-04.json`、`e2e-mutant-04.json`、`e2e-mutant-history-01.json` | 第 1 版候选 b5feeae24 | PASS 29 项；两个变异体拦下 |
| `e2e-red-candidate-01.json` | 新测试跑第 1 版候选 | 失败于 `commands_without_project_refused`（B1） |
| `e2e-green-05.json` | 第 2 版候选 fa3ee8c67 | **PASS，35 项** |
| `e2e-mutant-pending-authority-05.json` | 待批准即有权限 | 失败于 `pending_request_has_no_authority` |
| `e2e-mutant-history-in-zdotdir-05.json` | 删掉 HISTFILE 修正 | 失败于 `history_goes_to_user_home` |
| `e2e-mutant-no-withdraw-05.json` | 申请命令被杀不撤回 | 失败于 `killed_request_withdrawn_and_not_approvable` |
| `e2e-mutant-zdotdir-dropped-05.json` | 不恢复用户 ZDOTDIR | 失败于 `user_zdotdir_kept` |
| `e2e-green-06.json` | fa3ee8c67 + 新检查 `role_refusals_recorded` | **PASS，36 项** |
| `e2e-mutant-refusal-unrecorded-06.json` | 删掉 `request_rejected` 事件写入 | 失败于 `role_refusals_recorded` |

`e2e-green-03` 之前的运行发现：macOS `/etc/zshrc` 按 `ZDOTDIR` 推出 `HISTFILE`，终端历史被写进了 `workbench/terminal/zdotdir/.zsh_history`（内容只有测试命令，已删除）。现由 Enchanted 的 `.zshrc` 改回用户目录。

### 回归

| 文件 | 测试 | 结果 |
| --- | --- | --- |
| `regress-t118-01.json`、`-02.json` | T-118 终端环境 | PASS |
| `regress-t107.json`、`-t107b.json` | T-107 侧栏，默认中文 locale | INCOMPLETE：测试断言英文 `ahead 1, behind 1`，本机 git 输出“领先 1, 落后 1”。测试自身对 locale 的依赖，与本票无关，修前版本同样如此 |
| `regress-t107c.json` | 同上，`LC_ALL=C` | PASS |
| `regress-t109.json` | T-109 层级 | PASS |
| `regress-t111.json` | T-111 反例（`--daemon`） | PASS |

回归在第 2 版候选的逻辑改动之后运行；其后只改了 SKILL.md、`a2a help` 与 README 的文字。

## 真实入口：打包的 Enchanted Test + 真实 Claude Code

重跑：`evidence/2026-10-21-batch19/T-121/t121run.sh "<Enchanted Test.app>" <端口> <输出目录> claude-sonnet-5-5`，构建：`node workbench/app/package.mjs --slot <槽> --variant test`。应用数据隔离在 `/private/tmp`；终端里是用户自己的 claude 与正常登录。驱动扮演用户：在信任目录提示里选 “Yes, I trust this folder”，输入“你去做这个项目的执行主控。”，看到申请横幅后点“批准”，再在 Claude 里输入 `!a2a whoami`。

| 目录 | 构建 | 结果 |
| --- | --- | --- |
| `ui-01/` | t121-test-01 | 作废：驱动在信任提示里直接回车，默认选中 “No, exit”，Claude 退出 |
| `ui-02/` | t121-test-02 | 失败：点“批准”报 `Invalid role request decision`（主进程参数名改名时误改）。`99-failure.png` |
| `ui-03/` | t121-test-03 | PASS（第 1 版候选之前） |
| `ui-04/` | t121-test-04 | PASS，但构建早于最后几处文字修改，不作最终结果 |
| `ui-05/` | t121-test-05，即 fa3ee8c67 的工作区 | **PASS**：见下 |

`ui-05` 的事实：

- Claude Code 2.1.306，Sonnet 5.5 medium，自己加载了 `enchanted-a2a:a2a` skill，执行 `a2a request executor`（`04-roleRequest-banner.png`）。
- 横幅文字“demo 的一个终端里的 claude 申请成为执行主控”，申请窗格加框；点批准后侧栏为“执行主控 · 项目终端 · claude · 未知”（`05-sidebar-executor.png`）。
- `!a2a whoami` 输出 `"project": "demo"`、`"role": "executor"`，申请状态 approved（`07-whoami.png`、`ui-driver.json` 的 `whoami_screen`）。
- 后台库读回（`readback.json`）：`role_requested`（role=executor、project=demo、cli=claude）与 `role_request_decided`（approved=true），同一 launch；侧栏 agent 一条，`terminal: true`。
- 用户配置文件前后一致：`~/.claude/settings.json` 10062 字节、`~/.claude/settings.local.json` 不存在、`~/.codex/config.toml` 18012 字节，修改时间不变。

**本轮发现（交给 T-122）**：获批后 Claude 调用 `inbox_ready`（project=demo），门禁返回 `unknown_project`。门禁只经已有任务找项目仓库，不认工作台刚打开、还没有任务的项目。Claude 如实报告 BLOCKED，没有换名重试，也没有去动后台数据目录。这不在 T-121 验收内，但主控在新项目里第一步就会卡住，已写进 T-122。

## 已知边界

- **凭据可读（交用户决定）**：终端环境导出 `A2A_STATE`，操作员凭据文件在该目录下，同一用户的进程都能读。能读文件的 agent 可以拿它调用 `role_request_decide` 批准自己。所以“界面批准”现在防的是 agent 按说明自封身份，**不防一个有意绕过的 agent**。要防后者，需要把操作员凭据移出终端能推出的位置（例如只放在主进程内存或钥匙串），这改变凭据存放方式，超出本票范围。
- 已批准的主控没有结构化回合信号，侧栏状态显示“未知”。
- Codex 主控的挂法（`-c developer_instructions`）只在 T-120 探针里验证过，没有跑 GUI 全流程。用户的 Codex 是 `danger-full-access`，能连后台 socket；如果是 workspace-write 沙箱，会被拒绝连 Unix socket（T-075 实测）。
- 用户绕开包装、直接调用 CLI 的真实路径时，读不到说明，只剩 `a2a help`。
- 嵌套的 zsh 会重新加载用户的启动文件，不经 Enchanted 引导，包装命令可能排到后面；PATH 里 `a2a` 仍在。
- 终端关闭、后台重启导致的角色结束靠终端是否存活推导，不写 `role_request_ended` 事件。
- 终端主控收不到收件箱唤醒，派出的 worker 会显示为未归属：T-122。

## 审查

- `review-01.md`：第 1 版候选 b5feeae24，**不可合并**（B1 等），处理见其中的表。
- `review-02.md`：第 2 版候选 fa3ee8c67，（待填）
