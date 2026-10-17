# A-15 全场核对（2026-10-16，主控 #332）

**PASS：09B 冻结 protocol 的本场阶段与预算核对。T-078 整票仍 INCOMPLETE。** 本文是 worker 从主控已执行证据与现场文件作的只读读回，不是独立审查。没有启动进程、请求 API、调用 gate、操作窗口或读 SQLite。回收未执行。

运行的业务版本为 `dedd4f66bc424610183cbff2d7114e991483e1c6`；完整 reader harness 为 `c0c5caee3e70e58abadbd55efa4eade72a44370b`；主控 #332 的新增证据与签字件冻结于 `34aa4e130`。后续文档提交不改变这些运行版本。原 58 文件中只改三个 reader caller，其余 55 文件逐字节不变，新包共 65 文件，见 [harness manifest](09b-a15-reader-harness-01/manifest.json)。

机器读回原件为 [final-check-04](09b-a15-final-check-04/result.json)，复核脚本为 [a15-final-evidence.py](a15-final-evidence.py)。它直接计数现场 requests.ndjson、responses.ndjson、逐 POST 的 HTTP 原件和状态，并核对原生 UPS/Stop/PermissionRequest trace、登记 bound 文件、逐阶段执行/读回和签字件；只输出白名单。初稿 check-01 因误用 bound.dispatch_id 而 KeyError，未作通过证据，原件保留；实际字段为 id/seq。02、03 是较早核对，最终以 04 为准。

## 阶段、实际 POST 与全局派发顺序

以下每行恰一根实际提交。阶段顺序按真实全局 dispatch.seq 排列；E4 与 I3 的并行等待不改写为预设顺序。

| 阶段 | 全局 seq | dispatch id | 实际 POST | 工具许可 | 实际结果及来源 |
|---|---:|---|---:|---:|---|
| I1 | 2 | c9f2322a-0526-4430-a3d6-98b376b8b140 | 2 | 1 | [execute-02](09b-a15-b1-ideation-p1-01/phases/I1/execute-02/result.json)：真实 send 排队；Stop 转交为 stop，pending、零反馈 |
| E1 | 3 | b91b5f60-62e9-4983-b48e-f73630f1f854 | 2 | 1 | [readback](09b-a15-b1-executor-p1-01/phases/E1/readback-03/result.json)：原 inbox 唤醒；错目标被 worker_target_required 拒绝 |
| I2 | 4 | dac454b5-d34f-41fa-8f0e-98f0179c5280 | 1 | 0 | [collect](09b-a15-b1-ideation-p1-01/phases/I2/collect-01/result.json)：原 send 的 delivered 执行反馈，只确认 |
| E2 | 5 | 623e59a9-bb47-40e3-ad09-f78107d0f2c2 | 2 | 1 | [readback](09b-a15-b1-executor-p1-01/phases/E2/readback-03/result.json)：真实 stop，经门禁仅写一次 Esc |
| E3 | 6 | 6797a583-ff67-49fd-8412-e5f2159fcebd | 2 | 1 | [readback](09b-a15-b1-executor-p1-01/phases/E3/readback-03/result.json)：实际 from=executor 的 ack；伪造 --role ideation 无效 |
| I3 | 7 | d4bccb93-d72e-4ff9-8de9-0e6a1e6c8b98 | 2 | 1 | [readback](09b-a15-b1-ideation-p1-01/phases/I3/readback-03/result.json)：越权 ack 被 recipient_required 拒绝 |
| E4 | 8 | f9b9e570-7bcd-4e03-a3b9-c7155c30fe01 | 2 | 1 | [readback](09b-a15-b1-executor-p1-01/phases/E4/readback-03/result.json)：重复 ack 返回同一条目；没有第二次唤醒或 Esc |
| I4 | 9 | 5d4efb1c-52df-4060-b8be-3e57eb3a37d3 | 1 | 0 | [readback](09b-a15-b1-ideation-p1-01/phases/I4/readback-03/result.json)：真实拒绝反馈，只确认 |
| E5 | 10 | dade92bf-ef34-4e8d-824c-6168c21f2adc | 2 | 1 | [readback](09b-a15-b1-executor-p1-01/phases/E5/readback-03/result.json)：已 ack stop 被 stop_already_acknowledged 拒绝 |
| E6 | 11 | bd0d588f-5c43-4012-b41c-3adcf5647d6f | 1 | 0 | [readback](09b-a15-b1-executor-p1-01/phases/E6/readback-03/result.json)：最终确认与 Stop/idle |

ideation 为 **4 roots / 6 POST**，executor 为 **6 roots / 11 POST**，合计 **10 roots / 17 POST**，与 [冻结 protocol](09b-materials-01/protocol.json) 一致。每个 POST 均有对应 HTTP request/meta/response 原件、200 状态和完整 6 个 SSE 事件；没有 409 或重试 POST。17 次按实际 HTTP 统计，既非只数成功响应，也非把 tool_result 当新根。目标初始派发不计入两个主控的根预算。

两个真实 Claude Code 2.1.296 会话的原生 UPS 与 Stop 分别为 4/4、6/6，prompt_id 与真实登记/阶段对应，hook exit 均为 0。PermissionRequest 为 ideation 2、executor 5；七份实际 Electron Enter 回执、签字批准与 action id 逐一对应，均 form=action、text=CR，没有记成 message 或新增根。详细 action/command id 在 final-check-04.tool_permissions。

真实供应商模型回合 **0**：两份原始 runtime-manifest 的隔离环境分别指定 loopback `127.0.0.1:64830`、`:64829`，复用 Stage A 已登记 API 59387/59388；17 次均由这两只假 API 的 HTTP 原件承接。实际角色为交互 Claude CLI，目标为确定性 codex-receiver，不能外推为真实 Codex 或模型自主判断。

目标 received.bin 相对 target-baseline.bin 的完整差值恰为 **`1b`**，基线为空、最终 1 字节。E1 前为 0，E2 后为 1，之后 E3/I3/E4/I4/E5/E6 均保持 1。E2 的 relay 结果为 interruptRequested=true；E3/E4 的 ack id 均为 `324b5a30-e6d0-48c0-9f07-58532e66f1b3`，只有一个实际 ack。上述身份、错误码与目标字节均有逐阶段 readback，不以工具 queued 回执代替门禁执行结果。

## pending → delivered → 原 I2

I1 的实际 request 为 `80ef9485-80df-43f3-9791-bab43261cb5b`；stop 为 `c3ab1493-5c73-4af5-947f-a0f16f19d6c7`，实际 from=ideation、to=executor；参数中 --from executor 没有覆盖调用者。created_at 原样保持 `2026-10-16T10:51:40.728Z`。I1 执行结果为 pending/role_session_missing、relay ok、feedback_count=0，不显示已送达。

executor 启动只将原 inbox 消息排入 unknown 窗格。六次逐键 [queued 读回](09b-a15-b1-executor-p1-01/onboarding/s11-queued-readback.json) 均 PASS，逐份文件 s1/s3/s5/s7/s9/s11：仍 queued、无 delivered 历史、无 I2、零业务输入/POST，首启键可以送达而不 drain。主控完成首启、确认 readiness 并签 I2 arm/E1 release 后，原 dispatch b91b5f60… 才真正提交。

[delivery-i2-readback](09b-a15-e1-preparation-01/delivery-i2-readback-01.json) 的实际 turn_submitted=**176**；delivery.created_at=`2026-10-16T11:11:03.106Z`；随后 feedback=**187**。反馈、I2 注册、I2 提交各恰一次，关联原 request/entry，无第二次 send 或人为追加反馈。I2 的实际全局 seq=4，早于后来 I3/E4 的交错不代表提前投递。

延后 I2 是主控 #299 对用户 answer `20261016T012505Z-ideation-answer-001` 中“pending 时不回灌反馈”与“protocol 与预算不变”的解释；独立 pending 审查已核对该解释一致。这里不把 delivered 后的具体时点冒称为用户逐字批准。

## 许可原屏恢复与限制

主控 #332 外侧复验 [outside-recheck](09b-a15-reader-fix-01/outside-recheck-01/result.json) 九组 contract_verified=true、scene_actions=0。E4 原 dispatch 屏只有 65,536/76,125 字节；旧原件与未签 permission-01 未改。新 screen-02、[恢复收据](09b-a15-b1-executor-p1-01/phases/E4/screen-recovery-02/result.json)、screen-03 均完整，旧屏为新完整原件的严格前缀；permission-02 经主控核对签字后，一次 Enter 的完整读取校验通过。E5 读屏 93,747 字节与 dispatch 原屏逐字相同，check-only、Enter、读回均 PASS。

主控报告的 E4 check-only 两次失误如实保留：签前 permission_approval_required；签后因目录已存在 FileExistsError，管道吞掉退出码。因此 **E4 check-only 不是 PASS**。实际 Enter 在 build/窗口/按键前独立完成全屏读取与绑定校验，回执含完整 capture，随后只一次 CR；不靠失败的可选预检作批准依据。BSD cmp -n 的 EOF 误报由主控另用 Python 前缀比较核对；最终全文件比较以 screen-03 与恢复完整原件为准。

历史许可屏审计见 [HISTORICAL-SCREEN-AUDIT](09b-a15-reader-fix-01/HISTORICAL-SCREEN-AUDIT.md)：E1/E2/E3/I3 未截断；I1 的 16,322 字节与 Electron offset 一致，但当时缺直接 gate total 原件，直接完整性仍 **INCOMPLETE**，不改旧 PASS 结论文件，由主控/独立审查判断影响。全票还有真实 120 秒 09C、三窗格联合视图及新候选独立审查等缺口，见 RESULTS 汇总。
