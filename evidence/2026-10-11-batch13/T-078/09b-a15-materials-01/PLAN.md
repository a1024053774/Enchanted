# A-15 待审材料

2026-10-16，主控 #315／#321。**材料静态准备；launch NO_GO。** 本包不启动 daemon、假 API、Claude、target 或窗口，不发送按键、release 或业务请求。A-14 先按独立 owner-bound 材料回收，只有主控确认后才可签 A-15 Stage A。

源码基点为当前 `f2e07d077293909bd02aa19f9e0fdda85ca3e182`，含 main 的 T-082，以及原 pending/startup 差异。合并后的 pending/controller、startup 领域与 M5、startup 入口与 M5、worker inbox、T-082 启动矩阵及结束核对共六段均 PASS，原件 outside-01/02 已随该提交冻结。旧独立审查只覆盖各自 pending/startup 差异，不外推完整 09B。本轮没有产品 src/app/bin 改动，只把材料生成器的实例和提示文件改为明确参数，增加实际首启期间的只读核对命令。

统一 prepare 生成 `09b-executable-materials-15`，带新静态 root 和当前完整源码版本。提交脚本先冻结本次文件生成器、检查与草稿，再用该源码提交生成文件包；归档逐字核对 Git 中的原件，包含完整 workbench/src（包括 T-082 的严格报告协议和 contracts）。第二次只提交材料与回执，不再事后追加 RESULTS/receipt。Stage A 签字仍空；后续角色的实际 binding 只从新 Stage A 取，不复用 A-14 root/PID/attempt。

保留既有 `a14-approved-gate-history-v1` fixture_profile 是复用已验证的阶段协议版本名，不是 A-14 实例身份；API 代码未改。实例 nonce/scenario、B1/读屏/按键 label 都由显式 `--instance a15` 产生；prompt_file 也必须显式传入，不保留默选旧材料的路径。

**Tracer bullet**：I1 模拟用户停止请求 → Bash 请求文件 → Stop/relay → stop pending、发送方可见、零反馈 → executor B1/逐屏首启 → initial release → turn_submitted/delivered → 原 I2 → E1–E6/I3–I4。**Deep modules** 保留角色输入、投递、审查与真假 API 的既有职责，没有新增业务入口。**Ubiquitous language** 区分 queued 工具回执、pending/queued/delivered 投递状态、control action 和消息；首启键写出不能算 delivered。

protocol.json 与最初冻结 protocol 逐字相同，预算仍 ideation 4 roots/6 Messages、executor 6/11、合计 17、七次工具许可、供应商模型 0。pending 阶段零反馈，原 I2 只在实际 delivered 后出现，是主控 #299 对用户答复 `20261016T012505Z-ideation-answer-001` 的解释；独立审查认为一致，但不是用户另行逐字批准的 I2 时点。stop.created_at 不重置，不能用上线时刻重算两分钟。

执行顺序：

1. 主控审阅、冻结材料，确认 A-14 回收完成后签 Stage A；只执行 STAGE-A-COMMAND，停在 READY_FOR_APPROVAL，无角色 CLI。
2. ROLE-MATERIAL-COMMANDS 第一条只写 ideation P1，binding 取新 readiness；签其 B1，先 dry-run 再 real。复用同一 API 的完整 argv/PID/lstart/ready，不另起 API；api_url 保持模板 http://127.0.0.1:0。实际成功 B1 label 再经 BIND-LAUNCH 填入 manifest 路径，不复制旧文件。
3. ideation 首启：一屏一键、每条单独批准并保存签字件。主题 ArrowUp→Auto、ArrowDown→Dark、Enter；Security notes 逐字核对后用 onboarding-notice；trust ArrowDown 到 Yes 后 Enter，不用 Digit1 或默认 Enter。B1 screen plan 仍为 security-notice + screen_text。读到旧屏就新 -02 重读，不发键；最后 manual 空提示符、0 Messages，再确认 readiness。
4. I1 分三步：批准的 test-simulated-user 输入经原正常 pane_dispatch/release；dispatch 到权限屏即停，输出父目录先存在；按实际事件/屏幕生成空签字 permission；主控核对完整 Bash command 与 ❯ 1. Yes 后，第三步经真实 Electron 窗口发一次 awaited Enter。slot 包含 stage/新 output/launch，每次唯一；拒绝旧 output/slot。tool_result 只结算异步 queued request_id，真实 Stop 后 oracle 才要求原 stop pending、零反馈和 target 零新增字节。只有 READY_FOR_EXECUTOR 才继续。
5. 生成 executor P1，串行完成独立 B1 与 onboarding。在 unknown 且已有一条 inbox 排队时，六个已批准首启键必须可写，但每键之后、下一键及 release 之前，运行生成的 observe-startup-queued 命令：通过真实 inbox_list 刷新原 stop，要求 queued、无 delivered 历史、无 I2，unknown/active=null、原 queue/message/thread 不变、业务写出=0、API POST=0。任一失败立刻停，不签下一键。该观测器在六份真实候选原件上通过，并拒绝真实 M5 错误收据原件。
6. executor manual 空提示符、首启观测全过后才确认 readiness。先签并 arm 原 I2（不发输入），再签 E1 并 initial release 原排队 stop；actual turn_submitted 后才 delivered，原 I2 恰一次且关联原 request/entry。E1 到许可屏停，逐阶段推进；角色启动同一时间只一个步骤。
7. 后续自动根只读实际 gate feedback/inbox wake，全局 dispatch.seq 按事实核对，工具 argv 用实际 ID 替换；不重做 send，不由 operator 代发业务 send/stop/ack。每次许可读屏核对后只选一次 Yes；无工具阶段不应出现许可屏。

未批准阶段的同一个 HTTP 请求最多等待 180 秒；批准到位才给 SSE，超时整场 INCOMPLETE，禁止重试。Messages 以实际 POST 计数，不能以历史数组长度计数。任何 409、超预算、意外工具/屏幕、身份或命令不符、未知收据、首启业务输入、pending 冒充 delivered、I2 数量不符，均停下保留，不按第二次 Enter、不热替换 API、不接管旧 PTY。

本轮只跑了纯文件/身份比较/脱敏/已保存收据检查，未重跑新 A-15 的真实 HTTP、Electron 或 Claude。原 A-14 无模型排练可追溯阶段协议边界，本轮合并回归可追溯修复后的产品边界；两者均不替代 A-15 的逐阶段实跑。cleanup dry-run/正式动作与所有 Stage A/B1/业务阶段仍未执行。
