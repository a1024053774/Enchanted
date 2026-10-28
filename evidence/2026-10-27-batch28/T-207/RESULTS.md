# T-207 按 Esc 再发消息后，worker 的交付在回合结束时进门禁（2026-10-28）

状态：PASS。agy（`gemini-3.8-flash-high`）独立审查结论“可合并”，未提 P1～P3，见 `review-1.md`。

## 需求

- 来源：真实用户式试用第 3 轮 3b 发现 2（`../UAT-03/RESULTS.md`，事件摘录 `../UAT-03/t207-events.txt`）。
- 方案：用户 2026-10-28 选“回合结束就受理”。用户亲手发出的那一回合照样核对身份（会话、回合号、该回合的原生提示号），核对过了就在回合结束时受理 worker 交的请求。核对不过的照旧拒收。

## 根因

试用状态库里，用户回合 `cb16e0b6` 的 20 个工具钩子（PreToolUse、PostToolUse）全部记为 `native_question_unverified`，原因 `question_turn_mismatch`。

- `validateHookEnvelope`（`workbench/src/questions.ts`）对工具钩子要求窗格不在“被打断”状态。
- 按 Esc 后窗格一直是“被打断、等用户放行”，用户紧接着发的新回合也被当成被打断的那个回合。
- 回合里有了不可信记录，`currentTurnTrust` 不再是 `verified`；回合结束（Stop）在 `claudeStop` 里判为 `current_turn_untrusted`，请求文件留在请求目录。
- 放行（`releaseByUser`）只清窗格状态、drain 派发队列，不处理请求目录。要等下一回合结束，请求才被收下。

这条“被打断就拒收工具钩子”原本防的是被 Esc 打断的那个回合的迟到钩子。
- Claude Code 按 Esc 时后台会让该回合退场（`claude_submission_retired`），清掉它的提示号，迟到钩子本来就过不了提示号核对。
- Codex 不退场，旧回合号仍然对得上，这条拦截仍然需要。

## 修复

- `panes.ts`：每个回合记下它开始时所在的打断（`active.interruption`，即 Esc 或门禁打断写入时的事件号）。只有在窗格被打断时登记的回合才有这个值。三处登记回合的地方都记：
  - Claude 用户回合（UserPromptSubmit）；
  - Claude 排队输入转成的回合；
  - Codex 等按回车登记的回合。
- `questions.ts`：工具钩子的条件从“窗格没被打断”改为“窗格没被打断，或这个回合就是在当前这次打断之后由用户发起的”（`active.interruption` 非空且等于 `pane.interruption`）。
  - 打断前开始的回合：没有这个值，仍拒收。
  - 用户回合里又按一次 Esc：打断号变了，仍拒收。
  - 会话、提示号或回合号、transcript 路径的核对都不变。
- 放行、Esc 的打断语义不变：回合结束后窗格仍是“被打断、等放行”，门禁回执照旧排队等放行。

## 主测试（真实入口）

`workbench/tests/test_t207_user_turn_delivery_e2e.py`。环境：
- 真实 Electron 窗口，经 CDP 发原生按键。
- 真实后台与门禁。
- worker 是真实 Claude Code，模型换成本地脚本化接口，零真实模型调用。

场景：
1. worker 在派发回合里跑一个长命令（Python sleep 120 秒）。
2. 测试在窗格里按 Esc，再打 “deliver now” 按回车。
3. worker 在这个用户回合里写文件、提交、交付。

检查（预期来自需求）：
- `delivered_at_turn_end`：回合结束后 20 秒内门禁是 `submitted`。
- `no_release_no_extra_turn`：整个过程没有 `user_queue_release`，用户回合只有一个。
- `still_waiting_for_release`：窗格仍是“被打断”（打断语义没变）。
- `user_turn_hooks_trusted`：用户回合开始后没有 `native_question_unverified`。

| 运行 | 被测 | 结果 |
| --- | --- | --- |
| `red-1.json` | `--revision f5ae30f78`，第一版测试 | 无效：等“长命令在跑”的条件写错（钩子名在 `raw_stdin` 里），且 `sleep 120` 没有挡住回合，整个计划在派发回合里就做完了。保留为记录 |
| `red-2.json` | `--revision f5ae30f78`（修前） | 失败 2 项：门禁停在 `claimed`；用户回合 8 个工具钩子 `question_turn_mismatch`、Stop `current_turn_untrusted`，与试用一致 |
| `green-1.json` | 修后 | 通过，4 项；回车后 6.8 秒门禁已交付，`relay_received`、`relay_processed` 出现在用户回合内 |
| `mutant-user-turn-not-marked.json` | Claude 用户回合不记打断号 | 无效：测试等待条件在用户回合登记前抛 StopIteration（测试自身的竞态，已改）。保留为记录 |
| `mutant-user-turn-not-marked-2.json` | 同上，改好的测试 | 失败 2 项，与修前相同：`delivered_at_turn_end`、`user_turn_hooks_trusted` |

截图与界面日志在外置盘，清单见 `*-screenshot.archive.json`。

复现（在 `workbench/tests` 下）：`python3 test_t207_user_turn_delivery_e2e.py --summary <新路径> [--revision f5ae30f78 | --mutant user-turn-not-marked]`

## 身份核对不放宽（反例）

e2e 不容易造出“被打断回合的迟到钩子”。所以用 `workbench/tests/test_t207_interrupted_turn_hooks.ts` 直接调 `validateHookEnvelope`，预期取自票的第三条验收。

| 用例 | 预期 |
| --- | --- |
| `running_turn_not_interrupted`：没被打断的 Codex 回合 | 收 |
| `turn_cut_off_by_esc`：Esc 时正在跑的 Codex 回合（回合号仍对得上） | 拒 |
| `user_turn_after_esc`：Esc 之后用户发的 Codex 回合 | 收 |
| `user_turn_cut_off_again`：用户回合里又按一次 Esc | 拒 |
| `no_recorded_interruption`：被打断但没有打断号（null 等于 null 不能算数） | 拒 |
| `claude_user_turn_after_esc`：Esc 之后用户发的 Claude 回合 | 收 |
| `claude_other_prompt_id`：同一窗格，钩子带别的提示号 | 拒 |

在仓库根目录跑：`node workbench/tests/test_t207_interrupted_turn_hooks.ts <源码根> <summary.json>`，结果在 `unit/`：

| 运行 | 被测 | 结果 |
| --- | --- | --- |
| `hooks-green-1.json` | 修后 | 7 项全过 |
| `hooks-red-f5ae30f78.json` | 修前源码 | 只在两个“用户回合”用例失败（被拒），其余反例照旧拒收 |
| `hooks-mutant-no-interrupt-check.json` | 去掉打断条件 | 3 个反例被放行：`turn_cut_off_by_esc`、`user_turn_cut_off_again`、`no_recorded_interruption` |
| `hooks-mutant-any-interruption.json` | 只看回合有没有打断号，不比是哪一次 | `user_turn_cut_off_again` 被放行 |
| `hooks-mutant-null-equals-null.json` | 去掉非空判断 | `no_recorded_interruption` 被放行 |

## 相关单元测试（`unit/`，在仓库根目录调用；运行目录已归档，见 `*.archive.json`）

| 测试 | 结果 |
| --- | --- |
| `test_t078_claude_signals.ts` | 通过 |
| `test_t157_turn_identity.ts` | 通过 |
| `test_t166_queued_input.ts` | 通过 |
| `test_t165_queued_stop.ts` | 通过 |
| `test_t078_pane_runtime.ts` | 只剩 `interrupt_only_esc_not_reclaim` 失败，T-206 时已记录为 HEAD 上就失败，与本票无关 |
| `test_native_final_read.ts` | 失败；在 `f5ae30f78` 上失败情况相同（`base-native-final-read.out`），与本票无关，未查 |
| `test_t078_empty_declaration_entry.ts` | 见下一节 |

## 顺带补上 T-206 漏跑的测试

`test_t078_empty_declaration_entry.ts` T-206 时没有跑。这次在三个版本上对照，结果在 `unit/`：

| 运行 | 被测 | 失败项 |
| --- | --- | --- |
| `pre-t206-t078-empty-decl.out` | T-206 之前 `30ee51d30` | 5 项 |
| `base-t078-empty-decl.out` | `f5ae30f78` | 11 项：多出 6 项是 T-206 带来的 |
| `t078-empty-decl.out` | 本票修后、改测试前 | 同上 11 项 |

T-206 带来的 6 项，原因有两个，都是测试问题，不是产品问题：
- 手写的窗格夹具缺 T-206 加的 `draft` 字段，输入在写入前就报错，有 5 项受影响。产品里建窗格的各条路径都带 `draft`（`panes.ts` 已核对）。补上字段后（`t078-empty-decl-2.out`），只剩下面一项。
- `controls_are_actions_not_messages` 的旧预期是 Ctrl-C、Ctrl-U、Ctrl-S、↑ 各记一条 action。这与 T-206 的用户要求（“只记录我发送之后的完整消息,不要每次操作都要记录”）冲突，改为“字节照写、不记录”（`t078-empty-decl-3.out`）。

改后失败项与 T-206 之前完全相同，剩下的 5 项是：
- `exact_injection_and_stop_contract_unchanged`
- `hand_typed_marker_is_allowed`
- `injected_mismatch_blocks_actual_hook_output`
- `no_active_injection_hand_typed_is_allowed`
- `same_window_main_queue_does_not_hide_new_input`

它们早于 T-206，与本票无关，未查。

## 回归（`regression/`，命令见 `regression/run.sh`）

| 运行 | 结果 |
| --- | --- |
| `t206-1.json`（T-206 主测试，含 Esc 不记录） | 通过，5 项 |
| `t166-busy-1.json`（忙时输入、原回合 Stop 可信、交付受理） | 通过 |

## 没做

- 只用 Claude Code 跑了真实入口；Codex 的“Esc 后用户回合”只经单元用例证明。
- 放行时一并处理请求目录（票里列过的另一方案）没有做：用户选的是回合结束就受理。
- 看到但没改：在界面里回答原生提问（`answerQuestion`，`panes.ts` 约 2083、2097 行）也要求窗格没被打断。Esc 之后用户自己发的回合里如果 agent 用原生提问工具发问，界面面板答不了，只能在终端里答。这不在本票（交付）范围，没有实测。

## 独立审查

`review-1.md`：agy `gemini-3.8-flash-high`，只读，结论“可合并”，没有提出问题。审查逐项核对了：
- Claude 与 Codex 被打断回合的迟到钩子；
- 用户回合里再次 Esc、门禁打断、窗格恢复；
- Esc 写入前后的短暂窗口；
- 其他依赖“被打断”的路径。
