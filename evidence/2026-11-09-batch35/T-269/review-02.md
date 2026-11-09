# T-269 复审（审查 02）

审查员：codex-cli 0.167.0，`gpt-6-astra`，reasoning xhigh，service_tier default，`-s read-only`，新开会话。任务书原文见本目录 `review-02-brief.md`。下面依次是审查员的三段回答原文：中间小结、主结论、它对 Stop hook 提示的回应。

13 处调用的机械对照已通过：每处都保留了原来的 `launch` 表达式和其他过滤条件，文件其余内容未变。内存探针也确认新方法返回的完整行、顺序和 JSON 解析结果一致。仍需单列一个范围外风险：侧栏每三秒会聚合所有非空 launch 的历史事件，两个索引没有消除这部分工作量。

---

**复审状态：INCOMPLETE。** 审查 01 的第 1、2、4、5 条已在对应范围内解决；第 3 条的回归证据虽然补上了，但新运行脚本把两个没有执行测试的模块计为通过，仍不足以支持报告中的结论。未发现这次生产代码改动引入明确的行为回归或数据损坏。

审查对象是基于 `519fafb211ee3c13a4ec476ae4f60bed919e7800` 的未提交候选。当前代码 diff 的内容与提供的 `t269-v2.diff` 一致。未修改文件或 Git 引用，未接触正式后台及其数据目录；独立数据库探针全部使用 `:memory:`。

1. **P2 — 回归脚本没有执行两个声称通过的测试，关键路径的覆盖仍不完整。**

   位置：[run_regression.py:29](/Users/luckye/Documents/Code/a2a/evidence/2026-11-09-batch35/T-269/run_regression.py:29)、[RESULTS.md:48](/Users/luckye/Documents/Code/a2a/evidence/2026-11-09-batch35/T-269/RESULTS.md:48)。

   `t108_answer_lifecycle_contracts.mjs` 和 `t108_hook_failure_contracts.mjs` 只导出函数，没有顶层调用。脚本直接执行这两个文件，得到退出码 0，但没有运行场景。两份回归 JSON 中，这两项均为 `status:null`、`tail:[]`。

   **独立证据：**我在禁止文件写入的探针中加载了两个真实模块，观察到导出函数存在，但事件方法调用次数和文件写入尝试次数均为 0。真正的入口 [test_t108_questions.mjs:35](/Users/luckye/Documents/Code/a2a/workbench/tests/test_t108_questions.mjs:35) 会调用它们；现存父版和候选记录都在第 36 行失败：429 个 hook 场景中有相同的 179 个失败，尚未执行第 37 行的回答生命周期场景。

   同一脚本第 31 行的 `t166_queued_input` 调用也有前置错误：测试要求输出目录已存在，脚本却传入未创建的 `{out}.json` 路径。因此两边都在 [test_t166_queued_input.ts:18](/Users/luckye/Documents/Code/a2a/workbench/tests/test_t166_queued_input.ts:18) 的 `mkdirSync` 失败，未进入本次修改涉及的排队输入行为。

   **可成立的结论：**15 项记录的退出码、状态和错误字段一致；其中有 **4 项实际通过、2 项未执行场景、9 项失败**。不能写成“6 项通过并覆盖相关路径”，前置失败也只能说明观察到相同失败，不能证明后续行为没有变差。

   **复现／证伪：**在隔离运行中显式调用两个导出函数，要求场景数非零、逐项断言通过，并保存结果；为 T-166 创建其要求的输出目录后重跑父版／候选。属于同一证据不变式再次失守：**退出码 0 必须伴随实际执行的业务断言，前置失败不能充当业务回归证据。**后续应针对这一不变式修正运行器并系统核对，不再用新增审查轮次代替覆盖。

2. **P2，范围外、既有问题 — 侧栏每三秒仍遍历全部非空 launch 的事件，索引没有消除这部分主线程负担。**

   位置：[sidebar.ts:153](/Users/luckye/Documents/Code/a2a/workbench/src/sidebar.ts:153)。

   调用链为：

   `renderer.tsx:806/825` 三秒定时器 → `window.a2a.sidebar()` → `main.ts:230` → `daemon.ts:627–628` → `sidebarSnapshot()` → `MAX(time) GROUP BY launch`。

   **证据：**我用安装包的 Node v24.18.1／SQLite 3.53.1，在带两个索引的内存库中运行这里的真实 SQL。210,547 行均具有非空 launch，查询返回 160 组，单次约 153 ms；对聚合参数计数确认访问了全部 210,547 行。查询计划却显示：

   ```text
   SEARCH orchestration_events USING INDEX orchestration_events_launch_type (launch>?)
   ```

   因而这里不能凭 `SEARCH` 认定工作量很小。该数值是合成夹具结果，不能外推为正式后台的 CPU 占用。

   **复现／证伪：**在隔离库中放入大量非空 launch 的事件，执行该行 SQL并测量；要判断实际影响，应采样侧栏请求期间的后台主线程。这个问题审查 01 已提及，本次没有修改它，**不作为拒绝本候选的理由**。

13 处替换的核对结果如下。对 `panes.ts` 和 `daemon.ts`，我从父版本机械执行相同替换后，与当前文件逐字比较一致；因此没有伴随修改其他谓词、切片、投影或调用时机。

| 位置 | 保留的 launch 来源 | 核对结果 |
|---|---|---|
| `panes.ts:1898` | `pane.record.id` | 晚启动信任检查保持 |
| `panes.ts:2002` | `pane.record.id` | 保留 `controller_screen_key_intent` 类型过滤 |
| `panes.ts:2258` | `launch` | 排队输入历史及后续 `findLast` 条件保持 |
| `panes.ts:2344` | `launch` | Codex Stop 前信任检查保持 |
| `panes.ts:2353` | `launch` | transfer 后重新读取、重新核对保持 |
| `panes.ts:2384` | `pane.record.id` | 报告回合结束的信任检查保持 |
| `panes.ts:2516` | `pane.record.id` | Claude Stop 前信任检查保持 |
| `panes.ts:2526` | `pane.record.id` | transfer 后重新核对保持 |
| `panes.ts:2551` | `pane.record.id` | 保留 `claude_prompt_absorbed` 类型过滤及 UUID 投影 |
| `panes.ts:2581` | `launch` | 问题投影输入保持 |
| `panes.ts:2586` | `launch` | 回答问题前的信任检查保持 |
| `panes.ts:2606` | `launch` | 异步检查点重新读取及后续条件保持 |
| `daemon.ts:1038` | `pane.record.id` | 保留类型、submission、`slice(0,3)` 和字段投影 |

[store.ts:174](/Users/luckye/Documents/Code/a2a/workbench/src/store.ts:174) 仍使用 `SELECT *`、明确 `ORDER BY seq`，以及与 `read()` 完全相同的 `JSON.parse(String(data))` 映射。在 3,000 行内存夹具上，我对 45 个字符串 launch 值比较了完整返回对象，包括空字符串、中文／引号、不存在的 launch 和不同的 launch 标识，均与旧的 `read().filter(...)` 一致。这里的等价结论针对有效事件数据；没有把 `launch` 变量替换成 `pane.record.id`，也没有依赖两者必须相等。

审查 01 五条的处置和变异证据：

| 原发现 | 复审判断 |
|---|---|
| 1．漏检缺少复合索引 | **已解决。** 测试明确核对索引列序列，并要求按 launch 的查询实际利用 launch 条件；独立探针确认仅保留 type 索引会被拒绝。 |
| 2．放过带索引的全表 SCAN | **已解决。** 我将原来的 `SCAN … USING INDEX` 反例交给当前判定代码，确认被拒绝。这也符合 [SQLite 对 SCAN 的定义](https://www.sqlite.org/eqp.html)。 |
| 3．回归排除结论缺少证据 | **部分解决，仍未关闭。** 已有可核对的父版／候选输出，但存在上述空跑和调用错误。 |
| 4．红态计数、无序查询概括错误 | **原两处已更正。** 当前材料不再普遍承诺无 `ORDER BY` 查询的顺序。 |
| 5．13 处按 launch 过滤前全表读取 | **已解决。** 参数来源和剩余条件保持，读取已下推至 SQL。 |

三个变异确实分别拦住了它们指定的问题。我独立核对得到：缺复合索引时按 launch 的查询判红；恢复 `questions()` 的旧写法时源码检查由 0 个命中变成 1 个；去掉排序后，前四个 seq 为 `[88,208,328,448]`，而期望是 `[8,48,88,128]`。其中第二个是**特定写法的静态守卫**，不能替代真实调用行为的测试。另外，`RESULTS.md:56` 把变异 2 当作原第 2 条的证据不准确：它验证的是调用方全表读取；原第 2 条已由本次独立 SCAN 反例确认修复。

数据库敏感路径的核对结果如下：

- **约 21 万行旧库建索引：有正面证据，未发现损坏数据的新增路径。** 保存的副本记录显示 210,547 行，首次构造耗时 311 ms、再次打开 1 ms。DDL 只创建普通非唯一索引，没有改动事件行或替换触发器。不过，[time_live_copy.mjs:18](/Users/luckye/Documents/Code/a2a/evidence/2026-11-09-batch35/T-269/time_live_copy.mjs:18) 开始的多次查询已经预热数据库；311 ms 是这个无竞争副本的测量，不能当成冷启动或竞争锁情况下的上限。

- **回退到 0.1.6：代码和内存兼容性核对通过，文件级回退尚未验证。** 我读取了已安装 0.1.6 的 Store 源码，用真实构造及读写代码在共享内存库中执行“旧版建库写入 → 候选补索引 → 旧版再次初始化、读取、追加”。已有行保持一致，旧版成功追加，UPDATE／DELETE 仍被触发器拒绝，`integrity_check` 为 `ok`。这支持两个普通索引与旧代码兼容，但没有覆盖关闭并重新打开真实文件、WAL 恢复或完整旧后台启动。

- **另一个门禁连接不会在正常启动顺序中与本次建索引互相争锁。** `daemon.ts:70–72` 先完成 Store 构造，再创建门禁连接；索引属于共享数据库，门禁连接也能使用。两边均设置 WAL 和 `busy_timeout=5000`。外部写连接仍可能竞争锁，WAL 同时只允许一个写者；5 秒是锁等待期限，不是索引执行期限。[SQLite WAL 并发说明](https://www.sqlite.org/wal.html)、[busy_timeout 说明](https://www.sqlite.org/c3ref/busy_timeout.html)。

- **10 秒启动期限仍有未验证边界。** [transport.ts:91](/Users/luckye/Documents/Code/a2a/workbench/src/transport.ts:91) 的计时覆盖整个子进程启动。两个索引分别执行，等待锁及其他初始化耗时可能累加；超时后父进程报告失败，但不会杀掉子进程。本次没有竞争写锁、冷启动或启动超时的复现证据，因此不把它写成已发生缺陷，也不宣称风险已排除。

结构审查未发现新增吞异常、fallback、重试或绕过门禁的路径。正式安装后的 CPU、采样和 hook 时长仍未验收；地图检查为 0 个结构问题、`REVIEW.md` 一项 stale，保持只读未处理。

不可合并

---

该异常边界属于合理处理，**不构成新增缺陷**。

[run_regression.py:45](/Users/luckye/Documents/Code/a2a/evidence/2026-11-09-batch35/T-269/run_regression.py:45) 的真实入口是第 43 行 `subprocess.run(..., timeout=300)`：某个测试超过 300 秒时会抛出 `TimeoutExpired`。运行器负责控制测试期限、记录结果并继续收集其他测试的证据，因此由这一层捕获并把结果记为 `"timeout"` 是合适的，没有把超时伪装成通过，应保留。

现存父版和候选记录中没有超时项，所以这是对可达性和职责归属的代码核对，不是已执行的超时场景验证。该定位器命中不改变前述复审结论；阻碍合并的仍是回归证据中的空跑及调用错误。

不可合并

---

