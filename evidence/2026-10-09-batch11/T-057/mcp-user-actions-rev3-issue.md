# T-057：七动作 MCP 证据的用户身份边界

观察：当前 `packages/a2a-gates/src/core.ts:654` 对 `reopen`、`snooze`、`dismiss` 强制 `actor === user`；`apps/server/src/a2a/tools.ts:130` 的 `a2a_disposition` 只开给活跃主控会话，并由凭据提供身份。服务端能力预设没有用户 MCP 身份。spec 第 4 节规定用户可以重开、稍后、不处理，明确仅用户可 dismiss。

因此，七个动作都可以经真实 MCP 调用，但这三个用户动作必然被主控凭据拒绝、不会追加处置记录。brief rev3 第 3 项要求逐个 MCP 调用并核对追加记录与派生状态；它没有明确 reopen/snooze 的拒绝证据是否算此项覆盖。

建议维持现有权限：七动作全部经 MCP；对用户专属动作核对拒绝、零追加、状态不变，再经 HTTP 用户入口取得追加与派生状态证据。请主控明确这一证据组合是否满足任务书；如果要求所有动作经 MCP 成功，须先决定用户 MCP 身份与权限范围，worker 不自行新增。此问题默认不阻塞当前实现与机械调用。
