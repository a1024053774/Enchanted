# T-253 证据摘要（2026-11-08）

分支 `claude/dreamy-ptolemy-d0f2f0`，父提交 `faf1b0d7a`（T-252 收尾，已快进进本地 main）。两个代码提交：

- `cd69040d1`：方案 B 本身。包括 `panes.ts`、`daemon.ts`、`gates/core.ts`、README、两个新测试、T-252 端到端测试的补充，以及把票标为就绪。
- `b01096b84`：修审查 01 的 P2，即后台停止时还有绑定在进行。改 `daemon.ts`、`gates/core.ts` 和 README，加后台层测试 `test_t253_shutdown.py`，单元测试加两个停止时序和三个变异。

本目录顶层的结果都按 `b01096b84` 跑。`r2/` 是审查 01 审过的那一轮（`cd69040d1`），`r1/` 是提交 `cd69040d1` 之前在工作区上跑的一轮，见下文“前两轮”。

决定：用户选方案 B，原话“先合并,然后修法选 B”。用户在本会话的父会话“Worker 回收与派发问题”（`local_e9998522-d926-46a1-aac9-eda70d24d2b9`）里回答合并问题时说的，由该会话逐字转来。方案 B：后台得知 Codex 原生会话号时，就把它绑定到 attempt。

## 绑定时机

- **在哪一处得知会话号**：`panes.ts` 的 `scan()` 读到这个 worker 根 rollout 的首行 `session_meta`，窗格第一次记下会话号（`pane_native_session` 事件）。后台得知 Codex 会话号只有这一处。终端输出会触发 `scan()`，Codex 的钩子进 `signal` 后也先调 `scan()` 再核对钩子，所以“首个钩子”和“rollout 扫描”是同一个入口。只对 worker 窗格、只在第一次得知时调用；reviewer 不走这里，它们的身份在审查提交时另行核对。
- **在不在任务操作锁里写**：在锁里写。门禁新方法 `nativeSessionLearned` 的做法和 run 的 `observeRun` 相同：
  - 先在锁外读窗格（`readThread`）；
  - 读完后查一次后台是否在停，在停就不写（`daemon_stopping`）；
  - 再拿任务操作锁（`operationLock`，不等待）；
  - 在锁内重新读任务，确认这还是当前 attempt，用已有的 `bindObservedIdentity` 先核对身份（launch、thread、shell 进程、领导进程），再补空项；
  - 写 `runtime_bound`，并加上 `by: "native_session_learned"`，然后释放锁。

  拿锁和写入之间没有 await，所以从不持锁等待。锁被别的门禁命令占着时（例如开始这一回合的那次 `dispatch`），隔 100ms 重读窗格再试，不丢这次绑定。这与 run 在集成遇到 `operation_busy` 时的做法相同。下面三种情况就停：
  - 后台正在停（`daemon_stopping`），包括读窗格期间和等锁期间开始停的；
  - attempt 已被换掉（`stale_attempt`）；
  - 窗格身份与 attempt 记录不符（`identity_conflict`）。

  停下时，后台记一条 `native_session_bind_failed`，attempt 保持未绑定，回收照旧拒绝。
- **后台停止时**（`b01096b84`）：后台登记每次还在进行的绑定。停止流程在关掉门禁库和编排库之前等它们收尾，所以拒绝记录总能写进还开着的库。这条记录本身写不进去时，后台在 stderr 报 `event_write_failed`，并把用户输入记录标为失败，和 `panes.recordFailure` 处理窗格事件写失败的方式相同。
- **与 run 的 observeRun 是否重复绑定**：两处都只经 `bindObservedIdentity` 补空项，已绑定的值不会被覆盖。observeRun 只在 attempt 仍未绑定时才拿锁写。`regression/t252_codex_run.json` 里只有一次 `runtime_bound`，由 B 写下（`by: native_session_learned`）；run 之后读到的已是绑定状态，没有再写。两处都不持锁等待（单元检查 `lock_free_while_reading`，变异 `lock-across-read`），observeRun 那种拿不到锁就报错的写法不会因 B 撞锁失败。

## 测试

三个入口，期望都来自票据的验收条目、审查 01 的 P2 和门禁已有的身份规则，不取实现输出：

- **端到端**：`workbench/tests/test_t252_untrusted_turn_other_cli_e2e.py --cli codex --launch dispatch`。环境是真实编排后台与门禁，不开 Electron。真实 Codex CLI 0.164.0，模型换成本地脚本化 Responses 接口，零次厂商模型调用。执行主控用 `dispatch` 派出 Codex worker，回合中途进来一条来源不符的钩子，worker 的交付被拒，回合结束；然后回收旧 attempt，再给同一任务派新 worker。本票在这个测试里加了两样东西：回收前记下门禁的绑定事件和窗格的 `pane_native_session`（`observed.identity_binding`），以及变异 `t253-no-bind`。
- **门禁单元测试**：`workbench/tests/test_t253_native_bind.py`，它调用 `t253_native_bind.ts`。用测试运行时直接调真实的 `A2AGates`，不跑 CLI、PTY 或模型。任务记录按派发后的样子写入：领导进程已绑，原生会话为空，与 T-252 证据 `green/e2e-codex-dispatch-6159e7697.json` 一致。检查有 9 项：

| 检查 | 期望 |
| --- | --- |
| `binds_pane_session` | 补上窗格的会话号，领导进程不变，一条 `runtime_bound` |
| `lock_free_while_reading` | 读窗格时任务操作锁是空的 |
| `second_call_changes_nothing` | 第二次调用不再写，值不变 |
| `other_launch_refused` | 别的 launch：拒 `identity_conflict`，attempt 不变，回收仍拒 `identity_conflict` |
| `other_shell_refused` | 别的 shell 进程：同上 |
| `replaced_attempt_refused` | attempt 已换掉：拒 `stale_attempt`，什么都不写 |
| `waits_for_busy_lock` | 锁被占着时不写，锁一放开就补上 |
| `stop_during_read_refused` | 读窗格期间后台开始停：拒 `daemon_stopping`，什么都不写 |
| `stop_while_waiting_refused` | 等锁期间后台开始停：拒 `daemon_stopping`，锁放开后也不写 |

- **后台层测试**（`b01096b84` 新增）：`workbench/tests/test_t253_shutdown.py`，它调用 `t253_shutdown_host.ts`。起真实的编排后台（`serve()`、门禁、两个库、私有 hc core），把一个夹具窗格交给后台自己的“窗格得知会话号”回调；窗格读取是脚本化的，不起 CLI、PTY 子进程、钩子或模型。两个场景：

| 场景 | 做法 | 期望 |
| --- | --- | --- |
| `stop_while_binding` | 绑定正在读窗格时发 `daemon_stop`。窗格读取等到门禁关库，最多等 2 秒 | 停止被受理；后台以 0 退出；记一条 `native_session_bind_failed`（`daemon_stopping`）；门禁没有 `runtime_bound` |
| `record_write_fails` | 绑定被拒，而这条拒绝记录写不进去（夹具让这一类事件的写入抛错） | 后台不退出；stderr 有这个 launch 的 `event_write_failed`；之后照常停止并以 0 退出 |

## 修前红态

- `red/e2e-codex-dispatch-faf1b0d7a.json`（`--revision faf1b0d7a`，上一轮跑的，端到端测试此后没改）：FAIL，只有 `old_attempt_reclaimed`、`new_worker_dispatched` 两项失败，前提和 Stop 那几项都过。门禁事件只有 `dispatched`，记录的 `native_session` 为空；窗格之后记下了 `pane_native_session`，但没有任何 `runtime_bound`。回收被拒 `identity_conflict`，再派被拒 `already_claimed`。
- `red/unit-native-bind-faf1b0d7a.json`：FAIL，修前门禁没有这个方法（`gates.nativeSessionLearned is not a function`）。它只说明接口不存在；业务上的红态是上面的端到端结果。
- 审查 01 的 P2，在 `cd69040d1` 上复现：
  - `red/unit-native-bind-cd69040d1.json`：只有 `stop_during_read_refused` 失败。读窗格期间后台开始停，读完仍写下了绑定。`stop_while_waiting_refused` 在这一版也通过，因为循环开头已有停止检查。
  - `red/daemon-shutdown-cd69040d1.json`：两个场景都失败，后台都以 1 退出。
    - `stop_while_binding`：门禁先关了库，窗格读取才返回。绑定再去读任务，拒绝记录写进已关的编排库，抛 `ERR_INVALID_STATE: database is not open`（`daemon.ts:94`）。这个拒绝没有接收者，进程以 1 退出，也没有留下 `native_session_bind_failed`。
    - `record_write_fails`：拒绝记录写失败后，错误在 `.catch` 里再次抛出，后台随即退出，没有报 `event_write_failed`。

## 修后绿态（`--revision b01096b84`）

- `green/e2e-codex-dispatch.json`：PASS，8 项全过（前提 1 项加检查 7 项）。事件顺序：`dispatched`（06:20:49.898Z，会话为空）→ 窗格 `pane_native_session`（50.717Z）→ `runtime_bound`（50.781Z，`by: native_session_learned`，会话号与窗格记下的相同）。回收成功，再派成功。
- `green/unit-native-bind.json`：PASS，9 项全过。
- `green/daemon-shutdown.json`：PASS，两个场景都过。
  - `stop_while_binding`：窗格读取等满 2 秒才返回，门禁这时还没关库；绑定读完后拒 `daemon_stopping`，记录写在 `daemon_stopped` 之后，然后门禁关库，后台以 0 退出。
  - `record_write_fails`：stderr 有一行 `event_write_failed`，原因写明原拒绝是 `unknown_task`（夹具窗格不对应任何任务）。后台 1 秒后仍在运行，之后照常停止并以 0 退出。

## 变异

| 变异 | 改了什么 | 结果 |
| --- | --- | --- |
| `t253-no-bind`（端到端） | 窗格得知会话号后不调绑定 | `mutants/e2e-codex-dispatch-t253-no-bind.json` FAIL：没有 `runtime_bound`，回收 `identity_conflict`，再派 `already_claimed` |
| `bind-skips-identity-check` | 绑定时跳过身份核对，直接写窗格的会话号 | `mutants/unit-bind-skips-identity-check.json` FAIL：`other_launch_refused`、`other_shell_refused`（别人的会话号被写进 attempt）、`second_call_changes_nothing` |
| `busy-not-waited` | 锁被占着就放弃 | `mutants/unit-busy-not-waited.json` FAIL：`waits_for_busy_lock`（锁放开后会话号仍为空）、`stop_while_waiting_refused` |
| `lock-across-read` | 先拿锁再读窗格 | `mutants/unit-lock-across-read.json` FAIL：`lock_free_while_reading`、`stop_during_read_refused` |
| `stop-not-rechecked` | 读完窗格后不查停止 | `mutants/unit-stop-not-rechecked.json` FAIL：`stop_during_read_refused`、`stop_while_waiting_refused`（锁放开后照样写下绑定） |
| `shutdown-skips-bindings` | 停止流程不等还在进行的绑定 | `mutants/daemon-shutdown-skips-bindings.json` FAIL：`stop_while_binding` 没有留下 `native_session_bind_failed`（写进已关的库，被报为 `event_write_failed`） |
| `bind-record-unguarded` | 拒绝记录写失败时不接住 | `mutants/daemon-bind-record-unguarded.json` FAIL：`record_write_fails` 里后台以 1 退出 |

## 回归（`--revision b01096b84`）

摘要在 `regression/`：

- T-170（启动失败的回收）：`t170_failed.json`、`t170_fast.json`、`t170_hang.json` 都 PASS。hang 场景里原生会话为空、CLI 还在跑，回收照旧拒 `identity_conflict`。
- T-252：`t252_codex_run.json`（Codex 经 run 派出，见上文“绑定时机”：窗格 12.553Z 得知会话号，B 在 12.619Z 写下唯一一条 `runtime_bound`）、`t252_agy.json`、`t252_opencode.json` 都 PASS。agy、opencode 的会话号在派发时就有（`osc7501:…`），不走这条绑定。
- T-127：`t127_codex_home.json` PASS（Codex worker 可信回合，正常交付、审查、集成）。第一次运行 `t127_codex_home-env-hc-download.json` 是 INCOMPLETE，摘要里只有 `daemon_start` 失败（后台以 1 退出）。这个测试只给后台传 `PATH`、`LANG`、`TMPDIR`，所以每次都从 `releases.herdr.dev` 下载 hc。删夹具前我看过它的 `daemon.stderr.log`：下载时连接被重置（`ECONNRESET`，TLS 握手前断开）。这份 stderr 没有存档，所以这个归因只有我当时的读数，复审 02 记为未证实。同一命令重跑通过；第一次的结果没有算作 PASS。
- `native_final_read.json`：9 个场景都没有失败（窗格退出时最后一次读 rollout）。这个测试不收 `--revision`，是在工作区源码上跑的，当时工作区代码与 `b01096b84` 相同（`git status` 只有证据目录的改动）。
- `startup_shutdown-stale-host.json`：`test_startup_shutdown_e2e.py` 的 4 个用例都没跑起来。它的宿主 `startup_shutdown_host.ts` 不建操作者凭据，后台 `serve()` 一启动就拒 `operator_credential_required`。这个要求是 T-078-1（2026-10-11）加的，宿主从那以后没改过，与本票无关，不计入回归。停止流程这次的改动由 `test_t253_shutdown.py` 和上面各端到端测试结尾的 `daemon_stop` 覆盖。
- 没跑：全量测试；`relay_scope`（T-251 记录它在父提交上已有 4 项失败，本票没改中继）；真实厂商模型。

## 前两轮

### 第二轮（`r2/`，`cd69040d1`，审查 01 所审）

修复提交 `cd69040d1` 之后、审查 01 之前，按这个提交号跑的全部结果，原样移进 `r2/`。端到端的修前红态（`faf1b0d7a`）两轮共用，移到了顶层 `red/`。审查 01 在这一轮上判 FAIL，见下文“审查”。

### 第一轮（`r1/`）

提交 `cd69040d1` 之前，在工作区源码上跑过一轮，结论与第二轮相同。这一轮的摘要都保留在 `r1/` 里，有三点要说明：

- `r1/red/e2e-codex-dispatch-env-spawn-helper.json`：后台没起来。`npm ci` 装出来的 node-pty `prebuilds/darwin-arm64/spawn-helper` 没有执行位，这是 README 第 710 行记过的已知问题。按 README 改成 755 后重跑。这是环境问题，不是产品红态。
- `r1/*/unit-native-bind-fixture-unregistered.json`：单元测试夹具一开始没登记任务卡，回收停在 `task_card_registration_required`，没走到身份核对。补上任务卡快照与集成引用后重跑。这是测试夹具问题。
- 文件名带 `-r1` 的三份端到端摘要，是加 `observed.identity_binding` 之前跑的；不带 `-r1` 的是加了之后跑的。这一轮之后，我给 B 的 `runtime_bound` 加了 `by` 字段，用来分清它和 run 的观察，然后提交 `cd69040d1`。

## 设计自查（design-integrity，实现者自查）

- **复用已有做法，不另开接口**：核对与写入复用 `bindObservedIdentity`、`operationLock`、`save`，没有新的门禁命令或对外接口。新方法只由后台在窗格得知会话号时调用。
- **不放宽身份核对**：`checkThread` 的规则不变，回收要求的绑定条件也不变；身份不符照旧拒绝，T-170 的例外也没动。
- **三处异常处理**：
  - `core.ts` 只接 `operation_busy`，别的错误照样抛出。实际会碰到：开始这一回合的 `dispatch` 在等待时一直持锁。
  - `daemon.ts` 的 `.catch` 只记 `native_session_bind_failed`，不补救；attempt 保持未绑定，回收照旧拒绝，是安全的一侧。写法和 `resumeRuns` 已有的 `.catch` 一样。
  - `b01096b84` 在这条记录外面加了 try/catch，接住记录本身写失败的情况：报 `event_write_failed`，并把用户输入记录标为失败。没有它，这个错误会成为未处理的 Promise 拒绝，后台直接退出（红态 `record_write_fails`）。处理方式照搬 `panes.recordFailure`，不重试，也不吞掉。
- **停止流程多等一步**：`b01096b84` 让停止流程在关库前等登记过的绑定。等待有界：两个服务都关了以后，不会再有窗格或连接开始新的绑定；还在等锁的绑定，最迟在下一次重试（100ms 内）读完窗格后拒 `daemon_stopping`。
- **等锁没有上限**：后台没在停、锁又一直被占着时，每隔 100ms 读一次窗格，直到绑定成功或被拒绝。这和 run 跟随任务时每 100ms 读一次窗格的频率相同。

## 没覆盖的地方

- **后台重启**：重启后恢复的 Codex worker 窗格，会话号来自之前记下的 `pane_native_session`，不会再“第一次得知”，B 不会调用。两种 attempt 仍会像修前那样回收不了：
  - 后台在“窗格得知”与“绑定写入”之间停掉的（包括 `b01096b84` 在停止时拒 `daemon_stopping` 的那些）；
  - 本修复之前派出、还没绑定的。

  run 的 `observeRun` 只能补仍在运行、能过它前置检查的窗格。已经停止的恢复窗格，在任务仍是 `claimed` 时会先被拒 `run_external_unknown`，不会补绑（审查 01 P3 的探针结果）。本票不扩展恢复方案。
- 后台层测试里的窗格是夹具对象，窗格读取是脚本化的；真实 CLI 下“停止时有绑定在进行”的时序没有端到端证据。
- 停止流程等绑定用的 `Promise.all` 没有超时。窗格读取永远不返回时，停止就会一直等。目前没有证据表明真实的窗格读取会这样：已停止的窗格直接返回记下的事实，进程查询有 5 秒超时。夹具里的 2 秒只用来区分修前修后，不代表真实停止耗时。
- 后台层测试的 `record_write_fails` 断言了 stderr 和后台存活，没有直接断言用户输入记录被标为失败；这一点由复审 02 的内存探针补查。
- 票里写的“没交付就结束回合”没有单独跑，只跑了“交付被拒”。绑定发生在窗格得知会话号时，与之后交不交付无关。

## 审查

Codex `gpt-6.1-sol`，`model_reasoning_effort=high`，`codex exec -s read-only`，每轮新开干净会话。提示与结论在 `reviews/`；运行日志含账号信息，不入库。

- **审查 01**（`reviews/review-01.md`，固定候选 `dbde5eeb4`，即 `r2/` 那一轮）：FAIL，需修复。
  - **P2**：还在进行的绑定没有纳入停止流程。审查员在内存探针里复现了两个时序：
    - 等锁期间停止：库关掉后，拒绝记录写进已关的库，抛 `ERR_INVALID_STATE`，成为未处理的 Promise 拒绝，Node 默认以 1 退出；
    - 读窗格期间停止：读完后仍写下绑定。

    我先用真实后台复现了这两点（见“修前红态”里 `cd69040d1` 的两份结果），再在 `b01096b84` 修：
    - 登记还在进行的绑定，停止流程在关库前等它们；
    - 读完窗格后查一次停止；
    - 拒绝记录写失败时，照 `panes.recordFailure` 报 `event_write_failed`。

    新增的两个单元时序和后台层两个场景各有对应的变异。
  - **P3**：原 RESULTS 写“经 run 跟随的 attempt 仍由 observeRun 补绑”，说宽了：已停止的恢复窗格会先被拒 `run_external_unknown`。已在“没覆盖的地方”改为只限仍在运行、能过前置检查的窗格。
  - 没有发现跨 attempt 误绑定。审查员的独立探针显示：别的 launch、thread、shell、领导进程都拒 `identity_conflict`；attempt、fence、规格版本不符都拒 `stale_attempt`；连扫五次只回调一次；reviewer、辅助 rollout 不触发。
- **审查 02**（`reviews/review-02.md`，固定候选 `8fad54c0d`，最后一轮）：PASS，可合并，没有必须修的。
  - P2 已修：读窗格期间停止时，修前写 1 次、修后写 0 次；绑定没收尾时库保持打开，先记拒绝再关库；Set 登记与清理没有问题，也没找到停止流程取快照之后还能登记绑定的时序。
  - P3 的说明已收窄；`test_startup_shutdown_e2e.py` 判为与本票无关有依据。
  - 记为限制或未证实的有三点，已写进“没覆盖的地方”和上文“回归”：`Promise.all` 没有超时；后台层测试没直接断言用户输入记录被标为失败；T-127 第一次失败的网络归因没有存档的 stderr。

  按约定不再开第三轮。

## 重跑命令

在 `workbench/tests` 下：

```bash
ENCHANTED_HC_CACHE_DIR=/Users/luckye/Documents/Code/hc-cache python3 test_t252_untrusted_turn_other_cli_e2e.py --cli codex --launch dispatch --revision b01096b84 --summary /tmp/t253-e2e.json
```

```bash
python3 test_t253_native_bind.py --revision b01096b84 --summary /tmp/t253-unit.json
```

```bash
ENCHANTED_HC_CACHE_DIR=/Users/luckye/Documents/Code/hc-cache python3 test_t253_shutdown.py --revision b01096b84 --summary /tmp/t253-daemon.json
```

`--revision faf1b0d7a` 是 B 之前，`--revision cd69040d1` 是 P2 修复之前；`--mutant` 的取值见各测试的 `MUTANTS`。回归命令同 T-252、T-170、T-127 的测试，加 `--revision b01096b84`。

## 夹具状态

`fixtures-status.json` 记下了每次运行的夹具目录、是否保留、字节数、文件数和结果，共 126 条：前两轮 55 条，本轮 71 条（带 `round: b01096b84`）。本轮有 56 个目录在记录时还在，共约 139 MB，记下状态后都已删除。这些目录包括：
- 失败的运行（红态与变异）留下的夹具；
- T-170、T-127 通过后也会保留的夹具；
- 提交前在草稿区的探索运行；
- `test_startup_shutdown_e2e.py` 起不来留下的 4 个夹具；
- 9 个 2026-11-07 的 `native_final_read` 遗留目录。

仓库里只留本目录的文本摘要。
