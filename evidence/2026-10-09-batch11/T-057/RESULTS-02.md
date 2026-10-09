# T-057 ready_rev 2 交接

状态：**BLOCKED（工程候选已实现；独立审查 INCOMPLETE；待主控决定，ticket 保持 open）**。

fork 候选 `7831241073c582458c10180e382f943cce1a9c6f`，基线 `2330534b2cf906b9d8f0a0b643adb370683d7fe0`，分支 a2a，未 push。依据主控 #6/#7/#8、[决定 01](controller-decision-01.md)、T-057 ready_rev 2、spec 第 4 节。完整版本绑定见 [candidate-binding-01.json](candidate-binding-01.json)。初轮 BLOCKED 报告、异常、红态和过渡候选结果原样保留。

## 主控需要决定

[needs-decision-02.md](needs-decision-02.md)，blocking 条目 `20261009T154855Z-worker:s11-t057-issue-001`：

- 真实 OS 通知显示、权限和当前隔离 Electron 入口尚未验证。三次 GUI 尝试是启动/窗口绑定失败，不能当成通知业务红态；未授予系统权限，未操作正式工作台，也未构建或改写共享 dist。
- 结束转交已在 issues/events 可见；executor 的未确认收件箱/ack 属于 T-058，目前未建成。没有把普通 events 列表改名冒称为未确认列表。

一次 fresh-context 只读审查结论为 **INCOMPLETE**，没有建立可复现候选行为违约；另保留“初次读取的既存 blocking 问题、初始/转入后台”通知场景，以及每个动作都经过 MCP 的证据缺口。见 [中文审查](acceptance-review-01.md) 和原始机器输出。未再启动审查，未上调结论。

## 实现与证据

| 条件 | 结果与证据 |
| --- | --- |
| 红态、反事实 | PASS：父修订五组合同失败；旧核心 legacy message UNIQUE 在第二条共享消息输入处失败。另捕获 reopen→snooze 与 needs-user 新答复周期的失败后修正，旧答复全部保留。`contract-red-01`、`migration-parent-red-01`、`reopen-cycle-red/green`、`needs-user-cycle-red/green` |
| 处置、派生状态 | 核心 PASS：close/needs-user/forward/reopen/snooze/dismiss/delivered 追加记录，理由/依据与原问题保留，注入时钟覆盖 15 分钟、1 小时及回拨。forward 与 spec/inbox 的超时规则对齐。MCP 动作集合未逐项复验，不能算完整多入口验收 |
| 角色保护 | PASS：真实 MCP 活跃主控凭据拒绝 blocking close 和 dismiss；普通 close 成功且 from 由凭据绑定会话派生。核心反例覆盖 worker、伪造 actor 和替用户回答。`transport-01-*`、`issues.test.ts` |
| 视图、徽标、按钮 | PASS（功能，外观由用户判断）：默认等你决定、全部、已关闭、理由/依据、重开、稍后、任务汇总；会话、任务项目栏、上游项目栏计数一致。三题按钮与批量按钮的完整矩形、点击中心命中和实际发送均记录。`panel-drafts-05`、`panel-send-01` 及对应截图 |
| 草稿 | PASS（真实浏览器应用）：同一隔离 profile 刷新及关闭浏览器后重启，三题草稿仍在；单键存储与既有编码器共享视图，发送后清除。外置盘旧 profile 的启动停滞现场保留；新 profile 位于 /tmp，构建缓存仍在外置盘 |
| 打包/逐个、精确格式 | PASS：真实面板发送，问题号 1/3/4，空正文、省略行、601 个 emoji 截断成 599 个加“…”、分隔文字原样、末尾空白、题间空行、关闭告知均逐字核对。逐个 2/5 各一条消息。预期由需求手写，不导入生产模板。`native-oracle-01.json` |
| 输入与去重 | PASS：五条 answer，reply_to 与问题对应，前三条共享 bundle/message ID，后两条各不同；原生恰三条 dispatchOrigin=user 消息，零重复 form=message，五个派生人工介入事件；门禁业务状态未改变 |
| 结束会话 | 部分 PASS：真实 thread.archive 后 answer 保存、forward/session-ended 发给 executor，原生消息数量不变、门禁 task 不变。未确认列表未验证。`ended-native-01.json` |
| 关闭告知 | PASS：不在 close 时起 turn，下一条打包消息末尾带告知；一条通知回执，后续逐个消息不重复。`native-oracle-01.json`、核心单条/逐个用例 |
| 通知消费者 | PASS（受控接收端）：后台暂停轮询的真实查询库行为先红后绿；两条新待决定合成一次现有 bridge 调用，silent/suppressWhenForeground 均 true。document 状态与 bridge 接收端是受控输入，不外推到 OS。`notification-consumer-red/green-01` |
| 新工具普通确认 | PASS：未改 computerToolPermission；实际 Codex manager 在两种 runtime 模式、已有 coordinator grant 下仍生成待批准请求。权限用例 14/14，无免确认路径。此为受控 native I/O，未冒称真实模型自动调用 |
| 集中检查 | PASS：核心 10/10，服务端 26/26，web 4/4，交付/恢复 17/17、编排 18/18；全 workspace typecheck、lint、fmt、迁移检查 exit 0。lint 870 warnings、0 errors，同步 fs 预算通过。未跑全仓测试、桌面构建或平台边界检查 |

Tracer bullet 真实 close/reopen 面板入口在扩展后的完整验证中再次覆盖。Deep modules：状态、记录、消息登记、按会话分包与通知回执仍由同一核心拥有；单条 published API 与批量 API 共用实现。Ubiquitous language 沿用问题、答复、处置、task/attempt/thread，未另建门禁或收件箱。

用户输入表只移除已过时的 message UNIQUE 约束；事务中复制所有旧字段、顺序与 JSON 字节，并恢复 append-only trigger。旧源码反例与新迁移用例均保留。没有依赖、内容含义的关键词/正则判断、自动重试或权限目录变更。草稿复用既有本机存储编码器，新增聚合状态用于多题/多视图与明确保存错误；界面复用 Button/Input/Textarea/Select/Badge 与字号 token。

## 六种失败方式

| 失败方式 | 处理及证据 |
| --- | --- |
| 两窗口同题答复 | 同 task 操作锁拒绝并发，完成后 issue_answered 拒绝重复；一个 answer/消息。显式 reopen/needs-user 开始新周期，旧记录不删除 |
| 答复时正在跑 turn | 既有服务 sendUserAnswer 使用 dispatchMode=queue；真实三条用户消息各落到会话并完成相应模型 turn。未把请求配置当作模型服务 tier 证明 |
| 送达前会话结束 | 仅明确的 session_ended 回执转交；真实归档分支已验证，不伪造新消息 |
| close 与 answer 交叠 | 同一操作锁；并发 close 被 operation_busy 拒绝，已关闭题须重开再答复 |
| 时钟回拨 | 按追加顺序取当前周期/处置，elapsed 下界为零；隔离时钟验证 snooze 未提早到期，非计时关闭/送达状态不受影响 |
| 正文含格式分隔文字 | 原样保留，不转义；真实消息与 Unicode/分隔哨兵手写预期相等 |

## 上游与边界

获批的上游只改三处：`Sidebar.tsx` 导入/挂载徽标，`__root.tsx` 导入/挂载提醒，`agentGateway/Layers/AgentGateway.ts` 导入/注册工具；其它变更均在指定四个目录中。`packages/a2a-gates/README.md` 是该 package 的接口说明。没有修改用户规则、地图、术语、他人 ticket、T-061 checkout、正式工作台、Herdr 或共享构建输出。

范围外 provider 读取容量拒绝已非阻塞上报：`20261009T142839Z-worker:s11-t057-issue-001`。没有认定它是持久 profile 故障根因，也没有作 retry/fallback 修补。

## 失败、清理与交付边界

准备失败全部保留：首次 tour 定位时机、刷新等待不足、旧持久 profile 启动停滞、并发预热下两项 5 秒超时、初次 handler 类型错误、三次 native 启动/窗口绑定失败。串行重跑的核心/最终检查已通过，不改写原失败。

真实 Codex 总计五个完成 turn：worker 四个（准备、打包、逐个两题）和 controller 一个；只有传输验收，没有模型改文件、submit 或权限 grant。CLI 0.162.0 固定，配置明确 Fast、关闭启动更新，只复制 auth.json，仅信任核对过的夹具根，规则仅 git add/commit，无 hook；/tmp 下的整个 auth home 已删除。原始账户日志本机私有保留，分享日志脱敏，不发布 token、auth、rollout 或 profile。

清理控制器经 gate reclaim 成功。worker 的 gate reclaim 被 identity_conflict 拒绝：初始问题的设置阶段使用受控 native 边界，turn_id 为 seed-turn，而后来真实传输有实际 turn id。没有改绑定或反例来制造通过；`gate-cleanup-01.json` 保留拒绝。随后只停止核对归属的测试服务进程，不把进程停止冒称门禁回收或验收。Git/门禁现场进入 tar，完整原生库、旧 profile 与私有日志留本机，索引见 `retained-fixture-index-01.json`。

这是一份明确版本的阻塞交付，不是 ticket 关闭、门禁验收/集成或上线。只有主控解决上述边界并重新取得缺失证据后，才能整体报告 PASS。
