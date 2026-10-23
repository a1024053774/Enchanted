# 任务卡 T-153-1（迁移 `run_worker_delivery.py` 到现行契约）

先读 `evidence/2026-10-23-batch23/COMMON.md`、`.project-map/tickets/T-153-migrate-worker-delivery.md`、`.project-map/inbox/20261023T185657Z-ideation-answer-001.md`、`evidence/2026-10-23-batch23/T-149/DISPOSITION.md` 中本文件一行。

| 字段 | 内容 |
| --- | --- |
| 编号 | T-153-1 |
| 来源 | T-153 ready_rev 1（ready_by executor；用户授权见 ticket） |
| 目标 | `workbench/tests/run_worker_delivery.py` 的过时断言改到现行契约，保留有效检查；当前 main 绿；红态落在有效检查上。 |
| 非目标 | 产品代码；其他测试；HISTORICAL.md。 |
| 修改边界 | 允许：`workbench/tests/run_worker_delivery.py` 及只被它使用的辅助文件（列出来）；`evidence/2026-10-23-batch23/T-153/**`。禁止：`workbench/src/**`、`workbench/app/**`、其他测试、`workbench/tests/HISTORICAL.md`、`.project-map/**`、`AGENTS.md`、`CONTEXT.md`。 |
| 验收文件（oracle_paths） | `workbench/tests/run_worker_delivery.py`（本卡获授权修改） |
| 任务类型 | 测试 |
| 复杂度 | M |
| 执行器 | Codex `gpt-6.1-sol`，`model_reasoning_effort="high"`，`service_tier="default"` |
| 起点 | 本卡提交所在的 main |
| 唯一写入者 | Herdr agent `b23-t153`，worktree `/Users/luckye/Documents/Code/a2a-wt-t153`，分支 `exec/t153` |

## 完成条件与交付

1. 先列出该文件每条断言/检查：现行有效、过时（依据哪张 ticket/规格/产品代码行）、需改成什么。新期望来自现行规格与 ticket，不从产品当前输出抄。
2. 改断言，保留有效检查。变异或已知坏实现：优先用文件已有的 mutant；若已有 mutant 落在被改的断言上，补一个落在保留检查上的。
3. 沙箱内能跑就跑；需要 Electron、真实 CLI 或 socket 的写 `RUN-OUTSIDE-01.sh`（绿态 + 每个 mutant，输出 JSON 摘要到 `evidence/2026-10-23-batch23/T-153/outside-01-*/`），我在沙箱外跑。
4. RESULTS.md 逐条记录改动。`git add --sparse` 提交，说 DELIVERED <提交号>。
