# A-16 全场原件核对（主控 #349）

**PASS，限本次09B业务证据的worker只读核对；整票仍INCOMPLETE，归档/回收未执行。** 本轮没有发HTTP/钩子、启动角色、按键或停机。计数由HTTP请求/响应/meta与原生hook文件直接重数，未拿阶段结果或主控汇总作计数答案；阶段结果和活库仅用于独立交叉关联。正式独立审查仍由主控另行安排。

原件根为 /private/tmp/t078-2-09b-run-z9ov_cco。下表原件编号分别位于该role的http-exchanges/NNNN.request.bin、.response.bin、.meta.json；每根UPS/Stop和每次PermissionRequest的精确stdin路径、原始capture/写出事件、relay回执均在 [最终JSON索引](09b-a16-final-check-03/result.json)。

| 阶段 | role | 实际全局seq | 实际POST | role内原件编号 | 许可原屏字节 |
|---|---|---:|---:|---|---:|
| I1 | ideation | 2 | 2 | 0001, 0002 | 15877 |
| E1 | executor | 3 | 2 | 0001, 0002 | 16044 |
| I2 | ideation | 4 | 1 | 0003 | 无 |
| E2 | executor | 5 | 2 | 0003, 0004 | 29103 |
| E3 | executor | 6 | 2 | 0005, 0006 | 43187 |
| I3 | ideation | 7 | 2 | 0004, 0005 | 38646 |
| E4 | executor | 8 | 2 | 0007, 0008 | 60872 |
| I4 | ideation | 9 | 1 | 0006 | 无 |
| E5 | executor | 10 | 2 | 0009, 0010 | 78282 |
| E6 | executor | 11 | 1 | 0011 | 无 |

## 逐项结论与来源

- **17 POST**：ideation6、executor11；对每个request直接读取JSON、逐字关联最新真实登记正文；response逐条解析完整六个SSE事件、tool_use/tool_result同ID，17个meta均status200、complete，原请求/响应长度与meta/wire一致。原生第二条tool_result均是真实queued request_id，没有合成同步stop/ack条目。
- **10 roots**：从hook stdin直接数UserPromptSubmit，ideation4、executor6，session/prompt_id不重；与真实登记、turn_submit_intent/turn_submitted/UPS/Stop/idle一一关联。全局seq来自真实dispatch_records与请求正文中的登记标记，表内顺序是观察值，不是阶段号推算。初始确定性target的seq1不计入两主控预算。
- **7次工具许可**：PermissionRequest原件为ideation2、executor5；Bash.command与冻结protocol argv按真实target/stop/input引用展开后相符，与SSE、hook、签字件一致。七份execute的Enter均为实际action、单字节CR，关联唯一terminal_input_written，不新增业务根。I1有原始完整capture与Enter前verified capture；其余六次另有独立fresh screen/cmp及permission-check结果。E5为78,282字节，完整分页/EOF，不截在64KiB。
- **135个hook文件**：27次调用各有stdin/started/finished/stdout/stderr五件，ideation50、executor85；finished全部exit0。UPS/Stop各10次、PermissionRequest7次。
- **目标恰一个Esc**：target/home/received.bin相对target-baseline.bin恰增加1b（baseline0字节，最终1字节）；活库仅一条emergency_interrupt_requested，actor executor、thread为本场原target。E1错目标、I3越权ack、E5已ack再停的实际relay拒绝码分别worker_target_required、recipient_required、stop_already_acknowledged；E3/E4指向同一条实际executor ack，只有一次ack wake。
- **pending→queued→delivered→原I2**：原stop d48f9f7c-187e-4fcd-b125-58ec345710b6 的created_at仍2026-10-16T21:06:39.345Z；I1真实queued tool_result的request_id为4c754e99-a65e-450f-8381-bbb92d6114a0，Stop后的relay结果pending/role_session_missing、零原I2反馈。历史保留pending/queued，E1实际turn_submitted seq176才生成delivered（21:27:34.209Z），之后原request反馈seq187；I2反馈/登记/提交各一次，关联原entry/request，不重send。依据是停机前只读事务中的inbox_deliveries、relay_requests/results、orchestration_events及原I1 POST/tool_result，并与已提交DELIVERY-I2读回交叉核对。时点仍归于主控#299的解释，不冒称用户逐字指定。
- **真实模型0**：两个实际B1 runtime-manifest的API endpoint分别为127.0.0.1:64318/64319，对应原Stage A的两只假API；source7a6edbff87df85077b3a05d38f3cfd5654cde9c1闭包312成员逐字未变，假API只产本地确定性SSE、不转发供应商。模型标签Haiku5.5/low是CLI配置，不当作供应商实际执行证明；本次没有真实登录复核。

## 核对器及证据边界

首轮 [final-check-01](09b-a16-final-check-01/result.json) INCOMPLETE是worker核对器误以为HTTP meta有dispatch_seq字段；原meta实际只携带dispatch_id，seq在原生请求登记正文/真实dispatch行。没有改原件、服务或业务，改为核对这些直接来源后 [02](09b-a16-final-check-02/result.json) PASS，增加逐根Stop/idle和单ack wake关联后的 [03](09b-a16-final-check-03/result.json) PASS。旧失败保留。

同一原件读取函数对一次性/private/tmp副本中的缺response、截断SSE、重复UPS三反例全部拒绝；副本已删除，活root未改。计数断言来自冻结protocol与用户批准预算，源码/服务/原验收文件均不改。

两个s11键后capture的output_total_changed仍保留原INCOMPLETE；这是已written之后总长变化的采集拒绝，后续独立完整s13和六次queued收据已核对，没有重按或改冻结reader。以上PASS不把这些原文件改成PASS。

## 原件最终保留位置（尚未执行）

回收计划在 [closeout材料](09b-a16-closeout-materials-01/README.md)。预定外置归档：
/Volumes/WD-Elements/a2a-evidence/2026-10-11-batch13/T-078/09b-a16-raw-01/scene.tar.gz

归档前raw仍在活root，**当前archive状态INCOMPLETE，不宣称已外置**。标准rev2会保留files/roles/<role>/http-exchanges与hooks全部原件、停机前live-rows.json及identity-receipts/snapshot；逐成员字节读回后，每原件在外置pointers/<logical>.archive.json有指针，顶层bundle.archive.json和仓内轻量指针索引关联归档。本文的活root路径在删除后按相同logical路径查files/成员与pointer，而不是只剩本报告。

必须先capture/逐字读回、从tar独立重数并签readback、再owner-bound停机；停机后只查文件/归档、不打开SQLite。两阶段窗口/命令/事件已有Git原件，当前完整raw仍需按该顺序外置保存，不能重复A15仅保留summary的缺口。09C未做、系统IME仍未验证；三窗格/真登录仍在T091/T092，整票未宣布验收通过。
