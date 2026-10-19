---
from: "executor"
to: "ideation"
kind: "needs-decision"
reply_to: ""
refs: [".project-map/tickets/T-101-slim-history-and-publish-first-release.md"]
created_at: "2026-10-19T08:29:41.779726Z"
schema: 1
title: "T-101 凭据分诊完成：未确认真实密钥泄露；需用户裁定豁免清单与原生会话记录去留"
id: "20261019T082941Z-executor-needs-decision-001"
---

T-101 仍是 NO_GO（发布前停下），分诊已完成，报告在 exec/t101 ab5e65d66 的 evidence/2026-10-19-batch17/T-101/credential-triage-01.md。报告里没有凭据原文。
413 处命中的分类：
- (a) 379 处：测试或夹具里的公开假值，源码里有对应的常量定义。
- (b) 5 处：文档占位符或未展开的变量。
- (c) 29 处：
  - 其中 28 处是普通标识符（task 或 mask 名称）被正则误报，worker 保守地归入 c，逐条注明了原因；
  - 只有 1 处（H005）无法判断。它在 evidence/2026-10-07-synara-batch1/T-035/rollout-*.jsonl 里，是一份 Codex 原生会话记录，命中的是 payload.encrypted_content 这个不透明的加密字段，长 774。它不像 API key，但也无法证明不是。
结论：没有确认任何真实密钥泄露。
另一个相关事实：当前仓库跟踪着 23 份 Codex 原生会话记录（evidence/**/rollout-*.jsonl），本次瘦身计划只会移出其中 5 份。T-101 票里写明扫描范围包括“会话正文”，可见原意就是不发布这类内容。
请用户在以下选项中选一个：
A（推荐）：
- 把 (a) 379 处、(b) 5 处、(c) 中 28 处标识符误报加入扫描豁免清单。清单按对象哈希加 offset 精确定位，不写原文。
- 把全部 23 份 rollout-*.jsonl 原生会话记录从全部历史中移出，归档到外置盘，仓库里留清单。H005 随之消失。
- 然后用新的 run id 重新试跑，确认扫描 0 命中。
B：同样加入豁免，但把 H005 也豁免（当作加密的推理内容），会话记录保留在仓库里。
C：先暂停发布，用户自己逐条核查 H005 等。
选 A 或 B 之后，正式那次仍要等 T-104 和 T-102 合入、所有人静止后再做，大约要 2.5 小时。