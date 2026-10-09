---
id: T-061
title: 原生提示解析放宽到允许数字，a2a 工具缺 tool_name 时也免确认
type: build
status: open
blocked_by: []
claimed_by: s11-t061
supersedes:
ready: yes
ready_by: ideation
ready_rev: 1
---

## What to build

T-055 的范围外发现（收件箱 `20261009T115645Z-worker:t055-issue-001`，证据 `evidence/2026-10-09-batch8/T-055/native-name-finding.md`）：`codexAppServerManager.ts` 从原生提示文本提取工具名时用 `[a-z_]+`，不认数字，`a2a_submit`、`a2a_raise` 在帧缺 `_meta.tool_name` 时解析不出名字，免确认失效。当前真实 Codex 0.162.0 不缺该字段，所以现在不影响；Codex 升级后无人值守的 worker 可能悄悄卡在确认上。让解析认数字，免确认范围仍只由网关工具名目录决定，不扩大。

## Acceptance

- [ ] 红态在先：沿用 T-055 的 13 项探针，缺 `tool_name` 的帧下 `a2a_submit`、`a2a_raise` 仍弹确认，用例失败；保存输出与重放命令。
- [ ] 修复后这两个工具在该帧下按既有条件（受管 worker、有效身份、活跃 turn、已授权自动批准）免确认；非受管会话、非活跃 turn、目录外的名字（含带数字的目录外名字）仍要提示，反例逐条。
- [ ] 目录内其他工具的免确认结果与修复前逐一相同（不扩大范围），列出对照表。
- [ ] 改动限于该解析与其测试，列入上游文件改动清单；既有套件、typecheck、lint 通过。

## 说明

- 授权来源：用户 2026-10-09 对该问题上报选 B，逐字："问题 1：B"（权限解析所在的上游文件，已获用户授权）。不在关键路径上，排在 T-056～T-058 之后或插空；也可整理成通用修复回馈 Synara 上游。

## Resolution

2026-10-09 worker：**BLOCKED**，依据 ready_rev 1；ticket 保持 open，待主控决定与关闭。已保留两个 a2a 工具缺字段时的 4 个预期失败、44 个通过及 116 个目录名字的逐项父修订观测。目录中的 `synara_e2e_review` 也含数字、缺字段时同样 pending；通用修复会改变它，和“其他工具逐一相同”的验收冲突，阻塞上报 `20261009T130400Z-worker:s11-t061-issue-001`。未修改解析器。fork 红态测试快照 `1ec64d866c6a37985ddfada5f22c39f9fcb15e54`，只有 `raise-permission.test.ts`；不是通过候选，不供集成。完整证据、重放命令和未执行检查见 [RESULTS](../../evidence/2026-10-09-batch11/T-061/RESULTS.md)。另有非阻塞 submit 身份问题 `20261009T130123Z-worker:s11-t061-issue-001`；未擅自创建/接管 attempt。
