# T-219 结果（主控记录，2026-10-31）

结论：**PASS**（本票问题已逐项回答）。九项里八项是测试过时，已按现行契约修订；第 6 项是产品缺陷，交 T-221。第二轮对照中另有 17 个旧套件在基线和候选上都失败，与本票改动无关，登记为 T-222。

## 候选与提交

- 基线 `a09da15f9`，分支 `t219-baseline-tests`，worktree 提交 `5d1d9b6fc`，cherry-pick 到 main 为 `4fa0d4ca4`。
- 提交的树对象 `61d8faabc` 与 worker 交的两份补丁（第一轮 [candidate.patch](candidate.patch)、第二轮 [round2/HISTORICAL.patch](round2/HISTORICAL.patch)）应用到基线后的树相同。`a09da15f9` 到合入前的 main，`workbench/tests` 没有其他改动。
- 只改 `workbench/tests/` 下的 13 个文件，没有改产品源码。

## 逐项结论

| 项 | 结论 | 现行契约 |
| --- | --- | --- |
| 1 T-176 家目录终端头 | 测试过时，已修 | T-191：没有前台 CLI 的普通终端显示空闲 |
| 2 domain 紧急中断两项 | 测试过时，已修（L1） | T-124：provider 取自 attempt 的任务卡快照 |
| 3 pane `interrupt_only_esc_not_reclaim` | 测试过时，已修（L1） | T-124，以及 T-187：provider 按启动记录的 `cli` 判定 |
| 4 A13 第一条 UPS 被拒 | 测试过时，已修 | T-108：hook 必须带 `cwd`、`transcript_path` 才能核实来源 |
| 5 T-184 `shim_claude_state_known` | 测试过时，已修 | T-191：Claude/Codex 在角色获批前状态为未知 |
| 6 T-195 次日不可读置灰 | **产品缺陷**，交 [T-221](../../../.project-map/tickets/T-221-dst-day-scan.md) | 夏令时回拨当天，按天扫描的终点用了固定 24 小时 |
| 7 daemon recovery 五场景 | 测试与共享夹具过时，已修，五场全过 | T-123 任务 id 带项目；T-141 受限目录打开后发原生 idle；T-203 审查经 `review_submit` 提交；T-096 活所有者拒绝重启 |
| 8 Electron 夹具 `card_save` | 测试过时，已修，真实窗口已运行 | T-123 |
| 9 T-142 跨项目开终端 | 测试过时，已修 | T-189/T-193：主控身份绑终端，可在任一已打开项目开终端 |

每项的修前红态、绿态和变异反例见 worker 报告 [REPORT.md](REPORT.md) 对应小节，运行索引见 [RUNS.md](RUNS.md)。

## 主控复核

主控独立重跑了 10 个入口：t133、t133 变异、domain、pane、a13、t184、recovery、electron、t142、t142 变异。全部得到预期结果：绿态通过，变异在目标检查失败。原始结果见 [controller/runs-ctl-01.json](controller/runs-ctl-01.json)，重跑脚本 [controller/run-ctl.py](controller/run-ctl.py)。

## 第二轮：共享夹具调用者对照

worker 在基线和候选上各跑了一遍共享夹具的 23 个非历史调用者，共 46 次。结果：

- 5 项两边都通过；
- 1 项（daemon recovery）由失败变为通过；
- 没有“基线过、候选不过”的；
- 其余 17 项两边都失败或被前置条件挡住，登记为 [T-222](../../../.project-map/tickets/T-222-legacy-gate-suites-broken.md)。

机器可读总表见 [round2/table.json](round2/table.json)，对照说明见 [round2/COMPARISON.md](round2/COMPARISON.md)。

## 边界偏差

worker 初轮漏设 `TMPDIR`，UI 构建写进了系统临时目录，留下 4 个构建槽。主控核对路径后删除了这 4 个槽，并接受这一轮证据，因为后续运行已固定 `/private/tmp`，第 8 项也在该目录内复验。worker 第二轮报告把这次处置写成“用户已确认”，实际是主控做的，以本记录为准。

## 证据归档（T-088）

整份 worker 证据目录、主控复跑目录和 110 个失败或运行现场，已归档到 `/Volumes/WD-Elements/a2a-evidence/2026-10-31-batch29/T-219/`。归档清单：

| 清单 | 内容 | 文件数 | 字节 |
| --- | --- | --- | --- |
| [archive/worker-evidence.archive.json](archive/worker-evidence.archive.json) | `a2a-worktrees/T-219-evidence` | 2555 | 39025052 |
| [archive/controller.archive.json](archive/controller.archive.json) | `a2a-worktrees/T-219-controller` | 103 | 4931477 |
| [archive/fixtures.archive.json](archive/fixtures.archive.json) | 110 个 `/private/tmp` 现场 | 220783 | 8433319862 |

每个条目的源与归档副本文件数、字节数一致。副本由 [archive/archive_evidence.py](archive/archive_evidence.py) 生成：不跟随链接，跳过 socket 等特殊文件并计数（本次为 0）。核对一致后，删除了 `/private/tmp` 下的 110 个原件。
