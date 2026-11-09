---
id: T-258
title: Codex 原生会话晚于启动期限出现后，失败标记保留并阻塞交付和回收
type: build
status: open
blocked_by: []
claimed_by:
supersedes:
ready: yes
ready_by: executor
ready_rev: 1
---

## What to build

### 当前执行授权（2026-11-08 15:36Z）

用户在本轮回答问题“T-249 的第二轮 terra 验收又被启动阻塞卡住：原生回合未建立，门禁回收返回 identity_conflict，现场已保存。你希望先正常重启并修复 T-258 这类启动恢复问题，再继续两个面板，还是只重启并经门禁重派验收？”：

> 修启动阻塞后继续（推荐）

据此本票就绪，先修 T-258，再恢复 T-249 的独立验收并继续 T-250。执行主控与 worker/reviewer 仍按本轮要求使用 gpt-6-astra xhigh 普通速度，不启动 Claude、不 push；两个面板的最终验收仍由 gpt-6.1-terra Computer Use 加常规测试完成。下文“未授权”是此前停点，已被这次明确授权取代。

恢复事实：主控通过标准 daemon_stop 正常停止后台 81233，重新打开同一正式包后后台为 95522；原产品 worker 与 terra CLI 均已退出，用户自己的 hc core 42545/99586 未变。terra attempt 843d4f55 已经门禁 reclaim 成功，四个未交付文本文件复制保留，未强制清理原脏 worktree。证据在 [本次恢复目录](../../evidence/2026-11-08-batch34/T-258/controller/)。执行角色仍是用户原批准角色，未重新签发。

REALITY GATE: INCOMPLETE。15:37Z 停止后台前已观察到 terra 晚绑定 session `01a1bbc6-b73d-73d3-b38d-578c153ba9ad`、turn `01a1bbcd-1332-75a3-bc32-80ab09a8f539`，而 failed 仍为 native_session_unbound。这一后续事实补足晚绑定仍保留失败状态；起初输入排队的原因仍未知。修复应由受管 worker 先复现并区分前置环境问题与产品缺陷，不能凭一次静态观察清空状态。

验收边界不变：身份、提交来源、attempt/fence、重复请求和真实工作中不可回收都要有反例。生产代码最小变更；不改 T-249/T-250 实现，不修改冻结 acceptance/** 或 REVIEW.md，不更换原生 CLI、不写全局配置。实际候选触及 REVIEW.md 敏感条目时，仍在集成前交用户读证据批准。

2026-11-08 执行 T-249-1 v4 时发现，按项目规则登记缺陷；尚未获本轮新增实现授权，不派发修复。与 T-257 的 Stop 回执同 turn 续跑不同，本次首先出现的是启动时限后的原生身份绑定。

现场为正式应用 0.1.6，源码 08b8318f54224790916b7b95016e551499a0a0fa，后台 36212；task a2a+T-249-1，attempt 27481daa-4502-44a9-873e-c00a7b1cab4a，launch 408f904c-e5bc-4ae9-9bae-046fe1f13771，thread 06229cf4-6b37-4bd8-abbf-6e181ced929f。CLI Codex 0.167.0，gpt-6-astra xhigh，普通速度。

已观察到：

- 13:29:11Z 首次输入提交，13:29:31Z 记录 turn_start_missing；13:31:11Z 记录 native_session_unbound。
- 13:32:41Z 后台绑定原生 session 01a1bb59-3b6d-7591-b91c-2352e259d298，worker 随后正常工作并提交候选 9f96a9121ba6ed8d77a514a0a78c9341ceaacb86。
- 13:48:38Z 和 13:49:41Z 两个 Stop 都被 current_turn_untrusted 拒绝；pane 保留 failed=native_session_unbound、active 原回合、state=unknown。submit 与两条 issue 请求仍是待处理文件，任务仍 claimed，candidate_commit=null。
- worker Git 工作区干净。主控未向窗格输入、重发请求或改变运行时状态；一次正式 reclaim 返回 run_external_unknown，providerPresent=true、activeTurn 非空。

证据：[现场及请求](../../evidence/2026-11-08-batch34/T-249/controller/startup-delay-submit-blocked.json)、[回收拒绝](../../evidence/2026-11-08-batch34/T-249/controller/reclaim-a3-refused.json)、[首次启动时间线](../../evidence/2026-11-08-batch34/T-249/controller/startup-delay-01.json)。用户最新提醒“APP没打包应该computer use读不到”：本次 T-249 候选尚未打包，不宣称面板界面验收。

REALITY GATE: INCOMPLETE。代码可见启动超时设置 failed；Stop 的 matched 条件要求没有 failed，晚绑定原生会话不会自动消除此失败。为什么原生会话晚约三分钟出现仍未知。一次进程采样停在 read_dir/open，不足以认定是 TCC、磁盘或 CLI 缺陷。修复前须用隔离入口复现，保留未知身份和真实工作中仍拒绝回收的边界；不能直接延长期限、清空 failed 或放宽门禁代替证据。

## Acceptance

- [ ] 通过隔离后台、门禁和受控真实 CLI 场景复现晚绑定、结束后交付/回收受阻，保存修前红态和明确时间顺序。
- [ ] 修后已核对身份的晚启动回合能够按契约结束并交付或明确拒收后回收；请求不重放、不重复执行，真正工作中仍禁止回收。
- [ ] 没有原生身份、身份不符、未可信输入、过期 attempt 的反例继续拒绝；正式后台和其他会话不受隔离测试影响。

## 当前处置

BLOCKED（T-249 的门禁推进）。候选及测试文本已在原分支提交并保留，尚未进行独立审查、真实窗口测试或敏感变更集成。普通 gate reclaim 已拒绝，不能绕过。T-249 的明确约束是不重启正式后台，新的恢复操作须先由用户决定；旧 T-257 重启授权不自行扩张为本缺陷的实施授权。

2026-11-08 13:56Z 补充：用户针对这一次 T-249 阻塞明确批准“批准重启并经门禁恢复（推荐）”。正常重启后后台 81233，经门禁回收原 attempt 成功；见 [恢复记录](../../evidence/2026-11-08-batch34/T-249/controller/recovery-a3-approved.md)。该操作恢复了派发条件，不代表本缺陷已修复，ready 仍为 no。

### 2026-11-08 15:31Z 再次出现启动阻塞

T-249 产品候选已经 verified，Test 包已完成；第二轮 terra 独立验收的 task 为 `a2a+T-249-2`，attempt `843d4f55-505a-487e-8b0e-149ea092ec3e`，launch `d66b45e8-e416-4788-9360-cc5562e114a0`，thread `4c70d97d-1077-4444-bf87-e3347793d8f2`。实际参数 gpt-6.1-terra、xhigh、default；正式后台仍为 81233。

- 15:28:46Z 门禁写入并提交首次任务文字；终端可见文字留在 Codex 的 `Queued follow-up inputs`，没有原生 session 或 turn。
- 随后依次记录 `turn_start_missing` 和 `native_session_unbound`（事件 149001、149006）。本次截至证据截止点仍未晚绑定身份，不能把它直接说成前一次完整复现；首次输入为何排队也尚未确认。
- `pane_status` 为 unknown、active.nativeTurn 为 null、failed 为 native_session_unbound；工作区干净，尚未执行独立验收。
- 正常门禁 reclaim 返回 `identity_conflict`，live.running=true、live.blocked=true、activeTurn=null。未直接停止进程、改状态或向窗格补 Enter。

证据：[启动事件](../../evidence/2026-11-08-batch34/T-249/controller/terra-attempt2-startup/events.json)、[窗格状态](../../evidence/2026-11-08-batch34/T-249/controller/terra-attempt2-startup/pane-status.json)、[可见终端](../../evidence/2026-11-08-batch34/T-249/controller/terra-attempt2-startup/visible-terminal.txt)。现状 BLOCKED；已向用户提交“修启动阻塞后继续”与“仅重启并经门禁恢复”两个选项，等待决定。该记录不改变 ready，也不视为修复授权。

## T-259 后续执行（2026-11-08）

T-259 已按本轮明确批准合入安装，准备中 attempt 3bba04f2 已通过门禁回收，任务重新 ready。新产品基线含 T-259 的 core.ts 修改，因此不能宣称整个产品输入仍与旧 4c93144df 等价。下一受管 attempt 仅恢复已测 T-258 的三个产品/测试文件和精简证据，不做新实现；主控对新基线补跑真实 CLI 父版红态、候选绿态，之后重新独立审查。旧证据保留为来源明确的历史。用户最新原话：“以后再遇到这种合入我同意,不用等我,然后我截图中提到的几个问题也要开票修复”，后续同类修复完成必要审查和验证后直接合入继续。
