# 任务卡 T-156-2（迁移凭据检查后删除旧 t082 runner 与 bootstrap 测试）

先读 `.project-map/tickets/T-156-retire-t082-legacy-runner.md`（含 2026-10-24 答复）、`.project-map/inbox/20261024T005556Z-ideation-answer-002.md`、`evidence/2026-10-23-batch24/T-156/COVERAGE.md` 与 `BASELINE.json`。

| 字段 | 内容 |
| --- | --- |
| 编号 | T-156-2 |
| 来源 | T-156；用户 2026-10-24 逐字“迁移后删 (Recommended)” |
| 目标 | 把 `test_t078_quality_host_bootstrap.py` 第 71～100 行守护的检查（`QualityCase.start_host → quality_chain_host.ts` 两代隔离 operator 凭据创建、state/kind/0600、清理）迁到一个现行测试里（新建 `workbench/tests/test_t156_quality_host_credentials.py`，或并入现行质量串测试并说明），覆盖不丢；然后删除 `run_t082_boundary.py` 与 `test_t078_quality_host_bootstrap.py`，`HISTORICAL.md` 记录删除与覆盖去向。 |
| 修改边界 | 允许：新建上述测试；删除那两个文件；`workbench/tests/HISTORICAL.md`；`evidence/2026-10-23-batch24/T-156/**`。禁止：产品代码、其他测试的断言、`.project-map/**`。 |
| 任务类型 | 测试 |
| 复杂度 | M |
| 执行器 | Codex `gpt-6.1-sol`，`model_reasoning_effort="high"`，`service_tier="default"` |
| 起点 | 本卡提交所在的 main |
| 唯一写入者 | Herdr agent `b24-t156b`，worktree `/Users/luckye/Documents/Code/a2a-wt-t156b`，分支 `exec/t156b` |

## 完成条件

1. 迁移后的测试在当前 main 绿；红态：变异删除 `quality_chain_host.ts` 中 `createOperatorCredential` 调用（或等价已知坏实现，在隔离源码副本中），测试必须失败且落在凭据检查上；其余三项检查各有可区分的变异或说明为何合并。
2. 期望值来自原 bootstrap 测试与 COVERAGE.md 的检查定义，不抄产品输出。
3. 删除后 `git grep` 无残留导入；受影响测试导入或运行通过。
4. 沙箱外运行写 `RUN-OUTSIDE-NN` 交执行主控，不发起提权。`git add --sparse` 提交，完成说 `DELIVERED <提交号>`。
