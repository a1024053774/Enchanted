# T-056 执行主控决定 01：批准 wsRpc.ts 的入口接入（2026-10-09）

依据 ready_rev 1。T-056 的验收明确要求"非消息类输入在 WS RPC `dispatchCommand` 入口按枚举的命令类型记录"，该入口在 `apps/server/src/wsRpc.ts:1322`（调用点 :1338），属于 ticket 指定的观测点；接入是 spec"对上游只做注册与挂载"的范围。

批准只额外修改 `apps/server/src/wsRpc.ts`：import 并调用放在 `apps/server/src/a2a` 内的记录函数，位置在 `dispatchCommand` 入口；存储、关联、去重、失败策略与重放留在 a2a 模块；不改命令契约，不给命令加字段，不在 `dispatchOrchestrationCommand` 内部其他调用点埋点。列入上游清单。

临时线程清理（`useTemporaryThreadLifecycle.ts:99/:115`）等自动派生命令：按 ticket 与 spec 第 3 节处理；若窄探针证明现有字段不足以区分且需要改契约或加字段，再停下上报，不自行添加 origin 字段。
