---
from: "worker:s11-t056"
to: "executor"
kind: "needs-decision"
reply_to: ""
refs: ["ticket:T-056", "commit:c7aaaa433", "input:20261009T175417Z-worker:s11-t056-issue-001"]
created_at: "2026-10-09T18:03:05.415978Z"
schema: 1
title: "T-056 候选已冻结，请核对显式 submit 的身份与传输"
id: "20261009T180305Z-worker:s11-t056-needs-decision-001"
---

T-056 ready_rev 2 的工程候选正在收尾，覆盖矩阵、来源反例、fail-closed、迁移、真实 Codex 异步问答和既有套件已有证据。worker 角色卡要求显式 submit，但本 brief 未给受管 task/attempt/session/fence 或 submit 传输；当前工具列表没有 a2a_submit，且 brief 禁止读取正式工作台数据目录，不能借用其 endpoint。

请执行主控提供本 worker 当前 attempt 的授权 submit 入口与绑定身份，或明确本票在 Herdr 期应使用哪一种显式候选交接。不会自行 create/claim 一个执行 attempt，也不会读取正式 endpoint。此上报暂不阻塞候选冻结、证据整理与一次独立审查；最终交付会区分候选报告与门禁 submit 收据，不把自然语言完成当作门禁事实。
