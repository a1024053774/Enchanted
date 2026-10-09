# T-056 执行主控决定 02（2026-10-09，依据 ready_rev 2）

针对 needs-decision-25、submit-transport-11。

1. **Unblock（`reconcileProviderDelivery`）属于本票范围。** ticket 目标是“任何会话、任何渠道的输入都被记成数据”，spec 第 3 节观测点 4 规定发现界面绕过入口时补记录点。挂接位置在已获准的 `apps/server/src/wsRpc.ts` 内该 handler 的入口，记录实现留在 a2a 模块；不改该 RPC 的契约与语义，不新增其他上游文件。
   - 记录单位：**每个到达服务端的请求一条输入**（与 dispatchCommand 按命令记录一致），目标键带 thread 与该请求的 eventSequence；服务端看不到“按钮点击”，不在服务端发明按钮级分组。若用户之后要按钮级合并，作为后续需求处理。
   - 补真实入口红绿（父修订无记录 → 候选有记录），并纳入矩阵。
2. **BranchToolbar `:343/:393` 的自动停止**属于已批准的“需设置 origin 的 web 自动派生调用点”，补 `origin: ui-derived`，不改停止逻辑；补反例（不派生人工介入、不算用户明确决定）。
3. **prepareQuitResume 的普通 thread 项目键**：从服务端 thread 快照取已知 projectId 补齐，并加字段断言。
4. **submit**：Herdr 期不走门禁 submit，也不需要 attempt/session/fence。交付形式为：fork 提交 + a2a 证据提交 + RESULTS + 终端 DONE 行（与 T-061、T-057 相同）。worker 角色卡里的“显式 submit”在 Herdr 期由此替代。不要读取正式工作台 endpoint。
5. **独立审查**：授权在最终冻结候选上再做一次 fresh-context 只读审查；c7 的 FAIL 结论原样保留。

上述第 1 项的记录单位是执行主控按现有入口粒度做的默认，已报构思主控转用户，用户若改主意另行修订；blocking 问题 `20261009T190952Z-worker:s11-t056-issue-001` 由用户关闭，worker 不必等关闭即可继续。
