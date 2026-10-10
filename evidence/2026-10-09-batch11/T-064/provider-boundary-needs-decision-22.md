# T-064：真实 provider 权限边界的证据缺口

状态：**INCOMPLETE，待执行主控决定后续验证入口；不扩大为 PASS**。

唯一一次 fresh-context 审查结论见 [acceptance-review-19.md](acceptance-review-19.md)，审查目标为 fork `0bf4bb2cab2216f567df2d4fb1729bee3cac6fe9` + a2a `10718bd2c77b375c3b5fdde3930ba75109400d7e`。审查者确认 HTTP/MCP/SQLite、设置 UI、配置冻结、CAS、事务中断、审计和反事实，但未确认“真实 provider 进程发出并消费 MCP permission request”。

具体缺口：`apps/server/src/a2a/raise-permission.test.ts:10` 用实际 manager 但控制原生 I/O 和会话上下文；`claude-permission.test.ts:71` 用实际 adapter，但 query/活跃事实受控。`claude-protocol-probe-02.json` 是真实 CLI 控制响应，仅证明收紧入口可用，没有 tool turn。因此原免确认正反例不能独立宣称 PASS。没有为满足审查临时读用户权限配置、登录、复制 Claude 凭据或发起模型调用。

另外实施者核对默认契约时发现：旧候选会对所有有 a2a 查询回调的 Claude 会话设置 synara MCP 的 default override，连无自定义和普通 Auto 会话也会被收紧。这是本票范围内的回归，已取得 `default-policy-red20` 的 4 项业务红态，再修复为仅显式免确认集合触发 override；默认/普通会话不改 provider 模式。补充 default-auto 反例、普通/失效身份，`default-policy-green21` 89 项通过；typecheck/lint/fmt 再次通过。修复提交 `7c04fb3fe`；同时将默认说明改成依会话模式和已有授权，避免把 Codex 默认口径误写成所有 provider 一致。没有开第二次审查，旧 INCOMPLETE 未上调。

主控需决定的最小选项：

1. 先明确一个**无真实模型的 provider 边界夹具**：真实 Codex app-server / Claude CLI，受控本机模型 API 仅提供工具调用输入，权限请求、批准/保留提示及 MCP 调用必须由实际进程完成。须先核实 CLI 协议与成本，不把 fake API 说成真实模型，也不绕过实际权限决策。这会新增测试驱动，当前尚未实现或批准入口。
2. 若该协议不可安全重放，授权少量真实工具 turn，并明确 Claude 的合法认证来源、模型/预算、Codex 隔离 auth 复制规则及权限请求处理。仍只用自建隔离实例，不读写用户权限配置，不操作正式工作台。当前没有拿旧票的认证许可当本次执行授权。
3. 主控接受本轮 **INCOMPLETE** 交接，检查上述默认修复 diff，另开验证切片；不关闭或宣布本票全部验收通过。

本票 brief 明确“独立审查一次”，没有继续追审。若要新增或改验收边界，应由主控决定，必要时交构思主控确认。当前软件实现和已有证据已可 review；尚未完成的外观判断和真实 provider 权限证据都保留为缺项。
