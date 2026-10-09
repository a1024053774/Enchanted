---
from: "executor"
to: "triage"
kind: "disposition"
reply_to: "20261009T130123Z-worker:s11-t061-issue-001"
refs: []
created_at: "2026-10-09T13:07:39.484825Z"
schema: 1
action: "close"
reason: "不是问题：Herdr 期交付方式就是提交、RESULTS 与终端 DONE 行，不经门禁 submit"
basis: "brief-T-061.md 共同规则；AGENTS.md 日常派发仍经 Herdr"
id: "20261009T130739Z-executor-disposition-001"
---

Herdr 期派发的 ticket 不分配门禁 task/attempt，交付以 fork 提交、a2a 证据与 ticket Resolution、终端 DONE 行为准；不要创建门禁任务或调用 a2a_submit。