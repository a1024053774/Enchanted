# T-185 结果：Codex 项目终端装上开局钩子（SessionStart）

## 状态：INCOMPLETE（机械检查、真实 Codex 复跑、回归均通过；待 agy 审查、合并）

## 依据

ticket T-185（ready_rev 1）。用户 2026-10-25 原话：“1. 查明一下 3.装上钩子  5.发新 release,产品页也更新  新票:增加 antigravity,opencode 的支持吧,按理说应该不限 cli 的,但应该还要实测一下,”。验收：真实 Codex 在 Enchanted 项目终端启动，开局说明进入上下文；对同一句“你来当执行主控，派两个 worker…”直接执行 a2a request；用户自己传的 -c 或配置仍优先。构思主控 2026-10-25（inbox 20261025T132759Z-ideation-answer-001）同意真实复跑用隔离 CODEX_HOME，不用用户的 ~/.codex。

## Codex 的钩子能力（先查后做）

本机 Codex 为 `codex-cli 0.164.0`。二进制里的钩子事件有 SessionStart、SessionEnd、UserPromptSubmit、PreToolUse、PostToolUse、PermissionRequest、PreCompact、PostCompact、SubagentStart、SubagentStop、Stop 等；输出协议里有 `SessionStartHookSpecificOutputWire`，字段为 `hookEventName: "SessionStart"` 与 `additionalContext`。所以支持 SessionStart，不需要替代方案。

## 改动

- `terminal/bin/codex`：在已有的三条钩子前加 `-c hooks.SessionStart=[{hooks=[{type="command",command="\"$A2A_TERMINAL_BIN/a2a\" session-context",timeout=10}]}]`，放在用户参数之前，所以用户自己传同名 `-c` 时以用户的为准。
- `src/terminalCli.ts`：`a2a session-context` 改为输出 `{"hookSpecificOutput":{"hookEventName":"SessionStart","additionalContext":…}}`，Claude Code 与 Codex 都按这个协议读取。说明文字改成对两种 CLI 都准确：“在 shell 里运行”“命令超时设 600 秒以上”“Claude Code 里是 a2a skill，其他 CLI 看 `a2a help`”。仍然只在有终端身份时输出。
- `README.md` 同步。

## 机械检查（真实 Electron、后台、项目终端与真实 Codex 0.164；模型为本地脚本化 Responses 接口，隔离 Codex home）

`workbench/tests/test_t185_codex_session_start_e2e.py`。夹具用户自己的 hooks.json 里也有一个 SessionStart 钩子；钩子信任框由夹具用户明确选第 2 项“Trust all and continue”（Codex 0.164 的第 1 项是“Review hooks”）。

| 运行 | 结果 |
| --- | --- |
| 修前 main（`red-main-01`） | 失败 `orientation_in_codex_context`：模型请求里没有开局说明；其余 3 项通过 |
| 修后 `green-04`、`green-05` | PASS 4/4：A 终端开局说明进入上下文，用户 hooks.json 的开局钩子照常运行；B 终端用户自己 `-c hooks.SessionStart` 时，用户的钩子运行，Enchanted 的说明不进上下文 |
| 变异 `ours-after-user`（Enchanted 的 SessionStart 放到用户参数之后） | 被拒：`user_flag_session_start_runs`、`user_flag_replaces_enchanted_session_start` |

`setup-error-01/` 是测试脚本自身的问题，按原样保留：前三轮按回车进了“Review hooks”；用户 `-c` 里内嵌 JSON 引号破坏了 TOML；变异第一轮因不再弹信任框而超时，后来改为两种情况都接受。

## 真实 Codex 复跑（`real-codex-01`）

`workbench/tests/test_t185_real_codex_controller_e2e.py`：隔离后台、PTY、Electron；项目终端里敲 `codex`，走产品包装脚本。CODEX_HOME 在 /tmp 下，只复制用户的 auth.json，结束后整个删除（`codex_home_removed: true`），不进证据。模型 `gpt-6.1-sol`、强度 high。真实根提示 1 条：“你来当执行主控，派两个 worker 并行做：一个把 stock.csv 里低于 min 的物品生成补货清单 restock.md，另一个在 README 里加一段用法说明。”（没有点名 `a2a request`）。测试在界面上批准角色后再看 20 秒就停，不让它派出 worker（产品里 Codex worker 跑在用户自己的 ~/.codex）。

Codex 的前两次工具调用：`a2a help`，然后 `a2a request executor`；界面批准后它读 `card_template`，开始写卡。

| 检查 | 结果 |
| --- | --- |
| 1 个根提示（1 个 task_started），模型 gpt-6.1-sol | 通过 |
| 开局说明在会话上下文里（三项要点都在） | 通过 |
| 直接 `a2a request executor`，之前没有问答工具 | 通过 |
| 没有搜索入口、没有用绝对路径调 a2a | 通过 |
| 角色在界面上批准 | 通过 |

第一次评分（`real-codex-01/summary.json`）是 INCOMPLETE：两项失败都出在我的解析上，而不是 Codex 的行为。一是 Codex 0.164 用 code-mode 工具，shell 命令写在脚本文本里（`exec_command({cmd:"a2a request executor"})`），我的正则要求命令前是空白；二是我按不存在的 `user_message` 事件数根提示。改为允许引号、按 `task_started` 计数后，用保存的 rollout 重评（`--rescore`，不再调用模型）：PASS（`real-codex-01-rescore/`）。评分是看过数据后改的，期望没有变；为证明它仍能拒绝坏情况，用三份改坏的 rollout 重评，分别被拒（`real-codex-01-scorer-negatives.txt`）：先用问答工具再申请、用 `command -v` 和 `.app` 绝对路径找 a2a、上下文里去掉开局说明。

rollout 239 KB 已归档到外置盘（`real-codex-01/codex-rollout.archive.json`），工具调用原文在 `real-codex-01/tool-calls.json`，截图 `shots/real-codex-01-finished.jpg`。

## 回归

- `test_t133_codex_terminal_controller_e2e.py`（Codex 主控钩子、信任只问一次、提问与答复记录）：PASS 16 项（`regression-t133-codex-01.json`）。
- `test_t181_question_text_e2e.py`（Claude 侧开局说明改为 JSON 输出后仍进上下文；问答框正文可见）：PASS（`regression-t181-01`）。

## 观察（范围外，上报）

真实 Codex 主控批准后连调了 4 次 `card_template`，换了 4 种参数（不带 task、`demo-restock`、仓库内绝对路径、带 project 与 repo），说明 `a2a help` 里 `card_template` 的参数写得不够清楚。不在本票改。

## 没做 / 未验证

- 没有在用户自己的 ~/.codex 里复跑；那里第一次启动会弹钩子信任框，要用户本人确认（构思主控要求写进 T-186 发版说明）。
- 没有让真实 Codex 主控走完派发。
