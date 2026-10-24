---
id: T-161
title: F02+F07：只读查看报输入错误横幅；窗格头不显示主控角色
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

报告 F02（一般）：点只读审查员/历史 worker 即出现 `a2a:focus-observation: Window is not available for input` 横幅，未输入任何字符。F07（轻微）：窗格头仍写普通终端，角色只在侧栏。
目标：只读窗格不申请可写输入焦点，真正输入失败才报错；窗格头同时显示载体与已确认角色。

通用要求：先在真实 Electron（隔离实例）复现并留红态证据，再修最小根因层；不加自动重试掩盖未知；使用 `CONTEXT.md` 术语；修改界面文案前读 `frontend-less-ai-tone`。

## Acceptance

- [ ] 真实 Electron：点审查员与历史 worker 无错误横幅；真实输入失败仍提示。
- [ ] 批准后的主控窗格头显示角色，收起侧栏仍可辨认。

## 不做

范围外的问题经问题上报，不顺手改。
