STATUS: PASS
TARGET: frozen Synara candidate `8aba12a4911ce6bc682dbb75d343b3ae08529202` (parent `fc9e36c75af3bbcf701551abbb911883b94217c2`)

EVIDENCE:
- 冻结检查：`git rev-parse HEAD` 匹配候选；候选 diff 仅为 `service.ts`、`service.test.ts`、`layer-sharing.test.ts`、`serverLayers.ts`。
- 合同来自 `brief-T-039.md`、controller decisions 02/03 与 M1 spec 验证接缝 2；源码屏障位于 `apps/server/src/a2a/service.ts:41-46`，deadline/error 边界位于 `:48-85`，stop/archive 落定位于 `:161-183`。
- 真实门禁运行 `real-01/run.json`：自动 `run` 退出 0，task 为 `accepted`，`run.outcome=completed`；`events-final.json` 持久序列为 `submitted` → `integrated` → `reclaimed` → `run_finished(completed)`，未依赖手工 reclaim。
- `real-01/native-submit-raw.json` 记录真实 `a2a_submit`，task/attempt/session/fence/spec_rev/worker commit 一致；`native-archived.json` 独立读回 `latestTurn=completed`、session `stopped`、`archivedAt` 非空。
- CAS 集成命令为 `git update-ref ... C G`，事件读回与 `real-01/independent-readbacks.json` 的 `git rev-parse refs/a2a/integration` 均等于 worker 提交；同一 attempt/fence/spec_rev 贯穿交付、验证、集成和回收。
- 独立 oracle 对 starter 红态失败，对候选 12 项通过；contract/oracle 未变，原始命令结果和 `state.sqlite3` 证据均保留。
- `cleanup.json` 显示隔离 Codex home/overlay 已删除、服务进程组无残留；用户 Herdr/Codex/Synara 的 before/after 元数据与只读 status 一致。
- `sharing-proof.json` 证明生产组合中 ingestion/command 各单实例且 gate drain 使用同一实例；重复 `ingestion-2` mutant 被 `layer-sharing.test.ts:118` 拒绝。
- 候选有界复核命令通过：3 个相关测试文件、12/12 tests；35 项 orchestration/delivery-recovery 均通过。父版本反事实为 3 failures/7 pass，故已知坏实现被拒绝。

FINDINGS:
- 无可达违规。

COUNTEREXAMPLE:
- 父版本 `fc9e36c75af3bbcf701551abbb911883b94217c2` 未能通过投影落定测试；重复服务注册 mutant 产生 `ingestion-2` 并失败；starter pagination 实现被独立 oracle 判红。均被当前证据拒绝。

LIMITATIONS:
- `codex-launch-binding.json` 明确记录进程在 `ps` 捕获前退出；只有冻结 launcher/spawn 精确输入及 native version/settings，不能声称观察到真实 OS argv 或供应商实际 tier。
- 用户数据核对限定为元数据与只读 status，不是全内容审计；不外推 M1 发布。
- 全仓 `bun run test` 仍因 3 个 desktop 测试失败而退出 1；本结论仅覆盖本候选的相关服务与真实 T-039 闭环。
