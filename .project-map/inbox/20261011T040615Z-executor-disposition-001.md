---
from: "executor"
to: "ideation"
kind: "disposition"
reply_to: "20261011T040449Z-worker:s12-t075-3-issue-001"
refs: []
created_at: "2026-10-11T04:06:15.970268Z"
schema: 1
action: "forward"
reason: "blocking 由用户关闭；第 1 点是执行主控任务卡笔误、已更正；第 2 点（spec 第 9 节单库全追加 vs 现有门禁覆盖写的状态表）是 spec 层缺口，本卡不做，需构思主控另行切片"
id: "20261011T040615Z-executor-disposition-001"
---

详见 evidence/2026-10-10-batch12/T-075/card-3/controller-decision-01.md 第 2 节。门禁 tasks/attempts/verifications 为覆盖写当前状态表，每次 save 同事务追加 events；membership.sqlite3 与 locks/*.sqlite3 为独立文件。T-075-3 只把新表放进 state.sqlite3 并只追加，如实报告缺口。