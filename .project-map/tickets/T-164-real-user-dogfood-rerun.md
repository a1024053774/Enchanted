---
id: T-164
title: T-155 重跑：修复后走到集成，并补 Codex worker 覆盖
type: build
status: open
blocked_by: [T-157, T-158, T-159, T-160, T-161, T-162, T-163]
claimed_by:
supersedes:
ready: yes
ready_by: ideation
ready_rev: 1
---

## What to build

来源：用户 2026-10-23 逐字：“全部 7 条 + 3 条模型行为对策”（选项：切全部修复票）；报告 findings/2026-10-23-real-user-dogfood.md，执行主控 needs-decision 20261023T222913Z。

用户 2026-10-23 逐字：“重跑到集成走通,并补 Codex worker (Recommended)”（选项：修完后再跑一轮）。
沿用 T-155 的场景、边界与交付（Codex gpt-6.1-sol high 用 Computer Use，隔离 Electron，真实 Claude 用 claude-haiku-5-5），本轮目标：走到集成，且 worker 至少一个用 Codex。报告写入 findings/ 新文件，并与上轮逐条对照 F01～F07、M01～M04 是否消失。仍只报告，新缺陷经执行主控建缺陷级票并列出。完成后关闭 T-155 与本票。

通用要求：先在真实 Electron（隔离实例）复现并留红态证据，再修最小根因层；不加自动重试掩盖未知；使用 `CONTEXT.md` 术语；修改界面文案前读 `frontend-less-ai-tone`。

## Acceptance

- [ ] 走到审查通过并集成（经门禁），含 Codex worker。
- [ ] 上轮 7 条发现逐条复验结果。
- [ ] 新发现的 Herdr 对照小结。

## 不做

范围外的问题经问题上报，不顺手改。
