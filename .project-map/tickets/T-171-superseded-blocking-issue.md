---
id: T-171
title: N07：修订重派后，旧 attempt 的 blocking 问题仍挂着“等你决定、阻塞”
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

来源：T-164 第四轮 N07；用户 2026-10-24 逐字选择：“建票:标“已随修订失效”，由我一键确认关闭 (Recommended)”。
现状：worker 上报的 blocking 问题在主控修订任务卡并重派后，仍显示“等你决定、阻塞”（角标 2），没有说明根因可能已随新卡消除。
目标：修订（revise）使原 attempt 失效后，该 attempt 名下仍未关闭的问题在问题页显示“可能已随修订失效”，不再计入阻塞角标，并给用户一键确认关闭。不自动关闭、不删除；主控仍不能关 blocking 问题（AGENTS.md 问题上报规则不变）；确认关闭的动作记为用户输入。涉及权限/安全/验收条件的问题不适用“失效”提示，仍按原样等用户。

## Acceptance

- [ ] 真实 Electron：revise 重派后，旧 attempt 的 blocking 问题显示“可能已随修订失效”、角标不再计入、一键确认可关闭；红态（修前仍阻塞角标）入证据。
- [ ] 反例：未被修订影响的 blocking 问题、权限/安全类问题仍阻塞；主控接口仍无法关闭 blocking 问题。
- [ ] agy 独立审查。

## 不做

范围外的问题经问题上报，不顺手改。
