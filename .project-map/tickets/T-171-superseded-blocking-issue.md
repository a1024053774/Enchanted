---
id: T-171
title: N07：修订重派后，旧 attempt 的 blocking 问题仍挂着“等你决定、阻塞”
type: build
status: closed
blocked_by: []
claimed_by:
supersedes:
ready: yes
ready_by: ideation
ready_rev: 1
---

## What to build

来源：T-164 第四轮 N07；用户 2026-10-24 逐字选择：“建票:标“已随修订失效”，由我一键确认关闭 (Recommended)”。
现状：worker 上报的 blocking 问题在主控修订任务卡并重派后，仍显示“等你决定、阻塞”（角标 2），没有说明根因可能已随新卡消除。
目标：修订（revise）使原 attempt 失效后，该 attempt 名下仍未关闭的问题在问题页显示“可能已随修订失效”，不再计入阻塞角标，并给用户一键确认关闭。不自动关闭、不删除；主控仍不能关 blocking 问题（AGENTS.md 问题上报规则不变）；确认关闭的动作记为用户输入。所有被作废 attempt 名下未关闭的问题都显示失效提示，权限/安全类由用户在确认框里看全文后自行判断（2026-10-24 选 A，不做机械分类）。

## Acceptance

- [x] 真实 Electron：revise 重派后，旧 attempt 的 blocking 问题显示“可能已随修订失效”、角标不再计入、一键确认可关闭；红态（修前仍阻塞角标）入证据。
- [x] 反例：未被修订影响的 blocking 问题仍阻塞；门禁自己生成的问题不显示失效提示；主控接口仍无法关闭 blocking 问题。
- [x] agy 独立审查。

## 不做

范围外的问题经问题上报，不顺手改。

## Resolution

2026-10-24 PASS。`core.ts` `readIssues`：worker 上报（`from` 不是 `system`）、仍未关闭、其 attempt 为 `revoked` 且 `revocation_reason` 为 `spec revised` 的问题读成“可能已随修订失效”，带 `superseded_by_revision`；不再计入“等你决定”（侧栏、页签角标都从这个数来）。`disposeIssue`：用户关闭这种问题时追加一条 `action` 用户输入。`IssuesPage`：卡片上加说明与“确认已失效，关闭”，原文仍在卡片上。主控关闭 blocking 照旧被拒。

真实 Electron 端到端 `workbench/tests/test_t171_superseded_issue_e2e.py`：红态（`--revision 15a444674`）两条问题都“等你决定”、角标 2；绿态 2/2 PASS（角标 1、主控关闭被拒 `blocking_requires_user`、一键关闭记为用户 `action` 输入、a2 的问题不受影响）；两个变异（自动关闭、不看 attempt）都被拒；T-132 问题面板回归 PASS。证据 `evidence/2026-10-23-batch24/T-171/`。

未覆盖：门禁自己生成的问题（`from: system`）在修订后保持原状只有代码路径与 README 说明，本测试没有构造这类问题；普通 `revoke`（非 revise）不显示提示，同样未单独构造。
