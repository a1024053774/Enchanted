---
id: T-115
title: 断连重连后回到前台 Dock 角标偶发未清零：取得失败现场的焦点证据并归因
type: build
status: open
blocked_by: []
claimed_by:
supersedes:
ready: yes
ready_by: executor
ready_rev: 1
---

## What to build

来源：T-112 合并回归和第二轮独立审查（evidence/2026-10-20-batch18/T-112/independent-review-02.md 的“前台角标失败：归因 INCOMPLETE”一节）。缺陷级票，由执行主控在已批准范围内自建（T-004）。

现象：
- T-110 的真实入口 green 场景里，“Foreground after reconnect clears badge”一步失败过一次，最后 badge=1。原件是 T-112 证据目录下的 outside-merge-t110-native-03-executor-rerun.json，source_head 为 22783a1ee，当时负载约 10。
- 同一产品代码在负载约 5 时通过，原件是 outside-merge-t110-native-03.json。
- 第二轮审查在代码里没有找到“侧栏晚返回覆盖前台清零”的路径（main.ts 每次重算都同步读当前焦点）。失败原件没有焦点信息，所以既不能归为测试等待问题，也不能定为产品缺陷。

要做：
1. 用 5f19062f5 已加的焦点与角标时间线观测（hidden、focused、focused_window、badge，以及 focus/blur 事件），在有负载的条件下重复跑 T-110 真实入口，直到取得一次失败现场，或在约定次数内始终不复现；次数与负载条件事先写明。
2. 按现场归因：
   - 失败时窗口一直是 focused=true，badge 却是 1：按产品或原生事件路径修，修前取得红态；
   - 窗口没有取得焦点，或随后失焦：修测试动作的完成条件，不加产品重试，也不只是延长超时。
3. 不放宽 T-110 的任何断言。

## Acceptance

- [ ] 失败现场的完整时间线入证据；或者写明在既定次数和负载下没有复现，作为 INCOMPLETE 如实上报。
- [ ] 若是产品缺陷：修前红态、修后绿态，真实入口 PASS。
- [ ] `project_map.py status` 0 问题。

## 不做

不改 T-110 的提醒语义；不加自动重试；不为了让测试通过而修改等待期限。
