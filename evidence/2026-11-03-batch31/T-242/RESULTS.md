# T-242 结果（2026-11-03）

结论：**PASS**（Codex 没有端到端运行；复审的阻塞按审查轮数规则以不变式穷举处理，见末节）。按用户同意的第 2 种做法改了设计：没有角色的普通终端里，Claude Code、Codex 的回合状态取自 Enchanted 钩子，只在内存里，不记录。真实 Claude Code 端到端：回合中运行中、回复后空闲，标题栏、侧栏、后台一致，提示词不进状态库；修前同一测试失败于“回合中仍是未知”。Codex 没有端到端运行。

用户：“按这个顺序修,后两项我同意.”

## 改动

- `workbench/src/daemon.ts`：钩子事件到回合状态的对应抽成 `hookTurnState`（UserPromptSubmit → 运行中；Stop 或 idle_prompt 通知 → 空闲；AskUserQuestion / request_user_input_async 的 PreToolUse → 等待用户回答，PostToolUse → 运行中），有角色与没有角色两条路径共用。`terminal_hook` 在没有获批角色（或会话号不符）时，把状态交给 `panes.noteShellTurn`，仍返回 `kept: false`，不写事件、不记用户输入。
- `workbench/src/shellTurns.ts`（复审后新增）：钩子状态按报告它的进程号分别存，只在内存里；前台复查记下前台进程号；`status` 的 `hook_turn` 只取前台进程自己的那条；已退出进程的那条在下一次记录或前台复查时清掉。`workbench/src/panes.ts` 只持有它。
- `workbench/src/sidebar.ts`：普通终端前台是 Claude Code、Codex 时，`hook_turn` 的 CLI 与前台一致就用它，否则未知；已知限制里加一条（第一次提交前未知、Esc 中断后停在运行中）。
- `workbench/app/renderer.tsx`：输入焦点标签“正在输入”改为“键盘在此”，不再被读成回合状态。
- `workbench/README.md`、`test_t184_unwired_cli_e2e.py` 的注释随之更新；t184 的断言（启动后、第一次提交前为未知）不变，仍成立。

## 证据

新测试 `workbench/tests/test_t242_shell_hook_turn_e2e.py`：隔离夹具、真实 Electron 窗口、经包装脚本运行的真实 Claude Code（`claude-haiku-5-5`，模型由脚本化 API 应答，回合的模型请求由测试放行，没有真实模型回合）。

| 文件 | 结果 |
| --- | --- |
| `hook-turn-green.json`、`.log` | 修后 PASS，八项：第一次提交前未知、回合中运行中、回复后空闲、焦点标签不是“正在输入”、没有 `terminal_turn` 事件、提示词（唯一标记）不在状态库里、Claude 退出后空闲、下一个 Claude 第一次提交前未知 |
| `hook-turn-red-head.json`、`.log` | 修前（`--revision 20f1d8581`）：失败于“回合中”，后台、标题栏、侧栏都是 `unknown`，标签“正在输入” |
| `hook-turn-mutant-keep-turn.json`、`.log` | 变异体（去掉“前台换了就清掉”）：失败于“下一个 Claude 第一次提交前”，沿用了上一个的 `running` |
| `regress-t184.json`、`.log` | `test_t184_unwired_cli_e2e.py` PASS |
| `regress-t133.json`、`.log` | `test_t133_t107_terminal_controller_e2e.py`（有角色的终端主控）PASS |

五次运行的 core 都已停（`core_cleanup` 为 `stopped: true`），夹具路径下没有进程。

Esc 中断（只观察）：回合中按 Esc，Claude Code 不发 Stop，75 秒内一直是运行中，也没有出现空闲通知；它把被中断的提示词放回输入框。已写进侧栏的已知限制。

### 测试本身的失败（保留）

| 文件 | 原因 | 处理 |
| --- | --- | --- |
| `hook-turn-harness-exit.*` | 判定“退出后空闲”时没要求前台已换成 zsh，Claude 还在前台时就满足了 | 判定同时核对前台 CLI |
| `hook-turn-harness-esc-prompt.*` | Esc 把提示词放回输入框，随后打的 `/exit` 拼在后面当新提示词提交 | 先按 Ctrl-C 清空输入框 |

## 第三轮审查（`../review-3/REPORT.md`）

- 阻塞 3：前台读取是异步的，读取期间新 CLI 报的状态可能被这次读取按旧进程号清掉；`status` 不给进程号，同名新进程上可能短暂显示旧进程的状态。代码路径成立，没有运行复现（要一次前台读取跨越新 CLI 启动到它第一次提交，正常读取不到 100 毫秒）。修法是去掉清除，改为只在一处判断：前台复查记下前台进程号 `foregroundPid`，`status` 只在钩子状态的进程号与它相同时给出 `hook_turn`。没有清除，也就没有这个竞态；新 CLI 第一次报告到前台复查看到它之间（至多 5 秒）显示未知。
- 修后重跑：`hook-turn-green-2.json` PASS（八项）；变异体改为去掉这处进程号判断，`hook-turn-mutant-keep-turn-2.json` 失败于“下一个 Claude 第一次提交前”沿用旧状态。前一版的绿态与变异体（`hook-turn-green.json`、`hook-turn-mutant-keep-turn.json`）保留作记录。

## 命令

```bash
ENCHANTED_HC_CACHE_DIR=/Users/luckye/Documents/Code/hc-cache python3 workbench/tests/test_t242_shell_hook_turn_e2e.py --summary <新文件>.json [--revision <版本> | --mutant keep-turn]
```

## 复现与原因（修前，保留）

`probe_shell_claude_state.py`：隔离夹具和真实 Electron 窗口，普通项目终端里经包装脚本运行 `claude --model claude-haiku-5-5`（模型由夹具的脚本化 API 应答，没有真实模型回合），发一句话，回复出现后每秒采样一次，共 20 秒。

| 文件 | 结果 |
| --- | --- |
| `probe-2.json` | 回复出现在提交后 0.21 秒；20 次采样都是：标题栏“未知”（`data-state=unknown`），输入焦点标签“正在输入”，侧栏行 `unknown`，后台 `sidebar_snapshot` 为 `unknown`、前台 CLI `claude`；终端的钩子报出了原生会话（`shell_native_session`） |
| `probe-1-invalid-wait.*` | 第一次运行作废：等待条件被输入的提示词本身满足（`reply_seen_after_s` 为 0），不能证明已经回复 |

### 原因

- `workbench/src/sidebar.ts` 普通终端一段（T-191）：前台没有 CLI 时为空闲；agy、opencode 取它们自己的 OSC 7501；Claude Code、Codex 只有获批角色后才报告回合，之前为未知。
- `workbench/src/daemon.ts` 的 `terminal_hook`：没有获批角色时，钩子只用来记下会话号（T-195），回合事件丢弃、不记录（T-133：普通终端的提示词不进记录）。
- `test_t184_unwired_cli_e2e.py` 的 `shim_claude_without_role_state_unknown` 正是断言这一点。
- “正在输入”是输入焦点的标签（`app/renderer.tsx`），和状态无关。

标题栏、侧栏和后台三者一致，所以票面“修后显示与后台一致”现在已经成立；问题在于后台按设计就给出未知。

### 当时待用户决定（已决定：2）

1. 保持设计，改文案：例如没有角色的 Claude/Codex 显示“未接入状态”，并在提示里说明获批主控角色后才有回合状态。
2. 改设计：没有角色时也只在内存里取钩子的回合状态（运行中/空闲），不记录提示词。这样会改变 T-191/T-133 定下的边界。

## 复审（`../review-3/REREVIEW.md`）

第一次启动的复审没有开始：`codex exec` 从后台任务启动时没关标准输入，等了约 9 小时（`../review-3/rereview-codex-stdin-hang.log`）；加 `< /dev/null` 重跑。结论 NO_GO，一条阻塞：回合状态只有一个槽位，已退出 CLI 的钩子晚到时会覆盖当前前台 CLI 的状态，之后前台一直显示未知。这是第三轮已打破过的同一条不变式的新反例，按 T-240 的规则不再开审查轮，改为写不变式并系统搜索。

不变式：
- I1 显示的是前台进程自己最近一次报告的状态；它还没报告时为未知。
- I2 其他进程的钩子，不论早到晚到，都不改变 I1 的结果。
- I3 只有仍在运行（或在前台）的进程保留状态，已退出的不累积。

修法：状态按进程号分别存（`shellTurns.ts`），见“改动”。

| 文件 | 结果 |
| --- | --- |
| `turns-search/green.txt` | `workbench/tests/test_t242_shell_turns.ts` 对真实模块穷举 A、B 两个 CLI 与 zsh 的记录、前台读取、退出事件，长度 0～6 的全部 1,111,111 个顺序，PASS |
| `turns-search/mutants.txt` | 三个已知坏实现都失败：`single-slot`（修前的单槽位写法）失败于 I2，B 的报告抹掉 A 的；`no-front-check` 失败于 I1；`no-prune` 失败于 I3 |
| `hook-turn-green-3.json`、`.log` | 真实 Claude Code 端到端，修后 PASS（八项） |
| `hook-turn-mutant-keep-turn-3.json`、`.log` | 只去掉前台判断的变异体**没有失败**：第一个 Claude 退出后它的状态已被清掉，两道机制都护着第 5 项。保留作记录 |
| `hook-turn-mutant-keep-turn-4.json`、`.log` | 变异体改为两道都去掉：失败于“第二个 Claude 第一次提交前”显示旧的 `running` |

没建模的：已退出进程的进程号在前台读取看到别的进程之前就被新进程复用（不知道进程启动时间，分不出来）。新 CLI 第一次报告到前台复查看到它之间（至多 5 秒）仍显示未知。

```bash
node workbench/tests/test_t242_shell_turns.ts [模块路径] [最大长度]
```

按同一条不变式搜索相关代码：T-195 的原生会话报告（`noteShellHook` / `noteNativeReport`）也是单槽位，晚到的钩子会改写 `pane.native` 和记录。只读推导、没有复现，超出本票范围，登记为 T-246。
