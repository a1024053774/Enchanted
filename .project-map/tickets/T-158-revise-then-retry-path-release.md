---
id: T-158
title: F05：修订任务卡后重试仍被旧 attempt 路径占用挡住
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

来源：用户 2026-10-23 逐字：“全部 7 条 + 3 条模型行为对策”（选项：切全部修复票）；报告 findings/2026-10-23-real-user-dogfood.md，执行主控 needs-decision 20261023T222913Z。

报告 F05（严重）：`card_save` v2 后须找到 `revise`；revise 成功、旧 attempt revoked 后，新 dispatch 仍被自己旧 attempt 的 `path_overlap` 拒绝，还要选择交叠并人工核对旧窗格。
目标：给出完整的修订→旧会话处置→路径释放→重试流程，让角色说明里可发现；旧现场证据仍保留，但“保留证据”与“占用任务路径”要区分。不能简单取消路径检查。

通用要求：先在真实 Electron（隔离实例）复现并留红态证据，再修最小根因层；不加自动重试掩盖未知；使用 `CONTEXT.md` 术语；修改界面文案前读 `frontend-less-ai-tone`。

## Acceptance

- [x] 真实流程：打回→保存 v2→revise→对旧 attempt reclaim→正常 dispatch 一次成功，无需交叠参数（用户 2026-10-24 裁定显式 reclaim）。
- [x] 反例：旧 attempt 仍活跃时路径检查继续拒绝。
- [x] 角色卡/`a2a help` 写明步骤。

## 不做

范围外的问题经问题上报，不顺手改。

2026-10-24 关闭，PASS。用户裁定“显式 reclaim 后释放”。真实入口核对：修前门禁已支持 保存 v2 → revise → reclaim 旧 attempt → 正常 dispatch 一次成功（修前 flow 基线 PASS），缺的是可发现的步骤；红态为 `a2a help` 与角色说明五项可发现性检查失败。修复：`workbench/src/terminalCli.ts` 帮助、`workbench/roles/worker.md`、插件 `SKILL.md`、`workbench/README.md` 写明顺序与命令（候选 `98e61d19a`，合并见 git log）。RUN-OUTSIDE-03：候选与 T-121 通过；release-before-reclaim 落在 unreclaimed_attempt_still_reserves_paths，retain-after-reclaim 落在 one_dispatch_after_reclaim_without_overlap_reason；help-no-reclaim 变异被拒。前两轮失败为夹具问题（reclaim 早于打回消息写完；选择器错误），已保留证据。独立审查 agy PASS。

