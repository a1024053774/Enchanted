# T-203 审查员按字段提交结论（2026-10-27）

状态：PASS。agy（`gemini-3.8-flash-high`）独立审查结论“可合并”，见 `review-1.md`。两条 P3 都是证据记录问题：单元测试结果文件的位置、文件名写法。已按下文改正。

## 根因

- 回包卡死：协议要求审查员把 14 个字段的嵌套 JSON 写成最后一条回复，靠模型自己配括号。第 2 轮试用里两次都少了末尾的 `}`，门禁按 `review_json` 拒收，任务暂停。
- 两张卡同号：问题编号按会话（thread）计。每次审查都开新会话，所以同一次交付的两张卡都是“问题 1”。

## 修复（用户选“工具按字段提交”）

- `workbench/src/reviewResult.ts`（新）：
  - 工具 `review_submit` 只收 `verdict`、`findings`、`report` 三项。
  - 身份字段与 `review_requirements` 取自门禁开审查时写进请求目录的 `review-template.json`。
  - 工具当场用门禁同一个 `reviewRequest` 核对。不合格就返回出错字段和改法；合格就原子写入 `review-result.json`。
  - 同一文件也提供 `submit <请求目录> <文件>` 命令，给 agy 用。
- 门禁（`gates/core.ts`）：
  - 提示里只说用工具交结论，不再附整个模板。
  - 问题编号按 attempt 计；worker、审查员与系统问题统一。
  - 审查启动检查核对 Claude Code（`--mcp-config`）、Codex（`-c mcp_servers.enchanted.*`）、opencode（`OPENCODE_CONFIG_CONTENT` 的 `mcp`）挂的正是这次审查的服务器。
- 后台（`daemon.ts`）：
  - 审查员回合结束时读 `review-result.json`，按原样再核对一遍后转交门禁。
  - 没有这个文件就按 `review_result_missing` 暂停，问题卡保留最后一条回复作原文。
  - 不再读最后一条回复里的 JSON，旧协议删掉，不并存。
- 窗格（`panes.ts`、`terminalClis.ts`）：各 CLI 审查员的启动参数挂上服务器；agy 的提示附上提交命令。
- 界面：问题页加 `review_result_missing` 的说明。
- 文档：角色卡 `roles/reviewer.md`、`workbench/README.md`、`findings/2026-10-27-mcp-per-session.zh-CN.md`（各 CLI 怎样把工具交给模型）。

## 主测试

`workbench/tests/test_t203_review_submit_e2e.py`：真实后台、门禁，worker 与审查员是真实 Claude Code（模型换成本地脚本化接口，零真实模型调用）。同一次交付连开三次审查：

1. verdict 写成“通过”，被拒后结束回合。
2. 不调工具，最后一条回复是少一个 `}` 的 JSON。
3. 先交缺 `line` 的问题清单被拒，再交正确意见。

修前版本没有这个工具，审查员照旧在最后一条回复里写完整 JSON，并少一个 `}`。

| 运行 | 被测 | 结果 |
| --- | --- | --- |
| `red-1.json` | `--revision a3ae46cf2` | 失败：三次审查都按 `review_json` 拒收，三张卡都是“问题 1” |
| `green-1.json`～`green-4.json` | 修后，测试本身逐步修正 | 失败，均为测试问题，保留为记录：1 没按延后加载先经 ToolSearch 取工具；2、3 审查员第一个请求早于 MCP 服务器连上，且“工具是否延后”的判断被后续请求覆盖；4 检查要求报错里写 `location.line`，工具实际报 `location` |
| `green-5.json` | 修后，最终测试 | 通过，8 项 |
| `red-2.json` | `--revision a3ae46cf2`，最终测试 | 8 项全部失败 |
| `mutant-per-thread-number.json` | 编号仍按会话计 | 只在 `issue_numbers_distinct` 失败 |
| `mutant-tool-skips-check.json` | 工具不核对就写文件 | 坏 verdict、缺 line 都没被当场拒绝，第 1 次审查也没暂停 |
| `mutant-stop-reads-last-message.json` | 回合结束仍读最后一条回复 | 第 1、2 次没按 `review_result_missing` 暂停，正确意见也没被收下 |

复现（在 `workbench/tests` 下）：`python3 test_t203_review_submit_e2e.py --summary <新路径> [--revision a3ae46cf2 | --mutant per-thread-number|tool-skips-check|stop-reads-last-message]`

## 各 CLI 的实测

| 证据 | 内容 | 结果 |
| --- | --- | --- |
| `codex-real-probe-1.json`（脚本 `codex-real-probe.py`） | 真实 Codex 0.164、真实模型 `gpt-6.1-sol` high，`codex exec`，隔离 CODEX_HOME（只复制 auth.json，结束后已删） | 工具不在代码工具的声明里（延后加载）；模型经 `ALL_TOOLS` 找到 `mcp__enchanted__review_submit` 并调用，结果来自我们的服务器 |
| `codex-t127-1.json` | t127（Codex 交互 TUI，脚本化接口），按声明找工具 | 失败：声明里没有这个工具。保留为记录，据此改成真实模型的调用方式 |
| `codex-t127-2.json` | 同上，直接调用 `tools.mcp__enchanted__review_submit` | 通过：工具返回 `saved`，门禁收下，集成 |
| `opencode-real-probe-1.json`（脚本 `opencode-real-probe.py`） | 真实 opencode v2.1.4、用户自己的 HOME，`opencode run --standalone` | 模型在 `execute` 代码里调用 `tools.enchanted.review_submit`，结果来自我们的服务器 |
| `real-t187-opencode-agy-1.json` | t187 真实运行：opencode 主控派 agy worker，agy 审查员 | 通过：agy 审查员用提示里的命令交结论，审查通过并集成 |

两个探针都只核对工具能被看见、能被调用。模板是故意写的残缺模板，所以工具返回“模板不符合协议”，符合预期。

## 回归（`regression/`，命令见 `regression/run.sh`）

已改成按工具提交的旧测试：t160、t140、t141、t179、t122（含 `--review-result malformed`）、t187 替身 agy/opencode、t187 OSC、t187 Git 元数据守护，全部通过。期间两次失败保留为记录：

- `t187-managed-opencode-1.json`：替身找错了源码目录（辅助脚本被复制进 fake-bin）。改为取后台给的 `A2A_CLI`、`A2A_NODE` 后，`-2` 通过。
- `t122-1.json`：worker 启动检查仍要求 `--strict-mcp-config`。该参数 T-141 起已去掉（要加载用户的 MCP），这条断言从那时起就过时，与本票无关。按 T-141 改成“不得带此参数”后，`-2` 通过。

单元测试（`unit/`；`-head` 是在 HEAD 源码副本上跑的同一测试）：
- 通过：
  - `test_t141_reviewer_contract-2.json`
  - `test_t146_reviewer_hooks-3.json`：launch 记录补上 `request_dir`；`-2` 是补之前的失败
  - `test_t141_launch_contract-3.json`：`claudeArgv` 的 MCP 参数改为列表；`-2` 是改之前的失败
  - `test_t160_protocol_idle`：结果在 `t160-protocol-idle-4.results.json`、`-5.results.json`（`-5.json` 是同一次运行的标准输出），HEAD 上是 `-head3.results.json`。每个场景的 sqlite 等状态文件已归档到外置盘，清单见 `*.archive.json`
- `-1` 文件是从错误目录调用的结果，保留。
- `t112-reviewer-startup-1.json`、`-2.json` 与 HEAD 上的 `t112-reviewer-startup-head.json` 都失败（`vm.SourceTextModule` / 启动顺序断言），不是本票引起的，未修。
- t160 的变异体 `accept-fenced`（解析器剥代码围栏）已删除：新流程不再解析最后一条回复，这个变异体测的路径已不存在。围栏回复仍作为第一次审查的场景，按 `review_result_missing` 拒收。

## 没做

- `test_t082_review_protocol.ts`、`legacy_review_runtime.ts`、`test_t078_claude_epochs.ts`、`test_t112_execution.mjs` 没跑。
- 真实 Claude Code 审查员在第 2 轮试用式的完整 GUI 流程里没有重跑。主测试用的是真实 Claude Code，模型是脚本化接口。
- t127、t140、t141 的 Codex 审查员调用写法取自真实 Codex 的调用，没有在交互 TUI 下用真实模型跑完整审查。
- 问题页的 `review_json` 文案保留，给历史问题卡用；新流程里只有结果文件被改坏时才会出现。
