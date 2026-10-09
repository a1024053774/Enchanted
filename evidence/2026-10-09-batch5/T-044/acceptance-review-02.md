STATUS: FAIL
TARGET: 定向范围，`839a1e97c9807ac7a601015edf06f9137cb912e8`；parent `c4c1aff2bb6d81fb60d281191f36b39f4ffa99f0`。候选未漂移。

EVIDENCE:

- **PASS：attachment 同事务记账。** [core.ts:870](/Users/luckye/Documents/Code/synara/packages/a2a-gates/src/core.ts:870) 将 ended 与 `attachment_reclaimed` 放入同一事务。父修订事件写失败后错误留下 ended；[最终证据](/Users/luckye/Documents/Code/a2a/evidence/2026-10-09-batch5/T-044/lifecycle-event-final.log) 验证回滚、重试成功、完成事件恰有一条、attempt 为 null、业务状态仍为 ready。
- **PASS：attached 成员删除／重加。** 新实现从持久 attachment 获取结束时间。[父修订红态](/Users/luckye/Documents/Code/a2a/evidence/2026-10-09-batch5/T-044/lifecycle-readd-red.log) 丢失 `endedAt`；[最终绿态](/Users/luckye/Documents/Code/a2a/evidence/2026-10-09-batch5/T-044/lifecycle-readd-final.log) 保留原时间。
- **INCOMPLETE：结束已持久化后的 membership 修复。** [core.ts:833](/Users/luckye/Documents/Code/synara/packages/a2a-gates/src/core.ts:833) 已有重复 reclaim 修复路径，但所提供两个测试模式均未注入 membership 写失败，也未覆盖该 ended 分支。
- 修复位于原门禁核心，只改 core 和 attempt 时间字段；事务与持久事实派生针对根因。原生 error 回收保护未改。
- 证据使用真实 CLI 解析函数、Git、SQLite；native runtime 为明确的受控边界，未证明真实 provider 生命周期。审查未编辑或重跑测试。

FINDINGS:

- **[P2] [core.ts:156](/Users/luckye/Documents/Code/synara/packages/a2a-gates/src/core.ts:156)** — 存量已回收 worker 的结束标记仍会丢失。父修订合法记录为 `reclaimed=true`，没有新增的 `reclaimed_at`，但 membership 已有 `endedAt`。当前分支无条件选取缺失的 `attempt.reclaimed_at`，不会采用已有标记；即使保存时不删除成员，也会清掉结束时间。简化修正：从该 worker 已持久的 `reclaimed` 事件恢复缺失时间，保证随后删除／重加仍保留生命周期。此问题在定向范围内，已交接，未追踪新候选。

COUNTEREXAMPLE:

- 父修订分别在“事件失败仍提交 ended”和“删除／重加丢失 endedAt”的业务断言上失败；新候选两项通过。
- 合法旧 worker 记录缺少 `reclaimed_at`：当前保存逻辑确定丢失标记，属源码可达反例；本次未执行写入。
- 删除 ended 重放分支中的 membership 修复调用，现有两个最终测试仍可通过；第三项证据尚不能拒绝此已知坏实现。

LIMITATIONS:

- 定向范围因存量 worker 缺陷为 **FAIL**；重复 reclaim 修复的行为证据为 **INCOMPLETE**。
- UI、完整 35 项、真实 MCP Gateway 及真实成功回收限制继续有效。本报告不宣布 T-044 PASS。
- 本次定向复核结束；后续问题交接处理，不自动追逐新候选。

RULE:

- 生命周期验收补充：父修订格式的已回收 worker，先原样保存，再删除／重加；以及提交结束事实后让 membership 写失败，再重复 reclaim，要求修复归属且完成事件仍恰有一条。
- 结束 `project_map.py status`：Problems 0，Stale living docs 0。
