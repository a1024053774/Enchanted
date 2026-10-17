# 09C 第3场全场核对（主控 #373）

**业务场景PASS；worker原件核对PASS；全新独立终审未执行，整票INCOMPLETE。** 所有阶段由执行主控依据用户rev2授权代签，键为批准的test-simulated-user自动化，不冒称用户亲手操作。真实Claude Code2.1.296两角色，本地假API、供应商模型0，确定性receiver而非真实Codex。

运行输出/签字先独立提交 `91fe77992e15b33170b462e67feab4e0b034fa32`。业务/app/acceptance仍等于7a6edbff8，当前运行工具等于已排练77865b044，完整材料源码为8f359d364。主控计时段结果是 [timed-01](09c-c3-preparation-01/timed-01/result.json)。worker另读原HTTP/hooks与一次只读数据库事务，[live-06](09c-c3-final-check-01/live-06/result.json)为本表来源，不只采信driver的PASS。

## 原件与逐阶段计数

现场root为 `/private/tmp/t078-2-09c-run-kwp5kj5g`。HTTP来源 `roles/<role>/http-exchanges/NNNN.request.bin/.response.bin/.meta.json`；hooks来源 `roles/<role>/hooks/<trace>/started.json/stdin.bin/stdout.bin/stderr.bin/finished.json`。核对器只在内存解析原请求/响应，不把认证信息或完整系统提示复制入Git。原件尚在活root，**外置归档未跑**；后续按[回收顺序](09c-c3-closeout-materials-01/README.md)保留，不能在原件被删后只剩本表。

| 阶段 | 原始POST序号 | 实际全局dispatch.seq | 原生根 | 工具许可/Enter |
| --- | --- | ---: | ---: | ---: |
| C-I1 | ideation0001～0002 | 2 | 1 | 1 |
| C-E1 | executor0001 | 3 | 1 | 0 |
| C-I2 | ideation0003～0004 | 4 | 1 | 1 |
| C-I3 | ideation0005～0006 | 5 | 1 | 1 |
| C-I4 | ideation0007 | 6 | 1 | 0 |
| 合计 | ideation7/executor1 | 序号1是target初始登记，不计角色根 | 4/1 | 3 |

8个请求均逐文件计数、200/complete，request_bytes/response_bytes/wire_bytes_confirmed与原字节相同，SSE从message_start到message_stop完整。当前请求正文按实际SQL登记seq/source补协议包头后精确对应，未容忍拼接/裁剪；实际seq是事实读取，不是驱动写死编号。

hook独立重数：ideation UPS4/Stop4/PermissionRequest3，executor UPS1/Stop1；13组都有finished且exit0。Bash实际input只含command，3个tool_use各有同ID tool_result，其形状是queued=true/delivered=false/request_id；真实Stop后才有同原request的relay结果。I1的stop发送方实际为ideation，argv伪造--from executor没有覆盖身份。

三条permission_control_written对应3条terminal_input_write_intent、3条written和3条action/CR，未新增turn_submit_intent。命令、dispatch、permission_event和签字绑定相同，早晚stop命令恰为同目标thread与同原stop-id，没有额外argv。各根实际turn_submitted与UPS/Stop均一一对应；历史请求里的旧tool_result不是新执行。

## 时间与业务事实

- 原stop **a649f79c-f2a1-4cd1-bcd3-f623abe6f16c**，原queued request **8961bfe0-821e-45c6-af9d-ea173dafd9cd**，created_at **2026-10-17T04:03:56.934Z**。开始时点来自真实stop条目，没有重置为模型输入、上线或观察时间。Stop/relay生成条目，executor提交后delivered；原sender/refs与本场attempt/thread相符。
- C-I2真实relay_rejected事件seq236，UTC **04:04:01.589Z**，距原stop **4655ms**，结果stop_too_early。C-I2 collect的约5344ms是稍后读回时点，不是门禁拒绝发生时点。其target_bytes_hex为空、no_ack=true；原件在 `phases/C-I2/collect-01/settlement.json`。
- C-I3按键前保存的wall_age **121527.934ms**、OS CLOCK_MONOTONIC elapsed **121185.517ms**；两钟与原origin算术相符、差值未超过原1000ms阈值。原件 `phases/C-I3/execute-02/result.json` 的enter_at。
- 实际门禁emergency_interrupt_requested事件seq31，UTC **04:05:58.927Z**，由原created_at独立计算 **121993ms**，严格>120000且<150000。details明确actor=ideation、同原stop-id/目标thread；pane_interrupt_written seq392、原target leader40105。原relay结果ok=true/interruptRequested=true，只有一次实际中断。
- 协调器最终观察wall_age **123102.578ms**、elapsed **122760.159ms**，这是完成读回时点，不能冒称按键时点。C-I4/C-E1 collect均PASS。原 [clock](09c-c3-b1-ideation-p1-01/phases/C-I1/execute-02/clock-origin.json)保留初始wall/OS mono、observer_pid与stop/request，不重建起点。
- 目标baseline0字节，原received.bin当前恰1字节 **1b**；无其他字节，无对应原stop的ack。只读tasks/attempt快照仍是原attempt/session/fence/thread/workspace、claimed/reclaimed=false、无candidate/integration；业务事件未stop/exit目标。当前OS存活仍须回收dry-run验证，worker不冒称本次ps实测；原各阶段driver保存了其目标存活检查。

## 完整许可屏与授权证据

| 阶段 | 原dispatch屏/直接total | permission_event seq | 独立完整另读 | 签字件 |
| --- | ---: | ---: | --- | --- |
| C-I1 | 15945 | 110 | P1/4794c01e-ideation-C-I1-permission-screen-02/screen.bin | phases/C-I1/permission-approval-01.json |
| C-I2 | 33352 | 183 | P1/4794c01e-ideation-C-I2-permission-screen-01/screen.bin | phases/C-I2/permission-signed.json |
| C-I3 | 47553 | 258 | P1/4794c01e-ideation-C-I3-permission-screen-01/screen.bin | phases/C-I3/execute-02-review/approved.json |

P1均为09c-c3-b1-ideation-p1-01。三份原屏与另读逐字节一致，offset0→next=total，页总长一致，签字的screen_file与原屏相同；C-I1的Enter结果、C-I2的permission-check结果、C-I3的最后control/current-screen及capture均有直接total。C-I2按键前再次完整比较由冻结协调器代码和实际check/Enter收据支持，未另存那次比较的第三份raw，不把它写成另有原文件。C-I3最后实际raw也与原屏逐字节一致。原件索引、3条action/命令/许可来源都在live-06 JSON。

## 证据边界、失败记录与后续

本次核对器最初把SQL裸正文当完整提交，live-01因此拒绝；登记表原本保存裸正文，真实包头按source/全局seq补上。live-03误读C-I2的Enter.json期待capture字段，被KeyError拒绝；实际capture在permission-check-01。两份失败原样保留，是worker核对器问题，不是场景失败，不覆盖为PASS。live-02为初步计数核对，live-04补许可来源，最终以live-06为准。

8个已知坏证据反例（额外POST、额外Esc、伪造ack、过早中断、截断屏、时钟跳变、HTTP409、撤销持续停止要求）由[同一核对函数](09c-c3-final-check-01/counterexamples-03/result.json)拒绝；这些是明确的运输层变异，不冒充reviewer必须完成的产品变异。归档命名空间仅做了合成内存tar测试；真实C3 tar重数/凭据扫描/签字/finish尚未运行。

第1场仍INCOMPLETE：按键后字段错误、首份结果被重复执行的错误处理覆盖，现有事实是日志/HTTP/hooks/事件的间接还原，原场13/11 POST超预算；清理PASS不能补回丢失结果。第2场仍INCOMPLETE：C-I1成功后C-I2签名前拓扑拒绝、零C-I2键；原场3/11 POST。故障时额外PID没有捕获，后续真实探针证实合法caffeinate模式，不补称已找回故障瞬间PID。第1/2场各自原件与回收结果不改；第3场PASS只支持本场。

最新live-06还直接读取已复制的原protocol-plan/continued-stop-demand/clock原件，核对实际root/source/claim、同原stop且still_required=true，以及原clock与主控保存副本逐字节相同；未从driver PASS生成这些原件。它们将连同来源清单进入外置tar。
