---
id: T-167
title: N01：Codex worker 的门禁回执粘贴后提交未生效，需人工回车才开始
type: build
status: closed
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

- [x] 红态：真实 Codex CLI（隔离 CODEX_HOME）复现回执粘贴后未开始回合、后台却记已提交。
- [x] 绿态：同一序列下回执提交后原生回合开始；未开始时界面如实显示，不显示为已送达处理中。
- [x] 回归：Claude worker 的粘贴提交、T-157/T-165 场景不变。

## 不做

范围外的问题经问题上报，不顺手改。

## Resolution

2026-10-24 关闭，PASS（未用真实 Codex 复验）。写入者为执行主控本人（构思主控 answer 20261024T070244Z-ideation-answer-001 转述用户决定）。根因：额度接近上限时 Codex 0.163 在回合结束后弹出换小模型提示（`rate-limit-switch-prompt`）；a2a 随后写入的回执粘贴与回车答掉了提示（默认换模型），回合没有开始，后台却记 `turn_submitted`。T-164 中 worker B 因此自 06:26:08 起运行在 `gpt-6-luna`。修复：受管 Codex 会话启动参数加 `-c notice.hide_rate_limit_model_nudge=true`（只经启动参数，不写 home）；写入提交键后 20 秒无原生开始信号记 `turn_start_missing`，侧栏与窗格如实显示“回合未开始”，不重发、不替用户按键。README 同步。
证据：真实 Codex CLI `codex-cli 0.163.0` 对本地脚本化 Responses（报告额度已用 94%），厂商模型回合 0。验收第 1 条的“真实 Codex CLI”按此实现：CLI 与其提示是真实的，模型端为脚本。事实探针与端到端红态 2/2 与 T-164 一致；绿态 2/2；提示保留时如实显示 2/2；去掉开始判定的坏实现只败在显示检查；Claude worker 粘贴提交、T-127 回归 PASS。独立审查 agy PASS（三条 P3 观察，无需改动；`readWakeDelivery` 仍以写入为投递，已列未覆盖）。合并 5380ebb28；合并后整批回归 51/51（`evidence/2026-10-23-batch24/merge-wave/README.md`）。真实账号与厂商模型的复验并入 T-164 第二轮（构思主控 answer 20261024T072734Z-ideation-answer-001）。证据 `evidence/2026-10-23-batch24/T-167/RESULTS.md`。
