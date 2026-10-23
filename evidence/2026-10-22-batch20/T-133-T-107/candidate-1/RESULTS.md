# T-133 方案 A 与 T-107 #2、#4、#5 候选 1 结果

- **候选**：代码 `36fa74f6a`；测试修正在 `97f1bb748`、`5220b7fd6`、`2ea270a59`、`c24d58955`（只改测试），正式运行用 `c24d58955`。README 在 `1f7dac8b9`。
- **修前版本**：`836b9eeb0`。
- **来源**：用户 2026-10-22 逐字（见 T-133、T-107 的“用户决定”）：“1.T-133 A 2.可以 3.…… 4.要修 5.显示出来吧 ……”。
- **结论**：Claude Code 一侧 **INCOMPLETE**，等独立审查；Codex 一侧 **BLOCKED**，等用户定（`../codex-hook-probe/RESULTS.md`）。T-107 #3 仍等用户回答。

## 改了什么

- **钩子**：项目终端 `claude` 包装加载的插件新增 `hooks/hooks.json`。在提交、回合结束、空闲 60 秒通知、AskUserQuestion 前后，各调用一次 `a2a hook`。
- **`a2a hook`**：把事件交给后台。它不往标准输出写、总是退出 0。
- **后台 `terminal_hook`**：只在该终端持有已批准角色、且会话 id 与角色申请一致时处理。这条命令不记请求事件，没批准的提示词不进库。处理内容：
  - 提交的整句记为用户输入，来源 `controller-terminal`（界面上是“主控终端提交”）；
  - 对 AskUserQuestion 的答复记为答复；
  - 写 `terminal_turn` 事件，带状态。
- **侧栏（T-107 #4）**：终端主控的状态取最后一个 `terminal_turn`。从确认生效到第一个事件之间算运行中，因为确认发生在申请的那个回合里。Codex 主控和没有原生会话的仍显示未知。
- **上级（T-107 #2）**：批准执行主控的卡片有“上级”下拉框，列出本项目在跑的构思主控（默认第一个），也可选“不归属”。
  - 选择作为 `parent_launch` 存进 `role_request_decided`。
  - 后台核对它确实是本项目的构思主控，否则返回 `invalid_role_parent`。
- **项目行（T-107 #5）**：项目名下多一行，显示 `分支 · ↑领先 ↓落后`，没有上游时写“无上游”。

## 端到端（`e2e/commands.sh`）

- **测试**：新测试 `test_t133_t107_terminal_controller_e2e.py`。终端里跑真实 Claude Code，经 zsh 与包装脚本启动，模型是本地脚本化接口。真实 Electron。
- **场景**：
  1. 构思主控申请、批准。
  2. 提问、答复、跑 20 秒命令。
  3. 执行主控申请，在界面选上级后批准。
  4. 构思主控放弃身份后用户再说一句。
- **期望**：来自 ticket 与用户决定。

| 运行 | 结果 | 失败于 |
| --- | --- | --- |
| green | PASS，10 项 | — |
| red-parent（`--revision 836b9eeb0`） | 失败 | 构思主控一直不是“空闲”（没有钩子） |
| mutant-recorded-without-role（身份结束后仍记） | 失败 | `only_approved_prompts_recorded`：放弃身份之后的那句被记下 |
| mutant-terminal-state-unknown（状态不取钩子） | 失败 | 构思主控一直不是“空闲” |
| mutant-parent-not-saved（上级不存） | 失败 | `executor_under_ideation` |
| t133-t134-green（记录页：受管窗格与面板答复） | PASS，14 项 | — |
| t107-live-green | PASS，7 项 | — |
| t107-live-mutant-terminal-shown-idle | 失败 | `terminal_controllers_unknown_not_upgraded` |
| t121-green、t126-green、t124-green | PASS，49 / 10 / 26 项 | — |

- **摸底运行**：`probe-01` 至 `04` 原样保留。
  - `01`：这一版 Claude Code 没有“? for shortcuts”，判断启动的条件错了。
  - `02`：申请卡片在列表变化后 1 秒内按钮禁用，点击落空。
  - `03`：测试表达式括号写错。
  - `04`：通过。
- **夹具**：已归档，见 `e2e/fixtures.archive.json`。`t121-green`、`t126-green` 的测试结束时自己删除夹具，没有可归档的目录。
- **T-133 验收第一条**：三种输入的组合由两条测试共同覆盖。受管窗格与面板答复由 `t133-t134-green` 覆盖，主控终端由新测试覆盖，没有放在同一次运行里。

## 未覆盖

- Codex 主控：见探针，没有实现。
- Claude Code 主控被 Esc 中断：没有 Stop 事件，要到空闲 60 秒通知才显示空闲。本轮没有测。
- 打包后的应用。
