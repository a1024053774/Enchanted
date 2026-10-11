---
from: "executor"
to: "ideation"
kind: "needs-decision"
reply_to: ""
refs: ["ticket:T-078"]
created_at: "2026-10-11T10:19:58.118132Z"
schema: 1
title: "T-078 主控窗格的真实 Claude 回合：认证方式与额度（提前问，T-078 排在 T-076、T-077 之后）"
id: "20261011T101958Z-executor-needs-decision-001"
---

T-078 的验收要求：如需真实 Claude 回合，先在 needs-decision 里报认证方式与额度，由用户决定。T-074 的例外只覆盖 T-074。

T-078 要验证这几项：两个 Claude Code 主控窗格（启动参数只经 --session-id、--model、--effort、--settings 传入）；用户输入记录；空闲时注入唤醒、回合中排队、Esc 后由用户放行；紧急停止。这些都是终端和 hook 层的行为。

请用户选：
A（推荐）不用真实模型回合。启动真实的 Claude Code CLI，用每会话参数（环境变量 ANTHROPIC_BASE_URL 指向本地伪造的 Messages API）让它和本地假服务通信。T-064 决定 02 用过这个做法。hooks、Stop、PermissionRequest、窗格注入和忙闲判断都是真实 CLI 的行为，不需要登录，也不花额度。局限是模型输出是脚本给的，不能证明真实模型的行为。CLI 自己会写本次会话的历史；如果它要求写 ~/.claude.json 才能启动，我们改用 /tmp 下的隔离 HOME，不碰用户目录。
B 用用户平常的 Claude 登录，同 T-074 的例外：Haiku 5.5，最多 N 个回合，执行主控建议 N 不超过 15。CLI 自己写 ~/.claude 下的会话历史可以接受，不读、不复制凭据。
C 两者结合：A 做主体，B 只用 2～3 个回合复核一次真实唤醒。

执行主控的顺序是 T-076 → T-077 → T-078 串行，因为三张票都会改 workbench/src/gates/ 和 daemon.ts。另外并行做一张自建缺陷票 T-079（launcher 偶发 agent_pane_busy，只改 scripts/launch-worker）。T-078 开工前需要这个答复。