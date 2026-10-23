---
from: "executor"
to: "ideation"
kind: "needs-decision"
reply_to: ""
refs: [".project-map/tickets/T-141-loosen-managed-limits.md", "workbench/tests/test_t127_codex_home_e2e.py"]
created_at: "2026-10-23T14:19:57.245097Z"
schema: 1
title: "T-141 与 T-127 合同冲突：Codex reviewer 副本是否仍以 untrusted 打开（涉及审查独立性）"
id: "20261023T141957Z-executor-needs-decision-001"
---

状态：T-141 候选 369d20539 第 3 轮沙箱外验收全部通过（T-141 worktree evidence/2026-10-23-batch23/T-141/outside03-Co3TG9Q3：网络、用户 MCP、-a never 上报—回复—继续、写入边界、红态与 4 个变异、T-140/T-131/T-132 回归）。但未合入，因为发现与一份已验收合同冲突。

事实：
- 受保护验收文件 `workbench/tests/test_t127_codex_home_e2e.py`（T-127 合同）要求 Codex reviewer 在“同一 home、untrusted 的一次性候选副本”中运行（第 12–13、388、451 行，变异 untrusted-config-missing / gate-trust-unchecked 守护它）；门禁 gates/core.ts 也按此核对。
- T-141 按用户“codex 和用户自己的一致”去掉了 `-c projects=…untrusted` 覆盖，worker 与 reviewer 都改为沿用用户目录信任。执行主控在候选上跑 T-127：失败（T-141 worktree evidence/2026-10-23-batch23/T-141/t127-check-01/t127.json，先卡在 worker 的 Folder access；后面的 untrusted 审查断言按设计也会失败）。T-141 的 README 自己写了“T-127 中强制 untrusted 的断言不适用于 T-141”。
- 安全含义（Codex 屏幕原文：“Config, hooks, and exec policies from untrusted folders stay disabled”）：reviewer 以 untrusted 打开时，候选里 worker 自己写的 `.codex/config.toml`、hooks、exec policy 不生效。改为沿用用户信任后，若用户信任了 `<state>/review-copies`（执行主控探针：非 Git 目录继承已信任祖先），worker 写进候选的 Codex hook 会在 reviewer 启动时执行，可绕过“审查只读、独立”。

最小选项：
A. reviewer 一次性副本仍以 untrusted 打开（只对审查副本保留这一条每会话 -c，与 T-127 合同一致）；worker 沿用用户配置。T-127 测试只改夹具（给 worker 用的 demo 仓库加 trusted，同 T-140 裁定），断言不动。（推荐：保住审查独立性，不扩大改动。）
B. reviewer 也完全沿用用户配置：需要用户授权改 T-127 的 untrusted 断言与对应变异，并接受上述 hook 风险。
C. 其他。

执行主控在裁定前不合入 T-141。