# 主控 #354：09C 第 1 场只读还原与 harness 缺陷

状态：**诊断 PASS；场次 INCOMPLETE／NO_GO，禁止续行**。本次仅 SELECT、原文件读取与只读 pane_status；未执行 Stop/dispatch/release、许可 Enter、恢复时钟、归档或停机。[结构化读回](result.json) 与下列原件分别保存，没有改写被覆盖的 execute-02/result.json。

## 实际发生的 C-I1

- Electron 原 driver journal 的 terminal-key 请求 id6 为 Enter，唯一 delivered/written 回执 request_id `82ac3820-b39a-4843-90da-06e9b6f6b170`。daemon intent155 / written156 与同一 `user_inputs.form=action,data=CR` 对应。[单次 Enter 原收据](one-Enter-receipts.json) 只提取已有日志，不补发键。主控第二次执行在 mkdir 被拒；原 journal 没有第二个 terminal-key。
- HTTP 的 ideation 0001 下发真实 C_SEND_STOP/Bash.command；0002 收到同 tool_use_id 的真实排队 tool_result：request_id `2926ba23-f599-4a54-a4ab-72d256cd8e85`，queued=true、delivered=false。两次均完成 200；API 中性确认后，真实 Stop161 的 last_assistant_message=C-I1_ACK。
- Stop/relay 产生 stop **`fe5603b6-1abf-4045-b267-031e32f762ce`**，from=ideation→executor；**created_at=`2026-10-16T22:35:52.492Z`**。原 request/key/caller/prompt 可由 [stop、relay 与事件](stop-relay-and-events.json) 核对。executor inbox dispatch seq3 于事件167 turn_submitted，delivery 记录实际为 **delivered，22:35:52.800Z**；relay_processed168，原执行反馈 dispatch seq4/event169，ideation idle170 后反馈提交178。
- 因此业务 wall 时钟已经以原 stop.created_at 开始，**本地 clock-origin.json 不存在不代表未开始**。不得重写 created_at、现在补一个新起点或继续“提前 stop”测试。

## C-I2 没有在等许可批准

原 delivered 反馈已作为新根提交并通过 UPS185，但假 API 的 C 阶段解析器报 `C_actual_delivery_required`，没有生成 C-I2 tool_use/PermissionRequest。拒绝发生在阶段批准屏障之前；五阶段虽然已经 arm，也不是“请求还在等批准”。其原因是把反馈 envelope 当成执行结果，不是产品实际未投递。原请求/响应 meta 和日志投影见 [HTTP 读回](HTTP-metadata-and-tool-results.json)，原 hook stdin/started/finished/stdout/stderr 副本与索引见 [hook-index](hook-index.json)。完整 HTTP request/response 原件仍在活 root，须由回收工具先脱敏外置保留。

诊断快照时实际 POST 已是 **ideation13、executor11**（必须按 http-exchanges/*.request.bin 计数，不能数 requests.ndjson 行数）。ideation 前两次是 C-I1 成功交换，后续 409 均 C_actual_delivery_required；executor 的首条 C-E1 保持 SSE 到 150 秒后因 C_executor_hold_deadline 不完整结束，原生 CLI 随后重试得到 dispatch_replayed。计数可能在快照后继续增长，最终归档须重新独立重数；不能把这些 POST 从失败预算中抹掉。目标仍相对 baseline **零字节变化**，无 ack、无 emergency interrupt。本场已越过 C-I2 <120 秒窗口且超 POST 预算，必须重建第 2 场。

## 四类必须修的 harness 缺陷（本轮只给方案，未改源码）

| 位置 | 实际契约／错误 | 最小修复方向 |
| --- | --- | --- |
| `t078_09c_driver.py:333` | 真实 queued tool_result 与 relay_requests 有 request_id；relay_results.data 仅 `{ok,entry,delivery}` | 用前面已从 tool_result 取得、并经 launch/prompt/key 唯一核对的 request_id 写 origin；不在业务结果中合成该字段 |
| 同文件 NativePermission.actual 约258–265、observe 约467–470 | 从匹配 stop 的 relay_results.data 再读 request_id，会在 C-I3 等路径重现 | 统一以真实 relay_results.key 关联唯一 relay_requests 行，再核对实际 controller launch/native session/caller/prompt/stop，读取该行 request_id；歧义或身份不符拒绝，不加 fallback |
| 同文件 phase_for_dispatch 约158–171 | 实际 feedback JSON 为 `{key,request_id,replayed,result:<业务结果>}`，但代码在外层读 ok，并把 entry/delivery 又多套一层 result | 保留 request_id 在 envelope；业务判断统一读取 envelope.result。逐项修 C-I1→C-I2 的 delivered、C-I2→C-I3 的 stop_too_early、C-I3→C-I4 的 interruptRequested，不改 product/反馈格式 |
| `t078_09b_i1_permission.py:53,133` | global OUTPUT 在 mkdir 成功前已指向旧目录；重复调用 FileExistsError 后顶层 except 覆盖旧 result | 每次入口先清空 OUTPUT，独占创建新目录成功后才绑定为本次拥有的输出；创建失败只报错，不写任何旧目录。正例首次错误仍保存；反例重复执行零 build/Electron/Enter，原 result 逐字节不变 |

此外保留上一诊断已经指出的 `start_first_turn` 多余 pane_release：下一修订删掉该行，保留 initialize 的初始放行。它不要求产品改动。

[真实字段反例](field-assumption-reds.json) 已用本次数据只读复现 `receipt['request_id'] → KeyError('request_id')`，同一 queued 回执与 relay_requests 则正确关联 request_id；调用当前真实 phase_for_dispatch 只读入口对实际 feedback 得到 C_actual_delivery_required。原首份 traceback 已被重跑覆盖，不能冒充恢复了原字节堆栈；结合实际字段、已完成的 Stop/idle 与源码执行顺序，定位为 origin 构造处的字段访问，而不是 Enter 未送达或工具没有 request_id。

## 下一场前的证据要求

不能只改两处报错后直接重建。把本场 queued tool_result、relay_requests/result、feedback envelope 原形作为固定输入，先取真实入口红态，再修、再绿；C-I1～C-I4 的字段连接全部覆盖。必须把初始化/实际 start、许可入口的结算回调、真实 daemon/inbox/Stop/relay、phase_plan HTTP 接成一次性无模型排练；不要手动模拟“成功 relay”避开这次失败点。C-I3 的 owner/target/window 全绑定、真实 >120 秒及 <150 秒边界仍需证明。

第 1 场先按 [回收材料](../09c-attempt-1-closeout-materials-01/README.md) 保留逐 POST/hook、错误、不完整 SSE 与可追溯重建，归档逐字节读回/独立重数先于 owner-bound 停机；不得先关服务再补归档。第 2 场 [最小计划](../09c-attempt-2-plan-01/PLAN.md) 当前未绑定源码、未签、NO_GO。

交接期间主控又把 [run_09c_timed.sh](../09c-ci1-start-diagnosis-01/run_09c_timed.sh) 与 [run_09c_timed.log](../09c-ci1-start-diagnosis-01/run_09c_timed.log) 放入旧诊断目录。本次已读并原样纳入提交：日志18:35:53明确记录 `KeyError: 'request_id'` 后立即 STOP；它只保留末行，没有原 Python traceback，仍不能恢复丢失的第一份 result。脚本作为历史证据，**不能原样复用到第2场**：它从 `stop_entry` 取ID，但 C结算返回 `stop`；成功匹配含宽泛 `[A-Z_]+`，必须收紧为每阶段明确状态，不能让 INCOMPLETE 通过。C-I2 目前复用 B许可入口，缺少按 Enter 前的早停年龄硬检查；第2场须补独立的提前截止/余量与不发键反例，不能只在结算后发现已经超过120秒，否则同一条 stop 命令可能被当成晚停执行。原场次本次没有到达这一步，未实际造成中断。
