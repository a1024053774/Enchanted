---
id: T-060
title: scripts/inbox：ack 是终结，不再被列为未确认，也不能被确认
type: build
status: open
blocked_by: [T-053]
claimed_by:
supersedes:
ready: yes
ready_by: ideation
ready_rev: 1
---

## What to build

第一次真实使用 `scripts/inbox list` 时发现：收件人收到的 `ack` 条目本身也被列为"未确认"，要再 ack 一次，会形成确认的确认。[spec](../specs/controller-split-user-input-2026-10-09.md) 第 5 节对"未确认"的定义没有把 `ack` 排除，实现照字面做了，缺陷在 spec。本票以此处为准：`ack` 是终结，不再被列为未确认，也不能被确认。spec 是日期记录，不改写。

同时把 T-053 审查留下的两点行为说明写清：front matter 的列表接受哪两种写法；`send`、`ack` 遇到损坏条目就拒绝写入，是有意的，原因写明。

## Acceptance

- [ ] 红态在先：在 T-053 的最终提交上，夹具里收件人收到的 `ack` 出现在 `list` 的未确认清单里，对它再 `ack` 会写出新条目；保存失败输出与重放命令。
- [ ] 修复后：任何角色的 `list` 都不再列出 `kind: ack` 的条目；对 `ack` 条目运行 `ack` 被拒绝（退出码 1，说明 ack 是终结），不写文件。
- [ ] 其他种类（assign、revise、cancel、stop、report、needs-decision、issue、disposition、answer）的未确认判定不变：T-053 原有用例照常通过，预期不改。
- [ ] 已知坏实现被抓住：保留旧行为的 mutant 在新用例上失败，保存记录。
- [ ] `scripts/inbox --help` 或 RESULTS 的"行为说明"写明：front matter 列表接受 JSON 数组与无引号方括号两种写法；`send`、`ack` 遇到任何损坏条目就拒绝写入，及其原因。
- [ ] 在本仓库真实的 `.project-map/inbox/` 上运行 `list`，只读，工作区前后一致。

## 说明

- 开工前须等 T-053 关闭，`scripts/inbox` 同一时间只能有一个写入者。
- 授权来源：用户 2026-10-09 说"A，然后你开"，其中"你开"是让构思主控开这张票；`ready_by: ideation`，`ready_rev: 1`。

## Resolution
