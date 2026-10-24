# T-166 独立审查 01（agy，PASS）

启动参数：agy --model gemini-3.8-flash-high --mode auto --add-dir /Users/luckye/Documents/Code/a2a-review/T-166-r1 -i "$(cat /Users/luckye/Documents/Code/a2a-review/T-166-r1/prompt.txt)"
# pane wG:p24 started 2026-10-24T07:16:54Z candidate 206d3f60126fc1f0b26889fba33585b7d31471c0

以下为审查员窗格最终回复原文（去掉边框字符）。

T-166 独立审查报告

• 审查对象：候选提交 206d3f601（基线 a808c1137）
• 审查范围：workbench/src/panes.ts、workbench/README.
md、新增测试文件及相关验证证据
• 审查员身份：Enchanted（a2a）独立只读审查员（agy）
•
审查原则：写审分离、真实入口证据核对、最小根因层、无兼容垫片/重试兜底
──────
## 一、审查核对逐项结论

### 1. 根因分析与改动深度（最小根因层 / 架构整洁）

• 根因核对：正确。T-164 复现现场（Haiku worker
A）显示，用户输入发生在工作回合运行中（模型正在生成回复、执行工具，未
进入 Stop 批次）。Claude Code CLI 发送排队输入时复用了运行中回合的
prompt_id。修前（T-157）仅在 pane.stopInProgress
时允许该复用作为排队输入；工作回合期间（stopInProgress ===
false）坠入重复检查抛出 claude_prompt_id_reused，记录
native_question_unverified 导致回合身份不可信（currentTurnTrust 变为
unknown），随后该回合真正的 Stop
被拒（current_turn_untrusted），提交无法落地。
• 改动位置与深度：改动完全落在最小根因层 workbench/src/panes.ts：
1. panes.ts:1612：在 UserPromptSubmit 钩子处理中去掉 pane.
stopInProgress && 条件，使普通工作回合中的用户打字与 Stop
期间打字统一被识别为排队输入，保留原回合有效身份；保留了对用户
Enter
物理按键（terminal_input_write_intent/written）及转录真实路径的严
格核验。
2. panes.ts:1036：在 scan() 中加入 if (pane.active) return;
，防止工作回合仍在进行中（尚未完成原 Stop
结算）时提前消费转录而篡夺正在执行的回合身份。
• 坏味道排查：无吞异常、无
fallback、无自动重试、无兼容模式判断、无平行
API。改动直接修正状态机转换边界，非常干净。

### 2. 验收证据与期望值来源（真实入口 / 独立 Oracle）

• 真实入口测试：端到端测试 test_t166_busy_input_e2e.py 串接了真实
Electron 应用（经 CDP 驱动 window.a2a.input 输入）、真实 a2a
编排后台、真实 node-pty、真实 Claude Code CLI（v2.1.310）与脚本化
Messages
接口。在模型最终回复产生前截停并发送输入，测试严格核对了输入在 Stop
之前送达（input_precedes_original_stop）。
• 期望值来源：断言直接来自 T-166 Ticket
与构思主控转述的用户原则（20261024T030734Z-ideation-answer-
001）：“用户输入原样直达
CLI，只记人工介入；原回合交付照常通过；门禁核对不放松；不自动重试”。
• 关键断言完整性：
• 输入原样进入 CLI 下一次模型请求（sentinel
校验），字节未被改写（input_bytes_unchanged）；
• 原回合提交被门禁正常接受（original_submit_accepted），绑定原
attempt、commit 与 native turn；
• 记录人工介入且绑定原
attempt（human_intervention_bound_original_attempt）；
• 全流程仅一次
submit，无自动重试（exactly_one_submit_no_automatic_retry）；
• 输入引起的新回合由原生转录正常登记并完成，最终回归
idle（queued_native_turn_bound_and_completed、returns_idle）。


### 3. 红态与变异体检验（Evidence-First Testing）

• 修前红态复现：
• 在修前版本 a808c1137 上，test_t166_busy_input_e2e.py
运行两次（red-3、red-
4）：均准确复现缺陷（red_reproduced=true），失败于
original_submit_accepted、busy_input_not_judged_reused、original_
stop_trusted 等 8 项断言，重现了 T-164 真实事故现象。
• 早期因测试脚本等待条件不完备导致的两次超时异常（red-1、red-
2）已如实保留原始记录，无覆盖或抹除历史证据。
• 反例与已知坏实现（Mutants）：
• 反例 no-enter-reused：无对应用户 Enter 输入的 prompt_id
复用，修前修后均被拒并记录
claude_prompt_id_reused（test_t166_queued_input.ts:359-367）。
• 变异体 scan-ignores-active：移除 if (pane.active) return;
，模拟提前消费转录导致原 Stop 失配的坏实现，测试精准拒绝。
• 变异体 accept-without-enter：移除 check(enter,
'claude_prompt_id_reused');
，模拟无按键即放行的坏实现，在反例中被精准拒绝。
• 回归套件：RUN-REGRESSION-01.sh 涵盖的 14 项检查（含 T-157、T-
165、T-159、T-160、T-133、T-161 以及 3
个历史变异体）全部符合预期（正常测试 PASS，变异体 exit=1）。


### 4. 修改边界与文档文案

• 修改边界：严格控制在允许范围内（workbench/src/panes.
ts、workbench/README.md、新增测试文件与证据）。未改动
workbench/app/renderer.tsx、workbench/src/gates/**、AGENTS.
md、CONTEXT.md。
• 文档文案：workbench/README.md 第 757–762
行同步更新。文案准确描述了工作回合与 Stop
期间接收排队输入的统一语义、Enter 记录条件及转录建立新 turn
的时序，表述平实客观，属于纯技术规范白描，无任何营销腔。

### 5. 正确性、状态机流转与回归风险

• 时序完整性：Enter 检索逻辑以 turn_start_signal 或前一个
claude_prompt_queued 为界，支持同回合内多次排队输入的有序追加；
• 清理与释放：原回合 Stop 结算完成并清空 pane.active 后，后续无论是
PTY 输出触发 terminal.onData、钩子信号到达还是显式
processInfo，均能正常推进 scan() 登记排队 turn；若该排队 turn 的 Stop
先到，则顺利走 T-165 暂存逻辑，闭环完整。
──────
## 二、审查发现明细（Findings）

### [P3] 观察：scan() 转录行解析未引入多余防护，保持既有 fail-closed
契约

• 文件与行号：panes.ts:1040-1043
• 场景：scan() 逐行解析原生转录时，若遇到正在刷盘的不完整 JSON，JSON.
parse 抛出的异常会由调用方（如 terminal.
onData、processInfo）捕获并记录为 native_read_failed，不会静默吞掉。
• 结论：本实现沿用了 T-157
的既有设计，符合项目“不吞异常、不伪造状态”的原则，无需改动。

### [P3] 观察：执行主控自修模式下的任务授权记录

• 文件与行号：user-decision.md:14 / RESULTS.md:3
• 场景：因 Codex 额度耗尽，用户在 user-decision.md
中授权执行主控直接修复本票并由 agy 独立审查。本票未单独派发外部
worker 任务卡（无独立的 worker CARD.md），而是严格依据 Ticket（T-166-
￺busy-input-prompt-id-reuse.md）与公共修复约束（COMMON-FIX.md）执行。
• 结论：改动完全在 Ticket 规定的边界内，证据齐备，写审分离通过 agy
审查得到保证。
──────
## 三、审查结论

T-166
候选交付根因准确、改动克制精炼、断言独立且真实端到端证据充分、红态与
变异体闭环严密、回归测试全部通过。

T-166 REVIEW PASS
