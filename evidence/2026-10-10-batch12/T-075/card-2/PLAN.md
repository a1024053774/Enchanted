# T-075-2 计划（待执行主控审定）

状态：**INCOMPLETE**。本轮只交计划；没有修改产品或测试，没有运行验收，也没有提交实现。收到执行主控审定本计划的决定后才开始红态与实现。

## 0. 范围、起点与证据

- 来源：本会话 `⟦主控 #15⟧`，任务卡 T-075-2；ticket T-075 当前为 `open / ready: yes / ready_rev: 2`。
- 开工时完整起点：`e5e7dbb841131935aac0bd061649a55e7a1e7d20`。后续 RESULTS 沿用这个起点，不以启动记录里的较早提交替换。
- 写入者：本 worker，派发身份 `s12-t075-2`。启动记录与实际供应商 tier 是两件事；此计划不声称证明实际 Fast tier。
- 目标：经唯一 CLI 生成、校验、保存并注册任务卡；按卡检查路径、完成条件和尾注；通过后以 CAS 将项目工作分支从 G 推到 M，拒绝覆盖未提交改动并留事件。
- 非目标：编排后台、PTY、真实 Codex 被测会话、Electron；S2 的独立审查产品功能、红态门禁、规则式检查、打回回写、打分；S3 的命名清理、冲突回写与自动重新验收上限。交付前一次独立代码审查仍按本任务卡执行。
- 修改范围：`workbench/`；本计划第 4 节列明的 `acceptance/` 适配及新增测试；`card-2/`；最终只追加 T-075 Resolution，保持 open。现在只写本计划与计划检查收据。
- 已有脏文件：首次检查发现 `evidence/2026-10-09-batch11/controller-poll.log`；阅读期间又出现 `evidence/2026-10-10-batch12/controller-poll.log`。均属于主控工作，不改、不提交、不据此清理工作区。
- session 开始地图检查：退出 0，`Problems (0)`、`Stale living docs (0)`。本轮结束再检查一次。

规范引用缩写（下文的 S2 等是**章节**，不是切片编号）：

| 缩写 | 规范及原句 |
| --- | --- |
| S2 | [native-cli spec 第 2 节](../../../../.project-map/specs/native-cli-orchestration-2026-10-10.md#2-任务卡)：完成条件为“能跑的命令；至少一条在派发前由执行主控写好”；“存进后台库；修改出新版本，门禁在任务注册时快照”。 |
| S2-B | 同节：“起点是认领时工作分支的头；唯一写入者是本 attempt 的 worker 会话”。 |
| S3-C | [第 3 节第 4 步](../../../../.project-map/specs/native-cli-orchestration-2026-10-10.md#3-一次交付怎么走)：“在工作分支当前头 G 上合并候选得 M，依次查路径边界、完成条件命令……提交尾注”。本卡只做派发指定的检查子集。 |
| S3-I | 同节第 7 步：“CAS 把工作分支从 G 推进到 M，不 push。分支被某个工作区检出时，在那个工作区里快进；会覆盖未提交改动时拒绝并上报，不 stash、不 reset。” |
| D26 | [T-072 Resolution](../../../../.project-map/tickets/T-072-traceability-scoring-retrospective-metrics.md)：逐个核对候选提交；无尾注为 action 用户输入、人工介入，来源“推断：缺尾注”；别的任务尾注打回。九个尾注字段见 spec 第 8 节。 |
| F | [managed-delivery](../../../../.project-map/specs/managed-delivery-2026-10-06.md)、[recovery](../../../../.project-map/specs/recovery-2026-10-06.md)、[supervised-run](../../../../.project-map/specs/supervised-run-2026-10-06.md)：本卡未改变的锁、fence、CAS、attempt 绑定、中断恢复契约。旧文档中的集成目标及输入格式仅按 S2、S3-I 替代。 |

### 事实与待验证事项

**observed**：`workbench/src/gates/cli.ts:10` 的 create 要求 `--base --oracle --instructions`；`core.ts:1821` 起复制两个文件，`core.ts:2168` 固定运行 Python oracle；`core.ts:41`、`:1125`、`:2296` 使用 `refs/a2a/integration`。`claim` 用注册基线，`dispatch` 用当前集成头（`:1991`）；任务卡 S2-B 要求两者都取认领时工作分支头。既有 `appendUserInput` 已在一次数据库事务内保存用户输入和派生 `human_intervention`，可在该层增加缺尾注来源，不另造记录通道。

**observed**：现有 8/9/18 套件都经真实 CLI、SQLite、Git；只有编排 runtime 是隔离替身。T-075-1 runner 支持把标签设成 `card-2/<新标签>`，无需修改卡 1 的 runner。Git 本机为 2.52.0；本地官方手册说明 `update-ref --stdin` 支持 `start/prepare/commit/abort`，prepare 锁定引用并核对旧值；`read-tree -m -u G M` 支持保护本地修改的双树快进。手册路径为 `/opt/homebrew/opt/git/share/doc/git-doc/git-update-ref.html`、`git-read-tree.html`；未联网。

**inferred / 待审方案**：采用结构化 JSON 任务卡和 argv 完成条件，避免解释自然语言“是否像命令”；采用 Git 原生引用事务配合双树快进，避免先更新分支却留下旧索引。两项方案的具体表示由本计划送审，不冒充 spec 已逐字段规定。

**unknown**：引用事务与检出 worktree 的组合在本机的实际失败、中断窗口。批准后先做第 3 节探针；不以阅读手册代替真实验证。探针失败就停下交主控决定，不换成 reset、stash 或弱化 CAS。

**REALITY GATE：INCOMPLETE**。规范和调用点已核对；集成方案尚缺探针，计划尚待批准。用 **Ubiquitous language** 沿用任务卡、attempt、人工介入等词；用 **Deep modules** 把校验、快照与 Git 副作用留在门禁核心；批准后先做第 7 节的 **Tracer bullet**。

## 1. 任务卡取代 oracle 和 instructions

### 唯一受管任务入口

拟将注册改为：

```text
node workbench/src/gates/cli.ts --state ABS_STATE create
  --task CARD_ID --repo ABS_REPO --branch refs/heads/main
  --card-version N [--project PROJECT_ID] [--title TITLE]
```

`CARD_ID + N` 指向同一 SQLite 库中已通过校验的任务卡版本。门禁注册时再次校验并保存不可变注册快照；没有该版本、编号不符或卡不合法就拒绝。`--branch` 必须指向已存在的本地工作分支，不接受 detached SHA、远端跟踪引用或隐含默认分支；同一项目/仓库的受管任务不能登记不同的工作分支作为第二集成目标。

删除 create 的 `--oracle`、`--instructions`、`--base` 路径及 `task.oracle/task.instructions` 的产品读取，直接替换所有范围内调用方，不保留自动转换、兼容开关或第二入口。`attach --instructions` 是普通会话提示文本，不是受管任务注册入口，本卡不改它。旧状态记录可供 status/events 追溯，但缺任务卡快照的旧任务不能被静默补成新合同；本卡只用全新隔离库，不迁移正式数据。

### 命令的表示和执行

`completion_conditions` 为非空数组，每项是 `{ "argv": ["可执行文件", "参数", ...] }`，通过条件统一为退出 0；自然语言目标另放 `goal`。不接收以说明文本代替 argv，不用正则或关键词判断语义。参数可以包含换行（例如 `python3 -c` 的独立程序），不能有 NUL。必要的 shell 脚本须显式写成 `/bin/zsh -c ...`，门禁不隐式拼 shell。

注册前检查 argv 结构和 executable 能否解析为可执行文件（PATH 中的名字固定为当时解析出的绝对路径）；相对仓库程序以明确解释器加相对文件参数运行。校验不执行完成条件。实际参数中的一个完整元素 `{worktree}` 在 verify 时替换为 M 的绝对 worktree 路径，不做任意字符串插值。所有完成条件的 cwd 都是同一个独立 detached M worktree。

按原顺序逐条执行；每条先持久 command_intent，再保存实际 argv、cwd、stdout、stderr、exit、开始结束和 task/attempt/session/fence/spec/card-version/G/C/M/verification_id 关联。全为 0 才 verified。非零继续沿用公开拒绝码 `oracle_failed`，事件同时标明检查项为完成条件及序号；这个错误码不代表保留旧 oracle 入口。超时、缺退出结果和中断仍按现有 unknown/interrupted 语义处理，不把结果不明写成失败退出码或通过。

独立分页 oracle 的内容不改。已有测试 helper 在注册前读取外部 oracle 文本，把全文放进 argv 中的 `python3 -I -B -c <冻结源码> {worktree}`；因此函数测试仍运行同一份独立 oracle，而其输入从“文件路径”变成任务卡命令本身。卡内全部 argv 字节随快照冻结，之后改变原 oracle 文件或任务卡源文件都不会替换注册命令。不引入新的 oracle 附件 API。

常规卡可用 `python3 acceptance/check.py` 等仓库命令；该文件自然来自被验收的 M。冻结的是执行主控选定的命令及卡合同，不声称冻结整个工具链或保证仓库里的测试一定独立；独立性由派发前完成条件和本卡独立验收保证。

### 不可变快照和认领时绑定

1. `task_card_versions` 以卡号、递增版本为唯一键，存完整 JSON、来源与创建时刻；拒绝 UPDATE/DELETE。保存新版本是 INSERT，旧版本字节不变。
2. create 在一个事务中冻结选中的完整版本，建立 task 与该注册快照的关联并记事件。此后 verify/dispatch 只读库内快照，不再读源文件或查询“最新版”。
3. S2-B 的起点与唯一写入者在注册前尚不存在：模板必须有这两个字段，值为明确的 `null`（待认领），不得假造 SHA 或 worker 身份。claim/dispatch 获取当时工作分支头，生成 attempt/session/fence 后，追加一份**已绑定快照**：合同内容原样继承，起点和唯一写入者由门禁填实。原注册快照不被改写。绑定记录不算执行主控修改合同，不另增 spec_rev。
4. `revise --spec-rev N [--card-version V]` 保持原来的撤销与递增版本门禁。未指定 V 时只改变既有 spec 代次；指定 V 才显式采用另一已校验卡版本，追加新注册快照，原 attempt/候选/验收失效。已 accepted、pending integration intent、非递增 spec 的拒绝不变。仅保存 V+1 不会影响正在运行的任务。
5. task card version、spec_rev、ticket ready_rev 分别保存，不把三种版本混成一个数。保存与采用新卡是执行主控操作，worker submit 不能带新合同或 passed 值替换它。威胁模型仍是同一用户下可信但会犯错的 worker，不声称 SQLite 文件能防恶意同用户改写。

### 路径边界

使用仓库相对路径，文件精确匹配，末尾 `/` 表示目录及其后代，`.` 表示整个仓库；禁止项优先。第一版不解释 glob、自然语言或 Git pathspec 魔法。拒绝绝对路径、`..`、空段、NUL 和歧义写法。

verify 得到 M 后，检查 `attempt.base_commit → C` 的候选净改动及 `G → M` 的实际集成净改动，避免只看 M 漏掉候选越界、或只看 C 漏掉合并影响。用 NUL 分隔、关闭 rename 推断的 Git diff 取得路径集合，覆盖新增、修改、删除、模式改变；rename 的旧路径和新路径分别检查，不跟随工作区符号链接去读库外文件。失败记 `path_boundary_failed`、路径、命中的允许/禁止规则、卡版本及 G/C/M；后续完成条件不运行，不能 verified/integrate。

## 2. 尾注核对和人工介入

核对范围：`attempt.base_commit..C` 的全部提交，包括合并带入的提交，不只看 HEAD 或 first-parent；不把门禁构造的 M 当作 worker 新提交。提交清单、完整 SHA 和解析结果入事件。用 Git `interpret-trailers --parse` 解析正式 trailer 区域，不从提交标题、作者名或正文关键词推断身份。

| 分类 | 判定与处理 |
| --- | --- |
| 本 attempt | 九个 `A2A-*` 字段各出现一次且非空；`A2A-Task == task_id`、`A2A-Attempt == attempt_id`、`A2A-Session == session_id`、`A2A-Role == worker`。这四个字段决定归属。fence/spec 继续由 submit/verification 的正式身份绑定检查，不能靠 trailer 自报替代。 |
| 追溯字段 | 记录 `A2A-Tool`、`A2A-Model`、`A2A-Effort`、`A2A-Native-Session`、`A2A-Launch`；Tool 应包含 CLI 与版本，Model 拿不到可写 spec 允许的 `unknown`。本卡不建启动器，不能声称凭文本证明实际模型、tier 或原生会话；与真实启动记录的联接留卡 3。 |
| 别的任务 | 任何正式 `A2A-Task` 指向别的 task，直接 `trailer_task_mismatch` 拒收，记 offending commit、期望/实际身份；即使 HEAD 是正确尾注也拒绝。 |
| 同任务旧身份或坏尾注 | attempt/session/role 不符、只填一部分、重复或空字段，均以稳定错误码拒收并记事件；不能当“没尾注”降级成人工提交。字段不符的错误优先记录归属冲突。 |
| 完全无 A2A 尾注 | 按 D26 推断为用户本人提交；添加 `form: action` 的用户输入，来源标签精确为 `推断：缺尾注`，certainty 为 inferred，关联 project/task/attempt/session、commit、卡版本及检查事件。从该输入派生 `human_intervention`。不因此拒收，不阻止 verified/integrate。 |

在现有 `user_inputs`、`user_input_events` 与 `appendUserInput` 层扩展 `commit-trailer` 来源及 `inferred` 标记，不伪造 thread message，不写 Herdr 期用户输入文件。输入与介入在同一数据库事务内追加；以 `(task, attempt, commit, 缺尾注来源)` 去重，verify 重跑不重复计算同一次人工介入。独立检查需要读到输入 ID 和介入对它的引用，而不是仅在一条错误字符串里找到“人工”二字。

缺尾注记录只说明规范要求的推断，不把推断伪装成观察到用户键盘输入。有别的任务尾注的提交绝不进入上述推断分支。

## 3. 工作分支集成与中断恢复

### G、C、M 和唯一目标

- `integration_ref` 固定为注册的 `refs/heads/<工作分支>`。create 不写分支；claim 和 dispatch 都从此分支当时头建立 attempt。
- verify 在此分支当前头 G 上合并冻结候选 C，产生 M；能快进时 M=C，否则保留真实合并树及父提交。M 的 worktree 内完成本卡检查；不在用户检出目录里跑验收。
- integrate 再核对原 task/attempt/session/fence/spec/card snapshot/C/verification/G/M；要求 G 是 M 的祖先。G 已变且尚无 intent 时仍返回 `integration_conflict`，作废旧验收；自动重新验收与次数上限不在本卡实现。
- 产品不再创建、读取或更新 `refs/a2a/integration`。历史仓库中已有该 ref 只留作历史，不自动删除、不镜像到工作分支、不让它成为备用目标。新夹具从头到尾不出现该引用；另加历史 ref 哨兵证明集成未写它。

### 提议的 Git 操作顺序

1. 在现有任务级操作锁内，读取 `git worktree list --porcelain -z`，定位工作分支实际检出目录（包括 linked worktree）。核对目录归属、symbolic HEAD 和头值；多个强制检出、目录不可达或状态无法解释时拒绝并留事件，不猜一个目录。
2. 持久同一个 integration intent，包含原身份、卡快照、G/C/M、目标 ref、检出目录及即将执行的 Git 协议。Git 更新前一定已有 intent。各阶段结果追加为事件，不改写意图输入以迁就恢复。
3. 用真实 `git update-ref --stdin` 事务排队 `update <工作分支> M G`，`prepare` 核对并锁住旧值。检出时还验证并锁定该目录 HEAD 的 symbolic ref（本地 Git 支持 `option no-deref` 加 `symref-verify HEAD <工作分支>`），防止目录切换后写错 worktree。无检出目录也使用同一引用事务，不另设集成目标。
4. 有检出目录时，在该目录执行 `git read-tree -n -m -u G M` 预检和 `git read-tree -m -u G M` 实际双树快进；不使用 reset、stash、强制 checkout 或先 CAS 后放任旧索引。先显式验证 `G <= M`，因为 read-tree 自身不是祖先检查器。
5. 若暂存、未暂存或未跟踪文件会被覆盖，abort 引用事务，返回拒绝并保留原修改、原引用与诊断；无冲突的本地修改应原样保留，不能用“工作区必须全干净”替代 S3-I。调用的 Git 命令、stdout/stderr 和冲突路径均有事件。
6. 快进成功后发送 `commit`，CAS 使分支从 G 到 M。读回 ref、symbolic HEAD 与本次触及路径的索引/文件状态，再记 `integrated`、accepted。无检出目录时只有引用副作用。Git 结果不明或中途 I/O 失败时保留 pending intent / `needs_reconciliation`，不猜 accepted，不强制回滚本地文件。

Git 的引用与文件系统不是一个原子事务；因此必须验证下面的窗口，不能用“已经拿到锁”宣称恢复正确。保证范围沿用 F 的单机、可信参与者，不宣称能阻止任意外部程序在任意纳秒直接改磁盘。

### 保持 F 的恢复判定

| 重新调用 integrate 时 | 要求 |
| --- | --- |
| 引用仍 G，worktree 未快进 | 核对原 intent 与当前合法身份，恢复同一意图，重新执行受保护快进与 CAS；不新建竞争 intent。 |
| 引用仍 G，worktree 已全部或部分推进 | 核对同一意图；双树规则能够安全继续且保留本地修改时继续。无法确定、安全继续失败或尚有原 Git 执行者/锁时拒绝并保留现场，不删锁、不 reset、不把锁释放当验收。 |
| 引用已 M，数据库尚未 accepted | 按原意图核对；只补记账，不再次写 Git、不新增 reflog。必须在探针中证明正常 after-CAS 窗口已完成目录更新；异常目录状态保持待核对。 |
| 第三个值 X 或引用消失 | `needs_reconciliation`；原 intent、身份、引用与历史保持，revoke/revise 不能绕过。 |
| accepted 重放 | 同 attempt 幂等；旧 attempt 仍须先被拒，不能靠 accepted 分支跳过身份检查。 |

### 批准后第一个探针

负责人为本 worker；证据 `card-2/probe-git-<唯一标签>/`。在 /tmp 新建真实 repo、工作分支与 linked worktree，不改项目 Git 配置，用进程环境提供作者信息。执行上面的原生 Git 协议并保存每条 argv、stdin、返回值、索引、文件原文、ref/reflog。

通过条件：干净和无冲突脏文件都能正确快进；覆盖型暂存/未暂存/未跟踪文件被拒且原文保留；在 prepare 前另一个写入者把 G 改成 X 时 CAS 拒绝；prepare 后对方不能改被锁 ref；中断在目录更新前、目录更新后 CAS 前、CAS 后记账前，均符合恢复表。失败/未知即停止该路线，由主控决定，不写兜底实现。涉及 ps 与故障终止的探针按沙箱外交接流程由主控执行。

## 4. 8、9、18 项已有测试的改动白名单

本节列的是旧断言与新断言的**允许差异**，不是允许整文件改写。现有分页预期值、身份/锁/重放/超时/回收/事件前缀的判断都不放宽。保留原测试名称便于核对，名称里的 oracle 表示独立判据，不构成保留旧产品入口。

### 4.1 公共夹具和具体断言变更

| 编号 / 位置（起点版本） | 旧输入或断言 | 新输入或断言 | 依据 |
| --- | --- | --- | --- |
| A1 `test_coop_e2e.py:27,62,142`，供三套继承 | 初始分支名由 Git 默认；create 收 base、oracle、instructions；ref/reflog 查 `refs/a2a/integration` | 夹具显式建 main；用任务卡保存和 `create --branch refs/heads/main --card-version 1` 注册；所有原 ref/reflog 断言指向 main。spec_rev=1、持久库、重复注册拒绝不变。 | S2、S3-I |
| A2 同文件 `test_concurrent_claim...:307` 的第二次 create | 通过旧参数重复注册，要求业务状态不变、拒绝事件存在 | 用同一已保存任务卡版本重复 create；原断言不变。不会把重复 card_save 失败当重复 task create 证据。 | S2；F 的 task_exists 不变 |
| A3 同文件 `test_good_candidate_uses_oracle_snapshot...:400` | 注册后改外部 oracle 源文件仍成功，证明复制 oracle | 注册后把任务卡源文件中的命令改成 exit 23，同时另存 V2；原 task 仍运行 V1 的冻结命令。原 oracle 文本在注册前已放进卡内，改外部文本也不能影响它。保留一次集成及重放不增加 reflog 的断言。 | S2“注册时快照”“修改出新版本” |
| A4 同文件 `test_baseline_change...:454` | 外部提交先推进默认用户分支，再手工 update-ref 受管 ref；integrate 返回 integration_conflict | 外部提交本身推进工作分支，去掉已多余的第二次 update-ref。原错误码、ref/reflog 不再改变、不能 accepted、拒绝事件断言全部保留。 | S3-I；F 的 CAS 不变 |
| A5 `test_run_e2e.py:233` 与 `test_transient_tool_activity...` 间接复用 | `HEAD == original_head`，文案 User branch remains at its original head | `original_head == G`；成功后分支 HEAD=M（该夹具可快进，M=C），检出目录的已提交内容及索引对应 M。原 only_own_close、单 prompt、业务 oracle 和 worktree 保留断言不变。 | S3-I，直接取代“不更新任何用户工作分支” |
| A6 `test_recovery_e2e.py:135` 与 `ORACLE_BARRIER` | barrier 包装外部 oracle 文件，create 冻结该文件 | create helper 把同一 barrier + 同一 oracle 的全文放进任务卡 argv；保持候选目录为 `sys.argv[1]`，pid/ppid、屏障、退出结果和故障对象不变。 | S2、S3-C；F 的独立 oracle 不变 |
| A7 同文件 `test_interrupted_verify...:514` | frozen_keys 枚举 oracle/oracle_path 与单 command_intent 等输入 | 将已删除产品字段替换为任务卡注册/绑定快照标识、card_version 及完整命令列表；仍逐字段证明中断前输入未改，原 G/C/M/身份/worktree 键保留。旧结果未知，新执行完整退出 0、新 ID/目录、事件前缀、旧目录保留全部不变。 | S2；F recovery 第 2 条 |
| A8 同文件 `GIT_BARRIER:76`、`cas_records`，所有 CAS 场景 | 识别 `git update-ref REF M G` 的 argv，在调用前/后屏障；只记录 argv | 支持唯一新 `update-ref --stdin` 协议，记录 stdin；before 屏障必须位于真实 CAS 事务生效前，after 在 commit 成功及 ref=M 后。仍只包装真实 Git、只终止所属 CLI，保持原 CAS 次数、reflog 增量、锁和意图断言。不能以屏障没命中算业务红态。 | S3-I；F recovery 第 3 条 |
| A9 同文件 `unknown_reference:596-605` | 在默认分支外部 commit 后，再 update-ref 受管 ref 为 X | X 的外部 commit 已写工作分支，删去第二次同目标 update-ref；其余 needs_reconciliation、历史前缀、原意图、无重试/写入断言不变。删除引用反例改为删除工作分支；快照先留一个 detached 保留引用，保证 `show-ref` 不因空仓库误报夹具故障。 | S3-I；F recovery 第 3 条 |
| A10 `workbench/tests/test_cas_race.py:29`（35 项之外） | 外部 commit 后再 update-ref 私有集成 ref | 外部 commit 直接推进 main；保留外部 X、拒绝覆盖、不能 accepted 的原断言，屏障使用 A8。 | S3-I；F 的 CAS 不变 |

其他准备调整限于上述入口变化：公共 helper 生成 13 字段卡；原候选没有尾注的仍按 D26 推断，不能为了减少介入事件而改写所有旧候选提交；新增正例单独带完整尾注。`oracle_failed` 的公开错误预期不改。`acceptance/entry/a2a_gates.py` 不需要改；native-entry/runtime 只有在上述命令参数确实要求时才作直接适配，不改模拟身份事实与 caller 校验。

### 4.2 逐场景核对索引

“不变”包括全部原业务断言；共同使用 A1/A6/A8 只改变真实输入/副作用位置，没有豁免相应断言。

| 套件 / 原测试名（均省略 `test_`） | 该场景的允许变化；其余不变 |
| --- | --- |
| 交付 1 `concurrent_claim_is_unique_persistent_and_task_specific` | A1、A2；唯一赢家、三个拒绝、持久身份与事件计数不变。 |
| 交付 2 `identity_gates_and_revocation_reject_old_verified_attempt` | A1；全部身份错误、撤销、旧 attempt 拒绝不变。 |
| 交付 3 `unverified_and_oracle_failed_candidate_never_changes_ref` | A1；oracle_failed、ref 不变、不得集成不变。 |
| 交付 4 `oracle_rejects_candidate_missing_limit_upper_bound` | A1；上界 101 的已知坏实现和拒绝断言不变。 |
| 交付 5 `good_candidate_uses_oracle_snapshot_and_integrates_once` | A1、A3；新颖分页输入、恰好一次与 accepted 后禁止撤销/改版不变。 |
| 交付 6 `baseline_change_after_verification_rejects_integration` | A1、A4；G 变更后拒收与保存事件不变。 |
| 交付 7 `submit_requires_clean_head_and_cannot_replace_frozen_candidate` | A1；工作区干净、完整 HEAD、冻结候选和后改 worktree 不影响验收不变。 |
| 交付 8 `spec_revision_invalidates_candidate_and_old_identity` | A1；revise 递增、旧身份拒绝、重领和不变历史不变。 |
| 恢复 1 `live_verify_excludes_verify_and_integrate` | A1、A6；operation_busy、无第二 oracle、原执行继续不变。 |
| 恢复 2 `live_integrate_excludes_verify_and_integrate` | A1、A6、A8；无第二 CAS、同 intent、锁语义不变。 |
| 恢复 3 `interrupted_verify_gets_new_id_worktree_and_full_oracle` | A1、A6、A7；完整新 oracle、未知旧退出、保留现场不变。 |
| 恢复 4 `before_CAS_recovers_same_intent_once` | A1、A6、A8；G 状态下同 intent，恰好补一次 CAS/reflog 不变。 |
| 恢复 5 `after_CAS_recovers_bookkeeping_without_Git_write` | A1、A6、A8；M 状态下只补记账、零新增 CAS/reflog 不变。 |
| 恢复 6 `after_CAS_external_X_requires_reconciliation` | A1、A6、A8、A9；X 保留、拒绝、不能撤销绕过不变。 |
| 恢复 7 `after_CAS_deleted_ref_requires_reconciliation` | A1、A6、A8、A9；引用缺失保持缺失、同 intent、零重试不变。 |
| 恢复 8 `interrupted_verify_revoke_reclaim_rejects_old_identity` | A1、A6；旧身份拒绝、只集成新候选、旧现场保留不变。 |
| 恢复 9 `interrupted_verify_spec_change_rejects_old_candidate` | A1、A6；旧版本失效、新候选独立执行、旧事件保留不变。 |
| 编排 1 `run_entry_point_completes_registered_task` | A1、A5、A6；新增工作分支实际快进预期。 |
| 编排 2 `transient_tool_activity_keeps_same_thread_owner` | 与编排 1 共用 A5；辅助进程不等于领导者替换的断言不变。 |
| 编排 3 `new_native_turn_is_not_owned_even_with_old_thread_present` | A1、A6；错误领导者保留、不得验收/集成不变。 |
| 编排 4 `verify_expected_attempt_uses_real_gate` | A1、A6；匹配 guard 才能 verified、不能提前集成不变。 |
| 编排 5 `integrate_expected_attempt_uses_real_git_gate` | A1、A6；匹配 guard 写真实工作分支且有 reflog。原值比较不变。 |
| 编排 6 `fixture_existing_dispatch_submit_oracle_integration_and_reclaim` | A1、A6；done 无效、显式 submit、一次 oracle、只关所属会话不变。 |
| 编排 7 `done_without_submit_hits_deadline_and_cannot_accept_committed_candidate` | A1、A6；期限、无候选记录、无 oracle/集成、保留提交不变。 |
| 编排 8 `concurrent_duplicate_run_has_one_prompt_and_one_attempt` | A1、A6；第二 run 立即拒绝、单次派发/attempt 不变。 |
| 编排 9 `invalid_wait_values_have_no_worker_or_business_side_effect` | A1、A6；所有非法值、无 run/worker/业务副作用不变。 |
| 编排 10 `replacement_attempt_is_not_verified_integrated_or_closed_by_old_run` | A1、A6；原 run 绑定、替换会话保留、不得验收/集成/回收替换者不变。 |
| 编排 11 `oracle_failure_is_not_success_and_reclaims_only_owned_thread` | A1、A6；真实非零退出、引用不动、只回收所属会话不变。 |
| 编排 12 `startup_blocked_preserves_scene_without_prompt_or_close` | A1、A6；无 prompt、不关闭不变。 |
| 编排 13 `post_prompt_blocked_preserves_scene_without_answer_or_reprompt` | A1、A6；无自动答复/重派发/关闭不变。 |
| 编排 14 `unknown_identity_cannot_succeed_or_close_replaced_worktree` | A1、A6；身份未知保留、不重试不变。 |
| 编排 15 `stale_verify_integrate_guards_preserve_current_and_accepted_state` | A1、A6；包括 accepted 后仍拒旧 attempt，幂等无写入不变。 |
| 编排 16 `reclaim_guard_targets_history_and_rejects_foreign_and_unknown_attempt` | A1、A6；历史回收不动当前，跨任务/未知身份拒绝不变。 |
| 编排 17 `matching_reclaim_guard_is_idempotent_after_automatic_success` | A1、A6；所属会话只关一次、状态/ref 不变。 |
| 编排 18 `attempt_guards_preserve_existing_live_operation_lock` | A1、A6；operation_busy、无第二 oracle、原操作可继续不变。 |

最终保存 `git diff e5e7dbb841131935aac0bd061649a55e7a1e7d20 -- acceptance/`，逐 hunk 标 A1–A9 或“新增测试”。超出白名单的必要变化先停下报主控，不能先改断言再补理由。

## 5. 新 E2E 反例、正例与反事实

新增测试放 `workbench/tests/`，经 `acceptance/entry/a2a_gates.py` 调真实 CLI，独立建真实 Git/SQLite 夹具。预期来自本卡与上表规范，不导入产品逻辑、不写门禁数据库制造成功、不从实现返回值生成答案。

共同断言：拒绝须非零、稳定错误码、事件追加；没有 accepted 或分支推进；旧事件前缀及合法身份保持。每次运行保存命令/输入、stdout/stderr、退出码、卡原文和数据库只读快照、Git refs/reflog/索引及相关文件原文。全部使用唯一目录并归档嵌套 repo；原失败现场保留，不登记 gitlink。

| 编号 | 输入及独立预期 |
| --- | --- |
| N1 路径 | 允许 `src/`，禁止 `src/private/`；同时提交允许文件和禁止文件。verify 必须拒绝，事件列出禁止路径，完成条件未运行。再覆盖目录前缀碰撞、rename 跨边界、删除与带空格路径，防止路径解析漏检。 |
| N2 完成条件 | 卡内独立命令核对合并后的两份字面内容；另一个命令显式退出 17。保存实际 17，返回 oracle_failed，不运行其后的命令；不能集成。超时/命令不可用单独记 unknown，不混作 exit 17。 |
| N3 外来尾注 | 候选中间提交带另一个 task 的九项尾注，最终 HEAD 带正确尾注。必须拒绝并精确指向中间提交，不能只查 HEAD；不生成缺尾注人工介入。另测同任务旧 attempt、重复/部分尾注拒绝。 |
| N4 缺尾注 | 两个候选提交中一个完全无 A2A 尾注、另一个正确。完成条件通过，正常集成。库里有 action 用户输入，来源精确为“推断：缺尾注”、certainty=inferred；human_intervention 指向该输入、该 attempt、该 commit。重验/重放没有重复输入与介入。 |
| N5 过期身份 | 经任务卡注册的新流程，fence 错误及 revoke 后旧 attempt 的 submit 各被拒并留事件，当前 attempt 与工作分支不动。保留原套件的错误码预期。 |
| P1 中等复杂度正例 | claim 基线 B 后，工作分支另有不相交提交成为 G；worker 候选 C 改允许路径，带本 attempt 九尾注。真实合并得到 M，完成条件必须同时读到 G 与 C 的内容、并确认 cwd/HEAD 对应 M。验收前分支仍 G，集成后为 M、父链包含 G/C；实际检出 worktree 和索引正确，事件全，重放无第二 reflog。 |
| P2 集成目录 | 分别检出 main 在主 worktree、linked worktree，另测工作分支没有检出目录。都只更新同一目标；其他目录/分支保持。无冲突的暂存/未暂存/未跟踪修改原样保留。历史私有 integration ref 保持原值，新库不创建它。 |
| N6 覆盖保护 | 集成前在目标 worktree 分别设置将被覆盖的暂存修改、未暂存修改、同名未跟踪文件。集成被拒且事件明确，main 保持 G，原文件和索引内容保持；不能 stash/reset。 |
| N7 CAS 与快进 | 在验收后和 CAS 读取后分别制造外部 X；不得覆盖 X。拒绝非 `G <= M` 的实际 Git 操作，用独立 Git 故障边界提供已知坏结果，不改 SQLite。新增目录快进前后中断窗口，连同原 recovery 套证明同 intent、恰好一次。 |
| N8 卡结构与冻结 | 缺必填字段、空非目标、空允许项、完成条件为文字/空 argv/不存在的 executable、八类以外 task_type、坏复杂度、缺陷修复缺对象、坏来源 ready_rev 被拒；保存 V2 后当前任务仍 V1；改源文件无效；显式 revise 采用 V2 后旧 attempt 拒绝，历史快照保持。13 字段与版本从 CLI/只读库读回。 |
| N9 起点绑定 | create 后主控推进工作分支，再 claim；起点必须是认领当时的头，不是注册头。唯一写入者由返回的受管身份写入绑定快照；撤销重领产生新身份，不覆盖旧绑定。 |

红态报告分两层，不能混淆：

- 起点原生 CLI 不认识任务卡命令。因此新增完整场景在起点执行会因新契约入口不存在而失败；原样保存，标为 **expected-red / 新接口缺失**，不声称已到达路径或尾注检查。不得为起点加“支持新卡”的产品兼容入口。
- 起点已有 fence、旧 attempt 和完成条件失败保护，相应旧流程测试可能 PASS，照实记录。新任务卡流程在起点失败，不表示这些旧保护原本有缺陷。
- 候选上要求每个新增场景到达自己的业务边界并通过。再使用下述定点变异体证明失败原因，不能只用起点的 usage error 证明业务检查有效。

至少三个独立变异体，使用候选副本，不改正在交付的源码：

1. 去掉路径检查：N1 必须因越界被接受或没有拒绝事件而失败。
2. 尾注核对放过外来 task：N3 必须因外来提交被接受而失败。
3. 绕过目标 worktree 安全快进/覆盖保护：N6 必须因分支已推进、用户内容被改或未拒绝而失败。若只删预检而 Git 自身仍拒绝，该变异体没有改变可观察行为，不能拿它充数；需要让实际写入丢失保护的变异体。

另复跑 CAS 定点反例，确保正确旧值仍在真实 Git 原子更新里；如为新恢复窗口加断言，也为该窗口建立定点坏实现。导入错误、依赖缺失、屏障没命中、超时型夹具错误一律不是有效变异杀伤证据。

## 6. 任务卡命令、13 个字段和版本

所有命令都在现有 `workbench/src/gates/cli.ts`，经 `A2AGates.call` 作为唯一写入者，不增 `scripts/` 入口。拟用扁平命令名以贴合现有 CLI：

```text
--state ABS_STATE card_template --task CARD_ID --repo ABS_REPO
  [--ticket ABS_TICKET] [--project PROJECT_ID]
--state ABS_STATE card_validate --task CARD_ID --card ABS_JSON
--state ABS_STATE card_save --task CARD_ID --card ABS_JSON --expected-version N
--state ABS_STATE card_show --task CARD_ID --card-version N
```

`card_template` 输出 JSON 模板；有 ticket 时读取其 id、ready、ready_rev，核对卡号由 ticket 号加序号构成，不能将手填 ready_rev 当权威。没有 ticket 时来源为 null、编号用项目短名加日期序号。编号分配在库内防重，调用者提供的 CARD_ID 是请求值，脚本验证/登记；不会修改 ticket。生成模板不是通过校验，执行主控必须填完合同字段。

`card_validate` 仅校验，输出字段级错误与打印的规则；`card_save` 再校验后以期望前版号 CAS 追加（首版 expected-version=0），返回卡号/新版本；`card_show` 精确读取版本，不默认悄悄选择 latest。注册只引用已保存版本；保存新版本不自动 revise 当前 task。

| 序号 | 中文字段 / JSON 键 | 校验与填写 |
| --- | --- | --- |
| 1 | 编号 `id` | 脚本验证和登记，与 CLI task 和库键一致；不能为空或复用其他卡身份。 |
| 2 | 来源 `source` | 有 ticket 为 `{ticket, ready_rev}`，核对就绪与正整数；没有 ticket 为 null，键仍存在。 |
| 3 | 目标 `goal` | 非空字符串；不机械判断“好目标”。 |
| 4 | 非目标 `non_goals` | 非空字符串数组，至少一条。 |
| 5 | 修改边界 `paths` | `{allow: [...], deny: [...]}`；allow 至少一项，deny 可空；按第 1 节路径语法。 |
| 6 | 完成条件 `completion_conditions` | 至少一个 argv 命令，由执行主控在派发前保存，缺失、自然语言字符串、空命令或不可解析 executable 拒收。 |
| 7 | 红态命令 `red_commands` | 可空数组；填写时使用同一命令结构；本卡只存储/校验，不提前实现 S2 红态门禁。 |
| 8 | 任务类型 `task_type` | 只能是：后端逻辑、前端界面、缺陷修复、测试、重构、构建与基础设施、文档、调研。 |
| 9 | 修复对象 `repair_target` | 缺陷修复必须为原任务卡号或完整提交号；其他类型可 null，不推测。 |
| 10 | 复杂度 `complexity` | 仅 S/M/L。 |
| 11 | 执行器 `executor` | `{cli, model, effort}` 全部非空；CLI 限本阶段 Claude Code/Codex；不把填写模型当实际运行证明。 |
| 12 | 起点 `base_commit` | 模板及注册为 null；认领后绑定快照为当时工作分支完整 SHA，由门禁填写。 |
| 13 | 唯一写入者 `writer` | 模板及注册为 null；认领后由 task/attempt/session/fence 及 worker 会话身份填实，不接受 worker 自填替换。 |

spec 的表格把“起点、唯一写入者”放在一行，实际按两个字段处理，因此共 13 个。schema 版本、卡版本、时间、注册/绑定快照 ID 是存储元数据，不挤占或省略这 13 个字段。可选字段的键仍输出；缺少必填键拒绝；未知键和类型错误拒绝，避免拼写错误被静默忽略。JSON 由标准解析器处理，不引入 YAML/Markdown 解析依赖。

任务卡全文从已绑定快照渲染进现有 dispatch prompt，替代 `task.instructions`；没有另存一份可独立修改的说明文本。角色卡附带、真实 CLI 投递文本及启动记录接线由卡 3 处理；本卡不修改 Herdr 派发脚本。

## 7. 批准后的顺序、收据和交付边界

1. 先保存起点、新测试合同预期及第 3 节探针原始输出。保留起点代码副本和所有失败现场，不改共享 checkout 的 HEAD。新流程全部在起点运行，按第 5 节如实分类失败。
2. **Tracer bullet**：一张卡经生成/校验/入库/注册/认领/带正确尾注提交/verify/工作分支 CAS 集成，完整事件可读回；该路径保留在生产代码中。随后加宽路径、尾注、脏目录与恢复反例。
3. 改动主要落在 `workbench/src/gates/core.ts`、`cli.ts`、`workbench/src/contracts/a2aGates.ts`；任务卡 schema/格式化可用一个职责完整的模块承载。补 `workbench/README.md` 当前入口，测试按第 4 节。不改依赖或安装，不联网；需要依赖就先停下报主控。
4. 在有意义的检查点跑相关测试，然后用卡 1 runner 跑 8/9/18 全套。以下是拟用的重现入口，标签每轮更换；旧 runner 的 `task: T-075-1` 元数据是其原样输出，卡 2 收据另记实际 ticket、起点、候选与输入，不伪改旧收据：

   ```sh
   /opt/homebrew/bin/python3.11 -B evidence/2026-10-10-batch12/T-075/run-acceptance.py coop card-2/green-coop-01
   /opt/homebrew/bin/python3.11 -B evidence/2026-10-10-batch12/T-075/run-acceptance.py recovery card-2/green-recovery-01
   /opt/homebrew/bin/python3.11 -B evidence/2026-10-10-batch12/T-075/run-acceptance.py run card-2/green-run-01
   git diff e5e7dbb841131935aac0bd061649a55e7a1e7d20 -- acceptance/
   python3 /Users/luckye/Documents/SKILLS/project-map-skill/project-map/scripts/project_map.py status --root .
   ```

5. 新测试与变异体 runner 放本卡目录或 `workbench/tests/`，每项在 RESULTS 给出精确重现命令。沙箱外检查不在 worker 这里运行、不申请提权：写 `card-2/outside-sandbox.sh`，保存 stdout/stderr/退出码的新标签，回复 `T-075 OUTSIDE-SANDBOX READY` 后停下，由执行主控运行。外置盘缺失时涉及构建/缓存的步骤明确失败，不回退内置盘。
6. 候选冻结后只做一次 fresh-context 只读独立审查。因本卡改变验收与公开门禁行为，按 behavioral-acceptance-review 路由检查独立 oracle、起点证据、变异体与断言白名单；不再加第二轮结构审查。原文存本卡证据目录。发现问题先拿到红态再修，修后由主控看修复 diff，不追审。
7. 最后写中文 RESULTS，逐项区分 PASS/INCOMPLETE/BLOCKED；保留所有未知、跳过与环境失败。只提交本 worker 的文件与 T-075 Resolution，提交带九项尾注；Resolution 写“T-075-2 完成，待后续卡，待主控关闭”，ticket 保持 open。地图必须 0 problems；若本卡引起范围外 living doc stale，上报主控处理，worker 不越界改地图/AGENTS/CONTEXT。

本计划的交接动作：保存并回读 PLAN，运行地图 status，回复 **`T-075 PLAN READY`**，然后停止。此时既不提交实现，也不写 T-075-2 完成结论。
