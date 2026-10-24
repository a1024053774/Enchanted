---
id: T-157
title: F01：Stop hook 期间用户输入后交付停住，界面不说明
type: build
status: open
blocked_by: []
claimed_by:
supersedes:
ready: yes
ready_by: ideation
ready_rev: 1
---

## What to build

来源：用户 2026-10-23 逐字：“全部 7 条 + 3 条模型行为对策”（选项：切全部修复票）；报告 findings/2026-10-23-real-user-dogfood.md，执行主控 needs-decision 20261023T222913Z。

报告 F01（阻断）：worker 运行 Stop hook 时用户在窗格输入，之后同一 attempt 的 `submit` 被 `worker_not_active` 拒绝；侧栏“未知”、窗格头仍“忙”，界面没有拒绝原因和恢复入口。
目标：先明确 Stop 与用户输入相交时的交付语义（用户输入记为人工介入，不应无声使交付失效）；界面显示最后确定事实、拒绝原因与下一步；提供绑定原 attempt 的可核对恢复操作。不用自动重试掩盖结果未知；若语义选择涉及验收条件，经 needs-decision 交构思主控。
证据：findings/2026-10-23-real-user-dogfood.md F01 与 evidence/2026-10-23-batch24/T-155/。

通用要求：先在真实 Electron（隔离实例）复现并留红态证据，再修最小根因层；不加自动重试掩盖未知；使用 `CONTEXT.md` 术语；修改界面文案前读 `frontend-less-ai-tone`。

## Acceptance

- [ ] 真实复现：Stop hook 期间输入后，侧栏与窗格头一致显示原因与可操作恢复，不再“未知/忙”并存。
- [ ] 红态：修前同序列得到 `worker_not_active` 且界面无说明。
- [ ] 恢复后交付绑定原 attempt，不产生重复或过期交付。

## 不做

范围外的问题经问题上报，不顺手改。
