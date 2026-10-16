# A-15 E1 许可与剩余阶段待批材料

材料静态准备，全部后续动作尚未运行。主控 #329 的 executor readiness、I2 arm/collect、E1 dispatch 与投递读回，已先提交为 `1010601fed408181074779263a15f495ddba924c`，九项尾注齐。真实读回为 turn_submitted seq 176 → feedback seq 187，delivered，原 request/entry 关联，I2 注册/提交/反馈各一次；已观察实际 POST 为 ideation 3、executor 1。主控报告误重跑读回被 output_exists; no action 拒绝，无新增动作；没有虚构该拒绝的独立运行产物。

## 当前 E1 许可

E1 已在 executor 的 `phases/E1/dispatch-01` 返回 READY_FOR_PERMISSION。它来自原 inbox stop：dispatch `b91b5f60-62e9-4983-b48e-f73630f1f854`、实际全局 seq=3、entry `c3ab1493-5c73-4af5-947f-a0f16f19d6c7`。不得重跑 INITIAL-RELEASE 或再次派发。

本轮只调用已有 prepare 的文件生成步骤，写好 `phases/E1/permission-approval-01.json`，approved_by/approval_ref 为空。它引用真实 permission_wait seq 195、实际 Bash command、原 permission-screen.bin 和本次 executor launch/session。该命令故意指向 protocol 的错误 thread，预期真实门禁回 worker_target_required；是假服务下发批准工具，由角色 CLI 执行，不由 operator 代写业务动作。

主控后续分别执行：

1. E1 目录的 `PERMISSION-SCREEN-COMMANDS.txt` 初读命令，再逐字节 cmp 本次 fresh screen.bin 与 dispatch-01 的 permission-screen.bin；检查完整 Bash 命令、原 stop id、光标 ❯ 1. Yes。该文件列出初读/备用 -02 两组，不能整份批量执行。若内容不符，只用 -02 只读重看；cmp 不相同或仍不符就停，不改原结果或拼接批准。
2. 签已经生成的 permission-approval-01.json。E1 的 PERMISSION-APPROVAL-COMMAND 仅记录生成方法，本轮已经生成，不重复执行。
3. 执行 `PERMISSION-ENTER-COMMAND.txt`：沿用真实 Electron 窗口，一次 awaited Enter；不得选择持续允许或 auto。该脚本核对实际当前屏幕、active dispatch、permission event、完整 Bash command，再送一个控制动作；Enter 不新增业务根。输出为本阶段新 execute-02，内部已有真实工具/Stop/relay oracle。
4. execute-02 PASS 后、进入 E2 前，执行 E1 的 `READBACK-COMMAND.txt`，只 collect 到新 readback-03；不再 Enter、arm 或 release。

## 逐阶段执行规则

剩余顺序为 **E1 → E2 → E3 → E4 → I3 → I4 → E5 → E6**。I1、I2 已完成。各阶段命令与批准均在相应角色 P1 的 `phases/<stage>/`；`stages.json` 给出绝对目录索引。E2–E6、I3–I4 的 phase approval 签字字段均空，不批量批准或执行。

有工具的后续阶段 E2/E3/E4/I3/E5，每阶段依次执行：

1. 主控核对来源和本阶段批准，签 `approval.json`，只运行本阶段 `START-COMMAND.txt`，预期 READY_FOR_PERMISSION。虽然参数名是 protocol-phase dispatch，既有驱动只有 I1 分支调用 pane_dispatch；这些自动阶段只登记本阶段应答批准，并观察真实 gate feedback/inbox wake，不派发替代输入。
2. 用本阶段 PERMISSION-SCREEN-COMMANDS 的一组读屏/cmp。父目录、实际 B1 manifest 和 launch label 已填写；-02 只是备用只读，不发键。保存的 permission-screen 不匹配当前屏幕时停止，不绕过校验。
3. 用 `PERMISSION-APPROVAL-COMMAND.txt` 从本阶段真实 dispatch-01/result.json、permission_event 和原屏生成空签字 permission；未来 dispatch/tool/request ID 尚未产生，不能预填。主控逐项核对后签字。
4. 仅执行本阶段 `PERMISSION-ENTER-COMMAND.txt`，一次 Enter；PASS 后执行本阶段 `READBACK-COMMAND.txt`，新 readback-03 只读核对。完成后才进入下一阶段。

无工具阶段 I4/E6：签本阶段 phase approval，执行 START-COMMAND，预期 PASS（单条中性确认及实际 Stop/idle）；再运行 READBACK-COMMAND。没有 permission 草稿或 Enter 命令，不因没有许可屏而补发 Enter。

每阶段 START/Enter/collect 的 output 目录都独立、不覆盖。Electron slot 沿用已验证规则，含 stage、output label、实际角色 launch；本轮只核对计划路径，没有 build、启动窗口或角色。权限 Enter 都记 control action，不记 message，不新增 turn_submit_intent。

## 来源、读回与预算

| 阶段 | 自动来源 | 本阶段预期 POST | 许可次数 | 真实读回要求 |
| --- | --- | ---: | ---: | --- |
| I1（已完成） | 批准的模拟用户停止请求 | 2 | 1 | 原 stop、pending、零反馈、目标零增量 |
| I2（已完成） | 原 I1 send 的 delivered 反馈 | 1 | 0 | 原 request/entry、真实投递后恰一次 |
| E1（等待许可） | 原 stop 的 inbox wake | 2 | 1 | worker_target_required，目标无 Esc |
| E2 | E1 的真实拒绝反馈 | 2 | 1 | executor 请求中断原受管 target，实际仅一个 Esc，actor/thread 匹配 |
| E3 | E2 的真实执行反馈 | 2 | 1 | 一个实际 executor ack，reply_to 原 stop，ideation wake 一次 |
| E4 | E3 的真实 ack 执行反馈 | 2 | 1 | 同一个 ack 条目，幂等，无第二次 ack/wake/Esc |
| I3 | E3 实际 ack 的 inbox wake | 2 | 1 | recipient_required，不生成新 ack |
| I4 | I3 的真实越权拒绝反馈 | 1 | 0 | 只确认，实际 Stop/idle，目标仍恰一个 Esc |
| E5 | E4 的真实重复 ack 反馈 | 2 | 1 | stop_already_acknowledged，无额外 Esc |
| E6 | E5 的真实拒绝反馈 | 1 | 0 | 只确认，实际 Stop/idle，目标仍恰一个 Esc |

全场 ideation **4 roots / 6 POST**（I1 2 + I2 1 + I3 2 + I4 1），executor **6 roots / 11 POST**（E1–E5 各 2、E6 1），合计 10 roots / 17 POST、7 次工具许可、供应商模型 0。E1 已有首条 POST；本次许可只补同一根的 tool_result POST，不再消耗一根。当前已实测 4 POST，剩余预算为 13 POST。

READBACK-COMMAND 始终复用现有真实 phase collect oracle：根据真实 API exchange、UPS/Stop、relay request/result、收件箱条目与 target received.bin 判定。工具回执先结算 queued request_id，再由真实 Stop 执行请求；不把排队回执伪装成业务结果。每份 readback 的 dispatch_id/dispatch_seq 来自实际登记；有工具阶段须与本阶段 dispatch-01 的实际 bound dispatch 相同，禁止把阶段号映射成固定全局序号。现有 API 已把实际全局登记正文与原生请求逐字核对，不容忍拼接或重新包装。

E3 的 Stop 会同时产生 executor E4 反馈和 ideation I3 wake；两角色的实际 POST/seq 可以交错，不能预设全局编号或以角色局部计数替代。执行主控须及时签下一阶段并运行对应 START，同一个待批准 POST 最多等待 180 秒。收到 SSE 前已经发出的 POST 也算预算；它属于其真实阶段，不能漏算或重发来“续等”。任何 409、超时、超预算、身份/正文/命令不符、意外许可或目标字节不符，整场 INCOMPLETE 停止，不重试、不自动跳阶段。

这些材料的语法/路径与未签字段检查不等于真实运行。E1 许可及全部后续阶段本轮均未执行，API、daemon、角色与目标现场保持原状。
