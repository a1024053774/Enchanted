# T-130 候选 1 结果

- **候选**：`566e54b57`。README 随后在 `619bb849` 改了 Claude 尾注一段。证据运行期间源码未改动。
- **修前版本**：`04354734b`。
- **结论**：**PASS**（待独立审查）。

## 改了什么

- **`workbench/hooks/hook.py`**：Claude 分支原来直接返回 `unknown, unknown`。现在按启动时的会话号（`A2A_NATIVE_SESSION`）找会话记录：
  - 在 `CLAUDE_CONFIG_DIR`（没有则 `$HOME/.claude`）的 `projects/*/` 下找唯一一份；
  - 取最后一条非 `<synthetic>` 回复的模型与强度。
  
  规则与 Codex 分支一致：
  - 跳过半写入的行；
  - 记录不唯一、越界或会话号不符时拒绝提交；
  - 强度字段 `effort`、`perTurnEffort` 写了哪个用哪个，两者不一致时拒绝；
  - 记录缺失或没有强度时写 `unknown`。
- **`workbench/src/gates/core.ts`**：只改注释，门禁规则不变。

## 单元（`unit/commands.sh`）

`tests/test_t130_hook_claude_facts.py` 只测钩子的读取函数，期望值来自构造的会话记录。

| 运行 | 结果 | 失败于 |
| --- | --- | --- |
| hook-green | PASS，12 项 | — |
| hook-parent（`04354734b` 的钩子） | 失败 | `observed_model_and_effort`：`unknown` |
| hook-synthetic-kept | 失败 | `synthetic_reply_skipped` |
| hook-half-line-read | 失败 | 半行解析报错 |
| hook-any-session-file | 失败 | 别的会话的记录也被匹配，报不唯一 |
| hook-duplicate-first | 失败 | `duplicate_transcript_refused` |
| hook-session-unchecked | 失败 | `foreign_session_entry_refused` |
| hook-effort-field-only | 失败 | `per_turn_effort_field_alone` |
| hook-disagreement-first | 失败 | `disagreeing_effort_refused` |
| hook-missing-refused | 失败 | `missing_transcript_is_unknown` |
| hook-home-only | 失败 | `observed_model_and_effort`（忽略 `CLAUDE_CONFIG_DIR`） |

## 端到端，脚本化接口（`e2e/commands.sh`）

运行环境：真实后台，真实 Claude Code；脚本化的 Messages 接口故意以另一个模型名 `claude-haiku-5-5-t122-served` 回复。

| 运行 | 结果 |
| --- | --- |
| t122-green | PASS，23 项：尾注 `A2A-Model: claude-haiku-5-5-t122-served`（接口实际回复的模型，不是请求的 `claude-haiku-5-5`）、`A2A-Effort: low`（任务卡的值）；门禁 `trailer_check` 通过，走到集成 |
| red-parent（`--revision 04354734b`） | 失败于 `commit_carries_claude_identity`：尾注是 `unknown` |
| t127-green（Codex 尾注） | PASS，19 项 |
| t129-malformed、t129-rejected（T-129 的场景，测试文件同改） | 均 PASS，16 项 |

夹具已归档，见 `fixtures.archive.json`。

## 真实运行，sonnet 5.5 medium（`../real-01/`）

- **构建**：从 `566e54b57` 打包测试版（`a2a.revision` 与之对应）。
- **脚本**：原样复用 T-129 的 `real/t129run.sh`。
- **流程**：用户自己的 `claude --model claude-sonnet-5-5 --effort medium` 做执行主控，派 Claude worker（同模型、同强度），走完审查、打分、集成。

结果：

- **驱动检查**：5 项全过。
- **任务与审查**：任务 `accepted`，审查 `passed`，结论“可合并”。
- **提交尾注**：`A2A-Model: claude-sonnet-5-5`、`A2A-Effort: medium`。
- **与回合记录对照**：worker 两个回合的 `native_turn_facts` 都是 `claude-sonnet-5-5 / medium`，与尾注一致。
- **用户配置**：前后一致（same）。

截图在归档盘；夹具归档时去掉凭据目录，见 `../real-01.archive.json`。

## 已知边界

- 钩子取的是提交时会话记录里最后一条真实回复。如果 Claude Code 在执行命令之前还没把这条回复写进记录，取到的会是上一条回复。真实运行和脚本化运行里，尾注都与本回合事实一致。
- 门禁仍接受 Claude 交付的 Effort 为 `unknown`：记录行没有强度字段时（旧记录里出现过）不拒收。
