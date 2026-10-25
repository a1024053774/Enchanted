---
id: T-179
title: L06：worker 窗格里打印整段门禁回执 JSON
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

来源：findings/2026-10-25-lcu-real-use.md；用户 2026-10-24 逐字：“然后你再用 lcu 测试一下软件看看能不能发现其他问题”。

现象见报告 L06。目标：发给 worker 的门禁回执（submit 结果等）在窗格里是简短可读的中文摘要（状态、候选提交、下一步），完整 JSON 留在记录/门禁库可查；不改门禁语义与回执里 worker 需要机械读取的字段（若 worker 需要，给出简短字段而非整段）。

通用：先在真实 Electron 隔离实例复现并留红态，再修根因；真实 Claude 用 claude-haiku-5-5；不加重试掩盖未知；不用正则判断意图；agy 独立审查。

## Acceptance

- [x] 真实 Electron：worker 交付后窗格只出现几行摘要；完整内容在记录页可查。
- [x] 门禁与 worker 后续动作不受影响（回归）。

## 不做

范围外的问题经问题上报，不顺手改。

## Resolution

2026-10-25，PASS。记录见 [RESULTS.md](../../evidence/2026-10-25-batch25/T-179/RESULTS.md)。发给 worker 的门禁回执改为三四行中文摘要（命令是否受理；任务、状态、候选提交短号；下一步），开头说明完整内容在记录页；主控收到的回执不变。记录页新增“门禁回执”一节，每条有摘要，可展开完整 JSON，与“用户输入记录”分开。真实 Electron 红态 6 项失败，修后两次 PASS 10/10，两个变异被拒，记录页回归 PASS；agy 审查 PASS（一项 P3：多条摘要之间无空行，未改）；合并后复跑 PASS。
