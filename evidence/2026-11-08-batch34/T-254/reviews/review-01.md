STATUS: FAIL  
SUMMARY: 1 项 P3 文档不一致；未发现必须修改的运行时代码缺陷。  
TARGET: `653456fe38f5d3fb4d8947a3d62536a1af91e13e`，基线 `1bb19fa21`。结束时再次解析候选，SHA 未变。

FINDINGS:

- **[P3] [workbench/README.md:1462](/Users/luckye/Documents/Code/a2a/workbench/README.md:1462) — 停止语义未同步。** 候选 README 仍写“记 `daemon_stopping`；停止流程关库前会等还在进行的绑定收尾”。具体反例是本票的 30 秒读取场景：候选约 10 秒就关库，记录的是 `native_session_bind_abandoned`，之后不再补 `native_session_bind_failed`。代码及候选绿态均证实了这一行为。README 因本次变更而失真，违反 living doc 要与代码同步的规则。最小修正是说明“最多等待 10 秒、超时逐个记放弃、晚到结果不再记录”的分支，并完成地图核验。**这项需要修复，不要求改运行时代码。**

EVIDENCE:

- **10 秒作为正常情况下的等待预算合理，但理由需要说准确。**  
  [panes.ts:2626](/Users/luckye/Documents/Code/a2a/workbench/src/panes.ts:2626) 的 `readThread()` 对未停止窗格调用一次 `processInfo()`；后者在 [panes.ts:1418](/Users/luckye/Documents/Code/a2a/workbench/src/panes.ts:1418) 给进程查询设置了 5 秒 exec 超时。  
  不过，[core.ts:837](/Users/luckye/Documents/Code/a2a/workbench/src/gates/core.ts:837) 在拿锁失败后睡 100ms，再回到循环先读窗格。我的只读内存探针复现了“第一次读取 → 锁忙 → 等待期间开始停止 → 第二次读取 → 拒 `daemon_stopping`”：共读两次、只尝试拿锁一次、零次写绑定。因此票据第 21 行和 `daemon.ts` 注释中“只等手上这一次读取”不完全准确。正常情况下剩余工作可以是 **100ms 等待加下一次读取**；仍在 10 秒预算内，且已停止窗格会跳过进程查询。

- **赛跑、计时器和集合清理没有发现竞态。**  
  [daemon.ts:316](/Users/luckye/Documents/Code/a2a/workbench/src/daemon.ts:316) 的超时分支只 resolve；绑定分支的拒绝由现有 `.catch` 接住，记录失败时报告 stderr，用户输入观察器状态更新只改内存。正常生产路径下，两边都不会拒绝，两个结局都会执行 `clearTimeout(timer)`。  
  等待开始前，请求和恢复已收尾，受管窗格已终止，监听已关闭；未找到此后还能登记新绑定的生产调用路径。超时后遍历、设置 `abandoned`、写事件和关库之间没有 `await`，`.finally` 不能插入这段同步执行。双绑定探针得到恰好一条按时失败记录、一条超时放弃记录，最终集合为空。

- **放弃后不会晚写 `runtime_bound`。**  
  安全性来自 [core.ts:841](/Users/luckye/Documents/Code/a2a/workbench/src/gates/core.ts:841) 的停止检查，而不只是 `abandoned` 标记：读取返回后，先抛 `daemon_stopping`，再到操作锁、任务读取和保存。检查到保存之间没有异步让出点。因此，已放弃的绑定不能稍后成功写绑定；其 `.catch` 直接返回，`.finally` 删除登记对象。候选长读取场景也证实：关库后读取返回，stderr 为空，没有 `runtime_bound`，退出码为 0。

- **放弃记录写失败会使停止失败，这个选择可以接受。**  
  对 [daemon.ts:323](/Users/luckye/Documents/Code/a2a/workbench/src/daemon.ts:323) 注入事件写失败，内存探针观察到：计时器已清，`shutdown()` 抛错，尚未关库。外层随后设置退出码 1。  
  这与 T-253 普通拒绝记录失败时“报 `event_write_failed`、标观察器失败、继续服务”的处理不同，但没有把失败伪装成成功。这里要求先留下放弃记录才能关库；写不进去就停止清理，符合证据优先原则。无需为此增加吞错或重试。

- **没有发现门禁或锁语义被绕过。** 本次不改身份核对、操作锁或绑定重试规则，没有增加平行门禁入口、fallback 或重试。固定差异未触及 `REVIEW.md` 冻结的 `acceptance/**`；`git diff --check 1bb19fa21 653456fe3` 通过。

COUNTEREXAMPLE:

已核对作者生成的结果；四个新变异均因业务断言失败，没有把启动失败当作判红依据。我还核对了保留的变异源码副本，相关 `daemon.ts`、`gates/core.ts`、`panes.ts` 与候选加指定变异一致。

| 版本／变异 | 实际结果 |
| --- | --- |
| 修前 `1bb19fa21` | 30.004 秒才关库，没有放弃记录，新场景判红 |
| 候选 `653456fe3` | 9.994 秒关库；一条放弃记录，`waited_ms = 10001`；晚读取后无失败写入，退出 0 |
| `stop-wait-unbounded` | `stores_closed_within_bound` 等检查判红，30.005 秒才关库 |
| `abandon-unmarked` | 晚到拒绝尝试写已关数据库，出现 `event_write_failed`，检查判红 |
| `abandon-unrecorded` | `abandon_recorded` 判红 |
| `timer-kept` | 关库后又等待 8.040 秒，`exits_soon_after_close` 判红 |

候选证据见 [绿态摘要](/Users/luckye/Documents/Code/a2a/evidence/2026-11-08-batch34/T-254/green/shutdown-653456fe3.json)。T-253 单元回归 9 项通过；按候选运行的真实 Codex／脚本化 Responses API 回归也通过，旧 attempt 回收和重新派发成功。它们证明相关行为没有回归，不替代本票的超时场景。

LIMITATIONS:

- **上限是绑定等待阶段的预算，不是整个停止流程或进程退出的期限。** [daemon.ts:303](/Users/luckye/Documents/Code/a2a/workbench/src/daemon.ts:303) 起的请求排空、恢复、续跑收尾、窗格终止，以及后面的连接关闭，都先于计时器。它们若不返回，仍到不了本票的等待阶段；这是明确非目标。长读取夹具本身也让进程继续存活到约 30 秒，尽管库和 pid 文件已先清理。
- 5 秒 exec 超时不是整个 `readThread()` 的严格耗时保证：查询返回后还有同步解析、校验和扫描；本机 Node 的 exec 超时实现会发送终止信号，Promise 的结束仍依赖子进程收尾。**未证实真实进程查询会因此超过 10 秒**，也未发现本票需要修改它的证据。
- `processInfo()` 自身存在写观察事件的分支。若一个异常延迟的查询在关库后返回、且 `pane.leader` 仍为空，它可能尝试写 `pane_leader_observed`，随后被关闭的数据库拒绝，再由已放弃绑定的 `.catch` 吸收。**真实可达性未证实**；脚本化 `readThread()` 场景没有覆盖这一内部副作用，不能把它报告成已发生缺陷。
- 30 秒读取能充分区分 10 秒期限与无期限等待；15 秒关库阈值留了 5 秒调度余量，3 秒退出阈值能识别实测约 8 秒的残留计时器，当前未见抖动误判。测试只在最终检查 pid 文件已删，没有直接采样“第 20 秒 pid 仍在／第 15 秒前已删”；该时序还依赖关库时间线与关库后无 `await` 的清理代码佐证。
- 本次没有重新运行会写文件的后台测试，采用作者的固定候选产物，加只读内存探针核对。没有全量测试或真实厂商模型证据。
- 会话开始的地图检查报告 README stale；结束时工作区检查已为零。**后者不改变固定候选里的 README 内容，不能消除上面的 P3。**

**结论：需修复，仅需同步 README 的停止语义并完成文档核验；未发现必须修改的运行时代码问题。**