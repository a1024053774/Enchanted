# T-227 报告（主控在会话里写，2026-11-01）

基线 `03ba1cf54`（main），当前候选 [candidate.patch](candidate.patch)（第四轮），前三轮为 [candidate-round1.patch](candidate-round1.patch)、[candidate-round2.patch](candidate-round2.patch)、[candidate-round3.patch](candidate-round3.patch)。改在 main checkout 的工作区，未提交。T-228 已于第一轮之后提交（`10e4fcbfd`、`bbf8d5f80`），不碰这三个文件；候选相对 HEAD 与相对基线相同。

## 选定的规则（执行主控决定，缺陷级）

票里说“改法要先定”。两处都是实现层的选择，不改目标与验收，执行主控在 T-004 的自主范围内定，写进代码注释：

1. 初次打开项目终端时 trace 写入失败，算“没建成”：当场经 `closeShell` 关掉刚起的 hc 终端（杀进程、核对退出、记 `shell_closed`），再把原错误抛给调用者。用户本来就没拿到窗格，留着它只会在私有 core 里多一个看不见的终端。关闭本身也失败时，抛出同时含两个错误的 `AggregateError`。
2. 窗格写 trace 失败后，记为失败、只记一次，之后不再写这个窗格的 trace。项目终端、受管 worker 窗格、主控预设窗格、重启后接回的受管窗格用同一个 `appendTrace`。主控登录会话的 trace 边写边脱敏，写失败也同样停写、只记一次，事件名仍是 `controller_terminal_failed`。

## 改动

- `workbench/src/panes.ts`：`Pane.traceFailed`；新增 `appendTrace`；`startShell` 初次 attach 失败时关闭终端；shell 的 paint 与 data、受管窗格、主控预设窗格、接回窗格的 trace 写入都改走同一规则。
- `workbench/tests/test_pane_trace_failure.ts`（受管窗格，隔离注入）：失败后连送 5 帧，期望 `trace_write_failed` 只有 1 条、事件库只读时 `event_write_failed` 观察者只被调 1 次、失败不被后来的帧清掉。
- `workbench/tests/test_t212_trace_failure_e2e.py`（真实后台、私有 hc）：失败方式 6–9。resize 场景在注入前起一个 40×50 ms 的输出循环，失败后数事件；initial 场景用私有 core 的 `ls --all`（按 `shell_created` 记的地址）与 `ps` 核对终端已不在、shell 已退出，并核对 `shell_closed`。

## 运行

命令都在 `/Users/luckye/Documents/Code/a2a` 执行，hc 用例另加 `ENCHANTED_HC_CACHE_DIR=/Users/luckye/Documents/Code/a2a-worktrees/hc-cache TMPDIR=/private/tmp`：

```sh
node workbench/tests/test_pane_trace_failure.ts <dir>
python3 workbench/tests/test_t212_trace_failure_e2e.py --case resize|initial --output <dir>
python3 workbench/tests/test_t104_shell_e2e.py --archive /Volumes/WD-Elements/a2a-evidence/2026-10-31-batch29/T-227/t104-01 --summary <file>
/Applications/Xcode.app/Contents/Developer/usr/bin/python3 workbench/tests/test_t107_live_sidebar_e2e.py --summary <file>
```

| 运行 | 结果 |
| --- | --- |
| [修前 受管窗格](red-managed.log) | 退出 1：`5 !== 1`，trace 失败记 5 条；只读事件库时观察者被调 5 次 |
| [修前 resize](red-resize/run.json) | 退出 1：`trace_write_failed` 43 条 |
| [修前 initial](red-initial-02/run.json) | 退出 1：5 条；失败的终端 `t3` 仍 live，shell `Ss+` 仍在，没有 `shell_closed` |
| [修后 受管窗格](green-managed.log) | 退出 0 |
| [修后 resize](green-resize/run.json) | 退出 0：1 条，另一个终端照常可用，socket 仍在，后续请求明确拒绝不悬挂 |
| [修后 initial](green-initial/run.json) | 退出 0：1 条，终端不在 core 里，shell 已退出，记了 `shell_closed`；调用者收到 `pane_unavailable` |
| [变异：失败后仍重写 trace](mutant-retry-trace-resize/run.json)（[diff](mutant-retry-trace.diff)） | 退出 1：43 条 |
| [变异：初次失败不关终端](mutant-keep-terminal-initial/run.json)（[diff](mutant-keep-terminal.diff)） | 退出 1：终端仍在 core、shell 仍在、没有 `shell_closed` |
| [T104](t104.json) | PASS |
| [T107](t107.json) | PASS |

## 偏差与没做的

- 第一次 initial 红态（[red-initial-01-vacuous-core-check](red-initial-01-vacuous-core-check/run.json)）里，“终端不在 core 里”这项检查是空转的：测试按 labels 找终端，可 `hc ls` 的输出里没有 labels。用一次性私有 core 查明格式后，改成按 `shell_created` 记下的地址匹配，重跑红态时该项按预期失败。
- 第一次跑 T104 没给外置盘归档路径，被测试自己拒绝（[日志](t104-archive-path-refused.log)），换成 WD 路径后重跑。
- 票里“从侧栏点开它再关掉”那条路径不再适用：按选定规则，初次失败的终端不会留下。
- 主控登录会话（`login.observe`）的停写没有专门用例。

## 第二轮（GPT 审查 [REVIEW-01.md](REVIEW-01.md) 之后）

第一次启动的审查会话在等 stdin，12 分钟没有开始，主控停掉，日志留作 [review-01-stuck-stdin.session.log](review-01-stuck-stdin.session.log)；改为 `< /dev/null` 重开，就是 REVIEW-01。

审查结论 FAIL，三条 P2，主控逐条核对，都属实：

1. `native.jsonl` 直接 `appendFileSync`，绕过 `appendTrace`。主控实测：写它失败时，每次扫描都把同一批 native 行再记一遍（修前三次扫描记 6 条，应为 2 条）。改为经 `appendTrace`，规则写进 `appendTrace` 的注释：同一窗格的各个 trace（`pty.raw`、`native.jsonl`）共用一条规则。
2. 测试只证明失败事件去重，不证明停写。补两处检查：隔离测试在失败后把 trace 恢复可写，再送 3 帧，核对 trace 仍为 0 字节；e2e 的 resize 场景在失败后恢复权限，核对输出循环还在走（计数从 1 走到 40）而 trace 字节不变。用审查员给的反例做变异（[diff](mutant-record-once.diff)：失败后每帧仍去写，只是只记一次），两份测试都识别出来。
3. 关闭也失败时，`AggregateError` 的消息只带原错误。改为消息里同时带关闭失败的原因。没有专门用例。

| 运行 | 结果 |
| --- | --- |
| [修前 隔离（第二轮测试）](r2-red-managed.log) | 退出 1：native 场景 `6 !== 2`；另两个场景通过（候选本来停写） |
| [修后 隔离](r2-green-managed.log) | 退出 0 |
| [变异：只记一次、照写](r2-mutant-record-once-managed.log) | 退出 1：`75 !== 0`，失败后又写进 trace |
| [变异：只记一次、照写 resize](r2-mutant-record-once-resize/run.json) | 退出 1：`trace_not_written_after_failure` 失败，trace 从 1107 字节涨到 1814 字节 |
| [修后 resize](r2-green-resize/run.json)、[修后 initial](r2-green-initial/run.json) | 都退出 0；resize 恢复权限后计数 1→40，trace 保持 982 字节 |
| [T104](r2-t104.json)、[T107](r2-t107.json) | PASS |

偏差：

- 隔离测试的 native 场景前两版没测到东西，保留为 `r2-*-managed-01-hook-trigger-stale`、`r2-*-managed-02-undated-session-dir`：
  - 第一版用 hook 触发扫描。离线夹具里没有绑定的 native 会话，`noncurrentHook` 会拒掉 hook，扫描根本没跑。
  - 第二版把会话文件放在 `sessions/` 根目录，扫描只找日期目录，所以没找到这个文件。
  - 第三版改由 PTY 帧和 `launchInfo` 触发扫描，文件放进当天的日期目录。
- 范围外发现：`workbench/tests/test_native_final_read.ts` 在 HEAD 的 `panes.ts` 上也失败，8 个场景报 `hook_native_session_mismatch`（[日志](r2-native-final-read-HEAD.log)），原因同上面第一版。改动前后都这样，不是 T-227 引入的，需另开缺陷票。

## 第三轮（GPT 审查 [REVIEW-02.md](REVIEW-02.md) 之后）

审查确认 REVIEW-01 的三条已解决，另提一条 P2：受管窗格的回调在 trace 写失败后直接 `return`，之后每一帧的 native 扫描和 OSC 7501 报告（`reportedTurns`）都不再处理。基线逐帧处理：写失败只跳过这一帧，文件恢复可写后照常读取。主控核对属实，而且与 `appendTrace` 注释写的规则矛盾（“它所 trace 的流照常处理”）。

改法：写 trace 失败只停写 trace，调用处不再因此返回。改了三处：受管窗格（扫描、状态报告）、主控预设窗格、接回窗格（终端协议应答）。主控登录会话的 `login.observe` 失败后也不再返回。（这里原写“终端协议照常应答”，不对：失败窗格的写入一律被 `serializeWrite` 拒绝，应答发不出去，基线也如此，见第四轮。）规则写进 `appendTrace` 的注释。

隔离测试的 trace 场景补一项：失败之后 CLI 才写出会话日志，再来一帧，核对 native 记录被读到，会话已绑定。这一项代表回调后段的处理（扫描在前，`reportedTurns` 在扫描之后，同一个提前返回会跳过两者）。agy/opencode 的 OSC 报告本身没有专门用例。

| 运行 | 结果 |
| --- | --- |
| [修前 隔离（第三轮测试，第二轮代码）](r3-red-managed.log) | 退出 1：`later frames are still read after the trace stops`，`0 !== 2` |
| [修后 隔离](r3-green-managed.log) | 退出 0 |
| [变异：只记一次、照写](r3-mutant-record-once-managed.log) | 退出 1：`75 !== 0` |
| [修后 resize](r3-green-resize/run.json)、[修后 initial](r3-green-initial/run.json) | 都退出 0 |
| [T104](r3-t104.json)、[T107](r3-t107.json) | PASS |

以上运行都在冻结 `candidate.patch` 之前、同一工作区状态下完成，之后三个文件没有再改；run 记录里 `revision` 为 null，绑定靠这一顺序，不是靠记录本身。

## 第四轮（GPT 审查 [REVIEW-03.md](REVIEW-03.md) 之后）

审查确认前两轮的意见已解决，另提两条 P2，主控核对属实。两条是同一个问题：窗格失败后不再恢复，但之后每来一帧、每来一个查询，同一种失败都会再记一次。

1. trace 和事件库同时不可写时，每帧扫描都把没读完的会话日志记一次 `native_read_failed`，每次都再通知观察者“事件写入失败”。
2. 失败窗格收到终端协议查询时，应答被 `serializeWrite` 拒绝（`pane_unavailable`），每个查询都记一条 `terminal_protocol_failed`，并用它覆盖原来的失败原因。

基线在文件恢复可写后也会走到这两条路径，所以不是第三轮新引入的；第三轮去掉提前返回后，更容易走到。

改法：在 `recordFailure` 这一处统一实现票面的“同一窗格同一种失败只记一次”，规则写进注释。

- 每个窗格每种失败只记一次；
- `pane.failed` 保留第一个失败原因，后来的失败不覆盖（代码里没有任何地方清除 `pane.failed`，失败是终局）；
- 事件库写不进的告警，每个窗格只报一次。

隔离测试补两项：

- trace 场景在失败后送 3 个 `ESC[6n` 查询，核对 `terminal_protocol_failed` 只有 1 条、失败原因仍是 `trace_write_failed`；
- trace+events 场景在事件库只读前放一份没读过的会话日志，核对观察者只被调 1 次。

| 运行 | 结果 |
| --- | --- |
| [修前 隔离（第四轮测试，第三轮代码）](r4-red-managed.log) | 退出 1：trace 场景 `3 !== 1`；trace+events 场景观察者被调多次 |
| [修后 隔离](r4-green-managed.log) | 退出 0 |
| [修后 resize](r4-green-resize/run.json)、[修后 initial](r4-green-initial/run.json) | 都退出 0 |
| [T104](r4-t104.json)、[T107](r4-t107.json) | PASS |
| [单元测试对照](r4-unit-sweep/)（[脚本](unitsweep.sh)） | 50 个与窗格状态有关的单元测试，分别在 HEAD 与第四轮的 `panes.ts` 上跑：退出码逐个相同。但其中 32 个在两边都失败，多数是调用方式不对（有的参数要的是源码根目录而不是输出目录）或本来就过时；第一行错误信息的差异只在路径上。这项只能说明没有看到差异，不能当回归通过 |

第一次扫描用了 macOS 上没有的 `timeout` 命令，全部退出 127，作废，保留为 `r4-unit-sweep-invalid-no-timeout-cmd`。
