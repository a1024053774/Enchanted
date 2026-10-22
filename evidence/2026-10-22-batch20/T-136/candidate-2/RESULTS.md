# T-136 候选 2 结果

- **候选**：`338c51b4f`。
- **起因**：候选 1 的独立审查 01（`../candidate-1/review-01.md`）结论 INCOMPLETE：一是缺真实 haiku 运行（之后补了，见候选 1 RESULTS 的“真实运行”），二是三条 P2、一条 P3。
- **结论**：复审 02 INCOMPLETE（见下），由候选 3 处理。

## 审查 01 的处理

| 发现 | 处理 | 证据 |
| --- | --- | --- |
| F1 P2：包里的轨迹归档列出项目历来所有会话 | 只列范围内有归档的会话，归档字节数截到范围结束 | 新检查 `second_package_archive_in_range`：测试直接从索引表读出范围内有归档的会话，与包里的一致，并且确认范围外确实还有别的会话（否则检查没有意义）。变异 `archive-not-in-range` 与候选 1 代码都失败在这一项。 |
| F2 P2：运行记录先写，终端没能打开时永远“进行中”，那个定期时间点被静默跳过 | 记 `start_failed` 与错误，页面显示“没能启动”；定期检查里一个项目失败不影响其他项目和导入。不自动重试：那个时间点算用过，用户可以手动启动 | 新检查 `start_failure_recorded_on_run`：第二个项目的目录被移走后启动复盘，被拒，这次运行只有一条 `start_failed`。变异 `start-failure-silent` 失败在这一项。 |
| F3 P3：建议入库与“已导入”标记不在一个事务里，中途失败重试会重复 | 放进同一个 `BEGIN IMMEDIATE` 事务，失败回滚，下次重试 | 只有代码，没有端到端（要在两次插入之间制造写库失败）。 |
| F4 P2：Codex 复盘会话不归档 | 复盘启动记录给 Codex 也带上原生 home（`CODEX_HOME` 或 `~/.codex`）；归档按 rollout 首行 `session_meta` 的工作目录找，复盘的工作目录是这次运行独有的 `out/`，找到后记住 | 只有代码，没有端到端（夹具不跑 Codex）。 |

## 端到端（`e2e/commands.sh`）

运行在 `338c51b4f` 的干净分离 worktree 里进行。

| 运行 | 结果 | 失败于 |
| --- | --- | --- |
| green | PASS，12 项 | — |
| red-candidate-1（`--revision 01e0effd7`） | 失败 | `second_package_archive_in_range` |
| mutant-archive-not-in-range | 失败 | `second_package_archive_in_range` |
| mutant-start-failure-silent | 失败 | `start_failure_recorded_on_run` |
| t135-green | PASS，6 项 | — |

候选 1 的其余运行（修前红态、5 个变异、T-132 与 T-122 回归）覆盖的代码本轮没有改动，没有重跑。摸底运行 `probe-01` 原样保留。夹具已归档，见 `fixtures.archive.json`。

## 未覆盖

- Codex 复盘会话（运行与归档）没有端到端。
- F3 的事务回滚没有端到端。
- 打包后的应用。

## 独立审查 02

`review-02.md`（agy gemini-3.8-flash-high）：INCOMPLETE。F1、F3 确认修好；真实 haiku 运行确认满足“真实入口”验收。新发现：P2，没能启动后下一次复盘的默认范围起点错；P3，找 Codex 会话时某个文件打不开会中断整轮归档。两条都在候选 3 修了。
