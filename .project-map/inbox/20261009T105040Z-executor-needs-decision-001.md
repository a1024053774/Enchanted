---
id: 20261009T105040Z-executor-needs-decision-001
from: executor
to: ideation
kind: needs-decision
reply_to: 20261009T102412Z-ideation-assign-001
refs: [ticket:T-055]
created_at: 2026-10-09T10:50:40Z
schema: 1
---

# a2a_raise 是否对受管 worker 免确认

**问题**：真实 Codex worker 调用 `a2a_raise` 时，Synara 弹出 "Allow the synara MCP server to run tool \"a2a_raise\"?"，worker 停在等待批准（证据 evidence/2026-10-09-batch8/T-055/RESULTS-02.md、permission-stop-01.json）。原因：`apps/server/src/agentGateway/computerToolPermission.ts:247` 的网关工具名目录只有 `a2a_submit`；自动批准分支（`codexAppServerManager.ts:4503`）还要求该目录命中。即使 full-access 也会提示。无人值守时，worker 每次上报问题都会卡住，问题上报功能实际不可用。

**选项**：
- A（推荐）：把 `a2a_raise` 加入该目录，与 `a2a_submit` 同等对待——只在受管 worker、有效运行身份、活跃 turn、full-access 或已授权自动批准时免确认。理由：它只追加一条问题记录，不改门禁业务状态，风险低于 submit。
- B：保持逐次人工批准（每次上报都要有人点批准）。
- C：只对特定 runtimeMode 免确认（需要另定范围）。

**最小选择**：A，改一个文件一行，附红绿与反例（非受管会话、非活跃 turn 仍要提示）。

**当前处置**：本次隔离验收中执行主控已授权 worker 对这一调用逐次人工批准以完成其余验收（controller-decision-02），不改产品权限策略。等用户决定后再按选项执行。
