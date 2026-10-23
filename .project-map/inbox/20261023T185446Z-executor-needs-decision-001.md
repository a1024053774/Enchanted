---
from: "executor"
to: "ideation"
kind: "needs-decision"
reply_to: ""
refs: ["workbench/tests/HISTORICAL.md"]
created_at: "2026-10-23T18:54:46.906112Z"
schema: 1
title: "10 个过时历史测试仍守护现行契约：迁移还是接受缺口"
id: "20261023T185446Z-executor-needs-decision-001"
---

T-149 按裁定 C 逐文件判断后，下列 10 个过时历史测试仍是现行契约某些检查的唯一守护者，按授权不删、不静默标历史，交用户决定。它们都不在日常回归里，当前 main 上跑会因旧断言失败。

1. test_t112_execution.mjs：角色设置持久化、覆盖优先级、权限字段拒绝、未知 effort 透传、原生启动失败留据。
2. test_quality_tracer_e2e.py：评分必填且只写一次、修复后重跑全串、第三次拒绝暂停、拒绝复用原生审查会话（还是多个测试的基类）。
3. test_t082_review_boundary_e2e.py：共享 refs 变化作废审查、review_requirements.workspace 绑定、结束核对完成前拒绝集成。
4. run_pane_lifecycle.py：应用关闭期间 PTY 继续增长、重开逐字节回放、后台重启后原 attempt 中断。
5. run_worker_delivery.py：原生 Stop 批次只处理一次、门禁回执只注入一次。
6. test_t122_claude_worker_e2e.py：Claude worker 的 Git 元数据/钩子攻击矩阵、审查 CLI/模型绑定。
7. run_t112_native.py：设置界面保存→下次派发 argv→原生首轮请求的全链路。
8. test_t091_pane_ipc.mjs：跨窗口/iframe/未知窗口拒收、关闭竞争中的迟到凭据撤销。
9. test_t078_claude_signals.ts：有活动提交时重复 Stop 只产生一次空闲。
10. test_t108_questions.mjs：Claude 主控原生问答关联、伪造/过期 hook、重复答复拒收。

选项：
A 迁移：把这 10 个的过时断言改到现行契约，保留有效检查（改验收断言，需授权；可拆成几张票）。
B 接受缺口：整份标历史，承认这些检查当前无人守护。
C 部分迁移：只迁移你指定的几个，其余标历史。
执行主控建议 A 或 C（先迁 8、9、3、5 这几个守护安全/门禁边界的）。