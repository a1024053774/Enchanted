# T-254 证据摘要（2026-11-08）

本地 main。修复提交 `653456fe3`；审查 01 之后的 `cbdade968` 只改注释、README、票据和一个变异的定位，产品源码与 `653456fe3` 只差注释（`git diff 653456fe3 cbdade968 -- workbench/src`）。父提交 `1bb19fa21`（T-253 收尾，已快进进本地 main）。需求见[票据](../../../.project-map/tickets/T-254-shutdown-binding-wait-bound.md)。来由：用户看到 T-253 没覆盖的“停止时等绑定没有超时”后，要求“这个应该设置一个合理的上限”。

## 改了什么

`workbench/src/daemon.ts`：

- 新常量 `BINDING_STOP_WAIT_MS = 10_000`。理由：停止开始后，门禁的 `nativeSessionLearned` 在下一次窗格读取之后就查到 `daemon_stopping` 并结束。正在读的，就是手上这一次；正在等锁的，还要再睡 100ms、读一次（审查 01 用只读探针复现了“读两次、拿锁一次、零次写入”，原写“只等手上这一次读取”不准确，已在 `cbdade968` 改正注释与票据）。真实读取里的进程查询（`panes.processInfo`）有 5 秒 exec 超时，10 秒是它的两倍。
- 每次绑定登记为一个对象：launch 记录、会话号、`abandoned` 标记、Promise。
- `shutdown()` 里原来的 `await Promise.all([...bindings])` 改成和 10 秒计时器赛跑，按时收尾就清掉计时器。到期时，把仍在进行的绑定标为放弃，并在关库前逐个记 `native_session_bind_abandoned`（会话号、实际等了多少毫秒），然后照常关库、删 pid 与套接字。
- 绑定的 `.catch` 在已放弃时直接返回，不再写已经关掉的库。attempt 保持未绑定，回收照旧拒绝。

README 那段绑定说明补了上限与放弃记录（`cbdade968`）；地图里 README 的核对点改为 `cbdade968`。

## 测试

后台层测试 `workbench/tests/test_t253_shutdown.py` + `t253_shutdown_host.ts`：真实 `serve()`、门禁、存储与私有 hc core，夹具窗格交给后台自己的回调，窗格读取是脚本化的；不起 CLI、PTY 子进程、钩子或模型。

新场景 `binding_outlives_stop`：停止开始后，窗格读取 30 秒才返回。读取用计时器等待，进程在它返回前不会自己退出，所以“关库后才收尾”这条路径会真的走到。期望来自票据：

| 检查 | 期望 |
| --- | --- |
| `stores_closed_within_bound` | 从窗格读取看到停止，到门禁关库，不超过 15 秒（10 秒上限加余量） |
| `abandon_recorded` | 恰好一条 `native_session_bind_abandoned`，会话号是夹具的，`waited_ms` 不少于 9900 |
| `late_read_ran_after_close` | 窗格读取在关库之后才返回（被放弃的绑定确实在关库后收尾） |
| `nothing_written_after_close` | 没有 `native_session_bind_failed`，stderr 没有 `event_write_failed` |
| `host_exit_zero`、`nothing_bound`、`stop_accepted` | 以 0 退出；门禁没有 `runtime_bound`；`daemon_stop` 被受理 |

三个场景都新加 `pid_removed`（`daemon.pid` 已删）；`stop_while_binding` 新加 `exits_soon_after_close`（关库后 3 秒内退出，即按时收尾时计时器已清）。

### 结果

| 运行 | 文件 | 结论 |
| --- | --- | --- |
| 修前 `1bb19fa21` | `red/shutdown-1bb19fa21.json` | FAIL：`binding_outlives_stop` 30.0 秒才关库，没有放弃记录，记了一条 `daemon_stopping` 拒绝；另两个场景通过 |
| 修后（工作区源码，提交前） | `green/shutdown-worktree.json` | PASS |
| 修后 `653456fe3` | `green/shutdown-653456fe3.json` | PASS：9.99 秒关库，`waited_ms` 约 10000；读取在关库后返回，没有再写；`stop_while_binding` 关库后 0.02 秒退出 |

变异（都在当前源码副本上打，见 `mutants/`）：

| 变异 | 改了什么 | 判红的检查 |
| --- | --- | --- |
| `stop-wait-unbounded` | 上限改成 600 秒 | `binding_outlives_stop`：30.0 秒才关库等 4 项 |
| `abandon-unmarked` | 到期不标放弃 | `nothing_written_after_close`（迟到的拒绝写进已关的库） |
| `abandon-unrecorded` | 到期不记放弃 | `abandon_recorded` |
| `timer-kept` | 不清计时器 | `stop_while_binding:exits_soon_after_close`（关库后 8.0 秒才退出） |
| `shutdown-skips-bindings`（T-253） | 不等绑定 | `stop_while_binding:bind_failure_recorded`；`binding_outlives_stop` 的放弃记录与“关库后不写” |
| `bind-record-unguarded`（T-253） | 拒绝记录写失败不接住 | `record_write_fails` 5 项（后台以 1 退出） |

`shutdown-skips-bindings` 原来定位的是 `await Promise.all([...bindings]);`，`653456fe3` 把这一行改掉后定位不到，第一次运行报“变异定位必须唯一”。提交后把它改为定位新的赛跑语句、换成 `const settled = true;`（只改测试文件），重跑后判红。

### 回归（按 `653456fe3`）

- T-253 门禁单元测试 `test_t253_native_bind.py`：PASS，9 项（`regression/t253-native-bind-653456fe3.json`）。
- T-252/T-253 端到端 `test_t252_untrusted_turn_other_cli_e2e.py --cli codex --launch dispatch`：PASS（`regression/t252-codex-dispatch-653456fe3.json`）。真实 Codex CLI 0.164.0，本地脚本化 Responses 接口，零次厂商模型调用。事件顺序 `dispatched`（会话为空）→ `runtime_bound`（`by: native_session_learned`），回收与再派成功，测试结束时后台正常停止。

## 审查

Codex `gpt-6.1-sol`，`model_reasoning_effort=high`，`codex exec -s read-only`，新开干净会话，固定候选 `653456fe3`。提示与结论在 `reviews/`；运行日志含账号信息，不入库。

审查 01（`reviews/review-01.md`）判 FAIL，只有一项 P3：候选里的 README 还写“停止流程关库前会等还在进行的绑定收尾”，没写上限与放弃记录。运行时代码没有必须修的。已在 `cbdade968` 修：README 写明 10 秒上限、到期记 `native_session_bind_abandoned`、之后收尾不写。

审查 01 记下、本票没改的几点：

- 上限理由不准确（见上文“改了什么”），已改注释与票据，数值不变。
- 放弃记录本身写失败时，`shutdown()` 抛错、库不关、后台以 1 退出。审查员判为可以接受：先留下放弃记录才关库，写不进去就不假装停好了。与 T-253 普通拒绝记录写失败时“报 `event_write_failed`、继续服务”不同。
- 上限只管等绑定这一段，不是整个停止流程的期限（见“没覆盖的地方”）。
- 5 秒 exec 超时不是整个 `readThread()` 的严格上限：查询返回后还有同步解析与校验；未证实会因此超过 10 秒。
- `processInfo()` 在 `pane.leader` 仍为空时可能写 `pane_leader_observed`；一次异常延迟、在关库后才返回的查询会被关闭的库拒绝，再由已放弃绑定的 `.catch` 吸收。真实可达性未证实，脚本化读取没覆盖。
- 测试只在最后检查 `daemon.pid` 已删，没有在第 20 秒采样；票据的红态条目已按实际量到的改写。

没有开复审：`cbdade968` 对 `653456fe3` 只改注释、文档、票据和测试里一个变异的定位，属于文档级改动，以 diff 为证。

## 没覆盖的地方

- 停止流程里其他没有期限的等待（请求排空、恢复、`resumedRunsSettled`、窗格终止）不在本票改。
- 被放弃的绑定让 attempt 保持未绑定，回收照旧拒 `identity_conflict`，与 T-253 没覆盖的“重启后恢复的窗格”同样处理；重启后补绑仍没有做。
- 真实 CLI 下“读取超过 10 秒”只有夹具证据：真实读取有 5 秒 exec 超时，正常情况下碰不到这个上限。
- 全量测试与真实厂商模型没跑；正在运行的 /Applications/Enchanted.app 未换版（当前没有在运行）。

## 重跑命令

在 `workbench/` 下：

```bash
python3 tests/test_t253_shutdown.py --revision 653456fe3 --summary /tmp/t254-shutdown.json
```

```bash
python3 tests/test_t253_native_bind.py --revision 653456fe3 --summary /tmp/t254-unit.json
```

```bash
python3 tests/test_t252_untrusted_turn_other_cli_e2e.py --cli codex --launch dispatch --revision 653456fe3 --summary /tmp/t254-e2e.json
```

`--revision 1bb19fa21` 是修复之前；`--mutant` 的取值见 `test_t253_shutdown.py` 的 `MUTANTS`。
