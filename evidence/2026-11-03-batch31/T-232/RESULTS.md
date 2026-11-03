# T-232 结果（2026-11-03，HEAD `3aaeb41e0` 加工作区改动）

结论：**PASS**（按缩小后的范围）。`Fixture` 部分完成并通过审查；不走 `Fixture` 的测试按用户决定移到 T-243。

## 改动

`workbench/tests/scripted_claude.py`：

- `stop_private_core(state, env)` 从 `test_t212_shell_hc_e2e.py` 移到这里，只保留一份；`test_t212_shell_hc_e2e.py`、`test_t212_trace_failure_e2e.py`、`test_t228_core_identity_e2e.py` 改为从这里引用。
- `fixture_processes(path)`：列出 argv 或环境里含夹具目录的进程（`ps -E` 能看到本用户进程的环境；夹具的 HOME 或操作员凭据在环境里）。
- `Fixture.stop`：无论测试通过还是失败，停后台后停私有 core（它的窗格、shell、CLI 随之结束），然后核对夹具进程为空；有残留就失败并列出。夹具进程还在时再停一次 core：启动超过期限的后台仍在运行，可能在第一次停止之后才启动 core（见“第一、二次尝试”）。
- `Fixture.env` 传入 `ENCHANTED_HC_CACHE_DIR`（默认为本仓库旁的 `hc-cache`）。复制的源码旁没有 hc-cache，后台每次启动都会下载 hc；今天下载要约 13 秒，超过后台 10 秒的启动期限。版本与摘要仍来自发布固定值。
- `test_t216_hc_delivery_e2e.py`、`test_t216_prompt_provenance_e2e.py` 原来在 `f.stop()` 之后自己停 core，改为记录 `Fixture.stop` 的结果。

## 证据

| 文件 | 内容 |
| --- | --- |
| `red-t216-gui.json`、`red-residue.txt` | 修改前：`test_t216_issue_push_e2e.py --gui` 报 PASS，之后夹具的 `herdr-core serve`、`hold`、Claude Code 及其 MCP 子进程仍在（父进程 1） |
| `attempt-1/`、`attempt-2/` | 修改中的两次尝试：后台启动超过 10 秒期限，`Fixture.stop` 正确报出残留的 `herdr-core serve`。据此查到 hc 下载与“启动超时的后台在停止后才起 core”两点 |
| `green-forced-failure.json/.log` | 修改后：`forced_failure.py` 在 `Fixture.start` 之后故意抛错，跑完夹具路径下没有进程 |
| `green-t216-gui.json/.log` | 修改后：同一 GUI 测试 PASS，夹具路径下没有进程 |
| `green-user-core.json` | 故意失败的一次前后，用户自己 core 的目录清单与进程都不变 |

手工核对：`herdr-core server stop` 会连带结束 core 里的 zsh、Claude Code 与 MCP 子进程（红态夹具上实测）。

## 命令

```bash
python3 workbench/tests/test_t216_issue_push_e2e.py --gui --summary <新文件>.json
python3 evidence/2026-11-03-batch31/T-232/forced_failure.py <新文件>.json
evidence/2026-11-03-batch31/T-232/residue.sh /private/tmp/t216-
```

## 没有改的

自己启动后台、不走 `Fixture` 的测试有四十多个，其中大部分早于 hc 运行时（T-209），没有调用 `stop_private_core`。本票只改了 `Fixture` 及已经有停 core 逻辑的五个测试；其余按用户 2026-11-03 的决定（“做到新票里,然后继续修复”）移到 T-243。
