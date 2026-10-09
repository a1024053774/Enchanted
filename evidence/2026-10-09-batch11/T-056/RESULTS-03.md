# T-056 决定 02 后的交付

**INCOMPLETE：实现和列出的工程检查通过，最终候选的独立审查尚缺。** ticket 保持 open，待主控关闭。决定 02 已解决 Unblock 接入、派生停止、项目键和 Herdr 交付方式；不再沿用 RESULTS-02 的范围阻塞结论。旧报告、两次 FAIL 和全部失败现场均保留。

依据 `ready_rev: 2` 及 [执行主控决定 02](controller-decision-02.md)。实际本票父修订为 `d479dab2a1608c3219b7a4e1c07e9056bfb63a9e`；本轮起点为 `2ad957d359281215ad3bf21fe47595ad6ad39c80`。最终 fork 候选为 **`ddcff9a643e15dd68c18186782e688e492bb44a8`**，分支 a2a，未 push。[完整候选源码与差异](final-source-47/revision.json) 绑定版本。

## 实现结果

Tracer bullet 继续经过真实 WS、原生编排引擎、门禁库与人工介入展示。Deep modules 的输入事务留在门禁核心；三个 WS 观测点共用 a2a 模块内的记录和故障策略。Ubiquitous language 沿用用户输入、人工介入、task、attempt、thread，不判断正文含义。

- `reconcileProviderDelivery` 在 handler 入口记录，每个到达服务端的请求一条 action。目标保留 thread、已知项目与请求的 eventSequence；同一参数第二次到达，即使业务 CAS 拒绝，也有另一条输入。没有新增按钮级分组或修改 RPC 业务语义。
- BranchToolbar 的工作目录和 worktree 切换停止均带 `origin: ui-derived`，记录而不派生人工介入。普通 thread 的 prepareQuitResume 项目键取服务端快照。
- 第二次独立审查发现编辑重发、检查点回退漏记。已补入口命令及对应恢复事件枚举。编辑重发保留 message 目标键和结构化请求原文；人工介入展示接受动作所带的有效 message 键，继续拒绝空字符串、非字符串和身份绑定错误。
- 受管失败 latch、非受管尽力记录与恢复、消息来源判定、问题面板答复登记、迁移和追加式约束沿用已实现路径。T-057 的问题处置与发送行为没有重写。

## 行为证据

| 检查 | 结果及具体边界 |
| --- | --- |
| 原票实际父修订红态 | PASS（红态证据），见 red-matrix-03；worker 消息有记录，其余 9 项没有，断言退出 1。保留旧证据，不宣称它覆盖本轮新增项 |
| 决定 02 的 5 项追加红绿 | PASS；2ad 上 resume-red-30 五项均失败，cb9 上 final-resume-32 均通过。Unblock 一成功、一业务拒绝，均各一条输入；两处实际调用构造器标 ui-derived；普通退出恢复带项目键 |
| 重试漏记红绿 | PASS；[retry-red-37](retry-red-37/retry-oracle.json) 两条真实 WS 命令均被接受且有域事件，输入为 0。retry-green-38 每条恰一条 action，原请求、项目与 message 目标保留，重复 RPC 不重复。相应执行命令均保存 |
| 最终候选完整矩阵 | PASS；[final-resume-44](final-resume-44/summary.json) 原 10 项、[追加 5 项](final-resume-44/resume-oracle.json)、[重试 2 项及去重](final-resume-44/retry-oracle.json) 均通过。provider 禁用，原生回答与审批 ID 在该矩阵中是受控哨兵；不把它说成真实模型交互 |
| 人工介入目标展示反事实 | PASS；真实 managed 编辑事件交给实际 web 解析器。cb9 解析器退出 1，最终解析器退出 0，并拒绝无效 message 键，见 retry-projection-red-39.json、retry-projection-green-39.json。不是浏览器截图验证 |
| 重试恢复与 gap | PASS；[retry-recovery-43](retry-green-38/retry-recovery-oracle-43.json) 在隔离副本模拟事务输出丢失：来源登记存在时恢复原输入并补域事件引用；来源也丢失时各线程只记 gap，不生成用户 action 或人工介入。原 native journal 未修改 |
| 最终候选故障边界 | PASS；[boundaries-resume-46](boundaries-resume-46/summary.json) 验证已知目标字段、agent/automation/a2a 排除、ui-derived 与重复命令、明确 managed 输入派生、未知非观测命令、追加式、普通输入失败仍接受业务、managed 输入失败拒绝及 latch、隔离复制库重启恢复 |
| 原生 Codex 问答 | PASS（固定 c7 的真实 provider 边界及当前候选重放）；原问题、答复与原生接收见 native-frozen-15。最终 dd 读取其未修改的真实权威事件，恰一条 answer 指向真实问题，答案为外部哨兵“蓝色 Ω 用户哨兵”，见 [native-authoritative-replay-45](native-authoritative-replay-45.json)。本轮新增 provider turn 为 0；不是最终版本新跑一轮 provider |
| 迁移、历史与大负载 | PASS（此前专项，相关代码本轮未变）；migration-frozen-14、migration-parent-11、extras-16 保存旧库副本逐条比较、迁移中断回滚及重跑、父修订反例、大文本与附件引用、重启去重；不冒称本轮重跑迁移 |
| 最终候选既有 35 项 | PASS；[编排 18/18](orchestration-resume-44/command.json)、[交付 8 + 恢复 9](delivery-recovery-resume-44/command.json)，原断言与期限未变。这也是 T-044 所指的 35 项 |
| 最终候选 membership | PASS；membership-resume-45，原独立场景覆盖两任务、角色、CAS、未知身份、重复成员、trusted origin |
| 最终候选静态及相关测试 | PASS；final-*-44.command.json：fmt、lint、全 workspace typecheck、migrations:check、gates 10、server 77、web 4 均退出 0。web 命令匹配到 2 个测试文件；不将不存在的 web issues.test.ts 算成已运行 |
| 独立审查 | FAIL（c7）与 FAIL/P1（cb9），均保留。dd 已修复第二次 finding，但没有获得针对 dd 的 fresh-context 审查结论，故此项 INCOMPLETE |
| Herdr 交付 | 按决定 02，用 fork commit、a2a 证据 commit、本报告和 DONE 行交付；不要求门禁 submit 或 attempt/session/fence。不冒称已验收、集成或关闭 |

Unblock 的业务失败依赖状态由 server-fixture-30 控制，经实际 delivery repository claim/markTerminalFailure；输入经过真实 WS 和生产记录路径。BranchToolbar 证据执行两个源码构造器并经真实合同解码、WS 派发，未声称真的点击 GUI 按钮。

## 独立审查缺口

决定 02 授权的一次追加审查已用于 cb9，返回 [FAIL/P1](acceptance-review-35.md)。修复后没有把旧审查变成 PASS，也没有自行启动第三次。已交执行主控 [审查次数待决](needs-decision-44.md)，收件箱 `20261009T201420Z-worker:s11-t056-needs-decision-001`。

[behavioral-acceptance-review](/Users/luckye/.agents/skills/behavioral-acceptance-review/SKILL.md) 要求 “Review one frozen candidate snapshot in a fresh, read-only context.” 当前 dd 的审查缺项由此单列；不以工程绿态代替独立审查。此前故障归因 P1 的修正证据仍见 RESULTS-02 与 scope/checkpoint 专项。

## 重放、失败现场与收尾

新的独立标签会创建新目录，不覆盖旧输出。可按以下方式重放主要入口证据（`NEW_LABEL` 换成未使用的标签）：

```sh
python3 evidence/2026-10-09-batch11/T-056/start-server-30.py NEW_LABEL
python3 evidence/2026-10-09-batch11/T-056/final-matrix-44.py NEW_LABEL
python3 evidence/2026-10-09-batch11/T-056/final-checks-44.py
```

最后一条的证据名固定 44，保存原始输出时会拒绝覆盖；重放检查需先复制 helper 并换用新证据编号。35 项的完整 argv、环境与源码副本在各自 command.json/sources/；真实 provider 重放完整操作在 native-authoritative-replay-45.py。故障/恢复脚本、具体 RPC 输入、协议帧与 SQLite 查询结果均保留。

新准备失败不计作功能红态：resume-red-28 未建立 blocker；resume-red-29 的 delivery 已成功而不能 claim；retry-red-36 选到不可编辑的 async 回答；retry-recovery-39 在线备份被原生库锁阻挡，核对后只终止自己的 helper、保留 -15；retry-recovery-40 在副本仍被追加式 trigger 拒绝；41 的比较未允许重放补充 event 引用；42 错把 checkpoint 的 activity 事件当作请求区间起点；修正后的 43 使用合同的 requested 事件边界通过。归档准备 47 错读 scratch 字段，48 使用 artifacts 字段完成。原始异常与部分目录不覆盖。

所有自建后台服务均核对 PID、启动时间与 argv 后停止，见 cleanup-resume-reds-33、cleanup-final-resume-35、cleanup-retry-source-40、cleanup-final-47。Git/worktree 与门禁完整现场在 retained-resume-git-gates-35.tar.gz、retained-final-git-gates-48.tar.gz；原目录保留，无 gitlink，provider profile、认证和原始会话不打包。

原票上游接入清单为 **5 个文件**：`packages/contracts/src/orchestration.ts` 的相关可选 origin；`RunningChatsQuitCoordinator.tsx`、`useTemporaryThreadLifecycle.ts`、`BranchToolbar.tsx` 的自动派生调用标记；`apps/server/src/wsRpc.ts` 的 import 及三个入口挂接。其他代码在获批 a2a/contracts 模块。完整差异见 final-source-47。没有改 AGENTS、CONTEXT、地图、其他 ticket 或 attempt，没有停止正式工作台/Herdr、改用户配置、dist 或依赖目录，没有 push。

本轮新 provider turn 为 0，原票先前共 4 个完成 turn；隔离 CODEX_HOME 清理事实仍由 cleanup-auth-12/17 支持。实现 worker 的启动 argv 和供应商实际 tier 仍未证明；不把请求设置当作实际 tier 证据。未运行 Electron 构建、全仓完整测试或 GUI 外观验证。源代码 diff 检查通过；证据中的原始日志空白保留，另存暂存检查结果，不改写失败输出。最终 project-map status 与文档 UTF-8 检查另存证据。a2a 仅提交本票证据、自己的收件箱条目和 ticket Resolution，Acceptance 留主控核对。
