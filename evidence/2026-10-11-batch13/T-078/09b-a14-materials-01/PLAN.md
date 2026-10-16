# A-14 待审材料

状态：静态准备；launch NO_GO。此目录不是运行现场；`09b-executable-materials-14` 由提交脚本在冻结源码后经统一 prepare 生成，Stage A/B1 的真实 binding 尚不存在。本轮不启动 daemon、API、CLI 或 target，不发键，不发送业务动作。

主控 #303 接受的产品独立审查只覆盖 `7039840565754f7999b27061191b6506e61ef9d2`（冻结 `4b48664fd689aab8d52a8721098939067928847e`），不替本次驱动和新夹具变化背书。原 pending 链与真实 worker 回归的结果见 `independent-review-pending-01.md`。本包完整双角色运行尚 INCOMPLETE。

用户 answer `20261016T012505Z-ideation-answer-001` 要求目标无会话时追加留存、pending 可见、不给发送方回灌反馈，同时 protocol/预算不变。pending 零反馈、实际 delivered 后才登记原有 I2，是主控 #299 对这些约束的解释；独立审查认为一致，但这不是用户另外逐字批准的时点。条目的 created_at 不重置。

**Tracer bullet**：I1 经批准的模拟用户窗口请求进入正常门禁 `pane_dispatch`/`pane_release` 路径；Claude 原生 Bash 生成请求文件，真实 Stop 触发 relay，门禁追加 stop/pending；executor 首启只排队，初始 release 后 turn_submitted 使投递 delivered，再由产品生成原 request/entry 的唯一 I2，随后实际 ack。**Deep modules**：收件箱和派发事实仍由门禁/daemon/relay 持有；夹具只读真实持久记录来决定 API 应答。**Ubiquitous language**：queued 是工具请求回执，pending/queued/delivered 是投递状态；不能把 queued 的 tool_result 说成已经送达。

执行顺序与批准：

1. 审阅并提交本包；提交脚本统一 prepare materials-14、写实际 source_revision，Stage A 批准签字仍空。主控签字后只运行 STAGE-A-COMMAND.txt，停在 READY_FOR_APPROVAL。
2. 用 ROLE-MATERIAL-COMMANDS.txt 第一条生成 ideation P1。逐项核对生成的 B1 批准、签字，先 B1-COMMANDS 的 dry-run，再单独 real。用 BIND-LAUNCH 绑定实际成功结果；如 label 改为 -02，先改该命令的真实 result 路径再运行，不猜 manifest、不复制旧 manifest。
3. 按 ONBOARD-COMMANDS 每次一屏一个键。B1 的冻结 screen plan 保持 security-notice + 原文；P1 实际键用途为 onboarding-notice。每次读屏不符就换全新 -02 标签重读，不发键；批准和 --screen-file 同时引用实际采用的屏幕。主题 ArrowUp→Auto、ArrowDown→Dark、Enter；Security notes 去控制/空白后逐字核对；trust ArrowDown 到 Yes 后 Enter，禁 Digit1/default Enter。s13 空提示符/manual 且 0 Messages 后，主控另把 readiness-template 填成 readiness.json（confirmed_by=executor/readiness=confirmed/basis 非空）。
4. 签 I1 phase approval；完整输入见 i1-prompt.txt，自动化身份为 test-simulated-user，绝不冒称用户亲手。I1 三步 COMMANDS：dispatch 到权限屏即停；文件生成器按实际 dispatch/permission_event/screen 生成空签字模板；主控只读核对完整 Bash command 和 ❯ 1. Yes 后签字，再运行第三步唯一 Electron Enter。工具返回排队 request_id，API 第二条 Messages 只中性确认；真实 Stop 后 oracle 要求同 request 的 pending stop、零反馈、target 零新增字节。输出 READY_FOR_EXECUTOR 才能继续。
5. 用实际 I1 读回生成 executor P1，完成独立 B1/onboarding/0 Messages/readiness。executor unknown 阶段业务字节必须为零。先单独签并 arm ideation 的 I2（不发送输入），再签 E1，E1 release 只放行已排队的真实 stop inbox wake；不新派发。I2 实际完成后 collect 只读，要求原 request/entry、delivered 与目标 turn_submitted。E1 停在原生许可屏，三步同 I1。
6. 按 BUDGET 阶段单独批准；E2–E6/I3–I4 输入全部来自产品生成的 gate feedback/inbox wake。夹具不调用 operator send/stop/ack，不给业务表插入伪造 attempt/request/entry，不重新派发或自动重试。

本轮新增阶段夹具：显式 phase_plan 模式从真实 dispatch_queued/turn_submitted、relay 与 inbox 记录绑定正文/全局 seq/原 request/entry；tool_use 的 argv 来自冻结 protocol，实际 ID 替换后安全拼为 Bash input.command。每阶段收到的同一 HTTP 调用在对应空签字批准尚未补齐时最多等待 180 秒；这段等待是夹具响应门，不是 product 新业务入口，也不产生额外请求。超时返回拒绝并整场停止，不能自动重试。自动 feedback 在主控尚未审批下一阶段时可能已发起 HTTP，主控须在期限内决定签字；如需更久应在启动前另裁定，不在现场延时或重放。每个阶段最多一个根、1 或 2 次 Messages，API 按实际 POST 计数，历史 message 数不等于请求次数。

文件生成采用角色本地 input/scenario/nonce，避免第二角色覆盖第一角色的批准输入；正常单角色 slice1 仍走原 root 布局。A14 的 --reuse-stage-a 屏幕/键调用也明确传该参数。所有运行输出先建父目录，新目录拒绝覆盖；实际 manifest 由成功 B1 结果绑定；唯一构建 slot 含 A14/stage/新 output label/launch。

停止条件：任意 409、意外工具/许可屏、实际命令或窗口身份不符、Messages 超预算、旧输出/slot 存在、未知 Stop/无回执、目标字节超出零或唯一 Esc、pending 冒充 delivered、无反馈要求不符，均 INCOMPLETE 并保留现场；不得按第二次 Enter、重送或换端口替换进程。本包未证明完整 HTTP/Electron/双 Claude 执行，需主控先审驱动变更再批准启动。

清理待实际 PID/lstart/readiness/manifest 生成 owner-bound 脚本；正常 daemon_stop→panes.shutdown 关闭角色及 target、两个 API 各一次 SIGTERM、退出核对、外置归档逐成员读回后才删 root。slot 只列清单，删除另批；不把 A13 已清理的 PID 复用给 A14。
