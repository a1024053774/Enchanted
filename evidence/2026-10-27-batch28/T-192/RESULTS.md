# T-192 结果：任务页显示门禁全程，已结束的票不再是空页

用户 2026-10-27：“先做 T-192 任务页显示门禁全程。”问题来源 findings U07、U08。

## 根因

- 空页：没有保存过布局的任务，界面放一个“跟随当前 attempt 的 worker”的默认窗格（`app/main.ts`，`launches = [undefined]`）。attempt 回收后没有当前 attempt，这个窗格就是空的，盖住整个任务页，下面只剩一行门禁状态。`ui/02-red-placeholder-pane.jpg` 是修前同一状态的画面（窗格“尚未启动窗格”）。
- “待认领”：门禁没有关闭状态，回收后任务回到 ready。

## 改动

- 门禁 `task_history`（只读）：`src/gates/taskHistory.ts` 把事件整理成步骤（认领、启动 worker、交付、路径检查、验收文件、完成条件、尾注、验收、审查、打回、集成、打分、上报问题、撤销、回收、关闭、门禁拒绝），以及最近一次审查结论与问题、打分、集成提交与该候选的尾注、关闭理由。草拟任务卡、读状态与 verify 被拒不进时间线（verify 的结果已由验收与打回两步表达）。
- 门禁 `close`：必须写理由；只允许 ready、无当前 attempt、无集成意图的任务；关闭后 claim/dispatch 拒 `task_closed`；不能重开。
- 界面：没有当前 attempt 的任务不再放空窗格，整页显示 `app/TaskRecord.tsx`；有窗格时记录收在底部“门禁记录”。状态名补“已放弃、已升级、已关闭”。
- 主控 SKILL.md 加 `close` 与 `task_history`；工作台 README 记任务页与关闭语义。

## 证据

隔离后台 `/private/tmp/t190/state`（T-190 的夹具），经 `call.ts` 走真实后台入口。

- 红态（修前代码）：`red-tasks-after-revoke.json` 撤销后为 `ready`；`red-close.json`、`red-history.json` 两个命令都不存在。
- 绿态：`green-close-empty-reason.json` 空理由拒 `invalid_text`；`green-close.json` 关闭成功；`green-tasks-after-close.json` 为 `closed`；`green-dispatch-closed.json` 拒 `task_closed`；`green-close-twice.json` 拒 `close_requires_idle_task`；`green-history.json` 含关闭理由与此前的 `spawn git ENOENT` 拒绝。
- 整理函数：`history_check.ts` 读 `history-fixture.json`（用户真实状态库的只读导出：lcu T-2 与 a2a T-138 的事件，去掉 command_intent/result、human_intervention 与内嵌任务快照）。期望来自 findings（lcu 报告：独立审查打回一次、集成到 9312a70；U07：T-138 回收、未集成），不取自实现输出。`history-check-green.json` PASS；`mutants.sh` 生成六个已知坏实现（集成提交取 C、不过滤草拟拒绝、漏掉回收、只留最后一次审查、过滤全部 verify 拒绝、漏掉规则检查），各自 FAIL：`history-check-mutant-*.json`。
- 界面（打包的 Enchanted Test，`node app/package.mjs --slot t192pkg --variant test`，Computer Use 截图）：`ui/01-grid-closed.jpg` 任务格“已关闭”；`ui/03-closed-task-record.jpg` 已关闭任务整页显示关闭理由、任务卡与时间线；`ui/04`、`ui/05` 已集成任务显示审查、打分与理由、集成提交、尾注与按 attempt 分组的时间线。04、05 的任务是夹具：在隔离项目 lcu 经门禁建 T-2，再在后台停止时把 lcu T-2 的真实事件写进该任务的事件表（只写事件，不写 attempt，任务本身状态仍为待认领）。

## 审查第 1 轮（Codex `gpt-6.1-sol` high，`codex exec` 只读审查，报告 `review-01/REPORT.md`）

结论“需修复”，6 项，逐项处理：

| 编号 | 问题 | 处理 | 复验 |
| --- | --- | --- | --- |
| F1 P1 | 已关闭任务可经 revoke/revise 回到 ready | revoke/revise 先拒 `task_closed` | `green2-revoke-closed.json`、`green2-revise-closed.json` 均拒，`green2-tasks-beta.json` 仍为 closed |
| F2 P2 | 零窗格页面不跟随：之后派发看不到新 worker；门禁栏停在旧状态 | 记录页发现新的当前 attempt 时以 refresh 重新取视图（`a2a:select-task` 的 refresh 跳过“已选中”捷径）；零窗格时不显示门禁栏，记录页自己显示实时状态 | 停在 lcu T-2 记录页时经后台 claim，8 秒内页面自行换成窗格加底部记录（`green2-claim-while-viewing.json`、`ui/07`），展开底部记录 `ui/08` |
| F3 P2 | 按命令名过滤全部 verify 拒绝，藏掉独有原因；merge_failed 的 details 形状没认 | 只折叠紧跟在同一 attempt 失败步骤后的 verify 拒绝；`verification_result` 兼容两种写法；新增“合并冲突”步骤列出文件 | `history_check.ts` 反例：验收前 `git_failed` 保留；合并冲突只出现一次并带文件 |
| F4 P2 | red_check、rule_check 不进时间线 | 映射为“红态检查 N”“规则检查 id” | 反例断言；变异 `no-rule-check` 被检出 |
| F5 P2 | 只留最后一次审查结论，报告与建议丢失 | `reviews` 保留每次审查的结论、问题、建议与报告；界面逐次可展开，最近一次默认展开 | 真实 T-2 两次审查断言；`ui/06`；变异 `last-review-only` 被检出 |
| F6 P3 | 产品页仍写“点一张票，进入 agent 分屏” | `docs/index.html` 第 3 步改为分别说明有会话与没会话两种页面 | 文字对照 |

证据整理：第 1 轮报告指出 `green-history.json` 早于最终过滤规则（仍含草拟任务卡的拒绝），保留原样作为当时输出；最终入口输出见 `green2-history-beta.json`。早先手工生成的三个变异结果（含一个 0 字节文件）被我在改为可重跑脚本时删除，现由 `mutants.sh` 重新生成六个变异结果，均 FAIL；被删的原文件没有保留，这里如实记录。

## 审查第 2 轮（新会话，同模型，报告 `review-02/REPORT.md`）

F1、F4、F5、F6 判 PASS；F2、F3 部分修复，新提 R1～R5，结论“需修复”。处理：

| 编号 | 问题 | 处理 | 复验 |
| --- | --- | --- | --- |
| R1 P2 | 回收后留下已存空布局，刷新仍不出新 worker | 放弃“记录页自动刷新视图”的做法 | 见下 |
| R2 P2 | 首次读取前出现的新 attempt 被当作基线，永不刷新 | 同上 | 见下 |
| R3 P2 | 轮询保留挂载时 busy=true 的旧回调 | 同上 | 见下 |
| R4 P2 | 任意前一失败步骤都会折叠 verify 拒绝 | 只在前一个非命令簿记事件是同一 attempt 的打回（错误码相同）或合并冲突时折叠 | `history_check.ts` 新增两条：无关的 integrate 失败后 verify `git_failed` 保留；打回后同码 verify 拒绝折叠；变异 `any-previous-failure` 被检出 |
| R5 P3 | README 说所有 verify 拒绝都隐藏 | 改写任务页一段，写明显示条件、逐次审查与有限折叠 | 文字对照 |

R1～R3 的新做法：记录页不再自己切换视图。每次轮询看当前 attempt 有没有 worker 会话（`runtime_identity.launch` 且侧栏已有该会话），有就在页内显示“打开 worker 会话”，点击走侧栏点会话的同一路径（`selectAgent`）。按钮由当前状态决定，没有基线、旧回调或已存布局的问题，也不替用户重开他关掉的窗格。第 1 轮加的 `select-task` refresh 参数随之删除。

真实入口复验（打包的 Enchanted Test，新构建）：lcu T-2 撤销探针 claim 后停在整页记录；经后台 `dispatch`（`green3-dispatch-while-viewing.json`）派真实 Claude Code worker（argv `--model claude-haiku-5-5 --effort low`）；不做任何导航，页面显示“已认领”和“打开 worker 会话”，侧栏出现该 worker（`ui/09`）；点击后 worker 窗格打开，底部为“门禁记录 · 已认领”，门禁栏为已认领（`ui/10`）。`history-check-green.json` PASS，`mutants.sh` 七个变异全部 FAIL。

## 审查第 3 轮（新会话，同模型，报告 `review-03/REPORT.md`）

旧 F1～F6、R1～R5 的主要修复判有效；新提 N1～N4，结论“需修复”。处理：

| 编号 | 问题 | 处理 | 复验 |
| --- | --- | --- | --- |
| N1 P3 | 合并冲突后有冲突反馈事件，上一轮“前一个非命令事件”规则失效，同一冲突的拒绝重复显示 | 根因：折叠依据的是事件相邻，而不是那次验收本身。改为每个 attempt 记下最近一次验收的打回错误码或合并冲突，第一个 verify 拒绝与之同码才折叠，用过即清；新交付或新验收清除 | `history_check.ts` 加三条：按 core.ts 实际顺序（冲突、rework、feedback intent/delivered、清理）后的拒绝只显示一次；冲突后不同错误（git_failed）保留；同码第二次拒绝不折叠。变异 `feedback-breaks-fold`、`fold-not-consumed` 被检出，九个变异全部 FAIL |
| N2 P3 | 产品页以“有会话在跑”区分页面，与按钮方案不符 | 改为按是否有打开的窗格区分，并写明点“打开 worker 会话” | 文字对照 |
| N3 P3 | 界面忙时按钮可点但点击被丢弃 | 按钮按同一个 busy 禁用；README 注明 | 只有代码对照，没有在界面里制造忙碌状态复验 |
| N4 P2 | green2、green3 回执被截断；没有真实回收后的整页记录 | 两份截断文件保留原样不覆盖。补了 green4 系列完整回执，见下 | 见下 |

`history-check-*.json` 每轮都按当时代码重新生成，之前的变异结果被覆盖（由 `mutants.sh` 可重跑）；`any-previous-failure`、`drop-all-verify` 两个变异按新写法改了替换位置。

N4 的真实入口复验（隔离 lcu T-2，打包的 Enchanted Test 新构建）：

- `green4-status-submitted.json`：真实 Claude Code worker（`green4-launch.json` 记完整 argv：`--model claude-haiku-5-5 --effort low`）交付 0933c7e。
- `green4-verify.json`：verify 拒 `oracle_failed`，`check_readme.py` 不存在。这是我建夹具时漏了验收程序，不是被测代码的问题。worker 上报问题，说明这是验收程序、不在可改路径内，不会自行补。
- 我按卡的目标独立写了 `check_readme.py`，提交到夹具集成分支 work/demo（2083850）：基线退出 1，候选 README 退出 0。经 `answer_issue` 回复 worker（`green4-answer-issue.json`）。我在回复里让它变基，这是错误指示：沙箱按设计拦了 Git 元数据，worker 停下说明。随后两次 `pane_dispatch` 更正（`green4-dispatch-correction.json`、`green4-dispatch-commit-reminder.json`）：第一次它在沙箱内 git commit 被拒，按卡停下；第二次发出后，截止我停手时没有出现在它的屏幕上，也没有新交付。
- 推动这个 worker 不属于 T-192，于是在这里收尾：`green4-revoke.json` 撤销，`green4-reclaim.json` 回收，worker 进程退出。
- `green4-history-after-reclaim.json`、`green4-tasks-after-reclaim.json`：任务回到待认领、没有当前 attempt。第 5 次执行尝试的时间线依次是认领、启动 worker、交付、路径检查、验收文件、完成条件未通过、验收未通过、打回 oracle_failed、上报问题、撤销、回收。紧跟打回的同码 verify 拒绝（seq 406）只显示一次。
- 界面：从项目任务格点进 T-2，整页记录，没有“打开 worker 会话”（`ui/11`），时间线末尾与回执一致（`ui/12`）。

## 审查第 4 轮（新会话，同模型，报告 `review-04/REPORT.md`）

第一次运行中途模型报 “Selected model is at capacity”，没有写出报告，日志归档到外置盘，仓库留清单 `review-04/codex-attempt1-capacity.archive.json`；同配置重跑一次得到报告。N2、N3、N4 判已修；N1 同 attempt 路径已修，新提 1 项，结论“需修复”：

| 编号 | 问题 | 处理 | 复验 |
| --- | --- | --- | --- |
| Q1 P3 | 冲突后更换 worker 时，verify 拒绝写入时当前 attempt 已是新的 B，整理按事件行的 attempt 查不到 A 的冲突，于是在 B 下重复显示，且更换本身不显示 | 根因：事件行的 attempt 列是写入时的当前 attempt，不是那次验收的 attempt。verify 拒绝的 details 里带着它报告的那次验收的 attempt（`details.attempt.attempt_id`，green4-verify.json 里也有），整理改按它关联与归属；core.ts 不改，事件表不改。`conflict_worker_replaced` 显示为“合并冲突后更换 worker · 新执行尝试 …” | `history_check.ts` 按审查给出的实际顺序加替换场景：B 下不出现旧拒绝、更换可见；反例：B 自己的验收拒绝不被 A 的冲突折叠。变异 `row-attempt`（改回事件行 attempt）被检出，十个变异全部 FAIL。真实 lcu T-2 事件用新代码整理，与 `green4-history-after-reclaim.json` 的 63 步逐项一致 |

界面截图 `ui/11`、`ui/12` 用的是 Q1 修改前的构建；最终构建的同一页面见 `ui/13`。

## 审查第 5 轮（新会话，同模型，报告 `review-05/REPORT.md`）

Q1 的拒绝关联判有效；新提 1 项，结论“需修复”：

| 编号 | 问题 | 处理 | 复验 |
| --- | --- | --- | --- |
| S1 P3 | 时间线只在某个 attempt 第一次出现时标题；冲突更换 worker 后 A 的“更换 worker”出现在 B 之后，没有 A 的标题，看起来属于 B。我的夹具把这一步写成 B，与 core.ts 显式记为 A 不符，所以上轮检查漏了 | 标题规则抽成 `taskHistory.ts` 的纯函数 `attemptStarts`：与上一个有 attempt 的步骤不同就标题，回到 A 也重新标；编号仍按首次出现（A 第 1 次、B 第 2 次），不出现第 3 次。没有 attempt 的步骤不拆开所在的 attempt。`TaskRecord` 改用它。夹具改正为 A | `history_check.ts` 断言 A→B→A 三处标题与“更换 worker”归属 A，以及无 attempt 步骤不拆分；变异 `first-appearance-header`（恢复旧规则）只在标题断言上失败。十一个变异全部 FAIL。真实 lcu T-2、beta T-1 的标题与此前相同（5 个、1 个），最终构建截图 `ui/13` |

## 审查第 6 轮（新会话，同模型，报告 `review-06/REPORT.md`）

S1 判已修：替换成功、替换建立 B 后失败、建立 B 前失败三条路径，组件标题依次为 A=1、B=2、A=1，没有第 3 次；无 attempt 的步骤不占编号。抽查之前各轮修复没有回退。结论“可合并”。审查员写明这次 PASS 只覆盖本轮指定的复核范围，不代表 T-192 的端到端验收已全部通过。

## 收尾

隔离测试应用、它的后台和构建目录已清理；T-190 留下的空闲界面检查 codex（pid 16018）也已结束。T-191 早先留下的三个构建目录一并删除。夹具 `/private/tmp/t190` 保留，供复跑。

## 没有验证

- 停在记录页时派发新 worker 不会自动切到窗格，需要点“打开 worker 会话”；这是第 2 轮后有意的取舍。
- 真实回收这一条走的是“交付、验收打回、上报、撤销、回收”，没有经过独立审查与集成；页面上审查、打分、集成提交、尾注的内容仍来自注入真实事件的夹具（lcu T-2 早先的 attempt）。
- N3 的忙碌禁用没有在界面里复验。
- 用户真实的 a2a+T-138：没有在用户状态里操作，也未关闭。
- 并发与崩溃恢复下的 close：只有审查员的静态核对。
