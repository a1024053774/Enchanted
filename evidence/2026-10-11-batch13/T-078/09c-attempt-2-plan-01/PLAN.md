# 09C 第 2 场最小重做计划（不冻结、不启动）

状态：**INCOMPLETE／NO_GO**。当前只有未绑定的 Stage A 草稿与未来命令；source_revision=null、回归收据为空、批准为空，不能签或运行。没有新 root/daemon/API/角色/target。第 1 场不再续行，必须先归档和正常回收。

## 修复与排练先于重建

1. 按 [第 1 场诊断](../09c-attempt-1-diagnosis-01/DIAGNOSIS.md) 修测试 harness，产品源码不需要改：删除 start 的重复 release；统一真实 request/key/result 关联（包括 NativePermission 与 observe）；修全部反馈 envelope 层次；确保重复输出拒绝时不覆盖旧结果。旧失败原件不改。
2. 用本场原始工具 schema、queued tool_result、relay 行和真实反馈 envelope，证明修复前在对应真实读取/结算入口红、修复后绿。至少覆盖 C-I1→实际 delivered→C-I2 工具根→真实提前拒绝→C-I3 模板与原 send 关联→实际晚停成功反馈 C-I4。wrong request/key/prompt/stop、错误 envelope、重复输出、截断/变化原屏都必须拒绝；重复输出前后原 result 字节相同，零 build/Electron/键。
3. 一次性 scratch 的真实 daemon/relay/inbox/Stop/HTTP 排练必须调用实际 initialize/start/许可结算入口，而不是只走 phase core 或模拟 relay 成功；覆盖 owner/target/prompt 的原始绑定。系统真实时钟 >120 秒、全场 <150 秒、未 ack/只一个 Esc、无回收目标、完整 reader 与单 Enter 的已有边界保持。测试工具许可通路用明确标识的确定性窗口替身，不冒充真实 Claude/Electron；如需要补真 Electron 控制边界排练，另交主控批准，仍模型0、不启动角色 CLI。
4. 修复后的 C driver/permission 是冻结闭包成员。旧四份回归收据的 source guard 会拒绝这些源码变化，**不能自动沿用或改检查绕过**；按现有契约取得合格的新收据/绑定，或先交主控审定工具修订的重新验证范围。所有真实入口排练输出与修复独立审查冻结提交后，再生成新包。

主控后来补入的第1场计时脚本必须作为历史原件保留，不能直接复用：`stop_entry` 改读 C结算的真实 `stop` 字段；每步成功状态白名单必须精确，禁止宽泛 `[A-Z_]+` 接受 INCOMPLETE。更关键的是 **C-I2 的按键前早停门**：当前 B许可入口没有按键前的 stop 年龄检查，不能把 C结算事后 `<120秒` 断言当作安全门。需在实际按键入口核对原 stop/clock、无ack、真实年龄并设保守提前截止、预留命令/Stop/relay时间；不够则零键中止，迟到不得执行与 C-I3 同形的 stop 命令。用已迟到、时钟变化及慢结算等反例证明不会因 harness 延迟在 C-I2 误触晚停；具体提前余量和排练实测交主控审定，不放宽协议边界。

## 第 2 场命名与运行顺序

[FUTURE-COMMANDS](FUTURE-COMMANDS.txt) 给出路径完整的计划命令：新标准包 `09c-executable-materials-03`，Stage A 输出 `09c-stage-a-02`；新实例 c2，两角色 P1 为 `09c-c2-b1-ideation-p1-01` / `09c-c2-b1-executor-p1-01`。不能复用第 1 场 root、PID/lstart、launch/session、request/stop/permission ID、原屏、签字或构建 slot。所有实际 ID 仍取新 Stage A/B1/登记/Stop 收据；未发生的字段不伪造。

标准 prepare 在修复提交上冻结源码并记录静态 root；再从其实际 revision 重新生成 Stage A 批准与回归绑定，主控另签后运行。两个角色按 ideation B1/逐屏/readiness→executor B1/逐屏/readiness 串行完成；每屏只一键，完整 reader，初读不符换 -02 重读不发键，s7 key 的 purpose 为 onboarding-notice，B1 screen_plan 保留 security-notice 与原提示文字。

计时前完成两角色零 POST/readiness、九进程 owner、唯一 C-I3 build、五份 phase 预批准/arm，以及一次 initialize。随后 C-I1 只 dispatch，已放行 idle 窗格自然送达，不再 release。C-I1 真实 send/Stop/relay 后以原 stop.created_at 开始时间；C-E1 单 POST 保持无 ack；C-I2 在 <120 秒真实提前拒绝；C-I3 提前取完整原屏/模板，由主控核对签字后，真实 wall >120000ms 且 monotonic ≥120100ms 才条件式单 Enter，最迟130000ms开始，全场150000ms内完成实际只中断、C-I4确认与 C-E1收尾。任何不符、错误、未知写入、额外POST就停，不重试或重置时间。

| 角色/阶段 | roots | 实际 POST | 工具许可 |
| --- | ---: | ---: | ---: |
| ideation C-I1 | 1 | 2 | 1 |
| ideation C-I2 | 1 | 2 | 1 |
| ideation C-I3 | 1 | 2 | 1 |
| ideation C-I4 | 1 | 1 | 0 |
| executor C-E1 | 1 | 1 | 0 |
| 合计 | 5 | 8 | 3 |

预算仍 ideation4根/7POST、executor1根/1POST，供应商模型0；两个真实 Claude 会话和一个确定性 target receiver，不额外开 Codex/agent。归档继续逐 POST/hook 原件、停机前一致行导出、逐成员字节读回、独立 tar 重数、签字后正常回收；停机后不读 SQLite。当前仅计划，不把已有纯逻辑绿态或本次诊断计为第 2 场通过。
