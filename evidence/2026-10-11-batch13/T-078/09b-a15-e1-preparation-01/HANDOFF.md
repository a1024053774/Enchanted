# A-15 executor readiness、原 I2 与 E1 待批

先提交主控 #328 的 executor B1、六键/各屏签字、六次 queued 观测与实际 bind-launch：`019414f9cdea56902bc668c409de65096b0b5af5`，九项尾注齐。六个观测均 PASS：原 stop 仍 queued、历史无 delivered、无 I2、unknown/active=null、零业务写出；s13 空提示符/manual 为主控实际读回。本轮不重新操作这些现场。

后续命令按以下顺序由主控逐条运行；本轮全部未执行：

1. executor P1 的 `READINESS-CONFIRM-COMMAND.txt`。先调用已有 observe-startup-queued 再刷新一次原 stop，输出全新 `onboarding/readiness-queued-readback.json`；通过后核对六次原件、s13 的绑定及空提示符/manual 标记、executor 实际 POST/请求/响应均为 0，排他创建 readiness.json。屏幕标记辅助 #328 的人工读回，不冒称独立渲染验收。不 arm、release 或发送输入。
2. 审签 ideation `phases/I2/approval.json`（两字段空），再执行该目录的 `ARM-COMMAND.txt`。只登记原有 I2 的单次应答批准，预期 ARMED；不 pane_dispatch、不 release、不调用模型、不发送输入。此时仍无 I2 回合；原 I2 只在实际 delivered 后响应。这沿用主控 #299 对用户答复的解释，不冒称用户逐字批准了这个时点。
3. 审签 executor `phases/E1/approval.json`（两字段空），执行 `INITIAL-RELEASE-COMMAND.txt`。真实驱动核对 executor readiness 与已 arm 的原 I2，然后仅 pane_release 原排队 inbox 消息，不重新派发、不重做 send。原消息为 `b91b5f60-62e9-4983-b48e-f73630f1f854`，关联 stop `c3ab1493-5c73-4af5-947f-a0f16f19d6c7`。E1 是冻结 protocol 的 E_WRONG_TARGET；第 1 条实际 POST 下发 Bash command，真实 PermissionRequest 后保存事件/原屏，READY_FOR_PERMISSION 即停，不发 Enter。真实 seq/request/tool_use ID 继续由现场登记，不写死全局序号。
4. E1 到许可屏后，保持原屏，不批准工具，执行本目录 `DELIVERY-I2-READBACK-COMMAND.txt`。它先用既有 I2 collect oracle 等待原有回合的 ACK/Stop/idle，再只读现有事件、收据和 HTTP POST 原件数，核对 turn_submitted→delivered、原 I2 恰一次和原 request/entry，保存新 `delivery-i2-readback-01.json`。命令不 arm、release、dispatch、send、ack 或按键。任何错误立即保留并停止；已存在的输出不覆盖。

原 request 为 `80ef9485-80df-43f3-9791-bab43261cb5b`；原 stop.created_at 为 `2026-10-16T10:51:40.728Z`，不得因上线或投递而重置。两个批准草稿都携带这些原值和相同 target binding，签字字段仍空。读回还要求 delivered.message 是原队列消息，投递收据时间等于该消息 turn_submitted 事件时间，且 relay_feedback_registered 在该事件之后、只有一条，关联原 request/entry 与 I2 的真实 dispatch。

到该停点，预期实际 POST 为 ideation 3（I1=2、I2=1）、executor 1（E1 的 tool_use）；E1 尚未执行工具、尚未产生第 2 条 Messages。原 I2 无工具、无权限屏；E1 全回合预算 1 root/2 Messages、一次权限，本次仅到首条 Messages/许可屏。角色全场预算仍 ideation 4/6、executor 6/11，供应商模型 0；E1 Enter 及 E2 后续各阶段另批。

所有当前脚本、批准、readiness 原件、I1 收据、六次观测、s13 与实际 executor manifest 路径已静态核对；executor readiness、新观察/I2 arm/E1 dispatch/I2 collect/最终读回都是未来产物，本轮不造占位或执行。语法/文件检查 PASS 不能替代上述真实读回，运行状态仍 INCOMPLETE。

准备期附带问题：检查 A-14 既有排练 SQLite 的 `mode=ro` 连接仍更新了 SHM 读标记，未影响 A-15。`historical-sqlite-read-side-effect-01/` 保存提交原件和读取后的两个 32,768 字节版本及操作说明；留存后已逐字节恢复受控历史 SHM，没有丢弃异常副本或使用 git reset。此后不再直接打开该历史数据库；新命令的现场读库是主控后续执行的只读观察，不用于归档原件。
