你是 T-269 的复审员，是新开的会话，和审查 01 不是同一个。这份任务书由实现者 Claude Code 会话 `8be1abdd-5af9-4023-bff8-cbc0f40d9a84` 写，不是用户写的。

只读规则：
- 不改任何文件，不提交，不建、不移动 Git 引用；
- 不运行会写文件的命令；
- 不碰正在运行的 Enchanted 后台及其数据目录 `~/Library/Application Support/a2a-orchestrator/`。

用中文回答。仓库 `/Users/luckye/Documents/Code/a2a` 是稀疏 checkout，不要 checkout、switch 或 reapply。

## 复审范围

只审审查 01 之后的修复范围。审查 01 的原文在 `evidence/2026-11-09-batch35/T-269/review-01.md`，结论是“不可合并”。请核对它提的 5 条是否已经真正解决，并看这次修复有没有带来新问题。

## 改动（未提交，基于 `519fafb21`）

- 完整 diff：`/private/tmp/claude-501/-Users-luckye-Documents-Code-a2a/8be1abdd-5af9-4023-bff8-cbc0f40d9a84/scratchpad/t269-v2.diff`。涉及：
  - `workbench/src/store.ts`：两个索引，加新方法 `launchEvents`；
  - `workbench/src/panes.ts` 12 处、`workbench/src/daemon.ts` 1 处：调用方改用 `launchEvents`；
  - `workbench/README.md`：一句说明。
- 测试：`workbench/tests/test_t269_event_indexes.mjs`，已整份重写。
- 票：`.project-map/tickets/T-269-event-table-indexes.md`，Acceptance 以这张票为准。
- 证据：`evidence/2026-11-09-batch35/T-269/` 下的 `RESULTS.md`、`green-02.json`、`red-parent-02.json`、三个 `mutant-*.json`、`regression-parent.json`、`regression-candidate.json`、`run_regression.py`、`live-copy-timing-01.json`、`time_live_copy.mjs`。

## 请你判断

1. 这 13 处替换，每一处在行为上是否和原来等价：
   - 返回的行、顺序和 `data` 解析都要一样；
   - 原有的其他过滤条件要保留；
   - `launch` 的取值来源不能变，包括 `launch` 变量与 `pane.record.id` 不同的情况。
2. 还有没有别的高频路径，在不加更多改动时仍会读全表、占住主线程，比如每秒或每次 hook 都会走到的。请举出调用链。只要是本票范围外、已存在的问题，请注明“范围外”，不作为拒绝理由，但要写进发现。
3. 这是 `REVIEW.md` 第 19 行列出的敏感路径，失败的样子是“用户已有的数据目录打不开、被改坏或丢数据”。请核对：
   - 已有的约 21 万行正式数据，打开时建索引会不会出问题；
   - 回退到 0.1.6 后，带着这两个索引的状态文件还能不能正常使用；
   - 门禁的另一个连接、`busy_timeout`、启动期限 10 秒这几方面有没有风险。
4. 测试和三个变异，是否真能拦住它们各自声称要拦的问题；回归对照的说法有没有夸大。

每条发现写：严重度（P1/P2/P3）、`文件:行`、问题、证据，以及怎样复现或证伪。最后一行只写结论：`可合并` 或 `不可合并`。
