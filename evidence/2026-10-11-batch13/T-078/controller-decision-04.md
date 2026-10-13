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
