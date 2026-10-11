# T-075-3 交付结果

状态：**PASS（仅 T-075-3）**。2026-10-11，执行主控运行 outside-b-06 后，真实 Codex 已经完成显式交付、机械检查、验收和 CAS 集成；一次 fresh-context 只读独立审查 PASS。被测真实主回合累计 **7/10**，按主控 #32 停止，不再追加。T-075 保持 open，待 T-075-4 及后续切片，待主控关闭。

计划起点为 `8071a4638f94c9465c939445624d61c9c4809561`，实施起点为 `f1a8c1716ea4abc3281161655d506fceeebbf378`。被测候选以 base HEAD `471fa75f7f28531e035479c795b043bb6cbc15f2` 加 [完整 workbench 源码归档](outside-b-06/workbench-source.tar.gz) 标识；当时存在未提交文件，不能只用 base HEAD 指代候选。审查前后核对的 67 个源码/符号链接均与该归档逐字一致，见 [冻结清单](review-target-08.json)。审查后只更新 README、报告和 Resolution，产品逻辑没有变化。实现及首批证据提交为 **`93a707299d3f50309b52bfafacfd9d6529794130`**；其后只追加文档收据，终端 DONE 行报告最终交付提交号。

## a2a 提交与收尾

按主控 #33，单独执行 `git commit -m 'feat(workbench): deliver Codex tasks through a persistent daemon'`，由既有 Herdr 期钩子生成九项尾注。Task=T-075-3、Attempt=a1、A2A-Launch=`launch-dcd075b4fa8d4d1b86c3334de6ff59e0`，与本 worker 启动记录一致；完整读回见 [commit-receipt-09.json](commit-receipt-09.json)。钩子正常向 `records/launches.jsonl` 追加原生会话绑定，这一文件由执行主控提交，未纳入本 worker 的暂存范围。

此前带 A2A_LAUNCHES 前缀的提交被沙箱拒绝，其提权申请由主控 Esc 拒绝，未产生提交。commit-environment-08.json 和 worker-launch-for-commit.jsonl 保留为未采用方案的日期证据；实际提交没有使用副本。本人创建的 `/private/tmp/a2a-card3-commit-f8svq3y2` 已删除。

提交后地图检查仍为 0 problems、0 stale，输出保存在提交收据。全量 `git show --check` 退出 2：历史 source.diff 的上下文空格和 fixture_artifacts.py 的尾部空行产生告警，原输出同样保留；不修改原始证据或冻结候选来消除告警，也不把此项写成通过。产品行为验收与一次独立审查均 PASS。没有新增真实回合，没有 push。

## 最后走的是 A2 还是 B

**最后走 B。A2 没验证成，按决定 04 改走 B。** A2 的工具命令在执行探针脚本之前就被拒，缺少 probe-results.json；不能把这一结果说成“代理配置验证不通过”。没有重试 A2，也没有把代理或 socket 白名单写进产品默认参数。

B 保持网络关闭及 workspace-write。worker 用同一 CLI 显式写请求文件，Stop hook 经后台 CLI 转交；后台处理结果先登记，再以 `⟦门禁 #序号⟧` 写回空闲窗格。请求放在每 attempt 独立的 `/tmp/a2a-requests-*`，避免进入候选 Git 提交。没有请求文件就没有交付。

## 完成条件与独立读回

| 完成条件 | 结果与证据 |
| --- | --- |
| 后台入口驱动真实 Codex 完成交付及集成 | **PASS**：[执行收据](outside-b-06/delivery/verdict.json)、[逐条命令及输出](outside-b-06/delivery/commands.json)、[启动记录](outside-b-06/delivery/launch-record.json) |
| Git 独立读 G/M，并与库内集成事件比对 | **PASS**：[初次读回](outside-b-06/delivery/git-readback.json)、[收尾独立读回](final-readback-08.json)、[只读可查数据库](outside-b-06/delivery/state.sqlite3) |
| 后台入口机械反例拒收并留事件 | **PASS**：后台门禁 [15/15](outside-b-06/gates/run.json)，包括越界、完成条件失败、外来/坏尾注、过期 fence/旧 attempt；缺尾注按修订契约记账并允许集成。B 另有身份错误、请求不完整、重复转交的真实事件 |
| 后台脱离调用者进程组并常驻 | **PASS**：[进程读回](outside-b-06/delivery/daemon-process-readback.json)：PID/PGID/SID 均为 56959，调用者 PGID/SID 为 55265，启动命令返回后仍存活；ps 原文在 commands.json |
| 地图检查 | **PASS**：0 problems、0 stale；原始输出见 [final-checks-08.json](final-checks-08.json) |

真实夹具身份：task `T-075-3`，attempt `a14bc59b-d434-4f63-8a69-e650e47f4b55`，session `424553c8-9551-4e25-9f9b-f81e23f40361`，fence `1`，门禁 spec_rev `1`（任务来源 ticket ready_rev `4`），launch `693c290a-ee8e-4938-a3cb-17c9d148d215`。

- G：`51d612b486c6935fe1616e001507eeeb47bafbe1`
- C：`641e55b8d005281c672f544ebec1c8814ab87a53`
- M：`287bbf8ae5eeadc901198233eeb0a0ac84f02b9e`

工作分支当前为 M，M 的两个父提交恰为 G、C，G 是 M 的祖先；独立写入 G 的 host.txt 得以保留。C 有本 attempt 的九项尾注，见 [Git 提交读回](outside-b-06/delivery/candidate-trailers.json)。独立 Git 与库内指标均为 **2 个文件、增加 51 行、删除 2 行**。实际回合模型为 gpt-6.1-sol、xhigh，Fast 仅证明已请求。

归档中有 606 条编排事件、106 条门禁事件；主任务导出的 156 条编排事件与数据库一致。`submitted`、`integrated` 各一次；路径、完成条件、尾注检查各有实际结果。派发与回执各一次，都先登记；两个主回合都有开始和结束，回执回合无工具调用。原始事件见 [编排事件](outside-b-06/delivery/orchestration-events.json)、[门禁事件](outside-b-06/delivery/gate-events.json)。

不启动进程或模型的复核命令（夹具仍保留时）：

```sh
git -C /private/tmp/a2a-B-oryewvig/repo rev-parse refs/heads/main refs/heads/main^1 refs/heads/main^2
git -C /private/tmp/a2a-B-oryewvig/repo merge-base --is-ancestor 51d612b486c6935fe1616e001507eeeb47bafbe1 refs/heads/main
git -C /private/tmp/a2a-B-oryewvig/repo show -s --format=%B 641e55b8d005281c672f544ebec1c8814ab87a53
```

数据库以 `file:<绝对路径>/outside-b-06/delivery/state.sqlite3?mode=ro&immutable=1` 打开，查询 `SELECT details FROM events WHERE type='integrated'`，与上述 Git 值比对；具体 argv、查询与输出保存在 final-readback-08.json。完整夹具在 [fixture-artifacts.tar.gz](outside-b-06/delivery/fixture-artifacts.tar.gz)，不含 auth.json 或隔离 home。

## 一次独立审查

**PASS**，原文见 [independent-review-08.md](independent-review-08.md)。通过内置 fresh-context 只读子代理 `t0753_independent_review` 执行，gpt-6-astra / xhigh；未启动 Codex CLI，未新增被测主回合。审查按 [behavioral-acceptance-review](/Users/luckye/.agents/skills/behavioral-acceptance-review/SKILL.md) 的独立 oracle、真实边界与反事实要求进行，并合并检查结构风险。该技能是本机文件，不随仓库分发。

审查者从原始 SQLite 和 Git 独立核对，并用未见过的 `Z9/Ω-sentinel`、60 分钟边界及浮点非法输入排除固定输出。没有发现需要修复的本卡问题，没有追审。审查前的归档比对夹具曾把 macOS tar 生成的 AppleDouble 元数据误当源码，导致检查失败；[失败记录](review-snapshot-check-07-failure.json) 保留，核对其专用文件头后仅排除这些元数据，源码仍逐字比较。

## 运行历史与边界

- **PASS（红态有效）**：新增入口检查在实现前因不存在 `daemon_start` 退出 2；不是缺依赖或测试脚本缺失。命令：`python3 workbench/tests/test_orchestrator_e2e.py --output evidence/2026-10-10-batch12/T-075/card-3/red-daemon-01`。原始命令、输出与断言见 [commands.json](red-daemon-01/commands.json)、[verdict.json](red-daemon-01/verdict.json)。测试整体失败是预期红态，不是产品 PASS。
- **PASS（静态检查）**：新 TypeScript 的 `node --check`、Python AST、shell 语法和 `git diff --check` 通过，记录见 [implementation-check-01.json](implementation-check-01.json)。node-pty 模块加载及实际 helper 的 X_OK 检查通过，Node 为 `v26.5.0`；未 spawn PTY。
- **PASS（后台常驻）**：执行主控运行 outside-probe-01，后台 PID/PGID/SID 均为 84172，与检查进程 PGID/SID 84149 不同。启动命令退出后后台仍可查询，见 [进程读回](outside-probe-01/host/process-readback.json)。
- **observed（窗格和拒绝）**：outside-probe-01 用 1 个真实主 turn。派发登记、M3 注入、executor 首次 release、UserPromptSubmit、Stop 和返回 idle 全部留证；原生 turn_context 为 never、workspace-write、network_access=false。模型工具的一次连接被 `connect EPERM .../state/control.sock` 拒绝，未重试、未改文件、未提交。两个生命周期 hook 却成功连上后台；不能据此证明模型工具沙箱里的 Git hook 可达。
- **PASS（脚本门禁）**：执行主控运行 outside-verify-03，后台入口 **15/15 PASS、0 failures、0 errors**，见 [run.json](outside-verify-03/gates/run.json)。包含原任务卡 14 项断言和新表追加约束。
- **BLOCKED（A 已验证失败）**：verify-03 中 network_access=false、network_proxy=false，单独指定后台 socket 白名单仍为 EPERM；对照 socket 和 TCP 也被拒。见 [verdict](outside-verify-03/probe/verdict.json) 和 [原始观察](outside-verify-03/probe/socket-observations.json)。已交 needs-decision `20261011T043544Z`；rev 4 已给出 A2/B 后续授权，本卡不重试 A。
- **INCOMPLETE（A2 未验证成）**：执行主控已运行 outside-a2-04，[原始 verdict](outside-a2-04/probe/verdict.json) 为 BLOCKED。带 example.com 的工具命令整体被工具层拒绝，报 “Network access to example.com was blocked: local/private network addresses are blocked by the sandbox policy”。脚本没有执行，也没有 probe-results.json。因此不能写成“代理配置验证不通过”，只能说未取得要求的证明。按决定 04，只要没过就进入 B。
- **PASS（B 转交机制）**：outside-b-05 的 relay-cli、relay-core 及后台门禁 15/15 通过。真实 Stop 拒收错误 fence、缺 commit 的文件，转交 status/issue；第二次 Stop 记录五次重放，没有重复副作用。两个主回合均结束，门禁回执已进入窗格，无 PermissionRequest。此结论不包含真实 submit；见 [原始事件](outside-b-05/delivery/all-events-before-stop.json)。
- **INCOMPLETE（b-05 原始失败）**：Git add 写 worktree index.lock 被拒；worker 显式上报阻塞问题，没有提交或伪造交付。[verdict](outside-b-05/delivery/verdict.json) 保留超时失败；归档和隔离 home 清理成功。当时累计 5/10，后经生产提示修复，在 b-06 用两个主回合通过；不覆盖旧失败。
- 旧 8/9/18 全套后台适配回归尚未完成，不沿用旧候选结论，不恢复本地开库旁路、不修改 `acceptance/` 断言。
- 两份主控 poll 日志是其他会话已有修改，本 worker 没有编辑或提交它们。

实际运行命令（执行主控已执行；仅为复现记录，当前授权禁止再运行真实 Codex）：

```sh
zsh evidence/2026-10-10-batch12/T-075/card-3/outside-sandbox.sh b-06 all
```

`all` 先运行 CLI 请求文件检查、转交与去重检查、后台门禁 15 项，再启动真实 B；前置失败即停止。`checks` 只运行无模型检查，`probe` 只运行真实 B。累计预算追加在 `turn-budget.jsonl`。b-06 模型固定 gpt-6.1-sol xhigh Fast，network_access=false、network_proxy=false，无 socket 放行参数。用隔离 CODEX_HOME，只复制 auth.json、只信任夹具仓库、只添加 git add/git commit 两条 allow 规则。

回执经 bracketed paste 加 CR 注入，会启动第二个主 turn，不能把它算作零回合。用户直接答复：**“允许额外 1 个回执回合，完成后停止”**，原话及来源见 [授权记录](feedback-turn-authorization-05.md)。决定 05 另准修复后复验一次；脚本固定每次两个：一个交付、一个只确认回执，累计超过七个就拒绝 release，不再追加。检查原生记录里恰好两个主 turn，回执原文与登记文本一致，回执回合没有工具调用；结束后停止本脚本创建的进程并清理隔离 home。

| 运行 | 真实主回合 | 累计 |
| --- | --- | --- |
| probe-01 | 1 | 1/10 |
| verify-02（夹具失败，未启动探针） | 0 | 1/10 |
| verify-03 | 1 | 2/10 |
| a2-04 | 1 | 3/10 |
| b-05 | 2 | 5/10 |
| b-06 | 2 | 7/10，停止 |

B 的真实夹具要求修改两个 Python 文件，实现去空白、同名归并、时长格式化、Unicode 名称及非法输入处理。独立 oracle 在 worktree 外，固定五组输入和结果；派发前保存基线红态。认领后另在项目工作分支写入不冲突的 G，使候选 C 必须与 G 合并；集成后独立 git rev-parse 读 G/M，与库中 integrated 事件核对。还核对九项尾注、文件和行数、路径/完成条件/尾注事件，以及请求身份不符、不完整和重复转交。请求反例由脚本注入并明确标注来源，不冒充 worker 发起。

A2 的原参数、命令与观察保留在 [outside-a2-04](outside-a2-04/)。它只改过测试源码副本，未进入产品默认参数；旧 A/A2 探针源码另存 [retired-a2-source-05.tar.gz](retired-a2-source-05.tar.gz)，当前脚本已移除该路径。

## 决定 05：Git 前缀与 never 的无模型核对

**observed（真实红态）**：outside-b-05 的 call_ce2cb0e8c17943629c757f04fd217708 包含两个 exec_command。第一个是 status/diff/Python 检查并通过；第二个才是 `git add -- src/normalize.py src/report.py && git commit -m 'Implement normalized time report and validation' && git rev-parse HEAD && git status --short`，它在 git add 处退出 128，不能把两个 exec_command 误写成同一条长命令。

**observed（规则匹配）**：固定 Codex 0.162.1，用 b-05 源码归档里实际写入的两条规则重建无认证的隔离 home，运行 execpolicy check。`git add src/x`、实际 add 参数、`git commit -m fixture` 均返回 decision=allow；rev-parse/status 无匹配。整条 zsh 包装命令无匹配，但包装单条 add/commit 也无匹配。因此此子命令只提供参数匹配证据，不能用它证明运行时对复合命令的拆分或实际沙箱选择。`-c approval_policy="never"` 出现在核对命令里，也不等于启动过执行工具。

原输出见 [execpolicy-06](execpolicy-06/results.json)，增加实际 add 与 rev-parse 对照后的可复现输出见 [execpolicy-06b](execpolicy-06b/results.json)。两次都没有模型回合、没有执行被测 Git 命令、没有复制 auth，隔离 home 已删除。首次读取 help 未设 CODEX_HOME，CLI 提示创建 PATH aliases 被当前沙箱拒绝；之后所有 Codex 诊断均设临时 CODEX_HOME，未放宽权限。

**observed（官方文档，核对日期 2026-10-11）**：[Rules](https://learn.chatgpt.com/docs/agent-configuration/rules) 将 allow 定义为免提示在沙箱外执行，并说明运行时会在可安全解析时拆分 shell 命令链；[Agent approvals & security](https://learn.chatgpt.com/docs/agent-approvals-security) 和本地 help 将 never 定义为关闭批准询问，失败直接返回模型。文档没有写 allow 在 never 下改为强制沙箱内执行。

**inferred（复验前的原因判断）**：复合调用混入没有显式 allow 的读命令，是当时沙箱选择失败的候选原因，execpolicy check 没有证明内部解析分支。**observed（b-06）**：生产提示要求独立 Git 写命令后，本机 0.162.1 在 never 下成功 add/commit，未弹批准，并完成后续交付；不能再声称该组合不可用。这个结果证明具体调用可行，不等于已定位 Codex 内部完整规则评估路径。

生产 `core.ts` 的 dispatch 提示现明确：以执行工具的工作目录设置 worktree；git add 与 git commit 各自独立，检查另行执行，不用 &&、分号、管道或其他 shell 拼接；独立命令仍被拒就上报并结束，不自行重试。只改派发提示和本次预算，不改 allow 规则、沙箱或交付通道。b-05 是原始失败证据，b-06 是同一真实入口的绿态。

重新生成无模型匹配记录：

```sh
python3 -B evidence/2026-10-10-batch12/T-075/card-3/check-worker-execpolicy.py --output /tmp/新标签-execpolicy
```

## B 的实现与无模型证据

同一 CLI 在受管 worker 环境中把 submit、status、issue 写成请求文件，包含 task、attempt、session、fence、spec_rev；submit 必须给完整提交号。返回 queued=true、delivered=false，明确尚未交付。每个 attempt 的请求目录位于 `/tmp/a2a-requests-*`，路径写进启动记录和 A2A_REQUEST_DIR。选择工作树外目录，是为避免请求文件污染 Git 候选或要求修改项目的忽略规则。

Stop 读取原文件并调用 CLI signal；后台在当前主回合仍绑定身份时执行已有门禁。Stop 本身不产生 submit。请求意图及结果只追加；相同 request_id、相同内容只返回原结果，换内容拒绝，未知结果不重跑。过期 Stop 不消费尚未处理的文件。一次 Stop 的新结果合成一个门禁回执，先登记再在空闲时写；重复文件在回执回合的 Stop 再次出现时，只记录重放事件，不产生第三个回合。

| 检查 | 红态或反事实 | 当前结果 |
| --- | --- | --- |
| worker 使用同一 CLI 排队 submit/status/issue | [red-relay-cli-05](red-relay-cli-05/results.json)：旧入口不支持请求文件 | [relay-cli-final-05](relay-cli-final-05/results.json)：PASS，不启动后台或模型 |
| 同一请求只执行一次，改内容拒绝 | [relay-counterfactual-05](relay-counterfactual-05/)：去掉去重后副作用计数变为 2，被断言拒绝 | [relay-final-05](relay-final-05/results.json)：PASS，包括身份/字段拒收、状态/问题、追加约束和未知结果 |
| 换内容的拒收回执只发一次 | [red-relay-edge-05](red-relay-edge-05/results.json)：首个拒收被错误抑制 | [green-relay-edge-05](green-relay-edge-05/results.json)：PASS |
| 旧 Stop 不占用新请求编号 | [red-relay-stale-stop-05](red-relay-stale-stop-05/results.json)：旧 Stop 先把新请求记为已处理 | [relay-final-05](relay-final-05/results.json)：PASS |
| 粘贴至 CR 期间视为正在写入 | [writing-counterfactual-06](writing-counterfactual-06/)：去掉 writing 保护，被业务断言拒绝 | [dispatch-writing-05](dispatch-writing-05/results.json)：PASS |
| 并发重复 Stop 不提前清空当前回合 | [red-concurrent-stop-05](red-concurrent-stop-05/results.json)：第二个 Stop 错误占有正在转交的回合 | [green-concurrent-stop-05](green-concurrent-stop-05/results.json)：PASS |

重现（每次使用未存在的输出目录；变异体命令及 patch 在对应目录内）：

```sh
python3 -B workbench/tests/test_relay_cli.py --output /tmp/新标签-relay-cli
node workbench/tests/test_relay_core.ts /tmp/新标签-relay-core
node workbench/tests/test_pane_dispatch_state.ts /tmp/新标签-dispatch
```

以上只证明本地入口、转交与状态边界，不能替代真实 Stop/PTY/模型交付。writing-counterfactual-05 的测试在预期失败后未等待残余 drain，还出现关库错误；修复测试收尾后改用 06 标签重跑，保留 05 原始失败。

## 探针缺陷修复与无模型检查

**停止确认的夹具缺陷已修复。** a2-04 的后台正在停止时，旧收尾先等 pidfile 消失、再只查一次 ps；后台 PID 6641 已退出，但当时还有辅助进程 7179，于是误记未确认退出。主控 #30 随后独立核对 PID 6641 已退出且无残留，并删除 `/tmp/a2a-t0753-kc1peqqf/codex-home`；不补称旧脚本自动清理成功。

收尾现在在十秒期限内同时观察 pidfile 和本次记录的全部 PID，二者都消失才归档和删除 home；不重发停止，不新增 kill。共享实现位于 `workbench/tests/fixture_artifacts.py`，真实 B 和归档复放都调用它。[red-stop-wait-05](red-stop-wait-05/results.json) 在延迟退出夹具上失败，[cleanup-shared-05](cleanup-shared-05/results.json) 七项通过，包含 WAL、归档失败、已有目标、存活进程和延迟退出。green-stop-wait-05 另有提取 helper 后测试自身 NameError，已保留；修复夹具后用 green-stop-wait-06 重跑通过。

**WAL 归档缺陷已修复，未新增模型调用。** verify-03 的归档再次报 unable to open database file，但先前 finally 修复已保证该次 home 删除；旧零字节归档和 archive_error 保留。[诊断矩阵](archive-diagnosis-04/matrix.json) 在真实库副本中定位：当前 Python 3.9.6 / SQLite 3.54.0 以 mode=ro 访问缺少 WAL 辅助文件的 WAL 库，在首次查询就失败，问题不只是目标文件已存在。

修复为：先确认本探针写入进程已退出，独占创建归档，复制主库及仍存在的 WAL；只在归档副本上读写并转为 DELETE journal，检查完整性。原库不以读写方式打开，不重试、不覆盖旧产物。新增 WAL 关闭和 WAL 尚含已提交内容的检查，[红态](red-wal-archive-04/results.json)失败，[六项绿态](green-wal-archive-05/results.json)通过。

对实际 verify-03 保留库的副本执行归档也通过：[重放结果](archive-real-replay-05/results.json)、[可独立读取的 SQLite](archive-real-replay-05/state.sqlite3)。此前从后台读回的 140 条事件与归档逐条一致，归档共 146 条，原库字节未变。仅执行归档 finally，未重启后台、PTY 或 Codex。重现：

```sh
python3 -B workbench/tests/test_probe_cleanup.py --output /tmp/新标签-wal-archive
python3 -B evidence/2026-10-10-batch12/T-075/card-3/replay-db-archive.py --receipt evidence/2026-10-10-batch12/T-075/card-3/outside-verify-03/probe --output /tmp/新标签-real-archive
```

执行主控的 `outside-verify-02` 退出 1：15 项测试中 11 项在 setUp 的 daemon_start 因 socket 路径超过 103 字节失败，另 4 项通过。原始 [run.json](outside-verify-02/gates/run.json) 与 [stderr](outside-verify-02/gates.stderr.txt) 保留；这些失败是夹具路径错误，不是门禁业务拒收失效。`set -e` 阻止了后续真实探针，累计主 turn 仍是 1/10。

按主控 #27，仅缩短两处夹具临时目录前缀：外层 a2adc-、用例层 c-；完整用例名仍在 ARTIFACTS/COMMANDS。产品限制与业务断言未改。路径检查从 11/15 超限、最长 136 字节转为 15/15 均为 57 字节；之后 verify-03 整套 15 项通过。

路径检查证据：[红态](red-fixture-paths-03/results.json)、[绿态](green-fixture-paths-03/results.json)。重现：

```sh
python3 -B evidence/2026-10-10-batch12/T-075/card-3/check-fixture-paths.py --output /tmp/新标签-fixture-paths
```

outside-probe-01 在 `source.backup(dest)` 报 `unable to open database file`，阻断最终 verdict 和隔离 home 清理；旧 verdict 仍是中途 INCOMPLETE。原 [traceback](outside-probe-01/probe.stderr.txt) 保留。执行主控确认没有存活进程后，已删除 `/tmp/a2a-t0753-hz27kh8k/codex-home`，见决定 02；本 worker 不补称当时已自动清理。

| 检查 | 红态 | 绿态及限制 |
| --- | --- | --- |
| 备份失败仍清理、已有备份不覆盖、存活未确认则保留 home | [red-cleanup-02](red-cleanup-02/results.json)：异常跳出、home 残留、旧备份被覆盖 | [green-cleanup-02](green-cleanup-02/results.json)：三项通过，执行 probe 的实际 finally，省去模型/后台阶段 |
| pty.raw 写失败及事件库也失败 | [red-trace-02](red-trace-02/results.json)：无事件、未禁用门禁写入 | [green-trace-02](green-trace-02/results.json)：trace_write_failed 入库；库也失败则 event_write_failed，observer 标失败 |
| 尾注只依赖环境事实 | [red-hook-env-02](red-hook-env-02/results.json)：错误依赖 A2A_NODE | [green-hook-env-02](green-hook-env-02/results.json)：九项尾注、去重、缺身份/换行拒绝、模型/强度 unknown |
| 派发与状态 | [变异体](dispatch-counterfactual-02/mutant/results.json)：去掉 idle 限制，未知态提前写两段字节，被断言拒绝 | [候选](dispatch-counterfactual-02/candidate/results.json)：登记先于写入、CR 即忙、旧/辅助 Stop 不放行、登记失败不写入 |

PTY 回调注入测试不替代真实终端验收。重现命令：

```sh
python3 workbench/tests/test_probe_cleanup.py --output /tmp/新标签-cleanup
node workbench/tests/test_pane_trace_failure.ts /tmp/新标签-trace
python3 workbench/tests/test_hook_environment.py --output /tmp/新标签-hook
node workbench/tests/test_pane_dispatch_state.ts /tmp/新标签-dispatch
```

变异体的具体命令与改动见 [commands.json](dispatch-counterfactual-02/commands.json)、[mutant.patch](dispatch-counterfactual-02/mutant.patch)。失败全部保留，探针修复没有新增真实主 turn。

接入新版网络探针后，清理检查再次通过：[green-cleanup-03](green-cleanup-03/results.json)。本次语法、文档编码/链接、地图检查见 [implementation-check-02.json](implementation-check-02.json)，这些静态检查本身不替代后来完成的后台反例或真实 socket 验收。

## 本轮实现的路径

现有 `workbench/src/gates/cli.ts` 对主控是 Unix socket 客户端，对受管 worker 的 submit/status/issue 则写请求文件，由 Stop 使用同一入口转交；后台托管同一个门禁核心。新增编排表、启动记录、派发队列、node-pty/zsh、结构化信号与前台进程核对。Git 钩子按决定 02 暂只读环境事实，不查后台；取不到本回合 Model/Effort 则写 unknown，不冒充请求参数。dispatch 模型取任务卡，不写 MCP 工具名或旧模型。

此前两轮真实窗格固定 Codex 0.162.1，`--no-daemon --no-alt-screen -a never --sandbox workspace-write -m gpt-6-astra -c model_reasoning_effort="xhigh" -c service_tier="fast" -c check_for_update_on_startup=false`。UserPromptSubmit、Stop、PermissionRequest 三个 hook 经决定 01 批准，均以 `-c` 传入；hook 命令是绝对 Node 路径加本仓库 CLI 的 `signal --launch ...`，具体展开值由脚本保存的 `probe/launch-record.json` 及库中 launch_records 读回。信号输出仅 `{}`，不返回批准决定。 rev 4 的新被测会话改用 `-m gpt-6.1-sol`，其余模型参数仍为 xhigh/Fast；当前开发 worker 不换模型。

使用交互 `/bin/zsh -f -i`，禁用启动文件以免继承外部会话身份；CLI 退出后保留 zsh。主控先读 `pane_process_info` 的 ps 结果，再显式 `pane_release`。它是 executor action，不是用户输入或人工介入。初态和缺信号状态均不凭屏幕判断；UserPromptSubmit 不参与解锁，Stop 须匹配当前主原生会话和 turn_id。

官方 [Hooks 文档](https://learn.chatgpt.com/docs/hooks) 列出 SessionStart。当前仅批准的三个 hook 被安装；尚未实测 0.162.1 的 SessionStart 是否表示 PTY 已可收输入，不能将文档存在当作本机就绪证据。本阶段使用决定 01 / 主控 #24 指定的显式首次 release，完整初始化语义仍是限制。

## 数据与已知缺口

产品默认路径为 `~/Library/Application Support/a2a-orchestrator`；本 worker 未创建该目录。运行显式使用新 `/tmp/a2a-t0753-*` 或 `/tmp/a2a-B-*` 隔离目录，不访问 `~/Library/Application Support/a2a-workbench`。只复制 auth.json 到隔离 Codex home，不把 home 或凭据打包；结束后先确认已观测进程退出，再删除该 home，失败现场的夹具与库保留。b-06 已完成退出确认及 home 删除。

**已知缺口：Model/Effort 尾注为 unknown。** 早期 socket 可达性失败后，按决定 02 把 Git 钩子限定为读取会话环境，不向后台查询。当前环境里这两项设为 unknown，后台虽从原生 turn context 采到实际 gpt-6.1-sol/xhigh，尚未把最近回合事实传给提交钩子。spec 第 8 节允许取不到时写 unknown，因此本卡通过，但追溯仍有缺口。

后续补齐方向：由后台把已核对且带 launch/native-session/turn 绑定的模型与强度提供给钩子；若从启动记录预填环境，要明确区分启动请求与最近回合观测，并处理会话中切换模型的更新语义。仅把 model_requested/effort_requested 改名填入尾注，不能满足“最近一轮记录”的要求。补齐时需另设隔离验收，检查提交值与对应回合一致；本卡不再开真实回合。

按决定 01，当前会创建或保留以下数据库文件：

| 文件 | 内容与写法 |
| --- | --- |
| `state.sqlite3`（及 WAL/SHM） | 原门禁业务数据；新 launch_records、dispatch_records、orchestration_events、relay_requests、relay_results 在此追加，触发器拒绝 UPDATE/DELETE |
| `membership.sqlite3` | 原 memberships/session_presets，保留覆盖更新，本卡不迁移 |
| `locks/*.sqlite3` | 原门禁操作锁，保持现状，不算新增业务库 |

按 rev 3，门禁状态表“是由事件推出的当前视图，历史以事件为准”。旧表仍有覆盖写，新表只追加。逐个 save 点的字段与限制见 [save-point-audit.md](save-point-audit.md)：save 有同事务事件，但多处仅为增量；attachment creating 还存在无对应历史事件的路径。**尚未验证 events 重建与视图一致**，该检查按用户决定留到后续切片，本卡不改旧存储。

静态核对发现已非阻塞上报：`20261011T042856Z-worker:s12-t075-3-issue-001`，供后续切片处理。

另一项静态发现已非阻塞上报 `20261011T052530Z-worker:s12-t075-3-issue-001`：B 的回执会产生新原生 turn，而旧 run/reclaim 仍比较 submit 时绑定的 turn，预计会触发 identity_conflict，尚未真机复现。依据和建议见 [回合身份记录](receipt-turn-identity-05.md)。未放宽门禁身份检查；本次脚本分别走 dispatch/submit/verify/integrate，最后的 daemon_stop 仅停止自建服务，不算业务 reclaim 的通过证据。

本卡不背书：旧 8/9/18 全套后台适配、旧 run/reclaim、多回合人工输入和 Esc 放行、后台重启恢复、Electron 及 S2–S4。本次 PASS 只覆盖任务卡 3 和决定 01～05 的隔离 Tracer bullet；不宣布整个 T-075 完成或日常工作台可切换。
