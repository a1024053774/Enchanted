---
id: T-258
title: Codex 原生会话晚于启动期限出现后，失败标记保留并阻塞交付和回收
type: build
status: open
blocked_by: []
claimed_by:
supersedes:
ready: no
---

## What to build

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
