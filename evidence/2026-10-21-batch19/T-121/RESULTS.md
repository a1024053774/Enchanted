# T-121 结果：在项目终端里申请主控角色

日期：2026-10-21。实现与验收：Claude Code（Opus 5.5）。用户原话见 T-121 票。

## 后台级端到端（真实后台、socket、zsh 经 ZDOTDIR 引导、`a2a` 命令；夹具 claude 只记录参数，不调用模型）

重跑：`python3 workbench/tests/test_t121_role_request_e2e.py --summary <新路径>.json`

| 文件 | 对象 | 结果 |
| --- | --- | --- |
| `e2e-red-01.json` | 修前版本 48d4da01b（`--revision`） | 失败于 `a2a_command_first_on_path`：用户的 `userbin` 排在第一，`ELECTRON_RUN_AS_NODE=1` 漏进终端 |
| `e2e-red-02.json` | 同上，改名后的测试 | 同样失败 |
| `e2e-green-01.json` | 第一版实现 | 后台起不来：Node 类型剥离不支持构造函数参数属性；已改 |
| `e2e-green-02.json` | 改名前实现 | PASS，27 项 |
| `e2e-mutant-01.json` | 变异体 pending-authority | **误报 PASS**：测试缺陷，变异源码在 `cli` 路径确定之后才设置，实际跑的是真实代码。保留作证据，已修 |
| `e2e-mutant-02.json` | 同上，修正测试后 | 失败于 `pending_claim_has_no_authority`（拦下） |
| `e2e-green-03.json` | 术语改名后 | 失败：`a2a request` 输出字段仍为驼峰；另发现被拒时错误码引用了错变量；已改 |
| `e2e-mutant-03.json` | 改名后变异体 | 拦下 |
| `e2e-green-04.json` | 当前实现 | **PASS，29 项** |
| `e2e-mutant-04.json` | 变异体 pending-authority | 失败于 `pending_request_has_no_authority`（拦下） |
| `e2e-mutant-history-01.json` | 变异体 history-in-zdotdir（删掉 HISTFILE 修正） | 失败于 `history_goes_to_user_home`（拦下） |
| `regress-t118-01.json` | T-118 终端环境回归 | PASS |

`e2e-green-03` 之前的运行发现：macOS `/etc/zshrc` 按 `ZDOTDIR` 推出 `HISTFILE`，终端历史被写进了 `workbench/terminal/zdotdir/.zsh_history`（内容只有测试命令，已删除）。现在由 Enchanted 的 `.zshrc` 改回用户目录，测试新增 `history_goes_to_user_home` 与 `nothing_written_into_app_resources`。

## 真实入口：打包的 Enchanted Test + 真实 Claude Code

重跑：`evidence/2026-10-21-batch19/T-121/t121run.sh "<Enchanted Test.app>" <端口> <输出目录> claude-sonnet-5-5`（应用数据隔离在 `/private/tmp`；终端里是用户自己的 claude 与正常登录，与日常使用相同）。驱动脚本扮演用户：在 Claude 的信任目录提示里选 “Yes, I trust this folder”，输入“你去做这个项目的执行主控。”，看到申请横幅后点“批准”。

| 目录 | 构建 | 结果 |
| --- | --- | --- |
| `ui-01/` | t121-test-01 | 作废：驱动在信任提示里直接回车，而该版本默认选中 “No, exit”，Claude 退出。驱动已改为先选中 Yes 再回车 |
| `ui-02/` | t121-test-02 | 失败：Claude 加载了 `enchanted-a2a:a2a` skill，执行 `a2a request executor`，横幅出现且窗格加框；点“批准”报 `Invalid role request decision`（主进程参数名在改名时被误改）。截图 `99-failure.png` |
| `ui-03/` | t121-test-03 | **PASS**：横幅“demo 的一个终端里的 claude 申请成为执行主控”，申请窗格加框；批准后侧栏显示“执行主控 · 项目终端 · claude”；Claude 回报已获批，并用 `inbox_list` 读收件箱。读回 `readback.json`：`role_requested`（cli=claude）与 `role_request_decided`（approved=true） |

Claude Code 2.1.306，Sonnet 5.5 medium。`06-terminal-after.png` 拍于批准后约 7.5 分钟（驱动的结束条件没匹配上，等到 8 分钟上限），所以侧栏时间显示“7 分”。

## 已知边界

- 已批准的主控没有结构化回合信号，侧栏状态显示“未知”。可以在插件里加 hooks 补上，留给后续票。
- Codex 主控的挂法（`-c developer_instructions`）只在 T-120 探针里验证过，没有跑 GUI 全流程。用户的 Codex 是 `danger-full-access`，能连后台 socket；如果是 workspace-write 沙箱，会被拒绝连 Unix socket（T-075 实测）。
- 用户绕开包装、直接调用 CLI 的真实路径时，读不到说明，只剩 `a2a help`。
- 嵌套的 zsh 会重新加载用户的启动文件，不经 Enchanted 引导，包装命令可能被排到后面；PATH 里 `a2a` 仍在。
- 同一台机器上，同一用户的其他进程可以读到终端环境里的令牌（与操作员凭据文件同一威胁模型）；用户批准这一步防的是模型自封身份，不防本机恶意进程。
