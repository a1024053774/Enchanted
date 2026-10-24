---
id: T-164
title: T-155 重跑：修复后走到集成，并补 Codex worker 覆盖
type: build
status: open
blocked_by: [T-157, T-158, T-159, T-160, T-161, T-162, T-163]
claimed_by:
supersedes:
ready: yes
ready_by: ideation
ready_rev: 1
---

## What to build

来源：用户 2026-10-23 逐字：“全部 7 条 + 3 条模型行为对策”（选项：切全部修复票）；报告 findings/2026-10-23-real-user-dogfood.md，执行主控 needs-decision 20261023T222913Z。

用户 2026-10-23 逐字：“重跑到集成走通,并补 Codex worker (Recommended)”（选项：修完后再跑一轮）。
沿用 T-155 的场景、边界与交付（Codex gpt-6.1-sol high 用 Computer Use，隔离 Electron，真实 Claude 用 claude-haiku-5-5），本轮目标：走到集成，且 worker 至少一个用 Codex。报告写入 findings/ 新文件，并与上轮逐条对照 F01～F07、M01～M04 是否消失。仍只报告，新缺陷经执行主控建缺陷级票并列出。完成后关闭 T-155 与本票。

通用要求：先在真实 Electron（隔离实例）复现并留红态证据，再修最小根因层；不加自动重试掩盖未知；使用 `CONTEXT.md` 术语；修改界面文案前读 `frontend-less-ai-tone`。

## Acceptance

- [ ] 走到审查通过并集成（经门禁），含 Codex worker。
- [ ] 上轮 7 条发现逐条复验结果。
- [ ] 新发现的 Herdr 对照小结。

## 不做

范围外的问题经问题上报，不顺手改。

## 阶段记录（2026-10-24，票保持 open，INCOMPLETE）

- 用户 2026-10-24 选“B 现在开跑,应用内只用 1 个 Codex worker”（构思主控 answer 20261024T061431Z-001）。执行主控写好隔离生命周期（`evidence/2026-10-23-batch24/T-164/app_lifecycle.py`，应用内 Codex worker 用实例内隔离 CODEX_HOME），外层测试员 b24-t164（Codex gpt-6.1-sol high，Computer Use）。执行主控解释：用户限制的是 worker；产品规定 reviewer 与 worker 同 CLI 同模型，所以唯一 Codex worker 的独立审查也用 Codex，其余 Haiku（#82，已列给构思主控）。
- 外层测试员会话日志显示 Codex 周额度已用 97% 时执行主控叫停（周窗口 2026-10-30 14:15 EDT 重置）。走到：角色申请与批准、混合 CLI 并行派发（A Haiku、B 唯一 Codex、C Haiku）、人工介入、面板答复、任务视图分屏、C 交付与真实独审打回、B Codex 独审打回、手动 Reflect；**没有可合并审查、没有集成**。验收第 1 条未满足。
- 复验（`findings/2026-10-24-real-user-dogfood-rerun.md`）：F02、F03、F04、F06、F07、M03、M04 本轮已走范围内消失；F01、M02 仍在；F05、M01 未能复验（额度停点）。新发现 N01、N02。
- 执行主控事后只读核对实例事件，建缺陷级票：T-166（F01 残余：普通工作回合中输入，UPS 复用 prompt_id 被判重复、原 Stop 被拒）、T-167（N01：Codex 回执粘贴后提交未生效）、T-168（N02：只读审查窗格重叠）。
- 独立审查 agy INCOMPLETE（报告如实、未越界）。合并 4ec08032e。实例按 T-088 归档（`evidence/2026-10-23-batch24/T-164/t164-dogfood-xn9_oslt.archive.json`）；隔离 CODEX_HOME（含 auth.json 副本与应用内 Codex 原生会话）与 operator.json 按规则删除未归档。
