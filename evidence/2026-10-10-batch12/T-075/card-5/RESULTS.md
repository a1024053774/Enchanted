# T-075-5 结果（2026-10-11）

状态：**限定业务 PASS，收尾 INCOMPLETE**。outside-full-01 已在当前候选取得 8/8、9/9、18/18、CAS 1/1，以及三个业务变异体反事实；一次 fresh-context 只读独立审查确认限定业务 claim 为 PASS，无新增修复项，原始 STATUS 为 INCOMPLETE，仅剩主控已接管的 README stale。ticket 保持 open，待主控关闭。

- 开工 HEAD：`1b522e92aa3944ebc0caca78c62553d8de386ed0`。
- 来源：T-075，`ready_rev: 4`；任务卡 T-075-5，worker `s12-t075-5`。
- 启动记录：`launch-e2dfb51e50404371bb95e477b46bbac6`，attempt `a1`，session `f82c11a2-4410-42fc-b9f9-24b0ad037050`。请求模型 gpt-6.1-sol、xhigh、Fast，实际 tier 未核对。
- 开工已有脏文件：`evidence/2026-10-09-batch11/controller-poll.log`，原样保留。
- 开工地图检查：退出 0，0 problems、0 stale。命令：`python3 /Users/luckye/Documents/SKILLS/project-map-skill/project-map/scripts/project_map.py status --root .`。
- 三份断言文件相对 `7bcfe7d9` 的 diff 为空。命令：`git diff 7bcfe7d9 -- acceptance/test_coop_e2e.py acceptance/test_recovery_e2e.py acceptance/test_run_e2e.py`。
- [PLAN.md](PLAN.md) 列出 35 项迁移、三种变异体、沙箱外运行与待批准的内部后台构造边界。既有 35 项红态为入口失败；新绿态和新业务反事实尚未运行。
- 计划检查收据：[plan-check-01.json](plan-check-01.json)。UTF-8 无 BOM、LF 回读通过；断言 diff 为空；地图 0 problems、0 stale。
- 范围外边界已通过规定收件箱上报：`20261011T082956Z-worker:s12-t075-5-issue-001`（blocking，仅等待计划与产品边界批准）；正文见 [issue-daemon-fixture.md](issue-daemon-fixture.md)。

后续实际运行证据、审查与提交待探针返回后追加。本记录不代表 T-075 验收第 4 条通过，ticket 保持 open，待主控关闭。

## 主控 #47 批准后：三个探针待运行

批准依据：[controller-decision-01.md](controller-decision-01.md)。恢复工作时 HEAD 为 `2d7d416790e59b2082c9c5bd531b8505c3b4ac6f`；两份已有 controller-poll.log 修改和此前 issue 条目原样保留。

产品 diff 只在 `workbench/src/daemon.ts`：导出同一 `serve`，增加内部 `createGates` 参数，默认仍为 `new A2AGates(root, panes)`；原 daemon_start 调用不传此参数。参数仅用于测试注入，产品 CLI 没有新选项或环境开关。已核对 workbench/README.md 的运行时边界与产品操作说明：产品使用步骤未改变，内部测试入口的说明由主控处理。

随后地图检查返回退出 1、0 problems、1 stale：未提交的 daemon.ts 改动触发 README 覆盖检查。语义核对不等于地图通过。已另行上报主控：`20261011T084236Z-worker:s12-t075-5-issue-001`，并在 [issue-readme-stale.md](issue-readme-stale.md) 给出可直接采用的内部测试入口说明；worker 不改范围外 README/MAP。失败交接记录在 `probe-ready-01/` 保留，最新静态交接包另存 [probe-ready-02/receipt.json](probe-ready-02/receipt.json)；最终 0 stale 尚待主控处理。

探针与证据边界：

| 探针 | 原业务方法 | 状态与范围 |
| --- | --- | --- |
| delivery | `test_good_candidate_uses_oracle_snapshot_and_integrates_once` | 未运行；产品 daemon_start，最终 CLI，普通交付与幂等 |
| recovery | `test_interrupted_verify_gets_new_id_worktree_and_full_oracle` | 未运行；产品后台 SIGKILL、真实断连、显式同 state 重启、原恢复断言 |
| run | `test_fixture_existing_dispatch_submit_oracle_integration_and_reclaim`，随后 `test_run_entry_point_completes_registered_task` | 未运行；两项均为隔离编排证据，生产 serve 加既有线程服务，不证明真实 PTY/Codex/B 转交通道 |

新增 `daemon_acceptance_adapter.py`、`daemon_acceptance_host.ts` 与 `run_daemon_acceptance.py` 均位于 `workbench/tests/`。当前运行器只开放这三个探针，计数为 1+1+2 个原方法，不声称已提供全量套件或变异体运行器。临时根分配变短，state 与 repo 关系不变；所有业务请求仍经 `acceptance/entry/a2a_gates.py` → 产品 CLI → socket → 同一后台。恢复只中断记录且核对过的自有后台，原 CLI 的退出照实保存；原测试方法、业务 check、原始三份验收文件未改。

沙箱内检查：

- Python AST、Node `--check`、`bash -n`、运行器 `--help` 和 `git diff --check` 通过。没有执行任何 TestCase.setUp、socket 或后台启动。
- D1 入口检查：[host-export-red-01](host-export-red-01/) 的缺少 serve 导出 → [host-export-green-01](host-export-green-01/) 同命令通过。只是模块入口红绿，不计业务证据。命令：`node --input-type=module -e "import { serve } from './workbench/src/daemon.ts'; if (typeof serve !== 'function') process.exitCode = 1;"`。
- 四个测试方法的继承身份已核对，适配类没有重写业务方法；三份验收文件相对 `7bcfe7d9` 的 diff 仍为空。

请执行（新标签；已有标签会拒绝覆盖）：

```sh
bash evidence/2026-10-10-batch12/T-075/card-5/outside-sandbox.sh outside-probes-01
```

脚本在新 `outside-probes-01/` 保存协调命令与退出码，各探针分别保存到 `outside-probes-01-{delivery,recovery,run}/`。每项有实际源文件快照、原始输出、完整 CLI 命令、后台代次/PID/屏障/信号、只读 SQLite 读回与完整夹具归档。检查外置盘真实挂载、Node 26.5 与现有 node-pty helper；无自动安装或缓存回退。首个失败后停止，其余项记为未运行，保留自建 repo 原目录，不删除或覆盖失败现场。

独立重现某个探针用新标签：`python3 -B workbench/tests/run_daemon_acceptance.py --probe <delivery|recovery|run> --label <新目录名>`。实际业务失败交主控决定；本轮不提前运行全量、不提交最终交付，也不消耗真实 Codex 被测回合。

## 主控 #48／#49：读回夹具修复与沙箱外交接

主控报告与原输出分别保留：

- [outside-probes-01-delivery/stderr.txt](outside-probes-01-delivery/stderr.txt)：原 P1 业务方法通过，1 test、OK。这只证明方法已通过，未完成整项探针的读回与归档。
- [outside-probes-01/delivery.command.json](outside-probes-01/delivery.command.json)：随后 read_state 在查询 SQLite 时返回 `unable to open database file`，子运行退出 1。原汇总为 INCOMPLETE；P2/P3 因首项后处理失败未执行。原输出和原源文件快照均未改写。
- worker 核对到 `/tmp/a5-2w4wrneu/t-u1whvi0f/isolated state/state.sqlite3` 仍存在，后台已停止，库旁没有 WAL/SHM；[read-state-diagnosis-01](read-state-diagnosis-01/) 中复制的已关闭数据库也复现相同只读查询错误。未把“目录已移走”当已核实的原始原因；修复同时验证目录移走后的采集仍可完成。

修复只改两份新测试文件：

1. `daemon_acceptance_adapter.py` 在核对后台所有权后、daemon_stop 之前，用只读连接查询 SQLite 全表；显式关闭只读连接，把快照直接写进本次证据的 `readbacks/`，记 test、原数据库路径、PID、代次、时间与 `before-daemon-stop` 阶段。即使捕获失败，也在 finally 中执行既有后台停止流程，失败交给 unittest 记录，不吞掉异常。
2. `run_daemon_acceptance.py` 只汇总已保存的 JSON 快照，并核对它属于原 test/state；不再在测试 cleanup 后打开 SQLite，也不把缺少快照当通过。测试结束后先保存 `test-result.json`，再归档夹具，最后做读回汇总；后处理失败仍保留已完成的测试结果与原现场。

独立夹具回归（不是业务／后台验收）：

- 重现命令：`python3 -B evidence/2026-10-10-batch12/T-075/card-5/readback-timing-probe.py --label <新目录名>`。固定独立 SQL 行为 `id=7, value='snapshot survives cleanup'`，用原适配器 stop 顺序关闭一个合成 SQLite writer；分别在关闭后、移动自建临时根后检查保存结果。没有 daemon、socket、Git 或模型回合。
- [readback-red-02/run.json](readback-red-02/run.json)：改读回代码前，同一信号两项失败；关闭后为原 SQLite 错误，目录移走后拿不到预期行。
- [readback-green-01/run.json](readback-green-01/run.json)：修复后两项通过；最终连接关闭检查另保存在 readback-green-02。只声明读回夹具修复，不上调 P2/P3 或全量结果。
- 首次合成重现器 `readback-red-01` 的 writer 关闭 SQLite 后仍持有 stdin，停止等待超时；这是重现器自身错误，不计读回红态。原文件与失败记录保留；重现器改为同步关闭数据库后正常退出，readback-red-02 的 writer 退出 0。

**沙箱外流程纠正（来源：主控 #49）**：worker 的沙箱内 ps 被拒后曾申请提权 ps/kill，执行主控用 Esc 拒绝。此请求不符合本卡交接方式，不能记作已清理。随后执行主控在沙箱外核对：readback-red-02/writer-launch.json 的 PID 11137 已不存在；ps 中没有 writer.mjs 或与 `/tmp/a5-*` 相关的 Node 进程，因此不需要再清理。这是主控提供的观察，worker 没有冒称自己执行了沙箱外核对。后续所有需要沙箱外运行的步骤，包括 ps 与自有进程清理，一律写入 outside-sandbox.sh 交主控，不再自行申请提权。

下一次命令（脚本默认标签也已改为 02）：

```sh
bash evidence/2026-10-10-batch12/T-075/card-5/outside-sandbox.sh outside-probes-02
```

脚本仍按 P1→P2→P3 串行、首个失败停止，不重用或覆盖 01 的目录。地图当前仍为 0 problems、1 README stale，已上报主控；不将未运行的实际探针或最终地图条件写为 PASS。

## 主控 #50：探针通过，准备全量与反事实

已核对 [outside-probes-02/run.json](outside-probes-02/run.json) 和三个子收据：delivery 1/1、recovery 1/1、run 2/2，全部 exit 0、0 failures、0 errors、源文件运行中未变化。run 的两项为夹具准备和完整 run；协调层虽然记三个探针，不能把实际方法计数写成 1+1+1。主控另报告没有残留进程，worker 未自行运行 ps。

全量适配现在包含：

- 原类内明确成员选取：交付 8、恢复 9、编排 18；业务测试方法全部继承原文件。CAS 使用既有 CASRace 的后台生命周期子类，额外 1 项，不凑入 35。
- 后台启动前设置测试 Git 路由，原 Git 屏障安装后显式将路由切到该夹具；初态固定调用已核对的真实 Git，不在失败后换工具或重试。before/after-CAS、撤销/变更后的恢复均只中断自建后台，按原 control/代次/PID 绑定。
- 编排五项按 PLAN 使用默认 daemon_start，十三项使用受控线程服务；逐项标注运行时层。busy_probe 的原业务 check/cli_result 表达式保留，仅把超时分支的屏障选择改为本次请求新生成、由本后台拥有的屏障；不停止原后台。
- 测试 host 显式接收门禁模块路径，通过同一个生产 serve 加载原门禁或隔离变异体；默认运行时用 Panes，受控项用既有 GateRuntime。客户端仍是最终产品 CLI，没有新产品选项或环境开关。
- `prepare_daemon_mutants.py` 从同一候选冻结三个单点变异体：submit fence、Git update 的旧值 G、operationLock 的 BEGIN IMMEDIATE。版权声明保留；依赖链接只在新 `/tmp` 源码夹具内，不在共享构建输出。`mutation-prep-check-01` 只是源码准备检查，尚未运行任何变异体。

新的沙箱外脚本按以下顺序执行；任何意外失败即停止，已有证据目录拒绝覆盖：

1. 原 run-acceptance.py 在当前源码上重跑旧三套，预期 8/9/18 失败于明确的 socket 路径字段。协调记录标为入口红态；不能充当门禁业务红态。
2. 新适配器在同一当前候选跑 8/8、9/9、18/18；编排结果还机械核对五项默认、十三项隔离。三份 acceptance/test_*.py 相对 7bcfe7d9 的 diff 必须为空。
3. CASRace 1/1 单列通过。
4. 三个变异体各跑对应原信号，保留其 INCOMPLETE/exit 1；另判反事实是否成立：必须加载指定变异体、errors 为 0，并在错 fence 的真实交付结果／原 CAS 或锁的 false 业务断言上失败。入口、import 或夹具错误不算杀死变异体。

命令：

```sh
bash evidence/2026-10-10-batch12/T-075/card-5/outside-sandbox.sh outside-full-01
```

总协调收据在 `outside-full-01/`；分项在 `outside-full-01-{red,green}-{coop,recovery,run}`、`outside-full-01-green-cas`、`outside-full-01-mutant-{fence,cas,lock}`，变异体源与 patch 在 `outside-full-01-mutants/`。每项分别保留源文件、命令、后台生命周期、原断言结果、readbacks 和夹具归档；整个阶段再核对源文件未变化。原始缺尾注／人工介入等事件仍按原门禁记录，不为测试凑结果写库。

当前只做过语法、成员绑定、业务 check 保真及变异点准备检查；未在沙箱内运行新的全量、屏障或变异体。沙箱外身份核对和进程清理仍全部由该脚本里的运行器执行，交执行主控，不申请提权。阶段运行成功也只证明本次红绿与反事实，整体任务继续 INCOMPLETE；收到实际结果后再冻结候选，做一次 fresh-context 只读独立审查并完成交付。

## 最终业务证据与独立审查（主控 #51）

执行主控已运行并核对 [outside-full-01/run.json](outside-full-01/run.json)。运行时间为 2026-10-11 09:19:16～09:21:59 UTC；开始时 Git HEAD 为 `2d7d416790e59b2082c9c5bd531b8505c3b4ac6f` 加本卡未提交实现。实际执行源码完整保存在 [outside-full-01/sources.tar.gz](outside-full-01/sources.tar.gz)，[source-manifest](outside-full-01/source-manifest.json) 保存代码 diff 和文件清单；阶段 `changed_source_paths=[]`。不能只以 base HEAD 代指候选。随后冻结为 [review-candidate-01](review-candidate-01/manifest.json)，46 个源码文件均与实际运行包逐字节一致。审查后没有产品或测试代码改动；最终交付提交绑定的逐文件检查另保存在 delivery 证据。

| 当前证据 | 结果与位置 |
| --- | --- |
| 原入口红态 | coop 8 项、recovery 9 项、run 18 项全部失败于 socket 超过 103 字节；0 errors。coop 因子测试有 9 个 failure 记录，不能写成 9 项。见 outside-full-01-red-{coop,recovery,run}；只记入口红态 |
| 交付绿态 | [green-coop/run.json](outside-full-01-green-coop/run.json)：8/8，0 failures/errors/skipped，默认生产后台 |
| 恢复绿态 | [green-recovery/run.json](outside-full-01-green-recovery/run.json)：9/9，0 failures/errors/skipped；含 live 锁、verify 中断、新 ID/worktree、CAS 前后、X/删除引用与撤销/规格变化 |
| 编排绿态 | [green-run/run.json](outside-full-01-green-run/run.json)：18/18，test_phase_status=PASS、原 stderr 为 Ran 18/OK；五项默认 Panes、十三项隔离线程服务，逐项 layer 见 runtime_layers |
| CAS 补充 | [green-cas/run.json](outside-full-01-green-cas/run.json)：1/1，独立外部写入发生在检查 G 后、真实 CAS 前，保留 X；独立计数，不凑入 35 |
| Fence 反事实 | [mutant-fence/run.json](outside-full-01-mutant-fence/run.json)：C2 的 field='fence' 子测试错误接受 fence=32；原业务断言失败，0 errors。一次方法有两个子测试失败记录，未归类环境红态 |
| CAS 反事实 | [mutant-cas/run.json](outside-full-01-mutant-cas/run.json)：只删除旧值 G 后覆盖外部 X，原错误接受／引用保留／accepted 断言 BUSINESS_RED，0 errors |
| 操作锁反事实 | [mutant-lock/run.json](outside-full-01-mutant-lock/run.json)：只删除操作锁 BEGIN 后启动第二个 oracle，并发 integrate 成功，原排他断言 BUSINESS_RED，0 errors |
| 变异体源码 | [outside-full-01-mutants/manifest.json](outside-full-01-mutants/manifest.json)、sources.tar.gz 与三份 patch；host_ready 保存实际 loaded core，均为对应本次单点变异体 |
| 原断言保真 | 三份 acceptance 文件相对 7bcfe7d9 的 diff 为空；36 个原方法继承身份和 busy_probe 的原业务调用表达式在 full-ready-01 已核对，审查独立复核 |

环境：Node v26.5.0、Python 3.9.6（系统 CommandLineTools，SQLite 3.54.0）、Git 2.52.0；工作台现有依赖和缓存设置未改。实际运行 preflight 记录外置盘真实挂载、node-pty helper 路径可执行；没有安装、构建、缓存回退或真实被测 Codex 回合。各后台代次都有保存的 confirmed_exited；本次没有再次以 worker 自己的 ps 查询当前进程。

**独立审查一次，原文不改写**：[review-01.md](review-01.md)。使用 API 新上下文 `t0755_acceptance_review`，fork_turns=none、请求 gpt-6.1-sol/xhigh，只读固定候选，没有启动后台、运行测试或查询进程，也没有二次审查。审查者从任务卡、spec、独立 oracle、原始子运行记录和归档重建结论，另外核对归档的 39 个数据库与停服前快照、七个故障后台代次、三个真实单点变异体及 caller 原请求。结论为：限定业务 claim PASS，无新增 P1/P2/P3；整体 STATUS INCOMPLETE，仅 README stale。API 未提供实际 Fast tier 或原生 CLI argv 证明，报告不作该声明。

重现当前全量：`bash evidence/2026-10-10-batch12/T-075/card-5/outside-sandbox.sh <新标签>`。需要分项时，运行器 `--suite coop|recovery|run|cas --label <新标签>`；变异体按 manifest 使用 `--mutant fence|cas|lock --mutant-manifest <manifest.json> --test <原方法名>`，完整实际命令均在协调目录的 *.command.json。所有沙箱外动作由执行主控执行；worker 不申请提权。

历史失败完整保留：outside-probes-01 的方法绿态与后处理失败、读回诊断/红绿、合成重现器首次超时、Esc 拒绝、主控确认无需清理，以及各次静态交接的 README stale。额外的 [retained-failure-fixtures-01](retained-failure-fixtures-01/run.json) 归档第一次 P1 和两份失败重现器的原目录；这是事后保存，不补称为当时的独立监控。旧 run 红态的内嵌 repo 原目录保留，完整归档进入版本控制，未作为 gitlink 提交。

边界：十三项受控线程场景不证明真实 PTY、Codex 或 B 转交通道；本卡不覆盖 UI、S2～S5、生产发布、可靠性或成本。旧卡通过记录不替本卡背书。最后地图运行仍是 0 problems、1 stale、退出 1；README 的更新与地图 Verified 由主控 #51 明确接管，worker 未修改这些范围外文件。业务和审查的 PASS 不上调为整卡 PASS；提交交付后报告 INCOMPLETE，待主控完成该收尾并关闭 T-075。

## 提交与交付绑定

代码、证据与审查提交：`eb296cec6f98cf7e6ba48c540e691100648932cc`。九项 `A2A-*` 尾注齐全，A2A-Launch 指向本 worker 的 `launch-e2dfb51e50404371bb95e477b46bbac6`，原生会话为 `01a12a0e-ed80-78d1-b991-c66b949ba16d`。提交钩子仅为本启动记录追加一条 native-session 事实；该记录随交付收据保存，未修改脚本或 Git 全局/仓库配置。

[delivery-code-01/receipt.json](delivery-code-01/receipt.json) 保存提交后的 46 个源码逐文件核对：Git 中的版本、当前文件、实跑 source archive 与固定审查候选一致，原断言 diff 为空。无需复跑已通过的业务套件。模型/强度尾注取启动配置，不用它们证明实际 tier。

[delivery-index-01.json](delivery-index-01.json) 保存提交范围：328 个变更文件均属本卡，另五份已存在且未改变的文件仍在原 HEAD；没有 gitlink，三份他人的日志没有暂存。整体 staged diff 的空白检查在原始 unittest stderr、冻结 intent 的 Markdown 换行及 patch 上非零，原字节按证据保护要求保留；本卡源码与报告的检查为 0。

最后的文档/交付收据提交号以终端 DONE 行为准；它不再改产品或测试代码。本卡交付状态仍为 INCOMPLETE，唯一待主控收尾项为 README stale，T-075 保持 open、待主控关闭。
