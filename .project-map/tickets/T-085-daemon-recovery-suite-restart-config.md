---
id: T-085
title: 缺陷：恢复套件中断用例重启后 daemon 缺审查配置（review_launch_config_required）
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

`workbench/tests/test_daemon_recovery_e2e.py` 的 `test_daemon_verify_interruption_and_operation_lock` 在 main 上失败：中断后 `restart()` 以空配置调用 `cli.ts daemon_start`，第二次 verify 时 `panes.ts` 的 `createReview` 因没有 `reviewers` 配置返回 `review_launch_config_required`。被中断的受控宿主带审查运行时，重启的 daemon 不带。

T-084 审查与基线复跑确认：该套件在基线 `fb5dd288` 上 5/5 失败（4×`score_required`、1×进程身份断言），T-084 把它修到 4/5；本用例的失败与尾注规则无关。

## Acceptance

- [ ] 红态：在当前 `main` 上经真实入口复现本用例失败，保存原始输出与命令。
- [ ] 修复后整套恢复套件 5/5 通过；重启路径使用与中断前同一份启动配置（来源可核对），不伪造审查结果、不跳过 verify。
- [ ] 变异：恢复为空配置重启时本用例重新失败。
- [ ] 不调用真实模型；`project_map.py status` 0 problems。

## 说明

- 来源：T-084 范围外发现（`evidence/2026-10-15-batch15/T-084/RESULTS.md`、`independent-review-02.md` 第 4 节；基线复跑 `regression-03/recovery-baseline/run.json`）。属已批准范围内的测试/恢复缺陷，执行主控按 T-004 边界自建（`ready_by: executor`）。
- 写入范围：恢复套件与受控宿主/重启辅助；如需改产品 daemon 启动配置持久化，先报告再定。
