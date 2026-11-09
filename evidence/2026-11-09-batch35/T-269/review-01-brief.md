你是 T-269 的独立审查员。这份任务书由 Claude Code 会话 `8be1abdd-5af9-4023-bff8-cbc0f40d9a84`（实现者）写，不是用户写的。你只读：不改任何文件，不提交，不建或移动 Git 引用，不运行会写文件的命令，不碰正在运行的 Enchanted 后台和它的数据目录 `~/Library/Application Support/a2a-orchestrator/`。用中文回答。

仓库：`/Users/luckye/Documents/Code/a2a`。这是稀疏 checkout，不要 checkout、switch 或 reapply。

## 要审的改动（未提交）

- `workbench/src/store.ts`：建表时加 `orchestration_events(launch, type)` 和 `orchestration_events(type)` 两个索引。diff 在 `/private/tmp/claude-501/-Users-luckye-Documents-Code-a2a/8be1abdd-5af9-4023-bff8-cbc0f40d9a84/scratchpad/t269.diff`。
- 新测试 `workbench/tests/test_t269_event_indexes.mjs`。
- 票 `.project-map/tickets/T-269-event-table-indexes.md`，Acceptance 以这张票为准。
- 证据 `evidence/2026-11-09-batch35/T-269/`：`RESULTS.md`、`red-parent-01.json`、`green-01.json`。

## 背景（实现者的说法，请自己核对）

正式后台 CPU 一直在 97% 左右，10 秒采样里主线程全部耗在 SQLite `.get()` 上。事件表约 21 万行，除主键外没有任何索引。

## 请你判断

1. 这两个索引对不对、够不够：
   - 对照 `workbench/src` 里所有查 `orchestration_events` 的语句，看后台的高频路径是否都能用上；
   - 有没有漏掉明显也是高频的查询方式，比如按 `task` 查、`json_extract` 条件、自连接；
   - 漏掉的那些，是否属于“不加就仍会占满主线程”的情况。
2. 回归风险：
   - 原来不写 ORDER BY、依赖 rowid 顺序的查询，返回顺序会不会变；
   - 门禁 `workbench/src/gates/core.ts` 用的是不是另一个连接；后台启动时在 21 万行的旧文件上建索引，会不会与门禁或别的连接的锁冲突（`busy_timeout`、WAL），或者让启动超时；
   - 只追加触发器、迁移逻辑会不会受影响。
3. 测试是否真能证明它声称的：
   - 记录真实查询的方式是否可靠，会不会漏掉查询；
   - 判全表扫描的规则有没有漏判；
   - 父版本判红是否成立。
4. `RESULTS.md` 的说法有没有夸大，尤其是“7 项失败是早就存在的”这一条的依据。

每条发现写：严重度（P1/P2/P3）、`文件:行`、问题、你据以判断的证据，以及怎样能复现或证伪。没有发现就明说。最后一行只写结论：`可合并` 或 `不可合并`。
