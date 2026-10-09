---
id: T-044
title: 任务窗口由 agent 驱动
type: build
status: open
blocked_by: []
claimed_by: Codex T-044 worker（2026-10-09）
supersedes:
---

## What to build

用户要求（2026-10-09）：任务窗口里的任务与会话由主控 agent 经门禁建立，不靠人手动添加会话、选角色。
- 门禁 `create` 同时在任务窗口建立该任务（标题、项目取自任务信息）。
- `dispatch` 创建的 worker 会话自动归入该任务，角色 worker。
- 新增门禁命令 `attach`：主控传入任务、角色（reviewer、monitor 等）、模型与指令，Synara 新建会话并自动归入该任务。用户已确认：这类会话是"普通会话加角色"，不是交付 attempt，没有 submit、验收、集成权限，只记一条事件。
- 回收后会话标为已结束，保留在任务历史中，界面淡化显示。
- 手动"会话归属"编辑保留为人工修正入口。
所有新行为在门禁核心实现，CLI 与 HTTP 自动可用；主控的 MCP 工具等主控迁入 Synara 时再开放（本 ticket 不给 agent 会话开放 create/dispatch/attach 工具）。

## Acceptance

- [x] 经 `a2a/scripts/gate`（或同一 CLI 的 HTTP 传输）依次 create → dispatch → attach reviewer，任务窗口无需任何手动操作即显示该任务、worker 与 reviewer；有截图与命令输出。
- [x] attach 的会话调用 `a2a_submit` 被拒绝；不能经它推进门禁状态。先在缺失实现时取得红态。
- [x] 回收后会话在任务中标为已结束；membership 与门禁事件读回一致。
- [x] T-036/T-037 的 35 项与 T-038 membership 场景仍通过；typecheck、lint 通过。

## Resolution

2026-10-09 第二轮：**PASS（T-044 与主控决定 01 的明确隔离范围），保持 open 待主控关闭**。授权见 [主控决定](../../evidence/2026-10-09-batch5/T-044/controller-decision-01.md)；最终 fork 候选 `90e38b667e224caca75318591fac43e676bf77e3`，未 push。完整 [第二轮中文报告](../../evidence/2026-10-09-batch5/T-044/round2/RESULTS.md)、[新 fresh-context 审查 PASS](../../evidence/2026-10-09-batch5/T-044/round2/acceptance-review.md) 与截图、原始 argv/事件、红绿态、坏候选和 19 个夹具 root 归档已保存。

REALITY GATE: PASS。operation_busy/KeyError 两类原失败均来自夹具在固定 submit 窗口内读取全量 snapshot，迟到后触发门禁的正常期限清理；原时间线与受控慢观察红绿态证明，修复仅改公开 status 身份读取，不改业务断言/期限。最终候选 35/35、membership、fmt/lint/typecheck 与相关核心/服务测试通过；error 正例可回收，22 种反例在任何 stop/archive 副作用前拒绝，run error 仍非成功；真实 CLI HTTP 回收与 dev 截图显示两角色“已结束”且历史保留。签名 Gateway/真实 app 模型/生产/Electron 原生不在此通过声明内。

以下首轮 BLOCKED 记录原样保留，不作为第二轮候选的通过背书。

2026-10-09 worker 交接：**BLOCKED，保持 open**。代码已在 fork `a2a` 分支提交，最终候选 `808156d63ef8e265a0e2c017fae7851e50a51019`，未 push；[中文报告](../../evidence/2026-10-09-batch5/T-044/RESULTS.md) 保存全部红态、检查、截图失败、两次审查原文与边界。

create/dispatch/attach 自动归属已取得早期候选 HTTP 与 dev UI 证据；MCP handler 身份反例与最终候选 CLI/SQLite 历史修复通过。最终 35 项为 34/35，剩余一项 native 夹具 thread 缺失；fmt/lint/typecheck 通过，服务端另有 verifying 超时未定因。最终界面与真实 Gateway 认证链未通过，验收框保持未勾选。

主控需要决定：任务书要求 provider 关闭，导致原生会话为 error，既有 T-037 回收保护拒绝，无法完成门禁回收/淡化截图。选择保持保护并批准受控无模型 provider 夹具，或扩大恢复合同并重新取得反例；worker 未自行选择。另有一次范围偏离类型：执行正式 status 两次读取了被禁止目录中的启动身份元数据，详见报告；未写正式实例或重启它。
