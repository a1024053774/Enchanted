# T-133 Codex 一侧（方案 A）与 T-107 #3 候选 3 结果

- **来源**：用户 2026-10-22 逐字：“1. A 2. 一二都要.”。见两张 ticket 的“用户决定”一节。
- **候选**：代码 `af838d77e`；测试、README 与记录页文案到 `ddee5f5e8`。修前版本 `d0f89b48a`。
- **结论**：**NO_GO**，由候选 4 取代（`../candidate-4/`）。
  - 变异 `accepted-ends-wait` 没被抓住。
  - Claude 测试的 green 因测试自身的错误失败。

## 改了什么

- **`terminal/bin/codex`**：用 `-c` 传入三个钩子：UserPromptSubmit、Stop、PreToolUse（只匹配 `request_user_input_async`）。用户自己传了 `developer_instructions` 时也照传。
- **后台 `terminal_hook`**：
  - Codex 主控的提交记为消息。
  - 用户对 `request_user_input_async` 的答复记为答复，形如“问题：答复”。答复是一次带 `<send_user_message_question_reply>` 的提交（probe-05）。
  - 提问时是“等待用户回答”，收到答复后是“运行中”。
- **侧栏**：
  - 受管会话有未关闭、没有答复的上报时，显示“等待主控回答”。
  - Codex 主控在第一个钩子事件之前显示“未知”。
  - 缺口说明更新。
- **README、记录页说明**：写上 Codex。

## 端到端（`e2e/commands.sh`）

| 运行 | 结果 | 失败于 / 说明 |
| --- | --- | --- |
| codex-green | PASS，14 项 | — |
| codex-red-parent（`d0f89b48a`） | 失败 | `codex_keeps_the_trust_itself`。前一项“提示信任”在修前也过了：用户自己 `hooks.json` 里的钩子同样触发审查。候选 4 改为要求不止一个新钩子 |
| codex-mutant-hooks-not-passed | 失败 | `codex_keeps_the_trust_itself` |
| codex-mutant-reply-as-message | 失败 | `only_approved_prompts_recorded` |
| codex-mutant-accepted-ends-wait | **通过（变异存活）** | 包装脚本不给 Codex 传 PostToolUse，后台那条“Codex 的 PostToolUse 不算答复”的判断永远走不到，是死代码。候选 4 删掉它，变异改为“包装脚本多传 PostToolUse” |
| claude-green | 失败 | 检查“答复之后不再等待主控回答”那段 JS 的第二行不是 f-string，`}}` 原样留下，DevTools 报 SyntaxError，超时。是测试的错：库里那条上报有答复，也已送达 |
| claude-mutant-issue-not-waiting | 失败 | 超时：上报未答复时不是“等待主控回答” |
| claude-red-parent（`d0f89b48a`） | 失败 | 同上 |
| t107-live-green | PASS，7 项 | — |
| t133-t134-green | PASS，14 项 | — |
| t132-green | PASS，6 项 | — |
| t124-codex-controller-green（`--controller-cli codex`） | PASS，26 项 | — |

- **摸底运行**：代码 `af838d77e`，`codex-probe-01`～`03` 原样保留。
  - `01`：屏幕上的提示词被原地重画，丢了字母（“Hookseedreview”），而且输入框比审查提示先画出来。之后改为匹配不会被重画打断的词。
  - `02`：Codex 启动时自己往 `config.toml` 追加 `[tui]`，“配置一字未改”这个检查条件不成立。之后改为“用户选择之前没有任何 hooks 条目，原内容保留”。
  - `03`：PASS，14 项。
