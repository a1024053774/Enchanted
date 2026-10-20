# T-107 第一轮独立审查

**NO_GO，需修复。** 冻结候选：3c3f2e9e189ddf37eeec4091266c8701a2dde33f，分支 exec/t107。结论只适用于此候选。

确认两个产品问题和一个验收问题：辅助原生会话能把根会话的未知状态上调为运行中；侧栏读取会写库；现有检查不能拒绝主动写库的错误实现。完整层级、两种等待和真实通知仍是 INCOMPLETE，不能关闭整张票。

## 范围与独立性

- 按指定顺序阅读角色卡、AGENTS、T-107、T-095、RESULTS，再用 git show 和 git diff 3c3f2e9e1^ 3c3f2e9e1 审查原文及直接调用方；未阅读作者会话。
- 预期来自 T-107：保存事实决定归属，关系不明进未归属；无法核实的状态保持未知；读取不写库；只在进入等待用户回答时通知。截图按本次派发豁免。
- Ubiquitous language：启动记录、原生会话、attempt、派发记录分别核对。Tracer bullet 的局部通过不等于整票通过。Deep modules 方面重点核对状态读取与采集的职责。
- 应用 project-map、evidence-first-testing、behavioral-acceptance-review、design-integrity-review、frontend-production、document-writing；由本会话执行，没有开子 agent。
- 只写指定的报告、复验脚本及新建的 /private/tmp 目录；没有修改候选、提交、切换分支、调用模型工具、启动模型回合、操作 Herdr、申请升级或写全局配置。
- 初始工作树干净，收尾 HEAD 未变。提交说明如实披露作者手动切换后的 Desktop 身份、无 A2A 启动绑定、执行主控代提交且无 worker 尾注；没有把它冒充原 worker 的绑定交付。该说明本身不是门禁通过证据。

## 确认问题

### F1 · P1：辅助原生会话会清除根会话的问题线索

位置：workbench/src/sidebar.ts:32、:77、:93；直接调用方 workbench/src/panes.ts:670、:694、:707。

agentState 遇到任意 event_msg/task_started 就 pending.clear()，没有核对原生日志文件或当前原生会话。输入事件只按 a2a launch 过滤。Panes.scan 对相同 workspace 的日志都会保存 native_record；只有更新根回合身份时才限定根文件。新启动的 worker 没有 nativeFile 限制，此扫描路径可达。

独立受控夹具经过实际 sidebarSnapshot → Panes.status → scan 和 SQLite：

1. 根日志留下尚未回答的 request_user_input，侧栏为 unknown。
2. 加入同 workspace 的辅助原生会话日志，含辅助会话的 task_started。
3. 根 pane.turn 和 active.nativeTurn 均仍为 root-turn，没有根问题的回答。
4. 侧栏却变为 running。按票据应保持 unknown。

影响：辅助活动被误用为根问题已解除的依据，可能使主控漏看无法确认的待答会话。修复方向：按已核实的根原生会话/回合归属投影问题状态，未知来源不能清除 pending。加入“根问题 + 辅助会话开始”的反例，预期保持未知，再走真实入口复验。本轮是实际产品模块、真实 SQLite、受控日志的复现，不冒称真实模型现场。

### F2 · P2：侧栏读取并非零写入

位置：workbench/src/sidebar.ts:76；调用链 workbench/app/main.ts:145 → workbench/src/daemon.ts:166 → sidebarSnapshot → workbench/src/panes.ts:1001 → scan。

第一次读取会扫描未消费的原生日志，把 native_record 追加到 orchestration_events，同时追加 traces/<launch>/native.jsonl。独立夹具观察到事件行数 **0 → 2**。这是现有采集路径被侧栏调用产生的写入；README 也承认侧栏可以采集原生记录。

影响：不满足本次明确要求的“侧栏读取只读，不写库”。把接口列入 readOnly 不能消除副作用。修复应在现有采集职责处处理，侧栏消费已保存事实或无写入快照，不另加兼容读取路径。复验必须在有未消费原生日志时核对相关表和 trace 的原值。

### F3 · P1：现有完成条件放过“读取时主动写库”

位置：workbench/tests/test_t107_sidebar.mjs:65；workbench/tests/run_t107_sidebar.py:160、:209。

候选先通过投影检查后，在副本的 sidebarSnapshot 开头只增加一行 store.event('sidebar_read', { source: 'sidebar' })，现有投影检查仍 **rc 0 / PASS**。

Electron 检查仅对比 tasks 原值及 user_inputs 行数，不能拒绝向 orchestration_events 追加事件。本轮尚未在真实 Electron 跑此变异，不能把静态覆盖分析写成真实 Electron 已通过；复验脚本已包含该项。

“任务原值与用户输入零写入”不能推广成“侧栏读取零写入”。需要跨实际 daemon/侧栏入口核对相关持久化表和 trace，并要求此变异在业务断言上被拒；不能把环境失败或崩溃算拒绝。当前完成条件不够格，需修复。

## 必审项结论

| 项目 | 结论 | 结果 |
| --- | --- | --- |
| 层级事实 | 局部 PASS；完整层级 INCOMPLETE | 关联 dispatch 的 inbox_entry、成功 relay 结果、认证发送 launch 与接收 launch；核对同项目、from/to/preset，歧义归零，再限制合法角色边。未读取窗格标题/终端正文推断关系。任务与 attempt 来自启动记录；没有父 launch 的 worker 等进入未归属。 |
| 七状态与未知 | NO_GO | 两种等待没有生产返回分支；未识别通常未知，但 F1 可以上调。逐分支见下。 |
| T-095 直接复用 | INCOMPLETE | Herdr 期已有等待主控回答识别；其身份和观测边界不能直接用于工作台自管 PTY，详见下文。 |
| Git 事实 | 已查范围 PASS | porcelain v2 固定字段；本轮真实 Git 分叉夹具与 LC_ALL=C 的 status -sb 领先 1、落后 1 一致。无上游保留 null；不存在目录返回 null 和具体原因，没有从本地化普通文本猜数。 |
| 通知 | 合同局部 PASS；真实触发 INCOMPLETE | 只在 waiting_user_answer 转换时通知，按 state 路径/launch 去重；关闭时仍观察状态，重新启用不补发旧等待，离开后再次进入可通知。真实通知从未触发，当前生产状态来源不可达。 |
| IPC | 合同 PASS；只读承诺 NO_GO | 新增三个明确名称，均经 windowTarget 限制主 frame/注册窗口。selectAgent 校验 catalog/task/launch；历史视图不发输入凭据。20 handler、21 bridge，原拒绝断言保留，本轮复跑通过。真实采集副作用见 F2。 |
| 侧栏/注册 | 静态核对；本轮真实复验 INCOMPLETE | 复用 T-106 创建入口，有中文角色/状态、图例、任务分组和等待样式，T-106 IPC 回归通过。窄窗、聚焦和持久化只核对主控已有 electron-03 摘要，不宣称本轮 GUI 或完整读屏验收通过。 |

### 状态映射逐分支

入口 workbench/src/sidebar.ts:16，按执行顺序核对：

| 分支 | 结果 | 判断 |
| --- | --- | --- |
| restoration failed / pending | 未恢复 | 机械恢复事实；优先于 ended。 |
| lifecycle ended | 已结束 | 生命周期事实。 |
| 缺失 pane、historical、failed、interrupted、生命周期非 running | 未知 | 不上调。 |
| permission_wait | 设置权限等待标记 | 后续保守为未知。 |
| turn_start_signal / pane_idle | 清除权限等待标记 | 后续仍检查 pane 当前事实，不直接返回运行中。 |
| function_call 的 request_user_input / request_user_input_async | 加入 pending | 精确协议名，不是语义关键词；不把 accepted:true 当作答案。 |
| 任意 native task_started | 清除 pending | **F1：缺少根原生会话归属校验。** |
| 权限标记或 pending 非空 | 未知 | 没有在此区分两种等待。 |
| idle 且无 active / writing | 空闲 | 采用现有 host 状态。 |
| busy、active、非 writing、native_session，nativeTurn 与 pane.turn 相同 | 运行中 | 正向回合关联，不能挽救 F1 已错误清除的问题线索。 |
| 上述前置条件，active.id 对应 turn_submitted，之后有同 native_session 的 turn_start_signal | 运行中 | 旧提交之前的 start 不算正证；候选检查覆盖此反例。 |
| 其余 | 未知 | 最终未知改空闲变异被拒。 |

项目汇总顺序：等待用户回答 → 等待主控回答 → 运行中 → 空集合/含未知则未知 → 未恢复 → 有空闲则空闲 → 已结束。七种枚举/标签/图标不证明七种真实来源已经实现。项目中一个已确认运行中的会话可令汇总为运行中，单个未知会话仍保持未知。

### 作者缺口与 T-095

scripts/agent-status:192 要求 HERDR_ENV=1；从 records/launches.jsonl 取身份，限定 Codex worker 和已核对 CLI 版本，核对 Herdr pane、terminal、cwd、原生会话及前后读取一致。:204 读取 visible/detection，两边机械面板标记加 blocked，才在 :228 返回 waiting_controller_answer。

工作台的 SQLite 启动记录和自管 PTY 不提供上述 Herdr 身份和读屏边界，不能只传工作台 launch 直接复用。准确结论是：**Herdr 期已有等待主控回答识别；本候选未接入，也没有可直接适用于自管 PTY 的同等来源。** 工具名称本身不说明谁负责回答。两种等待目前显示未知的缺口属实，不能用角色或屏幕词语补猜；也不能笼统说整个项目没有这种信号。

worker 的直接 pane_dispatch 保存目标 launch、文本和来源，没有具体父 launch；可选 inbox_entry/sender 也不必然绑定具体父会话。候选仅在能关联 relay assign 时建边，完整 worker 层级不能 PASS。真实通知未触发的声明与原件一致。

## 证据与变异

环境：2026-10-19，macOS；Node v26.5.0、Python 3.9.6、Git 2.52.0，Git 检查 LC_ALL=C。模型调用及模型回合均为 0。

本轮正式复现命令：

~~~sh
bash evidence/2026-10-19-batch17/T-107/REVIEW-OUTSIDE-01.sh local
~~~

现场：/private/tmp/t107-review-outside-01-buvcxndm。用 git archive 创建候选及三个一次性副本，未建 worktree。完整命令、返回码、stdout/stderr、变异源码和探针留在现场。脚本最终退出 **1** 表示业务审查 NO_GO，不是环境失败。

| 检查 | 结果 |
| --- | --- |
| 候选 projection：真实 Git/SQLite、受控 pane 状态 | rc 0 / PASS |
| 候选 main/preload IPC：包含历史坏版本与内置变异 | rc 0 / PASS；旧版本因缺少侧栏合同被拒 |
| 单处变异：最终未知改为空闲 | rc 1，被 Missing signal must remain unknown 拒绝 |
| 单处变异：无派发证据时按 executor/title 回退猜父会话 | rc 1，被 Role-only parent must be rejected 拒绝 |
| 单处变异：侧栏读取主动 store.event | **rc 0 / PASS，未被拒绝，F3** |
| 独立读取/辅助原生会话探针 | 执行 rc 0；观察到写入 2 行、辅助 start 后 running，业务 NO_GO |
| 独立 Git 失败输入 | 具体读取错误可见，branch/ahead/behind 均 null |
| T-106 IPC 回归 | 单独运行 rc 0 / PASS，初次现场 candidate-t106.json |
| shell、UTF-8 无 BOM、Python 3.9 语法、diff 检查 | PASS |

初次现场 /private/tmp/t107-review-01-ik_ei26b 也保留候选、变异和结果；正式脚本另开新目录复跑，未覆盖旧结果。独立探针使用受控反例，不是历史真实模型原件。

主控提供的 electron-03-summary.json：四项局部检查 PASS，implemented_slice_status PASS，整体 INCOMPLETE，cleanup_complete true；与派发描述一致。本轮没有把主控证据改称独立运行。

真实入口待执行命令：

~~~sh
bash evidence/2026-10-19-batch17/T-107/REVIEW-OUTSIDE-01.sh electron
~~~

脚本默认 electron 模式；先确认候选，再跑候选与主动写库变异的真实 Electron/daemon/SQLite 旅程。使用内置盘 Electron 43.4.1，所有新输出在 /private/tmp；不截图、不调用模型、不改全局配置。**本轮 electron 模式未运行，未申请升级。** 即使局部 GUI 检查也放过写库变异，整票仍不能关闭。

## 结构审查与限制

冻结 diff 的 design-integrity 扫描定位 Git catch、侧栏读取 catch、聚焦 catch、设置保存 catch。逐一核对：错误转为带原因的未知/错误提示，没有吞成成功；三秒轮询是刷新事实，不是操作重试。changeTask 有两个真实调用点；旧 projects/tasks IPC 是原有公开合同，原拒绝检查保留。已查 diff 未发现新增门禁绕路、双写兼容或无依据重试。结构问题是 F2 的查询/采集职责混合。

本轮适用的行为能力：状态编排、launch/原生身份、Electron/IPC 交互和 SQLite/文件副作用。模型理解质量、检索和生产发布不属于本票，没有作相应通过主张。七状态真实信号、真实通知及完整 worker 父层级均保持 INCOMPLETE；视觉/读屏和长时间性能没有完整审查。

开场与收尾 project_map.py status 均 rc 1，8 个同样的稀疏检出断链，stale living docs 0；收尾输出保存在正式现场 closing-0.txt。没有把“0 stale”写成“0 问题”，没有改地图。另见 intent 构建约束仍保留外置盘旧文案，与本次 AGENTS 内置盘裁定不一致；按当前明确指令使用内置盘，未改范围外文档，通过报告上报执行主控。

机械防复发检查：在侧栏真实入口验收加入 F1 的根/辅助原生会话反例，及覆盖相关持久化表和 trace 的只读断言；要求 F3 变异在业务断言上失败。现有检查能拒绝未知改空闲和无证据猜层级，不能据此声称覆盖所有错误状态或副作用。

不批准集成或关闭 T-107。修复确认问题、补足拒绝证据后，对变更范围定向复审；未决信号缺口由执行主控按票据边界继续处理。

T-107 REVIEW NO_GO
