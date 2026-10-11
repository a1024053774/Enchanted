STATUS: PASS

TARGET: T-075-3 `outside-b-06` 冻结候选；base HEAD `471fa75f7f28531e035479c795b043bb6cbc15f2`。审查前后分别逐字核对 `review-target-08.json` 所列 67 个源码文件/符号链接，均与 `outside-b-06/workbench-source.tar.gz` 一致。结论仅覆盖本卡。

EVIDENCE:

- 验收依据为任务卡、T-075 `ready_rev: 4`、当前规格相关章节、执行主控决定 01～05及回执回合授权。未读取主 agent 对话、PLAN.md、RESULTS.md 或推理记录。
- L3 真实链路：`outside-b-06/delivery/commands.json`、原生事件与启动记录显示，独立 CLI 连接常驻后台，node-pty 在 zsh 内启动交互式 Codex 0.162.1，完成显式文件 submit、Stop 转交、verify 和 integrate。
- 从归档 SQLite 以 `mode=ro&immutable=1` 独立读取：606 条编排事件、106 条门禁事件；导出的 156 条任务编排事件及全部门禁事件与数据库原文一致。请求 `delivery` 仅处理一次，门禁仅记录一次 submitted、一次 integrated。
- 直接读取仍保留的夹具 Git：G=`51d612b486c6935fe1616e001507eeeb47bafbe1`，C=`641e55b8d005281c672f544ebec1c8814ab87a53`，M=`287bbf8ae5eeadc901198233eeb0a0ac84f02b9e`。当前工作分支为 M，M 的两个父提交恰为 G、C，与数据库集成事件一致；独立 G 的 `host.txt` 内容保留。
- 候选提交具备九项本 attempt 尾注；库中统计的 2 个文件、增加 51 行、删除 2 行与独立 Git 读回一致。路径检查、完成条件及尾注检查均有实际结果。
- 独立 oracle 在起点因业务断言失败，在 M 上通过五组输入。本次额外以只读方式运行未出现于原 oracle 的 `Z9/Ω-sentinel` 聚合、60 分钟边界及浮点非法输入，分别得到总数 182、`1:00` 与退出 2 的 `invalid_minutes`，排除了固定输出。
- 派发及门禁回执均先登记再注入。真实事件记录两个开始、两个结束；回执文本与原生收到的消息一致，回执回合工具调用数为 0。启动配置及原生 turn context 均显示 `never`、workspace-write、网络关闭；无权限等待事件。
- 后台 PID/PGID/SID 均为 56959，与调用者不同；启动命令退出后的 ps 显示其 PPID 为 1。隔离 CODEX_HOME 已删除，夹具归档不含 auth.json。
- 后台入口的机械验收保存了 15/15、0 failures、0 errors；五张新增表具备 UPDATE/DELETE 拒绝触发器。session 起止地图检查均为 0 problems、0 stale。

FINDINGS:

- 未确认本卡范围内可达或已复现的行为违约。异常结果保留为拒绝或 unknown，没有发现将异常转成通过、自动重放未知操作或另开门禁写入路径的结构性问题。

COUNTEREXAMPLE:

- b-06 真实入口拒绝身份错误与缺 commit 请求，分别留下 `relay_identity_mismatch`、`invalid_relay_request`；重复文件留下 replay 事件，没有重复提交。
- `relay-counterfactual-05` 故意重复执行请求，在“执行次数必须为 1”的业务断言上失败。
- `dispatch-counterfactual-02` 去掉空闲条件，在“unknown 状态不得写字节”的断言上失败；`writing-counterfactual-06` 去掉写入期间 running 标记，在“正在写入不得当作 idle 回收”的断言上失败。
- b-05 原始输出保留了 `index.lock: Operation not permitted`。b-06 在生产派发提示要求独立执行 Git 写命令后，经真实入口完成提交和集成，未以孤立测试代替复验。
- 后台机械反例覆盖越界路径、完成条件失败、外来/错误尾注、过期 fence、旧 attempt、脏工作区保护等；缺尾注按修订契约记一次推断 action 与人工介入，并允许集成。

LIMITATIONS:

- 这是本地隔离环境的 Tracer bullet 通过，不是整个 T-075、工作台切换或生产发布通过。Electron、后台重启恢复、S2～S4、旧 run/reclaim 均未获本次背书。
- 编排、异步信号、身份边界、CLI、文件及 Git 副作用适用；检索/记忆为 N/A。本次没有重新调用模型、启动后台或运行写夹具测试。
- Model/Effort 尾注为 `unknown`，按规格允许；实际回合的 `gpt-6.1-sol`、xhigh 另有原生记录。Fast 仅证明已请求，未证明供应商实际服务等级。
- 门禁旧状态表及 membership 保持现有例外；“从事件重建全部状态并与视图一致”尚未验证。
- 变异及故障注入属于 L1 证据，不能扩张为真实进程崩溃恢复或全部输入的可靠性保证。
