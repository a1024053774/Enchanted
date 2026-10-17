# 两场回收脚本契约：归档在前，停机后不读SQLite

**这是待实现/绑定的脚本施工单，不是可执行cleanup，也不是PASS收据。** 用户要求的顺序作为脚本不可跳过的状态机：`BOUND → DRY_RUN → CAPTURED_BEFORE_STOP → ARCHIVED_BYTES_VERIFIED → INDEPENDENT_READBACK → STOPPED → POST_STOP_FILES_VERIFIED → ROOT_REMOVED`。任何阶段异常保留原收据并BLOCKED，不走到删除；实际实现及入口证明要在合并T090后、源码冻结前完成。旧A15脚本只存projection，不能换个root/PID就当新脚本。

## 输入与输出

每场一个新的owner文件，来自真实Stage A readiness及两份实际B1成功manifest/运行identity。必须绑定scene、实际source包/版本、root/state/project/task/spec_rev、真实target attempt/session/fence/thread/workspace/launch/native session、daemon与两个API的PID/lstart/完整argv、两角色shell/CLI、原API ready、原角色launch/session/preset，以及外置新归档目录。字段缺失/空/旧实例一律拒绝，不能填null伪造target身份。

清理批准由执行主控在看过这份owner和实际归档后另签，引用本场root/身份/归档；草稿不是批准。CLI只通过本场operator凭据调用唯一门禁，凭据不归档；不把operator当业务send/stop/ack角色。实际脚本要提供 `--dry-run`，只读身份/路径/所有权核对并列动作，不捕获新包、不停服务、不发信号、不删除。输出目录必须新建，已有拒绝；每一步实际状态/时间、各成员字节结果、信号与退出结果均追加保存。

## 正式脚本的强制顺序

1. **全部身份先核对。** C locale的`ps -ww -o pid=,lstart=,command=`双读，比原ready/argv/root/lstart，核对daemon父子、两个角色前台leader/session、目标工作区。只认实际记录的本场进程集合，意外子进程/变化/旧PID则拒绝；不再用comm当完整argv，也不把已退出误报成另一个活进程身份。缺失进程如与正常待回收状态不符则交主控处理，不猜测接管。
2. **停机前采集完整原件。** 场景阶段驱动停止接收新业务动作，正常场确认两角色idle、队列/未完成HTTP/工具为零；失败场明确记录仍未完成，不能伪装正常。用已绑定捕获器全量枚举POST/hook及实际文件，导出所需事件/库行的一致只读快照，关闭数据库连接，保存目标和身份字节。只读导出发生在daemon仍活着时；不在停机后尝试补库或依赖WAL。
3. **脱敏、归档、逐字节读回。** 仅把经结构规则核对的逐记录副本写入本场受保护暂存区，绝不把root/用户HOME/SQLite整体传给tar helper。实际source文件列表、每条POST/hook目录和捕获时点清单必须齐；对暂存区普通文件逐字比较tar读回，目录/链接核对类型与目标，缺成员/新成员/路径穿越/未知类型/外置I/O失败均停止。全部成功后才生成每个逻辑文件的`*.archive.json`和总manifest，不能先写PASS再实际验证。
4. **独立读回作为删除前置。** 执行主控/fresh reviewer从外置包直接重数和关联，不执行collector的summary来当oracle。A16重数17 Messages/10根/七许可、原I2和单Esc/ack；C重数8 Messages/5根/三许可、实际时钟/无ack/ideation单Esc。多余或未完成记录仍保留并明确标INCOMPLETE；若决定回收一个失败现场，要另在批准中明确已完整保留失败原件，不要求它业务PASS。独立方认为原件不足则root保留，不用清理通过抵消验收不足。
5. **停止前最后确认。** 用全量清单/实际文件逐字义与副本重比，确定采集后无新的POST/hook或原件变化、身份未变。这里比较真实文件内容/变更映射，不能只比两个汇总计数；敏感原值不写输出。若场景仍在写、窗口命令未确认、hold连接未结束，不能假定quiescent；保存现场交主控，不先删root。
6. **认证正常停止。** 只调用原入口 `node <本次源码>/workbench/src/gates/cli.ts --state <owner.state> daemon_stop`（本场operator凭据），由panes.shutdown正常关闭两Claude/target；确认daemon/角色/target七个实际PID退出，socket/PID文件消失。**不直接给Claude或target发信号、不reclaim/归档业务target作为停止动作。** 再对两只原fake API各紧邻双读身份，各一次SIGTERM并确认退出；不是A05的同线程shutdown死锁旧实现。任一超时就BLOCKED，不自动SIGKILL、不重发信号、不重复daemon_stop。
7. **停机后仅文件复核。** 确认九PID全退，只重读已存tar/manifest/逐文件字节及原POST/hook的文件目录，不导入或打开SQLite/WAL/SHM、不调用需要数据库的collect。`daemon_stop`本身的新状态库字节不在要重读的原件集合。若关停期间出现新的hook/POST/finished或原件变化，**不能悄悄漏掉**：阻止root删除、保存差异清单，后续只按额外批准做文件尾部的脱敏归档/读回，不能停机后开库补证。
8. **只删固定本场root。** 实际归档与先前已保存副本逐字相同、独立读回已留、所有新增尾部记录已解决，才核对root realpath无符号链接并删除。记录archive_bytes、成员清单、signals_sent、root_removed等真实值。原始本场秘密随root按批准回收，但用户HOME/认证/会话历史、他人进程/目录和全部build slot均不删除。slot另列主控决定。

上面第3～5步均在停止之前，不能为了释放磁盘先停机再发现库不可读；第7步的**文件尾部差异检查**也不能反过来读库。归档先成功不代表关停后的新记录已被覆盖，必须防止再次发生F1。

## 代码复用与必须重做的部分

可复用旧A15身份双读、父子/前台核对和正常daemon_stop路径；可复用已证明的tar逐成员字节/类型比较，输入必须是新的脱敏暂存树。**替换**summary-only redactor、归档验收和root删除前置，原件sidecar与C时间/许可信息必须入清单；不添加遇到原件缺失就退回旧projection的兼容分支。新脚本名/实际argv只在实现、排练、合并后绑定时给出；本轮不提供无功能return READY脚本冒充可用回收。

冻结前的证明包括：身份/PID复用/错root、第一只API与第二只identity不能串用、归档成员内容变/漏/未知类型、断开外置盘、capture后增加一条POST/hook、finished在停机时才出现、停机后数据库不可用、已发SIGTERM回执重放、root符号链接。坏实现若删了原件完整性/字节比较/关停尾部检查或停机后仍collect，必须在新断言处失败。当前这些新检查未运行，不宣称脚本安全性已独立通过。
