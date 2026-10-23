# 任务卡 T-149-1（过时历史测试的删除与标记）

先读 `evidence/2026-10-23-batch23/COMMON.md`、`.project-map/tickets/T-149-retire-stale-historical-tests.md`、`.project-map/inbox/20261023T181318Z-ideation-answer-001.md`、`.project-map/inbox/20261023T172046Z-worker:b23-t148-issue-001.md`。

| 字段 | 内容 |
| --- | --- |
| 编号 | T-149-1 |
| 来源 | T-149 ready_rev 1（ready_by executor；用户授权见 ticket） |
| 目标 | 13 个过时测试逐个调查并处置：删 / 标历史 / 待决；删后无悬空引用；标历史的有统一标记。 |
| 非目标 | 产品代码；现行测试断言；把旧测试迁移到新契约（用户没选 A）。 |
| 修改边界 | 允许：删除或标记 ticket 列的 13 个文件；为删除而必须同步的引用（其他测试/脚本的 import、`workbench/README.md` 中对这些文件的提及）；新增一个历史测试索引文件（如 `workbench/tests/HISTORICAL.md`）；`evidence/2026-10-23-batch23/T-149/**`。禁止：`workbench/src/**`、`workbench/app/**`、`.project-map/**`、`AGENTS.md`、`CONTEXT.md`、其他现行测试的断言。 |
| 验收文件（oracle_paths） | 无现行验收文件可改；合并回归脚本 `evidence/2026-10-23-batch23/merge-1/RUN-MERGE-REGRESSION-06.sh` 的全部项目须仍通过 |
| 任务类型 | 测试 |
| 复杂度 | M |
| 执行器 | Codex `gpt-6.1-sol`，`model_reasoning_effort="high"`，`service_tier="default"` |
| 起点 | 本卡提交所在的 main |
| 唯一写入者 | Herdr agent `b23-t149`，worktree `/Users/luckye/Documents/Code/a2a-wt-t149`，分支 `exec/t149` |

## 完成条件与交付

1. 先调查再动手：每个文件写下守护的契约、该契约现在是否有效、由哪个现行且在 main 上通过的测试覆盖（给出文件与检查名），被谁引用（`grep -rn` 全仓，含 `evidence/` 里的复跑脚本只列出、不改）。写成 `evidence/2026-10-23-batch23/T-149/DISPOSITION.md` 表格：文件、处置、理由、覆盖它的现行测试、引用方。
2. 判据按 ticket：不确定的标“待决”，不要硬删。删除前提交一版只含 DISPOSITION.md 的提交并停下说 `PLAN <提交号>`，等我确认处置后再动文件。
3. 我确认后：删除、标记（文件头注明“历史测试：只针对 <revision>，当前 main 不跑”，并在索引文件里列出）、修引用。
4. 在沙箱里能跑的现行测试（node/py 非 Electron）跑一遍确认没被删除牵连；Electron 部分写 RUN-OUTSIDE-01.sh（跑合并回归 06 的项目即可），我在沙箱外跑。`git add --sparse` 提交，交付时说 DELIVERED <提交号>。
