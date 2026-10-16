# T-085 独立审查报告

审查对象：冻结候选 `e059da18c0d579b1d9da415b33e67bd840e109e0`，起点 `6ba3bde4174d8e0fc6db65a70a1216fd05c2cdac`。审查只读候选及其外部运行证据；未修改候选、未提交、未调用真实模型。

## 结论

**PASS**。候选满足 T-085 的恢复、配置来源、操作锁和受控审查完成条件。独立变异中有两枚有效错误实现被目标用例拒绝；作者的空配置变异虽在配置比对断言处停止，但这正是本票据要求的“同一份启动配置”断言，足以证明完成条件拒绝该错误实现。另有两枚审查脚本变异因生成了语法错误的副本，未计入有效变异数量，详见限制。

## 1. 改动范围和断言纪律

候选相对起点只改 `workbench/tests/test_daemon_recovery_e2e.py` 以及 T-085 证据文件；`git diff --name-status 6ba3bde4..e059da18c` 未显示 `workbench/src/`，`git diff --check` 无输出。测试没有删除或放宽原有中断、操作锁、孤儿 oracle、Git/CAS 和状态断言，也没有跳过第二次 `verify`。新增的断言在测试文件第 154–171 行核对重启 ready 记录、配置来源、配置 JSON、PID 和 state root；第 167–169 行要求来源路径和内容都与中断前相等。

目标测试仍以真实 gate CLI 启动 verify（第 45–50 行），通过 socket、SQLite、Git 和 `/bin/ps` 观察 daemon。新增 `host_stdout`/`host_stderr` 关闭只用于清理已等待的受控宿主，不改变业务判定。

## 2. 红态、绿态和重启配置

- 红态：`red-05/run.json` 为 `INCOMPLETE`，5 个用例中 4 个通过、0 个 errors，唯一失败是 `test_daemon_verify_interruption_and_operation_lock`。其第二次 verify 的 CLI 回执为 `{"ok":false,"error":"review_launch_config_required"...}`，与票据缺审查配置的故障一致。证据见 `red-05/run.json` 和 `RESULTS.md` 红态段。
- 绿态：`green-03/run.json` 为 `PASS`，`tests_run=5`、`failures=0`、`errors=0`；`outside-run-03.log` 记录五案均 `ok`。
- 配置来源：`green-03/artifacts.tar.gz` 中的 `restart-launch-config.json` 五份记录均为 `equal: true`，`before.source` 与 `after.source` 是同一规范化 `quality-control/config.json`，重启 argv 最后一个参数也是该目录。配置包含 8 个受控 reviewer 项，来源来自测试夹具文件而非产品常量。
- 完成状态：同一 artifact 的 `verify-complete.json` 为 `task.state=verified`、`verification.state=passed`、`review.state=passed`；`quality-control/driver.jsonl` 记录了经真实 gate CLI 的 `pane_release`、`signal`、`events`，且均退出 0。受控宿主记录 `real_codex_turns=0`，没有真实模型调用。

## 3. 受控宿主是否改变了本用例本意

事实是，当前套件在 `DaemonCards.setUp()` 中本来就用 `daemon_acceptance_host.ts` 调用真实 `serve()`，并由 `controlled_quality_pty.ts` 注入受控 PTY；中断断言也明确要求被杀 PID 是该 host。候选重启在第 135–140 行使用同一宿主和同一 `quality-control` 路径，因此恢复前后的 daemon 实例处于同一受控运行边界，仍通过真实 socket、gate CLI、SQLite 和 Git 运行。

产品入口 `workbench/src/gates/cli.ts` 的 `daemon_start` 确实声明可选 `--launch-config`，第 191–193 行把该文件解析后传给 `startDaemon`；省略参数时传空对象。原测试的 `daemon_start` 重启因此会丢失 reviewer 配置，正是红态根因。候选没有改产品入口，而是保持本用例原有的受控宿主边界，以便重启后仍能验证 reviewer 生命周期且不启动真实 Codex。这个选择覆盖了本票据要测的“中断后的 daemon 恢复、配置复用和门禁状态”，但不单独覆盖 `transport.ts:startDaemon` 对 `--launch-config` 的转发；若以后要验收该 CLI 转发契约，应另设产品入口测试。本票据范围内这不是缺陷。

## 4. `complete_review` 是否掩盖中断或操作锁

第 202–220 行先核对中断后的 `operation_busy`、旧 verification 为 `interrupted`、结果字段为空、命令意图保持、verification id 和 candidate directory 更换，并在释放旧 oracle 后确认孤儿结果不能结束新 verify。只有新 oracle 释放且真实 verify 子进程退出 0 后，第 227 行才调用 `self.quality.complete_review(self.task)`。

该调用与套件其他路径使用的 `DaemonCards.cli()` 自动 reviewer 驱动相同；`legacy_quality_driver.py` 的实现通过 `pane_release`、`pane_status`、`signal` 和 `events` 提交受控 reviewer 的独立结果，并核对当前 review id 和 `verified` 状态。它没有直接写门禁状态，也没有替代或跳过第二次 verify。因此没有掩盖中断或操作锁语义。

## 5. 完成条件的变异检查

### 有效变异

1. `review-01-mutant-01-01`：把重启恢复为无 `--launch-config` 的 `cli.ts daemon_start`。5 个用例中只有目标案失败，失败点为 `finish(following)['exit'] == 0`；该副本的真实 gate 回执为 `review_launch_config_required`。这直接拒绝了票据描述的错误实现。
2. `review-01-mutant-03-01`：对目标用例跳过 `complete_review`。只有目标案失败，失败点为最终 `after['task']['state']` 仍为 `reviewing` 而非 `verified`；其余四案通过。这证明新增 reviewer 完成步骤是必要行为，且不是放宽断言。
3. 作者的 `mutant-03/run.json`：目标重启改用空 `empty-review-control`，第 167–169 行的来源/等同性断言失败，另四案通过。该失败点足够：完成条件要求重启配置的来源可核对且内容等于中断前配置，空配置必须在此处被拒绝；不要求测试必须继续运行到产品的 `review_launch_config_required`。产品错误码已经由 `red-05` 的独立红态证明。

### 未计入的变异尝试

- `review-01-mutant-02-01` 的副本在套件启动前出现 `SyntaxError: EOL while scanning string literal`，没有 `run.json`；它不是有效行为证据。
- `review-01-mutant-04-02` 同样因生成的空配置字符串语法错误停止，`suite.log` 只含 Python 语法错误，没有运行任何用例；其整体脚本 exit 0 只是“预期套件失败”的包装结果，不能当作变异通过。

因此有效变异数量为 2 枚独立审查变异，加上作者保留的 1 枚配置变异，已达到 2–5 枚要求；未计入的两枚只作为审查过程限制保留现场，没有被误报为通过。

## 6. 其他用例和稳定性

红态 4/5、最终绿态 5/5、作者空配置变异 4/5、独立无配置变异 4/5、独立跳过 reviewer 变异 4/5，均只有目标用例按预期失败或通过，其余四案没有新的失败。`green-01`/`green-02` 是候选迭代过程中已保留的路径规范化和 reviewer 回收现场；最终冻结候选的 `green-03` 已通过，不能把早期现场覆盖为成功，也不构成当前候选的新不稳定。

## 限制与严重度

- **P2（证据限制，不阻塞本候选）**：独立变异脚本的 mutant-02 和 mutant-04 生成副本时把 `\\n` 变成了字符串中的实际换行，导致 Python 语法错误；因此没有独立证明“另一份配置”和“去掉配置比对后由产品错误码拒绝”的两条反例。两枚有效变异及作者变异已覆盖完成条件所需的拒绝能力，故不改变本次 PASS；后续审查脚本应修正生成方式再使用。
- **P2（覆盖边界）**：恢复用例使用受控宿主直接调用 `serve()`，没有同时验证 `daemon_start --launch-config` 的 transport 转发。当前票据未改产品入口且本用例原有运行边界就是受控宿主；若该转发行为需要独立保证，应新增只读产品入口验收。

项目地图复核：`project_map.py status --root .` 退出 0，`Problems (0)`、`Stale living docs (0)`。

T-085 REVIEW DONE
