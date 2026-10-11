# 门禁保存点核对（2026-10-11）

状态：**PASS（静态清点）／INCOMPLETE（事件重建一致性未验证）**。依据决定 01、03 和 T-075 rev 3；检查当前 `workbench/src/gates/core.ts`，基线 `7aee695f9bd8897210c9f9f6b6ae42ecb868336a` 加本卡修改。本卡未改变下列保存语义。

按规范，状态表是由事件推出的当前视图，历史以事件为准。当前没有从零重放 events 并逐项比较视图的验收。`save()` 在同一事务覆盖 tasks、当前/指定历史 attempt、当前 verification，再追加 events；只有省略 details 才记录完整 task。表中的“包含”是代码事实，不是重放通过。

| save 调用点 / 事件 | details | 还原范围与限制 |
| --- | --- | --- |
| interruptVerification / verification_interrupted | 完整 verification | 命令与未知结果齐全；task.state=submitted 依赖转换规则 |
| invalidate / revoked | reason、旧 attempt ID、spec_rev | 不含撤销后的完整 attempt 或被清空的 task 字段；须结合前序事件与撤销规则 |
| observeRun / turn_bound | 完整 attempt | 可还原 attempt；其他字段取前序状态 |
| create / create_intent | 完整 task | 本次 task 快照完整，含卡与快照号 |
| create / created | 完整 task | 本次 task 快照完整 |
| dispatch 或 claim / dispatch_intent、claim_intent | 完整 attempt；dispatch 另带请求模型/强度/tier | task.state=preparing、fence 等须按转换规则重建 |
| worktree 失败 / worktree_failed | reason | 没有直接存 task.state=paused、attempt.state=worktree_failed；单行不足以重建视图 |
| 认领完成 / claimed | 完整 task | 含认领身份与卡绑定快照 |
| 派发完成 / dispatched | 完整 attempt | 含当时 turn_id；其他任务字段取前序状态 |
| submit / submitted | 完整 attempt、commit | 候选与 attempt 可读回；task.state=submitted 依赖转换规则 |
| verify 开始 / verification_intent | 完整 verification | 含 G/C、命令列表、workspace、首条 command_intent；task.state=verifying 依赖规则 |
| merge 失败 / verification_result（v） | 完整 verification | 含 merge_failed 与命令结果；task 回 submitted 依赖规则 |
| 合并得到 M / merge_candidate | 完整 verification | 含 M；其他字段取前序状态 |
| 路径失败 / verification_result（verification/error/details） | 完整 verification 和错误 | 与直接 v 的 payload 形状不同，重放须支持两种结构 |
| 每条完成条件前 / completion_intent | verification_id、卡快照号、命令序号、command | 不含清空后的 v.result 或完整 results；须结合 completion_check，不能沿用上一条结果 |
| 完成条件未知 / verification_result（verification/failure） | 完整 verification，含 unknown result | task.state=paused 依赖规则 |
| 尾注失败 / verification_result（verification/error/details） | 完整 verification 和错误 | task 回 submitted 依赖规则 |
| 正常验收结束 / verification_result（v） | 完整 verification 与结果数组 | task.state=verified/submitted 由 v.state 推出 |
| 已集成核对 / integrated_reconciled | 完整 integration intent | task/attempt 的 accepted 状态需转换规则 |
| G 变化 / integration_conflict（expected/actual） | 旧 G 与当前引用 | 不含 task.state=submitted、verification=null；需明确转换规则 |
| 集成前 / integration_intent | 完整 intent，含 G/C/M、attempt、卡、worktree、命令 | task.state=integrating 依赖规则 |
| 引用写后 / integrated 或 integration_conflict（intent/readback） | 完整 intent 与读回 | 须区分与上一种 integration_conflict 的结构；accepted 状态依赖 completed 分支 |
| reclaim / reclaimed | attempt、archived；历史 attempt 绑定事件 | 回收事实齐全；若此前 invalidate，需先重放 revoked，并保持原 attempt 绑定 |

`saveRun()` 的每处调用均写完整 run：run_started 1 处、run_bound 1 处、run_phase 3 处、run_finished 2 处。覆盖 runs 与追加事件在同一事务，对 run 对象有完整快照，不代表整个 task 有快照。

`saveAttachment()` 的三处调用单列：

| 调用点 | 事件与缺口 |
| --- | --- |
| attach 写 creating | 没有相应 creating 历史事件；紧接外部 runtime 调用，失败时仅 events 不足以重建此中间记录 |
| attach 写 active | 覆盖后追加 attached（含完整 attachment/prompt），两者不在显式同一事务；中断窗口尚未重放验收 |
| reclaim attachment 写 ended | 同事务追加 attachment_reclaimed，含完整 attachment/archived；membership 随后另库更新 |

其他覆盖写：membership.sqlite3 的 memberships、session_presets；state.sqlite3 的 user_input_checkpoint、role_permissions（另有 role_permission_changes）。它们不经过 save，不能据 save 的事务推导它们历史齐全。

结论：每处 save 都有同事务事件，但不少事件只记增量；attachment creating 存在无对应历史事件的路径。**尚不能宣称事件重建与视图一致**，按 rev 3 留给后续切片，不在本卡改存储。

重新生成调用点清单：

```sh
rg -n 'this\.save\(|this\.saveRun\(|this\.saveAttachment\(|UPDATE SET' workbench/src/gates/core.ts workbench/src/gates/membership.ts workbench/src/gates/rolePermissions.ts
```
