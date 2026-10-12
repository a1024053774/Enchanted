# T-078-2 执行主控决定 04：PLAN-2 批准（P0）

时间：2026-10-11 22:1x；审阅对象：exec/t078 worktree `evidence/2026-10-11-batch13/T-078/PLAN-2.md`。依据：用户选择 C（answer `20261012T015257Z-ideation-answer-001`，原话"C 假服务为主，真登录复核 2～3 回合 (Recommended)"）。

批准 P0：按 PLAN-2 开始实施与无模型的静态/纯逻辑检查。附条件：
- 假服务阶段：每个 CLI 用 /tmp 下隔离 HOME 与 CLAUDE_CONFIG_DIR；环境白名单；假 key 为公开夹具字符串；不继承任何真实凭据；API 只绑 127.0.0.1；不代理外部服务。
- 真登录阶段：只替换构思主控接收者；用户正常 HOME，CLI 可自写本次 `~/.claude` 会话历史；不读、不复制、不枚举认证；`--settings` 只含批准的 hooks，不含权限或认证覆盖；默认 2 回合，第 3 回合另批。
- P1～P4 每次真实启动分别交完整 argv/env/hooks/预算给我批准，未批准不启动；所有 CLI、API、socket、Electron、进程信号步骤经 outside-sandbox.sh 由我运行。
- 不用 `--bare`（会跳过 hooks）；报告分清假服务证明与真模型证明。
- 合流（P5）等 T-076-2 提交后进行。
