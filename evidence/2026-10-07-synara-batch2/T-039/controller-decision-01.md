# T-039 主控决定 01：修复原生观察接缝后重跑（2026-10-08，Claude Code）

主控核对：`orchestration.ts:32` 在 shell 投影 turn 为 null、provider 已有 activeTurnId 时直接判 `identity_conflict`；`:23` 把 interrupted 一律判 `run_external_unknown`，使绑定原 attempt 的 reclaim 也被拒。run-01 的时间线（shell updatedAt 06:07:10.522，provider turn startedAt 06:07:16.211，拒绝 06:07:16.233）支持"投影滞后"判断。BLOCKED 结论与独立审查 FAIL 原样保留。

授权在本 ticket 内修复，不另开 ticket。范围限 `apps/server/src/a2a/orchestration.ts`、`service.ts` 及其测试（T-037 已关闭，这两个文件本轮归你；不碰 T-038 的 membership/OPTIONS 段）。

1. 身份分类：thread、cwd、provider 任一不符，或 shell 与 provider 两侧都有 turn 且不同，仍是 `identity_conflict`。shell 尚无 turn、provider 已有 activeTurnId 的情况归为"尚未投影"：run 继续在原有有界观察中读取，不推进业务，也不判冲突；该状态持续到 run 期限仍不一致，按原 deadline 结果处理。不加单独的重试循环或 sleep 补丁；若能以一次共同快照读取（同一时刻的 shell 与 provider）解决，优先该方案，并说明选择理由。
2. 回收：属于该 attempt、已 interrupted 的 thread，reclaim 可以按原受锁路径停止、归档并读回确认；run 观察中 interrupted 仍不算成功。error 与未知状态仍拒绝。
3. 先红后绿：用受控的 thread 服务替身复现"投影滞后"与"interrupted 后回收"两种输入，保留修复前红态；反例需显示真实身份更换（两侧 turn 都非空且不同）仍被拒绝。T-037 的 18 项与 T-036 的 17 项在新候选上重跑。
4. 修复冻结后，用全新证据子目录与全新隔离根重跑真实闭环（旧 run-01 证据不覆盖）。真实模型调用只做必要次数。
5. 用户数据核对：重跑前后各记录一次 `~/.codex` 下 config.toml、rules/ 的大小与修改时间，用户 Synara 数据目录（若存在）的顶层列表与修改时间，以及 `herdr status` 的只读输出；只读，不复制凭据。
6. 完成后做一次新的 fresh-context 独立审查。若修复超出上述两个文件或需要改变门禁契约，停下问主控。
