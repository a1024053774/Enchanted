# T-169 工作中输入被 CLI 并入当前回合：结果

- 写入者：执行主控（Claude Code）。T-166 残余缺陷，按 T-004 自建（ticket 写明来源）；T-166 由执行主控本人修，本票补它的漏洞。
- 基线：main `73b7e7873`（含 T-166～T-168）。真实 Electron、后台、PTY、Claude CLI；模型端为本地脚本化 Messages，厂商模型回合 0。
- 逐项结果见 `CHECKS.json`；运行命令见 `RUN-01.sh`；运行目录按 T-088 归档（`runs.archive.json`），保留红态与绿态截图 `red-1.png`、`green-1.png`。

## 根因

T-164 第二轮 worker A（launch `c55be686…`）：模型还有工具调用时用户输入（08:20:15），后台按 T-166 记 `claude_prompt_queued`，等它在原回合结束后成为单独回合。Claude Code 2.1.310 的原生转录写了 `queue-operation`（`operation: remove`，`reason: absorbed_mid_turn`）与 `queued_command` 附件，把这句话随下一个工具结果交给模型，此后不会有它的单独回合。原回合 Stop 交付照常受理，但排队列表非空，后台记 `pane_waiting_native_queue`、窗格一直忙，门禁回执 #8 没有写入，侧栏未知，reclaim 报 `worker_working`。T-166 的测试里输入发生在模型写最终回复时，CLI 把它排成单独回合，没覆盖这条路径。

## 修改

- `workbench/src/panes.ts`：原回合 Stop 完成转交后，按原生转录中同会话、同正文、不早于收到时间、`absorbed_mid_turn` 的 remove 记录，把已并入的排队输入移出等待，记 `claude_prompt_absorbed`（含 commandUuid，同一记录只用一次）。没有并入记录的输入照旧等单独回合。不按超时清队列。
- `workbench/tests/test_t166_busy_input_e2e.py`：加 `--scenario absorbed`（压住提交那一步的工具调用回复，在此期间输入）；默认场景不变，并核对 CLI 确实把输入排成单独回合。
- `workbench/README.md` 一段说明。

## 证据

| 项 | 命令 | 结果 |
| --- | --- | --- |
| 红态 | `--scenario absorbed`，修前（red-1 在当前 main、red-2 `--revision 73b7e7873`） | 2/2 `red_reproduced=true`：原生转录有 `absorbed_mid_turn`，交付受理后 `pane_waiting_native_queue`，窗格忙、侧栏未知，门禁回执 0 次写入，与 T-164 第二轮一致 |
| 绿态 | `--scenario absorbed`，修后 | green-1/2 PASS：各记一次 `claude_prompt_absorbed`，输入原样进入下一次模型请求，人工介入绑定原 attempt，回执写入一次，回到空闲 |
| 原场景 | 默认 `separate`，修后 | PASS：CLI 排成单独回合，仍由转录登记并完成 |
| 已知坏实现 | Stop 时直接清空排队（`mutant-clear-queue-at-stop.diff`，一次性提交 d7d7002f7，未合入、已删） | 默认场景只在 `queued_native_turn_bound_and_completed` 失败 |
| 回归 | T-157 stop-input、T-157 主机级、T-165 ordered、T-166 主机级 | 全部 PASS |

## 未覆盖

- 未用真实模型复验；按真实转录的并入记录判断，依赖 Claude Code 写 `absorbed_mid_turn` 的格式（2.1.310 实测）。CLI 改格式时排队输入会回到“等单独回合”，表现为窗格忙，不会误判交付。
- 一个回合里先并入、后又排成单独回合的混合序列未单独构造。
