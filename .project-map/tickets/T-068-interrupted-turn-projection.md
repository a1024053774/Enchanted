---
id: T-068
title: 被中断的回合最终存成"已完成"，改成如实记为中断
type: build
status: open
blocked_by: []
claimed_by:
supersedes:
ready: yes
ready_by: ideation
ready_rev: 1
---

## What to build

[T-064](T-064-role-permission-settings.md) 的真实 provider 验证在清理阶段发现（上报 `20261010T084341Z-worker:t064-issue-001`，原始记录 `evidence/2026-10-09-batch11/T-064/terminal-projection-observation-47.json`）：`codex-good44` 的 app-server `turn/completed` 的 payload.status 是 `interrupted`，同一 turn 的最终 SQLite 投影 `projection_turns.state` 却是 `completed`；两个 Claude 场景也有 adapter 发布 interrupted、最终投影 completed 的情况；`codex-bad45` 则正确为 interrupted。尚未归因。

中断被记成完成，会让界面、人工介入和停止的记录误导用户。用户要求修（逐字："1.修"）。

## Acceptance

- [ ] 先归因：在 fork `49cae984f` 上用真实服务（隔离数据目录）复现，记下 terminal 事件的到达顺序与投影写入的先后，指出把 interrupted 覆盖成 completed 的那一步；保存输出与重放命令。不能复现时记 INCOMPLETE 并保存尝试，不凭推测修改。
- [ ] 红态在先：用复现得到的事件顺序写端到端用例，在父修订上投影为 completed，失败。
- [ ] 修复后：原生终态为 interrupted 的回合，最终投影为 interrupted；Codex 与 Claude 各一个正例。原生终态为 completed 的回合仍为 completed（反例）。重放事件日志结果不变。
- [ ] 不加兜底或重试来掩盖顺序问题；修在决定终态的那一层。
- [ ] 既有套件（交付 8、恢复 9、编排 18、membership、T-044 的 35 项）、typecheck、lint 通过。
- [ ] 允许改的上游文件仅限 `apps/server/src/orchestration/Layers/ProviderRuntimeIngestion.ts`、`ProviderCommandReactor.ts` 及归因指向的同目录直接相关文件；超出时先停下说明，由执行主控批准。上游改动列清单；通用修复适合回馈 Synara 作者的，在 RESULTS 注明。

## 说明

- 失败方式清单（处理方式写进 RESULTS）：中断与自然完成几乎同时到达；回收（cleanup）在终态事件之前读回；服务重启后重放；同一 turn 收到两个终态事件。
- 真实模型调用：优先用已有证据的事件顺序做受控重放；确需真实 turn 时，Codex 按 AGENTS.md 的隔离规则，至多 2 个，Claude 不调用（T-059 的认证方式未定）。
- 与 T-059、T-066、T-067 共用 fork checkout，由执行主控串行安排。
- 授权来源：用户 2026-10-10 说"1.修"；`ready_by: ideation`，`ready_rev: 1`。

## Resolution
