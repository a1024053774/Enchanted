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
