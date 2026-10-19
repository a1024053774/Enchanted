STATUS: PASS
TARGET: d594057a9672e2b7441ca17c4e8632296927f1b4（对比 4533ebeb7f1a16ee50857da1e1f15a9222fde6cb；仅诊断修复）

EVIDENCE:
- 独立运行 `test_t093_daemon_rejection.ts`：候选 rc 0，3 项通过；基线 release 代码 rc 2，3 项均在 `daemon_error_field_must_survive_actual_chain_assertion` 失败。
- 独立运行 `test_t093_chain_publication.ts`：rc 0，5 项通过。原件位于 `/private/tmp/t093-review11-w8sb6uyy/`。
- 对实际 release 代码块执行额外 L1 哨兵：全新拒绝码、含合成凭据的 details、不同 before/after 状态均保留；发布前脱敏；清理回调执行前已有完整诊断；主失败保持 INCOMPLETE。原件：`/private/tmp/t093-review11-sentinel-uT6gMl/result.json`。
- `test_t093_login_chain.ts:114–117` 在断言前保存状态和回复；`t093_chain_evidence.ts:59–65` 在清理前发布主失败。
- 差异未修改产品源码、OS profile、release 前提或引入重试、强制状态和绕过。
- RESULTS:379–393、请求 11:44–50 明确旧回复已丢失、实际原因未知，并要求新 outside primary 未达到预期时停止后续场景。
- 审查结束时 HEAD 与受控文件未变；地图检查 0 problems、0 stale living docs。

FINDINGS:
- 本轮限定范围内未发现可达或复现的行为违约。

COUNTEREXAMPLE:
- 基线的布尔断言确实被拒绝，失败原因是业务要求的 daemon 错误字段丢失。
- 新 nonce 拒绝码及不同状态哨兵通过，排除了仅保留固定示例输出的实现。

LIMITATIONS:
- PASS 仅覆盖 L1 诊断保留、状态留证、脱敏及清理前发布。
- 真实 daemon 拒绝原因仍为 UNKNOWN；实际 OS 边界、新 primary、green 和正式六场均为 INCOMPLETE。
- 未执行 sandbox-exec、进程探测、CLI、认证读取、网络或模型回合；未操作已有夹具。真实复验留给请求 11 的操作方。

RULE:
- N/A：本轮无新增 finding。
