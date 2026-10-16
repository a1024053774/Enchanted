---
id: T-090
title: 审查结束核对误要求 worker HEAD 等于冻结候选，回归原交付验收（T-082 带入 main）
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

缺陷级（执行主控在 T-004 自主边界内自建）。T-082 合入 main（`a75070236`）后，原交付验收 `acceptance/test_coop_e2e.py` 的 `test_submit_requires_clean_head_and_cannot_replace_frozen_candidate` 失败：门禁在审查回收时以 `review_worker_workspace_changed` 拒绝，任务暂停，`review_reclaimed` 不出现。

根因：`workbench/src/gates/core.ts`（T-082 新增，约 `:2353`）在审查结束时要求 **worker HEAD == review.candidate_commit**。但该验收场景是"候选 C 冻结后 worker 又提交了 later_bad，不能拿它替换已冻结的 C，verify 仍验证 C"——worker HEAD 在审查开始前就已不等于 C，审查期间没有变化。

T-082 票的原文是："审查结束后门禁核对：候选提交号不变、审查目录与 worker worktree 干净、共享仓库引用未变"。没有要求 worker HEAD 等于候选，所以这是实现比要求收得更紧的缺陷，不是设计取舍。

修法（最小）：审查开始时绑定 worker 当时的实际 HEAD、分支与干净状态；结束时核对这些未变，并继续核对候选提交号不变、审查目录干净、共享 refs 未变。T-082 其余保证（副本、启动参数、结束核对后才可集成、`review_reclaimed` 前置）不变。

## Acceptance

- [x] 原验收用例在修复后的 main 上通过；`acceptance/` 文件不改（T-080 受保护）。
- [x] 红态：修复前同一用例在 main 上失败（`review_worker_workspace_changed`），证据可复现。
- [x] 反例：审查期间 worker HEAD 被改、worker worktree 变脏、分支被改、共享 refs 被改、审查目录被写，仍各自被拒绝并作废审查（至少覆盖 HEAD 改动与变脏两条真实入口反例）。
- [x] 整组回归在修复版本上通过：原交付 8、恢复 9、编排 18，以及 T-082 的启动边界、结束核对与四个启动变异。
- [x] 独立审查（fresh 只读会话）PASS。
- [x] `project_map.py status` 0 problems，没有 stale living doc。

## 不做

- 不改 `acceptance/`、冻结 protocol、T-082 的副本与启动参数检查。
- 不在测试驱动里把 worker reset 到 C、跳过回收或伪造 `review_reclaimed`。

## 说明

- 来源：T-078 独立终审后的整组回归（`exec/t078` worktree `evidence/2026-10-11-batch13/T-078/review-followup-regressions-01/`、诊断 `F4-REVIEW-BOUNDARY-DIAGNOSIS-01.md`、两版本对照 `review-followup-f4-compare-01/`：合并前 `150ef6516` PASS，main `0e6c2b833` INCOMPLETE）。
- 执行主控验收 T-082 时没有整组重跑原交付 8/9/18，漏掉了这个回归；修复后 T-078 再合入 main 重跑。

## Resolution

2026-10-16，执行主控验收 PASS，合入 main `89a1915f1`（产品改动 `0bcc5ab66`，只在 `workbench/src/gates/core.ts`）。审查开始时把 worker 实际 HEAD、分支与 status 存入 `review_requested` 事件的 `worker_boundary`，结束时按 `review_id` 取回核对未变；不再要求 worker HEAD 等于冻结候选。T-082 其余保证不变，`acceptance/` 未改。

- 红态 red-01：原用例以 `review_worker_workspace_changed` 失败；修复后 focused 用例通过。
- 回归：在修复版本上 coop 8、recovery 9、run 18 分别在不同运行中完整通过；剩余步骤 green-remaining-01 PASS（CAS 1、cards 15、worker 三反例、T-082 七场景与四启动变异，三条"删掉 worker 检查"的反事实按预期失败）。**整组从未在同一次运行里全部通过**：green-regression-01～05 均 INCOMPLETE，原件保留。其中的失败是短时限偶发（ready 文件读取竞态已修；recovery/run 的超时在 main-before-T082、main-T082、T090 三版本单独对照均 PASS），非阻塞 issue `20261016T162759Z`。主控曾把部分偶发失败归因于用户其他项目的构建负载，后续负载记录显示不可靠，已更正。
- 独立审查：01 INCOMPLETE（沙箱内无法调用 `/bin/ps`，变异未到业务断言；`workbench/README.md` stale）→ 主控沙箱外按 reviewer 设计的三变异执行，全部以业务断言失败（T090-WORKER-HEAD/DIRTY/BRANCH），补注 README → 02 PASS。
- 打分 `score-ff7303c80b2741848fb1542bfe608ec5`（边界 3、工程 2）。
- 主控验收 T-082 时未整组重跑原交付 8/9/18，漏掉了这个回归；之后验收凡改门禁检查，须整组重跑原 8/9/18。
