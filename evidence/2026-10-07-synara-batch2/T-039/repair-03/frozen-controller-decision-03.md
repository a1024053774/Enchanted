# T-039 主控决定 03：授权 serverLayers.ts 的一处服务注册（2026-10-08，Claude Code）

主控核对了 `repair-03/projection-settlement-comparison.md` 与 `proposed-server-layer-wiring.patch`：方案复用 Synara 已有的 runtime ingestion drain、ProviderCommandReactor drain 与 snapshot 已处理序号，期限沿用 run 的 submit 期限与回收窗口，不新增重试循环、不改门禁合同，符合决定 02。

授权在 `apps/server/src/serverLayers.ts` 应用该补丁（仅给 A2AGateServiceLive 提供 `runtimeIngestionLayer`、`providerCommandReactorLayer`），条件：

1. 只做这一处注册，列入上游文件改动清单。
2. 这两个 layer 常量在同一文件中已被服务图使用（约 177、178、314 行）；Effect 按引用记忆化，应共享同一实例。必须用证据确认没有启动第二个 ingestion 或 command reactor 消费者：例如真实服务启动后，对应 worker/fiber 或启动日志只出现一次，或用受控检查证明同一服务实例。若发现重复实例，停下报告。
3. 之后按原计划：typecheck、lint、自己文件的格式检查，35 项重跑，全新隔离根的真实闭环（以原自动 run 的 completed 收据为准），用户数据前后核对，新的独立审查。
4. 若还需要改其他上游文件，或期限需要改门禁合同，再停下问主控。
