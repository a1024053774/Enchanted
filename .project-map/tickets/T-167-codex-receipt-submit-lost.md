---
id: T-167
title: N01：Codex worker 的门禁回执粘贴后提交未生效，需人工回车才开始
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

来源：T-164 新发现 N01（严重），执行主控事后只读核对实例 `/private/tmp/t164-dogfood-xn9_oslt` 的 orchestration_events（launch `5314796c-773d-45e5-b88c-5bf5323d899a`，唯一 Codex worker B）。T-164 要求新缺陷由执行主控建缺陷级票。

现场：B 第一回合结束（seq 258 turn_end、262 pane_idle），门禁回执 #3 排队后 `paste_intent`/`paste_written`/`turn_submit_intent`/`turn_submitted`（seq 264～268，06:26:08），但之后没有 turn_start_signal；终端停在完整回执文本，侧栏未知、窗格忙。3 分钟后测试者手动按一次回车（seq 556～557，06:29:23），回合立刻开始（seq 567）。后续同类回执（#8、#13）粘贴后正常开始。即 Codex 的“粘贴后提交”有一次没被 CLI 当作提交，后台却记成已提交。

目标：查清 Codex 交互终端粘贴与提交键的边界（参照 T-157 夹具里“整块粘贴被当粘贴确认”的现象），让 a2a 写入的提交确实开始原生回合；后台区分“已写入终端”“已提交原生回合”（以原生 turn_start 为准），提交后在合理时限内未开始时如实显示并给出说明，不自动重发、不把 Enter 当默认批准。

## Acceptance

- [ ] 红态：真实 Codex CLI（隔离 CODEX_HOME）复现回执粘贴后未开始回合、后台却记已提交。
- [ ] 绿态：同一序列下回执提交后原生回合开始；未开始时界面如实显示，不显示为已送达处理中。
- [ ] 回归：Claude worker 的粘贴提交、T-157/T-165 场景不变。

## 不做

范围外的问题经问题上报，不顺手改。
