# T-066：PAUSED（主控挂起，等方向结论）

状态为 BLOCKED，不作为 PASS 或 fork 交付。依据 ⟦主控 #28⟧，决定 01 的上游接入批准已挂起；已立即停止本次隔离服务端和 UI 探针，不再修改 fork，不启动审查。ticket 保持 open，Acceptance 未勾选，待主控后续决定与关闭。

## 暂停现场与 stash

- fork 基线：`49cae984f22924de006e0f8358cb447eb881aaf6`，a2a 分支。
- 暂停前已经提交的候选：`ddb765956cae4a4d0b87b875970601068567ed93`。该提交发生在 #28 之前；保留原位，没有丢弃、改写历史或继续提交。
- stash 名：**无，未创建**。按指定消息 `T-066 WIP paused 2026-10-10` 对本票 11 个路径执行 `git stash push -u`，排除他人的 `.grok/`；结果为 `No local changes to save`。当时只有 `.grok/` 未跟踪，本票代码已提交，stash 无法保存已提交内容。
- [暂停状态](pause-state.json)、[进程停止记录](pause-process-stop.json)：本次服务端和 UI 探针均已退出，未留下本次浏览器进程。`ui05` 因主控暂停终止（UI exit 143，服务端 exit 0），不是界面验收结果。

规格仍为 T-066 ready_rev 1、controller-split-user-input spec 第 5 节及 brief-T-066；决定 01 批准的两处接入此前已经实现。没有改正式工作台、用户配置、Herdr 或共享构建输出，没有 push。所有失败与数据库保留；私有 token 未入 Git。

## 已实现但未验收完成的候选

核心 stop 删除 ideation 地址放行检查，改看 `a2a:stop` 能力；没有冻结角色的调用者仍拒绝。只有 a2a_stop 使用凭据的冻结角色地址，记录 caller_thread、caller_turn，目标 thread 独立保留；其他命令的地址投影不改。保留两分钟、ack、操作锁和只中断条件。

任务窗口新增“紧急停止记录”，旧 JSON 事件缺调用者字段时显示“未记录”。没有新增数据库列或改写旧事件。界面流程验证尚未完成，不能据代码或截图推定 PASS。

批准的上游文件仅两处：`apps/server/src/agentGateway/toolRuntime.ts` 增加可选 callerA2ARole；`apps/server/src/agentGateway/mcpTransport.ts` 从凭据冻结角色赋值。其余修改在 brief 允许的四个 a2a 目录内，完整清单在 fork 提交中。

## 现有证据

真实隔离服务端、真实 MCP、真实核心 SQLite；活跃会话事实受控，模型 turn 为 0。Bun 1.4.2、Node 24.13.1 经 fork 的 a2a/scripts/bun；后台服务脱离调用者进程组。没有真实 provider 绑定，所以证据证明中断请求与记录，不证明 provider 物理中断成功。

| 检查 | 暂停时状态与证据 |
| --- | --- |
| 基线红态 | red02：executor 调用成功，actor 却为 ideation，缺调用者 thread/turn；主控决定 01 接受该红态。red01 是 setup 失败；red02 原生事件 oracle 的过严部分按 reassessment 重评，原结果未覆盖。 |
| 实际角色、身份伪造、目标与状态 | green04 的 checks/trace：executor、ideation、授予 stop 的 monitor 按各自冻结凭据记录；伪造参数不生效，目标不变，task 状态不变。 |
| 期限、ack、权限与失效 | green04：新条目太早拒绝，超过 121 秒后放行；已 ack 拒绝；旧无 stop 凭据、inactive turn、吊销 token 均拒绝且不追加停止事件。 |
| 旧库 | old-db-reopen：候选核心重新打开实际 red02 SQLite，全部原事件行与表列保持不变；green04 核对旧事件原始详情字节不变。 |
| 相关套件 | server-final：128/128；gates-final：21/21；web01：3/3。 |
| 代码检查 | typecheck-final：8 个 workspace 通过；lint-final：0 错误、880 警告；fmt-final 通过。 |
| 反事实 | parent-tools-red03 拒绝旧角色投影；ack-mutant-red03 拒绝删锁；capability-mutant-red03 拒绝删能力检查。前两轮 mutant 配置加载失败保留，不算反事实。 |
| 界面 | INCOMPLETE。green02 dev origin 未配置、green03 首次导入弹窗、green04 同名按钮定位冲突均保留；ui05 的定位器已收窄，但重放被 #28 中止。没有界面 PASS。 |
| 独立审查 | 未启动。review-contract 只是准备文件，不是审查结果。 |

green01 因夹具复用 commandId 失败；green02 用被中断的目标作为调用者，green03 留下相互矛盾的受控活跃事实，均保留，未改生产逻辑绕开拒绝。gates01 与 typecheck01 的新增测试夹具错误也保留。曾在中间消息中过早把额外角色场景称为通过，随后依据原始输出更正；最终以机械输出为准。

## 失败方式清单

| 失败方式 | 处理与现有证据 |
| --- | --- |
| 调用者凭据已失效 | 网关拒绝 inactive/revoked，核心不记停止；核心第二次活跃检查的失效反例由相关测试验证。 |
| 同一目标被两个角色先后 stop | 独立追加各自调用地址、thread/turn，不覆盖旧记录；green04 验证 executor、ideation 和 monitor。 |
| stop 与 ack 交叠 | 现有条目锁保持；ack 先完成则 stop 拒绝；stop 持锁时 ack 返回 operation_busy，释放后可追加 ack。核心测试及删锁反例验证。 |
| 旧库缺新列 | 没有新增列；重开实际旧库后原事件行、表列不变。读取缺字段的界面实现存在，但可见流程验收仍 INCOMPLETE。 |

非阻塞上报 `20261010T151554Z-worker:t066-issue-001`：门禁 README 仍称不能编辑能力，与 T-064 已建接口不符；未顺手改其旧段落，交主控处理。

暂停证据提交的 diff 检查对原始工具日志报了尾随空白／末尾空行；日志原样保留，不为清理检查改写机械输出。文档与驱动文件另行检查。

重放命令保存在 replay.py、replay-ui.py、check.py、review-contract.md 和各 command/launch JSON。**暂停期间不执行这些命令**；恢复须有方向结论与主控指令。
