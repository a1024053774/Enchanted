# T-076-1 执行记录（2026-10-11）

状态：**PASS（仅 T-076-1）**。真实两回合、候选五类变异体、检查器字段/删行反事实、候选 8/9/18 回归和一次 fresh-context 只读独立审查均已 PASS。源码提交为 **`42e2b8ed3caed775133eb3cafff5f4ee5ab68330`**，与审查快照逐字节一致；本报告及 Resolution 的交付提交只更新证据和文字。真实预算累计 **3/3**，不再启动真实 Codex。完整交付的一致性报告仍为 INCOMPLETE，两个 attachment 窗口均为不一致；主控 #9/#10 已转构思主控另切片，本卡不修存储，原失败证据保留。T-076 保持 open，待 T-076-2、待主控关闭。

实施起点为 `18235b2c53610c412b5f4ea53e0e6e5c56d35849`；起点红态从该 Git 对象导出冻结产品源码。其后共享 main 已前进，本卡未改其他 worker 的文件，各候选运行以源码归档和完整版本绑定。初始授权为 `controller-decision-01.md` 与主控 #4、#6；最后两个真实回合由 `controller-decision-03.md` 明确批准。真实 Codex 累计 **3/3**，不是三次成功交付：outside-real-03 消耗 1，outside-real-04 消耗 2。

首次共享分支核对时 HEAD 为 `8ab5177d09dcb25f57a50ad2166dc0006ea99ce3`：相对本卡起点，T-079 已改变 `acceptance/test_herdr_traceability_e2e.py` 并新增 `test_launcher_shell_ready_e2e.py`，所以不能宣称整个 acceptance 目录的总 diff 为空。本卡没有编辑这些文件；门禁三套 `test_coop_e2e.py`、`test_recovery_e2e.py`、`test_run_e2e.py` 相对起点 diff 为空。该跨卡验收归属已单独上报，不回退他人的修改；最终报告按比较范围如实列明。产品 src/hooks 已在本卡修改，不再沿用实施前的空 diff 结论。

## 六项完成条件

| 条件 | 当前状态与证据边界 |
| --- | --- |
| 真实受管提交的实际模型/强度 | PASS；outside-real-04 的 C=`3f7f0b4...`，Model=gpt-6.1-sol、Effort=xhigh，与启动记录和提交回合原生上下文一致 |
| 多回合 run/reclaim 正反例 | PASS；确定性正反例 4/4；真实回执后 run completed/reclaimed，原交付回合及稳定身份未被替换 |
| 完整交付库的逐表一致性检查 | PASS（如实报告条件）；三张非空主视图一致、成员/预设无法重建；其余空表不冒称覆盖；attachment 两个窗口均不一致，主控已转另切片。全库报告仍 INCOMPLETE |
| 五类变异体在业务断言失败 | PASS；候选两个对照 exit 0，五个单点变异体均 exit 1，业务失败位置逐项见主控 #25 节 |
| 当前候选 8/9/18 与 acceptance diff | PASS；outside-green-regression-02 为 8/9/18、0 failures/errors/skipped；本卡未修改 acceptance，三套原断言相对起点 diff 为空。其他卡的 acceptance 改动单独上报并保留 |
| project_map.py status | PASS；源码提交后检查仍为 0 problems、0 stale；最终证据与提交读回另存 |

## 首次 red-focused：保持 INCOMPLETE

重现命令（标签必须全新，首次目录不覆盖）：

```sh
zsh evidence/2026-10-11-batch13/T-076/card-1/outside-sandbox.sh red-focused <全新标签>
```

首次原始结果：[outside-red-focused-01/run.json](outside-red-focused-01/run.json)。协调阶段退出 1、INCOMPLETE、真实回合 0；trailers 子运行退出 1，reclaim 子运行随后出现读库异常；run 和 checker 缺入口信号未执行。不能把首次整体结果上调为 PASS。

### 尾注五个用例的独立读回

核对原 [trailers/run.json](outside-red-focused-01/trailers/run.json) 和每个 `.message.txt`，两项各只有一个尾注，值如下。业务预期来自批准计划及测试提供的根回合记录，不来自 hook 输出。

| 用例 | 要求的实际 Model / Effort | Git 读回 Model / Effort | 结论 |
| --- | --- | --- | --- |
| matching-request | gpt-6.1-sol / xhigh | unknown / unknown | 预期业务红态 |
| different-request | observed-sentinel-model / medium | unknown / unknown | 预期业务红态，不能用请求值冒充观测 |
| latest-turn | latest-sentinel-model / high | unknown / unknown | 预期业务红态 |
| auxiliary-ignored | root-sentinel-model / medium | unknown / unknown | 预期业务红态 |
| current-context-missing | unknown / unknown | unknown / unknown | 正例 PASS；缺当前回合上下文就保持 unknown |

前四项在 `A2A-Model` 断言先失败；`A2A-Effort` 仍完整读回为 unknown，与各自所需实际强度不同。这些记录证明起点的字段缺口，不证明真实沙箱能读取原生文件或记录落盘时序。

### reclaim 与读回夹具错误

原 [reclaim/stderr.txt](outside-red-focused-01/reclaim/stderr.txt) 保存了 unittest 的 `reclaim --attempt ...` 断言失败，CLI 返回 `identity_conflict`，attempt.turn_id 为 delivery-A、live.turn 为 receipt-B。同一条回复中的原生会话与运行时身份事实不变。这是待重新取得完整收据的业务观察，不能据此忽略后处理错误。

随后 [reclaim.stderr.txt](outside-red-focused-01/reclaim.stderr.txt) 在测试结束后查询 SQLite 时抛出 `sqlite3.OperationalError: unable to open database file`。原收集代码在 `stop_host` 关闭后台之后才读库，错误使 `run.json` 没有写出；协调器因缺少完整子收据停止。没有把这个收集错误计入产品红态，也没有覆盖原输出。

原测试与协调器在修复前的字节副本保存在 [readback-repair-01](readback-repair-01/)。夹具修复仅改 `workbench/tests/`：

1. 自建 host 停止前，用只读连接查询 tasks、attempts、verifications、runs、events，显式关闭连接，把原始行和 test/数据库路径/PID/阶段直接保存到本轮证据的 readbacks/。
2. 汇总阶段只读已保存 JSON，并核对归属；不再访问已停止的 SQLite。即使捕获失败，仍走原自建 host 停止流程，异常交 unittest 记录。
3. 先保存不可覆盖的 `test-result.json`，再做快照汇总与归档。后处理失败会在最终收据里明确报告，不能再吞掉已经完成的失败断言与 CLI 回复。
4. 协调器把 checker 缺入口信号提前到本阶段开头，独立保存 `checker-contract-red.json`；随后任何夹具失败都不会掩掉该证据。有效身份红态还必须有完整的停止前快照，不能只有退出 1。
5. 新运行保存所用测试宿主与脚本的 `harness-source.tar.gz`，并检查期间是否变化；产品冻结包仍绑定原起点。

读回夹具本地反事实命令：

```sh
python3 -B workbench/tests/test_multiturn_readback.py --known-bad evidence/2026-10-11-batch13/T-076/card-1/readback-repair-01/test_multiturn_identity_e2e.py.before --output evidence/2026-10-11-batch13/T-076/card-1/readback-repair-01/<全新标签>
```

[local-counterfactual-01/run.json](readback-repair-01/local-counterfactual-01/run.json)：5 项 PASS。保留的旧 stop/收集代码在关闭 writer 并移动自建根目录后无法读取；候选从停止前快照读回独立 SQL 哨兵行，且拒绝错 test、错数据库路径和错阶段的快照。这里只用本地 SQLite 和合成 host，不启动 daemon、socket、Git 或模型；不把这项 PASS 当作真实后台重跑通过。

## 首次 red-mutants：起点覆盖取证 PASS

重现命令：

```sh
zsh evidence/2026-10-11-batch13/T-076/card-1/outside-sandbox.sh red-mutants <全新标签>
```

原始协调记录：[outside-red-mutants-01/run.json](outside-red-mutants-01/run.json)。离线字节/窗口对照、缺盘构建对照均退出 0。五个变异体各只改 `/tmp` 产品源码副本一处，均退出 1；执行主控运行未使用模型回合。覆盖归属与失败类型是两项事实：**前四类“已有覆盖”，其实际失败均为业务断言；第五类补了测试，也在业务断言失败。**

| 原计划类别 / 变异体 | 起点覆盖归属 | 实际失败位置与业务事实 |
| --- | --- | --- |
| 省略字节 / omitted_bytes | 已有覆盖 | 原 `test_offline_trace_e2e.py:107` 的 `actual == data` 失败；pane_output 调用退出 0、返回合法块，但与独立 trace 字节不同。失败发生在 CLI 字节断言，尚未启动 Electron；不冒称证明了实时关闭期间字节 |
| 关窗口误停后台 / window_stops_daemon | 已有覆盖 | 原测试第 157 行要求关窗后同一 daemon 可查询；实际窗口正常关闭、退出 0，随后 daemon_status 因自建 socket 已消失而退出 1。变异源码明确在关闭事件中请求 daemon_stop；这是产品生命周期被破坏，非初始环境/socket 建立失败 |
| 缺信号标 idle / unknown_is_idle | 已有覆盖 | 原测试第 98 行要求历史窗格 unknown/interrupted；pane_status 退出 0，却返回 state=idle、lifecycle=interrupted、historical=true。失败发生在结构化状态断言，Electron 尚未启动 |
| 重启标成功 / restart_success | 已有覆盖 | 原测试第 126 行要求实际窗口 state=unknown、gate=claimed；变异体错误投影 gate=accepted，窗口业务断言失败。没有启动新模型，也没有把数据库真的集成为 accepted |
| 缺盘仍构建 / missing_volume_builds | 原阶段缺这一明确变异断言，本卡新增 | 新 `test_build_volume_contract.py` 要求不存在的配置 volume 必须拒绝。变异体构建命令退出 0、创建外置盘专属 absent-volume 根及产物，故业务断言失败，classification=business-red；没有把缓存写到内置盘 |

每项原异常、traceback、命令和单点 patch 均在对应子目录与 `mutant-sources/`，原 verdict 不改写。前四项原脚本未保存 classification 字段，本表依据实际断言、命令读回和阶段记录补充分类；不伪造原字段。对照成功、变异体命中预期业务行为后才认可起点覆盖。此阶段只证明起点这些反例能被抓住，**不替尚未产生的最终候选背书**。

## red-focused-02：有效红态已核对

执行主控 #7 运行后，worker 核对 [outside-red-focused-02/run.json](outside-red-focused-02/run.json) 及各子收据：协调结果 PASS，只代表 focused 红态证据成立；源码基线仍为 `18235b2c...`，测试宿主期间没有变化，真实回合 0。

| 步骤 | 原始退出与失败 | 核对结论 |
| --- | --- | --- |
| trailers | exit 1；四个有实际上下文的用例均在实际 Model 断言失败，Model/Effort 均读回 unknown；第五个缺上下文用例通过 | 四个缺陷业务红态成立；缺上下文正例保留 |
| reclaim | exit 1；1 test、1 failure、0 errors/skipped，无 collection_error；首次 reclaim 返回 identity_conflict，delivery-A 对 receipt-B | 同一原生会话/领导者的新回合被误拒，业务红态成立；停止前快照与原任务绑定完整 |
| run | exit 1；1 test、1 failure、0 errors/skipped，无 collection_error；run 返回 identity_conflict/outcome=paused，停在 waiting_submit | 同一运行身份在提交后进入回执回合即误拒，业务红态成立；不是超时或环境失败 |
| checker | 独立命令 exit 1、entry_exists=false，缺 stateConsistency.ts | 合同红态成立；这是缺功能，不冒称某张表已证明不一致 |

run/reclaim 的 attempt.turn_id 均为 delivery-A，live.turn 为 receipt-B；运行身份、工作区和 provider 保持原值。每项保存 `test-result.json`、`run.json` 和 `before-host-stop` 的 readbacks，失败没有再被后处理错误覆盖。原 red-focused-01 仍保持 INCOMPLETE。

## 候选修复与绿态交接

- 尾注：启动请求改存 `A2A_MODEL_REQUESTED`/`A2A_EFFORT_REQUESTED`。prepare-commit-msg 从隔离 home 的唯一匹配根 JSONL 读取最近 task_started 对应 turn_context；缺当前事实保持 unknown，错根/歧义/坏记录明确拒绝，不用请求值替代。
- 身份：新增 attempt.runtime_identity，启动时绑定 launch/thread/shell，再只补首次观测的领导者与原生会话。已绑定值不能更换或消失；run/reclaim 比较该身份，submit 继续核对当前活动回合及原 session/fence/spec/attempt。停止后沿用原身份与确认的生命周期。旧受控线程测试宿主提供明确的所有者代次，原 acceptance 业务输入和断言不改；不在产品中加旧 turn 回退。
- 一致性：新增只读 stateConsistency.ts，不实例化门禁或改表。由事件重放任务、历史 attempt/verification、run、attachment，逐字段比较；覆盖写但缺完整历史来源的另库/其他表如实标无法重建，不补答案。
- 运行器：增加 output-root，suite/probe 默认路径不变，子运行传递输出根；旧 validation 的冻结基线程序保留原根，避免把旧证据混写到本卡。删除运行器中固定旧 worker/session/launch 的元数据，实际 task/attempt 身份仍来自每个夹具与外层收据。

执行主控首先运行：

```sh
zsh evidence/2026-10-11-batch13/T-076/card-1/outside-sandbox.sh green-focused outside-green-focused-01
```

该阶段使用新冻结源码副本，不消耗真实回合：尾注与现有 hook 拒绝检查；run/reclaim 正例和伪造原生会话/领导者反例；再经唯一 CLI 完成一个新的完整交付，在停止前取得 SQLite backup 与只读逐表报告。**一致性报告若不一致或无法重建，脚本保存报告后立即返回 INCOMPLETE，不改存储，不继续反事实、回归或模型阶段，交主控处理。**

绿态未运行前不能声称身份修复或真实沙箱取值通过。独立审查和实际两回合 Tracer bullet 尚未进行；真实模型阶段未启用，不能把 argv 模板当实际启动证明。

主控处理该报告后，另选新标签运行已有的 `green-regression`（8/9/18）与 `green-mutants`（本候选五类业务反例）阶段；二者不会自动触发模型。不提前绕过一致性停止边界。

## 下一检查点

执行主控按主控 #7 用新标签运行 `green-focused`；worker 核对结果与实际逐表报告。ticket Resolution、提交、真实回合、独立审查与最终 8/9/18 尚未进行；本卡保持 INCOMPLETE。

## green-focused-01 与主控 #9 决定

原 [outside-green-focused-01/run.json](outside-green-focused-01/run.json) 保持 INCOMPLETE，不上调；真实回合 0、源码期间未变化。

| 子步骤 | 原始结果 |
| --- | --- |
| trailers | exit 0，五个独立输入全过；实际上下文值与请求值不同、最近回合、辅助会话排除及缺上下文 unknown 均成立 |
| hook-environment | exit 0；重复尾注、缺身份、换行注入等原检查通过 |
| identity | exit 0，4 tests、0 failures/errors/skipped；run/reclaim 回执新回合正例和伪造原生会话、领导者反例都通过 |
| consistency-delivery | exit 0，1 test、0 failures/errors/skipped；经 CLI 完成新的交付、集成和首次回收，停止前保存数据库备份与报告 |

报告为 [consistency-c-gaod4as5.json](outside-green-focused-01/consistency-delivery/consistency-c-gaod4as5.json)：截止 events seq=99，重放 99 条，unknown_events=0。tasks、attempts、verifications 各 1 行，字段与事件重建一致；runs、attachments、user_input_checkpoint、role_permissions 都是空表，只说明该夹具未覆盖。另库 memberships、session_presets 各 1 行，因完整变更历史不在 events 中而无法重建。

脚本按原停止边界保存报告并停止。主控 #9 明确将成员/预设问题转给构思主控另切片，允许本卡继续取证和剩余验证；worker 不改事件、存储、地图或该决定。

### attachment 专门取证交接

```sh
zsh evidence/2026-10-11-batch13/T-076/card-1/outside-sandbox.sh green-attachments outside-attachments-01
```

两个案例各有新夹具、独立后台和实际 attach CLI。creating 在原 createAttachedThread 边界暂停；active 在原 attached 事件写入之前由测试宿主同步暂停。产品 saveAttachment/event 代码不改。另一个只读连接读取可见行、事件和 active 点的事务事实，SQLite backup 固化该窗口，再运行正式检查器。释放后正常结束同一 attach 和后台；后来的 attached 事件不覆盖先前窗口证据。模型/真实附着 CLI 均未启动。

每点只使用“一致”“不一致”“无法重建”之一作为结论，原报告与原因同时保留。此阶段 PASS 只表示两项取证完成，不表示存储一致。出现夹具/协议未知就保持 INCOMPLETE 并停；不修改存储。

专门取证结果见下节；接下来按主控 #9/#10 的顺序继续真实两回合阶段、候选五个变异体、8/9/18、独立审查与交付。真实回合仍 0/3，第三个须先问主控。

## outside-attachments-01：两窗口结论均为不一致

执行主控 #10 运行并报告后，worker 核对 [outside-attachments-01/run.json](outside-attachments-01/run.json)：取证阶段 PASS，模型回合 0、源码未变化、两个自建 host 均确认退出。**这只表示取证完成，两个存储窗口并未通过一致性检查。**

| 嫌疑点 | 结论 | 独立事实 |
| --- | --- | --- |
| creating 没有对应事件 | 不一致 | `windows/creating/observation.json` 的独立连接可见 creating 行，thread=`ec726d05-7411-4e1f-8b6e-4783cb5210bf`；窗口备份的 checker 重建 0 行、观察 1 行，事件没有该附件的创建事实 |
| active 与 attached 不在同一事务 | 不一致 | `windows/active/observation.json` 的独立连接已读到 active 行，thread=`f980b168-6ac5-40a3-83bf-903dcbe8f8eb`；原 attached 事件写入前的状态库 `isTransaction=false`，重建仍 0 行、观察 1 行。active 已对独立连接可见而 attached 不存在，证明该窗口不属于同一事务 |

两个窗口分别有 `window-databases/`、正式 `consistency.json`、边界源码/状态、实际 CLI 输入与返回、释放后的事件和完整夹具归档。释放后补写的 attached 不改变此前窗口事实。主控 #10 已报给构思主控；本卡不修存储，也不把两个“不一致”改称一致。

## 真实两回合交接（尚未运行）

```sh
zsh evidence/2026-10-11-batch13/T-076/card-1/outside-sandbox.sh real-two-turns outside-real-01
```

`run_t076_real.py` 使用当前冻结源码，真实交互 Codex 0.162.1、gpt-6.1-sol/xhigh、Fast 请求、更新检查关闭、审批 never。隔离 home 仅复制 auth.json，只信任已核对的夹具 repo，只有 git add/commit 两条规则；已批准 hook 仅经本次启动参数与 Git 会话环境安装。实际完整 argv、环境白名单和启动记录在 `launch-record.json` 保存，模板不算实际证明。

用中等复杂度的两个 Python 文件实现聚合/Unicode/空输入/bool 与负数拒绝；独立 oracle 在起点 stub 上先失败。真实 `run` 绑定原 attempt，显式 submit 等待期限 100 秒（产品 transport 上限 120 秒），派发仍经实际 node-pty/zsh。工作分支独立前进到 G，worker 交 C；验收的外部 oracle barrier 只在根会话两个 task_complete 且 Stop 确认 idle 后由测试释放，确保回执 B 已发生才允许 verify/integrate/reclaim。

预期读回：同一领导者与原生会话跨两个不同回合，实际 Model/Effort 与提交时根 turn_context、启动请求一致；提交回合绑定不被回执覆盖；run completed/reclaimed，M 的父提交为 G/C。回执不调用工具，原生计数必须恰为 2。实际 tier 未观测时只报告请求 Fast。

预算文件 `real-turn-budget.jsonl` 追加预留 2 个回合；发现已有预留就拒绝另一次运行，不自动重试、不自动用第 3 个。结束前 Node SQLite backup 保存活动库；确认自建后台、shell/CLI 与调用者子进程退出后删除整个自建隔离 home，凭据不归档。失败、未知与清理问题均保留并交主控；没有此阶段实跑前，真实验收仍 INCOMPLETE。

## outside-real-01：夹具编号错误，真实回合 0

执行主控 #11 与 [controller-decision-02.md](controller-decision-02.md) 核定了本次核账。原 [outside-real-01/run.json](outside-real-01/run.json) 保持 INCOMPLETE；在 card_save 被 `invalid_task_card` 拒收，field=id，原因是夹具卡号 `T-076-1-real` 不符合“ticket 号加一个正整数序号”的合同。该错误属于本 worker 的夹具，不是产品缺陷或模型失败。

worker 读回 `commands.jsonl`、`events-before-stop.json`：card_save 的拒收发生在 run 子进程创建之前；只有 daemon_started、两条 request_received、一条 request_result，没有 pane_started、native_record 或 turn_submit_intent。因此没有启动 Codex，实际消耗 **0**。原观测字段 null 不改写成 0；0 的结论绑定主控独立核定与事件证据。原隔离 home 已删除，后台 PID 退出得到 ps 读回确认。

按决定 02，`real-turn-budget.jsonl` **追加** kind=reconciliation、reserved=2、actual=0，引用决定及原事件/运行文件；原 reservation 和 observation 逐字保留。预算读取仅接受该获准的零消耗核账，拒绝重复核账、未批准引用或非零实际消耗；下一次预留 2 个回合后，再次启动仍会被挡住。没有增加自动重试额度。

夹具编号改为合法 `T-076-9`，source 仍绑定 T-076 ready_rev=1；不改任务卡产品校验。修复前的脚本与预算副本留在 `real-id-repair-01/`。纯函数校验 `card-check.json` 确认旧编号拒收、新编号通过；`budget-check-02.json` 分别验证三项独立核账反例与预留计数，无后台/模型调用。

主控明确批准的一次新标签重跑：

```sh
zsh evidence/2026-10-11-batch13/T-076/card-1/outside-sandbox.sh real-two-turns outside-real-02
```

真实回合累计仍 **0/3**，新阶段计划用 2 个，第三个仍须先问主控。其余阶段的顺序、hook 批准、只复制 auth 的隔离、原 attempt 绑定和失败保留要求不变。新阶段未运行前，真实提交与回收验收仍 INCOMPLETE。

## outside-real-02：BLOCKED、0 回合与两处定位

执行主控 #12 核定实际 **0** 个真实回合：shell 3182 与 Codex 领导者 3184 存在，但尚未收到第一次输入，隔离 `codex-home/sessions` 没有 JSONL。两次 daemon_stop 被拒为 daemon_busy；主控核对它们及后台 3108 都属于 `/tmp/t76-real-shmlqa77` 后依次 SIGTERM，确认退出并删除该隔离 home。依据为 [原运行](outside-real-02/run.json)、[清理前](outside-real-02/executor-cleanup-before.txt)、[清理后](outside-real-02/executor-cleanup-after.txt)。原 BLOCKED、观测 null、home_removed=false 的历史记录均不改写。

预算只追加一条 `kind=reconciliation`、reserved=2、actual=0，`decision_ref=conversation:主控 #12`；原预留和观测保留。累计实际仍 0/3，不自动使用第 3 个回合。产品/夹具修好并取得同一确定性检查的绿态前，不交接真实重跑。

### 首次派发：这次失败来自夹具，不是 requireGate

原 traceback 指向冻结的 `run_t076_real.py:222`：测试脚本自己在调用 pane_release 前要求 leader 与 native_session 都非空。首次任务尚在队列里，原生文件要收到第一次任务才出现，形成循环等待。

对保留数据库的只读核对显示：attempt 已正确绑定 launch/thread/shell=3182/leader=3184，native_session=null；门禁没有 rejected/identity_conflict，run 最终为 deadline，而后台请求留下两条 daemon_busy。`runtimeIdentity` 允许初始未观测值；`observeRun` 只填首次观测到的值，已绑定值不能替换；`Panes.release` 的既有条件是有效 leader 且没有 failed，不要求 native_session。因而没有触发“原生身份未知”的 requireGate，这次不需要放宽产品身份检查或改设计。submit/reclaim 的完整身份门槛继续保留。

读回产物：`startup-shutdown-repair-01/preserved-state-readback.json`。原夹具保留期间的重新生成命令（输出名必须新建）：

```sh
python3 -B evidence/2026-10-11-batch13/T-076/card-1/startup-shutdown-repair-01/read-preserved-state.py /tmp/t76-real-shmlqa77 <全新输出.json>
```

已先保存修复前脚本和核心文件的 `.before`。将原脚本循环原样抽成 `release_initial_worker` 供确定性调用，未改变 native 非空前提；`extraction-check-02.json` 用 AST 对照确认前提未变。`extraction-check.json` 首次记录的命令字段只有说明性占位，属于证据元数据错误；实际可重放命令以第二条记录及下列命令为准，首次原文件保留。

```sh
python3 -B evidence/2026-10-11-batch13/T-076/card-1/startup-shutdown-repair-01/check-extraction.py <全新输出.json>
python3 -B workbench/tests/test_initial_worker_release.py --source /Users/luckye/Documents/Code/a2a --output <全新输出目录>
```

本地纯函数红态：`initial-release-red-local-01/run.json` 为 INCOMPLETE，4 tests、1 failure、0 errors/skipped。失败只在“首次输入应先于原生日志出现”的业务断言，读回 startup_identity_unknown；无领导者、被替换领导者两个拒绝对照以及已存在原生会话的正例通过。没有 socket、真实 CLI 或模型调用。这证明的是本 worker 的真实探针时序错误，不冒称为产品身份缺陷。

### 后台停止：活动 run 占据停止门槛

`daemon.ts` 在每个请求处理期间增加 activeRequests，只有 activeRequests===1 才允许 daemon_stop。长期 run 请求贯穿等待提交及失败后的 waitForIdle；所以停止请求变成第二个活动请求，尚未进入 `Panes.shutdown` 就报 daemon_busy。本轮先取红态，不删掉并发保护直接关库。

专门夹具将走真实 CLI/socket/后台/门禁/Git/SQLite；node-pty 回调和进程观测明确模拟，不启动 Codex、不复制凭据。三个案例为：首次输入后原生身份才可见并绑定（对照）；waiting_submit 时显式停止；run_deadline 后等待空闲清理时显式停止。停止正例还检查 run 不得变 completed、不验收/集成、不冒称回收、pane_exit 与请求收尾持久化。旧代码预计只在两条停止业务断言失败；夹具 errors、缺读回、清理失败均不算红态。

执行主控只运行下面这一阶段，使用全新标签：

```sh
zsh evidence/2026-10-11-batch13/T-076/card-1/outside-sandbox.sh red-startup-shutdown outside-red-startup-shutdown-01
```

该脚本冻结当前候选，保存源码归档和完整测试输入/输出。expected-red 汇总 PASS 只表示三个指定业务断言取到失败；原子测试的 INCOMPLETE/失败输出保留。主控回传结果后再修夹具时序与后台生命周期，再交接 green-startup-shutdown；真实两回合阶段仍未重新启用。本卡尚未提交、审查或完成 8/9/18。

## 主控 #13：红态核对、候选修复与绿态交接

核对 [outside-red-startup-shutdown-01/run.json](outside-red-startup-shutdown-01/run.json)：红态取证 PASS，源码期间未变化、真实回合 0；主控核对无残留进程。原子测试仍为退出 1，失败证据不改写。

| 信号 | 红态落点 |
| --- | --- |
| initial-release，4 tests | 只在 `test_first_input_precedes_native_log` 的业务断言失败，native_session=None 触发夹具 startup_identity_unknown；3 个对照通过、0 errors/skipped |
| daemon-stop，3 tests | waiting_submit 与 run_deadline 后等待清理两例都在显式停止应受理的断言失败，实际回复 daemon_busy；延期绑定的产品对照通过、0 errors/skipped |

候选修复：

- 夹具首次派发只要求已核对的领导者且没有 failed，随后通过 pane_release 发首次输入。原生日志出现后仍由正式门禁绑定；回执后的对比不再把启动时合法的 null 原生身份当成预期实际值。无领导者、领导者替换继续拒绝，submit/reclaim 的完整身份与活动回合检查不改。
- 后台显式 daemon_stop 进入关闭流程，设置门禁的关闭标记并拒收新请求；run 在等待循环、等待清理及下一门禁操作前停止推进。已经开始的操作仍持原锁完成，保存原错误与最终运行记录；等待清理被停止时不冒称 reclaim 成功。
- 后台等待活动请求和已开始的异步回执写入结束，再停止窗格、记录 daemon_stopped、关闭数据库和移除自身端点/PID。关闭期间不启动新的回执回合。没有兜底重试，没有强杀任意 PID，没有提前关库。
- 真实探针的失败收尾先保存活动证据并显式 daemon_stop，再等原 run/本夹具进程退出；不释放未确认的 receipt oracle barrier，不接管新 attempt。回合计数在停止确认后读取最终持久化原生记录，避免漏掉退出时导入的字节；确认退出后才删除隔离 home。
- 预算读取原先只认识决定 02，拒收主控 #12 的已批准零消耗核账，先保留 `budget-reconciliation-red-01.json`，再限定接受本卡两个明确输出各自对应的批准引用；重复、错引用、非零实际数和错预留数继续拒绝。新预留 2 后挡住下一次自动运行，不增加预算。

本地 `initial-release-green-local-01/run.json` 4/4 PASS，0 errors/skipped；`budget-reconciliation-green-01.json` 的 6 项核账正反例 PASS。两项都不启动 socket/模型；Node 语法检查、Python AST 与 diff-check 通过，不能替代后台绿态。

核账产物的冻结输入为 `startup-shutdown-repair-01/budget-after-12.jsonl`，重新生成命令：

```sh
python3 -B evidence/2026-10-11-batch13/T-076/card-1/startup-shutdown-repair-01/check-real-budget.py workbench/tests/run_t076_real.py evidence/2026-10-11-batch13/T-076/card-1/startup-shutdown-repair-01/budget-after-12.jsonl <全新输出.json>
```

针对本次红态的修复差异为 [startup-shutdown-fix.diff](startup-shutdown-repair-01/startup-shutdown-fix.diff)，其起点是本次红态冻结源码，未混入此前身份/尾注/一致性实现的差异。重新生成：

```sh
python3 -B evidence/2026-10-11-batch13/T-076/card-1/startup-shutdown-repair-01/emit-fix-diff.py evidence/2026-10-11-batch13/T-076/card-1/outside-red-startup-shutdown-01/candidate-source.tar.gz /Users/luckye/Documents/Code/a2a <全新输出.diff>
```

绿态交接只运行下列命令，**不运行真实回合**：

```sh
zsh evidence/2026-10-11-batch13/T-076/card-1/outside-sandbox.sh green-startup-shutdown outside-green-startup-shutdown-01
```

预期：首次派发 4/4；原来三个后台案例及新增的“已开始的门禁结果先持久化、daemon_stopped 后记录”共 4/4；多回合 run/reclaim 和伪造原生会话/领导者 4/4。新增顺序断言有单点反事实：删除等待活动请求的语句，应在实际事件序号的业务断言失败，不能有环境错误或缺读回。该反事实属于新增保护的覆盖验证，不是把新断言补称为此前红态的一部分。

绿态报告回传并核对后，再给主控新标签 real-two-turns。主控 #13 允许的真实重跑仍计划 2 个、累计实际 0/3；第 3 个仍须先问。本卡保持 INCOMPLETE，候选五类变异体、8/9/18、独立审查与交付尚未完成。

## 主控 #14：保留绿态 INCOMPLETE，修复停止后的读回

原 [outside-green-startup-shutdown-01/run.json](outside-green-startup-shutdown-01/run.json) 保持 INCOMPLETE，实际模型回合 0，主控核对没有残留进程。initial-release 4/4 通过；daemon-stop 为 4 tests、0 failures、3 errors，均在停止后查询原库时抛 sqlite3.OperationalError。第一次完整绿态没有完成顺序断言和最终持久化检查，不能上调为 PASS；反事实与身份子阶段还没运行。

本 worker 新写的三个测试又在关闭后以 mode=ro 直读原 WAL 库，漏用了已有的归档处理。这是夹具错误。现场核对原库文件仍在，关闭后没有 WAL/SHM；原文件和失败输出保留。主控 #14 已审过并同意 beginShutdown 后等待进行中请求收尾的产品方向，本次不改产品 src/hooks。

修法统一为 `fixture_artifacts.archive_stopped_database`：调用者先核对 writer 已退出、端点/PID 已消失，再复制主库及残留 WAL。只把**新归档副本**转为独立 DELETE 库并校验完整性，最后从该副本只读查询。原文件不打开写连接，不改变存储。三个停止用例仍保留原业务断言；活跃阶段的快照继续在原 writer 存活时读取，并明确保存 phase 和源库/归档库路径。没有冷读失败后再换路径重试，既有归档文件也不会覆盖。

同类修正用于真实两回合脚本的最终事件计数；原 `archive_and_cleanup` 里的复制/规范化代码抽到同一 helper，删掉重复实现。归档只处理本夹具文件，不改正式工作台或用户配置。README 加入该入口和机械检查指针，避免依赖记忆再写一套冷读收集器。

本地检查（都未启动后台、socket、Codex 或真实信号）：

| 检查 | 结果与范围 |
| --- | --- |
| replay-01 | 三个原失败夹具直接重放 PASS：旧 readback 仍失败，候选读取归档成功，原文件字节保持；只证明收集修复，不改原运行结论 |
| replay-02 | 从原 `fixtures.tar.gz` 的 DB/WAL 常规成员重放同三例 PASS，摆脱原 /tmp 目录依赖；检查原 deadline/暂停结果、无验收/集成/冒称回收、最后 create 结果早于 daemon_stopped |
| shared-archive-01 | 既有 `test_probe_cleanup.py` 7/7 PASS：关闭的 WAL、已提交 WAL 行、归档错误、已有归档不覆盖、未确认退出保留现场及延迟退出均保持原行为；ps 回调明确模拟，未运行 ps |
| scope-check.json | daemon.ts、core.ts、panes.ts 与失败绿态冻结源码逐字节相同；原文件与 diff 保存；完整 src/hooks 核对见下方 audit |

完整审计的首次 `audit-02/scope.json` 保留 INCOMPLETE：审计脚本只列 tar 常规文件，却在当前目录跟随了 26 个 hook 符号链接，集合不一致。诊断确认常规文件字节没有差异；修正为“常规文件比字节、符号链接比目标”，不省略链接。后续 `audit-03/scope.json` 为 PASS，47 个 src/hooks 文件或链接均与失败绿态相同。这是审计脚本的表示错误，不是产品改动。

保留修复前的 E2E/真实探针/helper `.before`；修复 diff 和完整来源核对由下列命令生成（输出目录须全新）：

```sh
python3 -B evidence/2026-10-11-batch13/T-076/card-1/stopped-readback-repair-01/readback-audit.py evidence/2026-10-11-batch13/T-076/card-1/outside-green-startup-shutdown-01/candidate-source.tar.gz /Users/luckye/Documents/Code/a2a <全新审计目录>
python3 -B workbench/tests/test_stopped_readback.py --known-bad evidence/2026-10-11-batch13/T-076/card-1/stopped-readback-repair-01/test_startup_shutdown_e2e.py.before --failed-run evidence/2026-10-11-batch13/T-076/card-1/outside-green-startup-shutdown-01/daemon-stop/run.json --fixture-archive evidence/2026-10-11-batch13/T-076/card-1/outside-green-startup-shutdown-01/daemon-stop/fixtures.tar.gz --output <全新重放目录>
python3 -B workbench/tests/test_probe_cleanup.py --output <全新检查目录>
```

下一阶段只重跑专门绿态，使用新标签，不使用真实回合：

```sh
zsh evidence/2026-10-11-batch13/T-076/card-1/outside-sandbox.sh green-startup-shutdown outside-green-startup-shutdown-02
```

预期集合不变：initial-release 4/4；daemon-stop 4/4 且最终读回齐全；缺等待的顺序变异体在业务断言失败；多回合/伪造身份 4/4。完整绿态报告尚未取得，本卡与真实验收仍 INCOMPLETE，累计实际回合 0/3。

## 主控 #15：加强顺序反事实，保留第二次 INCOMPLETE

核对 [outside-green-startup-shutdown-02/run.json](outside-green-startup-shutdown-02/run.json)：initial-release 4/4、daemon-stop 4/4，0 failures/errors，真实回合 0。阶段总状态仍为 INCOMPLETE，身份子阶段尚未运行。

原变异体并没有走到顺序断言：[ordering-counterfactual/run.json](outside-green-startup-shutdown-02/ordering-counterfactual/run.json) 是 1 failure、1 error。先在附带的 daemon_status 检查读到 daemon_call_failed，而非预期 daemon_stopping；cleanup 释放原 create 后又在关闭窗口直读原库，报 sqlite3.OperationalError。没有 shutdown-order.json，不能把这次环境/清理失败当成顺序业务反例，也不能补称测试抓住了缺等待的缺陷。

本次只改测试宿主、E2E 和反事实运行器，不改产品。修复前文件留在 `shutdown-order-repair-01/*.before`。加强后的业务含义仍是“原进行中的门禁请求必须先完成，停止才能写最终事件或退出”：

1. 在实际 create 的 ensureProject 边界保持 barrier，独立读取 task=creating、对应 request_received 的唯一请求号、CLI 仍未返回。
2. 发实际 daemon_stop。测试宿主只给**原始 net.createServer** 加一个被动 close 观察器，不替换服务器、连接或请求处理。stop 响应连接 close 后，setImmediate 记录检查点，位于关闭回调及其 promise continuation 之后。原 create barrier 仍保持，避免用任意 sleep 猜停止走到哪里。
3. 在释放 barrier 之前独立读持久化表，保存 `gate-held-after-stop.json` 和 `shutdown-precompletion.json`。若已有 daemon_stopped 而该请求的 request_result 不存在，直接在业务断言拒绝；后台已退出也直接拒绝。正常候选必须仍处于 creating，既无该请求最终结果，也无停止最终事件。
4. 通过提前观察后才执行原 daemon_status 拒收检查，再释放同一个 create。最终归档仍核对**该请求号**的 request_result 先于 daemon_stopped，不再用所有 create 的总数代替具体请求绑定。
5. cleanup 区分已经受理的停止和未受理的停止：已受理时释放自身 barrier、保存原请求原始返回并等待后台结束，不再抢着查询正在关闭的库或发第二次 stop。提前退出的变异体可保留原请求失败回执，但主测试的业务 failure 不会因此变成 PASS；清理/环境错误仍使父阶段 INCOMPLETE。

运行器只在完整业务 witness 上承认这个单点变异体被抓住：barrier 未释放、task 仍 creating、该请求结果不存在、daemon_stopped 已存在，1 test/1 failure/0 errors/skipped。不会把其他断言失败或 daemon_call_failed 当成目标业务红态。新捕获文件和最终归档同时保留；没有兜底重试。

重新生成该检查的命令仍为统一入口，新标签：

```sh
zsh evidence/2026-10-11-batch13/T-076/card-1/outside-sandbox.sh green-startup-shutdown outside-green-startup-shutdown-03
```

预期正例集合不变，顺序变异体应在 barrier 保持期间的“提前最终事件”断言失败，然后正常完成自身清理。Node/Python 语法与 diff-check 已做；完整行为验证需要主控在沙箱外执行，尚未取得新报告前不称有效。真实回合累计 0/3；真实两回合、候选五类变异体、8/9/18、独立审查和交付继续保持待完成。

## 主控 #16：专门绿态 PASS，交接 outside-real-03

核对 [outside-green-startup-shutdown-03/run.json](outside-green-startup-shutdown-03/run.json)：阶段 PASS、源码期间未变化、真实回合 0；主控核对无残留进程。initial-release 4/4、daemon-stop 4/4、identity 4/4，正例无 failures/errors/skipped。

顺序单点变异体退出 1，1 test、1 failure、0 errors/skipped，host_exit=0。失败落在 `test_startup_shutdown_e2e.py` 的提前最终事件业务断言：create 请求 `1190fd24-c6d7-4500-957b-2b86d57886fd` 的 barrier 仍保持，task=`T076startup-ef09d08e-second` 仍 creating，该请求没有 request_result，daemon_stopped 却已在 seq=11 持久化。证据为 `ordering-counterfactual/.../shutdown-precompletion.json` 及 barrier 期间独立读回；不是 daemon_call_failed 或清理错误。原 green-01/02 不上调。

真实阶段用新标签，执行主控运行：

```sh
zsh evidence/2026-10-11-batch13/T-076/card-1/outside-sandbox.sh real-two-turns outside-real-03
```

按主控 #16，本次执行时锁住 `real-turn-budget.jsonl`，确认旧两项预留都已由明确批准核账为实际 0，再追加本次预留 **2**。不是再次使用旧预留，也不自动重试；准备本身没有启动模型，实际累计仍 0。累计上限 3，第 3 个使用前仍须问主控。

准备保持：固定 Codex 0.162.1、gpt-6.1-sol/xhigh/Fast 请求与关闭更新检查；只复制 auth.json 的隔离 home，只信任夹具 repo，只有 git add/commit 两条规则；已批准 Git 与三个 Codex hook 仍仅经会话环境/argv。实际 argv 与环境、最近交付回合的原生上下文、Git 九个尾注、G/C/M 和原 attempt/稳定身份均读回保存。

首次派发只等可核对的前台领导者，不再循环等待首次输入才能产生的原生日志。验收 barrier 只在两个不同根回合均 task_complete、匹配 Stop 已空闲后释放，要求真实 run completed/reclaimed、回执后身份稳定。失败收尾保存活动快照，显式停止并等待自建进程退出，再从独立归档副本读取最终记录和回合计数；不抢读关闭的原 WAL 库，不释放未确认的 receipt barrier。确认退出后删整个隔离 home，凭据不进入归档。

这次只更新启动授权引用，不改变已通过绿态的产品行为或断言。真实阶段尚未运行，不提前宣称尾注/沙箱取值通过。真实结果核对之后，按主控 #16 顺序做候选五类变异体、8/9/18、fresh-context 只读审查，最后提交与 ticket Resolution（保持 open）。

## 主控 #17／决定 03：已用 1 回合，最后一次运行准备

原 [outside-real-03/run.json](outside-real-03/run.json) 保持 INCOMPLETE。worker 根回合启动并开始实现，但 run 的 100 秒期限先到；父探针 110 秒观察窗也随后结束。没有 worker 提交或 Stop，不能证明实际尾注或回执后 run/reclaim。主控核定隔离 home 已删除、无残留进程，实际累计 **1/3**。

按 [controller-decision-03.md](controller-decision-03.md)，预算追加 reserved=2、actual=1 的 reconciliation，引用该决定、原运行结果及最终事件，不改原 reservation/observation。计数现在保留已花掉的 1；最终预留 2 后计为 3。只接受三个明确输出各自对应的批准与实际数，禁止把本次 1 当 0 退款、重复核账或错引用。`outside-real-04` 是最后一次，之后即使失败也不再请求回合或自动重跑。

最后一次同时延长期限和缩小夹具：只实现一个 `src/normalize.py`、一次提交；按名字去空白并合并整数分钟、排序、空输入、Unicode 名字、bool/负数/非法名字拒绝。去掉 report.py 与 duration 格式要求，保留独立 oracle、真实 Git hook、显式 submit、回执和原 attempt 的 run/reclaim。run 与两个回合观察窗都改为 **900 秒**；回执只确认收到，不再执行实现任务。

准备时发现另一个确定性截断点：transport 的所有请求固定 120 秒。`test_transport_deadline.ts` 在无网络连接/计时器夹具上调用实际 request 函数，900 秒 run 先在期限业务断言失败（实际设置 120000 ms），普通命令和非法 wait 对照通过。修复仅让有效 run 参数的客户端期限覆盖其显式等待并加 120 秒收尾余量，仍有限且超时不重放；900 秒 run 读回 1020000 ms，三个用例转绿。没有放宽身份门槛，没有更改服务端完成条件的 60 秒命令期限；小夹具与只确认的回执减少该阶段工作。

本地证据在 `real-preparation-04/`：旧源与预算副本、transport-red-01/transport-green-01、冻结预算输入和 fixture-check-01。fixture-check 的独立 oracle 对基线 stub 退出 1、控制实现退出 0、把 bool 当整数的变异体退出 1；预算 5 项正反例通过，900 秒参数成立。没有启动 daemon/socket/Codex，没有额外消耗真实回合。

重放命令（输出须全新）：

```sh
node workbench/tests/test_transport_deadline.ts evidence/2026-10-11-batch13/T-076/card-1/real-preparation-04/transport.before.ts <全新红态目录>
node workbench/tests/test_transport_deadline.ts workbench/src/transport.ts <全新绿态目录>
python3 -B evidence/2026-10-11-batch13/T-076/card-1/real-preparation-04/check-final-fixture.py workbench/tests/run_t076_real.py evidence/2026-10-11-batch13/T-076/card-1/real-preparation-04/budget-after-17.jsonl <全新夹具检查目录>
```

执行主控最后一次真实运行：

```sh
zsh evidence/2026-10-11-batch13/T-076/card-1/outside-sandbox.sh real-two-turns outside-real-04
```

沿用仅复制 auth.json、受信夹具 repo、git add/commit 两条规则、已批准 per-session hook、固定 0.162.1/gpt-6.1-sol/xhigh/Fast 请求和关闭更新检查。实际 argv/环境与 Git/native 读回保存，收尾先显式停止、确认自建进程退出再读独立数据库归档并删除隔离 home。第三回合已由决定 03 限定在本次最多两个回合内批准，累计不得超过 3；不存在第 4 个额度。

若本次仍未到“提交 → submit → 回执 → run/reclaim”，尾注和真实多回合两项如实记 INCOMPLETE，不再要求模型回合；保留失败，向主控交代，再按其决定完成候选五变异体、8/9/18、独立审查与交付。本次尚未执行前，本卡仍 INCOMPLETE。

大证据检查发现 outside-real-03/commands.jsonl 超过 5 MB，原文件保留在本地供诊断，不直接提交；新增 commands.jsonl.gz 进入交付，大小记录在 real-preparation-04/large-evidence.json。重新生成原命令日志为该真实阶段的统一重放命令；解压时用 `gzip -dc .../commands.jsonl.gz > <全新命令日志路径>`。最终提交逐文件选择压缩版，避免把本地原始大输出加入 Git。

## 主控 #24：真实两回合 PASS，预算 3/3 封顶

核对 [outside-real-04/run.json](outside-real-04/run.json)、[候选消息](outside-real-04/candidate-message.txt)、[启动记录](outside-real-04/launch-record.json)、[Git 与原生上下文读回](outside-real-04/git-readback.json)、[回执边界](outside-real-04/receipt-boundary.json)、[回执后身份](outside-real-04/after-receipt-identity.json)。阶段 PASS，实际两个根回合，源码期间未变化；主控 #24 又独立读回 Git、尾注和回收结果。

| 事实 | 独立读回 |
| --- | --- |
| 任务 / attempt / 受管 session | T-076-9 / a0842017-9355-4e8a-bc6b-aa6b9b6628d1 / 8c628645-4e47-4668-bb56-09aae7757271；fence=1、spec_rev=1 |
| 启动 / 原生会话 | b1041c2a-795f-4aeb-9570-571308c4e50f / 01a12ba0-0467-7c00-8c86-e7871e8ae65c |
| C 的实际 Model / Effort | gpt-6.1-sol / xhigh；提交回合 turn_context、Git 尾注和启动请求相同。Fast 只有请求记录，不宣称供应商实际 tier |
| G / C / M | 935d03cad92452440a9a192ab1f095c3adc67384 / 3f7f0b41ce36b559027d9032473f04adf734d1ee / ecf9a7af49e0743e5f561b139eaab2fbdb44a39c；M 的父提交为 G、C，main=M |
| 交付回合 → 回执回合 | 01a12ba0-0523-7560-b2a4-bf29a44773a0 → 01a12ba1-ec40-79d1-85ab-1eb9198b8623；两者均 task_complete，匹配 Stop 确认 idle 后才释放验收 barrier |
| 稳定运行身份 | 同一 thread=ce4aa75e-65db-4d2e-9ab9-5d19808acdfe、shell=71715、leader=71717 和原生会话；辅助进程出现不替换领导者 |
| run / 回收 / 清理 | e3cfaaa1-d756-4731-8d68-bd0e960300e6，wait_seconds=900，outcome=completed、reclaimed=true；isolated_home_removed=true |

本次真实完整路径通过，不覆盖 outside-real-03 的失败与一个已消耗回合。`real-turn-budget.jsonl` 保留原预留、观测和批准核账：0 + 0 + 1 + 2 = **3**。本卡不再运行真实阶段，不要求第 4 个回合。旧真实命令仅用于描述已执行步骤；当前重放只解压保留的日志/源码/库，不能再启动模型。

`outside-real-03/commands.jsonl` 与 `outside-real-04/commands.jsonl` 分别为 24,284,131 和 34,855,460 字节。压缩版与原始字节完全相等，原始文件保存在 `/tmp/t076-large-evidence-cov__aip/`，详见 [large-evidence-02.json](large-evidence-02.json)。最终提交使用 `.gz`，移除主控运行中曾暂存的 real-04 原始日志路径；不会把大原始输出直接提交。解压重放：

```sh
gzip -dc evidence/2026-10-11-batch13/T-076/card-1/outside-real-04/commands.jsonl.gz > <全新日志路径>
```

## 候选后续验证交接

统一脚本已有独立入口，以下按顺序执行，各自使用全新标签；前一项未 PASS 就停下保留原结果。全部 `real_codex_turns=0`，没有隐式模型调用或重试。五个变异体分别从当前冻结候选副本生成，先过两个对照；8/9/18 必须经过 `workbench/tests/run_daemon_acceptance.py`。检查器反事实沿用完整交付库的独立副本，只改字段/删行，不改 events 或产品存储。

```sh
zsh evidence/2026-10-11-batch13/T-076/card-1/outside-sandbox.sh green-mutants outside-green-mutants-01
zsh evidence/2026-10-11-batch13/T-076/card-1/outside-sandbox.sh green-regression outside-green-regression-01
zsh evidence/2026-10-11-batch13/T-076/card-1/outside-sandbox.sh green-checker-counterfactuals outside-green-checker-counterfactuals-01
```

三个阶段的源码归档、tracked diff、实际加载路径和运行中源文件不变检查绑定各自候选。检查器反事实 PASS 只证明差异检出，不能把原完整库的 INCOMPLETE 或 attachment 的不一致改称一致。取得这三项原始结果后再做一次 fresh-context 只读审查，审查成本单列，不算被测真实 worker 回合；最终提交与 ticket Resolution 尚未进行。

## 主控 #25：候选变异体、检查器反事实 PASS；回归夹具修复

三个阶段均为 0 真实回合，源码期间未变化，原结果不覆盖。

### 五类候选变异体

[outside-green-mutants-01/run.json](outside-green-mutants-01/run.json) 汇总 PASS。control-offline 与 control-volume 均 exit 0；五个变异体各 exit 1，起点覆盖归属不变：前四项已有覆盖，第五项补明确缺盘业务测试。

| 变异体 | 候选上失败的业务断言 |
| --- | --- |
| omitted_bytes | `test_offline_trace_e2e.py:107`，CLI 已返回合法字节块，但 `actual == data` 失败；未启动 Electron，不扩大为实时 PTY 字节证明 |
| window_stops_daemon | 第 157 行关闭窗口后应仍可查询同一 daemon；关窗已完成，查询却返回 socket ENOENT。单点变异在窗口关闭时停后台，因此是生命周期业务失败，非初始环境启动失败 |
| unknown_is_idle | 第 98 行，pane_status 正常返回但 state 为 idle，不符合 unknown/interrupted/historical 的结构化断言 |
| restart_success | 第 126 行，实际 Electron 窗口将 claimed 任务投影为 accepted，违反 unknown/claimed 断言；没有把真实任务集成为成功 |
| missing_volume_builds | `test_build_volume_contract.py:38`，缺盘配置的标准构建入口仍 exit 0 并创建目录/产物，业务拒绝断言失败；classification=business-red，目录仍在外置盘专属槽 |

重现命令见上一节的 green-mutants 入口；必须新标签。每个子目录保留原 traceback、实际命令、变异源码、归档与清理结果。

### 检查器字段与缺行反事实

[outside-green-checker-counterfactuals-01/run.json](outside-green-checker-counterfactuals-01/run.json) 汇总 PASS。control 保持原完整库的 INCOMPLETE，任务/attempt/verification 重建一致，成员/预设仍无法重建。独立副本只改 tasks.fence=999、attempts.session_id=independent-foreign-session、verifications.M=全零提交号，以及删除一条 attempt；事件未改。检查器分别精确报告该字段或缺行“不一致”，五份原始报告保留。此 PASS 仅指反事实检出，没有更改原库结论或修存储。

### 首次回归 INCOMPLETE 与摘要打印错误

[outside-green-regression-01/run.json.gz](outside-green-regression-01/run.json.gz) 保持 INCOMPLETE。`coop/run.json.gz` 与 `test-result.json.gz` 均已保存 8 tests、0 failures/errors/skipped、status=PASS；最后摘要打印访问 `record['task']` 导致进程 exit 1，父协调器正确停止，recovery/run 未启动。不能把这个退出 1 计为业务红态，也不能宣称 8/9/18 全通过。

本卡先前移除了会虚构当前 task 的固定旧身份元数据，末尾打印字段漏改。这次只把该字段改为现有 `runner`，不加旧 task、异常吞噬或重试，不改产品和验收断言。修复前源保存在 `regression-report-repair-01/run_daemon_acceptance.py.before`。

只重放实际末尾打印语句，用已保存的 8/8 回执作输入：旧代码 [red.json](regression-report-repair-01/red.json) exit 1、KeyError('task')；候选 [green.json](regression-report-repair-01/green.json) exit 0，正常输出 runner 与原结果。这只是夹具摘要的局部验证，不代替全套重跑。重放命令：

```sh
gzip -dc evidence/2026-10-11-batch13/T-076/card-1/outside-green-regression-01/coop/run.json.gz > <全新回执.json>
python3 -B evidence/2026-10-11-batch13/T-076/card-1/regression-report-repair-01/replay-report.py evidence/2026-10-11-batch13/T-076/card-1/regression-report-repair-01/run_daemon_acceptance.py.before <解压的回执.json> <全新红态结果.json>
python3 -B evidence/2026-10-11-batch13/T-076/card-1/regression-report-repair-01/replay-report.py workbench/tests/run_daemon_acceptance.py <解压的回执.json> <全新绿态结果.json>
```

新标签交接，仅完整重跑 8/9/18，不重跑已通过变异体或启动模型：

```sh
zsh evidence/2026-10-11-batch13/T-076/card-1/outside-sandbox.sh green-regression outside-green-regression-02
```

取得 8/9/18 全过后再做一次 fresh-context 只读审查。真实预算仍 3/3，本卡整体保持 INCOMPLETE。

## 主控 #27：8/9/18 PASS，候选已冻结供独立审查

[regression-result-summary.json](regression-result-summary.json) 从 outside-green-regression-02 的原始逐套回执提取，未替换原回执或改写首次 INCOMPLETE：

| 套件 | 方法数 | failures / errors / skipped | 子进程退出 |
| --- | --- | --- | --- |
| coop | 8 | 0 / 0 / 0 | 0 |
| recovery | 9 | 0 / 0 / 0 | 0 |
| run | 18 | 0 / 0 / 0 | 0 |

每套仍经过 `workbench/tests/run_daemon_acceptance.py`、原 `acceptance/entry/a2a_gates.py` 和当前 `workbench/src/gates/cli.ts`；原业务方法集合未替换，源码期间未变化，真实回合 0。精确命令见原协调/逐套回执，统一重放入口仍为 green-regression 加全新标签。

原回归收据包含完整命令/事件，部分大于 5 MB；压缩清单见 `large-evidence-03.json`，解压字节逐块与原文核对相等。审查期间原文留在原路径，审查结束后迁移到自建 `/tmp` 保留，只提交压缩版和小摘要。不能因大小截断事件或删掉失败记录。

冻结候选：`/private/tmp/t076-review-nns44qwe/source`，基础 HEAD=`c77361d7e4f6ed918300c96127ed1a70b553b2a8`，含当前 110 个 src/hooks/tests/app/README/package 文件；[manifest](review-01/manifest.json)、[tracked patch](review-01/candidate.patch)、源码归档 `review-01/candidate-source.tar.gz` 同时保留。所有新增源码文件也在快照中，不只靠 tracked diff。

一次 fresh-context 子会话 `/root/t076_card1_review`，请求模型 gpt-6.1-sol、xhigh，只读，不继承实现聊天；按 `behavioral-acceptance-review` 检查合同、原始证据和新测试，结构风险并入同一次审查。没有启动被测 CLI，没有花第 4 个真实回合；审查会话成本独立于本卡 3 个被测回合，API 子会话未读回 CLI 版本或实际 tier，不冒称 Fast。审查期间不修改候选源码、测试或 README。审查结论尚未返回，不能预写 PASS 或完成 Resolution。

## 独立审查与交付

该次审查已返回 **STATUS: PASS**，报告原文在 [review-01/REVIEW.md](review-01/REVIEW.md)，会话记录和所用 skill 内容副本在同目录。未发现确认可达的本卡合同缺陷，未提出修复，所以没有审后修改产品或追加审查。审查确认源码与真实、变异体、检查器和回归归档相同；同时明确被测入口、受控反例、离线轨迹的证据边界，以及存储历史缺口和实际 tier 未观测的限制。没有把独立审查冒称为卡 2 的产品 reviewer 功能。

审查后逐文件核对暂存源码与冻结快照，31 个源码/测试/README 文件字节一致；源码提交 `42e2b8ed3caed775133eb3cafff5f4ee5ab68330` 的九个尾注完整，Task=T-076-1、Attempt=a1、Session=e671d062-fd65-448d-895f-5d160fba9a17、Role=worker、Tool=codex-cli 0.162.1、Model=gpt-6.1-sol、Effort=xhigh、Native-Session=01a12a7a-deaf-76a0-b977-9020931ead25、Launch=launch-f7b4aabbcb584729b8d22d073e0e7986。它是本 worker 的 a2a 源码提交，区别于真实夹具里的 C/M；两者均保留独立读回。

大回归收据已在审查结束后迁移到 `/private/tmp/t076-regression-raw-a9hvie8_/`，全部原始字节保留，迁移前再次逐块核对压缩版。清单与解压命令在 [large-evidence-04.json](large-evidence-04.json)。`find ... -size +5M` 最终仅列出 real-03/04 的已压缩 `.gz`；没有把超过 5 MB 的原始文件直接提交。每个阶段的统一再生成命令见对应小节；真实阶段因预算封顶只能解压保留证据，不能启动新模型。

最终源码、范围、尾注、地图与大小检查在 [delivery-check-01/final-checks.json](delivery-check-01/final-checks.json)、同目录 `delivery-code-readback.json` 和 `final-project-map-status.txt` 保存。交付探针首次错把 Git 符号链接的目标字符串当作解析后的文件内容比较，原异常在 `delivery-probe-error-01.json`；修正链接比较方式后 110 个文件及链接全部通过，没有产品或审查候选改动。本卡没有修改 acceptance 断言；源码提交及交付提交的 acceptance diff 均为空。共享分支相对实施起点的 T-079 acceptance 改动不属于本卡，已上报且未回退。ticket 只更新 Resolution，保留 open/ready_rev=1；全票后续质量串由 T-076-2 完成。

暂存后的全路径 `git diff --cached --check` exit 2，原输出保存在 `staged-diff-check-raw.txt`：两份原始统一差异输出包含格式必需的单空格上下文行。原始 patch/命令输出不裁剪、不改写；作者文件及源码提交的格式检查均 exit 0，具体命令、两项原始证据排除范围和原因在 `staged-format-check.json`。这项原始证据格式提示没有计为产品失败，也没有伪称全路径检查通过。

交付读回与地图检查的重新生成命令：

```sh
git log -1 --format='%H%n%B' 42e2b8ed3caed775133eb3cafff5f4ee5ab68330
git diff 42e2b8ed3caed775133eb3cafff5f4ee5ab68330^ 42e2b8ed3caed775133eb3cafff5f4ee5ab68330 -- acceptance/
python3 -B evidence/2026-10-11-batch13/T-076/card-1/delivery-check.py 42e2b8ed3caed775133eb3cafff5f4ee5ab68330 <全新交付检查目录>
python3 /Users/luckye/Documents/SKILLS/project-map-skill/project-map/scripts/project_map.py status --root .
find evidence/2026-10-11-batch13/T-076/card-1/ -type f -size +5M
```
