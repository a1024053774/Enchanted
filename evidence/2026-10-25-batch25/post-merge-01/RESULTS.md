# T-177、T-179、T-180 合并后复跑

## 状态：PASS

T-180 审查 P1 要求合并后重跑。main 在 a1b626f34（T-177、T-179、T-180 都已合并；T-179 与 T-180 在 `src/daemon.ts` 的 import 与只读命令表上有相邻行冲突，两边都保留）。三项同时运行，均为脚本化模型，不耗额度：

| 测试 | 结果 |
| --- | --- |
| `test_t177_sidebar_history_e2e.py` | PASS（`t177/summary.json`） |
| `test_t179_receipt_summary_e2e.py` | PASS（`t179/summary.json`） |
| `test_t180_default_work_branch_e2e.py` | PASS（`t180/summary.json`） |

命令：在 `workbench/` 下 `python3 tests/<测试> --summary evidence/2026-10-25-batch25/post-merge-01/<t>/summary.json`。
