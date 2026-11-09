# T-269 审查 01

审查员：codex-cli 0.167.0，`gpt-6-astra`，reasoning xhigh，service_tier default，`-s read-only`，新开会话。任务书原文见本目录 `review-01-brief.md`。以下是审查员的最终回答原文。审查员的 Stop hook 另外报了 `workbench/README.md`、`REVIEW.md` 两项 stale；它是只读的，没有处理。

**验收状态：INCOMPLETE。** 两个索引的方向正确，未发现这两条 DDL 本身导致数据、触发器或门禁语义损坏；但测试存在可复现的漏检，回归证据不足，也遗漏了仍会全量读取事件表的高频路径。

审查对象为基于 `519fafb211ee3c13a4ec476ae4f60bed919e7800` 的未提交改动。未修改文件、Git 引用或正式后台数据；未运行会落盘的测试。以下独立探针使用安装包的 Node v24.18.1／SQLite 3.53.1，数据库均为 `:memory:`。

1. **P2 — 测试无法检出缺少 `(launch,type)` 索引。**  
   位置：[workbench/tests/test_t269_event_indexes.mjs:57](/Users/luckye/Documents/Code/a2a/workbench/tests/test_t269_event_indexes.mjs:57)，以及第 90、100 行。

   测试只要求旧库有至少一个索引，再让重开、新库的索引列表与旧库相等，没有独立核对票中要求的两个索引及列顺序。

   **证据：**在内存库中仅保留 `(type)`，对 `green-01.json` 中的 11 条真实 SQL 执行查询计划检查，**11 条全部通过现有扫描判定**。此时 `lastEvent` 的计划只有 `(type=?)`，已经失去按 launch 缩小范围的能力。其他索引列表断言也不能拒绝“所有库都只有同一个索引”的实现。

   **复现／证伪：**在隔离候选中删去 `(launch,type)` 的 DDL，运行完整新测试；测试应明确失败。建议用 `PRAGMA index_info` 核对两个列序列，并让按 launch 的查询断言实际利用 launch 条件。

2. **P2 — 扫描判定会放过遍历整张表的索引扫描。**  
   位置：[workbench/tests/test_t269_event_indexes.mjs:83](/Users/luckye/Documents/Code/a2a/workbench/tests/test_t269_event_indexes.mjs:83)。

   `! /USING (COVERING )?INDEX/` 将所有带索引的 `SCAN` 排除，混淆了“通过索引遍历全部记录”和“根据条件定位少量记录”。

   **证据：**内存探针执行：

   ```sql
   EXPLAIN QUERY PLAN
   SELECT data
   FROM orchestration_events INDEXED BY orchestration_events_launch_type
   WHERE task=?;
   ```

   得到 `SCAN orchestration_events USING INDEX orchestration_events_launch_type`，现有判定仍通过。这是非覆盖索引扫描，还需要回表读取数据。SQLite 官方也明确将按索引顺序遍历全部记录归为 `SCAN`。[SQLite 查询计划说明](https://www.sqlite.org/eqp.html)

   **复现／证伪：**把上述计划交给第 81—84 行的判定即可复现。对于本票的选择性查询，应拒绝这种全量扫描；同时不能仅凭出现 `SEARCH` 就推断查询便宜，见第 5 项。

3. **P2 — “7 项失败早已存在、与本次改动无关”缺少可核对的证据。**  
   位置：[evidence/2026-11-09-batch35/T-269/RESULTS.md:36](/Users/luckye/Documents/Code/a2a/evidence/2026-11-09-batch35/T-269/RESULTS.md:36)，尤其第 39 行。

   **证据：**目录中只有报告和索引测试的红绿两个 JSON；7 项测试的父版本／候选输出均已删除。没有逐项命令、退出码、失败断言和调用栈，无法核对“完全相同的错误”。历史索引确实将 `test_t112_execution.mjs` 列为历史测试，T-219 也记过 `test_t078_pane_runtime.ts` 的旧失败，但这些不能证明当前父版本上的这 7 次具体失败。

   此外，缺 `vm.SourceTextModule`、缺运行组件等前置失败，即使两边相同，也不能证明后续业务路径没有回归。

   **复现／证伪：**在相同运行时、参数和隔离环境中，分别跑精确父版本及候选，保存每项文本输出与退出码，并标明是否到达受影响行为。补齐前，这一部分应写“回归验证不完整”，不能作为排除回归的结论。

4. **P3 — RESULTS.md 有两处与现存材料不符的表述。**  
   位置：[evidence/2026-11-09-batch35/T-269/RESULTS.md:20](/Users/luckye/Documents/Code/a2a/evidence/2026-11-09-batch35/T-269/RESULTS.md:20)，以及第 41 行。

   **证据：**

   - 第 20 行称保存的红态不认识别名、`hasPaneLayout` 没判红；但 [red-parent-01.json:63](/Users/luckye/Documents/Code/a2a/evidence/2026-11-09-batch35/T-269/red-parent-01.json:63) 明确保存了该项 `ok:false` 和 `SCAN e`。当前文件确实是 **16 项中 12 项失败**。
   - 第 41 行称所有无 ORDER BY 查询都只有单个 type 等值条件；实际有 `hasPaneLayout` 的 `type IN (...)`、门禁的多 type 存在性查询，以及侧栏的分组聚合。它们未必有顺序敏感的消费者，但不能用该概括证明“返回顺序不变”。

   **复现／证伪：**直接对照上述 JSON 和 `store.ts:88`、`sidebar.ts:148`、`sidebar.ts:153`、`gates/core.ts:4577`。应修正文案；目前没有据此发现业务顺序回归。

5. **P2，pre-existing — 一个每秒触发的全表读取路径没有得到改善，也未进入本次测试。**  
   位置：[workbench/src/store.ts:168](/Users/luckye/Documents/Code/a2a/workbench/src/store.ts:168)、[workbench/src/panes.ts:2581](/Users/luckye/Documents/Code/a2a/workbench/src/panes.ts:2581)。

   **证据：**调用链为：

   `renderer.tsx:346/367` 每约一秒读取可见窗格快照 → `main.ts:572` → `daemon.ts:942` → `panes.questions()` → `store.read().filter(...)`。

   最后一步仍执行 `SELECT * FROM orchestration_events ORDER BY seq`，读取、解析所有事件后才按 launch 过滤。两个索引对此无效。独立内存夹具中，**21 万行、每行 JSON 794 字节、两个索引均存在**，调用真实 `OrchestrationStore.read()` 再过滤单个 launch，单次约 **814 ms**，计划仍为 `SCAN orchestration_events`。Stop 信任检查也有相同全量读取模式，例如 `panes.ts:2344`、`2353`。

   **复现／证伪：**按上述规模构造隔离库，调用真实读取方法；进一步在隔离后台打开受管窗格，采样快照与 hook 并发时的主线程和请求时长。814 ms 是合成夹具结果，**不能直接认定正式后台仍会持续 97%**，但说明这是足以继续占用大量主线程时间的路径。解决它需要把过滤下推到 SQL，仅追加索引不够。它不是本次引入的回归，不能单独作为拒绝这两条 DDL 的理由。

对其余要求的核对结果如下：

- **索引选择合理。** `(launch,type)` 能服务 launch＋type、相关 seq 范围和两处自连接；`(type)` 能服务跨 launch 的角色申请、布局和设置查询。`seq INTEGER PRIMARY KEY` 是 rowid，普通索引已有 rowid 作为同键记录的排序依据，无须为了这些查询再显式追加 seq。[SQLite 索引结构说明](https://www.sqlite.org/queryplanner.html)
- **未覆盖的查询不只按 task。** `store.read(task)` 仍全表扫描；`metrics.ts:103` 的 task＋type 查询只按 type 缩小范围。`sidebar.ts:153` 的 `MAX(time) GROUP BY launch` 虽显示 `SEARCH … (launch>?)`，仍需读取全部非空 launch 的事件并回表取 time；侧栏每 3 秒执行一次。JSON 条件通常只受外围 type／launch 索引帮助，JSON 字段本身没有被索引。两处自连接在探针中两侧都能使用复合索引，尚无证据证明必须再加 JSON 索引才能避免满载。
- **未发现具体的顺序回归。** 状态重放主要显式 `ORDER BY seq`；其他无序查询的消费者多为存在性、集合、计数或唯一性检查。但 SQL 未写 ORDER BY 就没有顺序契约，报告不应作普遍保证。[SQLite ORDER BY 说明](https://www.sqlite.org/lang_select.html)
- **门禁是另一个连接，正常启动顺序避免了自身争锁。** `gates/core.ts:193` 另开同一个 `state.sqlite3`，两边均设 WAL 和 `busy_timeout=5000`；`daemon.ts:70–72` 先完成 Store 构造，再创建门禁。外部写连接仍可能竞争写锁，WAL 并不允许多个写者同时写；5 秒是锁等待期限，不是建索引执行期限。[WAL 并发说明](https://www.sqlite.org/wal.html)、[busy_timeout 说明](https://www.sqlite.org/c3ref/busy_timeout.html) 启动总期限为 `transport.ts:94` 的 10 秒。报告所称副本首次打开 283 ms 缺少保存的运行输出，不能据此排除竞争锁或启动超时，但目前也没有证据将其认定为已发生缺陷。
- **触发器和迁移未发现新增问题。** 新 DDL 不更新或删除事件，不替换触发器，也未修改原有 launch 表迁移。现存绿态包含旧库行数、UPDATE／DELETE 被拒和重复打开的通过记录。
- **父版本判红成立，查询捕获范围有限。** 当前红态保存了 11 条扫描失败；我在无索引的内存 schema 上也得到这 11 条失败。拦截当前连接的 `prepare` 能记录这几个同步方法本次执行的 SQL，但只覆盖手工调用的分支，不覆盖 Panes、Sidebar、门禁连接等全部查询，也没有记录绑定参数。因此它是局部查询计划证据，不能代表后台完整负载。

正式安装后的 CPU、采样和 hook 时长尚未验证，报告对此如实标注，没有将这项验收写成已完成。当前应先修正测试漏检、补齐回归证据并纠正报告；正式性能验收还需覆盖上述全量读取路径。

不可合并
