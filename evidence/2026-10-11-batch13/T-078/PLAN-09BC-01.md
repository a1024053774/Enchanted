# 09B／09C 计划审稿：真实角色 stop／ack 与两分钟只中断

2026-10-14，主控 #157。**计划交审；当前 launch NO_GO，业务验收 INCOMPLETE。** 按“先审计划再做材料”，本轮不生成实例、UUID、HOME、launch argv 或已可执行的审批包，不启动服务／窗口／CLI／模型。09A-3R2 的实际 clean／block 与资源收尾已局部 PASS，不代表 09B／09C 或整票通过。

目标：两名实际 Claude CLI 角色经原生会话凭据、实际工具调用、真实 Stop 转交及唯一门禁完成 stop→执行→ack；另用新实例证明真实时钟超过 120 秒仍无 ack 时 ideation 仅中断指定受管目标。非目标：真登录、真实模型决策质量、真实 Codex、切换日常派发、一般可靠性／成本收益，以及编辑他人 ticket／core.ts／taskCards.ts。新的权限、预算和文件所有权由主控审定；本轮不把前置列成已有授权。

## 已知入口前置

| 前置 | 当前源码事实 | 批准后应先证明的最小切片 |
| --- | --- | --- |
| Claude 请求转交 | `daemon.ts` 的 Claude Stop 分支对非空 relay_files 返回 controller_relay_not_enabled；launch 身份只可直接 signal | 一名实际 Claude 用自己的 capability 排入 inbox 请求，在匹配实际 Stop 上经唯一门禁执行并产生真实结果；空请求、错 session／prompt、重复文件、失效 launch 均留诊断 |
| stop 客户端可达 | `cli.ts` 会话排队名单包含 inbox_*，没有 stop；其他非 signal 命令返回 worker_command_forbidden | 把已批准的角色 stop 纳入原生转交契约，不新建绕过门禁的 HTTP／operator 通道；先真实入口红态，再绿态及权限反例 |
| 控制会话身份 | `panes.caller()` 先要求 pane.attempt；现 Claude controller 的 attempt=null、turn=null。relay.ts 类型／角色只支持 worker/reviewer，SQL attempt NOT NULL，必填 worker 的 attempt/fence | controller 以真实 launch/preset、project/task/spec_rev、native session、当前 prompt_id 和实际 leader 核对身份；不造 worker attempt、不把 null 改成假字符串、不跳过 worker fence/CAS 检查。Claude prompt_id 与 Codex turn_id 分开核对 |
| 实际角色登记及唤醒 | inbox 投递查现有 membership.presetThreads 和 ownedThread；P1 controller_start 当前只启动／记录 Pane，未证明能被此查询唯一选中 | 接上现有角色／会话归属，读回同 project/task 下 ideation、executor 及一个受管目标；实际 stop 投递、忙时排队／空闲写出均证明，不用另一个角色表或 operator 冒充 |
| 同后台、独立 HOME | claudeLaunch 要求 state=root/state、repo=root/repo，并固定 HOME=root/home、config=root/claude；分别用两个 root 又会触发 controller_state_mismatch | 每个实验一个 broker/state/repo，角色目录由绑定 preset 导出，各自 HOME/config/tmp/requests/hooks/user-data；真实角色 token/session/thread 各不相同。不共享配置、不复制用户认证、不松开根路径核对 |
| 工具许可与多回合 | 当前假 API 只有 cancel／echo，无 tool_use 交互；CLI 仅有 Bash/Read 可用工具，manual 不等于批准工具。P1 turn_limit 只允许 1/2 | 最小 tool_use→真实 Bash 客户端→tool_result→实际 Stop 探针先跑；每个精确命令及每会话 allow 规则单批，不用 bypassPermissions。复用 Stop 反馈会增加回合，按实测因果顺序冻结预算，不死等本回合尚未转交的结果 |
| C 的长观察 | 当前 cancel 假响应在 90 秒等待后会报错；核心 ideation 门槛是 elapsed >120000 ms | 新的受控保持屏障须覆盖 120 秒，不能沿用 90 秒 cancel；真实时间按 stop.created_at 算，目标检查点用 120.1 秒之后，不回写／快进数据库时间 |

这些是本任务内待安排的前置，不是本轮实现范围。涉及 cli.ts 超出 UserPromptSubmit 输出路径、relay.ts、claudeLaunch.ts、core.ts 或角色归属时，先由执行主控分配所有权／子任务，并与 T-080 协调。不得仅删掉 controller_relay_not_enabled 就宣称已接通。

**Tracer bullet**：先通过一名真实控制 CLI 的 inbox 转交，再接两个角色与一个确定性目标，最后扩到真实 120 秒。**Deep modules**：沿用 gates／身份／队列／转交的所有者；不添平行门禁、operator 代理、假角色凭据或回执成功兜底。**Ubiquitous language**：stop 条目、实际调用者、执行收据、ack、排队／送达、只中断、attempt/fence、prompt_id／turn_id 使用现有术语。

## 09B 正例与反例

建议一套新 broker、一项夹具 task，同时显示 ideation、executor 和一个受管确定性 worker 接收器。目标明确标注不是实际 Codex；真实模型 0。两名角色使用固定 2.1.296＋各自 loopback 假 API，以独立设置和 capability 跑交互 CLI。主控先逐次批准两个启动、原屏引导／信任、各自 readiness、精确工具命令；业务提示由 test-simulated-user 注入并保存自动化来源，不假称用户亲手输入。

| 阶段 | 独立验收条件 | 停止条件 |
| --- | --- | --- |
| B0 归属及目标 | 新 project/task、真实角色登记、两个 launch/session/thread；受管目标经既有任务卡／claim／派发，保存实际 attempt/session/fence/worktree 和模型 0 标签；同任务三窗格截图 | 未登记／多候选角色、错任务／旧 attempt、共享 HOME、权限或窗口绑定不明 |
| B1 ideation 发 stop | 真实 CLI 调用库客户端 send，kind=stop，to=executor，refs 固定本目标 thread/attempt 和本次合成输入；实际 Stop 转交、结果、唯一库条目 from=ideation | 用 operator 代写、只见 queued 当执行成功、缺真实 hook、目标不符或重复新增 |
| B2 executor 执行 | 实际收同 stop 和带标记唤醒；真实 CLI stop 命令经过门禁；emergency_interrupt_intent/requested 的 actor=executor；目标只收到一次 0x1b 的真实写入，进程保留，task/attempt/fence 不被回收／归档／改判 | 工具自报当写入、错目标、杀进程／reclaim/archive、未知写入或额外 Esc |
| B3 执行后 ack | 先取得 B2 的实际成功结果；在其后原生回合调用 ack，reply_to 同 stop_id；实际 Stop 转交落一条 ack，from=executor，ideation 真收回执 | 在执行结果未知时 ack、ack 先于中断、只查库代替实际收到、错来源或重复副作用 |
| B4 有效反例 | 用实际规则入口检验假 from 不覆盖凭据、外人 ack／旧 session／失效 token／错目标拒绝；重复同 ack 仅一条 ack，且不重复中断；每个反例都看到禁止结果被对应契约捕获 | 只在整个入口失败就算角色权限红态；放宽断言、自动重送或复用旧候选结论 |

当前 Stop 转交是异步请求：工具返回 queued 不是执行结果。B2 与 B3 应使用不同原生回合，由真实结果反馈触发后续 ack；若把 stop／ack 同批排入请求文件，尚不能证明执行在先，也可能因文件顺序错误提前 ack。假 API 只给出预批的 tool_use／脚本响应，不直接 append 库行、伪造 hook、改角色或执行业务代替 CLI。

建议上限供主控审：每场景每角色最多 6 个根提交、12 个主 Messages（合计最多 24），真实供应商模型 0；count_tokens 单列。这是拟议上限，不是当前预算或 launch 授权。先用角色反馈切片取得实际回合／Messages 因果序列，再尽量缩小并写入冻结 manifest；超过即 INCOMPLETE，不加预算或重试。权限反例可分新夹具，不能把会话撤销负例混入正例后偷换身份。

## 09C：新 stop，无 ack，真实超过 120 秒

B 的真实角色、结果反馈和中断入口通过后，C 用独立新 root/IDs/stop_id/目标绑定及新批准，不能复用 B 的 stop。批准的合成用户输入持续要求停止该夹具目标；观察来源为 test-simulated-user，不能报告为用户现场紧急请求。executor 真收到 stop，但受控假响应保持、不执行、不 ack；不把任意工具错误或未送达说成“有意不 ack”。

| 阶段 | 独立验收条件 | 停止条件 |
| --- | --- | --- |
| C1 起点 | ideation 实际 send stop／Stop 转交；真实 created_at、refs、角色及目标；executor 的真实 UPS/API/窗口收到 stop，无 ack | 没有实际投递、旧 stop 或错误 target，原生角色／输入要求无法核对 |
| C2 提前拒绝 | 在 stop 年龄明确 <120 秒时，通过 ideation 实际命令调用 stop；返回 stop_too_early，目标无新增 0x1b；拒绝反馈不导致自动再送 | 改数据库时间、用 mock 时钟声称实测、提前中断、无实际工具／hook |
| C3 持续观察 | 每段最多 20～30 秒只读采样；记录 wall UTC 与 monotonic、stop 年龄、无 ack、两个角色和目标身份及持续停止要求；日志可随时读，不做一次 120 秒阻塞 sleep | 丢采样／身份变化、出现 ack、要求取消、假服务 90 秒超时或其它未知状态 |
| C4 晚到只中断 | 确认 stop 年龄 >120000 ms（建议 120.1 秒之后）且仍无 ack／要求有效，ideation 实际 stop 命令经相同门禁；actor=ideation；仅一份目标 0x1b 写入、进程与 task/attempt 保留 | 使用 operator、快进时钟、kill/reclaim/archive、错目标／调用者、重复中断或超过 150 秒总观察 |
| C5 单独负例 | 已 ack、已撤销角色、错误 stop_id／target，各由具体规则拒绝；截图、库及原始 hook／PTY 与实际 CLI client 结果齐备 | 入口整体拒绝冒充规则证明、弱化无 ack／权限／时钟条件 |

C 长屏障不能伪造 Stop 或替角色调用门禁；生命周期保持和无 ack 都须在实际原生会话层观测。不要把实际时间提前断言抄成 120.0 秒整点就可通过，当前代码是严格大于。总观察最多 150 秒，缺证即 INCOMPLETE。C 的提交／Messages 上限按 B 的实测角色反馈协议独立冻结，仍不超过审定上限，模型 0。

## 材料门槛与交接顺序

建议批准顺序：① 分配／批准前置产品切片与文件所有权；② 一名真实角色转交／工具的红绿及边界反例；③ 冻结 B 的完整 role/root/argv/env、每会话许可、回合预算、逐屏模板、API 声明与独立 oracle；④ 主控审 B launch；⑤ B 实跑及收尾通过后再冻结 C；⑥ 单独审 C launch。

材料应保存同源代码提交和字节快照，两个角色启动身份、管理凭据不进入其工具环境、受管目标 claim 来源与真实身份、三个窗口绑定、每一动作批准、工具命令／预期实际结果、每阶段截止点、完整失败／原件与清理计划。三种模拟范围分别标记：真实 Claude CLI、脚本假 API／模型 0、确定性 worker 接收器。不能把它们写成真实模型判断或真实 Codex 行为。

清理逐实例授权，记录本次 PID/start/argv、用 C locale 读 ps、确认实际退出；只停自己的服务并归档后删自己的根，slot 删除仍须主控另批，不能在 launch 内含糊授权。关闭窗口不等于 agent 退出；signal attempted 不等于写入。新候选须有独立 reviewer／验收，旧审查不背书。

本轮只交计划与 09A 收尾提交脚本。没有新的 09B/09C 运行材料或批准，当前产品入口 NO_GO，不启动、不改这些前置、不创建新 ticket、不关闭 T-078、不集成、不 push。
