# T-078：角色离线时留存待投递——红态与实现计划

本轮红态整理 **PASS**；新产品契约 **INCOMPLETE**，产品尚未修改。A-13 原现场保持，未发送输入、未重试 I1、未清理。A-14 **NO_GO**，尚未生成启动材料。

授权与验收口径取自主控 #298 引用的用户答复，并已只读核对主仓 `.project-map/inbox/20261016T012505Z-ideation-answer-001.md`（reply_to `20261015T193027Z-executor-needs-decision-001`）。用户选择“条目留存，等角色上线再投递”；原话包含“待投递必须对发送方可见”“不再给发送方回灌反馈回合”“protocol 与预算不变”。本记录不改写地图、ticket 或原决定。

## 本轮目标与边界

目标：先用真实 daemon → 库版 inbox → 本会话 UPS/Stop → relay 重现无 executor 会话时的旧行为，给出最小修改及可核对的验证顺序。

本轮不实现 pending、不启动真实 Claude/API/目标、不对 A-13 发键或 Stop、不运行回收。下一阶段改动只涉及收件箱投递、角色登记后的恢复投递、relay 结果与反馈筛选；不修改 T-082 的审查启动、reviewer 质量串或 task card。core.ts 重叠由执行主控安排，先合入的一方先走，后合入的一方变基并重跑本切片。

**Tracer bullet**：先把“离线发送 → pending 可见、无反馈 → 角色上线 → 既有队列实际写出 → delivered → executor ack”一条链走通，再扩忙闲、重放及身份反例。

**Deep modules**：投递选择、单条锁与投递日志继续由 gates 的收件箱模块拥有；daemon 只在现有 controller 启动/初始放行入口接线。复用 `Panes.wakeThread`、`dispatch`、`readWakeDelivery`，不加轮询重送器、平行 inbox 或 operator 业务代理。

**Ubiquitous language**：本地请求 `queued:true, delivered:false` 只表示请求文件已排队；投递 `pending` 表示确定尚无可接收的角色会话；投递 `queued` 表示已登记到既有窗格队列；`delivered` 只在 `turn_submitted` 的真实写出收据存在后成立；`ack` 是接收角色另追加的确认条目。四者不互相代替。

## 已取得的事实与红态

源码基线为 `887d85cdb37889941f1ed26836d4c94b277ab5fa`；本轮只改排练检查并新增采集脚本/证据，未改产品。A-13 原 daemon/API 的 source_revision 为 `a02baddf875bc381aad742ff4076a6669ef5627f`。

| 证据 | 实测结果 | 结论边界 |
| --- | --- | --- |
| `09b-pending-live-red-01/readback.json` | gate 只读读回事件 116：真实 stop 条目 `982f243c-a163-432d-af58-bf80dca7393d` 已追加，from=ideation、to=executor；delivery=undelivered、reason=role_session_missing、relay error=wake_undelivered。事件 117：向同一发送方排入 gate feedback，dispatch.seq=3 | 原现场红态成立；只保存选定业务事件和请求/响应数量，不复制请求原文、环境或凭据 |
| `09b-pending-chain-red-01/` | 真实 UPS、`workbench/bin/inbox send --from executor --to executor --kind stop …`、真实 Stop；无 executor 会话。最终 1 条 stop，真实发送方仍为 ideation；undelivered/role_session_missing、relay_ok=false、feedback_count=1 | 新契约检查 exit 1，原因精确；daemon、relay、inbox、hooks 未模拟，仅 native liveness/PTY 为 spy；没有 Claude/API/model |
| `09b-pending-chain-red-02/red-verdict.json` | 对同一场景经交付的阶段脚本实跑：子检查 exit 1；预期红态核验 PASS；约 1.1 秒自行退出，scratch_removed=true | 证明交给主控的脚本跑过；不把预期红态的 PASS 说成产品通过 |

独立重跑的完整命令见 `09B-PENDING-RED-COMMANDS-01.txt`，输出预留 `09b-pending-chain-red-03/`，不覆盖旧目录。子命令 30 秒硬期限、阶段脚本 40 秒期限；正常经认证 daemon_stop 关闭句柄，保存 SQLite 快照并移除本轮 scratch。

根因已经在真实链路观察到，与以下源码相符：

1. `workbench/src/gates/core.ts` 的 `deliverInbox`（约 2656 行）先追加 pending 意图；当目标集合为空时抛 `role_session_missing`，catch 再追加 undelivered。
2. `inboxCall` 的 send 返回值（约 2910 行）只将 queued/delivered 视为成功，因此 relay 持久结果为 `ok:false, error:wake_undelivered`。
3. `workbench/src/relay.ts` 按实际 result.ok 追加 relay_rejected；它没有伪造发送方，条目仍正确留存。
4. `workbench/src/daemon.ts` 的 Stop transfer（约 294–303 行）对所有新回执统一生成反馈，与 result.ok 无关。因此仅把错误改为 ok:true 仍会回灌反馈，不能完成本次改动。
5. `registerController`（core.ts 约 332 行）只登记角色和 membership；`controller_start`（daemon.ts 约 194 行）没有待投递条目的恢复调用。现有 `deliverInbox` 对任何已存在 receipt 都直接返回，待投递条目目前也不会因角色上线重新进入 wakeThread。

## 拟实现顺序

### 1. 明确 pending 的可恢复条件

在单条 inbox 操作锁内先解析实际可用角色会话。对本切片的角色地址 ideation/executor，确定没有会话且尚未发生任何 wake/dispatch 意图时，追加 `pending, reason:role_session_missing`，保存原 entry_id、created_at、refs。返回 `ok:true` 和明确的 delivery.pending，不附 wake_undelivered。

必须保留旧的故障保护：没有 reason/结果的历史 pending 可能代表中断的外部写入，不能视为“确定没投过”；已有 thread/message、queued、delivered、unknown 或写出意图的条目不能自动重送。多会话歧义、身份失效、未知 PTY 写入仍按原错误/未知语义，不泛化成可重试的 pending。发送方状态按 request_id → entry_id → 最新追加投递收据关联，不重写旧 relay_results 或 inbox 条目。

发送方可见性由原请求的 relay_processed 回执事件携带 `{ok:true, entry, delivery:{state:pending, reason:role_session_missing}}`，通过现有事件读取入口可核对；本地工具回执仍如实为 queued/delivered:false。绿态同时检查发送方 launch/request_id 对应的事件与返回结果，不能只检查数据库里“有一行”。

### 2. 只过滤“成功待投递”的即时反馈

daemon 的 Stop 回执分流必须精确到成功、inbox 投递、pending、role_session_missing；仍持久化 relay_processed，只有该分支不生成额外 gate dispatch。正常已投递回执、inbox_list、stop/ack 操作的执行结果和权限错误保持原反馈机制。重复 Stop/request 继续由现有 relay 去重，不二次执行、不补发。

### 3. 角色上线后复用唤醒路径

在真实 controller_start 完成 registerController 后，通过 gates 收件箱模块扫描明确待上线的 pending 条目，重验唯一目标与现有角色/任务/项目身份，再进入同一 `wakeThread → dispatch`，不用 operator 重发原业务。保持原 entry_id/request_id，不新建 stop。

controller 首启是 unknown：此时只允许把条目登记到队列，不能向主题/安全提示/信任屏自动输入。B1 逐屏完成并经现有初始 release 后才 drain；只有实际 `turn_submitted` 才允许追加 delivered。忙或中断时继续 queued/held。接收角色的 ack 经本会话 inbox/Stop/caller 校验；不由 operator 代写。上线检查重放和重复 ack 不产生第二份 dispatch/ack。

### 4. protocol/I2 的时点需要主控核对

本轮不采用“先启动 executor 再 I1”的选项 2，也不增加 root/Messages。保持原串行启动顺序：ideation B1 → I1 留存 pending → executor B1 上线并明确初始放行 → 既有唤醒实际送达。

冻结的 I2 输入是“实际 send 执行反馈”。为保持这条 protocol 不变，拟将**原来已有的那一条 I2**延后到实际投递 delivered 后登记，pending 阶段反馈数保持零；delivery 结果与原 request_id/entry_id 关联，不重新执行 send。主控需要先核对这一时点是否符合“不再给发送方回灌反馈回合”的答复范围；若该句禁止上线后的原有 I2，不能自行删 I2、改成管道确认或额外派发。此处只列计划，未实现任何延后反馈机制。

### 5. 文件范围与审查

- `workbench/src/gates/core.ts`：只改 inbox 投递/恢复/结果判定及角色登记后的投递接线所需部分；不进入 reviewer 启动和 T-082 区域。
- `workbench/src/daemon.ts`：精确筛选 pending 回执的反馈；controller_start/初始放行后的 inbox 接线。
- `workbench/src/relay.ts`：若需要暴露回执的反馈处置，只在 relay 结果层做；沿用身份与追加式 journal，不增加第二套执行通路。
- `panes.ts`、store/合同只在现有唤醒收据无法提供所需事实时作必要小改，不先铺设新状态表。pending 已在 `A2AInboxDelivery` 类型中。
- 测试与 `workbench/README.md`：同步状态说明和实际边界；历史红态、审批签字和旧输出不改写。README 的既有 stale 项随产品修改核对，不能把本轮红态交接写成整票完成。

完成后冻结提交，交主控安排一次全新只读独立审查；审查绑定候选修订、完整 diff、红绿反例与命令。不得复用旧审查结论。通过后再给 A-14 启动材料。

## 实现后的真实链路验收矩阵

所有业务都走同一 daemon/bin-inbox/UPS/Stop/relay；仅隔离 PTY 与 native 进程观察使用 spy。角色上线用真实 controller_start 入口，spy 只替换 native spawn 外部边界，不替换 pending 扫描或 gates.registerController。检查预计如下：

| 场景 | 独立观察与判定 |
| --- | --- |
| 无接收角色发送 stop | 原条目恰一份、from=实际 ideation；发送方同 request_id 回执为 pending；relay_processed；无 gate feedback、无接收窗格写出 |
| pending 不冒称 delivered | 无 session/thread/message/turn_submitted 时，返回值和发送方事件均 pending；created_at 保持原值，不能重置 120 秒无 ack 规则的起点 |
| 随后启动 executor | 真实 controller_start 只排队；首启 unknown 时 PTY 零业务输入；明确初始 release 后原条目 delivered，entry_id 不变；真实 wake dispatch 与 CR 写出、turn_submitted 一一对应 |
| executor ack | 新角色 UPS → bin/inbox ack → Stop；from=executor、reply_to=原 stop.id；重复 ack/request 上线检查重放不重复唤醒 |
| 已有接收角色 | 原 A-13 正例同一路径仍立即 delivered；保留正常执行反馈；不把已有会话误分为 pending |
| 旧 Stop/错 launch/错 preset | 仍拒绝或不转交；没有条目/投递/ack 越权 |
| 未知写出与多会话歧义 | 不从历史 pending 意图或 unknown 自动重送，不选择任意会话，不提前标 delivered |

先让同一个离线 missing-role 信号由当前红态变绿，再补上线→投递→ack；最后运行现有 controller inbox entry/relay、权限计数、dispatch/epochs/window 回归及受影响的 T-078-1 收件箱入口检查。需沙箱外的检查合成一个阶段脚本，使用全新输出目录交主控，不请求提权。

## A-13 收尾与 A-14 的后续交付

本轮采集仅覆盖事件 116/117。下一步先生成 A-13 凭据脱敏归档（沿 A-12 只保留计数、tool_use/tool_result、错误码；不复制 raw headers/system/tools/debug 或认证环境），再交 owner-bound cleanup 的 dry-run/正式命令。绑定 root `/private/tmp/t078-2-09b-run-0fe6fcpf`、API 45050/45051、daemon 45053、target 45144/45148、ideation Claude 45962/45963，manifest 取真实 `09b-a13-b1-ideation-p1-01/09b-a13-b1-ideation-02/process-manifest.json`。主控运行前核对 PID/argv/lstart；只用 daemon_stop→panes.shutdown 关闭 Claude/目标，API 各一次 SIGTERM；逐成员归档读回通过才删 root，slot 另列不删。

A-14 只能在修复与新独立审查通过后由统一 prepare 生成。protocol 与预算仍为 I=4 roots/6 Messages、E=6 roots/11 Messages、合计 17 Messages，供应商模型 0。A-13 历史签字、失败 root 归档、真实 gate 回执及本轮红态一起纳入下一份提交脚本；RESULTS/ownership 等自产物在最后一次 git add 前生成，check-only 用同一完整路径集合模拟最终干净，不沿用旧 HEAD 断言的 commit-09b-a13.sh。
