# T-194 结果：主控经 MCP 调用门禁

日期：2026-10-27。状态：PASS（第 8 轮独立审查 PASS；生产代码自第 3 轮 `c511bd9` 未变，之后各轮只改验收测试）。

## 改动

- `a2a mcp <cli>`（`src/terminalMcp.ts`、`terminalCli.ts`）：stdio MCP 服务器，工具与 `a2a` 命令同一组（申请角色、建卡、存卡、派发、查状态、验收与打分等），参数有结构；每个工具调用经 `a2a` 命令同一条终端身份与门禁入口，不复制门禁逻辑。没有已批准角色时与命令一样拒绝。
- 按会话挂上，不写全局配置：Claude Code 经插件 `mcpServers`（会话号取 `CLAUDE_CODE_SESSION_ID`）；Codex 经包装脚本的 `-c mcp_servers.enchanted.*`（`env_vars`、`default_tools_approval_mode="approve"`、`tool_timeout_sec=660`，会话号取调用的 `_meta.threadId`）；opencode 经 `OPENCODE_CONFIG_CONTENT`。用户自己的 `-c` 在注入项之后，优先。
- agy 不挂：agy 1.4.8 交互模式下模型拿不到工作区 MCP 工具（print 模式能），继续用 `a2a` 命令；包装脚本写明重新评估的条件。
- 会话生命周期：调用被 CLI 取消或后台断开返回 `outcome_unknown`，不重放；客户端关闭服务器输入或不再读输出时会话结束，在途调用一并中止，待批的角色申请撤回、之后的批准不生效；结束后不再写回包，进程以 0 退出。`requestAt` 收到已中止的信号时不建连接。
- 事实：`findings/2026-10-27-mcp-per-session.zh-CN.md`。README、SKILL.md、开局说明同步。

## 证据

| 文件 | 版本 | 结果 |
| --- | --- | --- |
| `red-3be2a96.json`、`red-87c30f0.json` | 修前（两个基线） | 失败于主控没有 Enchanted 的 MCP 工具 |
| `green-01`～`-04.json` | 开发中 | 各自失败，保留 |
| `green-05`、`-06-rebased`、`-07-on-t195v3`、`-08.json` | 第 1 版及变基 | 8 项 PASS |
| `green-09-cand3.json` | v3 冻结候选 `0586985` | 8 项 PASS |
| `green-10-v3test.json` | `d1989e9`：测试先用 ToolSearch 等插件的服务器连上（第 3 轮审查指出的启动竞态） | 8 项 PASS |
| `red-bf16c21-v3test.json` | 父提交，改后的测试 | 等过之后仍没有 MCP 工具，失败 |
| `mutant-grant-not-confirmed*.json`、`mutant-session-not-reported*.json` | 变异 | 失败于角色生效、会话号核对 |
| `real-01-codex.json`、`real-03-opencode-agy.json` | 真实 CLI，开发中 | 失败：Codex 钩子信任框挡住；agy 交互模式拿不到工具（导致不挂 agy）；保留 |
| `real-red-b6c2600.json` | 修前 | 真实 Codex 没有经 MCP 的申请 |
| `real-02-codex.json`、`real-04.json`、`real-05-cand3.json` | 真实 Codex（隔离 CODEX_HOME）与 opencode | 3、6、6 项 PASS（`real-05` 在 v3 候选上，生产代码与最终版相同） |
| `agy-interactive-probe/` | agy 交互模式探针（账号邮箱已遮去） | 服务器启动并列出工具，模型回答没有该工具 |
| `lifecycle-red-494d859.json`、`lifecycle-red-a6c65f7.json` | 第 1、2 轮对象 | 失败于关闭输入后撤回、关闭后不再写回包 |
| `lifecycle-green-01`、`-03.json` | 修复中 | 失败，保留（`-03` 是输出关闭后进程挂着、以 13 退出） |
| `lifecycle-green-02.json` | v2 | 4 项 PASS |
| `lifecycle-green-04.json`、`-05-cand3.json`、`-06.json` | v3（`-06` 在 `d1989e9`） | 6 项 PASS |
| `lifecycle-mutant-*.json` | 变异 | `aborted-still-sent` 第一次存活（随后加了单独检查，`-02`、`-03` 失败）；其余各在目标检查失败 |
| `green-11-v4test.json`、`green-12-v4test-slow-mcp.json` | 第 4 轮审查后的测试：等待连上有上限（最多 30 次、每次隔 1 秒）；`--slow-mcp` 让服务器晚 6 秒启动 | PASS；慢启动那次确实等过 |
| `red-bf16c21-v4test`～`-v6test.json` | 父提交，各版测试 | 都失败于主控没有 Enchanted 的 MCP 工具 |
| `mutant-*-v4test`～`-v6test.json` | 各版测试上的两个变异 | 各在目标检查失败 |
| `green-13`～`-16.json` | 第 5、6 轮审查后改判据的中间运行 | `-13` 失败于 `same_gate_events`（判据把正常的重新验收判成事件序列不同），`-16` 失败于 `comparisons_refuse_different_records`（反例 `recheck_unrelated_workspace` 被放过，随后要求别名一一对应）；都保留；`-14`、`-15` PASS |
| `green-17-v6test.json`、`green-18-v6test-slow-mcp.json` | `780e52d`：按任务内首次出现编号比较、核对重新验收的起止事件，24 个反例 | 9、10 项 PASS，反例全部被拒 |
| `green-19-v6test-fixture.json` | 同上，为离线重放留夹具 | PASS；夹具的 state 归档见 `green-19-fixture-state.archive.json` |
| `r7f1-replay.txt` | 第 7 轮 R7-F1 的反事实：同一夹具上新旧判据比较（`replay194.py`、`replay-old.py`） | 旧判据放过 `recheck_other_check`，新判据拒绝 |
| `green-20-v7test.json` | `6a42b22`：重新验收里不同的字符串只许在 id、commit、时间与验证工作区序号上不同；25 个反例 | 9 项 PASS，反例全部被拒 |

测试：`workbench/tests/test_t194_mcp_entry_e2e.py`（真实 Claude Code，模型为本地脚本服务：申请主控 → 建卡 → 派发 → 交付 → 审查 → 集成，并比较经 MCP 与经 `a2a` 命令的门禁事件）；`test_t194_real_clis_e2e.py`（真实 Codex、opencode 与真实模型，申请与拒绝）；`test_t194_mcp_lifecycle_e2e.py`（真实后台、终端身份与 `a2a mcp codex` 进程，客户端按 MCP 协议手写）。

复跑（`workbench/` 下）：

```sh
python3 tests/test_t194_mcp_entry_e2e.py --summary <新路径>
python3 tests/test_t194_real_clis_e2e.py --summary <新路径>
python3 tests/test_t194_mcp_lifecycle_e2e.py --mutant stdout-error-unhandled --summary <新路径>
```

## 未覆盖

- “门禁记录一致”比较两个任务的全部门禁事件（命令意图与结果两类除外）：顺序、次数和字段值，按任务内首次出现给 id、commit、进程号编号后比较；去掉的只有耗时字段，以及第二个集成的任务因工作分支前移而多出的一段重新验收（这一段单独核对，见第 6～8 轮审查）。比较判据靠 25 个改动记录的反例证明会拒绝，不是穷举。
- 没有实等 600/660 秒的长调用；批准与确认之间的窗口只用隔离的 `requestAt` 检查覆盖，没有穷举调度。
- 真实 Codex、opencode 只走了申请与拒绝；完整交付链只在 Claude Code 上走通。

## 独立审查

- 第 1～6 轮（Codex `gpt-6.1-sol` high，只读，`review-1.md`～`review-6.md`）：
  - 第 1、2 轮 NO_GO，修生产代码：会话结束时待批申请没撤回；结束后回包仍写 stdout、触发未处理的 `EPIPE`。
  - 第 3 轮 INCOMPLETE：两项修复关闭，未发现新的生产代码缺陷；审查者在自己环境里没取得完整交付链与两入口记录比较的绿色证据，并指出测试有插件服务器的启动竞态。此后生产代码未再改。
  - 第 4～6 轮 NO_GO，都是验收测试的缺陷：等待分支的结果下标错位、一次 ToolSearch 不保证服务器已连上；“门禁记录一致”判据过宽（归一化抹掉任务内绑定、重新验收的起止事件没核对）。逐项修复。
- 第 7 轮（agy `gemini-3.8-flash-high`，`review-7.md`，对象 `780e52d`）：PASS，另提 P3 R7-F1：重新验收段里出现一次的任意文本可以被当成别名换掉。已修（`6a42b22`），并补反例 `recheck_other_check`，`r7f1-replay.txt` 证明旧判据放过它。
- 第 8 轮（agy `gemini-3.8-flash-high`，`review-8.md`，对象 `6a42b22`）：PASS，R7-F1 关闭，没有新发现。审查只读、不运行命令，运行结论来自 `green-20-v7test.json` 等归档。

两次 agy 审查的报告原文取自 agy 会话记录的最终回复，账号邮箱已删。
