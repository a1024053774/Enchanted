# 任务卡 T-154-1（6 个测试标历史；HISTORICAL.md 最终处置）

先读 `evidence/2026-10-23-batch23/COMMON.md`、`.project-map/tickets/T-154-mark-six-historical.md`、`.project-map/inbox/20261023T185657Z-ideation-answer-001.md`、`evidence/2026-10-23-batch23/T-149/DISPOSITION.md`、`workbench/tests/HISTORICAL.md`。

| 字段 | 内容 |
| --- | --- |
| 编号 | T-154-1 |
| 目标 | 见 ticket。 |
| 修改边界 | 允许：6 个文件只加文件头注释；`workbench/tests/HISTORICAL.md`；`evidence/2026-10-23-batch23/T-154/**`。禁止：其他一切，尤其 T-150～T-153 的 4 个文件。 |
| 任务类型 | 测试 |
| 复杂度 | S |
| 执行器 | Codex `gpt-6.1-sol` high，default |
| 唯一写入者 | `b23-t154`，worktree `/Users/luckye/Documents/Code/a2a-wt-t154`，分支 `exec/t154` |

## 完成条件与交付

1. 每个文件找到最后一次在证据里通过的 revision（引用证据文件路径；找不到就写“无通过证据”，不要编）。
2. 加文件头注释，更新 HISTORICAL.md；沙箱内确认导入这些文件的离线测试仍可解析。
3. RESULTS.md；`git add --sparse` 提交，说 DELIVERED <提交号>。
