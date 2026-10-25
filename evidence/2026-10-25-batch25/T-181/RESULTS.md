# T-181 结果：主控说明开局就送到（L08）；问答框正文看得见（L09）

## 状态：INCOMPLETE（复现、修复、真实 haiku 复跑都已完成；待 agy 审查、合并）

## 依据

ticket T-181（ready_rev 1），来源 `findings/2026-10-25-lcu-real-use.md` 的 L08、L09；用户 2026-10-24 原话：“然后你再用 lcu 测试一下软件看看能不能发现其他问题”。验收：用真实 haiku 主控复跑报告同一句请求，直接执行 a2a request、验收脚本无绝对路径、无长轮询；L09 复现与结论。

## L09：问答框正文空白

### 复现与结论

`workbench/tests/test_t181_question_text_e2e.py`：真实 Electron 与 xterm（WebGL），项目终端里用户命令启动的真实 Claude Code 2.1.310（与 lcu 实测同版本），模型为本地脚本化接口，发出与实测同一句的 AskUserQuestion，另一个终端发一句短问题对照。

`l09-probe-01`（修前）：两句问题正文都在 PTY 原始输出里，也在 xterm 缓冲区里，但截图上看不见。PTY 中正文前的转义是 `ESC[38;5;231m ESC[1m`，即 256 色的 231 号纯白加粗。Claude Code 默认按深色背景配色，工作台终端是浅色背景，白字落在白底上。三层里排除了 CLI 没写、终端没收到，结论是**渲染层的配色对比问题**，与长度、宽度无关，短问题同样看不见。

### 修复

`app/renderer.tsx`：终端加 `minimumContrastRatio: 4.5`（WCAG AA 文字对比度；VS Code 终端默认同值）。xterm 绘制时把与背景对比不足的前景色调深或调浅，深浅两套配色都生效。不改用户的 Claude 配置（不写 `~/.claude`），对其他按深色背景配色的 CLI 也一样。

### 检查

同一脚本加两项机械检查：截图上问题那一行深色像素数（按 xterm 视口行号与单元格高度裁出该行）。

| 运行 | 长问题深色像素 | 短问题深色像素 |
| --- | --- | --- |
| 修前 main（`red-main-01`） | 32 | 0 |
| 修后（`green-01`） | 12004 | 866 |

截图：`shots/red-main-01-long.jpg`（空白）、`shots/green-01-long.jpg`（正文为深色粗体，可读）。

## L08：主控用问答框代替角色申请、找不到 a2a 入口

### 根因

lcu 实测的原生会话记录显示，Haiku 从头到尾没有调用 Skill 工具加载 a2a skill：先用 AskUserQuestion 问“是否批准”，再用 ToolSearch、`command -v a2a` 找入口，最后用 `.app` 内的绝对路径调用，之后才 `cat` 了 SKILL.md。主控说明只放在一个要模型自己去选的 skill 里，模型没选到就什么都不知道。

### 修复（提示词管判断，不加机制）

- `terminal/plugin/enchanted-a2a/hooks/hooks.json` 加 SessionStart 钩子，调用新子命令 `a2a session-context`（`src/terminalCli.ts`）：只在 Enchanted 项目终端里（有终端身份时）输出几行开局说明，Claude Code 把它放进会话上下文。内容：`a2a` 已在 PATH 上、`a2a help` 列出命令；用户让你当主控就直接 `a2a request executor|ideation`，不要先用问答框问；当主控、派 worker 前先读 a2a skill。
- `SKILL.md` 补三条：完成条件在 worker 工作区里运行，验收脚本读项目文件只用当前工作目录的相对路径；终端主控没有交付通知，不写 `sleep` 循环，要等结果就把 `run` 放到后台（结束时 Claude Code 会通知），用 `dispatch` 时查一次状态就结束回合；并行相关的卡把共用约定写进每一张卡。

### 机械检查（脚本化模型）

同一脚本的 `orientation_in_model_context`：Claude Code 发给模型的请求里是否带开局说明。修前 `red-main-01` 没有，修后 `green-01` 有。

### 真实 haiku 复跑（`real-haiku-01`）

`workbench/tests/test_t181_real_controller_e2e.py`：隔离后台、PTY、Electron，主控是真实 `claude-haiku-5-5`（一次性 HOME，只读用户登录、不带 refresh token，结束后删除），worker 用脚本化接口只结束回合。真实根提示只有 1 条，即 L08 原句逐字：“请申请成为这个项目的执行主控（a2a request executor）。批准后：把 stock.csv 低于 min 的物品生成补货清单 restock.md，并另起一个任务在 README 里加一段用法说明；两件事分别派给两个 worker 并行做。”问答框不禁用（要观察的就是它）。

| 检查 | 结果 |
| --- | --- |
| 1 个真实根提示，模型均为 claude-haiku-5-5 | 通过 |
| 先 `a2a whoami` 再 `a2a request executor`（第 2 条命令），没有问答框 | 通过 |
| 直接调用 `a2a`，没有搜索入口、没有用 `.app` 绝对路径 | 通过 |
| 验收脚本 `/tmp/a2a-cards/check_restock.py`、`check_readme.py` 不含项目主目录绝对路径 | 通过 |
| 没有 `sleep` 轮询：派发后查一次状态就结束回合 | 通过 |
| 没有停下来问工作分支，两张卡都派出，工作分支 `enchanted/demo` | 通过 |

整个回合约 80 秒（08:37:04 到 08:38:25 `end_turn`）。测试的回合结束检测没有识别到这次 `end_turn`，一直等到 900 秒上限（`outcome: timeout_900s`）；这是测试脚本的检测问题，不影响上面的检查，原生记录里回合确实已结束。

需要审查判断的部分（不在脚本里宣称通过）：
- 两张卡的共用约定：T-2 的 README 用法说明里写了 restock.md 的格式，是否与 T-1 卡要求的一致。卡全文见 `real-haiku-01/cards.json`。
- 最终回复是否如实：它说工作分支“沿用已有的 enchanted/demo（没有新建）”。实际是它第一条 `card_save; create` 命令里卡保存被拒、create 随之失败，但后台在门禁拒绝前已经建了分支；第二次 create 才收到 `reason: existing`。模型如实转述了回执，错在后台（见下）。
- 并行派发时用 `&` 同时发两条 dispatch，T-1 收到 `operation_busy`，它查一次状态后重派成功。这是一次有事实依据的重试，不是循环。

原生会话记录 573 KB 已归档到外置盘（`real-haiku-01/native-transcript.archive.json`）；工具调用、卡与验收脚本原文在 `real-haiku-01/`。

## 发现的范围外问题

T-180 的缺陷：不带 branch 的 create 在门禁拒绝时（这次是卡版本不存在），后台已经新建的工作分支留在仓库里；下一次 create 回执写 `existing`，主控据此告诉用户“沿用已有分支”，与事实不符。执行主控按 T-004 边界另建缺陷票 T-183 修。

## 回归

`test_t133_t107_terminal_controller_e2e.py`（终端主控的 UserPromptSubmit、Stop、AskUserQuestion 钩子与 T-176 状态检查）：PASS（`regression-t133-t107-01`）。

## 没做 / 未验证

- Codex 主控没有 SessionStart 钩子这条路，本票只改了 Claude Code 的插件；Codex 仍靠 skill。
- 真实运行只做了 1 次，用户额度紧张，没有做修前的真实对照；修前行为以 lcu 实测原生记录为准。
- `minimumContrastRatio` 也会把其他浅灰提示字调深一点，没有逐一核对每个 CLI 的观感。
