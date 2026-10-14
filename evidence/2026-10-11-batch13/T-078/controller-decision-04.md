# T-078-2 执行主控决定 04：PLAN-2 批准（P0）

时间：2026-10-11 22:1x；审阅对象：exec/t078 worktree `evidence/2026-10-11-batch13/T-078/PLAN-2.md`。依据：用户选择 C（answer `20261012T015257Z-ideation-answer-001`，原话"C 假服务为主，真登录复核 2～3 回合 (Recommended)"）。

批准 P0：按 PLAN-2 开始实施与无模型的静态/纯逻辑检查。附条件：
- 假服务阶段：每个 CLI 用 /tmp 下隔离 HOME 与 CLAUDE_CONFIG_DIR；环境白名单；假 key 为公开夹具字符串；不继承任何真实凭据；API 只绑 127.0.0.1；不代理外部服务。
- 真登录阶段：只替换构思主控接收者；用户正常 HOME，CLI 可自写本次 `~/.claude` 会话历史；不读、不复制、不枚举认证；`--settings` 只含批准的 hooks，不含权限或认证覆盖；默认 2 回合，第 3 回合另批。
- P1～P4 每次真实启动分别交完整 argv/env/hooks/预算给我批准，未批准不启动；所有 CLI、API、socket、Electron、进程信号步骤经 outside-sandbox.sh 由我运行。
- 不用 `--bare`（会跳过 hooks）；报告分清假服务证明与真模型证明。
- 合流（P5）等 T-076-2 提交后进行。

## P1 批准（2026-10-13 本地 11:1x，材料 p1-materials-02）

p1-materials-01 绑定的实例根已不存在，作废保留。审阅 p1-materials-02：实例根 `/private/tmp/t078-2-p1-02-dcmlidc0`，Claude Code 2.1.296，`--model claude-haiku-5-5 --effort low --permission-mode manual`，每会话 `--settings` 只含三个 hook（UserPromptSubmit/Stop/PermissionRequest → 本 launch 的 cli.ts signal），隔离 HOME 与 CLAUDE_CONFIG_DIR 在实例根内，ANTHROPIC_BASE_URL 为本地 127.0.0.1（端口启动时分配并写入 manifest 后才启动 CLI），ANTHROPIC_API_KEY 为公开夹具字符串；环境白名单；不继承真实凭据。批准 `p1-launch-02`（launch 阶段，不发送输入，停在初始 readiness 审批点）；continue 与 cleanup 阶段读回后另批。不花 Codex 或 Claude 模型额度。批准引用：`T-078 controller-decision-04 p1-02-launch`。

## P1 批准（材料 03，2026-10-13 本地 11:2x）

p1-launch-02 因 2.1.296 帮助中无 `--append-system-prompt-file` 在 CLI 启动前停止；已运行 p1-cleanup-02（PASS，无残留）。p1-materials-03 相比 02 只把该参数换成 `--append-system-prompt <角色卡原文>`，并换新 session/实例；其他 argv、环境白名单、隔离 HOME/CLAUDE_CONFIG_DIR、假 key、本地 API 不变。批准 `p1-launch-03`（launch 阶段，不发送输入）；continue/cleanup 读回后另批。不花模型额度。批准引用：`T-078 controller-decision-04 p1-03-launch`。

## p1-launch-03 读回与停止（2026-10-13 本地 11:3x）

真实 Claude Code 2.1.296 在隔离 HOME 下启动成功（launch e9d4ca48…，假 API 127.0.0.1:49351，模型回合 0）。经 operator 凭据读 pane_output：CLI 停在首次使用引导（主题选择），之后可能还有 API key 确认、目录信任等引导；假 API 未收到请求。按 PLAN-2 不把下一条输入或 Enter 当作同意，未运行 continue；运行 p1-cleanup-03（PASS）。cleanup 报 PASS 时 Claude 进程 16681 仍在，数秒后自行退出（我按 session-id 核对后准备 SIGTERM 时已不存在，未发信号）；最终无残留。缺口交 worker：引导需在隔离 CLAUDE_CONFIG_DIR/HOME 中以 CLI 文档化的配置预置，cleanup 须等到 CLI 进程确认退出才报 PASS。

## P1 引导预置的取舍（回应 issue 20261013T154915Z-worker:s13-t078s-issue-001，2026-10-13 本地 12:0x）

决定：先走选项 1——只用已文档化的机制（隔离 `claude/settings.json` 中 `"theme"`；环境 `IS_DEMO=1`）再做一次零模型探针，在出现任何 API key 批准或目录信任提示时停止并保存现场，不按 Enter、不选默认、不用 --bare、不换认证路线。目的：先以实测确认在 2.1.296 下实际还剩哪些提示，再决定是否需要授权读取固定 CLI 的内部状态格式（选项 2 涉及未文档化状态，留待实测后再定，必要时交用户）。cleanup 的进程退出核对修复认可，真实运行时一并验证。生成 p1-materials-05 并交审批。该 blocking issue 转构思主控备案，执行主控不关闭。

## P1 批准（材料 05，2026-10-13 本地 12:1x）

相比 03 只增加文档化的 `IS_DEMO=1` 与隔离 `claude/settings.json` 的 `{"theme":"dark"}`，换新实例与 ID。批准 `p1-launch-05`（launch，不发送输入）；遇 key/目录信任提示即停保存原文；continue/cleanup 读回后另批。批准引用：`T-078 controller-decision-04 p1-05-launch`。

## p1-launch-05 读回与 continue/cleanup 批准（2026-10-13 本地 12:1x）

仅用 IS_DEMO=1 与 theme 预置后，CLI 直接到主提示符（"Haiku 5.5 with low effort · API Usage Billing"、"Not logged in"），未出现主题、API key 批准或目录信任提示；未写任何未文档化内部状态。批准 `p1-continue-05`（向假 API 送一次 nonce 输入，无真实模型）与随后的 `p1-cleanup-05`。批准引用：`T-078 controller-decision-04 p1-05-continue`。

## p1-continue-05b 批准（2026-10-13 本地 12:2x）

continue-05 失败原因为缺 initial-ready.json（交接文件未生成），未发送输入。05b 只改 runner/wrapper/README，同一实例、launch、session、API 端口；继续前核对 manifest、API、就绪文件与 CLI 进程身份。批准 `p1-continue-05b` 一次（假 API，无真实模型）及随后的 cleanup。批准引用：`T-078 controller-decision-04 p1-05b-continue`。

## p1-continue-05b 读回（2026-10-13 本地 12:3x）

输入已登记并真实送达 CLI 提交（dispatch seq 1，屏幕显示 ⟦主控 #1⟧ P1_NONCE…），但 CLI 回答 "Not logged in · Please run /login"，假 API 未收到请求，runner 期限到即停（traceback 已记录）。结论：IS_DEMO 跳过了引导，但交互模式下 ANTHROPIC_API_KEY 仍需一次性批准（内部状态），文档化机制未覆盖。已运行 p1-cleanup-05b：PASS，无残留。下一步：只在假服务阶段评估文档化的替代认证——settings 的 `apiKeyHelper`（返回公开假 key）或 `ANTHROPIC_AUTH_TOKEN`——以官方文档为依据，零模型；真登录阶段不变。

## P1 批准（材料 06，2026-10-13 本地 14:2x）

相比 05 只把假服务阶段的 ANTHROPIC_API_KEY 换成 ANTHROPIC_AUTH_TOKEN（公开夹具字符串），依据官方 llm-gateway-connect 与 env-vars 文档；其余 argv/env/hooks、IS_DEMO、theme 不变，无 helper、无未文档化状态。批准 `p1-launch-06`（先外置归档 cleanup-05b 的 8,028,610 字节 fixture.tar.gz 并字节读回，再静态检查后启动，输入 0、模型 0）。continue/cleanup 读回后另批。批准引用：`T-078 controller-decision-04 p1-06-launch`。

## p1-launch-06 读回与 continue 批准（2026-10-13 本地 14:3x）

CLI 到主提示符，页脚无 "Not logged in"，无引导/key/信任提示。执行主控写入 p1-materials-06/readiness.json（confirmed_by executor）。批准 `p1-continue-06`（送原 nonce 一次，假 API 一条脚本化 SSE，真实模型 0）及随后 cleanup。批准引用：`T-078 controller-decision-04 p1-06-continue`。

## p1-continue-06 读回（2026-10-13 本地 14:3x）

AUTH_TOKEN 生效：假 API 收到 1 条 /v1/messages（CLI 的会话标题侧请求，含 nonce），不再报未登录。nonce 已送达并提交，窗格 busy、active 绑定本次 dispatch；但事件中没有 turn_start_signal（UserPromptSubmit hook 未登记），runner 以 "CR/hook did not establish the registered active submission" 停。屏幕显示 CLI 停在 "Forging…" 18 秒以上，假 API 只记录到标题请求、未见主回合请求。已运行 p1-cleanup-06：PASS，无残留。待 worker 只读诊断：(1) UserPromptSubmit hook 为何未落事件（hook 原始 stdin/退出、cli.ts signal 拒收原因）；(2) 假 API 是否串行阻塞在标题请求导致主请求未到。

## 用户决定：两个阶段都允许点一次目录信任（2026-10-14 UTC 01:17 收到）

依据 answer `20261014T011751Z-ideation-answer-001`（用户原话逐字："两个阶段都允许 (Recommended)"，见该条目"## 授权"）。执行：
- 假服务阶段：材料 08 = 07 基础上加 `CLAUDE_CODE_DISABLE_TERMINAL_TITLE=1`、去掉 `IS_DEMO`；/tmp 新建只含 value.txt 的夹具 repo，隔离 HOME/CLAUDE_CONFIG_DIR。启动后读回信任界面原文存证，由执行主控批准后用明确按键选一次"信任"，记录时间、原文、目录、按键。不写 CLI 内部状态，不碰用户 `~/.claude`。
- 真登录阶段：对 /tmp 夹具目录点一次信任，接受 CLI 在用户 `~/.claude.json` 写入一条信任记录；不改其他设置、不读不复制凭据；每回合仍逐次批准。
- blocking issue 20261013T182412Z：按此答复处理，不由执行主控关闭（--action forward）。

## P1 批准（材料 08 launch，2026-10-14 UTC 02:2x）

审阅 exec/t078 `58be5b71` 的 P1-APPROVAL-08：相比 07 去 IS_DEMO、加 CLAUDE_CODE_DISABLE_TERMINAL_TITLE=1 与 --debug-file，hook 原始 stdin/退出留证，信任拆为独立 Digit1 阶段（只写 ASCII 1、不补 Enter、一次性），新 /tmp 实例只含 value.txt、隔离 HOME/CLAUDE_CONFIG_DIR，无内部状态预置。批准 `p1-launch-08` 一次（启动、读屏，输入 0、模型 0）。screen/trust/continue/cleanup 读回后逐次另批。说明：本轮绑定变基前代码 721755d6，作为可行性探针；exec/t078 变基到 main 后须重新生成材料并完整重跑，旧结果不替变基后候选背书。批准引用：`T-078 controller-decision-04 p1-08-launch`。

## p1-launch-08 读回与 cleanup 批准（2026-10-14 UTC 02:2x）

读回 `p1-materials-08/launch/screen.bin`（3,576 字节，02:20:57Z）：去掉 IS_DEMO 后 CLI 停在首次引导的主题选择（"Let's get started. Choose the text style…"，光标在已勾选的 Dark mode），不是目录信任界面。按批准范围停下：不发送 Digit1（此处会选主题而非信任）、不按 Enter。批准 `p1-cleanup-08`（只停自建服务，核对 CLI 退出）。批准引用：`T-078 controller-decision-04 p1-08-cleanup`。

执行主控决定（范围内的执行细节，非用户保留事项）：隔离实例中的首次引导界面允许由执行主控逐屏读回后用明确按键选择，与信任步骤同样留证（时间、原文、目录、按键）；主题选择必须与 settings.json 的 theme（dark）一致，不用 Enter 选默认。理由：主题选择只影响隔离 HOME 内的显示偏好，不涉及权限、凭据、范围或用户数据；IS_DEMO 已证实会同时跳过信任界面，使 hooks 不生效（材料 05/06）。若引导中出现任何涉及权限、认证、遥测或数据共享的选择，停下交构思主控。真登录阶段用户 HOME 已完成引导，不受此决定影响。

构思主控（2026-10-14，跨会话消息）同意上述执行层决定，补充：①每屏读回原文与所按键都入证据；②真登录阶段在用户 HOME 出现任何引导屏（不只信任界面）一律停下交构思主控，不沿用本决定。照做。

## P1 批准（材料 08b launch，2026-10-14 UTC 02:5x）

审阅 exec/t078 `2d204c31`（产品 2f6d31ea：pane_trust 改为逐屏一次性 pane_screen_key，不留并行接口）。主题屏无数字编号，按官方 Select 操作用 ArrowUp/ArrowDown/Enter；Enter 只在读回已明确移到 Dark 后单独批准，后台拒绝默认 Enter。批准 `p1-launch-08b` 一次（启动、读屏，按键 0、模型 0）。每个按键逐屏读回后另批。批准引用：`T-078 controller-decision-04 p1-08b-launch`。

## p1-08b 逐屏按键读回与 cleanup（2026-10-14 UTC 02:48–02:5x）

- launch：PASS 启动，launch 自带 screen.bin 仅 13 字节（截取过早）。只读 `screen-theme-01`（3,576 字节）：首次引导主题屏，光标在已勾选 Dark mode。
- `theme-01` 批准 ArrowUp（onboarding-theme，目标 Auto）→ 发送；读回 `screen-theme-02`（3,746 字节），增量重绘光标到 Auto。
- `theme-02` 批准 ArrowDown（目标 Dark mode）→ 发送；读回 `screen-theme-03`（3,906 字节），增量重绘光标到 Dark mode。
- `theme-03` 批准 Enter（确认明确所选 Dark mode）→ 门禁拒绝 `theme_selection_not_explicit`，未写 PTY（读回 `screen-after-theme-01` 仍 3,906 字节）。按设计停，不重试。
- 批准并运行 `p1-cleanup-08b`：PASS，无残留进程。
结论：INCOMPLETE。门禁对"Enter 前一条登记导航须是从 Auto 的 ArrowDown"的核对与实际登记不符，属 2f6d31ea 新代码缺陷，交 worker 诊断（以 key-theme-0x/ 与 cleanup 归档为据），需修复后另起新实例。批准引用：`T-078 controller-decision-04 p1-08b-keys`。

## P1 批准（材料 08c launch，2026-10-14 UTC 03:0x）

审阅修复 95b69e04（selected_label 为按键目标项；Enter 须前两条依次为 ArrowUp→Auto、ArrowDown→Dark，默认 Enter 仍拒；以 08b 实际批准与屏幕原字节重放取得红/绿）与材料 e5c58e54（launch 只记录进程启动，首屏另行只读读取）。批准 `p1-launch-08c` 一次及随后逐屏只读 screen；每个按键逐屏另批。批准引用：`T-078 controller-decision-04 p1-08c-launch`。

## p1-08c 逐屏读回与 cleanup（2026-10-14 UTC 03:1x）

theme-01 ArrowUp→Auto、theme-02 ArrowDown→Dark、theme-03 Enter 确认 Dark：三步均被门禁接受并写入 PTY，主题屏结束（修复 95b69e04 在真实 CLI 上生效）。下一屏 `screen-after-theme-01`（4,685 字节）为 "Security notes: 1. Claude can make mistakes… 2. Due to prompt injection risks, only use it with code you trust… Press Enter to continue…"——无选项的安全提示确认。门禁无此用途，且内容涉及安全，按停止条件停下，未按键。批准并运行 `p1-cleanup-08c`：PASS，无残留。待构思主控确认：隔离假服务实例中，确认这条无选项的安全提示（单独批准一次 Enter、留证）是否属于已同意的引导屏决定。批准引用：`T-078 controller-decision-04 p1-08c-keys`。

构思主控（2026-10-14，跨会话消息）同意：隔离实例中确认无选项的 Security notes 属已同意的引导屏决定。条件：①onboarding-notice 只放行 Enter，读回原文须与 08c 读回的 Security notes 内容逐字一致，不同即停；②原文、按键、批准留证；③只适用隔离实例，真登录阶段用户 HOME 出现任何引导屏仍停下交构思主控。照此推进 08d。

## P1 批准（材料 08d launch，2026-10-14 UTC 03:3x）

审阅 f14d63df（onboarding-notice：仅 Enter；控制序列只做语法解析后与固定 SECURITY_NOTICE_TEXT 逐字比较，不支持的转义即拒，一次性；域检查 20/20 与文字变异反例）与材料 61868ce8。批准 `p1-launch-08d` 一次及逐屏只读 screen；主题三键与 notice Enter 逐屏另批。批准引用：`T-078 controller-decision-04 p1-08d-launch`。
