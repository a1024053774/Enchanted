# 任务卡 T-156-1（旧 t082 runner 与 quality host bootstrap：删或上报）

先读 `.project-map/tickets/T-156-retire-t082-legacy-runner.md`、`workbench/tests/HISTORICAL.md`、`evidence/2026-10-23-batch23/T-152/`（迁移后 t082 的覆盖范围）。

| 字段 | 内容 |
| --- | --- |
| 编号 | T-156-1 |
| 来源 | T-156 ready_rev 1（ready_by executor；授权引用见 ticket） |
| 目标 | 两个旧文件在当前 main 实跑，逐项对照覆盖；可删即删并记 HISTORICAL.md，唯一守护者停下上报。 |
| 修改边界 | 允许：删除 `workbench/tests/run_t082_boundary.py`、`workbench/tests/test_t078_quality_host_bootstrap.py`（仅当判定可删）；编辑 `workbench/tests/HISTORICAL.md`；`evidence/2026-10-23-batch24/T-156/**`。禁止：`workbench/src/**`、`workbench/app/**`、其他测试文件、`.project-map/**`。 |
| 任务类型 | 测试 |
| 复杂度 | S |
| 执行器 | Codex `gpt-6.1-sol`，`model_reasoning_effort="high"`，`service_tier="default"` |
| 唯一写入者 | Herdr agent `b24-t156`，worktree `/Users/luckye/Documents/Code/a2a-wt-t156`，分支 `exec/t156` |

沙箱外命令（启动 daemon/PTY、/bin/ps）写成脚本停下交我跑，不发起提权请求。测试启动的后台服务脱离调用者进程组。证据按 T-088。`git add --sparse` 提交（九项尾注），完成说 `DELIVERED <提交号>`；遇到唯一守护者说 `NEEDS-DECISION <提交号>`。
