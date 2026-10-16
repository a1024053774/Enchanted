# T-078 startup/pending 差异：独立审查请求

状态：**INCOMPLETE，待全新只读 reviewer**。不复用 `703984056` 的 pending 审查 PASS。本轮未开子 agent。

基线：`d1ca480223dd874721af71c36488af0ed8b96f37`。候选：本次 `fix(T-078): allow approved startup keys with queued inbox` 冻结提交；执行主控以实际提交号绑定。产品差异应仅为 panes.ts/assertStartup 删除 queue 为空的前提，README 补一句行为说明。不得把 A-14 过程证据、诊断提案的 NO_GO 或离线 spy 解释为真实新实例成功。

要求来自主控 #308 及 #298/#299 已审计划：unknown 首启可登记 pending inbox 队列，仍允许经批准的一屏一键，不得 drain；初始 release 后才写出/确认 delivered/原 I2，其余 assertStartup、身份、快照、信任与键次序约束不变。

请独立核对：

1. 原 A-14 executor 状态/拒绝原件，领域旧实现 red-01 的具体失败；一行修复没有改变其他条件和三次检查位置。
2. green-02 的六键中只有控制字节，没有业务 paste/turn_submit，队列未动；初始 release 才唯一写出。负例是否真的经过对应约束，而不是仍被旧 queue 前置否决遮挡。
3. run-startup-pending-entry.py 的已知坏副本红态必须在真实 pane_screen_key CLI 返回 screen_requires_startup；绿态必须经过真实 daemon/Stop/relay/上线排队/六键/release/delivered/原 request 的唯一 I2/ack。主控可先运行 `STARTUP-PENDING-ENTRY-COMMAND.txt`；当前交付时真实入口阶段尚未运行，缺证时结论只能 INCOMPLETE。
4. 当前 A-14 的 daemon 和 P1 source snapshot 都不能加载该修复；没有改旧签字包/转交能力/热补丁或后台 drain 来绕过。`09b-a14-s1-retry-NO-GO.json` 不得执行。
5. 整票与真实 Claude 新实例尚 INCOMPLETE；不宣布 09B 完成或批准 launch。
