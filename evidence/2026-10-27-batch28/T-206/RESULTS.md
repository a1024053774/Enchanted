# T-206 受管窗格的用户输入在发出时记一条（2026-10-27～28）

状态：PASS。agy（`gemini-3.8-flash-high`）独立审查结论“可合并”，见 `review-1.md`；唯一一条 P3（粘贴里的 `\r\n` 被换成两个换行）已改为换成一个换行，改后主测试 `green-2.json` 通过。

## 需求

- 用户 2026-10-27：“我建议是在我消息发送成功出去的那一刻,也就是输入完之后再记录,不然太乱了”。
- 补充：“让 agent 通过我们的系统接口来沟通传递信息,我肯定是通过输入框发送的,这就能判定是我发的消息了,然后就是那个只记录我发送之后的完整消息,不要每次操作都要记录”。

## 根因

xterm 每送来一段数据（一个键、一段粘贴），`panes.userInput` 就调一次记录回调。后台为每一段写一条 `user_inputs`；目标是受管 attempt 时，门禁再派生一条 `human_intervention`。一句 “fix it” 打下来（中间退格一次）是 9 条（`red-2.json`）。

## 修复

- `workbench/src/inputDraft.ts`（新）：每个受管窗格一份草稿。
  - 普通字符按光标位置插入；退格、←/→、Home/End、Delete 按一行编辑器处理；粘贴整段并入草稿。
  - 回车发出时，返回一条消息：攒下的整句。
    - 有编辑键时在 `content.keys` 列出（`action: terminal-submit`）。
    - 草稿跟不上的键（↑/↓ 翻历史、Tab 补全、其他控制键、二进制鼠标上报）另标 `text_uncertain`。
  - Ctrl-C、Ctrl-D 清空草稿。单独的 Esc、单按回车（草稿为空）都不产生记录。
- `panes.ts`：
  - 在写入锁里，用草稿的副本算出这段数据发出的消息。
  - 先逐条记录，再写终端；字节写成功后才保留新草稿。记录失败时字节不写入（fail-closed 不变）。
  - 协议上报（焦点、鼠标坐标）照旧不进草稿。
- `daemon.ts`：回调只在发出消息时调用；`terminal-submit` 记为 `form: message`，其他界面操作（如“用户声明输入框已空”）仍是 `action`。
- `metrics.ts`：只改注释。人工介入指标本来就按 `turn_submit_intent`（用户回车）计，紧急停止按写进终端的 Esc 计，不受影响。
- `workbench/README.md`：受管 worker 输入一节写明新规则。

## 主测试

`workbench/tests/test_t206_input_on_send_e2e.py`。环境：
- 真实 Electron 窗口，经 CDP 发原生按键给 xterm。
- 真实后台与门禁。
- worker 是真实 Claude Code，模型换成本地脚本化接口，零真实模型调用。

场景：
1. 打 “fiz”、退格、“x it”、回车。
2. 打 “abc”、←、“d”、回车。
3. 打 “zzz”、Ctrl-C、“done now”、回车，再按 Esc。

检查（预期来自需求）：
- 每句只有一条 message，文字分别是 “fix it”、“abdc”（`content.keys` 含 ←）、“done now”。
- Esc 和被清掉的 “zzz” 不记录。
- 人工介入数等于记录数，都是 3。
- 写进终端的字节与按键一一对应，回车正好 3 个。

| 运行 | 被测 | 结果 |
| --- | --- | --- |
| `red-1.json` | 第一版测试，修前 | 失败；其中“CLI 收到”的判断只看最后一条消息，是测试问题（Claude Code 会在其后追加系统文字），已改为在全部消息里找。保留为记录 |
| `red-2.json` | 修前工作树，用户补充前的测试版本（当时要求 Esc 单独记一条） | 失败：“fix it” 记了 9 条（f、i、z、退格、x、空格、i、t、回车），第 2、3 步各 6 条、3 条，人工介入 18 条 |
| `green-1.json` | 修后，最终测试 | 通过，5 项 |
| `green-2.json` | 按审查 P3 改粘贴换行后 | 通过，5 项 |
| `red-3.json` | `--revision 30ee51d30`，最终测试 | 4 项失败；终端字节一项通过 |
| `mutant-record-every-key.json` | 仍逐段记录 | 与修前相同的 4 项失败 |
| `mutant-cursor-ignored.json` | 草稿忽略 ← | 只在 `one_record_for_edited_message` 失败 |
| `mutant-ctrl-c-keeps-draft.json` | Ctrl-C 不清空草稿 | 只在 `cleared_draft_and_esc_not_recorded` 失败 |

复现（在 `workbench/tests` 下）：`python3 test_t206_input_on_send_e2e.py --summary <新路径> [--revision 30ee51d30 | --mutant record-every-key|cursor-ignored|ctrl-c-keeps-draft]`

## 跟着新规则改的旧测试

这些测试的预期原本是“每段输入记一条”，与新需求冲突，按需求改为“发出时记一条、操作不记”。要证明的其他性质不变。

- `test_t157_turn_identity.ts`、`test_t166_queued_input.ts`：手写窗格夹具补 `draft`；t157 的记录预期改为不含回车的整句。
- `t108_answer_lifecycle_contracts.mjs`：输入带回车，记录才会发生。
- `test_t078_pane_runtime.ts`：
  - “记录占住窗格”“后面的键不能抢先”两项改用带回车的消息（记录只在发出时发生）。
  - Esc 不再记录，记录只剩“用户声明输入框已空”。
- `test_t078_permission_accounting.ts`：权限框里单按回车不再记 action。
- `t078_input_failures.py`（`test_t078_input_entry.py --input-failures` 调用）：没按回车的中文组合输入、鼠标二进制上报都不记录；字节检查不变。
- `test_t145_mouse_reports_e2e.py`：打一个字时不记录，加按回车后才记一条。
- `test_t133_t134_records_metrics_e2e.py`：粘贴加回车是一条消息，回车不另记。

## 单元测试（`unit/`，在仓库根目录调用）

- `t108-2.out`：通过（退出码 0）。
- `t157-8.json`：通过，4 项。
  - `t157-head.json` 是 HEAD 源码副本上跑的旧测试，也通过。
  - `t157-3`、`t157-4`、`t157-7` 是夹具补 `draft` 之前，或输出目录给了相对路径（场景把它当 `CLAUDE_CONFIG_DIR`，报 `restore_home_missing`）的运行，保留。
- `t078-pane-7.out`：只剩 `interrupt_only_esc_not_reclaim` 失败。
  - 这项在 HEAD 上也失败（`t078-pane-head.out`），与本票无关，未修。
  - `t078-pane-5.out` 是改测试前挂住的运行（记录不再被调用），`-6` 是改 Esc 预期前的运行。
- `t078-perm-3.out`：跑不了，缺 `evidence/2026-10-11-batch13/T-078/slice1-readback/hooks/.../stdin.bin`（不在本地稀疏 checkout 里），与本票无关。

## 回归（`regression/`，命令见 `regression/run.sh`）

| 运行 | 结果 |
| --- | --- |
| `t159-1.json` | 通过 |
| `t166-separate-1.json` | 通过 |
| `t145-1.json` | 失败：旧预期“打一个键就记一条”。改测试后 `t145-2.json` 通过（新增“没按回车不记”检查） |
| `t133-t134-1.json` | 失败：旧检查要求单独的回车记录（记录页显示“按键：回车”）。改测试后 `t133-t134-2.json` 通过 |
| `t166-queued-1.json` | 失败：窗格夹具缺 `draft`。补上后 `t166-queued-2.json` 通过 |
| `t078-input-entry-1`（已归档，见 `*.archive.json`） | 没跑成：这个 T-078 期的测试建任务卡时用的旧任务名 `input-contract` 门禁里没有（`unknown_task`），测试本身已过时，与本票无关。`t078_input_failures.py` 的改动因此没有在真实入口上跑过 |

记录页对历史按键记录的命名（`（按键：…）`）保留，用来显示修前留下的旧记录。

## 没做

- `t078_input_failures.py` 的新预期没有跑过（入口测试已过时，见上）。
- `test_t078_permission_accounting.ts` 跑不了（缺稀疏 checkout 外的证据文件）。
- 草稿只按一行编辑器处理；CLI 里的多行编辑、历史翻找、补全后实际发出的文字可能与记录不同，这类消息标 `text_uncertain`，没有逐个 CLI 核对。
- 只用 Claude Code 跑了主测试；Codex、agy、opencode 窗格走同一段 `panes.userInput`，没有分别实测。
