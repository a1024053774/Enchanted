# T-243 结果（2026-11-03，HEAD `827b6c9fc` 加工作区改动）

结论：**PASS**。已运行且会起 core 的测试修后都不再留 core（其中 `test_t078_inbox_entry.py` 本身已失效，只核对了残留），故意失败的一次也不留，用户自己的 core 不变；26 个一次性批次脚本已分诊（都已失效或要专用输入，不修）；Electron 退出未确认的路径改为先记现场再停，修后 0 残留。T-244、T-245 已另修。独立审查：第三轮 NO_GO 的第 1、2 条修后，复审（`../review-3/REREVIEW.md`）无阻塞，结论改为 **PASS**；`test_t078_input_entry.py` 的新清理段没有运行证据，只做了编译检查。

## 分诊方法

`triage.py` 逐个运行不走 `Fixture` 的独立测试（每个限时 900 秒），记下测试期间新起、测试结束后仍在、可执行文件在 /tmp 下或 `HOME` 在 /tmp 下的进程，记录后结束它们。

**事故**：第一版脚本把环境里含 /tmp 路径的新进程都算作残留，结果误杀了用户两个 ssh ProxyCommand 进程（`Tailscale nc <tailnet-host> 22`），对应的两条 ssh 连接因此断开。原因是它们环境里的 `SSH_AUTH_SOCK=/private/tmp/com.apple.launchd…`。发现后立即停下，把规则收窄为现在这样，空跑核对只命中测试进程后才续跑。记录在 `runs/test_t121_role_request_e2e/triage.json`、`runs/test_t122_claude_worker_e2e/triage.json`。

## 每个测试的分类

### 已运行（`triage-red-part1.log`、`triage-red-part2.log`，修前）

| 测试 | 退出码 / 状态 | 修前 core 残留 | 分类 |
| --- | --- | --- | --- |
| `test_daemon_recovery_e2e.py` | 0 | 5 个 herdr-core | 能运行，已修（`test_daemon_gates_e2e.DaemonCards.stop_daemon`） |
| `test_electron_e2e.py` | 0 | 1 | 能运行，已修 |
| `test_t078_inbox_entry.py` | 1，INCOMPLETE，`checks` 为空 | 1 | 已失效（修前修后都在检查前失败）；仍补了停 core，修后无残留 |
| `test_t118_shell_env_e2e.py` | PASS | 2 | 能运行，已修 |
| `test_t121_role_request_e2e.py` | PASS | 2 | 能运行，已修 |
| `test_t122_claude_worker_e2e.py` | PASS | 2 | 能运行，已修 |
| `test_t123_project_identity_e2e.py` | INCOMPLETE：`no holder: holder build … differs from core build …` | 1 | 能运行，已修；失败原因是产品缺陷 T-244，修后 PASS |
| `test_t124_controller_e2e.py` | PASS | 2 | 能运行，已修；修后有另一类残留，见 T-245 |
| `test_t126_terminal_socket_e2e.py` | PASS | 2 | 能运行，已修 |
| `test_t127_codex_home_e2e.py` | PASS | 2 | 能运行，已修 |
| `test_t131_parallel_workers_e2e.py` | PASS | 2 | 能运行，已修 |
| `test_t193_multi_project_e2e.py` | PASS | 2 | 能运行，已修 |
| `test_t195_native_link_e2e.py` | PASS | 2 | 能运行，已修 |
| `test_t198_out_of_card_e2e.py` | PASS | 2 | 能运行，已修 |
| `test_t230_terminal_hc_isolation_e2e.py`、`test_t237_retrospective_end_e2e.py`、`test_t239_pane_invalid_utf8_e2e.py` | PASS | 0 | 能运行，原来就停 core 或清进程，不改 |
| `test_t078_cards_host_bootstrap.py`、`test_t081_duplicate_input.py`、`test_t156_quality_host_credentials.py`、`t078_input_failures.py`、`test_t096_archive_failed_02.py`、`test_t096_fixed_cleanup.py`、`test_t096_red_startup.py`、`test_t096_restart_cleanup.py`、`test_t096_version_cleanup.py` | 0 / PASS | 0 | 能运行，不起 core，不改 |
| `test_orchestrator_e2e.py` | 1：`absolute_operator_credential_path_required` | 0 | 已失效：后台现在要求操作员凭据的绝对路径，测试没给 |
| `test_t078_input_entry.py` | 2：`setup_error` | 0 | 已失效：夹具准备阶段失败 |
| `test_t081_archive_ownership.py` | 1：读不到 `evidence/2026-10-14-batch14/T-081/full-02/t075-coop/run.json` | 0 | 已失效：输入的旧证据按证据规则已删除 |

### 原来就停 core，修签名与失败路径

`test_t104_shell_e2e.py`、`test_t212_hc_boundaries_e2e.py`：T-232 把 `stop_private_core` 的参数改成 state 目录后，这两个还按旧参数（夹具目录）调用，找不到 core 清单就不停 core。这是 T-232 引入的回退。审查后两者都改为在 finally 里调用 `stop_fixture_core(state, fixture, env)`：停后台失败也停 core，并核对残留。

- `test_t212_hc_boundaries_e2e.py`：修后运行 PASS，五个场景（`green-t212b/out/run.json`），其中三个停了 core（exit 0），`corrupt-cache`、`long-holder-socket` 没有 core 清单，只核对了残留。
- `test_t104_shell_e2e.py`：已失效，开头断言外置盘 `/Volumes/WD-Elements` 已挂载（旧的整目录归档规则，2026-11-01 已改为只存状态），外置盘未挂载时直接退出（`green-t104/log.txt`）。
- `test_t216_real_cli_delivery_e2e.py` 同样按旧参数调用；它走 `Fixture`，`Fixture.stop` 已经停 core，所以改为记录 `Fixture.stop` 的结果。本票没有运行。

### 批次脚本（2026-11-03 补分诊）

下面 26 个是一次性的批次驱动脚本或工具，要带批次专用输入才能运行。逐个读了必填参数与开头的前置条件；能在本机直接起来的 4 个用 `triage.py` 跑了（`runs-batch/`），每个都在门禁检查前失败，都留下 1 个 core，由 `triage.py` 记录后结束。

| 脚本 | 分类 | 依据 |
| --- | --- | --- |
| `run_t109_hierarchy.py`、`run_t108_native_e2e.py` | 已失效（已运行） | 用 T-123 以前的裸任务名保存任务卡，门禁报 `unknown_task`（`runs-batch/*/triage.json`） |
| `run_t111_flow.py` | 已失效（已运行） | 同上，任务没建成，读 `lanes['T-A']` 时 `KeyError` |
| `run_t108_real.py` | 已失效 | 与 `run_t108_native_e2e.py` 同一个裸任务名 `card_save`；另需真实 Claude 与探针输入，未运行 |
| `run_t105_panes.py`、`run_t107_sidebar.py` | 推断已失效，未运行 | 要批次构建的 baseline 源码树或 dependencies 目录；t107 直接往 sqlite 写裸任务 id `task-0`/`project-0`，是 T-123 以前的身份形式 |
| `run_pane_lifecycle.py`、`run_t076_legacy_green.py`、`run_t076_real.py`、`run_t076_startup_shutdown.py`、`run_t078_p1.py`、`run_t081_capability_turn.py`、`run_t103_picker.py`、`run_t104_shell_ui.py`、`test_t096_process_tree.py`、`test_t078_a14_rehearsal.py` | 已失效 | 开头要求外置盘 `/Volumes/WD-Elements`（旧的整目录归档规则，2026-11-01 已改为只存状态） |
| `run_t112_native.py`、`run_daemon_acceptance.py`、`test_worktree_lifecycle_e2e.py`、`test_offline_trace_e2e.py`、`t078_topology_probe.py` | 已失效 | 读按证据规则已删除的旧证据或旧录制状态 |
| `run_worker_delivery.py` | 未运行 | 要用户的回合授权文件（真实模型回合），本票无授权 |
| `daemon_acceptance_adapter.py`、`prepare_workbench_mutants.py`、`t108_cleanup.py`、`t078_worker_mutants.py` | 工具，不是测试 | 被别的脚本调用或手工整理现场，自己不起 core |

结论：运行过的 4 个与按前置条件判定已失效的 18 个在当前代码上跑不到验收检查；`run_t105_panes.py`、`run_t107_sidebar.py` 只是推断已失效，`run_worker_delivery.py` 没有运行、未验证。本票不修它们；已失效的是否删除，另行决定（不在本票范围）。已运行的 4 个都在停 core 前就失败，正是本票要堵的那类残留，但它们不走 `Fixture` 也不调 `stop_fixture_core`，修它们等于重写，不做。

## 改动

- `workbench/tests/scripted_claude.py`：把 `Fixture.stop` 里“停 core、核对夹具进程、仍有残留就再停”的循环抽成 `stop_fixture_core(state, path, env)`，`Fixture.stop` 改为调用它。
- 11 个 `--summary` 测试（t118、t121、t122、t123、t124、t126、t127、t131、t193、t195、t198）：在写摘要之前调用 `stop_fixture_core(state, fixture, os.environ)`；有残留时状态改为 INCOMPLETE 并记录 `residue`。按状态决定退出码的（t118、t121、t126）因此返回 1；其余在写完摘要后断言没有 `residue`。
- `test_electron_e2e.py`、`test_t078_inbox_entry.py`：在停后台那一段的 finally 里调用（停后台失败也停 core），残留记为 `residue` 并使结果为 INCOMPLETE。窗口就绪或退出未确认的路径见下面“Electron 退出未确认”。
- `test_daemon_gates_e2e.py` 的 `DaemonCards.stop_daemon`：在停后台那一段的 finally 里调用（`test_daemon_recovery_e2e.py` 等由此覆盖）；前面的失败作为异常上下文保留在 traceback 里。

## 证据

| 文件 | 内容 |
| --- | --- |
| `triage-red-part1.log`、`triage-red-part2.log`、`runs/*/triage.json` | 修前：14 个测试留下 core |
| `triage-green.log`、`runs-green/*/triage.json` | 修后：13 个无残留，t124 报出 git 克隆残留（T-245） |
| `triage-green-t124-rerun.log`、`runs-green-2/` | t124 重跑，同一 git 克隆残留再次出现，core 已停 |
| `forced-t193/result.json`、`forced-t193.log` | t193 的副本在后台启动后故意抛错：core 已停（`stopped: true`），夹具路径下没有进程 |
| `triage-green-3.log`、`runs-green-3/` | 审查后改成 finally 结构再跑：t123、electron、t078_inbox_entry、daemon_recovery 均无残留；t123 PASS |
| `user-core.txt` | 绿态与故意失败前后，用户自己的 Herdr/hc 进程（pid 与启动时间）不变 |
| `hc-reinstall-inode.json` | T-244 的探针 |

## 命令

```bash
python3 evidence/2026-11-03-batch31/T-243/triage.py <新目录> [测试名 ...]
python3 evidence/2026-11-03-batch31/T-243/forced_failure.py test_t193_multi_project_e2e.py <新目录>
```

## 审查

`../review-2/REPORT.md`（GPT gpt-6.1-terra，只读）：NO_GO，5 条阻塞。处理：

1. 停后台失败时跳过停 core（electron、t078_inbox_entry、DaemonCards）：代码路径成立，已改为 finally；electron 的“窗口未确认”路径是原设计，不改。
2. t104、t212 失败时不清理：成立，已改；t212 修后 PASS，t104 已失效。
3. 整票 PASS 高于证据：成立，改为 INCOMPLETE。
4、5. 属于 T-244，见 `../T-244/RESULTS.md`。

复审 `../review-2/REREVIEW.md`：NO_GO，第 1、2 条仍有反例（`DaemonCards` 的停后台命令本身在 try 之外；t104、t212 在清理前先读 `private_tokens`）。这是上一轮已打破的同一条不变式，按规则不再开新一轮审查，改为写下不变式并系统搜索：

> 测试结束时，无论清理中前面的步骤怎样失败，都要尝试停私有 core 并核对夹具进程残留。

- `invariant_search.py` 用 AST 列出每个 `stop_fixture_core` 调用所在 finally 里、排在它前面且不在 try 保护下的语句。据此改了：`DaemonCards.stop_daemon` 把停后台命令移进 try；t104、t212 改为停 core 之后再读 token（core 停后不再改写 `terminals.json`）；8 个 `--summary` 测试把停 core 移到内层 finally 第一句；`Fixture.stop` 改为先停 core 再关脚本化 API（T-232 起就排在后面）。
- `invariant-search.txt` 是改后剩下的标记，逐条核对：t118、t121、t126 与 electron 的 `if` 里整段在 `try/except Exception` 内（脚本不看 if 内部）；t104 的 `tokens = set()` 与一句 import 不会抛错；electron 的“窗口就绪或退出未确认”路径按原设计连后台本身都留给主控看现场，只停 core 也做不到“没有残留”，复审认为这条以原设计驳回不成立；用户同意改为先记现场、再停（见下节）。
- 改后重跑（`triage-green-4.log`、`forced-t193-2/`、`forced-fixture.json`、`green-t212b-2/`）：t123、t195、daemon_recovery 无残留且 PASS；t193 与 `Fixture` 的故意失败都停了 core，夹具路径下没有进程；t212 五个场景 PASS。

非阻塞：残留检查按路径子串匹配，只报告不结束进程，可能误报引用夹具路径的其他进程，保留；t118 等在残留时仍删除夹具目录，保留（与原有做法一致，残留的进程行已写进摘要）。

## Electron 退出未确认（用户同意改设计，2026-11-03）

用户：“按这个顺序修,后两项我同意.”（同意先记现场、再结束 Electron，取代 T-091 的“从不自动结束”）。

- `electron_client.py` 新增 `capture_and_stop(scene)`：先核对进程仍是本测试启动的那个，把进程组 `ps -g` 写进 `process-group.txt`，用 `/usr/bin/sample` 采 3 秒栈，再对进程组发 SIGTERM，等不到退出发 SIGKILL，仍不退出就报错。启动失败分支先调用它再抛出原错误。`close()` 本身仍不结束进程。
- `test_electron_e2e.py`、`test_t078_input_entry.py`：退出未确认时记 `window_unconfirmed` 与 `window_scene`，调用 `capture_and_stop`，然后照常停后台、停 core；结果仍为 INCOMPLETE（不把未确认当成通过）。

| 文件 | 内容 |
| --- | --- |
| `forced-window-red/result.json` | 修前（HEAD 的测试副本，`close()` 被换成抛错）：留下 6 个进程（Electron、后台 node、herdr-core），事后手工结束 |
| `forced-window-green/result.json` | 修后：0 个残留，现场已记，后台与 core 已停，结果 INCOMPLETE |
| `regress-electron/verdict.json`、`regress-electron.log` | 正常路径回归：window 阶段 PASS |

`test_t091_client_cleanup.py` 单元测试 PASS。

```bash
python3 evidence/2026-11-03-batch31/T-243/forced_window_unconfirmed.py <新目录> [测试源码目录]
```

## 第三轮审查（`../review-3/REPORT.md`，GPT gpt-6.1-terra，只读）：NO_GO

- 阻塞 1：现场采集抛错时跳过停后台与 core。复现：`CAPTURE_FAILS=1` 注入（`forced-capture-fails-red/`），留下 6 个进程（Electron、后台 node、herdr-core），事后手工结束。修：`test_electron_e2e.py` 里采集失败记 `window_scene_error` 后照常停后台、停 core；`capture_and_stop` 里记现场失败（`OSError`、`SubprocessError`）只记 `scene_error`，仍结束进程组。修后：`forced-capture-fails-green/`（整个 `capture_and_stop` 被换掉，Electron 没人结束）后台与 core 已停，留下的 Electron 按残留报出，结果 INCOMPLETE；`forced-sample-fails-green/`（`sample` 超时）0 残留，后台与 core 已停。
- 阻塞 2：`test_t078_input_entry.py` 里 `close()` 抛错会跳过现场与停后台。代码路径成立；该测试在夹具准备阶段就失败，跑不到这段，未能运行复现。改为与上面相同的结构：`close()`、采集各自失败都记录后继续，停后台放进 try，finally 里 `stop_fixture_core`（原来这里根本没停 core）。只做了 `py_compile`。
- 非阻塞“分类结论高于证据”：成立，已改上面的结论句。

```bash
CAPTURE_FAILS=1 python3 evidence/2026-11-03-batch31/T-243/forced_window_unconfirmed.py <新目录>
SAMPLE_FAILS=1 python3 evidence/2026-11-03-batch31/T-243/forced_window_unconfirmed.py <新目录>
```

## 关闭时的清理（2026-11-03）

按只存状态的规则删除：`forced-window-green/out`、`regress-electron`、`forced-sample-fails-green/out`、`forced-capture-fails-green/out` 下的 `fixture.tar.gz`（各约 2.4 MB，共 4 个）；T-242～T-245 本批在 `/private/tmp` 留下的 41 个夹具目录（`a2a4-*`、`t078-2-*`、`t123-*`、`t124-*`、`t242-*`、`t244-*`，共约 3428 MB），删除前核对路径下没有进程。这些运行目录里的 `command-output/`（小的命令输出）与截图 `claimed-no-pane.png` 也删了；`result.json`、`verdict.json`、窗口现场的进程组与 `sample` 文本等摘要保留。
