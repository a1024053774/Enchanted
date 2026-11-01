# T-229 执行报告（2026-11-01）

候选状态：**INCOMPLETE**，第十二轮独立审查前。写代码的是 Claude Code 主控，在会话里写；基线为 `59815ea30`。

## 改动

- `workbench/src/inputDraft.ts`：草稿不再保存按键；`feedInput` 返回的每条消息只有文字和 `uncertain` 两项。
- `workbench/src/panes.ts`：
  - `userInput`：只有 agy、opencode 窗格（没有提交钩子）按 attach 拼出的那句记录。拼不准时 content 只有 `{ text_uncertain: true }`，没有按键。
  - Claude Code、Codex 窗格改由 `signal` 里的 UserPromptSubmit 记录，文字取钩子报来的全文；Claude 回合中排队的提交（`claude_prompt_queued`）也记。
  - `noteSubmission` 在窗格状态改动之前调用。worker 的派发只在窗格空闲时经 `paste_intent` 粘贴进去，后面跟着它自己的那次提交，所以可能是“我们的”只有一条：最近一次粘贴、之后还没有任何提交（`turn_start_signal`、`claude_prompt_queued`、`dispatch_prompt_claimed`）的那条派发。提交全文等于它时认领，记 `dispatch_prompt_claimed`，不进用户输入。其余提交是用户的，包括用户再次发出同一段文字，经 `recordUserSubmission` 记一条。全文相等即认领的规则同 T-216。
  - 记录失败时保持 T-206 的 fail-closed（第三轮审查后的形态）：`noteSubmission` 的查询、认领、记录任一步抛错，就把用户输入观察标为失败并原样抛出；后台照旧把这次失败记在 `request_rejected`。阻断由钩子命令 `gates/cli.ts` 统一给出：UserPromptSubmit 的请求只要后台没回 ok（包括请求本身失败、连不上后台），就输出 `decision: block` 并以 0 退出（两家 CLI 只在退出码 0 时认 JSON 里的阻断）。
  - 钩子缺 `prompt` 时拒绝（`claude_prompt_required`、`codex_prompt_required`），检查放在记录和改动窗格状态之前。
  - 项目终端草稿的恢复检查不再要求 `keys` 字段。
- `workbench/src/gates/cli.ts`：上一条的阻断。UserPromptSubmit 的后台请求最多等 8 秒（`PROMPT_SUBMIT_DEADLINE_MS`），到时放弃并阻断，赶在 CLI 自己 10 秒的钩子限时之前（第四轮审查后）。请求里带 `submit_deadline`（比放弃早 1 秒），`daemon.ts` 在 `signal` 入口、改任何窗格状态之前拒绝已过期的请求（`prompt_submit_deadline_passed`），所以钩子已阻断的提交不会被记下，也不开回合（第五轮审查后）。
- 阻断后的窗格（第八轮审查后，方案 1，用户 2026-11-01：“还是在 T-229 里直接做方案 1吧,相关回归也做”）：Claude、Codex 窗格的窗口回车只是输入证据，不开回合、不标忙，草稿仍算占用（`userDraft` 不清），所以派发不会粘到它上面。回合在后台处理这次 UPS、确认它不是我们的派发之后才开始：Claude 在新 prompt 时标忙并清草稿；Codex 在 UPS 建 `active`，同一回合里追加的输入保留原回合（早于最近一次打断的 `active` 不算同一回合，第十一轮审查后）。被阻断的提交什么都不改；成功的提交只在它的回车之后没有新输入（打字、输入法组合、中断）时释放草稿（`submitGeneration`，第十轮审查后）。用户提交一经记录就是提交点：之后这次请求里的写入失败，窗格标为失败，钩子不阻断（第九轮审查后）。第六、七轮加的 `beforeSubmit` 快照及 `submissionBlocked`、`submissionConfirmed` 已删掉。UPS 的回包不等反馈处理，反馈处理在关连接之后。
- `workbench/src/daemon.ts`：`recordUserSubmission` 写一条 `terminal-window` 渠道的用户输入，带窗格的 task、attempt。门禁照旧从中派生人工介入。窗口输入记录的 form 判断改为“content 带 action 才是 action”。
- `workbench/README.md`：受管 worker 输入一段按 CLI 分两条写。
- 测试：
  - 新增 `test_t229_worker_input_e2e.py`：真实 Electron，真实 Claude Code 或 Codex worker，本地脚本化接口。
  - 新增 `test_t229_managed_input_e2e.py`：agy、opencode，用 T-187 的本地替身。
  - `test_t206_input_on_send_e2e.py` 场景 2 原来断言 content.keys 列出左方向键，与 T-229 相反，改为断言没有 content。T-206 的两个草稿变异移到新测试，因为 Claude worker 改由钩子记录后，草稿编辑只对 agy、opencode 起作用。record-every-key 变异的定位行随改动更新。
  - `scripted_claude.Fixture.card` 加了可选参数 `executor`。
  - 五个直接构造 `Panes` 的单元夹具（第三轮后补）：`test_t078_claude_signals` 补上 drain 会写的 `paste_intent`；`test_t078_pane_runtime` 中三个 attach 记录的检查改用 opencode 窗格（T-229 后 attach 只为没有提交钩子的 CLI 记）；T-108 的四个问答状态夹具接一个什么也不记的 `recordUserSubmission`，并注明记录不在其测试范围内。

## 红态（基线 `59815ea30`，真实入口）

| run | 观察 |
| --- | --- |
| `red-claude`、`red-codex` | 场景 1 记录带 `{"action":"terminal-submit","keys":["←"]}`；场景 2 用 ↑ 调出历史再提交，没有记录（attach 拼出的是空串）；记录与人工介入都只有 1 条 |
| `red-opencode`、`red-agy` | 场景 1 带 `keys:["←"]`；场景 2 带 `keys:["↑"]` 与 `text_uncertain` |

## 绿态与变异（候选代码）

最终候选上的运行都是 PASS：

- `final-claude`、`final-codex`：两种 worker 各 4 项检查。
  - 方向键改字后记一条 “abdc”，没有 content。
  - ↑ 调出历史后再记一条 “abdc”，文字等于 CLI 实际提交的全文，没有 `text_uncertain`。
  - 任务书与主控派发都被认领（Codex 的 `claims: 2`），不进用户输入。
  - 记录 2 条，人工介入 2 条。
- `final-opencode`、`final-agy`：各 4 项检查。
  - “abdc” 没有 content。
  - “xy” 加 ↑ 只带 `{text_uncertain: true}`。
  - 被 Ctrl-C 清掉的草稿不记，之后的 “ok” 单独记一条。
  - 人工介入 3 条。
- `final-t206`：更新后的 T-206 PASS。

变异都被识别：

| 变异 | 结果 |
| --- | --- |
| `no-claim`（Claude） | 任务书被记成用户输入，`dispatches_not_user_input` 失败 |
| `attach-too`（Codex） | 一次提交记两条，记录 3 条、人工介入 3 条 |
| `cursor-ignored`（opencode） | 记成 “abcd” |
| `ctrl-c-keeps-draft`（agy） | 记成 “zzok” |
| T-206 `record-every-key` | 逐键记录 |

## 第一轮审查后的修改与运行

REVIEW-01：FAIL。逐条核实与处理如下。

1. **P1 记录失败不挡提交**：属实。改为先记录后改状态，记录失败就阻断，见上文“改动”。
   - `r3-fails-claude`、`r3-fails-codex`：注入一次记录失败（`--case record-fails`，只在测试源码副本里打补丁），两种 CLI 都没有把这句交给模型，没有记录，记了 `user_submission_blocked`。这也实测确认 Codex 0.164.0 认钩子返回的 `decision: block`。
   - `no-block` 变异（恢复第一轮“只抛错”的行为）在两种 CLI 上都失败：模型收到了这句。
2. **P1 旧派发可被认领**：属实。认领范围改为“最近一次粘贴、之后还没有提交”的那一条，旧库里早已提交的派发后面都跟着提交，不再可认领。本测试造不出旧版本留下的数据，这一条只做了代码核对；试写的 `claim-any` 变异在新数据上与新规则表现相同，区分不了，已删掉。
3. **P1 正文不一致被阻断时没有记录**：主控判断不是问题。`injected_prompt_blocked` 那条路径上，提交被后台阻断，CLI 没有执行；审查引用的 `test_t078_empty_declaration_entry.ts:126` 里，回车是后台派发自己按的，用户并没有发出。按票面“只记录最终发出的那一条”，没发出的不记。原始钩子正文留在 `injected_prompt_blocked` 事件里。
4. **P2 prompt 检查顺序**：属实，已随第 1 条一起前移。
5. **P2 测试没测只认领一次**：属实。主流程加了第 4 步：用户贴入那条已被认领的派发全文再发送，必须记为用户输入，并断言认领恰好 2 次。`r3-claude`、`r3-codex` 通过（记录 3 条、人工介入 3 条）；`r3-mutant-no-claim-codex` 失败。

改后整组重跑（`run-round3.sh`、`run-r3-final.sh`）：

- T-229 自己的四种 CLI、T-206，以及下面这组回归，都是 PASS。
- `r3-reg-t216-provenance-claude-01-daemon-start` 卡在后台启动超时，没走到任何业务检查。重跑 `-02` 为 PASS。

## 第十一轮审查后的修改与运行

REVIEW-11：FAIL，一条 P1，属实，是本票引入的 Codex 退步：以前 Codex 在回车时开回合，Esc 之后的回车会新建带打断标记的提交；本票改为 UPS 开回合后，被打断的旧 `active` 一直留到 UPS。Codex 新回合的 `task_started` 先被 rollout 扫描读到，把旧对象的 `nativeTurn` 改成新回合；UPS 比较相等，当成同一回合追加输入，没有新建提交。新回合的工具钩子于是按“被打断”判为不可信（`questions.ts:69`），回合结束交付不能受理。

- 改法：Codex UPS 判断“同一回合追加输入”时，除了 `nativeTurn` 相等，还要求这个 `active` 不早于最近一次打断（`pane.interrupted` 时 `active.interruption` 必须等于 `pane.interruption`）。早于打断的就是被打断的回合，UPS 新建提交并带上打断标记，与本票之前回车时的做法一致。
- 新场景 `esc-then-submit`（只在 Codex 上，Claude 的同一路径由 T-207 覆盖）：主控派发让模型跑长命令，用户按 Esc，再发 “run probe”，模型在这个用户回合里跑一条短命令。检查：这个回合的工具钩子出现过；钩子与回合结束没有被拒收，也没有 `native_question_unverified`；这个回合是一次带打断标记的新提交；用户这句只记一条。变异 `esc-reuses-turn`（只比 `nativeTurn`）失败于 `user_turn_hooks_and_stop_accepted`、`user_turn_is_its_own_submission`：工具钩子与回合结束都被记成 `native_question_unverified`，正是审查描述的现象。冒烟时这项检查原来只看拒收、漏看了 `native_question_unverified`，已补上。
- 第九轮把 Claude 那段代码多缩进了一级，T-207 自己的变异 `user-turn-not-marked` 按原缩进定位会找不到，测试里的定位串已跟着改；本轮跑了这个变异，失败于 `delivered_at_turn_end`、`user_turn_hooks_trusted`。
- 第十四轮（`run-round14.sh`，先跑新场景、新变异与 T-207 变异，再整组重跑）：
  - PASS：`esc-then-submit`；新场景两种 CLI 各四个；五个失败场景和主流程（`r14-query-fails-claude-2`，其余 `-1`）；`r14-t206-1`；agy、opencode；回归 T-167 两项、T-157 stale 两项、T-165 unrelated-stop、T-166 两项、T-133/T-134、T-207、T-216 三项；单元与第十三轮相同（`test_t108_questions` 254/429、答题生命周期 12，状态集合与第十一轮相同；`t078` 两个 `results.json` PASS；`r14-unit/c/` 三项 PASS）。
  - 卡在启动期限后重试的：`r14-query-fails-claude-1`。
  - 变异都失败在业务断言（同第十三轮，另加上面两项）。
  - **T-157 stop-input、T-165 ordered：INCOMPLETE，与 T-235 同一问题。** 都失败于 `positive_returns_idle_without_regular_recovery`：后台 idle，界面标题栏“运行中”“未知”。基线 `59815ea30` 上这两个场景各跑 2 次全失败（`r14-base-t157-stop-input-{1,2}`、`r14-base-t165-ordered-{1,2}`）。T-235 已扩到这三个场景。

## 第十轮审查后的修改与运行

REVIEW-10：FAIL，一条 P1，属实：回车后刚开始、还没上屏的输入法组合，`beginComposition` 已把草稿标为占用，但 attach 一侧草稿里还没有字；A 的 UPS 成功后按草稿判断，把它也释放了，派发可能在用户仍在组合 B 时送进去。

- 改法：不再看草稿内容，改看回车之后有没有新输入。每次 Claude、Codex 窗格的窗口回车记下它进来时的输入代数（`submitGeneration`，取自准入时已有的 `inputGeneration`）；成功提交时，只要之后输入代数又变了（打字、开始组合、门禁中断都会让它加一），草稿就继续占用。第九轮加的 `draftHeld` 已撤回，项目终端的两处恢复原样。保守的一面：后台在回车与 UPS 之间重启时，`submitGeneration` 为空，草稿占用到下一次提交。
- 新场景 `composition-after-enter`：后台把 “slowok” 压 3 秒，回车后用 CDP `Input.imeSetComposition` 开始组合 “中”、不上屏；派发应等着；再用 `Input.insertText` 上屏、回车，派发之后才送进去且不与 “中” 拼在一起。`draft-released-on-submit` 变异在这个场景上两种 CLI 都失败于 `dispatch_waits_for_later_draft`。
- 单元夹具：三个手搭窗格、直接发用户 UPS 而不经窗口回车的夹具（`t108_hook_failure_contracts`、`test_t108_hook_replay`、`t108_answer_lifecycle_contracts`），在新规则下草稿一直占用，问答检查报 `question_input_changed`（`test_t108_questions` 首次 115/429，答题生命周期 2/14）。产品里用户提交都来自后台看到的窗口回车，所以给夹具窗格补 `submitGeneration:0`，注释写明它代表一次代数为 0 的回车、之后没有输入。第九轮给前两个夹具补的空草稿已撤回。补后 `test_t108_questions` 254/429、答题生命周期 12，各用例状态与第十一轮完全相同（`r13-unit/test_t108_questions-3.json`、`answer-lifecycle-2.json`）。
- 第十三轮（`run-round13.sh`，先跑新场景与变异，再整组重跑）：
  - PASS：新场景两种 CLI 各四个（含 `composition-after-enter`）；五个失败场景和主流程（`r13-codex-2`、`r13-query-fails-codex-2`、`r13-result-fails-codex-2`，其余 `-1`）；`r13-t206-1`；agy、opencode；回归 T-167 两项、T-157 三项、T-165 ordered、T-166 两项、T-133/T-134、T-207、T-216 三项；`r13-unit/c/` 里 T-157 turn_identity、T-166 queued_input、T-165 queued_stop 单元。
  - 卡在启动期限后重试的：`r13-codex-1`、`r13-query-fails-codex-1`、`r13-result-fails-codex-1`、`r13-mutant-record-then-block-r-codex-1`。
  - 变异都失败在业务断言，与第十二轮相同，另加上面那项。
  - **T-165 unrelated-stop：INCOMPLETE，判断为基线既有问题。** `-1` 失败于 `positive_returns_idle_without_regular_recovery`：后台 `pane_status`、`sidebar_snapshot` 都是 idle，但界面侧栏行和窗格标题栏还是“未知”（测试在后台空闲后只等 2 秒读 DOM，之后的截图已是“空闲”）。补跑 `-2` 通过、`-3` 同样失败；三次的后台事件时间线完全相同。基线 `59815ea30` 上同一场景跑 3 次全失败（`r13-base-t165-unrelated-stop-{1,2,3}`）。所以不是本票引入的，登记 T-235。第十一、十二轮各跑一次都通过，只说明它时好时坏。

## 第九轮审查后的修改与运行

REVIEW-09：FAIL，两条 P1，都属实。

1. **成功的 UPS 把之后才输入的草稿也释放了**：用户发出 A，A 的钩子还没处理时又输入 B（未发送）；A 成功后 `userDraft` 被无条件清掉，B 还在输入框，派发可能粘到 B 上。改为成功提交后按 attach 一侧的草稿重新计算：草稿在回车时清空，所以只有回车之后又输入的字（或草稿跟不上的键）才继续占用。判断抽成 `inputDraft.ts` 的 `draftHeld`，项目终端原有的两处同一判断也改用它。
   - 新场景 `draft-after-enter`：后台把 “slowok” 的钩子请求压 3 秒（期限内），用户回车后接着打 “zq”。检查：只记 “slowok”；之后的派发等着（`dispatch_waits_for_later_draft`）；用户回车发出 “zq” 后派发才送进去，且没有和 “zq” 拼在一起（`later_draft_sent_alone`）。变异 `draft-released-on-submit`（照旧无条件清掉）两种 CLI 都失败在这两项。
2. **记录提交后又失败，钩子仍阻断**：第八轮我说这需要合并两条库连接；审查指出本层有更小的改法，属实。根因是钩子的放行与否绑在“整次请求成功”上，而不是绑在“记录已提交”上。改为记录就是提交点：用户提交一经记录，CLI 就执行它；之后这次请求里的写入（开回合的编排事件、后台的 `request_result`）失败时，用 `recordFailure` 把窗格标为失败（`user_submission_bookkeeping_failed`、`request_result_write_failed`，状态 unknown，派发停下，界面可见），不再让钩子阻断。这样“有记录”就等于“CLI 执行了”，不需要跨连接的事务。认领的派发同样在回包成功后不因 `request_result` 写失败而被阻断。
   - 新场景 `after-record-fails`（记录提交后，第一笔编排写入失败）、`result-fails`（请求处理完，`request_result` 写入失败）。检查：模型收到了 “failrec”；恰好一条记录；窗格的 `failed` 写明原因。变异 `record-then-block`（恢复为抛出、钩子阻断）两种 CLI、两种场景都失败在 `recorded_submission_sent_to_model`、`pane_failure_visible`。
   - 停止检查标出的两处 catch（`panes.ts` 的 `afterRecord`、`daemon.ts` 的 `request_result`）：都有真实失败到达（库写入抛错，新场景就是注入这一点）；后者对其他请求照旧抛出；恢复由本层负责（标窗格失败并留事件），不是吞掉。
- 第十二轮（`run-round12.sh`：先跑新场景和新变异，再把第十一轮整组重跑一遍，因为产品代码变了；重试规则同前，这一轮也从摘要 JSON 里认启动期限失败）：
  - PASS：新场景两种 CLI 各三个；五个失败场景和主流程（`r12-codex-2`、`r12-query-fails-claude-2`，其余 `-1`）；`r12-t206-1`；agy、opencode；回归 T-167 两项、T-157 三项、T-165 两项、T-166 两项、T-133/T-134、T-207、T-216 三项。
  - 卡在启动期限、没走到业务检查后重试的：`r12-codex-1`、`r12-query-fails-claude-1`、`r12-mutant-record-then-block-r-{claude,codex}-1`。
  - 变异都失败在业务断言：新增两个见上；其余与第十一轮相同（`no-claim`、`attach-too`、`enter-starts-turn`、`hook-error-passes`、`no-deadline`、`late-handled`、`no-observer-mark`）。
  - 单元：`test_t108_questions` 第一次跑全部 INCOMPLETE：`t108_hook_failure_contracts` 夹具手搭的窗格对象没有 `draft` 字段，`afterRecord` 读草稿时报错，窗格被标失败。产品里每个窗格构造处都有 `draft`（`emptyDraft()`），这是夹具缺字段，给它和 `test_t108_hook_replay` 的窗格补上空草稿后重跑（`r12-unit/e2/`），254/429，各用例状态与第十一轮完全相同。`test_t078_claude_signals`、`test_t078_pane_runtime` 的 `results.json` 为 PASS（后者进程退出码仍为 1，日志结尾仍是收尾时的 “database is not open”，与 HEAD 相同）；答题生命周期 12 PASS，集合相同；`r12-unit/c/` 里 T-157 turn_identity、T-166 queued_input、T-165 queued_stop 都 PASS。`test_t078_claude_epochs` 也发 UPS，但在 HEAD 上就以同样的报错失败（`r5-unit/base`），没有可比的通过项。

## 第八轮审查后的修改与运行

REVIEW-08：FAIL，四条 P1、一条 P2。前三条都出在第六、七轮加的回车前快照上；用户 2026-11-01 选定方案 1（“还是在 T-229 里直接做方案 1吧,相关回归也做,没存储了自己清理不用缓存.”），把快照整个去掉。

- 改法：Claude Code、Codex 窗格的窗口回车不再改窗格状态，只是输入证据；草稿仍算占用（`userDraft` 不清），所以这段时间排队的派发不会粘到用户的字上。回合在后台处理这次 UPS、确认它不是我们的派发之后才开始（Claude 在新 prompt 时标忙并清草稿；Codex 在 UPS 建 `active`，同一 `turn_id` 里追加的输入保留原回合）。被阻断的提交什么都没改，所以不需要恢复。`beforeSubmit`、`submissionBlocked`、`submissionConfirmed` 及其在 Stop、Esc 处的清除全部删掉；`noteSubmission` 改为返回这次提交是否被认领。
1. **P1 迟到的阻断覆盖后来的草稿**、2. **P1 门禁 Esc 不让快照失效**、3. **P1 未匹配的 Stop 删掉快照**：快照不存在了，三条路径随之消失。阻断后用户接着输入的 B 仍占着草稿，派发等用户发出 B。
4. **P1 记录提交后又失败**：第八轮后没有修好，当时如实留作遗留（第九轮后已改，见上一节）。用户输入与人工介入由门禁（`gates/core.ts`）在自己的 DatabaseSync 连接里提交；`turn_start_signal`、`request_result` 等编排事件由 `store.ts` 在另一条连接里写。两条连接开的是同一个 `state.sqlite3`，但一个事务跨不了两条连接；要统一事务边界，就得合并门禁与编排库的连接，超出本票范围。影响：记录已提交、之后同一请求里的编排写入失败时，钩子阻断，CLI 不执行，记录留在库里；窗格已被这次 UPS 标忙，要等下一次成功提交或后台重启恢复。这只在库写入刚成功、紧接着又失败时出现，没有故障注入覆盖。我在第八轮之前对用户说方案 1 会一并处理这一条，这不准确，已向用户更正。
5. **P2 Codex `late-handled` 只差错误码**：属实。第十轮里，第二次空回车让 Codex 窗格的回合变了，迟到的请求被另一条身份检查拒绝。方案 1 之后回车不建回合，这条变异在两种 CLI 上都失败在业务断言（见下）。
- 测试：删掉 `snapshot-overwritten`、`no-restore` 两个变异；新增 `enter-starts-turn`（回车照旧开回合标忙，即 T-229 之前 Codex 的做法）。阻断后的检查改为 `dispatch_waits_for_user_draft`：两种 CLI 的派发都等用户先处理草稿（Codex 自己清空了输入框，但后台不读屏，不知道）；用户发出 “ok” 后派发才送进去，模型收到的内容里没有 “failrec”。单元夹具 `test_t157_turn_identity`、`test_t166_queued_input` 接上 `recordUserSubmission`；前者在 Claude 窗格上原来断言 attach 记下了文字，T-229 后改由钩子记录，改为断言回车不记，其余断言不变。
- 第十一轮（`run-round11.sh`，结果在 `runs.log`；重试规则同第九轮，每次尝试的夹具路径记在 `fixtures-r11.tsv`，跑完即删）：
  - PASS：两种 CLI 的五个失败场景和主流程（`r11-codex-2`，`r11-query-fails-codex-2`，其余 `-1`），`r11-t206-1`，agy、opencode；回归 T-167 receipt、dialog-open，T-157 stop-input（`-2`）、stale recover、expired，T-165 ordered、unrelated-stop，T-166 separate、absorbed，T-133/T-134 记录与指标，T-207，T-216 issue-push、provenance 两项。
  - `r11-reg-t157-stop-input-1` 卡在后台启动期限，没走到业务检查。这个测试把错误写在摘要 JSON 里、不写日志，脚本的重试没认出来，主控手工补跑 `-2`。`r11-codex-1`、`r11-query-fails-codex-1`、`r11-mutant-no-observer-mark-claude-1` 同样卡在启动期限，脚本已重试。
  - 变异都失败在业务断言：`no-claim`、`attach-too`（两种 CLI 都失败于 `edited_message_one_record_without_keys`、`dispatches_not_user_input` 等四项）；`enter-starts-turn`（`pane_idle_after_block`、`dispatch_waits_for_user_draft`）；`hook-error-passes`、`no-deadline`（`unrecorded_submission_not_sent_to_model`、`dispatch_after_block_delivered`）；`late-handled`（两种 CLI 都失败于 `no_record_for_blocked_submission`、`pane_idle_after_block`、`dispatch_waits_for_user_draft`、`late_request_refused`）；`no-observer-mark`（`observer_failed_after_block`）。
  - 单元：`r11-unit/cand2/` 里 T-157 turn_identity（`-2`）、T-166 queued_input PASS，T-165 queued_stop PASS；`r11-unit/e/` 与第十轮相同（`test_t078_claude_signals` PASS；`test_t078_pane_runtime` 的 `results.json` 为 PASS，结尾仍是收尾时的 “database is not open”；`test_t108_questions` 254/429，通过的用例集合与第十轮相同；答题生命周期 12 PASS，集合相同）。
- 仍不覆盖：后台根本不知道的阻断（连不上后台、回包在余量之外）——钩子命令自己阻断，窗格本来就没被回车改动，后台只是没记录；空回车或被 CLI 吞掉的回车会让草稿保持占用，直到下一次提交（以前是窗格停在忙，不比以前差）；Codex 被阻断后派发也等用户下一次提交。

## 第七轮审查后的修改与运行

REVIEW-07：FAIL，三条 P1、一条 P2，都属实。

1. **快照被后续回车覆盖，Stop、Esc 也不让它失效**：改为只有在没有待决快照时才记下（`beforeSubmit ??=`），后面不发送任何东西的回车（空行、第二次回车）不再覆盖它。Stop 和 Esc 让快照失效。`request-hangs` 在第一次回车后再按一次空回车；新变异 `snapshot-overwritten`（每次回车都重新记下）失败在 `pane_idle_after_block`（冒烟 `r10s-mutant-snapshot-overwritten-claude-1`）。恢复仍不核对快照属于哪一次提交，因为窗口回车时还没有 prompt id；同一时刻只认第一个未决快照。
2. **记录成功后又失败**：快照不再在 `noteSubmission` 里丢掉，改由后台按回包的最终结果处理：ok 才丢掉，失败（包括 `turn_start_signal`、`request_result` 写入失败）就恢复。确认放在 `request_result` 写入之后、回包之前。遗留：用户输入与人工介入已经提交，之后的写入失败让钩子阻断时，这条记录撤不回来（追加式记录）。窗格会恢复，用户再次提交时会再记一条。这只发生在记录提交之后库写入失败，没有故障注入覆盖。
3. **阻断后的 drain 在库持续故障时会产生未处理的拒绝**：关连接后那一段的 catch 改用 `panes.recordFailure(pane, "queue_stopped", error)`。事件写不进去时它只报一次 `event_write_failed`，不再抛出。事件类型照旧是 `queue_stopped`，现有消费方只看类型。
4. **P2 `no-claim` 变异定位失效**：定位串改为现在的写法；全部变异与故障注入的定位串已逐一核对，都只出现一次。

- 第十轮（`run-round10.sh`，另补 `r10b-query-fails-codex`：原来四次都卡在启动期限；结果在 `runs.log`，重试规则同第九轮）：
  - PASS：两种 CLI 的五个失败场景和主流程，`r10-t206-1`，回归 T-166 separate、T-165 ordered、T-207、T-216 issue-push、T-216 provenance 两项，`r10-agy-1`、`r10-opencode-1`。
  - 变异都失败在业务断言：`snapshot-overwritten`（Claude 失败于 `pane_idle_after_block`；Codex 还失败于 `dispatch_after_block_delivered`）；`no-claim`（两种 CLI 都失败于 `dispatches_not_user_input` 等四项）；`no-restore`、`no-deadline` 同第九轮；`late-handled`，Claude 同第九轮，Codex 这次只失败在 `late_request_refused`。核实 Codex 那次：迟到的请求被以 `hook_origin_or_turn_mismatch` 拒绝，原因是第二次空回车让窗格的回合变了，所以没记下；变异仍能区分新旧行为。
  - 单元（`r10-unit/`）：与第九轮相同（`test_t078_claude_signals` PASS；`test_t078_pane_runtime` 的 `results.json` 为 PASS；`test_t108_questions` 254/429，通过的用例集合不变；答题生命周期 12 PASS，两个 `shell_*` INCOMPLETE）。

## 第六轮审查后的修改与运行

REVIEW-06：FAIL，两条 P1，都属实。

1. **回包前还在等反馈处理**：记录完成后，后台要先 `await settleInboxFeedback()` 才回包，其中单次进程观察最长可能等 5 秒，7 秒检查、8 秒放弃的余量盖不住。改为 UserPromptSubmit 的回包不等反馈处理；反馈处理改在连接关闭之后，和其他 signal 一样先 drain 再处理。现在从期限检查到回包，后台只剩同步处理；只有受管主控窗格的 UPS 还要多查一次本地门禁状态（`gates.call status`，读本地库）。
   - 没有加“记录成功后再压住回包”的故障注入：本票之后，产品路径上已经没有这样的等待，人为注入只能演示固有的残余窗口，区分不了新旧实现。
2. **被阻断的提交让窗格停在“忙”**：这是本票引入的退步，不是范围外问题。以前记不下的输入在 attach 一侧就失败，回车送不进去；本票让回车先进 CLI、再由钩子阻断。用户 2026-11-01 选定在本票修（选项“在 T-229 里修”）。T-234 并入本票，随本票关闭。
   - 改法：用户在 Claude、Codex 窗格按回车时，记下回车前的 `state` 与 `active`（`beforeSubmit`）。后台对这个窗格的 UPS 请求没有回 ok（规则和钩子命令一致：没回 ok 就一定阻断），就由 `panes.submissionBlocked` 恢复这两项，记 `user_submission_blocked`，并像其他 signal 一样在关连接后 drain。认领或记录成功、或派发自己按回车时，丢掉这份快照。
   - 第八轮发现：Claude 阻断一次提交后，会把这段文字放回输入框。`r8-request-fails-claude-2` 里，之后的派发粘贴进来，和它拼成了 “failrec⟦主控 #2⟧…”。所以恢复时 Claude 窗格保留用户草稿（`userDraft`），派发等用户先处理；Codex 会清空输入框（`r8-request-fails-codex-1` 的派发正文里没有 “failrec”），不保留。
   - 不覆盖：后台根本不知道的阻断，也就是后台连不上、或回包在 1 秒余量之外才到。这时窗格会停在“忙”，直到下一次成功提交，或后台重启后恢复窗格。
   - 测试：每个失败场景两种 CLI 都检查 `pane_idle_after_block`。观察正常的场景（`request-hangs`、`request-fails`）还要：发一条主控派发，Codex 应直接送进 CLI；Claude 应先等着（`dispatch_waits_for_returned_draft`），用户删掉那段字、发 “ok” 之后才送进去，且模型收到的内容里没有 “failrec”（`dispatch_after_block_delivered`）。新变异 `no-restore`（不恢复）：`r8-mutant-no-restore-claude-2`、`-codex-1` 都失败在 `pane_idle_after_block`、`dispatch_after_block_delivered`。
   - 第八轮另有 `diagnostic-fails` 两项失败在“变异定位必须唯一”：`request_rejected` 那一行改了，测试里的定位串跟着改。
- 第九轮（`run-round9.sh`，结果在 `runs.log`；每项只在卡在后台启动期限时重试，最多 4 次，卡住的尝试不算结果）：
  - PASS：两种 CLI 的五个失败场景和主流程（`r9-request-hangs-claude-1`、`r9-record-fails-claude-1`、`r9-query-fails-claude-2`、`r9-diagnostic-fails-claude-1`、`r9-request-fails-claude-1`、`r9-claude-2`；`r9-request-hangs-codex-3`、`r9-record-fails-codex-3`、`r9-query-fails-codex-2`、`r9-diagnostic-fails-codex-1`、`r9-request-fails-codex-1`、`r9-codex-1`），`r9-t206-1`，回归 T-166 separate、T-165 ordered、T-207、T-216 issue-push、T-216 provenance 两项，agy、opencode（`r9-agy-1`、`r9-opencode-1`）。
  - 变异都失败在业务断言：`no-restore`（Claude 失败于 `pane_idle_after_block`、`dispatch_waits_for_returned_draft`；Codex 失败于 `pane_idle_after_block`、`dispatch_after_block_delivered`），`late-handled`（两种 CLI 都失败于 `no_record_for_blocked_submission`、`late_request_refused` 及阻断后的状态检查），`no-deadline`（失败于 `unrecorded_submission_not_sent_to_model`）。
  - 单元（`r9-unit/`）：`test_t078_claude_signals` PASS；`test_t078_pane_runtime` 的 `results.json` 为 PASS，结尾的 “database is not open” 是收尾时的报错，第五轮候选上同样有；`test_t108_questions` 254/429，通过的用例集合与第五轮候选相同；答题生命周期 12 PASS，两个 `shell_*` INCOMPLETE，与 HEAD 相同。

## 第五轮审查后的修改与运行

REVIEW-05：FAIL，一条 P1，属实：8 秒期限只断开客户端连接，后台之后照样处理这条过期请求。`r6-request-hangs-claude`、`r6b-request-hangs-codex-03` 的 `observed.inputs` 各有一条 “failrec”，会派生人工介入；Claude 还会开一个等不到 Stop 的回合。

- 改法：钩子命令随请求发 `submit_deadline = 发出时刻 + 7 秒`，8 秒时放弃。后台在 `signal` 入口先比时间，过期就拒绝（`prompt_submit_deadline_passed`，记在 `request_rejected`）。从这一检查到记录，窗格的处理是同步的，中间没有 await，所以拒绝时什么都没改；留 1 秒给回包到达钩子。
- `request-hangs` 不再提前返回，改为检查：模型没收到这句；没有用户输入记录；`request_rejected` 恰好一条，错误为 `prompt_submit_deadline_passed`；窗格没有为它开回合（`active`、`cli_turn` 为空）。
- 新变异 `late-handled`（后台不比期限，即第五轮前的行为）：`r7-mutant-late-handled-claude`、`-codex` 都失败在 `no_record_for_blocked_submission`、`late_request_refused`、`no_turn_for_blocked_submission`。`no-deadline` 照旧失败在 `unrecorded_submission_not_sent_to_model`。
- 范围外发现，登记 T-234：Claude 窗格里被阻断的用户提交，窗格停在 `busy`，`active` 为空。来源是窗口回车先把窗格标忙（HEAD 上就有的输入证据规则），提交被阻断时 UPS 和 Stop 都不会来，要等下一次成功提交才恢复。T-229 之前记不下的输入在 attach 一侧就失败，回车没写进去；T-229 把记录挪到钩子以后，才走到这条路径。`r7-request-hangs-claude` 最初按“窗格空闲”断言而失败，就是这个原因（`state: busy`、`active: null`、`cli_turn: null`）。之后把断言收窄到“后台没为这次请求开回合”。
- 第七轮之初，Codex 的 `request-hangs` 也失败在 `no_turn_for_blocked_submission`（`r7d-request-hangs-codex-2`：`state: busy`，`active.nativeTurn` 有值，库里没有记录，后台拒绝了这条请求）。核实：Codex 窗格的 `active` 是窗口回车建的（非 Claude 的 CLI 回车即建），`nativeTurn` 来自 Codex 自己 rollout 的 `task_started`，都不是这条过期请求开的。所以“没开回合”这一条只对 Claude 有区分力（Claude 的 `active` 只由 UPS 建立），改为只在 Claude 上检查；Codex 靠“没有记录、后台拒绝”判断。T-234 原先写“Codex 会回到空闲”，依据的是没被阻断的变异，不对，已改为两种 CLI 都会停在 `busy`。
- 运行（`run-round7.sh` 及 `7b`～`7f`，结果在 `runs.log`，每项开始时记下负载）：
  - PASS：主流程 `r7-claude`、`r7d-codex-1`；`request-hangs`：`r7d-request-hangs-claude-3`、`r7f-request-hangs-codex-2`；`record-fails`：`r7d-record-fails-claude-1`、`r7-record-fails-codex`；`query-fails`：`r7b-query-fails-claude`、`r7e-query-fails-codex-1`；`diagnostic-fails`：`r7-diagnostic-fails-claude`、`-codex`；`request-fails`：`r7d-request-fails-claude-2`、`r7-request-fails-codex`；`r7-t206`；回归 `r7-reg-t165-ordered`、`r7-reg-t207`、`r7-reg-t216-provenance-claude`、`-codex`、`r7b-reg-t166-separate`、`r7b-reg-t216-issue-push`。
  - 变异按预期失败在业务断言：`late-handled` 在 Claude（`r7b-*`）上失败于 `no_record_for_blocked_submission`、`late_request_refused`、`no_turn_for_blocked_submission`，在 Codex（`r7e-*-1`）上失败于前两条；`no-deadline` 两种 CLI 失败于 `unrecorded_submission_not_sent_to_model`。
  - 卡在后台 10 秒启动期限、没走到业务检查的尝试，都留在 `runs.log` 里，没有算作通过或失败。负载 8～26 时最多，用户退出 TokenTracker 后，负载 3～4 时仍有：夹具里后台约 12 秒才起来。启动路径不在本票改动内。
  - 用户 08:20 让暂停时，`run-round7c.sh` 在第一次尝试后停下；中断留下的一个夹具后台和脚本化 Claude 进程已结束。

## 第四轮审查后的修改与运行

REVIEW-04：FAIL，两条，都属实。

1. **P1 钩子超时绕过阻断**：后台连上后不响应时，钩子命令会一直等到 120 秒的请求期限，CLI 在 10 秒时就杀掉钩子并照常执行（Claude 的超时默认继续）。改为钩子命令对 UserPromptSubmit 只等 8 秒，到时放弃并阻断，以 0 退出。遗留问题（已写在 `cli.ts` 注释里）：后台如果超过 8 秒才处理这次请求，仍可能记下这条被阻断的提交，并把窗格标为回合已开始。
   - 新增 `--case request-hangs`：在测试源码副本里让后台把这次钩子请求压住 30 秒。检查：模型没收到这句。
   - `no-deadline` 变异（不设期限，即第三轮的行为）：`r6-mutant-no-deadline-claude`、`-codex` 都失败在 `unrecorded_submission_not_sent_to_model`。
2. **P2 `unknown_pty_queued` 等不到同步点**：Claude 窗口输入不再在 attach 记录，场景的等待点永远等不到。改为该场景用 opencode 窗格（attach 仍为它记录）。单独跑这组用例（`r5-unit/run-answer-lifecycle.mjs`），HEAD 与候选结果相同：12 个通过，两个 `shell_*` 在 HEAD 上就不通过（`r5-unit/base/answer-lifecycle.json`、`r5-unit/cand2/answer-lifecycle.json`）。

第六轮（`run-round6.sh`，再加 `run-round6b.sh`，结果在 `runs.log`）：

- `run-round6.sh` 跑到 `r6-request-hangs-codex` 时内置盘写满（ENOSPC），此后各项都没走到业务检查。之前跑完的：两个变异见上；Claude 的 `request-hangs`、`record-fails`、`diagnostic-fails`、`request-fails` 及主流程 `r6-claude` 都是 PASS；`r6-query-fails-claude` 卡在后台启动期限。
- 腾出空间后 `run-round6b.sh` 重跑其余各项：`r6b-query-fails-claude`、Codex 的 `record-fails`、`query-fails`、`diagnostic-fails`，主流程 `r6b-codex`，T-206，回归集（T-166 separate、T-165 ordered、T-207、T-216 issue-push、T-216 provenance 两项）都是 PASS。
- 后台启动超时，没走到业务检查：`r6b-request-hangs-codex`、`-02`，`r6b-request-fails-codex`。夹具 `state/hc` 的修改时间比夹具目录晚 8 秒（`stat`，当时看的，夹具之后已删），后台没赶上 10 秒启动期限；同时 `uptime` 的负载约 7.5，没有另存日志。从第七轮起 `runs.log` 每项开始时记下负载。重跑 `r6b-request-fails-codex-02`、`r6b-request-hangs-codex-03` 都是 PASS。
- 夹具：用户 2026-11-01 让只存状态、不整目录归档。各夹具目录的状态（时间、字节、文件数）记在仓库 `evidence/2026-10-31-batch29/T-229/fixtures-status.md`，原目录已删。第六轮之后新产生的夹具同样处理。

## 第三轮审查后的修改与运行

REVIEW-03：FAIL，两条，都属实。

1. **P1 阻断只覆盖 `noteSubmission` 内部**：钩子请求外围的 `request_received`、`hook_received`、`request_result` 写失败时，后台回 `ok:false`，钩子命令以 1 退出，CLI 照样执行。改在根因层：钩子命令 `gates/cli.ts` 对 UserPromptSubmit 的任何失败都返回阻断。这样 `noteSubmission` 里第二轮加的“返回阻断 + 另包一层诊断写入”就成了平行路径，已删掉，改为标记观察失败后原样抛出，由后台既有的 `request_rejected` 记下失败。`user_submission_blocked` 事件不再有。
2. **P2 查询或认领失败时没标观察失败**：标记移到 `noteSubmission` 共同的 catch 里；daemon 里 `recordUserSubmission` 原来那层 catch 重复了，删掉。

运行（`run-round5.sh`，结果在 `runs.log`）：

- 失败场景，两种 CLI 各四个，都是 PASS：`record-fails`、`query-fails`、`diagnostic-fails`（记录失败，`request_rejected` 也写不进去）、`request-fails`（`request_received` 写不进去，请求没进到窗格）。共同检查：模型没收到这句，没有用户输入记录；前两个另查 `request_rejected` 记下注入的失败、观察标为失败。
- 变异：
  - `hook-error-passes`（钩子命令对失败只报错，即前三轮的行为）：`request-fails` 下两种 CLI 都失败在 `unrecorded_submission_not_sent_to_model`。
  - `no-observer-mark`：`query-fails` 下失败在 `observer_failed_after_block`。
  - `no-claim`、`attach-too`：照旧失败。
- 主流程 `r5-codex`、`r5-claude-03`，agy、opencode、T-206，以及回归集（T-166 两项、T-165、T-157、T-207、T-187 opencode、T-216 issue-push、T-216 provenance 两项）：都是 PASS。
- 后台启动超时，没走到业务检查：`r5-claude`、`r5-claude-02`、`r5-mutant-hook-error-passes-codex`、`r5-request-fails-codex`。日志是后台超过启动期限后才起来，此时启动方已关掉 IPC（`ERR_IPC_CHANNEL_CLOSED`），机器负载约 7。重跑 `r5-claude-03`、`r5-mutant-hook-error-passes-codex-02`、`r5-request-fails-codex-02`，结果见上。启动路径不在本票改动内。
- 单元测试：本仓库 35 个直接构造 `Panes` 的单元测试，在 HEAD 副本与候选上各跑一遍（`run-r5-unit.sh`，结果在 `r5-unit/`）。
  - 28 个在 HEAD 上就已失败（缺证据文件、模块路径过时、断言过时等），候选上第一条报错相同。
  - 有退步的三个，原因都是夹具没接新的 `recordUserSubmission`，或没有 drain 会写的 `paste_intent`：`test_t078_claude_signals`（HEAD 3/3）、`test_t078_pane_runtime`（HEAD 11 项全过，候选卡住）、`test_t108_questions`（HEAD 254/429）。按上文“测试”一条改夹具后，三者分别回到 3/3、11/11、254/429，与 HEAD 的通过集合相同（`r5-unit/cand2/`）。
  - `test_t108_hook_replay` 需要具名参数，两边都没跑起来，未覆盖。
  - 比较只对得上能解析出检查项的测试；其余只比了第一条报错，不算逐项等价。
- 行为变化：之前 UserPromptSubmit 钩子的其他拒绝（如会话不符、提示号重复）只报错，CLI 照样执行；现在一律阻断。理由：Claude Code、Codex 的用户输入只从这个钩子记，钩子没成功就是没记下，按 T-206 应 fail-closed。
- 文档：README 的认领规则改为“最近一次粘贴、之后还没有提交的那条派发”，并写明阻断。这两处改动在 r5 运行之后，只改文档。

## 第二轮审查后的修改与运行

REVIEW-02：FAIL，一条 P1：诊断事件 `user_submission_blocked` 写失败时，异常冒出钩子，`decision: block` 不返回，CLI 照样执行。属实：用户输入与编排事件同在 `state.sqlite3`，库坏时两者一起失败。

- 改法（已被第三轮后的改法取代）：`noteSubmission` 的查询、认领与记录整体放进一个 try；catch 里诊断事件另包一层，写失败时记后台日志并标事件写入失败，然后照常返回阻断。
- 新增 `--case diagnostic-fails`：在记录失败之外，再让这次的诊断事件写入失败（同样只在测试源码副本里打补丁）。检查：库里没有 `user_submission_blocked`，后台日志有 `event_write_failed`，模型没收到这句，没有用户输入记录。
- `diagnostic-unguarded` 变异（诊断写失败照旧抛出，即第二轮的行为）：`r4b-mutant-diagnostic-unguarded-claude`、`-codex` 都失败在 `unrecorded_submission_not_sent_to_model`，模型收到了 “failrec”。第一次跑（`r4-mutant-*`）测试在等日志那一步超时，没走到业务断言，所以把等日志改成固定等待后单独检查，重跑为 `r4b-*`。
- 绿态：`r4b-diag-claude`、`r4b-diag-codex`、`r4-fails-*`、`r4-claude`、`r4-codex`、`r4-t206`、`r4-reg-t216-provenance-claude`、`-codex` 都是 PASS。`r4-mutant-no-block-claude`、`r4-mutant-no-claim-codex` 照旧失败。`r4-*` 跑在改测试等待方式之前，那次改动只涉及 diagnostic-fails 一支，产品代码在 r4 与 r4b 之间没变。
- 跑完结束了 30 个夹具 core（T-232 根因）。另有两个 `/tmp/t78-pane-*` 夹具 core 不是本批留下的，结束操作被权限拦下，留给用户处理。

## 第一轮审查前的回归（`run-final.sh`，结果在 `runs.log`）

T-166 separate 与 absorbed（工作回合中的用户输入）、T-165 ordered（排队 Stop）、T-157、T-207（Esc 后的用户回合交付）、T-187 opencode 受管 worker 交付、T-216 issue-push（GUI）、T-216 provenance（Claude）：都是 PASS，没有失败的检查项。

## 偏差

1. `green-claude-01-dispatch-label`：派发正文前带 `⟦主控 #n⟧` 标签，测试按整段相等去等它，等不到。产品行为是对的，已认领。改为按包含判断后重跑。
2. `green-opencode-01-window-task`、`green-agy-01-window-task`：worker 窗口要带任务身份打开（`task=`），测试漏传。opencode 那次另有后台启动超时，当时机器上还有 Electron 回归在跑。
3. 第二轮绿态之后，`panes.ts` 又改了两处：钩子缺 prompt 的检查往前挪；一个辅助函数的位置。当时的说法“挪到改状态之前”不准确，第一轮审查指出检查仍晚于部分状态修改，第三轮已真正前移。第一轮审查前的整组测试（`final-*`、`reg-*`）是在那两处改完后跑的；最终候选以 `r3-*` 为准。
4. 跑完回归时发现，基于 `scripted_claude.Fixture` 的测试都会留下夹具的私有 hc core，T-229 自己的测试也一样。根因是 `Fixture.stop` 只停后台。主控手工结束了这些夹具进程（包括更早留下的 t078、t126 夹具 core），用户自己的 core（pid 87319、87320、87407）不受影响。T-232 已按这个根因改写。

## 没覆盖的

- 补全（Tab）后提交，没有单独的场景；它与 ↑ 走同一条钩子路径。
- 门禁反馈没有在 T-229 自己的测试里跑。回归现场里查过：`reg-t216-issue-push` 中，`gate` 来源的门禁反馈、`executor` 来源的主控答复、`user` 来源的用户答复派发各认领 1 次；`reg-t166-separate` 中的门禁反馈也认领了。两处的用户输入里都没有这些正文。`reg-t207` 的门禁反馈没被认领，用户输入里也没有它；它可能在测试结束前没有提交，没有核实。
- agy、opencode 只用了本地替身，没有在真实 CLI 上跑：记录在 attach 一侧完成，与 CLI 是否真的收到无关。
- 类型检查没有单独跑；产品代码由每次 e2e 的真实后台加载。
