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

## p1-08d 逐屏读回与 cleanup（2026-10-14 UTC 03:4x）

主题三键（theme-01..03）与 Security notes（notice-01，文字与 08c 逐字一致，Enter，selected_label=Continue）均被门禁接受并写入 PTY。下一屏 `screen-after-notice-01` 为目录信任："Accessing workspace: /private/tmp/t078-2-p1-08d-ohyh5win/repo … Quick safety check: Is this a project you created or one you trust? … Claude Code'll be able to read, edit, and execute files here." 选项无数字编号：`❯ No, exit`（光标、默认）/ `Yes, I trust this folder`；"Enter to confirm · Esc to cancel"。原字节确认无数字标签，Digit1 无依据且可能选中 "No, exit"，故不发 Digit1、停下。批准并运行 `p1-cleanup-08d`：PASS，无残留。
决定：信任改为与主题同一显式选择方式——单独批准 ArrowDown（目标 "Yes, I trust this folder"）→ 读回光标位置 → 单独批准 Enter 确认；属用户 "用明确按键选一次'信任'" 授权范围内的执行细节。交 worker 改门禁 workspace-trust 用途并起 08e。批准引用：`T-078 controller-decision-04 p1-08d-keys`。

## P1 批准（材料 08e launch，2026-10-14 UTC 03:5x）

审阅 ab997f4d（workspace-trust 改为 ArrowDown→"Yes, I trust this folder"，读回后单独 Enter；去 Digit1；默认 Enter、重复确认拒绝；域检查 30/30）与材料 e5768e54。批准 `p1-launch-08e` 一次及逐屏只读 screen；主题三键、notice Enter、信任两键逐屏另批。批准引用：`T-078 controller-decision-04 p1-08e-launch`。

## p1-08e 逐屏读回、信任与 continue 批准（2026-10-14 UTC 04:0x）

主题三键、Security notes（逐字一致）均生效。信任屏 `screen-trust-01`：目录 `/private/tmp/t078-2-p1-08e-8k1yyjw5/repo`（只含 value.txt），选项 `❯ No, exit` / `Yes, I trust this folder`。依用户授权 answer 20261014T011751Z（"两个阶段都允许 (Recommended)"），批准 trust-01 ArrowDown（目标 Yes）→ 读回光标在 Yes（screen-trust-02）→ 批准 trust-02 Enter，一次。读回 `screen-after-trust-01`：主提示符 "Claude Code v2.1.296 · Haiku 5.5 with low effort · API Usage Billing"，manual mode，无未登录或其他提示。执行主控写 readiness.json（confirmed），批准 `p1-continue-08e` 一次（一条 nonce，假 API 一条脚本化 SSE，真实模型 0）及随后 cleanup。批准引用：`T-078 controller-decision-04 p1-08e-continue`。

## p1-continue-08e 读回与 cleanup（2026-10-14 UTC 03:5x）

continue PASS，逐项独立核对：dispatch seq 1 由 executor 登记、paste+单独 CR 提交；UserPromptSubmit 与 Stop hook 均实际触发、exit 0，原始 stdin 已留（含 session/prompt_id/hook_event_name）；门禁事件 hook_received → turn_start_signal … hook_received → turn_end_signal → pane_idle；状态 busy（active 绑定该 dispatch）→ idle；假 API 收到主回合 Messages 请求（model claude-haiku-5-5，含 nonce）；会话 transcript 记 stop_hook 成功。真实模型 0。材料 06 中缺失的 hook 信号由目录信任解决，确认。cleanup-08e PASS，无残留；cleanup/fixture.tar.gz 8,103,787 字节经 archive_t078_evidence.py 外置归档、字节读回 PASS（manifest external-archive-73249ada…）。
说明：本轮绑定变基前代码（ab997f4d/e5768e54），是可行性证明；变基到 main 后须完整重跑。下一步：材料 09（Esc 释放、二次送达、紧急停止），以及 T-078-1 变基合并。

## P2 批准（材料 09A launch，2026-10-14 UTC 05:3x）

审阅 5510ee72（按真实 prompt_id 关联回合、Esc 登记并释放 active、nullable 主控窗口核对 leader、显式 turn_limit=2、假 API 并发两请求；红态 4 组与有效反例 4 个）与材料 7eecdd4d。批准 `p1-launch-09` 一次及逐屏只读 screen；引导与信任按键逐屏另批（同 08e）。continue 前另批 readiness 与 actions-approval。09B/09C 未冻结，不批。批准引用：`T-078 controller-decision-04 p2-09a-launch`。

## 09A 逐屏读回、信任与 continue 批准（2026-10-14 UTC 05:4x）

主题三键、Security notes（逐字一致）、信任 ArrowDown→Yes→读回→Enter（目录 /private/tmp/t078-2-p1-09-c_gw0g87/repo，仅 value.txt；依 answer 20261014T011751Z）均生效，读回主提示符。写 readiness.json 与 actions-approval.json（Escape 与 queue-release 两个自动化测试动作，仅在 PLAN-09 A3/A4 条件成立时各执行一次，记为执行主控批准的自动化而非真实用户亲手操作）。批准 `p1-continue-09` 一次（两条 nonce、假 API 两条声明请求，真实模型 0；会打开本实例自己的 Electron 窗口）及随后 cleanup。批准引用：`T-078 controller-decision-04 p2-09a-continue`。

## 09A continue 读回与 cleanup（2026-10-14 UTC 05:2x 运行）

continue INCOMPLETE（rc=1，phase continue-esc，"Observed-state deadline; no retry"）。A1 成立：nonce1 由 executor 登记送达，busy、active 绑定 dispatch1，prompt_id1=3b910c4b…；A2 成立：busy 期间登记 nonce2（seq 2）。A3 失败：等待 active 释放超时。electron-driver.jsonl 显示发 Escape 时窗口仍为启动态（"正在连接后台""尚未启动窗格"，state unknown），驱动仍报 sent:true——窗口未接上窗格就发键，判为夹具就绪缺陷，非产品结论；不重试。cleanup-09 PASS，无残留；fixture.tar.gz 8,208,905 字节外置归档、字节读回 PASS（manifest external-archive-578c9fe0…）。交 worker 诊断：Esc 是否到达 PTY（received.ndjson / pty.raw / 门禁事件），驱动须等窗口显示本窗格与 busy 后才发键，并核对键确实写入。

## 09A-2 批准（2026-10-14 UTC 05:5x）

worker 诊断：Esc 未写入 PTY；根因 (1) 驱动在窗口未接上窗格时发键（夹具），(2) renderer 对 nullable 主控窗格永久禁输入（产品缺陷）。修复 7cd19b58（窗口就绪核对、Esc 写出收据、renderer 主控窗格可输入；红/绿与收据反例），材料 e5f46505。批准：`p1-slot-cleanup-09`（删除 09A continue 自建的外置盘 Electron 构建 slot，脚本先核对 cleanup PASS、Electron 退出与归属）；`p1-launch-09a2` 一次及逐屏只读与逐屏按键（同 09A）。批准引用：`T-078 controller-decision-04 p2-09a2-launch`。

## 09A-2 逐屏与 continue 批准（2026-10-14 UTC 06:0x）

p1-slot-cleanup-09 PASS（09A 自建 slot 已删，signals 0）。09A-2 主题三键、Security notes（逐字一致）、信任 ArrowDown→Yes→读回→Enter（/private/tmp/t078-2-p1-09a2-sm_du7jo/repo，仅 value.txt；依 answer 20261014T011751Z）均生效，读回主提示符。写 readiness.json 与 actions-approval.json（Escape/queue-release 仅在 A3/A4 条件成立时各一次，记为执行主控批准的自动化）。批准 `p1-continue-09a2` 一次及随后 cleanup 与 slot-cleanup。批准引用：`T-078 controller-decision-04 p2-09a2-continue`。

## 09A-2 continue 读回（2026-10-14 UTC 05:50 运行）

INCOMPLETE（"Fake API protocol/budget error"）。A1、A2 成立；A3 成立：窗口已接上本窗格（可输入、忙），Esc 经窗口 terminal-key 入门禁（action 30b8e7ac…，seq 86），active 释放、interrupted=true、state busy、nonce2 留在队列，假 API 记录请求 1 被对端关闭。A4：放行已点击；随后请求 2 的用户消息为 "⟦主控 #1⟧ P1_NONCE…⟦主控 #2⟧ P2_NONCE…" 拼接——CLI 在 Esc 后把被中断的提示恢复进输入框（after_esc user_draft=true），放行的 paste 追加其后，假 API 按声明拒收（并见一次同内容重发）。判为产品缺陷：放行未处理 CLI 恢复的非空草稿。cleanup：自建进程均已停止（CLI 退出核对 PASS），按规则保留根 /private/tmp/t078-2-p1-09a2-sm_du7jo；slot-cleanup BLOCKED（前置 cleanup 非 PASS），slot 保留；fixture 外置归档 PASS（manifest external-archive-93611737…）。交 worker 出方案（设计取舍由执行主控定，涉及用户输入语义则交构思主控）。

## 重启后恢复（2026-10-14 本地约 08:2x）

用户电脑重启。核对：Herdr 由用户侧运行（未启动或重启 server）；Herdr 自行把 wF:p3E/p3F 以裸 `codex resume <id>` 恢复，argv 缺模型/强度/service_tier/--no-daemon/沙箱/审批参数，且无 A2A_* 与 git hooks 环境——不符合受管 worker 条件。确认两者 idle、交付均已提交（T-077 未跟踪证据在磁盘）后关闭两窗格，经 scripts/launch-worker --resume 重启：s13-t077s → wF:p3H（launch-ba8ddd4d…），s13-t078s → wF:p3J（launch-07b8db56…），argv 已记录（gpt-6.1-sol xhigh、service_tier="default"、--no-daemon、workspace-write、on-request）。/tmp 已被清空：09A-2 保留根 /private/tmp/t078-2-p1-09a2-sm_du7jo 不复存在（fixture 已于先前外置归档，manifest external-archive-93611737…；根中其余未归档原件随重启丢失，记为证据缺口）。外置盘 slot t078-09-d2d9c666… 仍在。无孤儿测试进程。
收到 answer 20261014T120839Z（用户选 A：用户自行清空并声明"输入框已空，放行"，后台不删字；加提交前拦截：仅对登记派发对不上的提交在 UserPromptSubmit 阻断，不改 Stop）。按此派发 T-078。

## 重启后 worker 恢复受阻（2026-10-14 本地 08:1x）

经 launch-worker 重启后观察到：(1) 受管进程退出后，Herdr 在同一 shell 自动执行裸 `codex resume <id>`（无模型/强度/tier/沙箱参数、无 A2A 与 git hooks 环境）：wF:p3J 08:10:10（T-078，已关闭该窗格）、wF:p3H 08:10:35（T-077，替换了 08:09:13 启动的受管进程 31805）。(2) 第三次经 launcher 启动的 T-078 受管进程（wF:p3K，pid 32966，argv 正确）停在 Codex 提示 "This conversation is open in another app. Close it there and press R to continue here."；本机除这些进程外，用户的 ChatGPT 桌面 Codex（app-server）在运行，疑为"另一个 app"，未核实。执行主控停止重试，不按 r/f/Enter，不操作用户的 Herdr 设置或 ChatGPT 应用；wF:p3H 的裸会话视为非受管，不向其派发。交用户决定。

## 用户决定 B：全新 worker 会话（2026-10-14 本地 08:14）

依据 answer 20261014T121326Z（用户原话："B 开全新会话 (Recommended)"；T-077 冲突测试："重跑 (Recommended)"）。核对 wF:p3H（裸 resume，idle）与 wF:p3K（受管启动停在锁提示）均无在途交付后关闭；等待 20 秒无 Herdr 自动拉起。经 launch-worker 开全新会话：s13-t077n → wF:p3M（launch-e47ca466…），s13-t078n → wF:p3N（launch-4f811bd7…），argv gpt-6.1-sol xhigh、service_tier="default"、--no-daemon、workspace-write、on-request；25 秒后进程仍在。旧原生会话 01a12b31…/01a12b32… 保留不删、不再使用。

## 并发上限更正与文件所有权调整（2026-10-14 UTC 12:4x）

用户原话（经构思主控逐字转述）："最多同时三个 codex 并行，限制的话我们的设计就失去意义了"。存活 Codex 会话上限 3（worker/reviewer/monitor 合计），T-077 与 T-078 可并行。
09A-3 worker（上一会话，已因重启中断）留下 BLOCKED 报告与 blocking issue 20261014T122545Z：提交前阻断需 gates/cli.ts 让 UserPromptSubmit 的阻断决定到达真实 hook 输出/退出码，放行声明需 app/main.ts、app/preload.ts 转发参数；这是我此前把 cli.ts 保留给 T-080 所致。执行主控决定（文件所有权，T-080 尚未开始）：T-078 可改 gates/cli.ts 中仅 UserPromptSubmit signal 输出路径（Stop 不变）、app/main.ts、app/preload.ts；gates/core.ts 仍不改。T-080 开始时基于含此改动的 main 变基。blocking issue 不由执行主控关闭，forward 构思主控备案。开全新 T-078 worker（第 2 个 Codex 会话）。

## exec/t078 变基到含 T-077 的 main（2026-10-14 UTC 13:4x～14:0x）

材料提交 c6b3a127（以 s13-t078m 身份）后，在沙箱外运行 worker 的变基脚本（备份 backup/t078-before-09a3-main-c6b3a127ba23，日志 /private/tmp/t078-rebase-09a3-a5TxSq），逐停由 worker 解决代码冲突（daemon/core/panes/relay/store/cli 等；core.ts、cli.ts 仅为解冲突），执行主控运行 rebase-continue-01～05；controller-decision-04.md 的 add/add 冲突取 main 侧超集。27 个提交全部重放，exec/t078 = ff3708d0（onto main 87e954a2）。待重跑检查、重生 09A-3 材料后审批。

## 变基后回归（2026-10-14 UTC 17:0x～17:3x）

commit-rebased-code-09a3 → 0f754a6d；regression（沙箱外）：runtime、input-failures PASS，worker-inbox 7 项空观测——worker 诊断为夹具仍按 id:<request_id> 查结果，未跟上 T-077 按 launch 登记的键（非产品），先以原失败库取 8 项红态再修夹具；commit-regression-02 → 567d7748（产品 src/app/hooks 不变）。regression-02：worker-inbox 14/14、coop 8/8、recovery 9/9、run 18/18、CAS 1/1 PASS；四个 worker 权限变异体（assign/ready/foreign-ack/revoked）各在目标契约失败、禁止结果实际出现。真实模型 0。批准生成 09a3r 新材料。

## 09A-3R 材料审阅（2026-10-14 UTC 17:4x）

commit-materials-09a3r → 6f0cfdb2（以 s13-t078m 身份）。审阅 P2-APPROVAL-09A3R：continue 要求执行主控在隔离窗口亲手清空草稿并点声明（180 秒）——执行主控无操作本机原生窗口的工具，不批准该设计。按 09A 先例改为测试驱动执行 test-simulated-user 动作（清空键需有依据并以快照证明空框；声明引用 Esc 中断收据与输入代次），执行主控在 actions-approval 逐项预先批准，证据记为自动化而非真实用户。正例/反例重生材料后再审 launch。slot-cleanup 只清单无归档的问题（issue 20261014T173439Z）暂不执行删除，清理阶段再定。

## 09A-3R2 材料与 clean launch 批准（2026-10-14 UTC 18:1x）

commit-code-09a3r2 → 643d59bf（清空草稿与空框声明改为执行主控逐项预批的 test-simulated-user：正例同窗一次 Ctrl+C，依据官方 interactive-mode，须控制收据与空框快照/PTY 证明；反例不清空、自动点故意不真实的声明）；commit-materials-09a3r2 → dc67ce58（两套新实例绑定 643d59bf，静态核对 PASS）。批准 `09a3r2 clean launch` 一次及逐屏只读 screen；引导/信任按键逐屏另批；continue 前另批 readiness 与 actions-approval；block 待 clean cleanup 后另批。slot 删除仍不执行。批准引用：`T-078 controller-decision-04 09a3r2-clean-launch`。

## 09A-3R2 clean 逐屏与 continue 批准（2026-10-14 UTC 18:2x）

主题三键、Security notes、信任 ArrowDown→Yes→读回→Enter（/private/tmp/t078-2-p1-09a3r2-hgqtpjz_/repo，仅 value.txt；依 answer 20261014T011751Z）均生效，读回主提示符。写 readiness.json 与 actions-approval.json（顶层与每步 executor/approval_ref/basis，source test-simulated-user：Escape、clear-restored-draft Control+C 一次、declare-empty-release truth=empty，各一次且有前置条件）。批准 `09a3r2 clean continue` 一次及随后 cleanup（slot 删除不批）。批准引用：`T-078 controller-decision-04 09a3r2-clean-continue`。

## 09A-3R2 clean continue 读回与 cleanup（2026-10-14 UTC 18:1x）

PASS（模型 0）。逐项核对：nonce1 送达、busy、prompt1；nonce2 登记排队；窗口接上本窗格后 Esc 经窗口入门禁并写入，active 释放，API1 被对端关闭；草稿恢复后 test-simulated-user 经同窗发 Control+C（action 521a36d7，0x03），空框观察 empty=true 并留 PTY；声明点击 → user_queue_release（seq 108，声明"用户声明输入框已空"引用该中断）；第二回合 prompt2 不同于 prompt1；假 API 请求 2 的末条 user 文本精确为 "⟦主控 #2⟧\nP2_NONCE_…"（不含 nonce1），请求 1 精确为 nonce1；hook UPS/UPS/Stop 均 exit 0；最终 idle。cleanup PASS，无残留；fixture 8,138,071 字节外置归档（archive_t078_evidence）。slot 未删。批准 `09a3r2 block launch` 及其逐屏、continue、cleanup（同机制另批）。

## 09A-3R2 block 读回与 cleanup（2026-10-14 UTC 18:2x）

逐屏引导与信任同 clean（目录 /private/tmp/t078-2-p1-09a3r2-block-093154n0/repo）。continue PASS（模型 0）：Esc 后保留恢复的草稿，test-simulated-user 点故意不真实的空框声明；真实 UPS2 的 prompt 同时含 nonce1 与 nonce2，hook 原始 stdout 为 {"decision":"block","reason":"登记注入与实际提交正文不一致；已阻断，请处理草稿后再决定。"}，exit 0；假 API 只有请求 1，无 API2、无 api-error。cleanup 及外置归档见下。用户决定 A 与提交前拦截的正例、反例在真实 CLI（假服务）上均成立。待续：09B/09C 停止链路、真登录 Haiku 2–3 回合（逐次批准）、新候选独立审查、合并。

## 09A-3R2 block 收尾（2026-10-14 UTC 18:4x）

原 cleanup BLOCKED（CLI 48987 退出过程中 ps 的 comm 变为括号名 "(2.1.296)"、lstart 不变，旧逻辑立即判 identity_changed，没有继续等待 PID 真正消失）；#153 恢复脚本另因 ps 以中文日期输出、按 5 个 lstart token 切列把解释器路径吃入，在 owns_api 前误判，未发信号。（2026-10-14 更正：此前把两次原因写成同一原因，见 issue 20261014T192750Z。）#155 修复：ps 子进程固定 LC_ALL=C/LANG=C，非 C 格式直接拒绝，比对规则不变。运行 cleanup-block-recovery-09a3r2.py --approval-ref "主控 #155"：PASS——仅对 48954（本实例假 API，命令/根/owner/双读 lstart 一致）发一次 SIGTERM 并确认退出；CLI 48987、壳 48986、后台 48977 已退出；根逐成员归档到 /Volumes/WD-Elements/a2a-evidence/2026-10-11-batch13/T-078/p1-materials-09a3r2-block/cleanup-recovery-154/fixture.tar.gz，字节读回 PASS 后删除根。两个 slot 未动。

## 09A-3R2 收尾提交与 09B/09C 计划裁定（2026-10-14 UTC 19:2x）

commit-closeout-09a3r2-09bc-plan → 50ea0f5f（以 s13-t078m 身份）：收尾读回 23 项、cleanup lifetime/ps C locale 修复与测试、PLAN-09BC-01、issue 20261014T191104Z 与 report。
裁定（执行层，属 T-078"紧急停止"验收内的实现缺口，不改设计）：
1. 先把 exec/t078 变基到当前 main（含 T-080：任务卡必填 oracle_paths、打分 schema 2；含 T-083），按双方意图解冲突，T-078 自建任务卡补 oracle_paths。
2. 文件所有权：T-080 已合入、T-081 不改产品、T-082 排在 T-078 之后——前置切片可改 workbench/src/gates/cli.ts（会话命令加 stop 等）、relay.ts、claudeLaunch.ts、panes.ts、daemon.ts、gates/core.ts（仅限转交/调用者身份所需）、store.ts 与测试。不得只删 controller_relay_not_enabled、不得伪造 attempt 或 operator 代写。
3. 顺序按计划：单个真实 Claude 角色转交/工具切片（红绿与边界反例）→ 冻结 09B 材料交审 → 09B 实跑与收尾 → 冻结 09C 交审。
4. 预算：每场景每角色上限 6 根提交、12 主 Messages（合计 ≤24），供应商模型 0；实测后在 manifest 收紧。09C 总观察 ≤150 秒、真实时钟 >120000 ms，不快进。
issue 20261014T191104Z 非 blocking，以本裁定处置（forward 构思主控备案）。

## 第二次变基与回归（2026-10-14 UTC 19:4x～20:2x）

prepare-and-rebase（以 s13-t078m 身份交接提交 be6e0195）→ 有界变基到 490de67d 无冲突，exec/t078=bf9bb9d7。commit-post-rebase-2 → 3d5225a9（三张自建卡补 oracle_paths，红 3/绿 3）；沙箱外 post-rebase-2-outside-01 停在 cards（15 errors：DaemonCards.setUp 未给 daemon host 提供 A2A_OPERATOR_CREDENTIAL，夹具缺口，产品拒绝缺凭据符合契约）。commit-post-rebase-2b → ee2f7c1b；post-rebase-2-outside-02 PASS：cards 15/15、empty-declaration-entry、input-failures、runtime、worker-inbox。真实模型 0。下一步：单角色真实 Claude inbox 转交切片（先入口红态），launch 逐次批准。

## 单角色切片 1 红态材料与 launch 批准（2026-10-14 UTC 21:0x）

commit-and-prepare-slice1（以 s13-t078m 身份）→ 源 6a59ef92、材料 14e19e2b；实例 /private/tmp/t078-2-p1-slice1-red-z7msieml，launch 70e18a26…；新假服务只给一条预批 Bash（workbench/bin/inbox list --role executor）并收同 ID tool_result，根提交 1、主 Messages 2、Bash 1，供应商模型 0。裁定：relayFiles.ts 的会话请求文件 helper 纳入 T-078 所有权（issue SLICE1-RELAY-FILE-OWNERSHIP）；工具许可 Enter 被记作新 turn_submit_intent 的问题（issue SLICE1-PERMISSION-ENTER）先在真实运行中取证，后续在 panes.ts 修，不改启动许可。批准 slice1-red launch 一次及逐屏只读 screen；按键、readiness、submit-approval、permission-approval 各另批。批准引用：`T-078 controller-decision-04 slice1-red-launch`。

## slice1-red 逐屏与 submit 批准（2026-10-14 UTC 21:2x）

材料缺 screen-key 审批模板（生成器缺口），执行主控按 09a3r2 模板结构、以本实例 approval.json 的 launch/session/目录写入 screen-key-approval-template.json（标注 executor-written）；首两次按键因缺模板在写 PTY 前失败、无键送达，改用新屏 ID。主题 ArrowUp/ArrowDown/Enter、Security notes、信任 ArrowDown→Yes→Enter（/private/tmp/t078-2-p1-slice1-red-z7msieml/repo，仅 value.txt；依 answer 20261014T011751Z）均生效，读回主提示符。写 readiness.json 与 submit-approval.json（根提交 1、主 Messages ≤2、Bash 1：workbench/bin/inbox list --role executor，模型 0）。批准运行 continue_driver（--phase submit）一次；遇工具许可屏停下不按键，permission-approval 另批。批准引用：`T-078 controller-decision-04 slice1-red-submit`。

## slice1-red submit 读回与工具许可批准（2026-10-14 UTC 22:0x）

submit：nonce 送达（dispatch 20422cf6…，seq 1），真实 CLI 发起 Bash，原生许可屏显示的命令与冻结命令完全一致，光标在 "1. Yes"（一次性）；permission_wait 事件 seq 57（tool_name Bash，tool_input.command 一致）。未按键。批准一次 Enter（test-simulated-user，经窗口按键通路，只选一次性 Yes，不选持久允许或 auto 模式）；permission 阶段会在外置盘构建本实例 Electron slot t078-slice1-70e18a26…。批准引用：`T-078 controller-decision-04 slice1-red-permission`。

## slice1-red permission 读回（2026-10-14 UTC 22:0x）

permission 阶段 rc=1：一次 Enter 经窗口送达（key_attempt），真实 Bash 执行 inbox list，tool_result 为 "Exit code 1 {"ok":false,"error":"daemon_call_failed","details":"Error: worker_request_directory_required"}"——即计划预测的最早入口红态，已在 api.jsonl 第 2 次请求中原样记录。但假 API 的 validate_request 要求"下一条 user 消息携带 tool_result"，而 2.1.296 在 tool_result 之后追加 system 消息，假 API 报 "The next user message must carry the tool result." 并写 api-error.json，未返回 ACK，回合未正常 Stop。判为夹具协议缺陷。实例根保留，交 worker 只读读回现场（UPS/Stop/hook/PTY、permission 事件与 intent 记账）、修假 API 校验（按实际消息序列定位 tool_result，不放宽 ID/命令/预算校验），再决定 readback/cleanup 与是否需要新实例重跑。

worker 报警（#175）：api.jsonl 实有 3 次 /v1/messages，第 2、3 次都携带同一 Bash tool_result——假 API 报错后 CLI 自行重发，超出该包主 Messages 预算 2。记为预算超出（客户端重发，非 a2a 注入），本次不计完整通过；只保留"worker_request_directory_required"的入口红态。旧实例不补 ACK、不改现场；等 worker 的归属核对与清理脚本。

## slice1-red 读回、提交与清理（2026-10-14 UTC 23:0x）

读回（SLICE-1-READBACK.md）：客户端入口红态 PASS（真实 Bash tool_result is_error、worker_request_directory_required；requests 与 relay/inbox 业务行均 0）；工具许可 Enter 虚记提交红态 PASS（一个真实 UPS，却有原 intent seq48 与 Enter 产生的 source=user intent seq87）；假 API 校验缺陷经原样请求红→绿修复；主 Messages 3/2 记 NO_GO（HTTP 400 后 CLI 自发补请求，非新根）；无 Stop/idle，不称闭合。commit-slice1-readback → 5b404cb9（以 s13-t078m 身份）。cleanup-slice1-red（#175）：仅对本实例假 API 发一次 SIGTERM 并确认退出，根逐成员外置归档读回 PASS；因协议失败现场（api-error）按规则保留根。下一步：在已分配文件内实现 controller 会话请求文件（relayFiles.ts）、Stop 转交与 caller 身份、Enter 许可不新增 intent，先单元/入口红绿，再生成新实例跑绿态（同机制逐次批准）。

## slice1-green 候选与准备（2026-10-14 UTC 23:5x）

worker 交候选（SLICE-1-GREEN.md）：controller 会话请求文件 producer 与许可 Enter 记账两条红态 red→green，controller relay/caller 22、角色白名单反例 2、worker writer 3、窗口/epochs/pane/inbox 回归通过；产品只改已分配的 8 个文件，controller 请求不补 worker attempt/fence、不经 operator。执行主控以 s13-t078m 身份运行 commit-and-prepare-slice1-green.sh（首提交→入口回归→生成新 slice1-green 实例→材料提交；失败即停）。README stale（issue 20261014T231202Z）：workbench/README.md 当前无其他写入者，分给 T-078，下次提交同步。预算：根提交 2、主 Messages 3、Bash 1、模型 0。
