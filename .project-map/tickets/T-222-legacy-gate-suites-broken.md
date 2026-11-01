---
id: T-222
title: 门禁与质量串的旧测试在 main 上失败，现在没人守着
type: research
status: closed
blocked_by: []
claimed_by:
supersedes:
ready: yes
ready_by: executor
ready_rev: 1
---

## Question

T-219 第二轮把共享夹具的 23 个调用者在基线 `a09da15f9` 和 T-219 候选上各跑了一次（证据在 `a2a-worktrees/T-219-evidence/round2/`，T-219 关闭时随它归档）。其中 17 个两边都失败或被前置条件挡住，与 T-219 的改动无关，按失败原因分组如下：

1. 调用已经不存在的 `pane_release` 命令（CLI exit 2）：`test_quality_chain_e2e.py`、`test_bad_worker_e2e.py`、`test_protected_acceptance_e2e.py`、`test_quality_widen_e2e.py`、`test_review_worktree_lifecycle_e2e.py`、`test_s3_quality_joint_e2e.py`。基线上它们先卡在缺项目的 `card_save`，T-219 修好这一步后才走到这里。
2. 仍用旧的 reviewers 数组配置，报 `review_launch_config_required`：`test_quality_legacy_e2e.py`。
3. 仍按“最后一条回复是 JSON”交审查结论，T-203 已删除这个协议，报 `review_result_missing`：`test_t082_review_boundary_e2e.py`、`test_t090_review_worker_boundary_e2e.py`。
4. host 缺操作员凭据，报 `operator_credential_required`：`test_conflict_trailer_proofs.py`、`test_relay_conflict_e2e.py`、`test_multiturn_identity_e2e.py`。
5. 直接调用 `card_save` 没带项目，报 `unknown_task`（T-123）：`test_daemon_gates_e2e.py`、`test_t084_trailer_record.py`。
6. 不起编排后台就调用门禁 CLI，连接 `control.sock` 报 ENOENT：`test_task_cards_e2e.py` 自身的 14 个用例。
7. 被运行条件挡住，没进入业务路径：`test_worktree_lifecycle_e2e.py`（需要未展开的历史证据 `evidence/2026-10-11-batch13/T-077/PLAN.md`）、`test_t082_parent_launch_e2e.py`（要求夹具放在外置盘）。

这些测试守的是质量串（红态核对、验收文件不被改动、规则式检查放宽）、冲突尾注、多回合身份、审查边界与副本生命周期。受管窗格切片要在 hc 上“重新证明交付与编排场景”，需要其中一部分作真实入口。

要回答：

1. 每组的现行契约是什么、由哪张票改的；测试要迁移，还是整份标为历史。
2. 这些测试守的检查里，哪些现在还有别的现行测试覆盖、哪些完全没人守。
3. 受管窗格切片之前，必须先迁移哪些。

处置照 T-154 的先例，由用户裁定（T-154 的处置索引在 `workbench/tests/HISTORICAL.md`）。本票先给出逐项依据和选项，不自行迁移或标历史。

## Resolution

2026-10-31 关闭（研究完成）。worker 报告见 [evidence/2026-10-31-batch29/T-222/REPORT.md](../../evidence/2026-10-31-batch29/T-222/REPORT.md)，源码固定在 `1e5f0a348`。

1. 现行契约：报告第 2 节把 17 个套件涉及的契约归为 C1～C14，逐条给出票号、行号与落实提交。主要变化：`pane_release` 删除，改由原生就绪放行（T-127、T-141）；预建 reviewers home 删除（T-127）；审查改经 `review_submit`（T-203）；后台启动者须提供操作员凭据（T-078-1、T-125、T-126）；任务与卡按项目定位（T-123）；卡外改动交主控判断（T-198）。17 个套件守的大部分业务检查仍有效，只是入口、协议或个别预期过时。
2. 覆盖：报告第 4 节逐项列出检查、原断言位置、其他现行覆盖与结论。大多数检查“没人守”或只有部分覆盖，例如红态 B/C 配对、规则冻结、第 3 次拒绝暂停、oracle 目录矩阵、四个尾注追溯字段、审查期间 worker 变动、冲突重派与第 4 次 CAS 落空。有直接现行断言的少数项（卡外交主控判断、路径重叠、按项目同名任务、`review_submit`、新用户回合）本次未复跑。
3. 受管窗格切片之前：报告第 5 节建议先在现有运行时恢复 P0-1～P0-6 六组检查，再换 hc，否则换运行时后分不清旧测试错误与运行时回归；这是排期建议，不是已定门禁。
4. 新发现：`workbench/tests/test_relay_scope.ts` 5 场中 4 场失败，首交付即 `invalid_relay_request`，原因是夹具用了不带项目的任务 id（C11），所以“跨 attempt 同 request_id 是新交付”目前也没有有效守护。主控复跑结果相同（`controller/relay-scope-rerun.log`）。

主控抽查了报告引用的 `pane_release` 调用、relay-scope 夹具、`HISTORICAL.md` 的 T-154 先例、cards 里不带项目的 `card_save`、parent-launch 的外置盘前置，都与源码一致。

处置（迁移、标历史或拆开）照 T-154 先例由用户裁定，见 [T-225](T-225-legacy-suites-disposition.md)。
