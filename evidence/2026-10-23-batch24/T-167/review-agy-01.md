# T-167 独立审查 01（agy，PASS）

启动参数：agy --model gemini-3.8-flash-high --mode auto --add-dir /Users/luckye/Documents/Code/a2a-review/T-167-r1 -i "$(cat /Users/luckye/Documents/Code/a2a-review/T-167-r1/prompt.txt)"
# pane wG:p26 started 2026-10-24T07:43:55Z candidate 9baf0a77f9be7c4b1bbe6eb82f271862be9270b0

以下为审查员窗格最终回复原文（去掉边框字符）。

T-167 独立审查报告

• 审查对象：候选提交 9baf0a77f（起点 98e31ce0c，证据基线 73bd907d3 /
a808c1137）
• 审查范围：full.diff（覆盖
README.md:775-781、renderer.tsx:35-800、panes.ts:151-1498、sidebar.ts
:160-165、test_t167_codex_start_e2e.py:1-215）、T-167-codex-receipt-s
ubmit-lost.md、T-167/ 及其外置归档证据
• 审查员身份：Enchanted（a2a）独立只读审查员（agy）
•
审查原则：只读检查、写审分离、真实入口证据核对、最小根因层、无兼容垫
片/重试/吞异常/平行 API
──────
## 一、核心核对结论

### 1. 根因分析与改动深度（最小根因层 / 架构整洁）

• 根因核对：正确、精准且完整闭环。
• 现象再现：在 T-164 实测（launch 5314796c…，唯一 Codex worker
B）中，门禁回执在第一回合结束后写入并按回车（06:26:08），Codex
未发出 task_started，而是连写三条 thread_settings_applied
将模型由 gpt-6.1-sol high 切换为 gpt-6-luna
medium，新回合未开始；3
分钟后人工按回车才真正开始，且模型已被降级。
• 根因机理：Codex 0.163 在额度使用接近上限（实测
94%）时，在回合结束后弹出交互式提示（rate-limit-switch-
prompt：“Approaching rate limits / Switch to … for lower credit
usage?”），默认选项为切换小模型。a2a
随后写入的回执粘贴与回车直接答掉了该提示并确认切模型，CLI
没有将回车识别为新回合任务的提交；而后台 drain() 此前在写入 \r
后直接记录 turn_submitted 并标为 busy，造成后台状态与 CLI
原生真实状态脱节。
• 改动深度与最小根因层：
• 配置层（根因抑制）：在 panes.ts:746 为受管 Codex
会话启动参数显式传入 -c notice.
hide_rate_limit_model_nudge=true，与既有的 -c
check_for_update_on_startup=false
处于同等机制，直接抑制该弹窗，使后续任务输入不被窃取。
• 编排与观测层（真实状态对齐）：在 panes.ts:1314-1318 引入 20
秒超时判定（TURN_START_DEADLINE_MS），若 20
秒内未收到原生开始信号（turn_start_signal），记录
turn_start_missing；并在 panes.ts:1481-1496、sidebar.ts:163 和
renderer.tsx:450,462,798 中透出
start_missing，侧栏、窗格头与窗格提示如实反映“回合未开始”。
• 坏味道排查：
• 无吞异常、无自动重试、无替用户补按回车、无平行 API。
• 严格遵循用户原则：“不把 Enter
当默认批准、不自动重发；以原生回合开始为准”。

──────
### 2. 关键专项核对（用户重点指示项）

1. 根因证据链是否成立：
• 归档事件：T-164 实例 B 原生事件日志确证回执回车后紧随三条
thread_settings_applied（切换到 gpt-6-luna），且无
task_started，证实回车被提示消耗。
• Codex 二进制字符串：codex-cli 0.163.0 二进制中确有 rate-limit-
switch-prompt 相关文本及配置键 notice.
hide_rate_limit_model_nudge。
• 事实探针：探针脚本 probe_codex_nudge.py 在 PTY 中驱动真实 Codex
CLI，复现了额度 94% 时未隐藏提示被回车切换为
luna、隐藏提示后正常开始回合的对照事实。
• 端到端红态：在基线提交 a808c1137 上执行
test_t167_codex_start_e2e.py，真实 Electron + 后台 + PTY + 真实
Codex CLI 稳定复现红态（red-base.json，red_reproduced=true）。
• 结论：证据链严密、完整且相互印证。
2. 隐藏提示是否越权（只经启动参数、不写 home）：
• 核对 panes.ts:746：仅在 argv 数组中增加 "-c", "notice.
hide_rate_limit_model_nudge=true"。
• 绝对没有向 CODEX_HOME、~/.codex/config.toml 或 rules
写入任何文件。行为与已有的 check_for_update_on_startup=false
一致，未越权。
3. 20 秒判定有无误报或与 Claude worker 冲突：
• 判定逻辑：panes.ts:1316 检查 lastEvent(pane.record.id,
["turn_submitted", "turn_start_signal"])?.type !==
"turn_submitted"。
• Claude 与 Codex 正常时序：CLI 接受输入并按回车后，通常在 0.1
秒至 1 秒内触发 UserPromptSubmit hook 并生成
turn_start_signal。20 秒裕度极为充足（约 200
倍），不会因为正常思考或模型等待而误报。
• 自愈机制：若用户在 20 秒后手动处理弹窗并按回车，一旦
turn_start_signal 产生，panes.ts:1482 中的 startMissing()
查询最新一条事件将不再是
turn_start_missing，界面上的“回合未开始”标识与警告横幅自动清除。
• 回归证据：Claude worker 回归测试 t157-stop-input.json 与 t165-
ordered.json 结果均显示 start_missing: false，全部 PASS，证明对
Claude worker 无任何误报或冲突。
4. 界面文案检查：
• 窗格头与侧栏：清晰显示标签 回合未开始（data-start-missing）。
• 窗格状态横幅（renderer.tsx:462-464）：
“消息已写入终端并按了提交键，但 CLI

没有开始新回合。终端里可能有等待回答的提示，请查看终端并自行处理
；后台不会重发，也不会替你按键。”

•
文案客观陈述技术事实与用户操作建议，明确界定系统不自动重发、不替
用户按键的责任边界，完全无任何营销词汇或 AI 口吻。
5. 证据运行基线与未覆盖说明：
• 基线状态：证据运行在分支提交 73bd907d3 上（变基/合并到 main
前）。依既定流程，合入后会重跑回归。
• 未覆盖真实性：
• 特别声明：本票未用真实 Codex
复验（未调用厂商模型与真实扣额账号）。按用户与构思主控决议（2
0261024T072734Z-ideation-answer-001），真实 Codex 复验留待与
T-164 重跑集中进行，避免在修复阶段浪费有限额度。
• RESULTS.md 中如实记录：仅隐藏了弹窗提示，终端内仍保留 Codex
自身的额度告警文本（如截图中可见的 ⚠ Heads up, you have less
than 10% of your weekly limit left）；readWakeDelivery 仍以
turn_submitted 作为投递完成口径。


──────
### 3. 真实入口与独立 Oracle

• 真实入口测试：
• 测试 test_t167_codex_start_e2e.py 驱动真实 Electron
客户端（CDP）、真实 a2a 编排后台、真实 node-
pty、真实门禁派发以及真实 codex-cli 0.163.0。
• 模型端通过本地脚本化 HTTP 响应（x-codex-primary-used-percent:
94）提供精确协议桩，厂商模型回合为 0。
• 独立预期来源：
• 预期值直接来自 T-167 ticket
规格与用户原则：回执提交后原生回合必须启动且模型强度不可降级（rec
eipt_turn_started、worker_model_and_effort_unchanged）；提示阻断
时必须记录 turn_start_missing 并由 UI
如实告知，禁止重发或代为确认（len(pastes) == 1、len(intents) ==
1）。
• 预期非抄袭产品现有输出，具备独立鉴别力。

──────
### 4. 红态复现与变异体核验（Evidence-First Testing）

• 修前红态落点：
• 在修前版本 a808c1137 下运行：red-base.json 准确在
receipt_turn_started（started: false, starts: 0）和
worker_model_and_effort_unchanged（模型切换为
luna）双重断言失败，red_reproduced=true，截图 red-base.png
呈现现场停在 luna 且无新回合。
• 已知坏实现（变异体）：
• 变异体（no-start-check）：将 panes.ts:1316 的超时开始检查直接
patch 为 return;
，模拟“仅写入回车、完全不监测是否真正启动”的失责实现。
• 运行 mutant-no-start-check.json：精准且仅在
start_missing_recorded、pane_status_says_not_started、sidebar_say
s_not_started、pane_header_says_not_started
四项呈现检查上失败（exit 1），有效拒绝了假装正常处理的坏实现。

──────
### 5. 修改边界与回归测试

• 边界受控：本次改动仅修改 workbench/ 内部 4
个文件（文档、panes、sidebar、renderer）及 1 个测试文件，full.diff
352 行。没有修改门禁核心、没有修改 home 目录配置、没有修改其他无关
CLI。
• 回归套件（RUN-01.sh 全部 PASS）：
• build：Electron 前端与后台打包正常（exit 0）。
• t157-stop-input：Claude worker
停止期间输入的端到端验证通过（exit 0）。
• t165-ordered：排队输入顺序与 Stop 交互验证通过（exit 0）。
• t127：Codex home 隔离与配置继承验证通过（exit 0）。

──────
## 二、审查发现列表

序号 │ 文件与行号         │ 严重… │ 发现与场景说明
──────┼────────────────────┼───────┼─────────────────────────────────
1    │ panes.ts:1274-128 │   P3   │ readWakeDelivery
投递判定与界面显示口径存
在语义细分差失败场景/行为
：readWakeDelivery
目前仍通过 type IN
('turn_submitted', ...)
判定投递状态为
delivered。当某个收件箱唤
醒消息写入终端后若发生
turn_start_missing，发送
者查询投递状态仍会得到
delivered，而界面与侧栏则
如实提示“回合未开始”。作
者在 RESULTS.md
中已将此如实列为“未覆盖”
，当前优先保证工作台直观
状态如实反映，对系统核心
无害。建议未来视通信层演
进统筹收敛。
2    │ panes.ts:1307renderer.ts │  P3   │ 20
x:447                    │       │ 秒超时前窗格呈现短暂的“忙
”状态失败场景/行为：在消
息写入并回车后到 20
秒超时判定触发前的窗口期
内，pane.state 为
"busy"。若 CLI
秒后才会跳出“回合未开始”横幅
。这是平衡调度/网络抖动避免
误报的必要工程取舍，20
秒时限合理，行为符合预期。
3    │ RESULTS.md:4          │  P3   │ 证据基于合并前分支提交生成，
合入后需按规重跑失败场景/行
为：候选运行证据基于提交
73bd907d3（此时 T-166 与 T-
168 尚未合入
main）。代码层面与已合入的
T-166/T-168
无逻辑冲突，但合并后仍须按项
目规则重跑 wave
回归以完成证据闭环。
──────
## 三、最终审查结论

T-167 的根因分析准确定位了 Codex 0.163
额度接近上限时换模型弹窗答掉任务回车的物理机理；修法在启动参数层隐藏
弹窗、在状态层以原生开始信号为准做超时如实告警，严格遵循“不默认批准、
不自动重发、不替用户按键”原则，未越权触及用户 home
目录；修前红态落点精确，坏实现变异体被有效拒绝；Claude worker
粘贴提交无回归；报告按用户决定明确写明“未用真实 Codex
复验”，未覆盖项如实记录。审查结论为通过。

T-167 REVIEW PASS
