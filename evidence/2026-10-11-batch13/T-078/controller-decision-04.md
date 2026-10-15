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

## slice1-green 准备与 launch 批准（2026-10-15 UTC 00:1x）

controller-green-outside-01 失败经诊断为夹具在异步 drain 前断言（SQLite 原件 seq29 执行、seq34 反馈 paste、seq38 CR 均存在），非产品缺陷；修夹具等待（先复现同一 undefined !== '\r'）。commit-and-prepare-slice1-green-2（以 s13-t078m 身份）→ 代码 7e77f8b8、材料 41672c93（README 同步）；outside-02 controller-entry/空框/runtime/input-failures/worker-inbox 全 PASS；新实例 /private/tmp/t078-2-p1-slice1-green-1yhrmwad，launch 284a5916…，静态核对 PASS。批准 slice1-green launch 一次及逐屏只读 screen；按键、readiness、submit、permission 各另批。预算：根 2、主 Messages 3、Bash 1、模型 0。批准引用：`T-078 controller-decision-04 slice1-green-launch`。

## slice1-green 逐屏与 submit 批准（2026-10-15 UTC 00:2x）

主题三键、Security notes、信任 ArrowDown→Yes→Enter（/private/tmp/t078-2-p1-slice1-green-1yhrmwad/repo，仅 value.txt；依 answer 20261014T011751Z）均生效，读回主提示符。写 readiness 与 submit-approval（根 2、主 Messages 3、Bash 1、模型 0）。批准 submit 一次，遇许可屏停。批准引用：`T-078 controller-decision-04 slice1-green-submit`。
slice1-green permission: native Bash dialog shows the frozen command, cursor on one-time Yes; approve one Enter (ref T-078 controller-decision-04 slice1-green-permission).

## slice1-green 读回（2026-10-15 UTC 00:3x）

一次 Enter 许可后：真实 Bash inbox 请求被接收（tool_result {"ok":true,"queued":true,"delivered":false,"request_id":"a76b424c…"}），API2 回 ACK "SLICE1_TOOL_RESULT_RECORDED <nonce>"，真实 Stop 转交后门禁反馈 "⟦门禁 #2⟧ 本回合的异步请求处理结果…" 作为第二根到达 API3——产品侧 controller 请求→Stop 转交→反馈回送已出现。但假 API validate_request 以 "The second root must be the registered gate feedback." 拒收 API3（夹具对反馈文本的期望与实际不符），CLI 随后重发 API4，主 Messages 4/3 超预算，记 NO_GO；未得到最终 ACK/Stop/idle。判为夹具缺陷。实例保留，交 worker 读回并修校验（以登记的 dispatch2 原文为准、不放宽身份/预算校验），再定是否新实例重跑。

## slice1-green 清理与 green-3 批准（2026-10-15 UTC 00:5x）

worker 读回：登记 dispatch2、UPS2 与 API3 文本逐字相同；API3 user.content 为字符串，旧 validator 只取 text block 数组而漏判（夹具缺陷）；scoped Stop 转交与第二根到达已真实发生，但无最终 ACK/第二 Stop/idle，原场景 INCOMPLETE、预算 4/3 NO_GO，不续跑。cleanup-slice1-green-184：PASS（daemon 认证停止、仅 API 一次 SIGTERM、外置归档读回，根保留）。commit-and-prepare-slice1-green-3 → 8e99d62e（validator 用 api.jsonl 原样 red12→green14）、材料 b5b8b165；产品源码自 455696c9 无变化，显式复用 outside-02。批准 green-3 launch 一次及逐屏只读；按键、readiness、submit、permission 各另批；预算不变（根 2、Messages 3、Bash 1、模型 0）。批准引用：`T-078 controller-decision-04 slice1-green-3-launch`。

green-3：主题三键、Security notes、信任 ArrowDown→Yes→Enter（/private/tmp/t078-2-p1-slice1-green-3-jzfi4ju5/repo）均生效，读回主提示符；写 readiness 与 submit-approval，批准 submit 一次（ref T-078 controller-decision-04 slice1-green-3-submit）。
green-3 permission：原生许可屏命令一致、一次性 Yes，permission_wait seq 57；批准一次 Enter（ref T-078 controller-decision-04 slice1-green-3-permission）。

## green-3 读回：单角色切片 PASS（2026-10-15 UTC 01:0x）

permission 阶段 PASS（模型 0）。执行主控逐项核对：假 API 恰 3 次（API2 回 SLICE1_TOOL_RESULT_RECORDED、API3 回 SLICE1_FINAL_ACK），无 api-error；controller 请求 inbox_list（schema 2，绑定 launch/native session/preset ideation/prompt_id）在真实 Stop 时 relay_processed 一次；参数 --role executor 未覆盖凭据——返回的是 IDEATION_ONLY_SENTINEL；门禁反馈作为第二根（prompt_id dc91281d…）到达；turn_submit_intent 2（seq48、100）、turn_end_signal 2、pane_idle 2；许可 Enter 记为 control action（\r，form action），不新增 intent。单角色 controller inbox 转交切片在真实 CLI（假服务）上成立。下一步：清理本实例、冻结证据；然后按计划冻结 09B 材料交审。

## 09B 材料提交与计划裁定 #187（2026-10-15 UTC）

#186 修复后以 s13-t078m 身份（launch-a2ded34c…，CODEX_THREAD_ID 01a13a72…）重跑 commit-closeout-and-09b-materials.sh：exit 0，c6a81742（收尾/cleanup-185/前置探针）+ d63611ea（09b-materials-01 计划包），9 条 A2A 尾注齐；launch NO_GO，真实 CLI/API/模型/目标启动均为 0。
审阅 plan.json：预算 ideation 4 根/6 Messages、executor 6 根/11 Messages、合计 17，供应商模型 0，均在 #163/决定 4 上限（每角色 6/12、合计 24）内；operator 只做脚手架、只读观察与另批 cleanup，不代发角色 send/stop/ack。计划批准为方向，launch 不批准。
裁定（执行层实现缺口，不改设计）：
1. 前置切片：claudeLaunch 按 preset 推导各自 HOME/config/tmp/shell/requests/hooks/debug/user-data，保留共用 broker/state/repo；turn_limit 与 Panes Claude signal 按批准 manifest 支持到 6 根；同步 P1 生成器；删除共享目录路径，不留 fallback，不删根校验。
2. 先保存真实入口红态（现状共享六路径、第三根被 invalid_controller_turn_limit 拒绝），再绿态；反例至少：超出 manifest 的根仍拒绝、两角色路径互不重叠、单角色 slice1 回归不变。
3. 再实现共库双角色假 API／逐阶段驱动与 oracle 执行器：绑定实际登记文本与实际 stop/request ID，不写死 #1/#2；dispatch.seq 按全局号核对。
4. 完成后另冻结可执行 launch 包交审；我批准前不启动任何 CLI/API/目标。
issue 20261014T235850Z-worker:t078-09b-issue-001 非 blocking，以本裁定处置。

## 09B-PRE 提交与继续 #188（2026-10-15 UTC）

审阅产品 diff：claudeLaunch 按 roles/<preset>/ 推导 HOME/config/tmp/shell/requests/hooks/user-data/debug，删除共享根路径、无 fallback，state/repo 根校验保留；turn_limit 与 Panes signal 接受 1～6，7 拒绝。红态 09b-profile-red-02（共享六路径、第三根被拒）在改动前保存。以 s13-t078m 身份运行 commit-09b-pre.sh：exit 0，b9b5fdd3（产品+证据）+ 50efd2f0（source freeze），9 条尾注；launch NO_GO。
#188：按 #187 第 3、4 步继续实现共库双角色假 API／逐阶段驱动／独立 oracle（红→绿→反例），再交可执行 launch 包审阅；批准前不启动。

## 09B-DRIVER 提交前审阅退回 #189（2026-10-15 UTC）

未运行 commit-09b-driver.sh。原因：claudeLaunch.ts 第 36 行把 role_file 改为同时接受 root/role.md 与 roles/<preset>/role.md，是新旧双路径兼容分支，违反 #187"删除共享目录路径，不留 fallback"及项目"不保留兼容分支"。其余（driver/oracle 纯夹具红绿与三个反例）未发现问题。
#189：role_file 只接受 roles/<preset>/role.md；P1 生成器、单角色 slice1 夹具与测试同步迁移；补一个反例（root/role.md 被 controller_launch_config_required 拒绝）；重跑 profile/budget/slice1 relay/permission/entry/empty 回归与 driver 红绿反例（新输出目录，旧目录保留）；更新提交脚本的固定 HEAD/allowlist 后再交。

## 09B-DRIVER 提交与运行入口 #190（2026-10-15 UTC）

#189 返工审阅：claudeLaunch 只接受 roles/<preset>/role.md，旧路径红态（被接受）与绿态（controller_launch_config_required 拒绝）分存；回归与 driver 红绿反例新目录重跑 PASS。以 s13-t078m 身份运行 commit-09b-driver.sh：exit 0，31b45c02（driver/oracle/边界测试）+ 05cac8b4（09b-executable-materials-01），9 条尾注；static-check PASS，真实启动全 0，launch NO_GO（target claim 未取得）。
#190：静态包接受为审阅基线，launch 仍不批准。下一步写分阶段真实入口 runner：阶段 A 建 root、以脱离进程组方式启动 daemon 与假 API、经门禁真实 dispatch/claim 目标并以其回执填 attempt/session/fence/workspace，写 readiness 后停；阶段 B 起每个角色启动、逐屏按键、一次性工具批准沿用 p1 approval 机制。先用 PTY spy 证明批准前不 spawn、伪造/空 claim 被拒（红绿），交提交脚本与阶段 A 待批材料。

## 09B-RUN 交接退回补证 #191（2026-10-15 UTC）

未运行 commit-09b-run.sh。#190 要求的 spy 红绿证据缺失：工作树与 allowlist 中没有任何 runner 拒绝路径的运行证据（只有 runner、fake API、计划与模板）。runner 写法本身与计划一致（无 approval 时建 root 前退出、dispatch 回执填 attempt、allow_role_cli_spawn=false）。
#191：经真实 runner 入口补三项拒绝（无/伪造 approval、approval 的 source_revision 与包不符、dispatch 回执缺字段或空 claim），每项以 spawn/root 创建 spy 证明零进程零 root；各有已知坏变异体（去掉对应检查）取红。新输出目录，加入 allowlist 后再交。

## 09B-RUN 提交、阶段 A 批准与入口缺陷 #192/#193（2026-10-15 UTC）

#191 补证审阅：09b-run-spies-06 PASS 5/5（真实入口对伪造 approval、source 不符 exit 1、spawned=false、无新 root；三个变异体接受取红）。以 s13-t078m 身份运行 commit-09b-run.sh：exit 0，661064d7（runner/spy）+ 88d3c422（09b-executable-materials-02），9 条尾注。
#192：执行主控批准阶段 A（stage-a-approval.json，source_revision 661064d7，allow_role_cli_spawn=false；内存 free+inactive 约 3.8 GB，预计 80–190 MB）。运行结果 09b-stage-a-01/result.json：exit 1，INCOMPLETE，`Executable packet is stale; no spawn`，spawned=false，无 root、无进程。
根因：run-09b.py 第 11 行要求 HEAD == 材料包 revision，但提交脚本按设计在 source 提交后再提交材料包，HEAD 必然前进一格，条件不可满足。属 runner 缺陷，非环境问题。
#193：改为核对“材料包 revision 是 HEAD 的祖先，且 revision..HEAD 只改动该材料包目录与本票证据目录”（任何 workbench/、scripts/ 或 runner 本身改动都拒绝）；补红（当前实现在本状态下拒绝，即 09b-stage-a-01）与绿，及反例（revision..HEAD 改动 workbench/src 被拒）；runner 改动后需重冻材料包，approval 重签。09b-stage-a-01 保留。

## 09B-RUN-03 提交、阶段 A 第二次运行与卡片缺陷 #194/#195（2026-10-15 UTC）

审阅 lineage 修复（祖先 + 只允许本票证据变更，workbench/scripts/runner 变更拒绝）；以 s13-t078m 身份运行 commit-09b-run-03.sh：exit 0，885acdae + 09b58c69（materials-03、revision-spy-03），9 条尾注。
#194：重签 stage-a-approval-03.json（source 885acdae，allow_role_cli_spawn=false）并运行 → 09b-stage-a-03：exit 1，INCOMPLETE，spawned=true。root /private/tmp/t078-2-09b-run-576xn98k；已启动 fake API 62217（ideation）、62218（executor）与 daemon 62220；card_save 被门禁拒：invalid_task_card，paths.deny "oracle/**" Invalid repository path。未 dispatch，无 target 进程，无 Claude CLI，模型 0。三个进程仍存活，未发信号。
根因：runner 生成的卡片在 spawn 之后才交门禁校验；卡片 deny 写法不合门禁路径语法。
#195：（1）cleanup 脚本只针对 09b-stage-a-03 记录的 root 与 PID（daemon 经 daemon_stop，fake API 核对 argv/root/lstart 后各一次 SIGTERM），归档读回后删 root，交我审后运行；（2）修卡片 deny 写法；（3）runner 在任何 spawn 前先用门禁 card_validate（或等价真实入口）校验卡片，补红（当前卡片在 spawn 前即被拒）绿；重冻 materials-04。

## #195 交接审阅：cleanup 退回 #196（2026-10-15 UTC）

未运行 cleanup-09b-stage-a-03.py，也暂不运行 commit-09b-run-04.sh（应先完成 cleanup，再一起冻结）。
缺陷：（1）API 信号循环比较 `current != identity`，identity 是前一循环残留变量（=62218 身份），62217 必然不符 → 在 daemon 已停后 BLOCKED，留下半清理现场；应比较 api_id[pid]。（2）"byte_readback: PASS" 实为只列成员名，未逐成员与原文件比对字节，标签不实。
#196：修这两处；加一个不发信号的 dry-run（只核对身份、打印将执行的动作）供我先运行；修后交我。runner/card 预检修复无意见。

## stage-a-03 cleanup 运行与假 API 死锁 #197/#198（2026-10-15 UTC）

#196 修订审阅：API 比较改为 api_id[pid]；归档逐普通文件字节、目录类型、symlink 目标比对。dry-run（"主控 #196"）PASS，未发信号。正式运行：daemon_stop 成功，62220 已退出；62217 收一次 SIGTERM 后 15 秒未退出 → BLOCKED，root 保留未归档，62218 未发信号。
根因（sample-62217.txt 栈证据）：t078_09b_fake_api.py 第 20–21 行在 SIGTERM 处理函数中于 serve_forever 同一线程调用 server.shutdown()，shutdown 等待 serve_forever 退出 → __psynch_cvwait 永久等待。属假 API 缺陷，62218 同样会卡。
#197：执行主控批准针对这两个本测试创建的假 API 的恢复：核对 argv/root/lstart 与 09b-stage-a-03 记录一致后各一次 SIGKILL（62217 已证死锁；62218 SIGTERM 必然死锁，故直接 SIGKILL），确认退出后按 #196 的逐成员读回归档并删 root。
#198：修假 API 停止路径（处理函数不得在同线程调用 shutdown），补真实进程测试：SIGTERM 后 2 秒内退出，先在当前实现取红（超时）再取绿；runner 引用新假 API 后重冻 materials-04。

## stage-a-03 恢复 PASS；run-04 提交 allowlist 遗漏 #199（2026-10-15 UTC）

#198 恢复脚本 dry-run PASS，正式（"主控 #198"）PASS：62217、62218 各一次 SIGKILL 并退出；归档 /Volumes/WD-Elements/a2a-evidence/2026-10-11-batch13/T-078/09b-stage-a-03-recovery/fixture.tar.gz（25,523 字节，71 成员：42 文件、29 目录），逐成员读回 PASS 后删 root。62217/62218/62220 均不存在。假 API 停止红 07（2s 超时）/绿 08 证据已存在。
commit-09b-run-04.sh exit 1：`Unowned work; no mutation`, workbench/tests/t078_09b_fake_api.py（修复本身不在 allowlist），未提交。#199：补入 allowlist 后再交。

## run-04 提交与阶段 A 第三次运行 #200/#201（2026-10-15 UTC）

#199 后以 s13-t078m 身份重跑 commit-09b-run-04.sh：96e0703e（卡片预检、假 API 停止修复、stage-a-03 恢复证据）+ 2f34ae8e（materials-04），9 条尾注；脚本末尾 `assert not git status` 失败（exit 1），唯一残留为 worker 在提交后更新的 herdr-handoff-receipt-04.json（追加 #199 一行），不影响源码与材料包，由 worker 下次提交。
#200：签 stage-a-approval-04.json（source 96e0703e，allow_role_cli_spawn=false）运行 → 09b-stage-a-04：exit 1，INCOMPLETE。进展：卡片预检通过；真实 dispatch/claim 回执 attempt f1dd4297…、session 6923b6e0…、fence 1、thread a7b98242…、workspace 齐全，state=claimed。失败：pane_process_info 返回 shell_pid 68179、leader null、processes 仅 /bin/zsh -f -i；codex-receiver 未启动（数秒后复查仍无），不是读取时序问题。
存活：fake API 68081/68082、daemon 68084、pane zsh 68179；root /private/tmp/t078-2-09b-run-s6slqnu3。未发信号。
#201：worker 只读诊断（经 CLI 读 pane 屏幕/事件，不向 pane 输入），找出 receiver 未启动的原因；修 runner 与证据（红=09b-stage-a-04）；写 stage-a-04 cleanup（带 dry-run；daemon_stop、假 API 现可 SIGTERM）交我。

## stage-a-04 清理、run-05 提交、阶段 A PASS 与阶段 B 实现 #202/#203（2026-10-15 UTC）

#201 诊断审阅：pane_output 实为 `create sessions: File exists`；runner 预建 target/home/sessions，receiver 自行 mkdir 得 EEXIST 退出；删预建，receiver 空 HOME 真实进程 green-10 PASS。cleanup-09b-stage-a-04.py dry-run PASS，正式 PASS：daemon_stop，68081/68082 各一次 SIGTERM 均退出（假 API 修复在真实现场生效），96 成员（55 文件/41 目录）逐成员读回 PASS 后删 root。commit-09b-run-05.sh exit 0：64c752ec + e301f15b（materials-05），9 尾注，工作树干净。
#202：签 stage-a-approval-05.json（source 64c752ec）运行 → 09b-stage-a-05：exit 0，READY_FOR_APPROVAL。真实 dispatch/claim：attempt 766c797e…、session 3d1411f5…、fence 1、thread c6961479…；target shell 70837、leader 70839 codex-receiver、native 00000000-0078-…0001；fake API 70730/70731，daemon 70733；roles_started=[]，模型 0。现场保留供阶段 B。
#203：实现 runner 阶段 B（复用 stage-a-05 root 的 runtime binding；每角色独立 approval，先 ideation 后 executor；逐屏 theme/notice/trust 按已批准按键规则；一次性工具批准；I/E 阶段逐次停）。先 spy 红绿（无 B approval 不 spawn；approval 与 readiness 不符拒绝；同时只起一个角色），交 commit 脚本与 B1 待批材料。

## 阶段 B 交付退回 #204（2026-10-15 UTC）

未运行 commit-09b-stage-b.sh。审阅 run-09b-stage-b.py（123 行）：main 只读 readiness、校验 approval 后写 READY_FOR_ROLE 并返回，无论是否 --dry-run 都没有启动 Claude CLI、逐屏按键、读屏、权限 Enter 的代码路径——#203 要求的阶段 B 未实现。spies-01 四项只有绿（拒绝/接受），缺去掉对应检查的变异红态。
#204：在 runner 中实现真实阶段 B（复用 run_t078_p1.py 已在 slice1 green-3 真实 CLI 上验证过的启动/逐屏/权限机制，经 claudeLaunch 与门禁入口，不另造）：每次调用只执行一个已批准动作（启动到第一屏、一屏一键序、一次权限 Enter、一个 I/E 阶段），执行后读屏存证并停。补三项变异红态。A-05 现场继续保留。

## 阶段 B 修订审阅与提交失败 #205（2026-10-15 UTC）

#204 修订：非 dry-run 委托 run_t078_p1.py 单一 phase；spies-03 含三项变异红态。commit-09b-stage-b.sh exit 1：`Unowned work; no mutation`, 09b-stage-b-allowlist.json（allowlist 未列自身），未提交；herdr-handoff-receipt-04.json 亦有改动。另：B1 approval 需 p1_materials 绑定 A-05 root，但未见为 A-05 生成的 ideation p1 材料目录（role 目录、role.md、launch 输入、fake API URL）。
#205：提交前用与脚本相同的归属函数对完整 `git status --porcelain` 预检（含 allowlist 自身与 receipt）；生成 A-05 的 ideation p1 材料并起草填好的 B1 approval（approved_by 留空由我签），一并纳入提交。

## stage-B 提交与 B1 首次运行 #206/#207（2026-10-15 UTC）

#205 后以 s13-t078m 身份运行 commit-09b-stage-b.sh：0a63abed + c04bc410，9 尾注；末尾干净断言失败（exit 1），唯一残留又是 worker 交接后更新的 herdr-handoff-receipt-04.json。
#206：核对 stage-b-ideation-approval.json（binding 与 A-05 readiness 一致；5 个现场进程 lstart 未变；内存约 2.9 GB）后签字。dry-run PASS（READY_FOR_ROLE，spawned=false）。真实 B1 → 09b-stage-b1-ideation：runner rc=0 但 status INCOMPLETE；run_t078_p1.py 在第 24 行读 /private/tmp/t078-2-09b-run-94_wksxv/scenario.json 时 FileNotFoundError，p1_exit_code 1。未启动 Claude CLI（pgrep 无），A-05 五个进程完好。
缺陷：（1）A-05 ideation p1 材料未满足 run_t078_p1 的前置文件（scenario.json 等），#205 只写了部分；（2）runner 在 p1 失败时仍 exit 0，且 spawned=true 指的是 p1 子进程而非 CLI，记录易误读；（3）receipt 反复在提交后变更，提交脚本应把 receipt 更新放在提交之前或不在交接后再改。
#207：按 run_t078_p1 实际读取的全部前置文件补齐 A-05 材料（先列清单、逐项对照代码），并以不启动 CLI 的方式验证 p1 能读完前置并停在 spawn 前；runner 对 p1 非零退出返回非零，字段改为 p1_spawned/cli_spawned 分开记录；B1 approval 需新签。

## stage-b-02 提交失败 #208（2026-10-15 UTC）

commit-09b-stage-b-02.sh exit 1，第 14 行：断言旧红态 09b-stage-b1-ideation/result.json 的 `cli_spawned is False`，但该结果由旧 runner 生成，只有 `spawned: true`，无 cli_spawned 字段；断言对已保留证据永远不成立。未提交。旧证据不得改写；CLI 未启动的事实来自本日志 #207 的 pgrep 核对。stage-b-ideation-approval.json 的改动是我在 #206 的签字。
#208：断言改为按旧结果实际字段核对（status INCOMPLETE、p1_exit_code 1、FileNotFoundError scenario.json），并引用 #207 的 pgrep 记录；重跑归属预检后交。

## stage-b-02 提交与 B1 第二次运行 #209/#210（2026-10-15 UTC）

commit-09b-stage-b-02.sh exit 0：48dd6ce5 + 92a61308，9 尾注，工作树干净。#209：签 stage-b-ideation-approval-02.json（source 64c752ec，B1 first-screen），dry-run rc 0；真实 → 09b-stage-b1-ideation-02：rc 1，p1_spawned true，cli_spawned false；p1 结果 `Local API exited before readiness; retain logs, no restart`（run_t078_p1.py 第 102 行）。p1 launch phase 自行启动一个本地 API，而非使用 A-05 已就绪的 09B ideation 假 API（57534/PID 70730）；该 API 退出且 command-output 为空，无日志。pgrep 无 Claude 进程，无新增残留进程，A-05 五进程完好。
#210：p1 launch 在 09B 绑定下必须使用 input.api_url 指向的既有假 API，不得自启第二个 API（只核对其 PID/lstart/ready 文件）；单角色 slice1 路径行为不变（回归）；先在当前实现上取红（即本次）再取绿（不启动 CLI 的 spy：停在 spawn 前且未起 API）。另查明自启 API 为何无日志退出并修日志捕获。B1 再用新 approval。

## #210 交付审阅退回 #211（2026-10-15 UTC）

未运行 commit-09b-stage-b-03.sh。run_t078_p1.py 复用分支核对 `str(api_script) in identity['command']`，api_script（第 26 行）为 t078_fake_messages.py / t078_fake_inbox_tool.py，而 A-05 的 API 运行 t078_09b_fake_api.py → 真实运行必报 reused_api_identity_changed。reuse-spy-01 为纯 approval 预检，未经过 run_t078_p1 复用分支，未能发现。另：09B 假 API 阶段 A 版只提供 /health、业务 Messages 一律 409；B1（到第一屏）或不需 Messages，但 I1 起必须由 09B 驱动按 protocol 应答。
#211：复用分支按 09B 假 API 的实际 argv 核对（脚本路径、--root、--role、ready 文件 PID/lstart）；用真实 run_t078_p1 入口对活的 A-05 API 只读探测、在 controller_start 前停（加显式 stop-before-cli 标志）取红（当前代码）/绿；说明 B1 首屏是否会发 Messages 请求，若会，09B 假 API 在 B1 的应答需先实现并取证；I1 起的 Messages 应答计划列入下一步。

## #212 复用分支红态（2026-10-15 UTC）

签 stage-b-ideation-approval-04.json（p1_args: --reuse-stage-a、--reuse-api-root roles/ideation、--stop-before-cli）并经真实入口运行 → 09b-stage-b1-reuse-red-02：rc 1，p1 exit 1，`RuntimeError('reused_api_identity_changed')`，cli_spawned false；pgrep 无 Claude、无 t078_fake_messages/inbox_tool 新 API；A-05 五进程完好。红态符合预期。待 worker 修身份核对后取绿。

## #213 复用绿态失败与根因 #214（2026-10-15 UTC）

签 stage-b-ideation-approval-05.json 运行 → 09b-stage-b1-reuse-green-03：rc 1，仍 `reused_api_identity_changed`（run_t078_p1.py:107）；无 Claude、无新 API，A-05 五进程 lstart 不变。
根因：复用分支用 probe_process（第 47 行 `ps -o pid=,lstart=,comm=`）取身份，comm 只有可执行名不含参数，argv[1:] 恒为空。我用同一 identity_from_ps 加 `/bin/ps -ww -o pid=,lstart=,command=`（LC_ALL=C）核对 70730，得到完整 argv 与 expected 一致。
#214：复用分支改用完整 argv 探测（-ww command=，C locale），保留 probe_process 原用途不动；绿态前须在 worker 侧先以同一函数对 70730 只读核对一次并存档，approval-06 由我签后跑 reuse-green-04。

## #215 读回脚本失败、复用绿态推进到端点模板 #216（2026-10-15 UTC）

readback-stage-b-api-identity.py 运行即 `ModuleNotFoundError: No module named 'workbench'`（第 4 行 import），未生成输出——worker 未实际运行过即交付。我把读回与绿态同批发出，读回失败未能先拦住绿态；属我的流程疏忽，以后先确认前置 PASS 再签下一步。
签 approval-06 运行 → 09b-stage-b1-reuse-green-04：rc 1；身份核对已通过，p1 随后在 resolved_input 报 `ValueError('dynamic_endpoint_template_required')`——p1 input.api_url 写死 http://127.0.0.1:57534，而 resolved_input 要求动态端点模板，再由 ready 填入。无 Claude、无新 API，A-05 五进程 lstart 不变。
#216：修读回脚本导入路径并实际运行；p1 ideation input 改为模板，由 A-05 ready 文件解析（或在复用分支内提供等价绑定，不放宽 resolved_input 检查）；worker 须先在自身沙箱内对不需外部权限的部分实跑，交付时附实际运行输出。

## #217 读回与复用绿态 05（2026-10-15 UTC）

readback-stage-b-api-identity.py 单独运行：rc 1，INCOMPLETE，argv_match false。两次探测 lstart/command 完全一致，实际 argv 指向 /Users/luckye/Documents/Code/a2a-wt-t078/workbench/tests/t078_09b_fake_api.py；脚本的 argv_expected 却是 /Users/luckye/Documents/Code/workbench/tests/…（SOURCE parents 层数错一级）——脚本自身 oracle 错误，非现场变化。经我人工核对现场身份正确，且绿态入口用 run_t078_p1 的正确常量复核，决定继续。
签 approval-07 → 09b-stage-b1-reuse-green-05：rc 1，`Approved input changed: input.json`（run_t078_p1.py:91 逐字节比对 root 与 materials 的 input.json/nonce.txt/scenario.json）。p1-02 的 input.json api_url 已改为 http://127.0.0.1:0，A-05 root/input.json 仍为 57534，仅此一行差异。无 Claude、无新 API，A-05 五进程 lstart 不变。
#218：修读回脚本 SOURCE 路径；把 A-05 root 的 input.json 同步为 p1-02 版本（只此一文件）；交付前在 worker 侧实跑对三个文件的逐字节比对和读回脚本，附输出。

## #219 复用绿态 06 与 ready 绑定差异 #220（2026-10-15 UTC）

读回脚本忽略 --output、写死 readback-01（已存在，exist_ok=False 拒绝覆盖，旧证据未动）；未重跑，改由我人工 ps -ww 核对 70730 身份 + 绿态入口自身复核。root/input.json 与 p1-02 cmp 一致。
签 approval-08 → 09b-stage-b1-reuse-green-06：rc 1，`ValueError('api_ready_identity_mismatch')`（p1_endpoint.resolved_input 第 8 行要求 ready.launch/session 等于本次 input 的 launch/session）。09B 假 API 在阶段 A 先于任何角色 launch 启动，ready 只有 host/port/pid/role/stage，结构上不可能带 launch/session。无 Claude、无新 API，A-05 不变。
#220（执行层裁定，测试夹具范围）：resolved_input 不改、不放宽。复用分支用独立的 09B 解析函数，绑定强度等价：ready.pid == 完整 argv 探测得到的 PID（两次 lstart 一致）、ready.role == preset、ready.stage == 'A'、ready.host/port 合法、且与 09b-stage-a-05 readiness.api_processes 中该角色的 pid/argv/ready 原值逐项一致；launch/session 由本次 input 提供并记入结果。为该函数先写失败清单（pid 不符、role 不符、readiness 不符、端口非法、stage 不符），逐项红绿；默认 slice1 路径仍走 resolved_input。读回脚本改为尊重 --output。交付前在 worker 侧实跑解析函数单测并附输出。

## #221 复用绿态 PASS（2026-10-15 UTC）

resolver 单测 09b-stage-b1-reuse-resolver-tests-01 PASS（valid 绿；pid/role/stage/端口/readiness 不符各红）。readback-02 PASS：argv_match true，两次 command/lstart 一致。签 approval-09（含 --reuse-readiness-file、--stop-before-cli）→ 09b-stage-b1-reuse-green-07：rc 0，PASS，cli_spawned false；无 Claude、无新 API，A-05 五进程 lstart 不变。红态链：reuse-red-02（旧身份检查）→ green-03/04/05/06 各自失败原因已记录 → green-07 PASS。
#222：worker 写提交脚本（本轮全部证据、resolver、p1_reuse、读回、approval-04..09 签字件），归属预检后交；回答 B1 首屏是否发 Messages（附 Claude Code 2.1.296 在 slice1 green-3 的实际请求时序证据，不推测）；起草真实 B1 approval-10（去 --stop-before-cli，stop_after first-screen）。

## stage-b-05 提交与真实 B1 第三次运行 #223/#224（2026-10-15 UTC）

commit-09b-stage-b-05.sh exit 0：23b6aefa + 54e13274，9 尾注，工作树干净。worker 关于 Messages 的回答：slice1 green-3 中第一次 /v1/messages 发生在 nonce 提交之后；launch 结果没有首屏捕获，B1 首屏时序仍未观察到；若出现 409 即停止条件。
#223：签 approval-10（去 --stop-before-cli，launch 只启进程、不发输入）。dry-run PASS；真实 → 09b-stage-b1-ideation-03：rc 1，`NameError: name 'task' is not defined`（run_t078_p1.py:144，构造 controller_start 参数时）。task 仅在复用分支跳过的 setup 段赋值。controller_start 未执行；无 Claude 会话进程，A-05 五进程 lstart 不变。副作用：root 下新写 runtime-input.json（22:11:39，open('x')，会阻断下次运行）；另有 B1-02 遗留的 api-owner.json/api.stderr/api.stdout（21:36:18）。
#224：复用分支给 task 赋值（取 A-05 binding 的 task_id，与 input.task 核对一致）；runtime-input 等每次运行生成的文件改到按 label 区分的路径，不删除、不覆盖既有遗留文件，遗留文件在结果中列出；补一个不启动 CLI 的测试覆盖复用分支到 controller_start 参数构造为止（变异：删掉 task 赋值时红）。approval-11 留空签字栏。

## #224 期间沙箱升级请求处置（2026-10-15 UTC）

s13-t078m 请求以 local 环境（沙箱外）执行 `rm -f evidence/2026-10-11-batch06-allowlist.tmp; git status …`。按常规不批准沙箱升级：已发 Esc 拒绝。核对目标：0 字节、未跟踪、22:16 由该 worker 创建的临时文件；由我在沙箱外删除。之后通知 worker 继续 #224，临时文件以后写在 scratch/tmp，不写进 worktree。

## stage-b-06 提交失败 #225（2026-10-15 UTC）

commit-09b-stage-b-06.sh exit 1，第一条断言：before='54e13274f6a7bfe8d76c9e5c76e0cc6b508d64e8'，真实 HEAD 54e13274675fc25d9cf558fb40803e2382540941——仅前 8 位一致，余下为手写错误值。未做任何变更。#224 第 2 点已实现（复用分支 runtime-input 写入 out/，run_t078_p1.py:27）。
#225：before 用 `git rev-parse HEAD` 的实际输出填入（不得手写），改后在 worker 侧实跑脚本前段断言（不提交）并附输出。

## stage-b-06 提交第二次失败 #226（2026-10-15 UTC）

commit-09b-stage-b-06.sh exit 1，heredoc 第 13 行：断言 'NameError' in red['p1_stderr']，而 09b-stage-b1-ideation-03/result.json 的 p1_stderr 为空、NameError 在 p1_stdout 的 JSON error 字段。未变更。preamble-01 只覆盖到 HEAD/暂存/归属，未覆盖后续读证据断言。
#226：断言改按实际字段；交付前在 worker 侧把脚本中 `git add` 之前的全部只读断言整段实跑（可抽成 --check-only 模式），附输出。

## stage-b-06 提交与真实 B1 启动 PASS #227/#228（2026-10-15 UTC）

commit-09b-stage-b-06.sh --check-only PASS（23 paths，unowned 0），正式 exit 0：8058def4 + 950dd0e4，9 尾注，工作树干净。
#227：签 approval-11（launch，无 --stop-before-cli，stop_after first-screen），dry-run PASS；真实 → 09b-stage-b1-ideation-04：rc 0，PASS，cli_spawned true。ideation Claude Code 2.1.296：zsh 1227 → claude 1228（session f7689321…，haiku-5-5、effort low、permission manual、tools Bash,Read、空 MCP、debug 写 roles/ideation/claude-debug.log）。未发送任何输入。假 API 尚无请求（roles/ideation/requests 空；debug 日志无 /v1/、409）。A-05 五进程 lstart 不变。
#228：worker 起草 screen 阶段 approval-12（只读读屏，screen-id ideation-s1，不发键），我签后运行；之后按读到的首屏逐屏另批键序。

## B1 读屏第一次 #229/#230（2026-10-15 UTC）

签 approval-12（p1_phase screen，screen-id ideation-s1，不发键），dry-run PASS；真实 → 09b-stage-b1-screen-ideation-01：rc 1，FileNotFoundError 09b-stage-b-ideation-p1-02/launch/process-manifest.json。screen/key/continue 阶段的 same_cli 写死 materials/'launch'/process-manifest.json，而复用模式下 launch 输出在按 label 的 09b-stage-b1-ideation-04/process-manifest.json（cli pid 1228）。未发键；claude 1227/1228 存活。
#230：screen/key/continue 等后续阶段在复用模式下显式接收 --launch-label（或从 approval 指定的 launch 结果目录）读取 process-manifest，不写死、不复制文件；逐个列出后续阶段读取的所有 launch 产物路径并一并改；在 worker 侧用现有 ideation-04 manifest 做不发键的只读校验并附输出；approval-13（签字栏留空）。

## stage-b-07 提交与 B1 首屏读回 #231/#232（2026-10-15 UTC）

commit-09b-stage-b-07.sh --check-only PASS（29 paths），正式 exit 0：b9b37d5f + 408e0815，9 尾注，工作树干净。
#231：签 approval-13（screen，ideation-s1，--launch-label 09b-stage-b1-ideation-04，不发键）→ 09b-stage-b1-screen-ideation-02：rc 0，PASS。首屏为 Claude Code v2.1.296 欢迎 + 主题选择 "Choose the text style that looks best with your terminal"，选项 Auto / Dark mode（光标在 Dark mode，✔）/ Light … ，原字节 09b-stage-b-ideation-p1-02/09b-stage-b1-screen-ideation-02/screen.bin。未发键。
#232：按既定规则此屏需 ArrowUp→Auto、ArrowDown→Dark、Enter，每键绑定实际读回屏幕。worker 提供阶段 B 的单键批准生成器（类同 09A k9.sh：由模板生成 approval，绑定 screen_file、screen_id、key、purpose、selected_label、approval_ref），以及配对的单屏读取包装，供执行主控逐屏使用；不得批量发键；先 --dry-run 自检并附输出。

## stage-b-key.sh dry-run 失败与审阅 #233（2026-10-15 UTC）

运行 stage-b-key.sh ideation ideation-s1 ArrowUp … --dry-run：rc 1，AssertionError matches=[]。未发键；留下空目录 09b-stage-b1-key-ideation-ideation-s1-ArrowUp-dry-run-01。
审阅发现：（1）map(Path, argv) 把 screen-id 变成 Path，与 JSON 中 str 比较恒不等；（2）脚本先 mkdir $OUT 再以同一路径作 runner --output（runner mkdir exist_ok=False）必冲突；（3）--materials 传 p1 目录，阶段 B 一直传 09b-executable-materials-05；（4）screen-key approval 的 directory 用 worktree/repo，应为 A-05 root/repo。
#233：修上述四点；工具交付前必须由 worker 在沙箱内对 dry-run 实跑到 runner 的 READY_FOR_ROLE（dry-run 不需沙箱外权限），附完整输出；空目录保留为失败证据，新输出用 -02。

## B1 ideation 首启完成 #234（2026-10-15 UTC）

worker 的 stage-b-key.sh 未采用：批准写入 /tmp 且 trap 删除（签字件不留证据）、command.json 恒写 dry_run True、--approval-file 传整份阶段批准而 p1 key 阶段要求顶层 launch/session/directory/key 的 screen-key approval（第 171 行，真跑必报 screen_approval_binding_mismatch）。改用执行主控自写助手（已复制到 09b-stage-b1-exec-approvals/executor-key-helper.sh、executor-screen-helper.sh），每次只发一键，两份批准均落证据目录。
逐屏记录（原字节在 09b-stage-b-ideation-p1-02/<id>-…/screen.bin）：
- s1 主题屏，光标 Dark mode → ArrowUp（dry+run）；s2 为按键即时快照（仅 28 字节终端模式序列，未重绘）；s3 读回增量：❯ 重绘于 "Auto (match terminal)"。
- s3 → ArrowDown；s5 读回：❯ 回到 "Dark mode"。
- s5 → Enter；s7：Security notes，去控制序列与空白后 247 字符与 p1-materials-09/security-notice-text.txt 逐字一致 → Enter（onboarding-notice）。
- s9：信任屏，目录 /private/tmp/t078-2-09b-run-94_wksxv/repo，光标默认 "No, exit" → ArrowDown；s11：❯ 在 "Yes, I trust this folder" → Enter（workspace-trust；用户批准见 answer 20261014T011751Z；隔离 HOME）。
- s13：Claude Code 空闲提示符，Haiku 5.5 low effort，manual mode，cwd 夹具 repo。全程 roles/ideation/requests 为空、debug 日志无 /v1/messages 与 409。未用 Digit1，未发默认 Enter。
注：我的简易渲染器不处理光标上移后的覆盖写，选择状态以原始增量字节为准。
#235：worker 下一步——（1）提交本轮证据（含我的两个助手与 exec-approvals 目录）；（2）实现 I1：09B 假 API 按 protocol 应答 ideation 的 Messages（登记正文、request/stop ID 绑定），以及 I1 回合驱动；先离线红绿，再交 I1 待批材料。executor 角色 B1 在 ideation I 阶段完成后另批（同一时间只一个角色启动步骤）。

## I1 离线提交与真实 I1 衔接问题 #236（2026-10-15 UTC）

commit-09b-i1.sh --check-only PASS（177 paths）；正式：ad12136f + 6f8bc4fc 落地（9 尾注），随后 heredoc 第 30 行断言失败（exit 1），RESULTS.md 追加未提交。离线 I1：1 root/1 Messages，SSE 四事件；正文/seq/request_id/role/预算五类变异红。
衔接缺口：A-05 中 ideation 假 API 70730 运行的是阶段 A 代码（Messages 一律 409），ideation Claude（1228）启动时 ANTHROPIC_BASE_URL 固定为 127.0.0.1:57534。09B-I1-PLAN 未说明真实 I1 如何让新应答生效。
#236：worker 提出最小衔接方案并论证（候选：同端口替换 API 进程并更新 A-05 绑定；或新建 A-06 现场用最终假 API 重走 A/B1；或其他），列出每种方案对既有身份绑定、预算与已完成 B1 证据的影响，交我裁定；同时补交 RESULTS 并说明第 30 行断言为何失败。不启动任何东西。

## I1 衔接裁定 #237（2026-10-15 UTC）

审阅 09B-I1-BRIDGE.md。采纳 B：新建 A-06，用最终协议假 API 从阶段 A 起重走 B1；A-05 身份与 B1 历史原样保留为证据。否决 A（同端口替换使复用绑定的 PID/lstart/ready 失效）与 C（代理/热切换为未登记平行路径）。
附加要求：A-06 前假 API 须一次实现全部 09B 阶段（I1–I4、E1–E6）按 protocol 的登记与 SSE 应答，离线逐阶段红绿；避免每阶段重建现场。预算不变（I 4/6、E 6/11）。
顺序：（1）A-05 owner-bound cleanup（含 ideation Claude 1227/1228：先经门禁/controller 停止路径，确认退出；再 daemon_stop、假 API SIGTERM、target；逐成员归档读回后删 root），带 dry-run，交我运行；（2）完整协议假 API 离线红绿；（3）A-06 材料（阶段 A + B1，沿用已验证的复用/label/逐键路径），提交脚本含 RESULTS 补交；交我。

## A-05 cleanup dry-run 失败 #238（2026-10-15 UTC）

cleanup-09b-a05.py --dry-run（"主控 #237"）：rc 1，BLOCKED，未发信号。第 34 行 API argv 比较 args[1:]==expected[1:] 错位（args 含 -B，expected 无 -B 且切掉脚本路径），必然失败。退回修正；失败目录 09b-a05-cleanup-dry-run 保留。

## A-05 清理 PASS #239（2026-10-15 UTC）

dry-run-02 PASS（身份核对全过）。正式（"主控 #237"）PASS：认证 daemon_stop 经 panes.shutdown 关闭 ideation Claude 1227/1228 与 target 70837/70839（无直接信号），确认退出；假 API 70730/70731 各一次 SIGTERM 并退出；归档 /Volumes/WD-Elements/a2a-evidence/2026-10-11-batch13/T-078/09b-a05-cleanup/fixture.tar.gz，921 成员（622 文件、298 目录、1 symlink）逐成员读回 PASS 后删 root。七个进程均不存在。result 中 archive_bytes 为 null（字段未填，外部文件大小已另行 ls 核对）。

## A-06 材料审阅与退回 #240（2026-10-15 UTC）

commit-09b-a06.sh --check-only PASS（17 paths）；正式：a5b37b05 + 5fd62384 落地，随后 RESULTS 提交步骤断言失败（同 I1 那次），RESULTS.md 追加仍未提交。
缺口：t078_09b_protocol_full.py 是离线 oracle（无 HTTP 服务）；run-09b.py:68 阶段 A 仍启动 t078_09b_fake_api.py（Messages 一律 409）。A-06 若按此材料起，会重复 A-05 的衔接问题。
证据卫生：cleanup-09b-a05.py 在 A-05 正式清理运行后才改（补记 archive_bytes），而该脚本此前从未提交，提交进去的是事后版本，实际运行版本无法逐字节复原；09b-a05-cleanup/result.json 未改（archive_bytes null）。外部归档大小 8,062,309 字节由我另行 ls 核对。
#240：（1）让 t078_09b_fake_api.py 这个真实服务进程按完整 protocol 应答（复用离线 oracle 的登记/校验，不另写平行实现），loopback 真 HTTP 测试：先在现版本取 409 红，再取 SSE 绿与反例；run-09b.py/prepare 引用同一文件；重冻 A-06 材料。（2）修 RESULTS 提交步骤并补交。（3）RESULTS 如实写明 cleanup-09b-a05.py 运行后改动的确切 diff 与原因。

## A-06 HTTP 衔接提交与阶段 A 第一次 #241/#242（2026-10-15 UTC）

审阅：t078_09b_protocol_core.py 由离线 oracle 与 t078_09b_fake_api.py --protocol 共用；loopback 真 HTTP 09b-http-protocol-red-green-01：旧模式 409 红、protocol SSE 200 绿、正文/seq/身份/角色/预算 5 类 409 反例；RESULTS 记录 cleanup-09b-a05.py 运行后改动（补 archive_bytes 字段）与原因，09b-a05-cleanup/result.json 未改。p1_reuse 以 readiness 记录的 argv 比对，含 --protocol 不冲突。commit-09b-a06-02.sh --check-only PASS（11 paths），正式 exit 0：90115899 + 34f0b9af，9 尾注，工作树干净。
#241：签 a06-stage-a-approval-01.json（source 90115899，allow_role_cli_spawn false），run-09b.py --materials 09b-a06-materials-02 --protocol → 09b-a06-stage-a-01：rc 1，KeyError('root')（run-09b.py:55 需 static['root'] 的静态夹具 repo/value.txt、oracle/contract-09b.json）。09b-a06-materials-02 非 prepare-09b-executable.py 生成，static-check 无 root。spawned false，无进程；建出的 /private/tmp/t078-2-09b-run-zgikbcl7 只有空目录（0 文件），我以 find -empty -delete 删除。
#242：A-06 材料须由同一 prepare-09b-executable.py 生成（含静态 root 与 --protocol 记录），不另造平行材料格式；runner 对缺 root 应在建 root 前拒绝（补红绿）；重冻后交我。

## A-06 材料门修复与提交失败 #243（2026-10-15 UTC）

worker 请求沙箱外执行（rm -rf /tmp/pycache-t078-a06、py_compile、写 preflight、跑 check-only），不批升级，已 Esc。审阅：run-09b.py 在建 root 前拒绝缺静态 root 的材料（executable_material_static_root_required），material-gate-green-03 PASS（spawned false、roots_created 0）；红态即 09b-a06-stage-a-01（先建 root 后 KeyError）。commit-09b-a06-03.sh --check-only PASS（14 paths）；正式 exit 1：git add 路径列表含不存在的 workbench/tests/run-09b.py（实际在 evidence/…/T-078/run-09b.py），git 128，未提交；materials-03 未生成。check-only 未覆盖 git add 参数存在性。
#244：修 git add 路径；check-only 增加"每个将要 add 的路径存在或属 future 生成物"的断言；交我。

## A-06 材料提交与阶段 A PASS #245（2026-10-15 UTC）

#244 修正后 commit-09b-a06-03.sh --check-only PASS；正式：471c3fae + e5de6ec4（9 尾注），末尾干净断言因脚本在提交后生成 09B-A06-STAGE-A-COMMAND-02.txt 与 a06-stage-a-approval-02.json 而失败（这两项待下次提交）。materials-06 由 prepare-09b-executable.py --protocol 生成：static-check PASS，root /private/tmp/t078-2-09b-executable-5vifu3wd，protocol true，revision 471c3fae。
#245：签 a06-stage-a-approval-02.json，按 COMMAND-02 运行 → 09b-a06-stage-a-02：rc 0，READY_FOR_APPROVAL。root /private/tmp/t078-2-09b-run-bmnmhs0h；protocol 假 API ideation 47931（61558）、executor 47932（61557）；daemon 47935；target shell 48027、leader 48029；无角色 CLI，模型 0。现场保留供 B1。
#246：worker 为 A-06 生成 ideation p1 材料（同 p1-02 结构，绑定 A-06 root/readiness、api_url 模板）与 B1 launch 批准草稿（复用 --reuse-stage-a/--reuse-readiness-file/label），签字栏留空；把 COMMAND-02 与 approval-02 纳入下次提交。

## A-06 B1 ideation 首启完成 #247/#248（2026-10-15 UTC）

commit-09b-a06-b1.sh --check-only PASS（30 paths），正式 e15d1890（9 尾注，工作树干净）。#247：签 stage-b-a06-ideation-approval-01（launch，复用 A-06 readiness），dry-run PASS；真实 → 09b-a06-b1-ideation-01：PASS，ideation Claude zsh 54976 → claude 54977（session d23ca7a4…）。
逐屏（执行主控助手 executor-a06-*.sh，批准落 09b-a06-b1-exec-approvals/）：s1 主题屏 → ArrowUp → s3 ❯ 在 Auto → ArrowDown → s5 ❯ 在 Dark mode → Enter → s7 Security notes 247 字符与参考逐字一致 → Enter → s9 信任屏（/private/tmp/t078-2-09b-run-bmnmhs0h/repo，光标默认 No）→ ArrowDown → s11 ❯ 在 Yes → Enter → s13 空闲提示符（Haiku 5.5 low、manual）。全程 roles/ideation/requests 为空，debug 日志无 /v1/messages 与 409。未用 Digit1、未发默认 Enter。
#248：worker 实现 I1 真实回合驱动（经门禁真实入口登记 dispatch 正文/request/stop/seq，protocol 假 API 按登记应答；ideation 回合经正常输入路径注入，不由 operator 代写；停在 I1 结束），先离线/spy 红绿，交 I1 待批材料（预计 1 root/1 Messages）。

## A-06 I1 驱动提交与现场重建裁定 #249（2026-10-15 UTC）

commit-09b-a06-i1.sh --check-only PASS（212 paths），正式 07a0efdd（工作树干净）。I1：protocol core 归一化真实 /v1/messages，绑定登记正文/seq/角色/attempt/session/fence；fake API 每次请求读取 roles/<role>/protocol-registry.json（动态登记），协议标记 a06-registered-anthropic-v1；I1 驱动 pane_dispatch → 写登记 → pane_release 一次，等 1 响应与 idle 后停。spy：1×200 绿、6×409 反例，0 进程。
问题：A-06 正在运行的 API（47931/47932）是旧代码，驱动按协议标记拒绝 → 真实 I1 需新现场。
#249 裁定：先离线证明 I2–I4、E1–E6 都只靠登记文件、无需再改 API 代码（逐阶段红绿）；若需改 API，现在改完。之后 A-06 owner-bound 清理（含 ideation Claude 54976/54977，经 daemon_stop/panes.shutdown，dry-run 先行），再用 prepare 生成 A-07 材料，阶段 A + B1 重走，I1 起在 A-07 上一路走完。

## A-06 清理与 A-07 提交 #250/#251（2026-10-15 UTC）

审阅 09b-a07-protocol-matrix-01：I2–I4、E1–E6 九阶段各 200 绿 + 一类反例，summary PASS；API 代码仅改协议标记为 a07-registered-anthropic-v1。cleanup-09b-a06.py dry-run（"主控 #250"）PASS；正式 PASS：daemon_stop 经 panes.shutdown 关闭 ideation Claude 54976/54977 与 target，API 47931/47932 各一次 SIGTERM，七进程均退出；归档 /Volumes/WD-Elements/a2a-evidence/2026-10-11-batch13/T-078/09b-a06-cleanup/fixture.tar.gz（8,062,301 字节，918 成员）逐成员读回 PASS 后删 root。
commit-09b-a07.sh --check-only PASS（36 paths）；正式：81ea4754 落地，随后 prepare 失败（exit 1）：脚本传 --label 09b-a07-materials-01，prepare-09b-executable.py:11 要求前缀 09b-executable-materials-；09B-A07-STAGE-A-COMMAND.txt 引用 09b-executable-materials-07。材料未生成，失败记录 09b-a07-commit-01/ 保留。
#251：label 统一为 09b-executable-materials-07；check-only 增加对 prepare 参数前缀与命令文件引用一致的断言；交我。

## A-07 材料、阶段 A、B1 完成 #252/#253（2026-10-15 UTC）

#251 修正后 commit-09b-a07.sh --check-only PASS，正式 75ff6832（materials-07：static PASS，revision 81ea4754，protocol_tag a07-registered-anthropic-v1，静态 root 存在）。
#252：签 a07-stage-a-approval-01.json（source 81ea4754）→ 09b-a07-stage-a-01 READY_FOR_APPROVAL：root /private/tmp/t078-2-09b-run-1o4prsr5；API ideation 5436（54603）、executor 5437（54604），均 --protocol/a07 标记；daemon 5439；target 5535/5537；无角色 CLI。
#253：主控运行 worker 的 prepare-a07-b1-ideation-p1.py（按 COMMAND-AFTER-STAGE-A）生成 09b-a07-b1-ideation-p1-01；主控写 stage-b-a07-ideation-approval-01.json（结构同 A-06 approval-01，binding 逐字取 A-07 readiness.target_binding）。dry-run PASS；真实 B1 → claude 10267（zsh 10265，session 62b9df2f…）。逐屏（executor-a07-*.sh，批准落 09b-a07-b1-exec-approvals/）：主题 ArrowUp/ArrowDown/Enter（各屏增量核对 ❯ 位置）→ Security notes 247 字符逐字一致后 Enter → 信任屏路径核对为 /private/tmp/t078-2-09b-run-1o4prsr5/repo，ArrowDown 至 Yes 后 Enter → s13 空闲提示符（Haiku 5.5 low、manual）。全程 requests 空，debug 无 /v1/messages 与 409。
下一步 I1：worker 按 A-07 绑定重生成 I1 材料与批准草稿。

## A-07 I1 材料提交与首次执行 #254/#255（2026-10-15 UTC）

worker 指出：我写的 stage-b-a07-ideation-approval-01.json 由 A-06 approval 复制而来，残留 api_reuse 字段仍指向 A-06 路径；runner 实际使用 p1_args（A-07 路径正确），未造成错误，签字件未改写。主控疏忽，记录在案。
commit-09b-a07-i1.sh --check-only PASS（229 paths），正式 178ca7e4。审阅 09b-a07-i1-materials-01：绑定取自 A-07 readiness、B1 input/manifest、ideation api-ready；正文 i1-prompt.txt；dispatch id/seq 由 pane_dispatch 返回，request_id/stop_id 实到后读回；预算 1 root/1 Messages；不符 409、不重送。
#254：签 approval.json，执行 I1-COMMAND → 09b-a07-i1-execute-01：rc 1，INCOMPLETE，FileNotFoundError，real_process_starts 0。根因：t078_09b_i1_driver.py:89 写死 p1 = materials/'09b-a06-b1-ideation-p1-01'（A-06 残留），未用 approval.p1_materials。失败发生在 pane_dispatch 之前：无 dispatch、无登记（protocol-registry.json 不存在）、无 release、无请求；A-07 七进程完好。驱动异常记录无文件名与 traceback。
#255：p1 改取 approval.p1_materials（并核对其 input.json 的 launch/session 与 approval 一致）；异常记录补 traceback；spy 增加"p1 路径来自批准"红绿；新输出 execute-02。

## A-07 I1 第二次执行：钩子被 hookTrace 拦截 #256/#257（2026-10-15 UTC）

#255 修正提交 b77ccb29（p1 取自批准并核对 launch/session；异常带 traceback；spy 8 项 PASS）。#256：沿用 #254 签字的 approval.json 执行 → 09b-a07-i1-execute-02：rc 1，i1_response_deadline。实况：pane_dispatch 成功（dispatch 7d714d00…，seq 2），protocol-registry.json 已写，pane_release 已调用；Claude UserPromptSubmit 钩子 exit 2：`invalid_hook_trace_binding`，claude-debug.log 记 "prompt.submit: dropped (UserPromptSubmit operation blocked by hook…)"。API requests/responses 均空，Messages 0。
根因（产品缺陷）：workbench/src/hookTrace.ts:12 要求 A2A_HOOK_TRACE_DIR == <root>/hooks；#187 前置切片 b9b5fdd3 已把角色 hooks 移到 <root>/roles/<preset>/hooks（claudeLaunch 设置），hookTrace 未同步。B1 从未提交提示，故此前未暴露；本次即真实入口红态。
现场：门禁 pane_status 为 busy，active=dispatch #2，nativeTurn null（未收到回合开始信号），Claude 10265/10267 存活。
#257：修 hookTrace 接受角色目录（不留旧 root/hooks 兼容，若单角色路径仍需则说明其实际布局），真实入口红绿；并带证据分析卡住的 active 提交如何处理：产品现有中断/恢复路径能否把它收回（不伪造事件、不由 operator 代写），或须重建 A-08。交我裁定，不启动、不发送。

## hookTrace 修复与 A-08 重建裁定 #258（2026-10-15 UTC）

hookTrace.ts 改为按 A2A_PRESET（ideation|executor）推导 <root>/roles/<preset>/hooks 并核对 A2A_LAUNCH，无旧 root/hooks 兼容。真实 cli.ts signal：red-01 复现 invalid_hook_trace_binding，green-03 通过且错 preset/错 launch 仍拒，既有 hook trace 回归 PASS。提交 ea4c6e05（9 尾注）。
A-07 恢复分析（09b-a07-active-recovery-analysis.md）：active dispatch #2 无 nativeTurn/prompt_id，伪造 Stop 不可；emergencyStop 拒 controller；stopThread 只接受 idle；唯一正规路径为认证窗口用户 Esc→声明/放行。
裁定 #258：不在 A-07 上做 Esc 恢复（属 09C 场景，会污染 I1 证据，且需认证窗口用户动作），重建 A-08。要求：A-07 owner-bound 清理（含 ideation Claude 10265/10267 经 daemon_stop/panes.shutdown；dry-run 先行）；materials-08 由 prepare 生成；B1 p1 生成器与 I1 材料生成器参数化为按 --stage-a 读取，不再写死阶段路径；A-08 阶段 A 命令与批准草稿。

## A-07 清理、A-08 阶段 A/B1 与 I1 第三次执行 #259–#263（2026-10-15 UTC）

#259：cleanup-09b-a07.py dry-run 与正式 PASS（Claude 10265/10267 与 target 经 daemon_stop/panes.shutdown 关闭，API 5436/5437 各一次 SIGTERM；930 成员读回 PASS，8,078,900 字节归档后删 root）。commit-09b-a08.sh：54086f27 + 9c29ec7d 落地，末尾干净断言又因 RESULTS 追加未提交而失败（反复出现的同一问题）。materials-08 static PASS（revision 54086f27，a07 标记，静态 root 存在）。
#260：签 a08-stage-a-approval-01 → 09b-a08-stage-a-01 READY：root /private/tmp/t078-2-09b-run-4_qt67n9，API ideation 23124（51640）/executor 23125（51641），daemon 23134，target 23286/23288。
#261：运行参数化 B1 p1 生成器 → 09b-a08-b1-ideation-p1-01；B1 批准由 worker 新模板填写（不再复制旧批准）。模板缺 runner 必校验的 screen_approvals 与 tool_approval（固定常量），我从 A-07 批准取这两项补齐；首次 dry-run 拒（保留 09b-a08-b1-ideation-dry-run），补后 dry-run-02 PASS。真实 B1 → claude 28969（session b9d90f6e…）；逐屏首启同 A-07（Security notes 247 字符一致；信任路径 /private/tmp/t078-2-09b-run-4_qt67n9/repo），s13 空闲；0 Messages、无 409、无 invalid_hook（hookTrace 修复生效）。
#262：参数化 I1 材料生成器 → 09b-a08-i1-materials-01（session 与 claude 28969 一致）；签 approval.json 执行 → execute-01：rc 1，i1_response_deadline。实况：UPS 钩子正常运行（hookTrace 已修），返回 decision block："登记注入与实际提交正文不一致"。hook trace stdin：实际提交 prompt 无末尾换行；登记 dispatch text 以 "\n" 结尾（a08-i1-prompt.txt 带换行）。API 未收到请求，Messages 0。
#263：产品缺陷——派发正文末尾换行在 Claude 提交时被去掉，逐字比对必然不一致。worker 须：查清 Claude 提交前的实际规范化（以本次 trace 与 slice1 证据为准，不推测）；在产品登记处让规范形式等于实际提交形式（不整体放宽比对）；经真实 signal 入口红（本次）绿与反例（正文中间不同仍拦）；并分析 A-08 当前被拦状态能否按已批准的"清空草稿→确认放行"路径（主控批准的模拟用户自动化）收回，或须重建 A-09。交我裁定，不操作现场。

## 尾换行修复提交与 A-09 重建裁定 #264（2026-10-15 UTC）

worker 再次请求沙箱外执行（rm -rf /tmp/t078-newline-perm && 权限计数回归），不批升级、已 Esc，要求在交接中列命令由主控运行。审阅 09b-a08-newline-analysis.md：A-08 trace UserPromptSubmit.prompt 无末尾换行；store.register 原样保存 prompt 文件尾换行，panes.drain 以 bracketed paste 写入后单独 CR。修复：store.ts 登记时仅去除末尾 CR/LF（canonicalText），内部正文仍逐字比对。真实 signal：red-02（修复前拦截）PASS、green-01（尾换行接受、中间正文变异仍拦）PASS。提交 60a3db95（9 尾注），worktree 干净。
裁定 #264：重建 A-09。理由：store.register 运行于 daemon，A-08 daemon 加载修复前代码，即使经认证窗口用户 Esc→声明放行收回卡住的 active，后续派发仍走旧登记逻辑；且该收回需认证窗口用户动作。要求 worker：A-08 owner-bound 清理（含 Claude 28968/28969）、A-09 materials（prepare，label 09b-executable-materials-09）、阶段 A 命令与批准草稿、B1 批准模板补全 screen_approvals/tool_approval、需沙箱外运行的回归命令清单（全新输出路径，不 rm -rf）、修复提交脚本末尾 RESULTS 未提交的断言问题。

## A-08 清理、A-09 阶段 A/B1、I1 第四次执行 #265–#269（2026-10-15 UTC）

#265：权限计数回归（node test_t078_permission_accounting.ts /tmp/t078-newline-perm-02）PASS 3/3，结果拷入 09b-newline-perm-regression-02/。cleanup-09b-a08.py（"主控 #265"）dry-run 与正式 PASS：七进程退出，935 成员读回 PASS 后删 root。commit-09b-a09.sh：27e754af + 3aeed23c（末尾 RESULTS 断言仍失败，worker 所称修复未生效）。materials-09 static PASS（revision 27e754af）。
#266：签 a09-stage-a-approval-01 → 09b-a09-stage-a-01 READY：root /private/tmp/t078-2-09b-run-jyat2h5s，API 65352（59304）/65353（59305），daemon 65355，target 65451/65453。
#267：B1 p1 生成、模板（已含 screen_approvals/tool_approval）填写 → dry-run PASS → 真实 claude 65991（session 65052abd…）。首启由主控脚本 onboard.py 逐键执行并断言每次重绘（主题 ArrowUp/ArrowDown/Enter、Security notes 247 字符逐字一致、信任路径为本现场 repo、ArrowDown 至 Yes、Enter）；末条 s13 断言因光标定位拆字失败，渲染核对确为空闲提示符（Haiku 5.5 low、manual），0 Messages、无 409、无 invalid_hook。
#268：主控写 a09-i1-prompt.txt（同 A-08 句式，末尾保留换行以在真实现场验证换行修复），生成 09b-a09-i1-materials-01，签字执行 → rc 1：driver:142 断言 dispatch.text == 头 + 原始 prompt（含尾换行），而产品登记已去尾换行（60a3db95）→ 驱动未同步规范化。pane_dispatch 已成功（queued 90958996…），未写登记、未 release；pane_status active null、queued [90958996…]，未进入 PTY。
另：/tmp 清理 01（用户选择，1684 项 4.5 GB，见 evidence/2026-10-15-batch15/tmp-cleanup-01/）。
#269：worker 修驱动按产品规范化比对；并给出处理已排队派发的方案：优先产品现有撤回/取消已排队派发的操作（若有）后重派；否则驱动以门禁 pane_status/记录中的真实 queued 派发（id、seq、原文）写登记并 release，不新派、不伪造。spy 红绿，交我裁定。

## I1 第五次执行：提示通过钩子、假 API NameError #270/#271（2026-10-15 UTC）

#269 方案审阅：产品无撤回已排队派发 API（cli.ts 仅 pane_dispatch/release/status/events）；driver --resume-queued 只读 pane_status 唯一 queued id 与 orchestration_events 同 id 的 dispatch_queued 原文/seq，核对与批准提示规范化后一致再写登记、release 一次，不新派、不伪造。提交 b36c81aa。
#270：沿用 #268 签字 approval，I1-RESUME-COMMAND（--resume-queued，输出 execute-02）→ rc 1，i1_response_deadline。实况（重大进展）：登记写入（dispatch 90958996…，seq 2）；UserPromptSubmit 放行（尾换行修复在真实现场生效）；Claude 向假 API 发出 /v1/messages（source=repl_main_thread），每次得到 409 `{"error":"name 'ROLE' is not defined"}`，Claude 按自身策略重试（≥7/11）。门禁 pane_status busy，active=该 dispatch，nativeTurn null。
根因：workbench/tests/t078_09b_fake_api.py:24 `normalize_anthropic_request(request,registry,ROLE)`，ROLE 在文件中从未定义（--role 未赋值）。07a0efdd 引入；A-07 协议矩阵仅离线，未经真实 HTTP。另：requests.ndjson 只记 body_bytes（16855），未存请求原文，不足作证据。
#271 裁定：修 ROLE（取自 --role），假 API 保存每个请求原文与响应原文；补真实 loopback HTTP 测试，请求体用真实 Claude Code 2.1.296 请求原件（从既有证据取，给出处）——绿：已登记派发 200 SSE；红：当前代码 409 NameError；反例照旧。两个 API 进程都加载了缺陷代码，原端口替换会破坏 readiness 身份绑定（#237 已否决），故 A-09 清理后重建 A-10；A-09 Claude 的重试只打假 API，无外部副作用，任其结束后随清理关闭。

## A-10 准备审阅：HTTP 测试未运行即交付 #272（2026-10-15 UTC）

worker 交：fake API ROLE=a.role；http-exchanges/NNNN.request.bin/response.bin 原文留存；支持 Claude 2.1.296 text-block 请求；A-09 红态原件 09b-a10-http-red-observed-01（11×409 NameError）；请求原件出处 slice1-green-3-readback/api.jsonl。但无 HTTP 绿态证据。主控沙箱外运行 test_t078_09b_fake_api_http_claude.py --output 09b-a10-http-green-01 → 未到 HTTP 即失败：prompt_block 报 `captured dispatch prompt missing`（fixture 解析），说明交付前未运行。失败目录保留。
#272：先在沙箱内跑通 fixture 解析等不依赖端口的部分；红态经真实 HTTP 对旧 API（git show b36c81aa 版本导出到 /tmp）得 409 NameError；绿态对修复版得 200+完整 SSE；反例照旧。交付时附实际运行输出；需绑定端口的部分写明命令由我跑（新输出目录）。

## A-10 重建与 I1 PASS #272–#276（2026-10-15 UTC）

HTTP 修复证据：09b-a10-http-red-02（b36c81aa 旧 API 经 git show 导出，真实 Claude 2.1.296 请求原件 → 409 NameError，五类反例 409）PASS；09b-a10-http-green-02（修复版 → 200 + 完整 SSE，反例 409）PASS。请求原件出处 slice1-green-3-readback/api.jsonl。
#273：cleanup-09b-a09.py（参数化，填 A-09 真实 PID；p1 manifest 用实际 label 目录 09b-a09-b1-ideation-01）dry-run 与正式 PASS：七进程退出，939 成员读回 PASS 后删 root。（首次以 $ARGS 传参因 zsh 不分词而 usage 退出，未执行任何动作。）
commit-09b-a10.sh：db532b6e + f1362104，工作树干净（RESULTS 断言问题已修）。materials-10 static PASS（revision db532b6e）。
#274：A-10 阶段 A READY：root /private/tmp/t078-2-09b-run-t1q79hur，API 23489（64556）/23490（64557），daemon 23492，target 23602/23605。
#275：B1：p1 生成；批准由 A-09 完整模板填写（binding 取 readiness）；dry-run PASS；claude 23894。onboard.py 逐键断言 ONBOARD PASS；0 Messages、无 409、无 invalid_hook。
#276：a10-i1-prompt.txt（末尾带换行）→ 09b-a10-i1-materials-01 → 签字执行（正常模式）：rc 0，**I1 PASS**。driver：dispatch 06a7f3cf…（seq 2）release 一次；API 响应 request_id 96a37691…、6 个 SSE 事件；Stop prompt_id 421d14de… 作为 stop_id；last_assistant_message "I1_ACK"；messages_sent 1、roots_used 1。主控独立读回：http-exchanges 仅 0001（1 次交换）；requests.ndjson 1 行；protocol-registry 已绑定 request_id 与 stop_id；pane_status idle、active null、queued []；claude-debug.log 中 409/API error 0。
意义：真实 Claude Code 首次经门禁登记 → UPS 钩子 → 协议假 API → Stop 完整走完一个受控回合，预算恰好 1/1。
下一步 #277：worker 提交本轮证据；把 I1 驱动推广为按阶段参数（I2–I4、E1–E6）的驱动，登记内容按 09B protocol/plan；executor 角色的 B1 启动与首启沿用同一套（同一时间只一个角色启动步骤）；先离线/spy 红绿，交 I2 待批材料。

## 更正：#276 的"I1 PASS"只是管道追踪回合；I2 材料偏离 protocol #278（2026-10-15 UTC）

worker 交 I2（da91e780 已提交）：驱动按阶段参数化，I2 材料内容为"acknowledge this registered phase turn exactly once, do not call tools, and stop"。对照冻结的 09b-materials-01/protocol.json：I1 = 批准的 test-simulated-user 窗口 stop 请求 → 假 API 下发工具调用 I_SEND_STOP（node workbench/bin/inbox send --kind stop …，故意 --from executor，期望实际 from=ideation）、2 Messages、Stop 时真实 send 并唤醒 executor；I2 = 真实 send 执行反馈、只确认；E1–E6、I3–I4 为 wrong-target 拒绝、真实一次 Esc、ack、重复 ack 幂等、越权 ack 拒绝、已 ack stop 拒绝等，按实际 dispatch/request/inbox ID 关联。
更正：#276 跑通的是"无工具确认回合"，验证了登记→UPS 钩子→协议假 API→Stop 的管道，但**不是 protocol 定义的 I1**；此前日志与对构思主控的汇报中"I1 PASS"一语过度，改称"管道追踪回合 PASS"。I2 材料（再一次确认回合）偏离 protocol，不签、不执行。
#278：按 protocol 实现真实阶段：假 API 按登记下发 Anthropic tool_use（Bash，argv 取自 protocol.commands，占位由实际 ID 填充），Claude 以 manual 权限模式触发 PermissionRequest，由主控按一次性 Yes 规则逐次批准（沿用屏幕/按键批准机制），工具执行结果作为 tool_result 回到假 API 结算第二条 Messages；I1 的输入是批准的 test-simulated-user 窗口 stop 请求（记为自动化，不记为用户）；独立 oracle 按 inbox/relay/目标 received.bin 读回判定。先离线红绿，再交 I1（protocol 版）待批材料。现场 A-10 保留（已消耗 1 root/1 Messages 于管道回合，需计入 ideation 预算 4/6 或说明是否重建）。
