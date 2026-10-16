# T090合并后的实现/排练/冻结清单

本轮只准备计划，下面均**未实施/未运行**。不能因为已有A16/C阶段JSON就将launch标READY，也不能只把旧prepare输出改个label绕过缺失功能。

| 项目 | 可复用事实 | 必须完成的新增部分与可证伪检查 |
|---|---|---|
| B完整协议 | A15真实Bash command/queued→Stop、10根阶段、pending/六次startup/I2时点已局部验证 | 沿同一API/registry/driver，不改09B protocol；实际枚举所有POST/hook而非从summary拼原件；启动前一次实现全部阶段/捕获，禁启动后热换API |
| 原件捕获/导出 | fake API已有逐请求/响应文件，hookTrace有stdin/started/finished，reader严格分页已证明；F6标准包已补八个Python本地依赖 | 原始序号在验证前记录、全部成功/失败/未完成条目保留、结构脱敏、完整源目录/服务序号枚举、每条archive sidecar、停机前事件行导出；缺一POST/metadata、重复hook、额外409必须被新原件oracle检出 |
| 归档/回收 | 身份双读/归属、正常daemon_stop/panes.shutdown、API一次SIGTERM、成员字节验证可复用 | 按CLEANUP契约替换旧summary-only出口；禁止停机后SQLite；关停新增raw/finished被检出并阻止删除。直接从外置包独立重数，不只让两个同源summary相等 |
| 09C协议/driver | 两真实Claude角色、相同门禁/inbox/Stop/window输入通路 | 专用阶段图与预算I4/7、E1/1；原executor单POST保持/正常结束；C-I2真实提前拒绝，C-I3早备原生权限屏、真实时钟等待与严格条件单Enter、C-I4真实成功反馈。不能用旧09B I2确认代替工具根，不造业务结果 |
| C条件单Enter | 已有一次awaited Electron CR/action与完整原屏比较可复用 | schema实值/签字/原屏/实际PermissionRequest/stop/target/native/窗口/时钟/无ack全部检查，一次消费intent；错字段/原屏变化/截断/提前/超时/重复/回执丢失的真实入口负例，证明零额外写入 |
| 原生场景前排练 | A14曾真实HTTP/daemon/relay、确定性替身排练；它没覆盖原生onboarding时序而曾漏问题 | 新排练保留真实宿主/relay/HTTP/窗口路径；回放脱敏的真实CLI请求schema、实际执行仅本scratch的Bash和真实UPS/Stop；覆盖B的pending→上线首启六键/刷新→delivered/I2、C的PermissionRequest等待/条件Enter及保持超时；不得把spy未走到的边界写PASS |
| 源码冻结 | 标准prepare具备逐文件Git字节核对和完整产品TS树，reader基础闭包已修 | 新helper/C模块/归档器与对应本地imports一并入包；旧/新包原件保留。完整F4及受影响T082边界绿后冻结实际HEAD，生成两场新的Stage A/B1/阶段/许可/归档/cleanup实值材料，实际commands只在此时给出 |
| 独立审查 | 终审01已指出F1～F7和原件/历史total边界 | 新候选fresh reviewer用隔离临时worktree做2～5个错误实现检查（主控#335裁定）；只读原始逐记录外置包，scope按ready_rev2排除T091/T092、保留IME INCOMPLETE。旧review PASS不背书新捕获/C driver |

真实时钟路径与权限屏能否稳定等待必须从新场景观察，不能由合成返回值断言。若C等待中原屏增长/目标变化、原件脱敏后不足以独立核对、完整闭包或分阶段权限仍有缺口，停在对应阶段INCOMPLETE，不增加预算、不重新命名重复同一动作。所有本轮模板签字仍空，任何后续缺失runtime字段都不能默认为旧A15/A16值。

本目录的authority副本保持main原文，其原链接按main票目录解释；不改原字句来适配本地路径。没有sources.tar.gz、静态root、源码revision绑定或实际批准回执。待T090合并后按主控阶段安排实现/排练/冻结；已授09B/09C代签范围不重问，每次实际launch仍核对具体批准件，worker不从本施工清单自行开始现场。
