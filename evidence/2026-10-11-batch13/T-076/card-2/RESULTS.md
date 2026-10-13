# T-076-2 运行记录

状态：**PASS（卡2交付，限隔离受管交付）**。真实worker修复→新只读reviewer→主控后填分→唯一集成/回收已完成并独立读回；超大日志已外置盘归档并字节核对。fresh-context只读独立交付审查为**PASS / LIMITED_GO**，实际累计**7/8**，槽8未使用。全库一致性仍为**INCOMPLETE**；T-076保持open，待主控关闭。本结论不表示正式工作台切换或生产可用。

- 任务：T-076-2，ticket `ready_rev: 1`，worker `s13-t076-2`。
- 续接执行器：主控 #76 后为`s13-t076-2r`，launch=`launch-f74f0d2636684448a884b551e0ba1ee2`，同原生会话；实际模型gpt-6.1-sol、xhigh，普通速度，无Fast。后续提交尾注绑定新launch。
- 再续接：2026-10-13主控 #82 后为`s13-t076-2s`，launch=`launch-632ff9488406442585d7e3ec1aa6fa35`，原生会话仍`01a12bbb-d44f-74e2-a218-b44fb0fa283b`，gpt-6.1-sol/xhigh/显式default，日志读回default；后续尾注用此launch。
- 开工HEAD：`a7f4cc3033c16d5888de50d8352da516c941f8e9`，主checkout的`main`。
- 计划：[PLAN.md](PLAN.md)。主控 #30 的计划停止点已履行；主控 #32 根据[决定01](controller-decision-01.md)批准P1–P5、W01–W06、F01–F04；#35批准第一条生产路径，#39批准加宽。
- 本卡真实Codex：**7/8**；P-review1回合、真实正例5回合及独立交付审查1回合均已取证。三组隔离CODEX_HOME均已删除，未使用槽8。
- 初始及主控后来产生的脏日志均保留。旧acceptance只按已批准白名单迁移，W07改了末尾集成断言，Recovery9逐字不变。产品/测试源码提交：`2bc3a1e96b1ecb687e8fae32ebbc5478fa58de88`；交付证据和Resolution随最终证据提交保存。
- 开始检查命令：`python3 /Users/luckye/Documents/SKILLS/project-map-skill/project-map/scripts/project_map.py status --root .`；输出Problems=0、Stale living docs=0。
- 规范差异：[ISSUE-spec-channel.md](ISSUE-spec-channel.md)，已上报`20261011T161950Z-worker:s13-t076-2-issue-001`；不修改spec。命令：`scripts/inbox send --from worker:s13-t076-2 --to triage --kind issue --title 'T-076-2：spec 第5节仍写方案A，当前worker已采用B通道' --body-file evidence/2026-10-11-batch13/T-076/card-2/ISSUE-spec-channel.md --ref ticket:T-076 --ref file:.project-map/specs/native-cli-orchestration-2026-10-10.md#L115 --ref file:.project-map/tickets/T-075-tracer-bullet-daemon-gate-pane.md#L55`。
- 收尾地图检查：**PASS**，0 problems、0 stale，确切命令与输出在[plan-status.json](plan-status.json)。文档按UTF-8无BOM回读；这只是文档/地图检查，不是产品验收。

以下按时间保留各阶段命令、输入、版本、原始失败与读回证据；历史INCOMPLETE及夹具错误不覆盖。当前交付结论和逐条验收对应见文末。

## 主控 #32：阶段1–3准备

本轮开始HEAD为`d3f2c2cf3b838d8f56e8a57629a19b9d282ea64f`，相对开工起点只增加主控/收件箱记录；产品代码与旧验收断言未变。另有主控正在写的batch13轮询日志/dispatch临时文件，保留，不纳入本卡文件。

新文件：`workbench/tests/test_quality_chain_e2e.py`、`quality_chain_host.ts`、`run_t076_quality_red.py`；证据目录的[outside-sandbox.sh](outside-sandbox.sh)、[assertion-hunks.md](assertion-hunks.md)、[HANDOFF-red-01.md](HANDOFF-red-01.md)。未改旧断言，未改`src/`、`hooks/`、`scripts/`、spec或地图。

- 阶段2预写11项起点红态，按明确ContractFailure编号核对，导入/usage/环境/协议异常不计红态。
- 阶段3预写8项既有保护对照与3个单点产品变异体；它们不是旧交付8项，也不是尚缺review/score/三次上限接口的替代证据。
- 只替换测试进程中的PTY和进程观察；真实CLI、后台、B relay、门禁、Git和SQLite执行待主控沙箱外运行。模拟版本字符串/原生记录不当作真实CLI/模型证据。
- 暂未取得第三次打回、有效reviewer身份/错C、独立评分/放弃/格式等反事实，阶段报告会显式列为deferred。P-review不在脚本的可选阶段里。
- 测试准备时通过静态阅读修正了两处夹具问题：脚本根目录上溯层数；成功`signal`的CLI输出为`{}`而非通用`{ok:true}`。尚未执行动态测试，没有把这些修正记为产品缺陷或业务红态。

静态检查：Python AST、Node TypeScript语法、zsh语法与根目录映射检查通过；确切命令、退出码见`preparation-checks.json`。阶段1–3尚未执行，因此业务结果仍为INCOMPLETE，真实Codex **0/8**。

执行命令（按顺序分阶段核对）：

```sh
zsh evidence/2026-10-11-batch13/T-076/card-2/outside-sandbox.sh stage-1 red-01
zsh evidence/2026-10-11-batch13/T-076/card-2/outside-sandbox.sh stage-2 red-01
zsh evidence/2026-10-11-batch13/T-076/card-2/outside-sandbox.sh stage-3 red-01
```

按主控 #32，交付脚本后停下，等待执行主控运行并回传红态；不自行申请提权或开始产品实现。

## 主控 #34：red-01读回与夹具修正

已逐项核对`outside-red-01/stage-2/baseline-contracts/run.json`：前9个用例均为对应预写ContractFailure，cleanup_failures均为空；第10项`red_run_reject_preserves_worker`为TypeError且assertions为空；第11项未运行。stage-2仍为INCOMPLETE，不能写成11项红态全得。

原attempt=`df2bd640-a213-463f-8018-7fe738d2389e`；run=`0b0a6719-9378-4b7a-ad90-b87bd334bbe2`。run收据为oracle_failed/verification_failed、reclaimed=true，任务ready/current_attempt=null；历史attempt保留为revoked/reclaimed=true。事件58–63依次记录验收失败、拒收、回收意图、撤销、回收和run结束；工作分支仍为B=`95cbd80f30b67da9ba9bfdc084f023ec8b3efd29`。这些与起点core.ts的既有回收路径一致，确认是夹具读取错误，不是新的产品协议异常。

修复范围仅`test_quality_chain_e2e.py`的三个相关绑定断言：显式把丢失/替换的current_attempt判为不满足合同；RED-RUN-REPAIR在判定前保存原attempt历史、当前task、run与Git读回。旧源码、诊断及diff保存在`harness-repair-01/`；red-01原目录/归档不动。

离线分类复放**PASS**：原保存读回在旧断言产生TypeError，新断言产生指定ContractFailure RED-RUN-REPAIR并保存读回。没有启动后台/socket/进程信号或模型；不是新的产品端到端运行。命令：

```sh
python3 -B evidence/2026-10-11-batch13/T-076/card-2/harness-repair-01/replay_assertion.py --before evidence/2026-10-11-batch13/T-076/card-2/harness-repair-01/test_quality_chain_e2e.py.before --after workbench/tests/test_quality_chain_e2e.py --recorded evidence/2026-10-11-batch13/T-076/card-2/outside-red-01/stage-2/baseline-contracts/red_run_reject_preserves_worker --output evidence/2026-10-11-batch13/T-076/card-2/harness-repair-01/offline-replay-01
```

再次执行复放时须换新的output目录，原结果在`harness-repair-01/offline-replay-01/run.json`。red-02三阶段命令见[HANDOFF-red-02](HANDOFF-red-02.md)，待执行主控运行；真实Codex仍0/8，不启动P-review、不实现产品。

## 主控 #35：red-02核对与第一条生产路径

已核对`outside-red-02/stage-{1,2,3}/run.json`及其中逐案记录：三个阶段status=PASS，product_status=INCOMPLETE，真实回合0、oversize_files为空；stage-2全部11项按预写编号契约失败，stage-3的8项对照全过、三个变异体分别命中预期断言。没有把外层“预期红态收集完成”写成产品PASS。

当前产品增加：明确打回授权的C2/新交付回合、gate登记/空闲回写/第三次暂停、fresh只读reviewer与B结论转交、结论候选/原生身份核对、单次集成评分与run等待执行主控。实际交付模型绑定当前root turn，缺上下文拒绝沿用旧值。状态继续用既有JSON和追加事件，未改存储结构。

新测试`test_quality_tracer_e2e.py`提供首拒修复闭环及10项受控场景；`run_t076_quality_green.py`先跑单条Tracer bullet，再跑其余场景/8项保护对照/旧评分格式校验，最后在候选副本运行9个明确坏行为的变异体。修改已有本卡测试驱动仅为复用其生命周期报告、独立reviewer home、不同交付轮次及与实际受控launch对应的尾注；没有改旧acceptance断言。

沙箱外交接与剩余项见[HANDOFF-focused-tracer-01](HANDOFF-focused-tracer-01.md)：

```sh
zsh evidence/2026-10-11-batch13/T-076/card-2/outside-sandbox.sh focused-tracer focused-tracer-01
```

本阶段尚未执行该命令。Python AST、Node语法及无副作用模块导入可做静态验证；它们不能代替质量串绿态。第一条贯通路径取得结果后再加宽红态/项目规则、放弃/升级和格式/恢复等项；8/9/18和T-077联验也未完成。P-review启动实例仍需逐次批准，不在此脚本里。

交接前静态检查 **PASS**：29项语法/模块导入/变异目标唯一性与语法检查，product_status仍INCOMPLETE；具体命令、输出和退出码见[focused-preparation-checks.json](focused-preparation-checks.json)。project-map为0 problems、0 stale，证据无>5 MB文件。`test_relay_core.ts`仅为其受控binding显式填写role=worker，配合内部角色必填契约，不保留未知角色默认worker的路径；原断言未改。

## 主控 #39：focused-tracer读回与加宽交接

`outside-focused-tracer-01/run.json`为PASS、product_status=INCOMPLETE、真实回合0、oversize_files为空。单条tracer、协议10项、既有边界8项全部通过；9个变异体均为预写ContractFailure。旧评分校验器的命令收据为第8条：exit=0、stdout精确为`schema-1 payload accepted\n`、stderr为空；对应原始字节在`command-output/00008.{stdout,stderr}.bin`。读回不改变旧产物，重现首轮命令见上一节，需新label。

本轮产品实现了声明测试路径的B/C检查、注册时项目规则快照及M上执行、放弃/升级与一次终结评分、只读`scores_validate`。评分恢复继续沿integration intent，在CAS成功后的门禁事务写最终分；新测试将在CAS前后实际中断并核对恢复行为。Deep modules仍按门禁持有事实与状态、Panes持有运行时、relay持有显式传递划分；未改存储结构或增加另一评分入口。Ubiquitous language沿用task、attempt、verification、review、score，不另设业务别名。

新文件`test_quality_widen_e2e.py`含15项加宽合同与3项reviewer异常探针；`run_t076_quality_widen.py`冻结并执行，包含13个单点变异体。现有本卡夹具增加可读回的后台重启及显式PTY故障输入，不替换门禁方法、结果或数据库状态。每个新阶段的来源/命令/进程/事件/Git/归档分别保存。`review-red`使用上轮通过的产品归档，而非已改动的checkout；本轮尚未实现这三类异常的修复。

按新接口的批准方式补反事实，不把新增CLI入口在起点不存在的usage错误充作红态。完整8/9/18及T-075/T-076-1回归须在加宽与reviewer处理后继续，当前旧acceptance与`scripts/` diff为空，W01–W06/F01–F04的旧夹具迁移未做。

T-077衔接的静态疑点已按角色卡非阻塞上报，见[ISSUE-t077-native-home.md](ISSUE-t077-native-home.md)，收件箱ID `20261011T180613Z-worker:s13-t076-2-issue-001`：新attempt释放worker名额时须重新核对隔离home/原生记录归属。本卡恢复并保留S1的`single_worker_slice`约束，避免提前扩大为多worker；没有实测或修改T-077分支。

本轮沙箱外命令与边界见[HANDOFF-widen-01](HANDOFF-widen-01.md)。静态检查收据在[widen-preparation-checks.json](widen-preparation-checks.json)，生成命令为：

```sh
python3 -B evidence/2026-10-11-batch13/T-076/card-2/check-widen-preparation.py --output evidence/2026-10-11-batch13/T-076/card-2/widen-preparation-checks.json
```

只检查语法、无实例模块导入、变异文本唯一性/语法、旧收据与文档编码；不能替代新动态绿态。真实回合仍0/8，P-review实例未提出启动。按主控停止点交回两项沙箱外阶段，等待结果。

## 主控 #48：加宽结果读回与reviewer修复

两个阶段原始`run.json`逐案核对完成：reviewer-red为三项指定ContractFailure、无harness_error/清理失败；wide-green为15项候选PASS、13个变异体全部命中预写编号，无超大文件。三项红态的具体旧行为为：创建抛错后task仍reviewing/review仍requested；重启后仍reviewing/running；退出未确认后仍verified/passed且只有reclaim intent。它们证明新增的未知暂停合同尚未落实，不是环境错误。汇总与精确路径见`review-repair-01/readback.json`。

修复在门禁保存`review_lifecycle_failed`和执行主控issue：创建/回收失败保留原错误并抛回；daemon启动后只将未完成旧审查标未知，不采用其PTY、不自动新开reviewer。当前审查故障暂停当前task，历史审查不覆盖新attempt/终结结果；成功回收记录使已完成review免于重启暂停。状态一致性诊断认识新增完整task快照事件，未改表结构。三份源码相对wide-green冻结候选的diff及完整前后文件位于`review-repair-01/`。

完整回归迁移在静态接口核对时遇到PLAN F01明列的决定点：真实手工claim没有thread/launch，也不会由submit保存delivery，合法review及score不足以满足最终评分来源要求。已上报`20261011T184331Z-worker:s13-t076-2-issue-001`，详见[ISSUE-legacy-claim-provenance](ISSUE-legacy-claim-provenance.md)。没有虚构launch、写数据库passed/delivery、放宽门禁或偷偷把claim换dispatch；旧acceptance与适配器均未改。此迁移子项为BLOCKED，独立reviewer修复已继续完成到可验证候选。

为节省回合与重复运行，把原3项异常、3条受影响正常路径、2项评分恢复合成`review-green`一个阶段，共8项，无新增模型调用。脚本与确切命令见[HANDOFF-review-green-01](HANDOFF-review-green-01.md)，静态收据为`reviewer-preparation-checks.json`。新阶段尚未运行，不写绿态PASS；真实仍0/8。

## 主控 #50：reviewer绿态读回与F05清单

`outside-reviewer-green-01/run.json`已逐案核对：reviewer-fault-green 3/3、reviewer-normal-paths 3/3、completed-review-score-recovery 2/2，均exit0/业务passed、cleanup_failures为空、无超大文件；product_status仍INCOMPLETE，真实0/8。修复diff已获主控认可，不重复运行这8项。

[决定02](controller-decision-02.md)确认手工claim没有受管来源时拒绝集成符合合同，批准需要集成的夹具向受控dispatch迁移，但准确清单须先批准。[F05-migration-list.md](F05-migration-list.md)列出F05–F12的文件、helper、全部受影响method、保留的手工入口、来源反例/变异体和单阶段回归安排。

清单F12另标一处不能静默迁移的旧断言冲突：冻结候选方法要求手工claim最终集成成功。建议补充W07，仅将其末尾改为合法review/评分齐备仍拒绝无来源，并在单列受管场景完整保留原冻结与最终集成C的证据；待主控明确决定，不自行改断言。Recovery9拟只改adapter准备选择，业务源码逐字不动。

本轮HEAD为`07c596fe6561ccd7b3f0c3cc5bc3bf94490a3230`；相对上一轮HEAD的workbench/acceptance已提交diff为空。旧断言/适配器仍未改；本轮仅本卡文档与只读结果核对，未新增沙箱外执行、未启动真实CLI。核对命令与文档检查收据保存为`migration-list-checks.json`，不作产品验收。按清单审批停止点等待。

## 主控 #52：批准迁移实施，F13漏项上报

已按[决定03](controller-decision-03.md)落实F05–F11/W07。`legacy-acceptance-hunks.diff`是两份acceptance文件的准确变更；Recovery文件仍逐字不变。W07明确修改了末尾旧成功断言，不称“全部原断言未改”；冻结候选保护前缀保持逐字一致，受管集成证据在新增场景中完整重放，尚未运行。

真实门禁不变。受控worker的创建事实在外部fixture账本持久记录；reviewer继续通过真实Panes/独立home/B/relay。新driver的固定评分和明确review输入均经CLI，记录逐attempt的手工claim或受控dispatch。未向生产库预填launch/delivery/passed，也未加产品test mode。

`legacy-green`已写为单阶段，F10/W07的已知坏来源变异体先于候选绿态，之后按8/9/18、T-075/T-076-1顺序运行。新断言当前仍是待取证，不将语法通过写成业务红态或绿态。

实施时静态核对发现漏项：`test_non_fast_forward_git_result_cannot_integrate`仍是手工claim，缺来源会早于原Git fast-forward保护拒绝；决定03/F08只准六个准备调用点，不能自行加入第七个。已上报`20261011T185808Z-worker:s13-t076-2-issue-001`，详见[ISSUE-non-fast-forward-fixture](ISSUE-non-fast-forward-fixture.md)。申请只改该方法一行到`create_managed()`，原全部Git反例断言不变。清单漏项是本worker的疏漏，不是产品缺陷。

其余获准迁移已推进，F13方法未改；runner在任何后台启动前拒绝未完成的F13准备，避免耗用沙箱外轮次跑一个已知错误前置。[HANDOFF-legacy-preparation-01](HANDOFF-legacy-preparation-01.md)列具体文件、阶段和命令；静态收据`legacy-preparation-checks.json`不表示完整阶段可运行。真实仍0/8，未调用模型、未运行沙箱外步骤。当前停止等F13决定。

## 主控 #56：F13落实，合并阶段READY

已读回决定03末尾的F13批准。`test_non_fast_forward_git_result_cannot_integrate`仅将准备调用改为`create_managed()`；没有修改其原Git反例断言。范围审计和静态检查按完整方法逐字核对这一限制。旧F13待批记录保留不覆盖。

`legacy-green`移除已不适用的待批阻断，统一调用范围审计；原8/9/18和任务卡runner遇首次失败停止，不改变套件成员或成功标准。其余顺序仍为新来源红态先行，再候选与完整回归。新产物尚未运行，不称红态或绿态已取得。

本轮HEAD为`16c8d9410df3ceaeaea9eaac794b89bfc0dd7f2b`；相对上一轮的已提交workbench/acceptance变化为空。本轮无产品逻辑改动、无真实CLI调用；真实0/8。沙箱外命令见[HANDOFF-legacy-green-01](HANDOFF-legacy-green-01.md)，新静态收据为`legacy-ready-checks-01.json`。按主控停止点交回，由主控运行；原始失败须保留。

## 主控 #57：legacy-green-01分类与F14待批

原目录保留。F10的MANUAL-CLAIM-PRECONDITIONS通过，MANUAL-CLAIM-SOURCE命中来源变异体；W07在verify更早失败，不能计入预写W07红态。旧`ManagedDeliveryCLI.create()`卡model为fixture，reviewer的真实Panes启动参数检查拒绝它。精确读回见[legacy-diagnosis-01.json](legacy-diagnosis-01.json)及[F14-fixture-executor.md](F14-fixture-executor.md)。

这次不是reviewer未知暂停遗漏：机械verification=passed、task=paused、review=unknown；event93记录create阶段的review_lifecycle_failed，event94保存blocking issue且issue表存在同条，event95保留verify失败。已通过的REVIEW-CREATE-PAUSE明确要求命令失败与paused/unknown/issue同时存在；返回gate_failure不与该合同冲突。没有改产品或创建额外产品修复红态。

F14请求只改`acceptance/test_coop_e2e.py:148`、`ManagedDeliveryCLI.create()`的model字符串为gpt-6.1-sol，其他卡字段/断言不变；尚未实施。此卡片helper由8/9/18共用，受控运行事实继续明确标为fixture。获批后重新冻结交接diff，换legacy-green-02，不能覆盖01。

主控报告顶层退出0，本目录无该shell退出原始收据；两个子步骤记录均退出1，总报告INCOMPLETE。保存这个尚不能独立核对的差异，不推断包装命令行为或据此改runner。后续判断仍以完整阶段报告及子步骤为准。

诊断脚本只读已保存JSON，不启动后台、socket或模型；其命令在F14文档中。真实回合仍0/8；本轮停止等F14批准，不宣称新的OUTSIDE-SANDBOX READY。

## 主控 #59：F14落实，交legacy-green-02

已核对决定03的F14补充。`ManagedDeliveryCLI.create()`只把executor.model由fixture改为gpt-6.1-sol；审计增加该helper的完整正文比较，只准这一字符串变化，不改断言或Panes约束。旧hunk保存为`legacy-acceptance-hunks.pre-F14.diff`，当前hunk加入唯一的F14卡值变化。

主控确认先前“runner exit 0”来自`tail`，不是runner返回。该疑点已澄清；01仍为INCOMPLETE，不修改其原报告/命令/诊断。新label为legacy-green-02，重新冻结后沿同一红态先行的完整阶段执行。确切命令见[HANDOFF-legacy-green-02](HANDOFF-legacy-green-02.md)，静态收据为`legacy-ready-checks-02.json`。

本轮HEAD为`915f390d2b0a4308a28b177351f3329e96e6949e`。未触及主控日志或新增的records/launches.jsonl脏改动；无新产品改动、无后台/模型调用，真实仍0/8。新阶段尚未运行，按READY停止点交回。

## 主控 #60：F09路径夹具修复，交legacy-green-03

02原目录保留。读回launch、归档config和事件后确认：shell=/bin/zsh，8个reviewer home已登记；错误仅为config用/tmp，产品传入解析后的/private/tmp。文件级同目录核对为真，严格字符串包含为假；失败发生在写原生session/pane_started之前。

修复只改测试配置生成器，使root先resolve(strict=True)再创建所有路径；PTY夹具原严格home/shell条件不变，只补拒绝时原值/登记值的诊断。没有修改Panes、门禁或业务断言。相关原文件与diff保存在`fixture-path-repair-01/`。

按要求一并核对W07前置：独立home、session文件归属与根CLI标记、turn_context、三条hook argv的Node/CLI/state/launch、B请求文件realpath/0600/完整JSON/重放，以及Stop调用的身份链。离线probe旧配置复现拒绝，新配置接受，陌生home与错误shell仍拒绝；详情和局限见[README](fixture-path-repair-01/README.md)。没有后台、socket、ps、真实信号或模型调用，真实0/8。

probe的offline-01因读取shell_argv索引2（-c）而非3（program）失败；该探针错误及脚本原样保留，修正后offline-02通过。它不是产品协议失败，不替代W07业务红/绿态。

新阶段命令见[HANDOFF-legacy-green-03](HANDOFF-legacy-green-03.md)。静态收据为`legacy-ready-checks-03.json`；产品仍INCOMPLETE，不把文件级probe当作新端到端验收。交回READY，等待主控沙箱外运行。

## 主控 #62：W07红态确认，managed_frozen输入顺序修复

已读回03：W07为1 failure/0 errors，实际命中W07-MANUAL-SOURCE；Git由20d8f7a6d423fa497df113b12e2bf267b2ac332a变为1a30b26fc5470ebefabffd5607cc942fdbdec6ac。F10同样命中预写来源反事实；候选手工claim来源拒绝通过。managed_frozen仅dirty断言通过，后续未执行，不能报告该场景或回归通过。

managed_frozen的事件56已经将ACK T2置idle，之后没有pane_dispatch/新turn。fixture写四个新请求并重发T2 Stop；事件69–73拒绝requires_current_stop，74记录stop_not_matched。只有dirty有持久relay结果，task仍claimed/C为空/交付turn为空。这是夹具把“idle”误当作“新工作回合”的输入顺序错误，不是产品漏推进。

仅新增测试helper `LegacyQuality.begin_worker_turn()`及两处调用，经真实pane_dispatch启动T3/T5，再核对busy/nativeTurn、原attempt/原生身份及repair=null。未改产品、通用worker_submit或任何旧业务断言。完整流程静态表核对了T1 dirty→T2 ACK→T3 clean批次→T4 ACK→T5 C2反例→T6 ACK→reviewer自身T1→集成/reclaim，总合成输入7、既有上限10；评分拒绝计数预期仍为4。

03原目录不动。证据分类脚本、源文件before与精确diff见[managed-flow-repair-01](managed-flow-repair-01/README.md)；该脚本只读保存证据，不是新业务运行。新命令见[HANDOFF-legacy-green-04](HANDOFF-legacy-green-04.md)，静态收据`legacy-ready-checks-04.json`。真实仍0/8，交回READY后停止等主控执行。

## 主控 #65：Recovery cleanup重复后续动作修复

04读回：provenance-and-frozen-green两项通过，coop为8 tests/0 failures/0 errors/0 skipped；Recovery为2 tests/0 failures/1 error，后续未运行。第二项已生成一次review_result/reclaimed（事件70/72），再integrated/score_recorded（113/114），最终accepted。error发生于cleanup重读setup的旧verify响应，adapter把历史reviewing又当成需驱动的新审查，不是产品未完成。

F06/F09内修复`DaemonLifecycle.complete()`：同一个verify handle在首次后续动作前保存明确绑定/started，成功后记completed；重复读取只记fixture收据重放并返回原CLI响应；绑定变化或前次未完成则拒绝，不再驱动。首次及同步verify后续动作显式传原attempt/C，避免接管另一个执行者。无产品或Recovery源码修改。

已静态走查全部9项setup、故障恢复和cleanup路径，表格及原文件before/diff见[recovery-cleanup-repair-01](recovery-cleanup-repair-01/README.md)。离线复放用保存的verify/verified/accepted三类快照，旧方法重现相同错误，新方法仅驱动一次且保留原响应；变更C/attempt/review、incomplete动作及忙锁拒绝对照有效。这不是新Recovery端到端PASS。

新的单阶段命令见[HANDOFF-legacy-green-05](HANDOFF-legacy-green-05.md)，静态收据`legacy-ready-checks-05.json`。04原目录不动，真实仍0/8。按READY停止点交回。

## 主控 #69：run异步review就绪窗口

05读回：coop8/recovery9均0 failures/errors/skipped；run执行1项、0 failures/1 error。事件71在20:56:08.972Z登记requested，76在20:56:09.447Z登记同review running，间隔475毫秒；窗格与派发也已建立。因此没有产品创建被锁住的证据，是driver提前退出状态等待。

仅修`QualityDriver.finalize_run()`：原12秒期限内固定attempt/C/review，只有running且launch/runtime_identity存在才推进；requested继续等，失败/unknown/换绑定/超时即拒绝。状态查询的timeout限制为剩余时间，新增调用意图记录，超时不重试。不改产品、任何业务断言或原run等待期限。

静态核对主正例、helper-joins委托、duplicate run、matching reclaim、fixture_existing_dispatch及MultiTurn；同步verify路径已await创建结束，无需改成另一个轮询流程。表格、原文件before及diff见[run-review-wait-repair-01](run-review-wait-repair-01/README.md)。保存快照加虚拟时钟的离线复放通过，并覆盖unknown/失败/替换/超时，但不称产品绿态。

05原目录不动，真实仍0/8。新命令见[HANDOFF-legacy-green-06](HANDOFF-legacy-green-06.md)，静态收据`legacy-ready-checks-06.json`。按READY停止点交回，完整后续仍INCOMPLETE。

## 主控 #71：legacy-green-06读回与P-review槽1审批

已核对原运行的22份子报告（含压缩报告），实际退出码逐项等于expected_exit。F10的MANUAL-CLAIM-SOURCE、W07的W07-MANUAL-SOURCE均命中，W07读回的ref确实不等于B；候选手工claim来源拒绝和受管冻结候选完整流程通过。coop8/recovery9/run18均0 failures/errors/skipped；任务卡15、多回合4、首次放行4、后台停止4、relay/hook及离线/外置盘对照通过。停止顺序和五类变异体均在原预写业务边界失败。源码未在运行中变化，没有>5MB文件；没有重跑动态套件。

一致性报告原样保留INCOMPLETE：tasks/attempts/verifications一致；空表不代表覆盖，memberships/session_presets仍无法由现有事件重建，unknown_events为空。没有改存储或把整票写成PASS。

[P-REVIEW-APPROVAL-01.md](P-REVIEW-APPROVAL-01.md)列出槽1完整argv政策、唯一两个产品UUID替换、独立home、三个hook、sentinel写入反例、1回合预算与清理。`run_p_review.py`走真实后台/Panes/PTY；`p_review_host.ts`只在spawn前核对argv，原生身份、模型输出与结论均不伪造。槽1手工准备固定候选，不运行worker或集成；槽2–6未开放。

审批包冻结于HEAD `89691762d201d8c484baa247060accd60f49881b`，含118个源码/测试/依赖清单文件；48个产品源码/hook文件与legacy-green-06逐字一致。这个HEAD只是仓库版本，未提交的本卡实际被测字节以快照为准。Fast只记录requested，实际tier待原始记录核对。

准备脚本第一次把hook符号链接原样打包，违反了本探针的“仅普通文件”快照要求；这是打包夹具错误，未运行产品。保留[p-review-preparation-checks-01.json](p-review-preparation-checks-01.json)和`p-review-draft-symlinks.tar.gz`；仅改tar打包为dereference后，02静态检查PASS，03复核PASS，未改产品。记录含legacy06完整读回摘要、Python AST/Node/zsh语法、argv与hook完整值、冻结字节比较、UTF-8与地图检查。一次通过stdin追加中文文档的临时命令在解析阶段报Non-UTF-8错误，尚未写文件；随后改用apply_patch，未影响快照或测试结论。

再生成审批包与静态报告（仅在未批准/未启动时；output须为新路径）：

```sh
python3 -B evidence/2026-10-11-batch13/T-076/card-2/prepare-p-review-approval.py --freeze-bundle --output evidence/2026-10-11-batch13/T-076/card-2/p-review-preparation-checks-02.json
```

只复核现有快照时去掉`--freeze-bundle`，并换新output。此命令不启动Codex/后台、不复制auth、不创建真实夹具；真实**0/8**。当前APPROVED.json不存在，按主控 #71 停在逐实例审批点；后续真实执行入口及所有停止条件见审批材料。

## 主控 #76：普通速度与审批材料02

用户决定由主控逐字转述：“全继续，不用 fast了，用 6.1sol 普通速度”，引用构思主控answer `20261012T015257Z-ideation-answer-001`。暂停已解除，按指定范围继续准备；真实预算仍0/8，周额度用尽即停，不切账号或模型。

Panes删去worker/reviewer共用argv里的Fast配置，启动记录service_tier_requested及dispatch_intent的requested_service_tier均写default；没有增加开关或改其他沙箱、hook、模型/effort和身份检查。同步修改两份真实探针报告/期望；历史格式夹具中的fast数据继续作为旧记录输入，不改旧证据。精确本轮产品diff与修改前文件在`launch-policy-change-01/`。

新的两项受控用例核对实际worker/reviewer启动argv及default记录；worker还核对dispatch记录。单阶段`run_t076_launch_policy.py`先在01的旧产品快照上取得两个指定无Fast红态，再跑两个候选绿态，最后复验TRACER-READONLY-ARGV变异体。不重跑8/9/18或其他宽套件；没有真实模型、自动重试或预填业务状态。本轮仅准备，动态结果待执行主控取证。

```sh
zsh evidence/2026-10-11-batch13/T-076/card-2/outside-sandbox.sh launch-policy launch-policy-01
```

[P-REVIEW-APPROVAL-02.md](P-REVIEW-APPROVAL-02.md)为新的完整实例审批；原01及快照/收据均保留，不续用。02根目录为`/private/tmp/a2a-t076-p-review-02`，唯一信任Git根、独立home、三个hook、完整B结论、sentinel反例和1回合预算沿原合同，argv无service_tier覆盖。未写APPROVED.json、未复制auth、未启动真实后台/reviewer。

审批包与静态报告再生成命令（仅未批准/未启动时，output须新路径）：

```sh
python3 -B evidence/2026-10-11-batch13/T-076/card-2/prepare-p-review-approval.py --freeze-bundle --output evidence/2026-10-11-batch13/T-076/card-2/launch-policy-preparation-01.json
```

[launch-policy-preparation-01.json](launch-policy-preparation-01.json)为静态PASS：冻结HEAD `a502355a7f2715c3024e9bdb0bb57a131c73efa8`，119文件，46个产品文件逐字匹配legacy-green-06，另2个仅含批准的tier替换；无超大文件，地图0问题/0 stale。它只作语法、argv/hook政策、冻结字节、编码/地图和旧结果读回检查，不能替代本轮动态红绿。主控审02并写批准文件后，真实执行命令为`zsh evidence/2026-10-11-batch13/T-076/card-2/outside-sandbox.sh p-review p-review-02`；按 #76 的READY停止点交回。

## 主控 #80：真实P-review读回与槽2–6审批

outside-launch-policy-01已读回：worker/reviewer旧快照分别命中TRACER-WORKER-NOFAST-ARGV、TRACER-REVIEWER-NOFAST-ARGV，候选两项通过，只读变异体命中TRACER-READONLY-ARGV；清理失败为空、无源码变化/超大文件。

P-review02读回PASS：原生会话`01a12dde-45f9-7c70-b511-2781da612a21`仅一个完整主turn `01a12dde-4667-7cc0-b79e-fa02ad704367`，模型gpt-6.1-sol、xhigh、read-only、never。唯一sentinel写入EPERM/errno1、write_attempts1，归档中的审查/项目sentinel字节均未变；独立主机对照确实写入成功。Git工作区干净，项目ref保持B=`5b9c240d7677b57ce9be60c95d867dfef70100da`。review passed/可合并/findings空、C=`d22b6ebb7f2660cd9649b196d47a77ae1193ffe8`，结论经匹配Stop/B/relay落库并回收。reviewer home已删除，无>5MB文件；不据请求参数宣称供应商实际tier。

读回收据为[p-review-readback-01.json](p-review-readback-01.json)，预算账已有reservation=1/observation=1，追加readback审计不重复计费，累计**1/8**。再生成读回收据须换新output；命令：

```sh
python3 -B evidence/2026-10-11-batch13/T-076/card-2/readback-p-review-02.py --output evidence/2026-10-11-batch13/T-076/card-2/p-review-readback-01.json
```

[REAL-DELIVERY-APPROVAL-01.md](REAL-DELIVERY-APPROVAL-01.md)提供槽2–6完整两份argv、独立home、三个hook、Git规则及尾注hook、外部oracle/G提交、原生与ACK核对、评分待办、停止和清理。新runner走真实生产路径，host仅audit实际spawn；不伪造身份/结论。按既有global turn_limit语义配置5，最终独立要求worker4/reviewer1；不宣称按窗格限4。审查可合并后主控读ready-for-score再提供executor-score.json，不预填分；未给分即停止、不集成。

静态准备也保留oracle的已知坏基线、C1 bool红态及11项正确控制版本，不当成真实产品红绿。新runner静态走查补上项目规则必填id，并明确原生验收失败也继续删除已确认退出的home；这是尚未运行夹具的准备修正，没有改产品或任何旧业务断言。快照与静态检查再生成命令（新output目录；未批准/未启动时才可冻结）：

```sh
python3 -B evidence/2026-10-11-batch13/T-076/card-2/prepare-real-delivery.py --output evidence/2026-10-11-batch13/T-076/card-2/real-delivery-preparation-01
```

当前仅准备，无新reservation、APPROVED.json、auth副本或真实根目录。完整真实正例及卡片状态仍INCOMPLETE；按 #80 逐实例审批点停下，待主控运行。批准后的命令见审批材料，槽7/8没有授权。

最终静态收据为[real-delivery-preparation-04/run.json](real-delivery-preparation-04/run.json)，PASS：121个冻结文件，48个产品源码/hook与P-review02逐字一致；语法、完整argv/规则、oracle基线/C1红态和11项正确控制、编码/地图检查通过，actual1、新reservation0、无超大文件。01–03各检查与对应早期快照原样保留。准备期间收紧了最终原生完整回合/错误读回，移除了reviewers项中未声明的turn_limit覆盖（两个启动记录都用全局5），并在复制auth前检查夹具没有继承未批准的core.hooksPath；未执行新产品协议。一处无效的文档补丁因上下文匹配失败而未写文件，之后用准确位置追加本记录。

再生成最终静态包用上述prepare-real-delivery.py命令，将output换成`real-delivery-preparation-04`或其他未用目录；批准后不得重新冻结。真实预算账1/8的事实不因重复静态检查改变。

## 主控 #82：恢复、显式default与真实审批02

依据answer `20261013T142903Z-ideation-answer-001`，主控的无模型探针证明default覆盖能压过用户全局priority，用户决定所有会话都显式覆盖；证据见[2026-10-13-tier-probe](../../../2026-10-13-tier-probe/README.md)。不读写该全局配置、不重跑主控探针。恢复时读回ticket ready_rev=1、地图0问题/0 stale；产品48文件与旧real-delivery01快照全部一致，预算reservation/observation仍仅P-review的1回合，原01未启动。

产品仅改Panes共用argv一处，添加`-c service_tier="default"`；tier记录仍default，其余参数/身份检查不变。修改前源码、测试、runner和本轮准确product.diff在`default-tier-change-01/`。旧01材料、快照和所有失败/检查收据原样保留并视为过期，真实正例重建为[REAL-DELIVERY-APPROVAL-02.md](REAL-DELIVERY-APPROVAL-02.md)，根目录`/private/tmp/a2a-t076-real-delivery-02`。

启动参数测试改为严格要求唯一default配置值及其前一个参数-c；不能凭record里的default冒称实际argv正确。单阶段先让旧01的worker/reviewer分别在DEFAULT-ARGV断言失败，再跑候选两项通过，最后priority值变异体和原只读变异体命中预写编号。均真实后台/CLI加受控PTY，真实模型0；动态红绿待主控沙箱外运行，不先写PASS，不重跑8/9/18或未变的oracle。

```sh
zsh evidence/2026-10-11-batch13/T-076/card-2/outside-sandbox.sh launch-policy launch-policy-default-01
```

新静态收据为[real-delivery-02-preparation-01/run.json](real-delivery-02-preparation-01/run.json)，PASS：121个文件，47个产品源码/hook逐字匹配旧01，Panes仅含批准的两个argv参数；模型/沙箱/default政策、语法、UTF-8、地图检查通过。oracle字节未变，沿用原04控制结果，不重复执行。再生成命令（新output；只在未批准/未启动时）：

```sh
python3 -B evidence/2026-10-11-batch13/T-076/card-2/prepare-real-delivery.py --output evidence/2026-10-11-batch13/T-076/card-2/real-delivery-02-preparation-01
```

重新核对原01和新02实例根都不存在，02没有APPROVED.json，未复制auth或新增reservation，实际仍**1/8**。清理范围仍仅本实例daemon/PID、两个隔离home、repo/state/B目录；普通速度之外未改预算、评分待办或停止条件。按 #82 READY点交回，待最小阶段结果与新实例批准。批准后实际命令为`zsh evidence/2026-10-11-batch13/T-076/card-2/outside-sandbox.sh real-delivery real-delivery-02`。

## 主控 #86/#90：真实闭环读回、归档与独立审查准备

真实闭环读回PASS：B=`29d45fbd`、独立G=`5ce713f5`、C1=`709a85ba`、C2=`e08f87cf`、M=`b24ec63e`；M父提交顺序精确为G、C2，当前main=M且工作区干净。C1在bool-true完成条件首拒，只有一条completion delivery_rejected和一条登记的quality-repair；原attempt及leader保持，提交绑定worker第1/3回合。worker实际4个完整回合，reviewer1个完整回合，两个source=cli会话不同，ACK1/2零工具调用。两个候选的9项尾注均与同一次worker身份和实际gpt-6.1-sol/xhigh一致，worker workspace-write、reviewer read-only、never，argv唯一显式default。

review passed/可合并/findings空，绑定C2。缺分返回score_required；主控在ready-for-score边界之后写3/3分，唯一integrate与唯一score_recorded，delivery_rounds=2、human_interventions=0、七类拒绝计数仅completion=1。自建模型进程已退出、两个完整CODEX_HOME删除，无trace/native/cleanup错误。sentinel只属P-review，不将它混入本正例。

直接Git/原生/事件读回收据：[real-delivery-readback-01](real-delivery-readback-01/run.json)、归档后[readback-02](real-delivery-readback-02/run.json)。再生成须新output：

```sh
python3 -B evidence/2026-10-11-batch13/T-076/card-2/readback-real-delivery-02.py --output evidence/2026-10-11-batch13/T-076/card-2/real-delivery-readback-02
```

原run.json保留INCOMPLETE/archive_required，因为compressed commands.jsonl.gz仍48,122,290字节。主控 #90 执行[archive-real-log-01](archive-real-log-01/run.json)，外置盘复制后逐字节读回一致，pointer写好才删本地原件；无其他>5MB文件。archive状态为PASS，原失败状态没有改写。路径：`/Volumes/WD-Elements/a2a-evidence/2026-10-11-batch13/T-076/card-2/outside-real-delivery-02/commands.jsonl.gz`；解码重放：`gzip -dc <该绝对路径>`。归档生成命令为`python3 -B evidence/2026-10-11-batch13/T-076/card-2/archive-real-log.py --output evidence/2026-10-11-batch13/T-076/card-2/archive-real-log-01`，是一次性移动，已执行的归档/输出不得覆盖。

静止真实数据库一致性报告仍INCOMPLETE：[real-delivery-consistency-01.json](real-delivery-consistency-01.json)。tasks/attempts/verifications一致，membership/session_presets无法重建；runs/attachments等为空，不能据此称覆盖。unknown_events为空，不改存储。命令：`node workbench/src/stateConsistency.ts --state /private/tmp/a2a-t076-real-delivery-02/state --output evidence/2026-10-11-batch13/T-076/card-2/real-delivery-consistency-01.json`（重新运行换新output）。

候选冻结为delivery-review-01：baseline a7f4cc30、HEAD 15f28e449f2c7c63af9914e399237ee08ac7ec9c、142个文件及基线/diff；原始model任务日志只来自上述隔离实验，不含实现聊天、PLAN/RESULTS。冻结复制的第一份草稿曾丢执行位，已保存candidate-initial-copy.tar.gz并在最终快照恢复源权限，未改主候选。由于子代理接口无法显式指定default，依 #86 请求真实CLI一次干净上下文只读审查，计划槽7，结构风险同审；准确argv/输入、home、预算、停止/清理见[DELIVERY-REVIEW-APPROVAL-01.md](DELIVERY-REVIEW-APPROVAL-01.md)。未开始审查、未新增reservation，实际仍6/8。需先批准才能准备auth和启动，未作交付提交或push；审查发现问题须先红后修并交diff。


## 主控 #92：最终交付、逐条验收与局限（2026-10-13）

卡2交付为**PASS**，独立审查为**PASS / LIMITED_GO**，仅覆盖已验证的隔离受管交付。产品和测试源码提交为`2bc3a1e96b1ecb687e8fae32ebbc5478fa58de88`；本节、原始证据和ticket Resolution进入随后单独的证据提交。ticket保持open、ready_rev=1，待主控关闭。没有push、改存储或切换正式工作台。

**候选与审查绑定。** 开工起点为a7f4cc3033c16d5888de50d8352da516c941f8e9。审查冻结源HEAD为15f28e449f2c7c63af9914e399237ee08ac7ec9c；实际未提交源码以delivery-review-01的142个文件、baseline和diff确定。审查读回时142个文件与主checkout逐字节一致；真实正例的48个产品源码/hook文件也与冻结候选一致。审查之后更新README、RESULTS、Resolution、断言变更记录和交付核对脚本/收据；暂存检查另发现controlled_quality_pty.ts第13行空行有两个尾随空格，仅删除这两个空格。失败原文及格式diff保存在source-staging-check-01，最终核对逐字限定这一差异。产品、hooks和旧验收源码没有变化，测试仅有上述空白修正。两次提交使用本worker当前launch、实际gpt-6.1-sol/xhigh及原生会话的9项尾注。

### T-076 Acceptance逐条对应

| ticket验收项 | 结果与证据 |
| --- | --- |
| 1. 后台CLI驱动真实Codex worker/reviewer；命令、事件、Git读回 | PASS。真实正例[run.json](outside-real-delivery-02/run.json)、bindings.json、gate-events.json、events-after-stop.json、两个native-sessions及[读回](real-delivery-readback-02/run.json)。worker4回合、reviewer1回合，均由实际Panes/PTY/原生CLI启动；CLI、B relay、Git、SQLite均走产品入口。run.json历史归档状态的解释见下文。 |
| 2. 第一次打回→自动回写→修好重交→审查可合并→带分集成 | PASS。C1 709a85ba78c9e341c6d9b47013bbdaf48e11623c完成条件首拒；登记⟦门禁 #3⟧写回；同attempt重交C2 e08f87cf6621c39436aff5bb37210270f0ec8990；新只读reviewer可合并。主控在ready-for-score之后填写3/3，唯一integrate生成M b24ec63e5ffce0fd5da598247dbfe09b8722ab20，父提交精确为G 5ce713f51d3ffbc4c2ca4d8cc54d4add65625c38和C2；score_recorded一次，随后回收。证据：integration.json、executor-score.json、score-payload.json、[读回](real-delivery-readback-02/run.json)。 |
| 3. 六类反例各在入口拒绝并留事件 | PASS。逐案对应见下一表；六类使用实际后台/CLI/Git/SQLite和受控PTY/外部JSON输入，真实模型另证明缺分拒绝、只读权限和结论通道。不把全部受控反例称为真实模型实验。 |
| 4. 真实worker尾注Model/Effort与启动记录一致 | PASS。outside-real-delivery-02的C1/C2完整提交号.message、bindings.json、native-sessions和[读回](real-delivery-readback-02/run.json)核对9项尾注；实际模型gpt-6.1-sol、xhigh，与交付turn_context一致。 |
| 5. 多回合后run/reclaim仍核对身份；伪造会话拒绝；先红 | PASS。卡1先取得多回合红态与真实run/reclaim证据；本卡同原生会话4回合、两次ACK零工具调用，提交绑定第1/3回合，原attempt和leader保持。outside-legacy-green-06/multiturn、run及身份反例继续通过；真实正例最终回收。卡1原始证据见[RESULTS](../card-1/RESULTS.md)，本卡没有删除或放宽身份检查。 |
| 6. 一致性结果如实报告 | 已报告，**全库INCOMPLETE**。[real-delivery-consistency-01.json](real-delivery-consistency-01.json)中tasks/attempts/verifications一致；memberships/session_presets无法由事件重建。空表不代表覆盖；本条真实正例未覆盖attachment中断窗口。卡1已报告creating及active-before-attached不一致并交构思主控另切存储，本卡不修存储、不称全库PASS。 |
| 7. 五类产品变异体失败；8/9/18与T-075正反例不退化 | PASS（受控回归）。[outside-legacy-green-06/run.json](outside-legacy-green-06/run.json)22步均符合预期；coop8/recovery9/run18均0 failures/errors/skipped。五类变异体各命中业务断言；同阶段还覆盖T-075/T-076-1任务卡、B relay、hooks、多回合、初始释放、停止、离线与外置盘。批准W01–W07/F01–F14及Recovery逐字不变由[断言变更记录](assertion-hunks.md)、legacy-acceptance-hunks.diff和最终范围审计证明。之后仅改变tier参数，最小红绿及priority/只读变异体见[outside-launch-policy-default-01/run.json](outside-launch-policy-default-01/run.json)，未声称把全部旧套件重跑在该参数版本上。 |

### 六类反例与已知坏实现

| 反例 | 入口证据及对应反事实 |
| --- | --- |
| 起点红态命令不失败 | outside-red-02/stage-2先取得RED-BASE-PASSES；outside-wide-green-01/widened-contracts的red_base_not_failing拒绝并留事件；red-base-zero-allowed变异体命中同一业务断言。 |
| 项目规则式检查失败 | 起点RED-RULES/RED-RULES-FROZEN；widened-contracts的red_rules_failing/red_rules_frozen分别拒绝失败或证明使用冻结项目配置；rule-failure-ignored及project-rules-silently-disabled变异体均被捕获。 |
| 写入会话或旧会话审查 | outside-focused-tracer-01/protocol-controls的tracer_writer_cannot_review、tracer_reused_native；old-native-accepted与reviewer-writable变异体分别命中TRACER-REVIEW-REUSE、TRACER-READONLY-ARGV。真实权限边界为outside-p-review-02：唯一sentinel写入EPERM，文件及Git未变，主机写入对照成功。 |
| 审查结论绑定错候选 | protocol-controls的tracer_wrong_candidate拒绝并留事件；wrong-c-accepted变异体命中TRACER-REVIEW-CANDIDATE；合法同C审查作为对照。 |
| 缺打分 | protocol-controls的tracer_score_required及score-invented/score-fields-unchecked；真实outside-real-delivery-02/missing-score-refusal.json为score_required，Git保持G，主控后填分才集成。 |
| 第3次打回停止自动回写 | protocol-controls的tracer_third_rejection：三次拒绝、仅前两次修复回写，第三次paused/stopped并上报；third-rejection-keeps-writing命中TRACER-THIRD-STOP。 |

这些目录保存逐案CLI收据、事件/数据库读回、原始失败和mutation.json。reviewer创建/重启/回收异常另有outside-reviewer-red-01三项预写红态及outside-reviewer-green-01的3+3+2项绿态；需修复问题清单原文回写、严格JSON、评分放弃/升级/双向导入及CAS前后恢复分别在focused/wide阶段通过，新增合同没有用兜底重试取绿。

### 独立交付审查与真实预算

[审查原文](outside-delivery-review-01/REPORT.md)来自全新CLI会话01a135fd-fd26-7693-a738-ad75036b220e，唯一完整主回合01a135fd-fd89-7f43-a55c-5ff290b54978。原生记录确认gpt-6.1-sol/xhigh、read-only、never；argv显式default，原生日志没有实际tier字段，供应商实际tier为未知。REPORT与task_complete.last_agent_message逐字一致；独立从ticket/spec重建验收，未读实现聊天或PLAN/RESULTS，并将结构风险纳入同一次审查。

审查未确认可达违规或结构风险；另用16项纯协议独立输入，以及从归档读出的C2执行8项整数边界/变体和7项非法类型检查，均通过。没有重跑需要写入、socket、后台或模型的完整套件。执行主控在task_complete之后按本实例cli.pid 46695发SIGTERM、核对无残留后删除整个CODEX_HOME；auth未进入证据。只读文件核对确认home不存在，不重复发信号或启动审查。

真实预算见[real-turn-budget.jsonl](real-turn-budget.jsonl)：P-review1＋真实交付5＋交付审查1＝**7/8**，槽8未启动。历史5回合运行的INCOMPLETE归档状态和各阶段零回合报告原样保留。最终核对脚本首次运行前静态修正了CARD.parents索引，未产生执行失败或产品改动。 槽7登记后，历史真实交付读回脚本的“全账本必须等于6”已不适合重放；仅将预算核对拆成该两组实验仍严格6回合、全账本如实报告当前累计且不超过8，其他业务断言不变。原readback-02的6回合收据不覆盖，重新读回见real-delivery-readback-03/run.json。

### 归档与剩余局限

48,122,290字节的commands.jsonl.gz已由主控在沙箱外复制到`/Volumes/WD-Elements/a2a-evidence/2026-10-11-batch13/T-076/card-2/outside-real-delivery-02/commands.jsonl.gz`并逐字节读回一致，本地原件删除，留下[指针](outside-real-delivery-02/commands.jsonl.gz.pointer.json)及[归档PASS](archive-real-log-01/run.json)。原真实run.json的INCOMPLETE/archive_required不覆盖；原始业务过程、归档完成及最终交付分别判断。审查与收尾仅核对外置盘存在/字节数和既有读回收据，未重新完整解压大日志。

- 全库一致性INCOMPLETE及attachment中断窗口保持上述边界；不改变存储结构。
- P-review02证明其当时冻结版本的真实只读sentinel拒写；该快照没有后来新增的显式default，当前候选未重新做sentinel。当前argv有针对性红绿/变异体和真实正例的启动记录证据。
- 受控输入证明协议和状态处理，不证明真实模型理解或审查准确率。一次良性候选通过不证明漏检率、可靠性、吞吐或成本改善。
- reviewer快照缺MAP，审查中的project_map status为不可用；主checkout收尾实际执行为0 problems/0 stale，收据见最终检查，不补称审查快照的地图检查通过。
- 审查及真实正例原生日志未报告供应商实际tier，只报告显式请求default。
- T-077 worktree命名/清理/R8、新worker原生记录归属合流问题（issue 20261011T180613Z）和T-078仍交主控衔接；没有接管、改其分支或宣称联验完成。正式工作台切换与生产使用不在LIMITED_GO范围。

### 重新生成与收尾检查

历史端到端阶段的确切命令见各阶段HANDOFF、审批包和run.json；重放须使用新label/实例根，保存原结果，真实CLI和沙箱外动作仍按主控逐次审批。最终只读核对不新增模型回合，可用新output目录重放：

```sh
python3 -B evidence/2026-10-11-batch13/T-076/card-2/check-final-delivery.py --allow-readme-update --allow-final-format --output evidence/2026-10-11-batch13/T-076/card-2/final-delivery-check-replay
python3 /Users/luckye/Documents/SKILLS/project-map-skill/project-map/scripts/project_map.py status --root .
git diff --check
find evidence/2026-10-11-batch13/T-076/card-2/ -type f -size +5M
```

首次全冻结字节/原生审查核对及槽7观察登记见[delivery-review-readback-01/run.json](delivery-review-readback-01/run.json)；最后提交前检查见[final-delivery-check-01/run.json](final-delivery-check-01/run.json)。检查对象包括冻结源码、白名单、Recovery逐字不变、审查原文/唯一回合、账本7/8、home删除、归档指针、地图、差异和证据大小。审查后README更新事实、controlled_quality_pty.ts仅删除空行的两个尾随空格；最终核对严格限定这两处差异，不给新业务变更背书。git diff --check首次未暂存检查不包含当时的未跟踪新文件，暂存后失败已保留，格式修正后再次检查。


提交暂存检查区分当前源码/文档和原始证据：源码42个文件的cached检查为PASS（source-staging-check-02）；当前Resolution/RESULTS/核对脚本的cached检查为PASS（evidence-staging-check-02）。额外完整`git diff --cached --check`退出2，315条空白告警全部来自162个原始diff、终端stdout/stderr.bin、Git消息和冻结快照，包括diff上下文空行必需的空格；原输出与INCOMPLETE状态保留在evidence-staging-check-01，不清洗原始证据、不把该完整检查写为PASS。要求的`git diff --check`退出0，地图与>5MB检查均通过，见final-delivery-check-01。分类探针首次遗漏stderr.bin和hook-turn的message.txt路径而AssertionError，属于探针错误；原错误和精确修正登记在evidence-staging-check-02/classifier-error.json，未改业务断言或产品。

最终证据提交前再次执行同一有界核对，最新收据为[final-delivery-check-02/run.json](final-delivery-check-02/run.json)；仅补文档与提交检查收据，没有新增产品/测试行为或模型回合。
