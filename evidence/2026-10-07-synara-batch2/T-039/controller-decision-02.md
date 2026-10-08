# T-039 主控决定 02：投影落定（projection settlement）后再判定回收（2026-10-08，Claude Code）

repair-02 的 BLOCKED 与第二次独立审查 FAIL 原样保留；手工补充回收不改判原 run。真实 run 已证明 submit → 独立 oracle（12/12）→ CAS 集成成立，剩下的是同一类根因：门禁把 provider 的即时状态与滞后的 SQLite 投影当作同一时刻的事实。两次补分类都是在治标，本轮改为在根因层处理。授权范围仍限 `apps/server/src/a2a/orchestration.ts`、`service.ts` 及其测试；改门禁合同或上游文件先问主控。

1. 先调查 Synara 已有的"等投影追上"机制，再选方案：`OrchestrationEngine.getEventHighWaterSequence`、`readEventsThrough`，以及 `CheckpointReactor.ts`（约 2628、2849、2930–2967 行）、`ProviderCommandReactor.ts:2807` 对 domain high-water 的用法。写一页对照：这些机制能否表达"投影已处理到某个序号"。
2. 优先方案：门禁在需要同时判断 provider 与 shell 的地方（run 的 waitForIdle、reclaim 的 stop/archive 读回），以一个明确的序号屏障判断投影已落定，再读取 shell 并分类；超出原有期限仍未落定，用既有错误码，不新增"等等再试"的循环。若 Synara 没有可用屏障，再考虑在原有的有界观察内把"provider 已退出、shell 仍为 running"和"stop 已发出、读回尚未 stopped"作为未落定状态继续观察，并写明为何没有更好的机制。
3. 不变的拒绝：error、两侧都非空且不同的 turn、provider 仍活跃但 shell 显示 interrupted 等矛盾状态，仍拒绝。
4. 先红后绿：用受控边界替身复现"turn completed + session closed，shell 仍 running"与"stop 已执行、读回滞后"两种时序，保留父版本红态与反例；35 项重跑。
5. 用全新根和全新证据子目录（例如 `repair-03/`）重跑一次真实闭环；验收以原自动 run 的 completed 收据为准，不再手工补回收。用户数据前后核对照旧。
6. 新的 fresh-context 独立审查。
