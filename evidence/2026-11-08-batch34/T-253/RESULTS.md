# T-253 证据摘要（2026-11-08）

分支 `claude/dreamy-ptolemy-d0f2f0`，父提交 `faf1b0d7a`（T-252 收尾，已快进进本地 main）。修复提交 `cd69040d1`，包括 `panes.ts`、`daemon.ts`、`gates/core.ts`、README、两个新测试、T-252 端到端测试的补充，以及把票标为就绪。

决定：用户选方案 B，原话“先合并,然后修法选 B”。用户在本会话的父会话“Worker 回收与派发问题”（`local_e9998522-d926-46a1-aac9-eda70d24d2b9`）里回答合并问题时说的，由该会话逐字转来。方案 B：后台得知 Codex 原生会话号时，就把它绑定到 attempt。

## 绑定时机

- **在哪一处得知会话号**：`panes.ts` 的 `scan()` 读到这个 worker 根 rollout 的首行 `session_meta`，窗格第一次记下会话号（`pane_native_session` 事件）。后台得知 Codex 会话号只有这一处。终端输出会触发 `scan()`，Codex 的钩子进 `signal` 后也先调 `scan()` 再核对钩子，所以“首个钩子”和“rollout 扫描”是同一个入口。只对 worker 窗格、只在第一次得知时调用；reviewer 不走这里，它们的身份在审查提交时另行核对。
- **在不在任务操作锁里写**：在锁里写。门禁新方法 `nativeSessionLearned` 的做法和 run 的 `observeRun` 相同：
  - 先在锁外读窗格（`readThread`）；
  - 再拿任务操作锁（`operationLock`，不等待）；
  - 在锁内重新读任务，确认这还是当前 attempt，用已有的 `bindObservedIdentity` 先核对身份（launch、thread、shell 进程、领导进程），再补空项；
  - 写 `runtime_bound`，并加上 `by: "native_session_learned"`，然后释放锁。

  拿锁和写入之间没有 await，所以从不持锁等待。锁被别的门禁命令占着时（例如开始这一回合的那次 `dispatch`），隔 100ms 重读窗格再试，不丢这次绑定。这与 run 在集成遇到 `operation_busy` 时的做法相同。下面三种情况就停：
  - 后台正在停（`daemon_stopping`）；
  - attempt 已被换掉（`stale_attempt`）；
  - 窗格身份与 attempt 记录不符（`identity_conflict`）。

  停下时，后台记一条 `native_session_bind_failed`，attempt 保持未绑定，回收照旧拒绝。
- **与 run 的 observeRun 是否重复绑定**：两处都只经 `bindObservedIdentity` 补空项，已绑定的值不会被覆盖。observeRun 只在 attempt 仍未绑定时才拿锁写。`regression/t252_codex_run.json` 里只有一次 `runtime_bound`：B 在窗格得知会话号后约 60ms 写下，带 `by: native_session_learned`；run 之后读到的已是绑定状态，没有再写。两处都不持锁等待（单元检查 `lock_free_while_reading`，变异 `lock-across-read`），observeRun 那种拿不到锁就报错的写法不会因 B 撞锁失败。

## 测试

两个入口，期望都来自票据的验收条目和门禁已有的身份规则，不取实现输出：

- **端到端**：`workbench/tests/test_t252_untrusted_turn_other_cli_e2e.py --cli codex --launch dispatch`。环境是真实编排后台与门禁，不开 Electron。真实 Codex CLI 0.164.0，模型换成本地脚本化 Responses 接口，零次厂商模型调用。执行主控用 `dispatch` 派出 Codex worker，回合中途进来一条来源不符的钩子，worker 的交付被拒，回合结束；然后回收旧 attempt，再给同一任务派新 worker。本票在这个测试里加了两样东西：回收前记下门禁的绑定事件和窗格的 `pane_native_session`（`observed.identity_binding`），以及变异 `t253-no-bind`。
- **门禁单元测试**：`workbench/tests/test_t253_native_bind.py`，它调用 `t253_native_bind.ts`。用测试运行时直接调真实的 `A2AGates`，不跑 CLI、PTY 或模型。任务记录按派发后的样子写入：领导进程已绑，原生会话为空，与 T-252 证据 `green/e2e-codex-dispatch-6159e7697.json` 一致。检查有 7 项：

| 检查 | 期望 |
| --- | --- |
| `binds_pane_session` | 补上窗格的会话号，领导进程不变，一条 `runtime_bound` |
| `lock_free_while_reading` | 读窗格时任务操作锁是空的 |
| `second_call_changes_nothing` | 第二次调用不再写，值不变 |
| `other_launch_refused` | 别的 launch：拒 `identity_conflict`，attempt 不变，回收仍拒 `identity_conflict` |
| `other_shell_refused` | 别的 shell 进程：同上 |
| `replaced_attempt_refused` | attempt 已换掉：拒 `stale_attempt`，什么都不写 |
| `waits_for_busy_lock` | 锁被占着时不写，锁一放开就补上 |

## 修前红态（`--revision faf1b0d7a`）

- `red/e2e-codex-dispatch.json`：FAIL，只有 `old_attempt_reclaimed`、`new_worker_dispatched` 两项失败，前提和 Stop 那几项都过。门禁事件只有 `dispatched`，记录的 `native_session` 为空；窗格之后记下了 `pane_native_session`，但没有任何 `runtime_bound`。回收被拒 `identity_conflict`，再派被拒 `already_claimed`。
- `red/unit-native-bind.json`：FAIL，修前门禁没有这个方法（`gates.nativeSessionLearned is not a function`）。

## 修后绿态（`--revision cd69040d1`）

- `green/e2e-codex-dispatch.json`：PASS，8 项全过（前提 1 项加检查 7 项）。事件顺序：`dispatched`（05:54:11.988Z，会话为空）→ 窗格 `pane_native_session`（12.591Z）→ `runtime_bound`（12.681Z，`by: native_session_learned`，会话号与窗格记下的相同）。回收成功，再派成功。
- `green/unit-native-bind.json`：PASS，7 项全过。锁被占着的 400ms 里，读了 4 次窗格，什么都没写；锁放开后补上。

## 变异

| 变异 | 改了什么 | 结果 |
| --- | --- | --- |
| `t253-no-bind`（端到端） | 窗格得知会话号后不调绑定 | `mutants/e2e-codex-dispatch-t253-no-bind.json` FAIL：没有 `runtime_bound`，回收 `identity_conflict`，再派 `already_claimed` |
| `bind-skips-identity-check` | 绑定时跳过身份核对，直接写窗格的会话号 | `mutants/unit-bind-skips-identity-check.json` FAIL：`other_launch_refused`、`other_shell_refused`（别人的会话号被写进 attempt）、`second_call_changes_nothing` |
| `busy-not-waited` | 锁被占着就放弃 | `mutants/unit-busy-not-waited.json` FAIL：`waits_for_busy_lock`（锁放开后会话号仍为空） |
| `lock-across-read` | 先拿锁再读窗格 | `mutants/unit-lock-across-read.json` FAIL：`lock_free_while_reading` |

## 回归（`--revision cd69040d1`）

摘要在 `regression/`：

- T-170（启动失败的回收）：`t170_failed.json`、`t170_fast.json`、`t170_hang.json` 都 PASS。hang 场景里原生会话为空、CLI 还在跑，回收照旧拒 `identity_conflict`。
- T-252：`t252_codex_run.json`（Codex 经 run 派出，见上文“绑定时机”）、`t252_agy.json`、`t252_opencode.json` 都 PASS。agy、opencode 的会话号在派发时就有（`osc7501:…`），不走这条绑定。
- T-127：`t127_codex_home.json` PASS（Codex worker 可信回合，正常交付、审查、集成）。
- `native_final_read.json`：9 个场景都没有失败（窗格退出时最后一次读 rollout）。这个测试不收 `--revision`，是在工作区源码上跑的，当时工作区与 `cd69040d1` 相同。
- 没跑：全量测试；`relay_scope`（T-251 记录它在父提交上已有 4 项失败，本票没改中继）；真实厂商模型。

## 第一轮（`r1/`）

提交之前，在工作区源码上跑过一轮，结论与上文相同。这一轮的摘要都保留在 `r1/` 里，有三点要说明：

- `r1/red/e2e-codex-dispatch-env-spawn-helper.json`：后台没起来。`npm ci` 装出来的 node-pty `prebuilds/darwin-arm64/spawn-helper` 没有执行位，这是 README 第 710 行记过的已知问题。按 README 改成 755 后重跑。这是环境问题，不是产品红态。
- `r1/*/unit-native-bind-fixture-unregistered.json`：单元测试夹具一开始没登记任务卡，回收停在 `task_card_registration_required`，没走到身份核对。补上任务卡快照与集成引用后重跑。这是测试夹具问题。
- 文件名带 `-r1` 的三份端到端摘要，是加 `observed.identity_binding` 之前跑的；不带 `-r1` 的是加了之后跑的。这一轮之后，我给 B 的 `runtime_bound` 加了 `by` 字段，用来分清它和 run 的观察，然后提交，再按提交号重跑了上文全部结果。

## 设计自查（design-integrity，实现者自查）

- **复用已有做法，不另开接口**：核对与写入复用 `bindObservedIdentity`、`operationLock`、`save`，没有新的门禁命令或对外接口。新方法只由后台在窗格得知会话号时调用。
- **不放宽身份核对**：`checkThread` 的规则不变，回收要求的绑定条件也不变；身份不符照旧拒绝，T-170 的例外也没动。
- **两处异常处理**：
  - `core.ts` 只接 `operation_busy`，别的错误照样抛出。实际会碰到：开始这一回合的 `dispatch` 在等待时一直持锁。
  - `daemon.ts` 的 `.catch` 只记 `native_session_bind_failed`，不补救；attempt 保持未绑定，回收照旧拒绝，是安全的一侧。写法和 `resumeRuns` 已有的 `.catch` 一样。
- **等锁没有上限**：只要锁被占着，每隔 100ms 读一次窗格，直到绑定成功、被拒绝或后台停止。这和 run 跟随任务时每 100ms 读一次窗格的频率相同。

## 没覆盖的地方

- **后台重启**：重启后恢复的 Codex worker 窗格，会话号来自之前记下的 `pane_native_session`，不会再“第一次得知”，B 不会调用。两种 attempt 仍会像修前那样回收不了：
  - 后台在“窗格得知”与“绑定写入”之间停掉的；
  - 本修复之前派出、还没绑定的。

  经 run 跟随的 attempt 仍由 observeRun 补绑。
- `daemon.ts` 记录 `native_session_bind_failed` 这条路径没有端到端证据；门禁那一侧的拒绝由单元测试覆盖。
- 票里写的“没交付就结束回合”没有单独跑，只跑了“交付被拒”。绑定发生在窗格得知会话号时，与之后交不交付无关。

## 审查

（待补）

## 重跑命令

在 `workbench/tests` 下：

```bash
ENCHANTED_HC_CACHE_DIR=/Users/luckye/Documents/Code/hc-cache python3 test_t252_untrusted_turn_other_cli_e2e.py --cli codex --launch dispatch --revision cd69040d1 --summary /tmp/t253-e2e.json
```

```bash
python3 test_t253_native_bind.py --revision cd69040d1 --summary /tmp/t253-unit.json
```

`--revision faf1b0d7a` 是修前；`--mutant` 的取值见各测试的 `MUTANTS`。回归命令同 T-252、T-170、T-127 的测试，加 `--revision cd69040d1`。

## 夹具状态

`fixtures-status.json` 记下了每次运行的夹具目录、是否保留、字节数、文件数和结果，共 55 条。其中 43 个运行留下了夹具（失败的运行，以及 T-170、T-127 通过后也会保留夹具），共约 230 MB，记下状态后都已删除。`native_final_read` 的 9 个场景目录也已删除。仓库里只留本目录的文本摘要。
