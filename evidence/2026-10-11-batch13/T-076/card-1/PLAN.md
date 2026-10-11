# T-076-1 计划（2026-10-11）

状态：**INCOMPLETE（计划交接，尚未实施或运行产品验收）**。

本轮只交计划，收到执行主控批准后才写测试、取红态和改产品。批准前不启动后台、Electron 或真实 Codex，不提交代码。

## 1. 起点、范围与验收依据

- Ticket：`.project-map/tickets/T-076-quality-chain-scoring.md`，`ready_rev: 1`，保持 open。
- 本卡：`evidence/2026-10-11-batch13/card-T-076-1.md`；唯一写入者 `s13-t076-1`。
- 计划检查时 HEAD：`ffe7ecb85e9e224d5917183b48754f15ac0c5ba6`。实施前重新核对；若 HEAD 已变化，记录新的完整起点并检查相关差异，不把当前号冒称实际测试起点。
- 已读：AGENTS.md、CONTEXT.md、intent.md 第三阶段、MAP.md、T-075/T-076、原生编排 spec 第 2、3、5、6、8、9 节与 Test seam；T-075 完成报告 `20261011T094922Z-executor-report-001`；两个缺口上报；卡 4 PLAN 第 8 节及卡 3 保存点清单。
- 开始检查：`project_map.py status` 退出 0，0 problems、0 stale。已有两份 batch11/batch12 `controller-poll.log` 修改属于他人，本卡不改、不暂存。

目标是补四个明确缺口：实际模型尾注、多回合身份、只读事件重建检查、五类产品变异体。验收逐项采用本卡六条完成条件；不把 T-076-2 的质量串、打回回写、产品 reviewer 会话和打分并入。也不做 T-077/T-078/T-079，不改变存储，不改 `acceptance/`、scripts、地图、spec、全局配置或 fork。

**Tracer bullet**：先让一条受管交付贯通“启动记录 → 本地原生回合事实 → Git 尾注 → 后台 submit → verify/integrate → 回执回合 → run/reclaim → 独立 Git/SQLite 读回”，再补确定性反例和变异体。**Deep modules**：沿用 Panes、门禁和现有测试入口，不增加 provider、重试层或第二套门禁。**Ubiquitous language**：沿用 CONTEXT.md，明确受管运行身份、原生会话、领导进程与交付回合的不同用途。

## 2. 尾注的取值来源

### 已观察与未知

`panes.ts:createThread` 已把模型/强度写入 argv 和启动记录的 `model_requested` / `effort_requested`，但给 hook 的 `A2A_MODEL` / `A2A_EFFORT` 写死为 `unknown`。`hook.py:add_trailers` 只读这两个变量。`Panes.scan` 另从根 CLI rollout 的 `turn_context` 取得实际模型/强度。当前 `run_worker_delivery.py` 还把两个 unknown 当作预期，需要按本卡合同更新，不能拿该旧预期证明修复。

**请求的模型**来自任务卡、启动 argv 和启动记录；**最近一轮的实际模型**来自本原生会话最新回合的结构化 `turn_context`。二者即使相等也必须保留不同来源。启动请求本身不能证明 CLI 未在会话内换模型，也不能证明实际 Fast tier。

### 拟采用的最小路径

1. 在每会话环境中传入启动记录中的请求模型/强度，并用带 `REQUESTED` 的名称区分；启动记录仍保存原始请求、环境白名单和 argv。
2. 提交 hook 在沙箱内读取自己的隔离 `CODEX_HOME/sessions/` 中、由 `CODEX_THREAD_ID` 绑定的根 CLI JSONL。只接受 `session_meta.source=cli` 且原生会话号匹配的唯一文件，不取辅助会话、不按文件 mtime 选“最新”。
3. 按文件顺序解析完整 JSONL，定位最近回合及其 `turn_context`，取实际 `model` 与 `effort` / `reasoning_effort`。当前回合没有上下文时，不能沿用前一回合或启动请求。保持现有 spec 的 unknown 语义；本卡真实正例若仍为 unknown，则验收 INCOMPLETE 并报告。
4. `A2A-Model` / `A2A-Effort` 使用上述观测值，其他七项尾注继续从受管环境取值。保留重复尾注替换、换行拒绝、原仓库 hook 转发，不连接后台 socket，不要求扩大沙箱写权限。
5. 证据保存被选中的文件、完整记录位置、原生会话/回合号和取值来源；真实验收另外从后台已归档的 `native_record` 独立读回，对照提交时的回合，而不是事后回执回合。解析错误或身份歧义明确拒绝，不兜底到请求值。

实际读取权限与记录落盘时序尚未实测。最小探针是同一受管真实回合中的一次提交：能读取匹配根回合的上下文，且尾注等于独立记录的实际值，才算通过；读取被拒、上下文未落盘或绑定含糊则保留现场，交主控，不换权限、不重试付费回合。

**REALITY GATE: INCOMPLETE。** GOAL / NON-GOALS 见第 1 节；DECISION 是实际回合事实能否通过本地文件可靠进入提交 hook。OBSERVED 是启动请求与原生记录已有不同来源；MEASURED 目前只有地图检查；INFERRED 是本地读取可以免除 socket 连接；UNKNOWN 是沙箱内读取权限与提交时的记录时序。PROBE 如上，由本 worker 准备、执行主控沙箱外执行，证据放本卡全新运行目录。DECISION CONSEQUENCE：探针不成立就停下，不用启动请求冒充观测；NEXT ACTION 是交接本计划，批准后取得红态。

红态先用起点源码的启动环境和真实 Git `prepare-commit-msg` 链做确定性夹具：提供独立写好的根回合记录，要求尾注为记录中的实际模型/强度，起点应输出 unknown 而失败。请求值与实际值不同、两个回合模型不同、辅助会话有诱导记录、缺当前上下文、重复尾注与注入拒绝分别验证。此红态不消耗真实回合；真实提交另作外部边界证明。

## 3. 多回合身份与交付绑定

### 起点缺陷与不可放宽的检查

`core.ts:checkThread` 把 `live.turn` 与 `attempt.turn_id` 比较；observeRun、waitForIdle、reclaim 均使用它。submit 将交付回合写入 `attempt.turn_id`，Panes 遇到新 `task_started` 又更新当前 turn。按该路径推断，同一原生会话的回执回合会被旧检查误判为 identity_conflict。旧上报仅是静态发现，本卡先取得可重复红态。

拟将两种事实分开：

| 事实 | 来源与持久绑定 | 使用位置 |
| --- | --- | --- |
| 原生会话与领导进程身份 | Panes 拥有的 launch/thread、shell、Codex 前台进程组领导者及根原生会话；由后台观察，调用者不能自填成权威 | run 的观察/等待；reclaim 停止前与停止、归档后的确认 |
| 本次交付绑定的回合 | submit caller 的当前活动回合，与根原生记录、受管 task/attempt/session/fence/spec 和具体候选绑定 | submit、Stop 转交、交付及验收证据；不能被回执的新回合覆盖 |

实现落在 `panes.ts`、`gates/core.ts` 和必要的 `src/contracts/` 类型中：给 GateRuntime 增加明确的运行时身份事实；在事实首次可核对时绑定并保存。启动尚无原生会话/领导者不能冒称已核实；事实丢失、换领导者、换原生会话或换工作区都不得成为成功。run/reclaim 改核对稳定运行身份，不用当前回合等于交付回合来替代它。停止后的读回使用同一绑定身份和已确认的停止事实，不能因 ps 已看不到进程而重新猜身份。

submit 仍核对当前活动 caller、live 回合、工作区、候选 HEAD、干净工作区、session/fence/spec/attempt；保留旧 Stop 不能消费新请求、伪造 token/native session、旧 attempt 拒收。当前卡只允许同一交付之后的回执新回合，不提前实现 T-076-2 的改候选/打回重交协议。交付回合不为通过 reclaim 而改成回执回合。

### 红绿与反例入口

- 新增 `workbench/tests/test_multiturn_identity_e2e.py`，经实际产品 CLI → socket → serve → 门禁运行。受控外部运行时给出明确身份事实与两个不同回合，不用模型输出作答案。
- 起点正例：turn A 显式 submit，完成后同一身份进入回执 turn B，再 idle。分别测试 `run --wait-seconds <显式期限>` 的完整路径与单独 `reclaim --attempt <原 attempt>`；两者应通过，起点因 identity_conflict 失败。单独 reclaim 必须测试第一次有效回收，不能用已回收后的幂等返回当身份证明。
- 候选同信号转绿；核对 run outcome、reclaimed、只停止/归档原 thread，候选与验收的交付 turn A 不变。
- 反例逐一替换原生会话、领导者、工作区、launch/capability 或 attempt；即使使用相同当前回合也要拒绝，且没有 oracle、集成或错误回收。领导者不变时辅助工具出现仍应通过。负例保存事件、Git 引用与外部运行时操作记录。
- `acceptance/test_run_e2e.py:test_new_native_turn_is_not_owned_even_with_old_thread_present` 目前用 `leader-changed` 夹具通过换 turn 模拟换领导者。若接口需要适配，只在 `workbench/tests/daemon_acceptance_host.ts` 等测试宿主中提供明确的受控所有者事实，保留原业务方法、输入与拒收断言；不在产品中做缺字段回退或“信任所有新回合”。若无法保留其独立含义，停下报告，不改 acceptance。
- 真实正例复用第 6 节的两回合交付。用完成条件的可控 barrier 让回执回合 B 完成后再放行 verify/integrate，保证 run 的等待/回收确实见到新回合，而不是偶然赶在回执前回收。

## 4. 只读一致性检查

拟新增 `workbench/src/stateConsistency.ts`，提供离线命令：

```sh
node workbench/src/stateConsistency.ts --state /绝对路径/夹具状态目录 --output /绝对路径/card-1/新目录/consistency.json
```

这是只读诊断，不新增 claim/submit/集成入口。数据库以 read-only 模式打开，不实例化会建表/迁移的 A2AGates 或 Membership，不修表、不补事件、不自动恢复。报告写到证据目录，不写状态目录。不增加依赖。

### 重建与逐表比较

只从 `events` 按 seq 从零重放：完整快照直接替换对应历史对象；增量事件依据已有合同显式应用状态转换，保留被撤销 attempt 和旧 verification，不能只看当前 task。转换清单以 `save-point-audit.md` 为清点线索，再核对本起点所有保存点。包括 claim/dispatch、turn 绑定、submitted、verification intent/result/interrupted、completion intent/check、integration intent/conflict/reconciled、revoked/reclaimed 和完整 run 事件。

先重建，后读取待比表；不得把当前表行、生产 load()/save() 输出或当前表缺失字段补到重建答案中。比较主键集合、缺行/多行及每个 JSON 字段的语义值，键顺序不算差异；数组顺序、null、缺字段、完整代码/身份绑定都保留。不算 hash。

| 表/库 | 检查与报告边界 |
| --- | --- |
| `state.sqlite3: tasks` | 从事件重建任务完整当前状态与嵌入的 attempt/verification/intent |
| `attempts` | 比较当前及历史 attempt，包括已撤销、已回收记录 |
| `verifications` | 比较每个验证记录、命令意图/结果、结束状态，不沿用前一条完成条件结果 |
| `runs` | 由 run_started/bound/phase/finished 完整记录重建 |
| `attachments` | 重建可观察的 attached/reclaimed；对 creating 及事件窗口明确标出无法重建的行/历史 |
| `membership.sqlite3: memberships`、`session_presets` | 单独读取并报告；只有事件确实含完整可推导信息时才能说一致，不能用最终行倒推 revision 或 preset |
| 其他覆盖写表 | 清点 `user_input_checkpoint`、`role_permissions` 等，列出来源、覆盖边界与未覆盖原因；不把未检查表默认为一致 |

每表列数据库路径、事件截止 seq、行数、差异字段、相关事件、原因与结论（“一致”“不一致”“无法由现有事件重建”）。没有行注明空表；未知事件或缺重建规则如实标不可判定，不静默忽略。总结果不能把不可重建或未覆盖上调为全库 PASS。

### 三个嫌疑点逐一取证

1. **attachment creating 没有事件**：在受控外部 runtime 的 attach 创建边界暂停，读回 creating 行与事件清单；再以创建失败的隔离夹具保留该行。仅从事件无法重建就明确报告，不能把后来的 attached 回填成早前 creating 历史。
2. **saveAttachment 与 attached 不同事务**：核对两个写入点，测试夹具只在自建服务该边界冻结/中断，保留“行已 active、attached 事件未写”的现场；报告缺事件。最终正常表一致也不能证明该窗口原子性。
3. **memberships/session_presets 在另库、不经 save()**：对照同一交付的两个库与事件，核对内容、revision、preset 和写入顺序。事件未记录完整变更就报告不可重建，不能因当前 task 可查而说另库一致。

附加检查器反事实：在完整交付库的独立副本中分别只改一个 task/attempt/verification 字段或删一行，events 保持原样，检查器须精确报差异。该改动仅是测试输入，不接回产品库。先列孤立检查器失败方式：漏表、漏历史行、反向借当前表补答案、漏增量状态转换、忽略未知事件、把不可判定算一致、诊断时写源库；再写测试。

起点红态是新检查器入口/功能不存在，属于合同红态，不冒称某张表已经运行证明不一致。候选在一个完整交付夹具的静止快照上输出逐表结果；SQLite 使用只读源的 backup 保留 WAL 内容，不直接复制运行中的单一主库文件。另库快照在无写入时取得，记录各自截止点，不宣称跨库同事务。

**发现实际不一致或不可重建时，保存报告并停下交执行主控；不改存储，也不自行决定继续其余实施。** 本卡接受如实报告结果，不要求把已知历史缺口修成一致；其余完成条件未运行时仍为 INCOMPLETE。

## 5. 五类产品变异体

以 T-075 卡 4 PLAN 第 8 节的原五类为准，不用 fence/CAS/锁变异体替代。每个变异体从一个冻结源码副本单独产生，保存单点 diff、实际加载源码、命令、原始退出结果及失败的业务断言。对照候选同场景先通过，变异体必须在该业务断言失败；导入、构建依赖、权限、缺文件、探针超时均不是检出。

| 类别 | 隔离副本改什么 | 独立业务断言与入口 |
| --- | --- | --- |
| 省略关闭期间字节 | 在输出读取/回放路径跳过一段已由夹具写定的离线区间，保留合法进程与响应，不改 oracle | 真实 Electron 关窗、夹具 trace 追加中文/ANSI/序号、重开；收到的 bytes 必须逐字节等于独立 trace 高水位区间。经 preload → daemon pane_output，不只测解析函数 |
| 窗口关闭误停后台 | 仅在隔离 `app/main.ts` 的关闭处理加入对该夹具 `daemon_stop` 的调用 | 实际关闭 Electron 后，同一后台 PID 应仍存在、daemon_status 可用；失败必须先保存为“关闭窗口导致后台死亡”的断言，不计清理失败 |
| 缺信号标 idle | 把 Panes 历史/缺结构化信号状态的 unknown 改为 idle，不改变 gate | 当前 CLI pane_status 与实际窗口应显示 unknown；终端里的 idle/done/accepted 与 OSC 标题不能解除未知。沿用离线 trace 独立断言 |
| 重启自动续跑或标成功 | 本卡选择同类中的“标成功”：重启投影错误地把尚 claimed 的任务报告 accepted，不启动新模型 | 经 CLI workbench_snapshot、独立 SQLite/Git 和实际窗口断言：重启仍保留原 attempt，门禁 claimed、执行 interrupted/unknown；不能把投影成功当业务完成 |
| 缺盘仍继续构建 | 仅在隔离 `app/build.mjs` 删除挂载校验，让它继续创建配置的构建根并成功构建 | 从产品构建入口调用、配置一个不存在且非挂载点的 volume 路径，应拒绝且不创建缓存/产物；变异体能构建并创建目录即业务失败。该路径放在真实已挂载外置盘的本卡专属槽内，避免反例真的把缓存写到内置盘；不卸载真实磁盘 |

后四项优先复用 `test_offline_trace_e2e.py`、`test_electron_e2e.py`、`test_daemon_recovery_e2e.py` 的外部观察面；在 `workbench/tests/` 补缺失的关闭区间、重启投影和构建 guard 场景及统一运行/变异准备脚本。离线 trace 明确是受控字节夹具，不冒称来自实时 PTY。第一、二项的运行都操作测试自己创建的窗口和后台。

正式源码不改 `workbench/app/`。main/build 等变异只发生于 `/tmp` 隔离源码副本，由本卡 `workbench/tests/` 变异脚本生成；构建仍用标准入口和外置盘独立槽，不替换共享 dist、不在 dist 链接源码/依赖。

起点先清点并实跑五个指定变异体的适用现有断言，逐项登记“已有断言检出”“未检出”“缺测试”。现有 `test_offline_trace_e2e.py` 已有 byte/unknown/关窗断言，因此不能预先宣称五项测试都不存在。若起点已有某类检出，就保留真实业务红态，报告其覆盖已存在；不删断言制造“未检出”。若主控要求该类也必须证明起点未检出，交主控处理这项红态口径，不擅自改验收。

## 6. 沙箱外交接与真实回合预算

批准计划后统一写 `card-1/outside-sandbox.sh`，分 `red`、`green`、`mutants`、`regression` 阶段，输出各自全新目录；不覆盖失败。可复现命令与精确参数写入每轮 command receipt。脚本准备好后回复 `T-076 OUTSIDE-SANDBOX READY` 并停下，由执行主控执行；本 worker 不申请提权、不提前运行其中部分。

下列都在脚本中列明：短 `/tmp` 路径下启动/停止隔离后台与 Unix socket；ps/前台领导者核对；真实 node-pty/Codex；Electron 与 capturePage；外置盘构建及反例；自建进程的信号和恢复；夹具 Git 写入；静止 SQLite 快照、归档和隔离 home 收尾。

**被测真实 Codex 总上限 3 个主 turn，计划使用 2 个：**

| 回合 | 用途 | 验收产物 |
| --- | --- | --- |
| 1 | 真实受管 worker 一次提交并通过 B 显式 submit | 启动 argv/记录、根 turn_context、候选完整 SHA、`git log -1 --format=%B` 尾注、submit 事件 |
| 2 | 本次交付回执的新回合，只确认回执、不新增交付 | 原生会话和领导者不变、回合号改变；Stop 后放行 oracle barrier，run/integrate/reclaim 及 Git/SQLite 读回 |
| 3 | 保留预算，未安排 | 不是自动重试许可；使用前向主控说明原因与累计数，等其明确决定 |

红态、伪造身份、检查器和五类变异体均用确定性夹具，不消耗模型回合。检查器的完整交付夹具可先用受控 runtime 跑通，避免已知存储缺口被发现前就花真实回合。独立源码审查不使用被测 worker、不向其派发新回合；由主控安排一次 fresh-context 只读审查，其会话与成本单列，不隐入本表。

固定被测 CLI 0.162.1、`gpt-6.1-sol`、xhigh，显式 `-c 'service_tier="fast"'` 与 `check_for_update_on_startup=false`；真实 tier 未观测时只报告请求值。每个实际 task_started 都计数，预算记录追加；启动失败、辅助会话和未完成回合分别保留，不删失败后重新计数。

CODEX_HOME 在 `/tmp`，仅复制 auth.json，只信任已核对的夹具根，仅 git add/commit 两条 allow prefix_rule。初始不装 hook；本卡运行所需 Git prepare-commit-msg、原生信号/Stop 转交 hook 的完整 argv 和授权引用写进脚本，**等主控逐次批准才安装/启动**。不写用户 ~/.codex 或 ~/.claude，不加 socket/网络权限。保持既有 B 文件转交通道，不重做 A/A2 探针。

后台脱离调用者进程组；只操作自己创建且已核对的进程。结束先确认后台、CLI、shell/子进程退出，再删除自己创建的完整隔离 home；凭据不进证据、tar 或 Git。不能确认退出就报告并保留现场，不误删。依赖/下载/构建缓存只在 `/Volumes/WD-Elements`；未挂载立即报错，不安装或回退。正式工作台、用户应用、Herdr server 和他人的夹具都不操作。

## 7. 实施检查点、回归、审查与交付

1. 主控批准本计划；复核 ready_rev、实施起点与授权范围。
2. 先写确定性信号与 outside 脚本，取得四项起点红态和五类逐项覆盖清单。产品修复保持 pending，直到对应红态成立；无关环境失败不算。
3. 在原责任层最小修尾注与身份；实现只读检查器；同信号转绿，发现存储不一致就按第 4 节停下报告。未知协议/产品失败亦保存并交主控；探针本身的错误可修，记录错误和新运行目录。
4. 一次真实两回合 Tracer bullet，五类候选对照与变异体业务失败；更新范围内 README，区分请求/观测与诊断边界。
5. 用 `workbench/tests/run_daemon_acceptance.py` 跑 coop/recovery/run 三套，要求 8/9/18、0 failures/errors/skipped。只为本卡证据位置增加测试运行器输出根参数，保留原业务方法和断言；当前 runner 默认输出在 T-075/card-5，不能将本卡结果混写到旧证据。
6. 冻结候选和运行源码，交一次 fresh-context 只读独立审查；应用 `behavioral-acceptance-review` 核对独立 oracle、红态、变异体与证据范围。若出现结构风险，按 `design-integrity-review` 的路由纳入同一完成检查点。审查发现先红后绿，修复 diff 交主控审；不把旧 PASS 复用到新候选，不自行追审。
7. 写中文 RESULTS，逐条列本卡六项完成条件、起点/完整候选版本、task/attempt/session/fence/spec/launch、命令/退出码、真实回合、失败和审查原文。T-076 只改 Resolution，写“T-076-1 完成，待 T-076-2；待主控关闭”，保持 open；未完成不能用这句话冒称完成。
8. 核对 `git diff <实际起点> -- acceptance/` 为空；运行下面的地图命令并保存证据。README 的 MAP Verified 若 stale，由执行主控处理，本 worker 不越界修改；收尾未齐则 INCOMPLETE。

```sh
python3 /Users/luckye/Documents/SKILLS/project-map-skill/project-map/scripts/project_map.py status --root .
find evidence/2026-10-11-batch13/T-076/card-1/ -type f -size +5M
```

超过 5 MB 的原始产物先压缩；仍过大则由沙箱外脚本归档到 `/Volumes/WD-Elements/a2a-evidence/2026-10-11-batch13/T-076/`，仓库保留中文摘要、重放命令和路径，不覆盖旧证据。仅 git add/commit 本卡授权文件与 T-076 Resolution，两条命令各自独立，核对本 worker 提交尾注，不 push。

最终交付行才使用 `T-076 DONE <PASS|INCOMPLETE|BLOCKED> <a2a commit>`。本轮按任务卡“先交计划，停下等我”的要求交接 PLAN，不进入实施。
