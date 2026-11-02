# T-237 第 2 轮结果（2026-11-02）

候选：基于 HEAD `82e747f4a` 的未提交改动，`candidate.diff`。第 1 轮审查 NO_GO（`../reviews/REVIEW-01.md`，5 条阻塞），第 2 轮审查 PASS（`../reviews/REVIEW-02.md`，无阻塞）。

## 改了什么

- `Panes.shellFront`：只有 `shell_closed` 有记录才判“终端已不在”；后台没有这个终端的窗格（未恢复、退出未确认）、终端已退出但关闭没记下、读不到进程、只剩其他进程组的后台程序，都判“无法确认”（`unknown`，带原因与查询诊断）。前台判断改为“shell 所在终端的前台进程组里有 shell 以外的进程”，zsh 关掉作业控制时也成立。
- `retrospectiveTick`：后台恢复终端期间不做结束判断；`await` 之后同步再查一次该复盘仍未结束、未导入才记录；无法确认的情况经 `Retrospectives.noteEndCheck` 记在复盘上（进入或原因改变时一条 `end_check_unknown`，恢复时一条 `end_check_known`）。第 1 轮的兜底 catch 去掉：`shellFront` 自己只在不变量被破坏时抛错，由已有的 `retrospective_tick_failed` 暴露。
- `hc.find`：core 随后台一起没了、重新启动后，旧代码对找不到的终端直接抛错，恢复走不到 shell PID 退出核对，终端永远“退出未确认”。现在找不到或不再 live 都返回 null，由 PID 核对确认 shell 已退出后才写 `shell_closed`（T-212“只有程序真的没了”的语义不变）。
- Reflect 页：无法确认时显示“进行中（无法确认 CLI 是否还在：原因）”；README 写明判断方式、拿不准时的处理与状态优先级。

## 证据（命令：`bash evidence/2026-11-02-batch30/T-237/r2/run-all.sh`，在仓库根目录运行）

| 项 | 结果 |
| --- | --- |
| `green-1..3.json` | 三次 PASS，各 19 项检查（真实后台、门禁 CLI、zsh、hc core、两次重启、真实 Electron 读 Reflect 页；截图 `green-*.png`） |
| `red-baseline.json`（修前 `82e747f4a`） | 失败于 `exited_cli_marked_ended` |
| 11 个变异 `red-*.json` | 各自失败在对应检查上：no-end-check、no-grace、gone-is-running、end-before-import、missing-is-gone、job-control-only、unknown-not-recorded、unknown-every-check、no-recheck、core-restart-unconfirmed、ui-revert |
| 回归 | T-136 PASS（13 项）；T-223 三个时区 exit 0；T-212 项目终端重启与 core 崩溃 PASS |
| `v1/` | 去掉 daemon 兜底 catch 之前的整套结果（同样全绿全红）与中途失败的尝试 `attempt-*.json`（测试计数写错、core 重启后恢复确认不了而发现 `hc.find` 问题） |

## 已知边界（审查非阻塞意见）

- 测试清理用 `pkill -f <夹具目录>`，不是进程所有权证明。
- 没有直接反例的保护分支：恢复超过一分钟时不判结束、等待期间被另一轮导入、`background_only`、无法确认的原因改变。
- T-136 测试结束后遗留私有 core、holder 与复盘 Claude 进程（`Fixture.stop` 不结束 core），已有 T-232；本批两次都由主控手工清理。

## Computer Use 复验

第 1 轮（审查前版本）四个场景通过：`../../cu-fixcheck/REPORT.md`。最终版本的复验：`../../cu-fixcheck-r2/REPORT.md`。

## 存档（2026-11-02，ticket 关闭时）

按“只存状态”规则删除了大文件：`reg-t212-shell.json/*.raw` 与 `v1/reg-t212-shell.json/*.raw`（终端原始字节，约 1.2 MB）、`v1/*.png`（与本轮截图重复，约 1.2 MB）；各回归的 `run.json` 摘要与本轮 `green-*.png`、`red-ui-revert.png` 保留。测试夹具都在 `/private/tmp` 下，测试结束时已删除。
