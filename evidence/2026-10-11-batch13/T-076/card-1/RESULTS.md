# T-076-1 执行记录（进行中，2026-10-11）

状态：**INCOMPLETE**。focused 红态与候选确定性绿态已核对；完整交付的一致性报告仍为 INCOMPLETE。执行主控 #9 接受成员/预设无法重建为如实报告，已交构思主控另切片，本卡不修存储；接下来先补 attachment 两个窗口，再按指定顺序继续。本记录不把起点覆盖、取证完成或语法检查称为本卡完成。

实施起点为 `18235b2c53610c412b5f4ea53e0e6e5c56d35849`；两次外部运行均从该 Git 对象导出冻结产品源码。其后共享 main 已前进，本卡未改其他 worker 的文件，后续候选会单独记录完整版本。授权为 `controller-decision-01.md` 与主控 #4、#6。真实 Codex 回合累计 **0/3**；计划用 2 个，第 3 个先问主控。

共享分支核对时 HEAD 为 `8ab5177d09dcb25f57a50ad2166dc0006ea99ce3`：相对本卡起点，T-079 已改变 `acceptance/test_herdr_traceability_e2e.py` 并新增 `test_launcher_shell_ready_e2e.py`，所以不能宣称整个 acceptance 目录的总 diff 为空。本卡没有编辑这些文件；门禁三套 `test_coop_e2e.py`、`test_recovery_e2e.py`、`test_run_e2e.py` 及产品 src/hooks 相对起点 diff 仍为空。该跨卡验收归属已单独上报，不回退他人的修改；最终报告按主控确定的比较范围如实列明。

## 六项完成条件

| 条件 | 当前状态与证据边界 |
| --- | --- |
| 真实受管提交的实际模型/强度 | INCOMPLETE；已有确定性 Git hook 红态，没有真实 Codex 提交 |
| 多回合 run/reclaim 正反例 | 确定性正反例 4/4 PASS，0 errors/skipped；真实回合尚未验证，整体 INCOMPLETE |
| 完整交付库的逐表一致性检查 | 已在完整交付库逐表报告；三张非空主视图一致、成员/预设无法重建；其余空表不冒称覆盖，attachment 专门取证待运行 |
| 五类变异体在业务断言失败 | 起点覆盖取证 PASS；最终候选重跑未做，故本卡条件仍 INCOMPLETE |
| 当前候选 8/9/18 与 acceptance diff | INCOMPLETE；三套尚未运行；本卡未修改 acceptance |
| project_map.py status | 当前检查 0 problems、0 stale；最终交付前还要重新检查 |

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
