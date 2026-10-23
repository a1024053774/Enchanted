# T-155-1 / a1：真实使用运行记录

状态：INCOMPLETE。模型执行已停在真实阻断：两票被独立审查输出协议暂停，一票在运行中人工介入后交付被拒、界面状态未知，无任何集成。两 worker 并行、问题答复、真实打回与修复重交、记录/指标/Reflect、同后台 UI 重开已实际走到；最终停止读回、37 个根回合核对和外置盘归档均已完成。不能以“报告写出”替代完整流程通过。

## 版本与启动

- 产品基线：`f3412fb4ae5cfa3c4983440eb26ea8c5b34b0697`；分支 `exec/t155`。本票只改证据目录，没有产品改动。
- 原计划提交：`ad72bc2ec2f1c2c49f4b5be721e6306d55287144`。
- 实例 1：`/private/tmp/t155-dogfood-lv2rm2nt`。主控在沙箱外运行 `START-APP.sh` 成功并于消息 #17 交接；Electron PID 73231、daemon PID 73230。
- Computer Use 用完整路径 `/Users/luckye/Documents/Code/a2a-wt-t155/workbench/node_modules/electron/dist/Electron.app` 绑定。首屏 AX 中的 renderer URL 指向该实例构建目录，窗口标题 Enchanted。
- Claude 启动命令：在界面项目终端中输入 `claude --model claude-haiku-5-5`；屏幕显示 Claude Code v2.1.309、Haiku 5.5、Claude Pro。

## 实例 1 与启动准备缺陷

项目打开、终端启动、执行主控申请与界面批准已走到。两个受管任务 T-A / T-B 已注册，但派发报 `launch_config_required`，没有 worker 窗格或启动记录。两任务仍显示准备中；流程页为阶段未知，任务页为空的只读窗格。

事后只读核对发现本票启动脚本遗漏 `--launch-config`。正式桌面入口 `workbench/app/desktop.mjs` 会配置 CLI、角色卡、版本、hook 授权和回合上限；原脚本仅 daemon_start，默认空配置。这是测试准备缺陷，不能据此认定正式产品无法派发。原始实例和失败截图完整保留，没有修复、恢复或清理其 attempt。

修订只补本票脚本的启动配置，按产品入口字段只配置 Claude、每会话 6 回合；不读取 Codex auth、不改用户配置。新实例 `/private/tmp/t155-dogfood-ohzs_78v` 的启动已由主控消息 #18 确认，两个 worker 实际同时运行（图 26），因此启动配置修订取得了真实入口的前后对照；不代表整个多 agent 流程通过。以下为当时的重启命令，主控已执行：

```sh
bash evidence/2026-10-23-batch24/T-155/STOP-APP.sh /private/tmp/t155-dogfood-lv2rm2nt --all
bash evidence/2026-10-23-batch24/T-155/START-APP.sh /private/tmp/t155-dogfood-ohzs_78v
```

以上停止与启动由主控沙箱外执行；旧实例停止后继续保留现场，不删除。原始 run 目录不纳入 Git，最终按 T-088 归档，状态以文末最终记录为准。

## 截图索引

图片在 `screenshots/`。截图内容优先于文件名；动作后即时截图偶有前一帧，已显式标明，不据此声称对应步骤完成。

| 图 | 画面 / 证明范围 |
| --- | --- |
| 01-window-ready.png | 隔离窗口空项目首屏 |
| 02-project-open.png | 测试 repo 已出现在项目侧栏 |
| 03-cli-launch-input.png | 指定 Claude 命令与测试 repo 的 workspace trust 提示 |
| 04-fixture-trust-selection.png | 只选择信任该一次性 repo，尚未确认 |
| 05-cli-ready.png | 实际为初始化过渡帧，不能证明 CLI 已就绪 |
| 06-role-request-progress.png | Claude 申请执行主控；编号卡片与窗格框对应 |
| 07-role-approved.png | 界面批准后显示等待 CLI 确认 |
| 08-flow-before-workers.png | 无任务时流程页空状态与未归属解释 |
| 09-records-after-role.png | C2 需求已完整记录，1 条主控终端提交 |
| 10-reflect-before-tasks.png | 主控会话树、复盘入口与默认关闭的定期复盘 |
| 11-dispatch-progress.png | 实际仍为 Reflect 切页前一帧，不作为派发证据 |
| 12-task-registration.png | T-A / T-B 准备中，主控正在轮询派发错误 |
| 13-dispatch-errors-expanded.png | preparing 状态；Claude 的 sleep 45 被其工具规则拒绝后改用 read 轮询 |
| 14-worker-start-failure.png | 实际为展开的任务状态与任务卡，不包含首次错误，不能单独证明失败原因 |
| 15-launch-config-required.png | C3 解释 preparing 与无 worker；首次错误全文在同回合上方，精确错误另由事后源码核对 |
| 16-preparing-without-worker.png | T-A 准备中、尚未启动窗格、只读未知；没有启动失败原因入口 |
| 17-flow-after-start-failure.png | 两条任务泳道均阶段未知、无 worker，主控未归属 |
| 18-first-dispatch-error-text.png | 实际为 C3 尾部，只看到 already_claimed 与 preparing 解释，未滚到首次错误 |
| 19-dispatch-error-details.png | 去掉 max_turns 后的派发仍为 already_claimed；其余为 C3 解释 |
| 20-error-commands.png | 快捷键尝试后的相同终端位置，不提供额外证明；完整保留 |

## 回合、输入与介入

界面中实际提交 3 个主控提示：C1 申请身份；C2 拆分和并行派发；C3 停止轮询并只读报告错误。C2 经界面 Escape 中断。原文或摘要见 `SESSION-NOTES.md`；C2 原文在记录页截图 09 中可核对。

尚未有应用内 worker / reviewer / Reflect 回合，未开应用内 Codex。当前“3”是可见根提示提交数；完整后台事件与原生回合统计尚未在停止后的只读证据中核对，不能将此升级为完整精确计数。全局上限仍是应用内 60 回合。

只对屏幕明确指向测试 repo 的信任提示操作 Down、截图核对后单独 Enter；执行主控卡片的批准也是本票计划内操作。没有系统隐私授权、登录、付款或越界操作请求；没有需要主控代批的系统权限。没有经 shell、CDP、DOM 或数据库驱动业务流程。

## 实例 1 截止时未完成（后续结果见实例 2）

两个 worker 真正并行、worker 问题页答复、受控打回与重交、worker 窗格人工介入、多窗格滚动切换、独立审查、集成、带结果的指标与 Reflect、UI REOPEN、新隔离实例复现、正式中文发现报告、最终证据归档和独立接受性审查均待后续运行。

项目地图在本阶段交接前检查：Problems 0、Stale living docs 0。此结论只证明地图结构，不证明多 agent 能力通过。

## 实例 2：真实运行与截止点

主控消息 #18 确认旧实例 UI 与 daemon 全停、目录保留；新实例 Electron PID 83084、daemon PID 83082。每会话 Claude hooks 已由主控代批，引用批次 `evidence/2026-10-23-batch24/approvals.jsonl`；本 worker 不写该文件。没有系统隐私、登录、密码、付款或其他越界代批。

通过 Computer Use 打开新 repo、启动同一 Claude 命令、仅信任该 repo、申请并批准执行主控。C5 让主控并行派发 T-101 库存汇总、T-102 补货单；C6 补 T-103 草稿演练。所有业务操作仍经屏幕与 app 内主控完成。事后源码/公开 README 与停止后的数据库副本只用于解释观察，未用于直接改业务状态。

| 检查 | 结果与实际证据 |
| --- | --- |
| 两 worker 同时在跑 | PASS（本场景）：图 26 侧栏两项运行中，图 27 为真实 worker 输出 |
| 问题上报与回复 | PASS（有人工提醒）：B 起初未按卡上报，提醒后问题页出现卡片；面板答复送入正确 worker 并确认，图 30/31 |
| worker 人工输入 | PASS（本场景）：图 28 为完成后介入；图 37 是 Stop 忙碌期间介入，随后变未知，不能说结果正常 |
| 真实打回及修复重交 | PASS（发生事实）：T-101 a1 被独审拒绝；a2 被 oracle_failed 拒绝后，在同 attempt 中提交第 2 个候选，图 52 |
| 新独立审查 | 已实际运行 4 个干净审查会话；1 个需修复结果被接受，3 个 fenced JSON 被 review_json 暂停。没有可用于集成的审查通过 |
| 集成、打分 | INCOMPLETE：没有任何任务 verified/accepted，没有 score_file、integrate 或 push |
| 切换、分屏与滚动 | 已实际操作；侧栏能切换，但只读窗格出现输入错误，向右分屏未保留原 worker，图 33/34/41/50/51 |
| 流程、记录、指标 | 已查看真实多任务状态；数据与未知/无数据的限制见图 32/35/45/56 与报告 |
| Reflect | PASS（只指产物生成）：选择 Haiku，手动复盘实际写报告，页面已完成，8 条建议未批准/执行，图 43/46/47 |
| 新实例复现一条发现 | PASS（发生事实）：两个全新 root 的角色批准都未出现在输入记录；两实例停止读回均确认批准事件存在、输入记录缺少批准 |
| UI 关闭再重开 | PASS（同后台 UI-only）：主控 #19 执行，旧 UI 83084 停止，新 UI 14775，daemon 仍 83082；图 57～61 核对持久状态。未测试 daemon 重启 |

最终业务状态：

- T-101：a1 `cdb29d08-9752-491d-9da4-358ca1d2fba4` 经 revise 失效；a2 `38eb5051-8098-44bf-9cf9-cc3e855be20d`，fence/spec_rev/card_version 均为 2。首候选 b1064d9 被格式检查打回；修复后的当前候选 `ee215d7d8c0b0ba44234f6490ffa093304e5be35`，新机械验收通过；新 reviewer `478e9d92-17ce-47d8-b802-06dae3cde3ad` 输出可合并但协议无效。task 暂停，attempt submitted。
- T-102：a1 `35b623e3-deeb-4c0c-b8d3-2dd97077481c` 经 revise 失效；a2 `bf538441-c264-4d52-a200-fc63a650cee1`，fence/spec_rev/card_version 均为 2。当前候选 78992b3，机械通过，reviewer `3f31cbf3-230a-4715-9c08-c3801e37930e` 协议无效。task 暂停，attempt submitted。
- T-103：`bf95a30d-84ad-4521-a02a-8f5a2251b537`，task/attempt claimed，worker 分支有草稿提交 4c9ade9，但门禁无已接受候选或验收。未重发未知写入。
- main 仍为种子提交 `13f0524...`。旧 worktree、审查目录、refs 和失败结果保留；没有 abandon/reclaim、清理、强制解除锁、直接改库或 push。两次 a2 重试用了主控先前提出、测试者明确选择的 overlap_reason；没有隐藏由旧 revoked attempt 引起的 path_overlap。

## 实例 2 截图续表

| 图 | 画面 / 证明范围 |
| --- | --- |
| 21-instance2-ready.png | renderer 来自新实例，空项目首屏 |
| 22-instance2-trust.png | 只信任新测试 repo 的选项 |
| 23-instance2-role-request.png | 编号角色申请与目标窗格 |
| 24-role-confirmed-header.png | 侧栏执行主控、窗格头普通终端 |
| 25-metrics-before-workers.png | 新 worker 已登记、原生模型尚未知的早期指标 |
| 26-two-workers-running.png | 同时运行的两 worker 与项目任务卡总览 |
| 27-worker-a-active.png | worker 实际写库存文档，数字与总计可见 |
| 28-worker-manual-input.png | A 收到完成后的人工介入并保持提交不变 |
| 29-controller-after-dispatch.png | 主控承认未把首版漏总计写入 A 卡 |
| 30-worker-issue-answer-draft.png | worker 上报与问题答复输入 |
| 31-issue-answer-received.png | B 终端收到答复并确认 |
| 32-two-independent-reviews.png | 两票各自独立审查阶段 |
| 33-reviewer-focus-error.png | 只读 reviewer 查看触发输入错误，终端重叠显示 |
| 34-second-reviewer-readonly-error.png | 第二 reviewer 同样错误，显示变异测试发现 |
| 35-records-human-interventions.png | 真实根提示、键入/回车、面板答复的记录 |
| 36-review-problems-and-duplicate-numbers.png | T-101 的 worker 审查问题与 T-102 的 system 协议阻断，原文留存；两卡分属不同任务，不是同任务编号冲突。T-102 分组问题见图 30，未在本图并列 |
| 37-worker-c-busy-before-input.png | T-103 输入前确处于 Stop 忙碌阶段 |
| 38-controller-review-stops.png | 主控报告两票弱验收及等待修订授权 |
| 39-input-during-stop-unknown.png | T-103 回复 done 后交付仍未落地，状态未知/忙 |
| 40-unknown-pane-menu.png | 未知窗格无明确恢复入口 |
| 41-task-split-result.png | 向右分屏后变新普通终端，仍是旧任务上下文 |
| 42-controller-recovery-progress.png | 主控再次长轮询未知状态的实际命令 |
| 43-reflect-session-tree.png | 真实会话树、实际模型/未知主控、复盘 Haiku 设置 |
| 44-controller-bounded-diagnosis.png | repair_submission_required、not_submitted 与 T103 无交付事实 |
| 45-metrics-with-real-turns.png | managed 当时 14 回合，主控 0 |
| 46-reflect-terminal.png | 复盘实际写中文 report.md，不是只有启动记录 |
| 47-reflect-completed.png | 复盘已完成及报告路径、建议仍待决定 |
| 48-revise-progress.png | revise 成功后自己的旧 attempt 仍造成 path_overlap |
| 49-retry-queue-check.png | revoked 与队列核对后仍需人工确认旧 CLI 空闲 |
| 50-revoked-worker-a-idle.png | 旧 A 历史只读、空闲、done，仍有输入失败横幅 |
| 51-revoked-worker-b-idle.png | 旧 B 历史只读、空闲、done |
| 52-worker-repair-new-candidate.png | A2 第 2 次交付已被门禁接受为 submitted |
| 53-repaired-candidate-review-progress.png | 主控重验时任务已暂停，仍在等待循环 |
| 54-mergeable-review-rejected-protocol.png | 新 reviewer 可合并的原文仍因 fenced JSON 被拒 |
| 55-controller-end-state.png | C13 只读汇总，明确未集成、未清理和预算限制 |
| 56-final-metrics-before-reopen.png | 9 个 managed 会话共记录 22 回合；完整文本另存 metrics-before-reopen.ax.txt |
| 57-reopened-isolated-window.png | 重开同一 renderer，默认选择独立终端，侧栏角色和会话保留 |
| 58-reopened-terminal-restored.png | 重新选主控后，C13 最终输出、main 种子与阻断状态可读 |
| 59-reopened-flow-persisted.png | 同一任务阶段、打回轨迹、T-103 未知和旧 attempt 未归属均保留 |
| 60-reopened-reflect-persisted.png | Reflect 会话树与原有结果仍可访问；AX 同时核对已完成记录及 8 条待决定建议 |
| 61-reopened-user-records.png | 全部筛选下仍为 17 条记录、8 条人工介入；未新增模型提示 |

## 累计回合与权限口径（停止后终核）

停止后只读统计本票专属原生 JSONL，共 12 个会话、37 个根回合，全部 assistant model 字段为 `claude-haiku-5-5`；预算核对 PASS（只指本口径 37 ≤ 60）。逐提示 UUID、时间及来源文件见 `native-turns.json`，脚本为 `count_native_turns.py`。不把消息编号、工具调用次数或配置上限当回合数。

| 会话 | 实际根回合 | 计数说明 |
| --- | --- | --- |
| 旧实例主控 C1～C3 | 3 | 含 C2 被 Esc 中断的原提示 |
| 新实例主控 C4～C13 | 10 | 含 C7 被 Esc 中断的原提示 |
| T-101 a1 / a2 worker | 6 / 4 | 含回执、人工输入与面板答复 |
| T-102 a1 / a2 worker | 5 / 2 | 含回执、提醒与面板答复 |
| T-103 a1 worker | 2 | 初始指令及 Stop 期间的人工输入 |
| 四个独立 reviewer | 4 | 每个 1 回合 |
| Reflect | 1 | 手动复盘 |
| 总计 | 37 | managed 实际 23，主控 13，Reflect 1 |

计数取原生记录中有文本的根 `user` 消息；排除 `isMeta` 技能展开、纯工具结果、`interruptedMessageId` 中断占位符和 sidechain；没有发现额外子会话。被中断的原提示仍计一次。该口径是任务提示与回复构成的回合，不是供应商 API 调用数、token 或成本。看板最终 22 漏了 T-103 一次人工输入回复，主控为 0、Reflect 未计入；以看板估算全局预算不可用。

本阶段模型执行截止在 C13 回复后；后续未新增应用内模型提示，预算累计不超过 60。最终已从停止后的原生记录补齐根回合；外层 Codex 的审查/写报告不算应用内回合。应用内没有 Codex worker。

权限操作只有测试 repo 信任、两次主控角色批准、问题页答复、选择同目标卡修订及明确的交叠理由；没有系统隐私、登录或付款操作。没有批准 Reflect 的任何改进建议。Computer Use 的操作来源是测试 agent，产品记录名“用户输入”不意味着真人亲手操作。

## UI 重开与最终停止交接

主控 #19 已按原任务卡在沙箱外只停 UI 再重开同一后台，没有重新创建 root：

```sh
bash evidence/2026-10-23-batch24/T-155/STOP-APP.sh /private/tmp/t155-dogfood-ohzs_78v
bash evidence/2026-10-23-batch24/T-155/START-APP.sh /private/tmp/t155-dogfood-ohzs_78v
```

Computer Use 已确认同一隔离 renderer；生命周期日志 `logs/electron-c18cd8fc.json` 为新 Electron PID 14775，`logs/daemon_status-9840d5cc.json` 为保留的 daemon 83082。图 57～61 核对任务/角色/终端/记录/Reflect，T-103 的未知没有因重开被掩盖。默认页面落在独立终端，重新选择项目后可读原内容。未新增模型回合，也未测试 daemon 重启。

主控 #20 确认已在沙箱外 `STOP-APP.sh /private/tmp/t155-dogfood-ohzs_78v --all`，UI 与 daemon 停止，目录保留。#21 补充：返回后立即 pgrep 仍见 4 个 Claude（1977、2097、3369、7382）与 4 个本实例 gate CLI，十几秒后再次检查均退出。此项只记录为主控事后观察，测试者未独立复核该时间窗，不列为新发现。

阶段文本检查：报告 UTF-8 回读与 20 个本地引用存在性检查通过；project-map status 为 Problems 0、Stale living docs 0；产品 workbench 与基线无改动。默认 `git diff --check` 在原样保存的 AX 文本中报告 14 处 UI 字段自带尾随空白（分隔符与日期占位符），记录保留、不为消除告警改写原文。仅排除此原始 AX 文件后，手写报告与脚本的 diff check 退出 0；不把默认检查写成通过。

## 冻结阶段独立审查

按 behavioral-acceptance-review，在干净只读上下文审查 `b6963c6c8b58263c5e8ce8d5fd9cbaa4fdcf1159`；原文保存于 `ACCEPTANCE-REVIEW.txt`。结果 INCOMPLETE：未发现报告失实或未标注限制，七条发现均有截图，模型行为与产品机制已区分；缺少最终停止读回、精确回合与归档，无法判定完整旅程通过。审查没有读取作者聊天或 SESSION-NOTES，没有启动应用、运行模型或访问外部临时实例。该审查只对冻结阶段结论有效，不为后续新增证据背书。

## 停止后数据库终核

主控 #22 读过脚本后，在沙箱外运行 `python3 evidence/2026-10-23-batch24/T-155/readback_stopped.py`，rc=0，输出 `{"instances": 2, "output": "/private/tmp/t155-final-readback"}`。脚本先检查 daemon.pid/control.sock 已消失和无带实例路径的进程，再复制 DB/WAL；只对副本转 DELETE、做 integrity_check，后以 mode=ro 查询，未修改原库。两副本均 integrity=ok、copied_wal=false。

测试者在沙箱内首次执行因系统禁止 `/bin/ps` 未开始复制；随后提权弹窗被主控拒绝、由主控代执行，不是脚本业务失败。`stopped-readback.json` 为实际产物；测试者随后只读副本核对了以下事实：

- F04：两实例 `role_request_decided` 与 `role_request_confirmed` 均存在；新实例 decided 的 approved=true，时间 21:08:21.376Z，随后 confirmed=21:08:21.452Z。输入记录旧实例 2 条 message，新实例 17 条（12 message、3 action、2 answer），均没有角色批准。
- F01：新实例 events seq 299 / orchestration seq 860 在 21:14:48.746Z 拒绝同一 T-103 submit，错误 `worker_not_active`；当前仍 claimed、candidate=null。时间在人工输入记录 .583/.725Z 之后、原生提示 .865Z 之前；只据此确认交付被拒与时序，不宣称已定位竞态根因。
- T-101/T-102 均 paused，当前 a2 submitted，候选与前述完整提交号一致；T-101 delivery.number=2。三票 integration_intent 均 null；main 保持种子 `13f052436fa25e8a88e7b154daa7cdb14a8c9023`。
- events 中三次 `review_protocol_failed` 为 21:13:01.662Z、21:29:42.939Z、21:34:35.342Z，均含 review_json，与界面三次协议暂停一致。
- `fixture-inputs/` 原样复制主控生成的 5 张小卡和 5 个验收脚本，共 9,912 字节，逐字节比对；provenance.json 记录原路径。这些是被门禁读取的输入和模型失误证据，不是本报告的可信 oracle；未运行或修订它们。

## 最终归档与交付边界

主控 #23 读过 `archive_runs.py` 后，在沙箱外执行以下命令，rc=0；提权弹窗由主控拒绝，worker 调用的中断不是归档失败。后续沙箱外动作按主控要求先写脚本交接，不再发起提权请求。

```sh
python3 evidence/2026-10-23-batch24/T-155/archive_runs.py
```

结果 `{"status":"PASS","directories":18,"files":574,"bytes":28558091}`。外置盘根目录 `/Volumes/WD-Elements/a2a-evidence/2026-10-23-batch24/T-155/`；`runs.archive.json` 为实际写出的清单，逐项含 original/archive/bytes/replay，不含哈希。归档脚本逐文件核对大小与内容，原件全部保留；测试者随后独立只读核对 18 项源/目标相对文件大小表、文件总数与总字节，均一致。两个真实实例、准备仓库、旧读回与最终读回目录、本票原生日志、两个主控 scratchpad（变异样本、卡片、诊断）均在清单内。停止后没有遗留 socket，本次没有特殊文件跳过。

报告、小截图、摘要、脚本和真实门禁读取的小输入留在 Git；raw run、DB 与原生日志只在外置盘归档及保留原件中。新运行需重新 prepare 并按 SESSION-NOTES 的 UI 提示人工推进；归档/计数/读回命令采用排他创建，不覆盖旧现场，不要对本轮归档直接重放业务门禁。

未完成项保持：独立审查接受、打分、集成；未覆盖 Codex worker/混合供应商、monitor、多项目、daemon 重启。没有产品修复、push、worktree 清理或直接改库。阶段独立审查绑定 b6963c6c8，后续读回与归档尚需主控最终审查，不能借其旧结论宣称完整验收通过。
