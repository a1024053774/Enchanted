# T-222：旧门禁套件的契约、覆盖缺口与迁移选项

研究截止：本次会话；源码固定在 `t222-legacy-suites` 的 `1e5f0a34888978a13b3eadc5381c75ba9236bb10`。工作目录为 `/Users/luckye/Documents/Code/a2a-worktrees/T-222`。本报告是中文日期研究记录，不是测试迁移授权，也不是 hc 切片的验收结论。

**PASS（研究交付）**：已逐一分析票面 7 组、17 个测试，查到契约变更来源，列出保留检查、其他覆盖及处置选项。**INCOMPLETE（当前运行保障）**：17 个套件沿用 T-219 的失败/前置阻断结论，没有重跑；本文列出的其他测试除两个 relay 离线测试外均未在本次会话运行。**NO_GO（证据使用）**：不能拿旧 PASS、模块导入、当前正向交付成功，替代这些失效反例或 hc 上的新证明。迁移、整份标历史、拆分都仍待用户裁定。

目标是回答“哪些契约仍有效、哪些检查有人守、hc 受管窗格开工前缺什么”。非目标是修改实现、测试、地图或历史标记。材料中尚不能确定的，是各套件越过现有首个失败后还会暴露多少问题、迁移后的实际工作量，以及 hc 受管路径的行为；均记为未知，不从当前实现倒推契约。

## 1. 阅读方法与证据边界

本文的源码、票面路径均相对上述 T-222 工作目录，`文件:行号` 均指该固定 HEAD。提交号是 Git 原文来源；带行号的旧票面若已被后票修订，按下文明确列出的修订关系读，不能单独当作最新契约。

覆盖表使用以下判定，避免把“测试文件还在”写成“检查还有效”：

- **有断言**：其他非历史测试确实构造了相应输入，并在具体断言检查该行为；本次未运行时，只能确认源码覆盖设计，运行状态为 **INCOMPLETE / 未复跑**。
- **部分**：只覆盖正例、子项、离线协议或观察器，不替代原来的完整场景。原检查其余部分明确写“没人守”。
- **没人守**：在本仓库现行测试中，未找到能够作为该项替代的检查；或者唯一相似入口已知失败、被前置挡住。这里不是断言产品一定有缺陷，而是缺少可用守护证据。
- **已取代**：旧预期与后续用户裁定相冲突，应换现行预期或保留为历史；不能通过放宽断言而不说明语义变化。

T-219 证据只读引用：`/Users/luckye/Documents/Code/a2a-worktrees/T-219-evidence/round2/table.json`、`comparison-details.json`、`unmasked-existing-failures.json` 及 `runs/<测试名>/{baseline,candidate}/`。23 个调用者、46 次运行：5 个两边通过，1 个由失败转通过，17 个两边失败/阻断，无超时。第 7 组 worktree 两边阻断点不同，不能说业务表现等价。入库摘要为本工作树 `evidence/2026-10-31-batch29/T-219/`，并参见提交 `4fa0d4ca4`、`19d1d883e`。

**Ubiquitous language**：原生会话身份、交付回合、attempt、审查副本、审查 worktree、验收 worktree分别处理；“回合结束”不等于“交付通过”，“回收成功”不等于“验收通过”。**Tracer bullet**：hc 迁移先跑一条真实后台→私有 hc→worker→交付→独立 reviewer→集成的薄切片，再扩展反例。**Deep modules**：建议修现有入口和共享夹具，不另建一套绕过门禁的测试接口。

## 2. 契约来源索引

| 编号 | 现行契约与修订关系 | 票面、规格原文位置；落实提交 |
| --- | --- | --- |
| C1 | 唯一后台门禁；锁、fence、CAS、attempt、版本与中断语义保留。任务卡版本化，交付须为分配 worktree 的干净完整 HEAD。 | `.project-map/tickets/T-070-gates-task-cards-quality.md:19`、`:20`、`:25`；`.project-map/specs/native-cli-orchestration-2026-10-10.md:81`、`:89`、`:96`；门禁搬入 `4d81efcacd`，持久后台入口 `93a707299d`，任务卡/工作分支集成 `1273b17e93`。 |
| C2 | 红态命令可选；填了则候选测试在 B 失败、在 C 通过；规则检查按项目配置。失败回写原 worker，修复后整串重跑；同 attempt 第 3 次停止自动回写并交执行主控。独立审查、终结评分保留。 | `T-076-quality-chain-scoring.md:18`、`:19`、`:20`、`:21`、`:34`；上述原生规格 `:90`、`:93`；`2bc3a1e96b`。规则检查“加宽套件”不等于用户批准放宽规则本身。 |
| C3 | 运行身份与交付回合分开；回执新回合后 run/reclaim 可继续，另一个原生会话或 leader 仍拒绝。后续真正的新用户回合仍须按新回合身份处理。 | `T-076-quality-chain-scoring.md:26`、`:36`、`:59`；`42e2b8ed3`；后续 `.project-map/tickets/T-157-stop-hook-user-input-submit.md`，`c6725344a`、`d9e948bba`；T-207 的用户回合结束交付修订 `6e094fcf7`。 |
| C4 | worker/reviewer/验收 worktree 命名与序号；干净才删、保留隐藏引用，脏/未知留场景并上报；结果入库后清理临时副本。冲突通知 worker，结束会话换 attempt；CAS 最多 3 次自动重验，第 4 次落空升级；C 不变复用审查、C 变重审。 | `T-077-worktree-lifecycle-conflicts.md:18`～`:23`、`:28`～`:32`、`:54`；`34536c5510`、`cd140e190d`，票面记录产品 `5d0bf1e8`、合并 `60eb6ac5`。冲突 request_id 按 launch 隔离的修复 `044c7618d6`（提交原文及新增 `test_relay_scope.ts`）。 |
| C5 | `oracle_paths` 必填、B 上存在、与红态 test_paths 不相交；改验收文件须在完成条件执行前硬拒，计入 oracle 拒绝及三次上限。 | `T-080-protected-acceptance-files.md:18`～`:24`、`:49`；实现 `91071891a9`，合入 `9c1f4be7`。 |
| C6 | 九项尾注是封闭协议；矛盾身份/外任务/额外字段不能放行；完全无尾注记一次推断人工介入。Launch/Tool/Model/Effort 对本 attempt 启动/交付事实核对，不能对任务卡自证；无启动交付记录拒收。允许的 unknown 保留。 | 原生规格 `:140`；`T-077-worktree-lifecycle-conflicts.md:45`～`:47`；`T-084-trailer-launch-record-match.md:18`、`:23`、`:29`、`:37`；`T-081-bad-worker-suite.md:48`；`45aa68ef`、`e9c8aa47cb`、`8b4053325`。agy/opencode 的 unknown 见 AGENTS.md 第三阶段及 `T-187`，不能把旧 Codex 常量扩成所有 CLI 的规则。 |
| C7 | reviewer 在一次性候选副本可写，审查 worktree/worker/共享仓库仍受保护；请求含完成条件与变异检查；workspace 必须绑定；结束核对并回收后才能集成。T-090 绑定审查开始时的实际 worker HEAD/分支/干净状态，不能误要求 HEAD 恒等于 C。 | `T-082-reviewer-oracle-sufficiency-mutation.md:18`～`:22`、`:43`；`5f7f9816e`、`9fd96145e`、`a75070236`；`T-090-review-end-check-worker-boundary.md:20`、`:22`、`:45`，`0bcc5ab66`、`89a1915f1`。 |
| C8 | `pane_release` 删除；启动由原生就绪信号放行。预建 reviewers home 数组删除，改 reviewer_role_card/revision；新会话由不 resume/fork、新原生身份、cwd 在副本等事实证明。产品 home 与隔离验收 home 是不同约束。 | `T-127-codex-sessions-in-user-codex-home.md:28`～`:34`、`:39`；`282906b9e` 原文明确 “pane_release is removed”，删除 CLI/daemon 分支、旧 reviewers 类型；T-141 的 `bf3d00a82` 改成原生 OSC idle 首次放行，合并 `1204f2e0e`。 |
| C9 | 模型/强度/Fast 可配置，不按固定模型或强度拒绝；CLI 版本只记录。T-141 放开网络、不再 strict-mcp-config、worker 沿用用户信任；Codex reviewer 副本仍 untrusted，写入范围仍硬边界，后续回合仍靠匹配 Stop。 | `T-112-launch-model-effort-configurable.md:22`～`:26`，`44f163011`、合并 `777db09a1`；`T-118-cli-versions-shell-markers-restore.md:18`，`224f2f38c`；`T-141-loosen-managed-limits.md:21`～`:25`、`:45`～`:46`，`1204f2e0e`。 |
| C10 | 后台启动者必须提供、创建绑定隔离 state 的操作员凭据；CLI 管理请求带该身份。终端令牌不是操作员凭据。产品持久化位置移出后台数据目录，隔离测试自有路径。 | `c0b23f6705`（T-078-1）原文新增 credentials.ts、0600/wx 创建、serve 缺凭据拒绝及 transport 传递；`.project-map/tickets/T-078-controllers-in-workbench.md:23` 的实际调用者凭据要求；后续 `T-125-operator-credential-storage.md:34`、`T-126-operator-credential-out-of-terminal-reach.md:18`～`:21`、`:35`，`35cadc44b`、`87453d496`。首次凭据要求不是 T-126 才新增。 |
| C11 | task/card 按项目定位：内部 `<project>+<task>`；新建草稿用明确 project 或有项目上下文的终端身份，不能让无项目裸 id 获得错误优先级。 | `T-123-project-scoped-task-and-card-ids.md:22`、`:26`～`:29`、`:42`；`a04c60a50`。T-121 的旧草稿归属机制由它删除。后续跨已打开项目操作见 T-193，不能复用旧“主控永远不能操作别项目”的断言。 |
| C12 | 审查员只交 verdict/findings/report，`review_submit` 用门禁模板补身份并即时校验；Stop 读结果文件，再校验；没有成功提交则 review_result_missing。最后回复 JSON 协议删除、不并存。 | `T-203-review-submission-robustness.md:24`～`:28`、`:44`；`30ee51d30`。T-160 的“最后回复必须 bare JSON”已被此项取代，协议失败后的新审查恢复语义仍可保留。 |
| C13 | 路径重叠：进行中不带理由仍拒，理由可放行，accepted 不再占路径；卡外改动：列清单交主控判断，未判断不得集成，验收文件与 Git 元数据仍硬拒。 | `T-197-overlap-advisory.md:18`～`:26`，`4a5e1f3fc`；`T-198-out-of-card-paths-judged.md:18`～`:21`、`:25`～`:28`，`6b6be4f01`。旧“任意卡外路径都 path_boundary_failed”不能原样迁移。 |
| C14 | 证据与运行条件：大 run/fixtures 外置归档，输入小文件仍留仓库；batch16 起生效，历史不改写。2026-10-19 允许内置盘构建/临时目录。hc 后续只换运行时，不改门禁串语义。 | `T-088-evidence-archive-policy.md:23`～`:31`，`6efd94e64`；`T-102-package-workbench-as-mac-app.md:50`、`:57`，`61aa5a961`、AGENTS 变更 `ecef58667`；`.project-map/specs/hc-runtime-2026-10-31.md:28`、`:38`、`:45`，`3570fdaf2`。 |

上表 `T-xxx-*.md` 简写均位于 `.project-map/tickets/`。来源判定 **PASS（原文定位）**，不表示每条已在当前运行时重验。

## 3. 按 7 组、逐个测试的处置选项

代价用小/中/大表示相对改动范围，不是工时承诺。**迁移**要取得现行入口正常对照与独立坏实现命中；**历史**要写明适用 revision 与失去的守护，不能编造“最后全绿提交”；**拆开**保留有效业务检查、把旧条件/专用历史重建部分单列。下表只是建议，未执行任何处置。

### 第 1 组：旧 pane_release 及其后续协议

共同首因：`test_quality_chain_e2e.py:224`～`:232` 的手动放行由 C8 删除；还不能假定改一行即可全绿。共享基类在 `:115`～`:125` 仍构造 reviewers home 数组，历史 `Tracer.send_review`（`test_quality_tracer_e2e.py:78`）仍按最后回复 JSON 提交；C8、C12 都要处理。T-219 仅修共享就绪/部分 caller，不代表六个套件已迁移。

| 测试 | 仍有效/已改变的契约 | 选项、代价与风险；建议 |
| --- | --- | --- |
| `test_quality_chain_e2e.py` | C1/C2 的红态、规则冻结、失败回写、重交、fence、relay/忙时队列；C8/C12 替换旧放行与审查通道；`:671` controls 的卡外硬拒按 C13 重写。 | **迁移**（中）：先修启动/Stop/配置，再保留红态与 relay 场景，风险是首个基础错误解除后暴露后续陈旧断言。**历史**（小）：丢掉当前最直接的红态/规则冻结反例。**拆开**（中）：机械红态/规则与受管回写两部分按现行入口独立运行，旧放行只留历史；需防公共 helper 被不当算作覆盖。建议迁移，优先恢复独有检查。状态 **INCOMPLETE**。 |
| `test_bad_worker_e2e.py` | C5/C6 的验收篡改、矛盾尾注、四个追溯字段/无记录反例；C1 的旧 attempt、冻结 C；`deny_path` 的旧卡外硬拒按 C13 区分。 | **迁移**（大，矩阵较广）：保留每个独立坏输入和正确交付对照，追溯字段用当前 delivery 事实。**历史**（小）：四字段、无记录与矛盾尾注拒收将无人有效守护。**拆开**（中）：先迁 oracle/身份/冻结 C，旧路径预期单列再处理；风险是遗漏余下矩阵。建议拆开分期迁移，所有条目仍逐项追踪。状态 **INCOMPLETE**。 |
| `test_protected_acceptance_e2e.py` | C5 完整矩阵仍有效，`oracle_boundary_first`（`:270`）的旧卡外硬拒前置与 C13 冲突；验收文件即使卡外仍须硬拒。 | **迁移**（中）：保留修改/新增/删除/重命名、存在性、快照、计数、三次上限，改边界先后例的输入/现行期望。**历史**（小）：T-198 只有一个 oracle 硬拒子例，补不齐此矩阵。**拆开**（中）：保护/schema 与回写/上限分别迁移；风险是失去保护检查到 PTY 的连通性。建议迁移。状态 **INCOMPLETE**。 |
| `test_quality_widen_e2e.py` | 是 T-076 的套件加宽，不是允许规则宽松。C2 的 B/C 红态隔离与顺序、规则配置拒绝；C2/C5 的评分 schema/计数、CAS 评分恢复、review 故障仍相关。 | **迁移**（大）：15 个 wide 场景及 3 个 review-red 场景，需逐项区分离线格式与后台真实路径。**历史**（小）：红态正例/文件合法性、CAS 与评分绑定等缺口扩大。**拆开**（中）：先迁红态/规则/执行顺序，把分数导入/终结恢复/旧重启预期另列；hc 后台接回原 attempt 不应沿用“重启一律 unknown”的旧期待。建议拆开，核心红态/规则先迁。状态 **INCOMPLETE**；未来 hc 重启语义未在本票决定。 |
| `test_review_worktree_lifecycle_e2e.py` | C4/C7：detached、冻结 C、命名序号、结果先落库后删、脏/未知保留；不因换 hc 取消。 | **迁移**（中）：当前四场改启动/配置/提交协议后重证事件顺序及 Git 注册清理。**历史**（小）：干净清理有部分近测，严格顺序、序号及异常保留没人守。**拆开**（中）：正常清理与异常保留分期，风险是只迁正例。建议迁移四场。状态 **INCOMPLETE**。 |
| `test_s3_quality_joint_e2e.py` | C4：G 改/C 不变重跑机械串、复用审查；C 改新 reviewer；冲突重交再被质量拒收后 C3 重交整串。 | **迁移**（中到大）：三场跨层，需同时修 Tracer 和受管回合。**历史**（小）：单独的 CAS 或新审查正例不能替代这三种组合。**拆开**（中）：同 C、换 C、冲突再质量返工分别运行，仍保留全部预期。建议迁移三场。状态 **INCOMPLETE**。 |

### 第 2 组：reviewers 数组

| 测试 | 现行契约 | 选项、代价与风险；建议 |
| --- | --- | --- |
| `test_quality_legacy_e2e.py` | C8 明确删除预建 reviewers home；C2 评分仍要 managed provenance，手工 claim 无 delivery 不能凭一份审查拿到最终评分并改 Git（`:29`～`:51`）；C1/C7 冻结 C，worker 后续 HEAD 可在审查开始前不同于 C，但不能替换冻结候选（`:53`～`:81`）。 | **迁移**（中）：两场及继承 helper 都需新 reviewer 配置/就绪/Stop 结果文件。**历史**（小）：不能因文件名含 legacy 就推断业务已废弃；来源缺失拒收和冻结 C 的端到端保障丢失。**拆开**（中）：claim 评分来源与 managed 冻结候选拆开迁，纯旧 home 流程留历史。建议迁移；可排在核心受管迁移之后，但不得作为“已有替代”的理由。状态 **INCOMPLETE**。 |

### 第 3 组：最后回复 JSON

| 测试 | 现行契约 | 选项、代价与风险；建议 |
| --- | --- | --- |
| `test_t082_review_boundary_e2e.py` | C7/C9/C12。T-152 已迁过一次（票 `:18`、`:37`～`:39`，合并 `866cc08bc`），但这不覆盖后来的 T-203。当前 `send_review`（`:65`）和 held socket（`:322`）仍把 JSON 塞进 Stop 最后回复，不能用其失败证明边界拒收。 | **迁移**（中）：普通提交与 held socket 都先经 review_submit 写结果，再触发 Stop；保留 copy、refs、workspace、脏结束、锁竞争的目标断言。报告回读场景 `:383` 还在找 prompt 尾部旧 JSON 模板，也须按 C12 的门禁模板读，不应删报告完整性检查。**历史**（小）：撤掉此前用户优先迁的安全边界。**拆开**（中）：纯旧协议展示可历史，七场有效边界全部迁，注意不能只修 tracer 正例。建议迁移。状态 **INCOMPLETE**。 |
| `test_t090_review_worker_boundary_e2e.py` | C7 的实际 worker HEAD/分支/干净快照，三种期间变动各应作废并保留场景（`:57`～`:64`）。继承上份 `send_review`，当前协议失败挡住预期结束检查。 | **迁移**（小到中，依赖 T-082 helper）：修提交协议后保留三个隔离反例，不能把所有 paused 都当通过，须仍核对 `review_worker_workspace_changed`。**历史**（小）：三项结束核对没人守。**拆开**收益小、易漏 branch 反例。建议整份迁移。状态 **INCOMPLETE**。 |

### 第 4 组：host 缺操作员凭据

共同契约是 C10；不是通过关闭身份核对让测试起来。host 启动者应在它拥有的夹具路径创建/传递凭据、隔离继承的 A2A 身份，收尾删除自有凭据。其他 host 的凭据探针不证明这三个 host 合规。并且越过凭据后还有 C8/C11/C12 的陈旧点，代价不能只算“加一个环境变量”。

| 测试 | 现行契约 | 选项、代价与风险；建议 |
| --- | --- | --- |
| `test_conflict_trailer_proofs.py` | C4/C6：结束 worker 的冲突换新 attempt，C2 同源码多两项尾注拒收，生产 hook 的九项尾注通过并保留 host 改动/隐藏引用（`:118`、`:148`、`:172`）。 | **迁移**（中）：凭据、建卡项目、继承的 pane_release（relay 文件 `:96`）、审查协议一起改；保留成对固定源码输入。**历史**（小）：r3 专用重建可留历史，但“额外尾注拒收”的现行反例没人替代。**拆开**（中）：r3 历史资料装配单列，封闭九字段检查迁到现行冲突入口；需保留独立源码 oracle。建议拆开。状态 **INCOMPLETE**。 |
| `test_relay_conflict_e2e.py` | C4：新 launch 可用同一个 delivery id，同 launch 文件/Stop 重放只生效一次；旧 rollout 不被新 attempt 改写；结束后换 fence，最终保存 C1/C2 引用。 | **迁移**（中）：凭据之后还需 C8 原生就绪及 C12 审查；`launch()` 的 `native_session is None`（`:98`）也要按就绪后的真实时点审计。**历史**（小）：离线 relay-core 不覆盖“实际换 attempt→重交→审查→集成”。**拆开**（中）：离线去重与冲突端到端分开，后者不能省。建议整场迁移。状态 **INCOMPLETE**。 |
| `test_multiturn_identity_e2e.py` | C3：回执 B 不替换交付 A，run/reclaim 仍绑定原生会话/leader；改原生会话/leader 则拒且不关闭。 | **迁移**（中）：凭据、项目、review 配置与协议、完整 Stop/回合记录及收尾 state_readback 均审计。**历史**（小）：T-157 管新旧 prompt，不等价于此处“同原生身份跨回执仍能回收”。**拆开**（中）：先迁 run/reclaim 正例加会话/leader 两负例，旧一致性报告部分另行保留；不能只迁成功场景。建议四场迁移。状态 **INCOMPLETE**。 |

### 第 5 组：直接 card_save 不带项目

| 测试 | 现行契约 | 选项、代价与风险；建议 |
| --- | --- | --- |
| `test_daemon_gates_e2e.py` | C1/C11。继承 cards 的有效/无效建卡都应有项目，才能测到卡片错误；正常 helper 已被 T-219 修，但 inherited 校验循环直接 `card_save`（cards `:286`、`:294`、`:300`）仍缺项目。另有本文件 `:97`～`:109` 三张追加表拒 UPDATE/DELETE。路径测试须按 C13 逐项换预期。 | **迁移**（中）：修的是入口身份与卡外语义；不是把预期 invalid_task_card 改成 unknown_task。**历史**（小）：hc spec 明确点名此真实门禁驱动，删除会让任务卡矩阵与追加表缺守护。**拆开**（中）：从共有 cards 继承保留业务检查，纯旧启动/过时路径预期单列；风险是继承方法被漏算。建议迁移为唯一当前 cards/daemon 入口。状态 **INCOMPLETE**。 |
| `test_t084_trailer_record.py` | C6/C11：直接 `card_save` 位于 `:248`；其后是四字段不符、允许 unknown、无尾注推断、无 delivery 拒收，以及真实事实与卡上请求不同的反事实（`:266`、`:302`、`:342`、`:421`）。 | **迁移**（中）：建卡带项目、后续 task id/worker runtime/断言锚点审计；变异器不能假定历史源码针仍存在。**历史**（小）：bad-worker 当前也坏，不能互相宣称替代。**拆开**（中）：将仍有效的来源/unknown/缺记录矩阵迁，旧红态/文本变异工装历史化；需用户批准。建议迁移；hc 前可先选择迁 bad-worker 同等矩阵，避免两套都当强制依赖。状态 **INCOMPLETE**。 |

### 第 6 组：CLI 前没有后台

| 测试 | 现行契约 | 选项、代价与风险；建议 |
| --- | --- | --- |
| `test_task_cards_e2e.py` 的 14 个自身用例 | C1：CLI 从 `93a707299d` 起调用持久 daemon，不再在 CLI 进程内另建门禁。现自身 setUp 未起后台，CLI helper（`:83`）连不到 socket。14 方法列在 `:153`～`:465`；`test_path_prefix_rename_delete_and_whitespace` 中“卡外一律硬拒”由 C13 改变。 | **迁移**（中到大）：在实际后台入口上跑同一业务检查，需与 DaemonCards 避免双重维护/重复入口。**历史**（小）：只能将旧“无后台入口”历史化，不能声称 14 项业务契约都消失。**拆开**（中）：业务断言迁入/保留在当前 DaemonCards，原文件作为共享 helper 或旧直接入口须明确身份，不能再依赖“可导入”宣称通过。建议拆开；当前业务全集由第 5 组 daemon 驱动承担，逐项证明后再裁定本文件。状态 **INCOMPLETE**。 |

### 第 7 组：运行条件挡住，先判断条件再判断业务

| 测试 | 事实、现行契约与条件判断 | 选项、代价与风险；建议 |
| --- | --- | --- |
| `test_worktree_lifecycle_e2e.py` | `snapshot_source()`（`:952`～`:970`）无条件装包旧 T-077 PLAN/决定/脚本。**PASS（事实）**：本 worktree 是 sparse checkout，batch13 未展开；`git ls-tree HEAD evidence/2026-10-11-batch13/T-077/PLAN.md` 能找到 blob，`git show HEAD:.../PLAN.md` 能读到原文，文件没有从 Git 消失。T-088 C14 从 batch16 起、不改历史，且要求测试输入小文件保留，因此不能说“T-088 后无需此文件”。本例 PLAN 是 `archive.add` 的源码快照资料，所查没有业务读取；baseline 模式还在 `:1006` 读取旧 sources.tar.gz，是另一条历史重建路径。`:995` 的外盘/Node 26.5 前置也不等于业务契约；真实 Git checkout 对身份预检仍有必要，git archive 副本没有 .git 本来就不能充当它。 | **改条件并迁移**（大）：当前业务用真实隔离 checkout，源码装包显式从 Git 取被 sparse 排除的记录或取消其当前运行依赖；历史 baseline 重建单列，运行夹具固定 /private/tmp，原始大证据按 C14 归档。仍须处理 C8/C11/C12/C13，不是补 PLAN 后就全绿。**整份历史**（小）：丢失 worktree/R8/冲突的主要现行反例。**拆开**（中到大）：迁当前生命周期/冲突/R8，固定旧 baseline/归档重建保留历史。建议拆开，优先当前子集。业务状态 **BLOCKED（沿用 T-219）**；条件研究 **PASS**。 |
| `test_t082_parent_launch_e2e.py` | `:88` 强制 `/Volumes/WD-Elements`；在当前规则和本会话 /private/tmp 约束下不是有效业务前置，内置盘裁定 C14 足以否定“所有夹具必须外盘”的普遍解释；大证据归档仍要外盘，不等于运行夹具必须外盘。更关键的是 `:21` 固定 START=`451be8462…`，`:42`～`:54` 要旧 read-only/非副本事实，`:58` 调 pane_release，本来是重建旧门禁的拒收红态。`network-enabled` 已被 C9 废止为反例；`wrong-workspace` 与共享 tmp 可写仍有当前对应安全要求，但输入要换成新协议。 | **只改条件**（小）只能修历史重放可达性，不能使它成为当前回归。**整份历史**（小）：作为固定 START 红态脚本最合适，但须保留当前 wrong-workspace/tmp 写界限的替代覆盖；当前文件标历史不是已获本票授权。**拆开**（中）：旧 START 重建保留历史，把当前 workspace/tmp 负例并到已迁 T-082，网络用当前应允许的正例。建议历史或拆开，**不建议只改外盘检查就当现行**。业务状态 **BLOCKED（沿用 T-219）**；过时条件与用途判断 **PASS**。 |

**PASS（处置先例核对）**：`workbench/tests/HISTORICAL.md:3` 记录 T-154 用户选“先迁安全边界的 4 个”，`:18` 明说标历史后检查无人守；`:31` 也警告 Tracer 可导入不使 caller 自动现行。故本次不能自动把 17 个套件一律标历史，也不能把 T-152 曾通过视为 T-203 之后仍通过。

## 4. 检查覆盖表

以下原测试统一省去 `workbench/tests/` 前缀；“其他覆盖”列保留全路径。行号有范围时表示一组连续断言，首个行号可直接定位。每行状态针对该检查，不以文件整体状态替代。**有断言/部分**而未补跑者的当前运行证据统一 **INCOMPLETE**。

### 4.1 质量串、评分与受保护验收

| 检查项 | 原测试与断言位置 | 其他现行覆盖、断言位置与局限 | 结论 |
| --- | --- | --- | --- |
| 红态缺 test_paths 拒收 | quality_chain `:330`～`:334`；quality_widen 复用 | 未找到独立替代。T-219 前五场已通过中的首项只证明此项，不代表全套。 | **没人守（独立替代）；INCOMPLETE** |
| 测试在 B 通过不得算红态；C 失败拒收 | quality_chain `:336`～`:355` | 未找到其他执行同样 B/C 反例的现行测试；近测普遍 red_commands=[]。 | **没人守；INCOMPLETE** |
| 项目规则失败拒收；候选清空 quality.json 不可绕过注册规则 | quality_chain `:357`～`:365` | 没有其他直接规则执行/冻结反例。metrics 中 rule_checks=0 不是执行过规则检查。 | **没人守；INCOMPLETE** |
| 红态成功成对 B=1/C=0、B/C 目录隔离及检查顺序 | quality_widen `:71`～`:81`；bad_worker `:436` | 正向 worker 交付不核对 B/C 隔离；没有替代。 | **没人守；INCOMPLETE** |
| red manifest 非法路径、符号链接拒绝；坏项目质量配置不退化成无检查 | quality_widen `:89`、`:100`、`:110` | 没有其他同项反例。 | **没人守；INCOMPLETE** |
| 首次质量拒绝回写原 launch/attempt，Git 不动，修好显式重交 C2 | quality_chain `:382`～`:407` | `workbench/tests/test_t133_t134_records_metrics_e2e.py:175` 构造一次 completion 拒绝后修复并检查交付轮数/计数；T-198 `:350`～`:355` 是卡外判断回写。都不覆盖红态/规则失败的原窗格准确回写全链。 | **部分；剩余没人守；INCOMPLETE** |
| 修复后整串重跑、review 必经、未给评分不得终结/run 不自作主张 | quality_chain `:418`、`:428`、`:475`、`:487` | `workbench/tests/test_t203_review_submit_e2e.py:151` 验证审查成功；`test_t124_controller_e2e.py:629`、`:676` 涉主控结束后的未评分处置。没有等价的红态/规则修复整串及全部终结前置反例。 | **部分；剩余没人守；INCOMPLETE** |
| 第 3 次拒绝暂停，只回写两次、升级 issue 绑定原 attempt，重放不继续 | protected_acceptance `:162`～`:195`；历史 Tracer 的 third_rejection | 未找到其他当前直接上限/不再回写/重放矩阵。 | **没人守；INCOMPLETE** |
| oracle 文件修改硬拒（含卡外） | protected_acceptance `:48`、bad_worker oracle_test/oracle_entry `:165`～`:177` | `workbench/tests/test_t198_out_of_card_e2e.py:316` 直接断言 oracle_modified 且有 repair，现行独立覆盖一个修改子例。 | **部分有断言；INCOMPLETE（未复跑）** |
| oracle 目录新增、删除、重命名及前缀邻接正例 | protected_acceptance `:88`～`:130` | T-198 的单文件子例不含这些输入。 | **没人守；INCOMPLETE** |
| oracle 必填/非空/语法；与 red test_paths 不相交 | protected_acceptance `:210`～`:240` | cards 字段删除循环含缺字段，但该入口已被项目前置挡住；没有可用独立替代。 | **没人守；INCOMPLETE** |
| claim 时 oracle 必须存在，按认领当前 B 查，拒绝前不建 worktree | protected_acceptance `:251`、`:255`、`:267` | 没有其他反例。 | **没人守；INCOMPLETE** |
| oracle 检查先于完成命令/审查，不执行被改 oracle；Git/reflog/评分不动 | protected_acceptance `:53`～`:66`；bad_worker `:176` | T-198 只查错误与 repair，没有断言完整执行顺序/无副作用。`test_t187_git_metadata_guard_e2e.py:156` 是 Git 元数据拒绝顺序，不是 oracle。 | **没人守（完整项）；INCOMPLETE** |
| oracle 拒绝写回 PTY、单列 rejections.oracle、卡版本/快照不被新版本替换 | protected_acceptance `:73`、`:80`、`:145`、`:287` | `workbench/tests/test_score_schemas.py:142`、`:146`、`:155` 只验证脚本写分/格式里的 oracle 字段，不验证真实门禁从拒绝事件累计。T-198 有 repair 不等价。 | **部分（格式）；业务链没人守；INCOMPLETE** |
| 卡外普通文件由主控判断；理由/拒绝/再交付绑定 | cards `:185`、`:340`，bad_worker deny_path；这些旧预期已变 | `workbench/tests/test_t198_out_of_card_e2e.py:311`、`:333`、`:335`、`:338`、`:354`（后续重交见同文件）。当前检查存在，不能将旧 path_boundary_failed 原样迁回。 | **PASS（语义已取代且覆盖定位）；运行 INCOMPLETE** |
| 评分必填、字段合法、相同终结只写一次、abandon/upgrade 后 reclaim 不改终态 | quality_widen `:117`～`:154` | `workbench/tests/test_score_schemas.py:145`～`:159` 只守格式；`test_t137_reflect_e2e.py:218` 守正常集成一条分数，未试缺分/重复终结；历史 tracer 不计。 | **部分；缺分/终结重放等没人守；INCOMPLETE** |
| schema v1/v2 兼容读取、非法字段/残缺末行拒绝且不改原文件 | quality_widen `:184`～`:207` | `workbench/tests/test_score_schemas.py:122`、`:152`～`:159` 有 v1/v2 读写及非法 schema 断言；它是 scripts/score/validator，不覆盖后台 scores_validate 的整个比较回路。 | **部分；后台通路没人守；INCOMPLETE** |
| CAS 前后评分 intent 不能改包、只落一次、重放不写 Git | quality_widen `:229`、`:255`、`:261`、`:266` | `test_daemon_recovery_e2e.py:287`～`:293` 直接覆盖相同 integration intent 与 Git 幂等，但未断言 pending score 替换拒收或 score_id 仅一次。 | **部分；评分绑定没人守；INCOMPLETE** |
| claim 无 managed provenance 即使 reviewed 也不得评分集成，Git/内容/分数不动 | quality_legacy `:36`～`:51` | `acceptance/test_coop_e2e.py:543` 有同类预期，但默认入口只转 CLI、没有本身启动 daemon；适配 runner 不等于本次有可用/通过证明。没有可确认有效的其他端到端替代。 | **没人守（有效当前证据）；INCOMPLETE** |

### 4.2 坏 worker、尾注、回合与交付身份

| 检查项 | 原测试与断言位置 | 其他现行覆盖、断言位置与局限 | 结论 |
| --- | --- | --- | --- |
| worker 自报完成但未改/改错内容，独立完成条件拒收 | bad_worker self_report `:185` 起；共用拒收 `:149`～`:161` | `workbench/tests/test_t133_t134_records_metrics_e2e.py:175` 的一次 completion 拒绝及两轮修复是部分真实路径；`test_daemon_recovery_e2e.py:197` 的内容 oracle 用于恢复，不构造这两种坏交付并断言不能集成。 | **部分；完整坏输入矩阵没人守；INCOMPLETE** |
| 部分尾注、矛盾重复 Session、外 Task/Attempt 拒收；拒绝事件、分支和评分不动 | bad_worker `:14`～`:29`、`:140`～`:161`；cards `:397`～`:419` | `workbench/tests/test_t081_duplicate_input.py:39`～`:50` 仅构造并用 git interpret-trailers 解析矛盾输入，refused 是空 spy，不调用门禁。不能算拒收覆盖。 | **没人守（门禁拒收）；INCOMPLETE** |
| 四个 Launch/Tool/Model/Effort 与本 attempt 记录不符分别拒收 | bad_worker identity cases；t084 `:354`～`:356` | 其他近测主要查正确提交的值；没有四种伪造都能到目标检查的替代。 | **没人守；INCOMPLETE** |
| 带尾注但缺 delivery/启动记录拒收；完全无尾注恰好一次推断人工介入 | bad_worker trailer_no_launch、`:389`、`:406`；t084 `:421`～`:430`；cards `:209`～`:229`、`:437` | 输入记录/鼠标测试的人工介入不是“缺尾注推断”；没有其他当前等价矩阵。 | **没人守；INCOMPLETE** |
| 正确尾注、实际 model/effort/native 与交付相符，允许的 unknown 不误拒 | t084 `:358`～`:368`；bad_worker positives | `workbench/tests/test_hook_turn_facts.py:91`～`:94` 检查生产 hook 的九项/当前 turn 事实（离线，不是门禁）；`run_worker_delivery.py:371`～`:374` 核对原生事实→delivery→尾注；`test_t127_codex_home_e2e.py:388` 正例；`test_t187_managed_worker_e2e.py:190` 查 agy/opencode unknown。 | **有部分直接正例；unknown/伪造组合不能替代；INCOMPLETE** |
| 闭集九项：同 C2 源码，额外 Fence/Spec-Rev 拒；生产 hook 九项可集成 | conflict_trailer_proofs `:109`～`:112`、`:156`～`:184` | hook_turn_facts 九项输出只证明生成器，未向门禁送十一项。 | **没人守（封闭拒收对照）；INCOMPLETE** |
| 已旧 attempt 不可覆盖/集成/回收新 attempt | bad_worker `:305`；cards `:231`～`:239` | `workbench/tests/test_t157_stale_turn_e2e.py:170`～`:175` 守旧 attempt 的“恢复交付”不得注入；是 UI/恢复子项。旧 run 套件有更广断言，但不可凭其文件存在宣称当前入口通过。 | **部分；完整旧执行者隔离没人守；INCOMPLETE** |
| 干净完整 HEAD、短 SHA/base 拒收；C 冻结后 later_bad 不可替换，集成仍为 C | quality_legacy `:58`、`:68`、`:76`、`:81`；bad_worker `:325`、`:334`；quality_chain `:503` | `acceptance/test_coop_e2e.py:505` 的原冻结验收还在，但默认无 daemon；其适配也依赖旧驱动运行条件。当前大量正例仅提交干净 HEAD，无 late candidate 反例。 | **没人守（可用完整负例）；INCOMPLETE** |
| fence 旧值/未显式 submit 的 Stop 不产生候选 | quality_chain `:511`、`:521` | `workbench/tests/test_relay_core.ts:28`～`:33` 拒 fence 不符的文件（离线 relay）；`test_t157_stale_turn_e2e.py:138`～`:139` 拒真实旧回合，非无请求 Stop 的全部组合。 | **部分；INCOMPLETE** |
| 同 launch 重复文件/Stop、改包、并发不重复生效，旧 Stop 不吃掉新请求 | quality_chain `:537`～`:552`；relay_conflict `:168`～`:170` | `workbench/tests/test_relay_core.ts:24`～`:42`、`:51`～`:61`，本次 **PASS**；`run_worker_delivery.py:413`～`:422` 是真实输入/收据一次且无工具的另层断言，本次未跑。 | **PASS（relay 离线层）；完整端到端 INCOMPLETE** |
| 新 attempt/launch 使用相同 request_id 是新交付；旧 rollout 与意图保持 | relay_conflict `:149`～`:170` | `workbench/tests/test_relay_scope.ts:33`～`:42` 本应直接守该项，**本次失败**，首交付 invalid_relay_request、effects=0，未到第二次交付。relay_core 只有单 launch。 | **没人守（有效跨 attempt 路径）；INCOMPLETE** |
| 运行中 input 排队，按注册→paste→独立 CR 次序写；不把 busy 当 idle | quality_chain `:564`～`:572` | `workbench/tests/test_pane_dispatch_state.ts:53`～`:64` 有离线序列断言（本次未跑）；`test_t166_busy_input_e2e.py` 用真实输入路径，人工介入绑定断言 `:183`～`:184`。不能以它们替代质量回写的同一场景。 | **部分；INCOMPLETE** |
| 回执 B 后 reclaim 仍认原运行身份、仅关闭自己的 thread、交付仍 A | multiturn_identity `:136`～`:139` | `run_worker_delivery.py:398` 仅回执状态的同 attempt；`:422` 无工具。没有回执后 reclaim 的相同保证。 | **没人守（完整项）；INCOMPLETE** |
| 回执 B 后 run completed/reclaimed；伪造另 native/leader 则 identity_conflict 且不关 | multiturn_identity `:166`～`:183` | T-157 的旧 prompt caller 拒收（`test_t157_turn_identity.ts:112`、`:134`）是交付回合事实，不构造另 leader 的回收负例；历史 run8/9/18 不自动证明现行多回合。 | **没人守；INCOMPLETE** |
| 真正新用户回合按新事实；旧提交拒收、恢复不替换 attempt/session/fence/version | 与 multiturn 的语义相邻，但非其替代 | `workbench/tests/test_t157_stale_turn_e2e.py:122`、`:138`、`:201`～`:209`；`test_t157_turn_identity.ts:112`～`:155`；`test_t207_user_turn_delivery_e2e.py:141`～`:145`。 | **有直接现行断言；INCOMPLETE（本次未跑）** |

### 4.3 审查、结束边界与副本生命周期

| 检查项 | 原测试与断言位置 | 其他现行覆盖、断言位置与局限 | 结论 |
| --- | --- | --- | --- |
| 启动原生 ready，后续 OSC idle 不能代替 Stop | quality_chain 旧 release；T-082 `:39`～`:46` | `workbench/tests/test_t141_startup_signal.mjs:26`～`:42` 直接检查 split OSC/只放一次/缺 leader；末尾 `:47`、`:52` 依赖未展开日期截图，整文件本次未跑。T-219 PTY 修订是夹具输入不是边界 oracle。 | **部分有断言；INCOMPLETE** |
| reviewer 正确 cwd/sandbox/tmp/untrusted；错误写范围/审批参数拒 | t082 boundary `:123`～`:133`、`:250`～`:256`；parent_launch `:76` | `workbench/tests/test_t141_reviewer_contract.mjs:51`、`:59`、`:73`～`:103` 用生产 builder+真实 reviewLaunch 的离线断言，覆盖 foreign_workspace/broader_writes/approval/trust 等；不启动 PTY，不能证明沙箱实际拒写。 | **部分有断言；INCOMPLETE** |
| reviewer 副本可运行变异；worker/共享路径实际写失败、共享 tmp 禁写 | parent_launch 的 tmp 项只是 argv，T-082 真实边界另有历史证明 | `workbench/tests/test_t127_codex_home_e2e.py:464`～`:466` 检查真实原生执行输出；`test_t141_loosened_limits_e2e.py:305`、`:326`～`:328` 查实际文件与 temp 结果（worker 边界）。均未在本次运行；网络开启已是正向要求。 | **部分；INCOMPLETE** |
| 新干净审查上下文：不 resume/fork、不复用 worker/已有原生会话 | C7/C8；旧 Tracer 的反例不是现行证明 | `workbench/tests/test_t127_codex_home_e2e.py:400`～`:452` 的 resume-worker-in-argv/hidden、session-folder-differs 有具体拒收与未绑定断言；`run_worker_delivery.py:349` 只查正常新 session。T-127 票 `:46` 明示有些结果层检查被更早层拒掉，不能说都执行到 gate 结果分支。 | **部分有反例；结果层/所有复用形态未知；INCOMPLETE** |
| review_submit 三字段即时拒坏、Stop 无结果暂停、好结果绑定；最后回复 JSON 不再通道 | t082/t090 尚停旧协议 | `workbench/tests/test_t203_review_submit_e2e.py:142`～`:151` 精确断言，`:159`～`:160` 查两次失败问题号不同。 | **有直接现行断言；INCOMPLETE（本次未跑）** |
| 严格 review envelope、report 对象及必需节、身份/未知字段/Markdown 拒绝、报告完整保留 | t082 `:387`～`:398` | `workbench/tests/test_t082_review_protocol.ts:18`～`:40`、`:55`～`:57` 是 parser/relay 离线断言；`:32` 明确只要求节存在，不保证变异实做。T-203 守坏 verdict/location.line 和正常报告，不含全部 envelope 绑定反例。 | **部分；完整生产绑定矩阵没人守；INCOMPLETE** |
| 伪造 candidate/workspace 审查结果不能被接受 | t082 `:300`～`:307`；旧 Tracer wrong_candidate | T-127 session cwd 反例不同于 review_requirements.workspace 篡改。parser 正确字段不等于核对当次副本。 | **没人守（门禁 workspace/candidate 绑定完整负例）；INCOMPLETE** |
| 改审查 worktree / 共享 refs → 作废、上报、保留副本、不得集成 | t082 `:268`～`:293` | `workbench/tests/test_t082_real_readback.py:51`、`:61` 人工造回执测试观察器；不执行生产审查结束核对。Git metadata guard 是 worker 交付阶段，也非此边界。 | **没人守（生产结束核对）；INCOMPLETE** |
| 结束核对前 integrate 被拒；held socket 干净/脏两对照 | t082 `:322`～`:371` | 近测先等 review_reclaimed 再 integrate，只是避开窗口，不能证明窗口内拒绝。 | **没人守；INCOMPLETE** |
| 审查期间 worker HEAD、dirty、branch 分别改变 → 作废且不删场景 | t090 `:41`～`:64` | 未找到其他三项隔离反例；worker 冻结 C 正例也不替代“审查期间变动”。 | **没人守；INCOMPLETE** |
| 正常结果后副本/审查目录删除，detached、冻结 C、结果→cleanup→reclaimed 顺序 | review_worktree_lifecycle `:27`～`:44`；t082 `:239`～`:244` | `workbench/tests/test_t160_review_recovery_e2e.py:143`～`:146` 是协议失败后新审查时清理旧副本；`test_t187_managed_worker_e2e.py:167` 是 checkout read-only 事件。它们不核对正常结果精确顺序/注册移除。 | **部分；完整顺序/注册项没人守；INCOMPLETE** |
| 两次审查命名 review-1/review-2、不同 id；需修复/通过都清理 | review_worktree_lifecycle `:56`～`:63` | T-160 `:133`～`:137` 检查恢复后的新 review/thread/session/launch，不检查该命名序号与两个 verdict 清理。 | **部分；命名序号没人守；INCOMPLETE** |
| 审查目录脏或 HEAD 未知：保留目录/注册/内容，paused unknown 并 issue | review_worktree_lifecycle `:80`、`:101` | 协议失败后的正常清理不构造脏/未知目录；未找到替代。 | **没人守；INCOMPLETE** |
| reviewer 创建失败、启动中后台重启、回收身份未知时暂停上报 | quality_widen `:283`、`:294`、`:310` | `workbench/tests/test_t160_protocol_idle.ts:54`～`:65` 离线守匹配 Stop 后可回收、unknown 不 kill；`test_t160_review_recovery_e2e.py:133`～`:148` 守协议失败恢复。创建失败与运行时重启场景未替代，hc 重启期望需按后续恢复规格重定。 | **部分；其余没人守；INCOMPLETE** |

### 4.4 工作分支、冲突、R8 与 worktree

| 检查项 | 原测试与断言位置 | 其他现行覆盖、断言位置与局限 | 结论 |
| --- | --- | --- | --- |
| G+C 得 M、父提交/两边内容保留、一次集成后重放不再写 Git | cards `:163`～`:183` | `workbench/tests/run_worker_delivery.py:355`～`:358` 直接核对 M 双亲为 G/C、host 内容与 oracle 保留，`:379`～`:382` 查唯一集成及引用读回；`workbench/tests/test_daemon_recovery_e2e.py:287`～`:293` 直接守同 intent/Git 重放，后者在 T-219 5/5 PASS。cards 额外的验收隐藏 ref/临时分支删除不在前者这些断言中，见下方生命周期行。 | **这些合并/幂等性质有直接覆盖；INCOMPLETE（本次未跑）** |
| 集成失败/未验收不得改分支，外来中间提交尾注也必须检查 | cards `:201`～`:207`、`:142`～`:150` | 当前正向 tests 不构造外来中间提交；bad_worker 也失效。 | **没人守（外来中间提交负例）；INCOMPLETE** |
| 脏 target 的 staged/unstaged/untracked/index/reflog 全保留；linked/未检出分支集成 | cards `:241`～`:261`、`:362`～`:395`；worktree `:275`～`:293` | `test_work_branch_recovery.py:75`～`:84` 有正常中断恢复到干净 M，但不构造这组脏目标/另 linked worktree 情况；其 runner 自身未证当前可达。 | **没人守（完整矩阵）；INCOMPLETE** |
| Git 合并命令给出非 fast-forward 的 M 不可集成 | cards `:465`～`:497` | 无其他已核对的当前输入/断言替代。 | **没人守；INCOMPLETE** |
| worker 目录/分支、验收目录用途序号 detached、结果后验收临时目录删除与隐藏 ref | worktree `:158`～`:229` | `workbench/tests/test_daemon_recovery_e2e.py:224`～`:225` 检查中断重建新 id/目录，非命名或正常清理；T-160 只含 reviewer 目录。 | **部分；命名/正常清理没人守；INCOMPLETE** |
| clean revoke/revise/已集成/run timeout/拒绝后的目录清理、提交留隐藏引用 | worktree `:169`～`:195`、`:386`～`:445` | `workbench/tests/test_t158_revise_retry_e2e.py:176`～`:185` 直接检查 revise 后未回收仍占路径、回收后可派新 worker；未逐一检查 timeout/未提交 commit 隐藏引用等。原 `acceptance/test_run_e2e.py:248`～`:253`、`:343` 有对应源码，但不能当当前可执行证明。 | **部分；余下清理矩阵没人守；INCOMPLETE** |
| 脏/未知回收不删并上报；历史清理只清自己不动当前/foreign | worktree `:244`～`:273`、`:447`～`:514` | T-157 旧 attempt 恢复 UI 防护不是回收目录/hidden refs 的矩阵；没有等价有效替代。 | **没人守；INCOMPLETE** |
| active 路径重叠无理由拒、理由放行并记录；accepted 不占路径 | worktree `:231`～`:242` | `workbench/tests/test_t131_parallel_workers_e2e.py:420`、`:424`、`:435`～`:441` 是 T-197 更新过的完整正负断言。 | **有直接现行断言；INCOMPLETE（本次未跑）** |
| G 改后机械检查在新 M 重跑；CAS 实际竞争保留外部提交 | worktree `:295`～`:321`、`:518`～`:550` | `workbench/tests/test_cas_race.py:39`～`:52` 有新 verification/G/C/祖先/oracle 两次断言，但需 `run_daemon_acceptance.py`/adapter，依赖旧 runner preflight/审计；不能认定当前全绿。T-219 recovery 守 CAS 中断，不制造 G 竞争重验。 | **有同性质源码；有效当前重验入口未知，INCOMPLETE** |
| 第四次 CAS 落空停止，次数绑定原 attempt，重放不重置预算/不重复 issue | worktree `:342`～`:360` | 没有其他当前相同预算反例。 | **没人守；INCOMPLETE** |
| C 不变审查复用但 path/completion/red/rule/trailer 都在新 M 再跑 | s3_quality_joint `:56`～`:71` | 单 CAS/oracle 重跑不统计 review_requested/result/reused，不能替代。 | **没人守；INCOMPLETE** |
| C 变必须新 review/native；冲突 C1→C2 质量失败→C3 全串再验 | s3_quality_joint `:92`～`:102`、`:124`～`:150` | T-160 是同 C 的协议恢复，T-133 修复正例无相同 G/C/review 计数断言。 | **没人守；INCOMPLETE** |
| 文本冲突活会话准确回写一次，同 attempt 新回合显式重交、不自动选内容 | worktree `:728`～`:808` | relay_conflict 也坏；`test_t194_mcp_entry_e2e.py:415` 比较门禁事件同构，不独立构造全部冲突反例。 | **没人守（完整项）；INCOMPLETE** |
| 结束 worker 的冲突换 attempt/fence，旧提交/旧日志保留，新交付不能被旧 request_id 吃掉 | worktree `:810`～`:838`；relay_conflict `:149`～`:176` | 离线 relay-scope 本次失败；现行正向派发/回收不构造冲突重派。 | **没人守；INCOMPLETE** |
| 冲突时 session 未知保留现场；反馈结果未知不重发 | worktree `:840`～`:870` | 没有其他直接场景。 | **没人守；INCOMPLETE** |
| 合并命令本身 exit 73 不是文本冲突，不发修复回写 | worktree `:872`～`:892` | 没有其他分类反例。 | **没人守；INCOMPLETE** |
| 冲突修复后仍查卡外文件/外 Task 尾注 | worktree `:900`～`:922` | 前者旧一律硬拒应按 C13 改成主控判断；T-198 守非冲突卡外行为；外 Task 尾注的冲突后路径没人守。 | **已取代一部分；另一部分没人守；INCOMPLETE** |

### 4.5 任务卡、记录与夹具

| 检查项 | 原测试与断言位置 | 其他现行覆盖、断言位置与局限 | 结论 |
| --- | --- | --- | --- |
| 缺字段/错误类型/argv/source 报具体原因 | cards `:263`～`:301`，daemon_gates 继承 | 现行项目身份 E2E 多为合法卡片；不能替代故意坏卡，且当前 daemon cards 首个 case 正卡项目问题挡住。 | **没人守（可用完整矩阵）；INCOMPLETE** |
| 卡版本 CAS、当前 attempt 快照 B/writer 冻结、旧快照不变 | cards `:310`～`:338` | `workbench/tests/test_t123_project_identity_e2e.py:415`～`:432` 查项目身份/矛盾项目，非整个 snapshot；T-158 测 revise 重派，不核对旧卡 JSON 不变。 | **部分；快照细项没人守；INCOMPLETE** |
| template/source ticket ready_rev 与传入 revision 一致 | cards `:443`～`:460` | 未找到其他完整反例。 | **没人守；INCOMPLETE** |
| 按项目同名任务各自交付集成、尾注完整 id、跨项目参数矛盾拒收 | 第 5/6 组缺少的现行前置 | `workbench/tests/test_t123_project_identity_e2e.py:415`、`:421`、`:426`、`:430`、`:465`～`:478` 直接检查；T-193 已修相邻旧跨项目限制，见本测试 `:400` 注释。 | **有直接现行断言；INCOMPLETE（本次未跑）** |
| launch_records/dispatch_records/orchestration_events 追加式不可 UPDATE/DELETE | daemon_gates `:97`～`:109` | `workbench/tests/test_relay_core.ts:59`～`:61` 只覆盖 relay_requests/results 两张表，不能扩称所有记录表。 | **没人守（三张表可用入口）；INCOMPLETE** |
| 两代 host 自有 operator 凭据、state/mode/可读/继承 launch 隔离及删除 | 第 4 组启动缺口；非它们原业务检查 | `workbench/tests/test_t078_cards_host_bootstrap.py:78`～`:88`、`test_t156_quality_host_credentials.py:105`～`:117` 各自验证 cards/quality host；T-219 两者 PASS，但 serve/PTY 被探针替换。**不覆盖 conflict/multiturn 的 host**。 | **部分（其他 host）；本组三 host 没人守；INCOMPLETE** |
| 回读状态一致性是真实收尾前快照，不以空表/夹具报告代替运行 | multiturn_identity `:192`～`:200` 读回来源绑定 | `workbench/tests/test_state_consistency.ts:26`、`:45`～`:59` 检查重建器抓状态表变异，不证明该 multiturn host 运行快照；`test_multiturn_readback.py` 在 T-219 PASS，票面/索引明确仅夹具读回。 | **部分（观察器）；原运行链未知，INCOMPLETE** |

不能计入的“替代”还有：整份历史 `test_quality_tracer_e2e.py`；直接用 CLI 默认入口却没起后台的 acceptance 文件；只导入 host 的模块；日期 runner 里列了名字但业务步骤没执行；读回脚本的人造事件。`workbench/tests/HISTORICAL.md:14`、`:18`、`:31`、`:41` 已明确这些边界。

## 5. hc 受管窗格开工前的最小迁移清单

**研究建议：NO_GO，先恢复下列当前 node-pty 基线，再开始受管窗格运行时改动。** 这是根据 hc spec `:28` 的“真实后台+真实私有 hc 重新证明”和 `:45` 的“不改门禁检查串语义”推导的建议，不是用户已经裁定的新强制门禁。若没有当前基线，换 hc 后无法区分旧测试/旧协议错误与运行时回归。

“必须迁移”指这些检查必须有一个现行入口；不要求保留重复文件，也不要求所有历史工装先全量翻新。

| 顺序 | 必须先恢复的测试/子集 | 理由与最低验收 |
| --- | --- | --- |
| P0-1 | `test_daemon_gates_e2e.py` 继承的现行卡片/交付/集成检查；其中旧路径案例按 T-198 改。`test_task_cards_e2e.py` 不再独立强求第二个入口。 | hc spec 点名的门禁入口。先消除直接 card_save 项目缺失，证明卡片错误真的到校验层；坏输入拒收、合法 G/C 集成、旧 attempt/fence、记录追加性都要可执行。 |
| P0-2 | `test_quality_chain_e2e.py` 的红态/规则冻结、回写/重交、Stop 无请求、relay 反例；`test_quality_widen_e2e.py` 的 `widen_red_rules_success`、manifest 路径、symlink、坏配置。 | 受管输入由 hc attach 承担，最易让“就绪→回写→新回合→重交”断链。仅 T-219 前五场或一次好交付不能证明 B/C 配对和完整修复链；红态/规则不能在换运行时中被静默漏掉。 |
| P0-3 | `test_protected_acceptance_e2e.py` 保护矩阵及三次上限；`test_bad_worker_e2e.py` 的四字段/缺记录/矛盾尾注/旧 attempt/冻结 C 和正常对照。 | 文件保护、来源身份与拒收后无 Git 副作用是门禁底线，目前只有 T-198 单点 oracle 及正向尾注生成覆盖。t084 可作为四字段的替代迁移选择，但不能两套都留坏、互相引用。 |
| P0-4 | `test_t082_review_boundary_e2e.py` 有效边界全部、`test_t090_review_worker_boundary_e2e.py` 三负例、`test_review_worktree_lifecycle_e2e.py` 四场。 | reviewer 也是受管窗格。要证明结果文件→Stop→结束核对→回收→允许集成，不得因 hc 的异步关闭/重连提前接受；held socket、worker 变动、脏/未知场景不可删。 |
| P0-5 | `test_multiturn_identity_e2e.py` 四场、`test_relay_conflict_e2e.py` 完整冲突重派场景；跨 launch 去重的离线 `test_relay_scope.ts` 也先修前置，作为辅助。 | hc 进程/终端身份和原生回合可能分离。必须同时证明“同原生身份的回执后仍可回收”与“换 native/leader 拒绝”，以及新 attempt 同 request_id 不被旧记录吞掉。单 launch relay-core PASS 不够。 |
| P0-6 | `test_worktree_lifecycle_e2e.py` 当前 worker/verification 命名清理、脏/未知保留、历史只清自己、冲突活/结束/未知/未知发送/命令错误；R8 第四次上限与 CAS 真竞争。`test_s3_quality_joint_e2e.py` 三场。 | 受管生命周期与运行时紧耦合；同 C 复用/新 C 重审、冲突后质量再返工必须不被 hc 换层绕过。先拆掉固定旧源码包/过时运行条件的依赖，保留实际 Git/SQLite oracle。 |

可后置、但不能宣称已覆盖：quality_widen 的脚本格式 roundtrip、终结评分/CAS-score 专用矩阵；quality_legacy 的 claim-only provenance 与额外冻结细项；t084 与 bad-worker 重复部分；conflict_trailer_proofs 的 r3 专用重建；task_cards 的旧无后台入口。**后置不等于标历史**，这些仍是报告列出的缺口。若选择不先迁封闭九字段反例，则受管切片中不得声称已经“重新证明全部尾注契约”；可将它并入 P0-3 的坏 worker 输入，不必保留整个 r3 历史装配。

不必为当前 hc 回归迁整个 `test_t082_parent_launch_e2e.py`：它的固定 START 重建用途与当前回归不同；当前 workspace/tmp 安全反例应由 P0-4 和现行原生边界测试承担。“network-enabled 必拒”不得复活。

以上先在本基线恢复独立正常/坏输入和坏实现证据；实际 hc 切片还必须把输入/进程替换面换成**真实独立 HC_SESSION 的私有 core**，经相同生产后台入口再次留红态、绿态、反例。当前 controlled PTY 测试迁绿只提供门禁语义基线，不能标 hc 通过。后台重启接回同 attempt 的新语义在 hc spec `:38` 后续切片另定，不能顺手把旧“重启则暂停”断言照搬过去。

## 6. 需要用户裁定的问题

| 问题 | 选项与代价 | 研究建议与状态 |
| --- | --- | --- |
| 17 个文件如何处置？ | A 全迁：守护最完整，旧工装成本最大。B 全历史：最快，但多数独有检查无人守。C 按上表拆分，先迁安全/交付/冲突路径，重复与固定旧版本重建另列：需维护逐项迁移清单。 | 建议 C，先恢复第 5 节；**BLOCKED（处置待用户裁定）**，本次未迁移/未标记。 |
| 是否把第 5 节作为受管 hc 开工前的检查基线？ | A 先迁并在当前运行时取得基线，再换 hc：归因清楚，多一个前置阶段。B 与 hc 同票迁：起步快，但旧错误与新运行时错误交织。C 缩到只跑正向交付：成本低，无法声称边界“重新证明”。 | 建议 A，范围以“检查”而非所有文件全量为单位；**BLOCKED（排期裁定）**。 |
| T-084 与 bad-worker 的重复来源矩阵选哪个作先行入口？ | A 先迁 bad-worker 的独立伪造输入，t084 后迁。B 先迁 t084 的记录/卡请求分离矩阵，bad-worker 其余项分期迁。C 都历史：失去伪造四字段及缺记录拒收保障。 | 建议 A，t084 的 unknown/事实与请求分离等独有项继续登记，不能算已被 A 全替代；**BLOCKED（取舍待定）**。 |
| task_cards 与 DaemonCards 如何避免双入口？ | A 当前后台承载同一组业务，旧无后台执行方式历史；保留必要共享 helper。B 两个都迁为独立 daemon 套件：重复维护。C 两个都历史：放弃 hc spec 点名入口。 | 建议 A，需逐项证明继承方法实际运行；**BLOCKED（文件处置待定）**。 |
| 第 7 组如何处理？ | worktree：A 改 sparse/快照/临时目录条件并迁当前路径，旧 baseline 重建单列；B 整份历史。parent-launch：A 固定 START 重建整份历史；B 历史重建与当前 workspace/tmp 反例拆开；C 仅移除外盘检查。 | worktree 建议 A；parent-launch 建议 A 或 B，C 不足以成为当前回归；**BLOCKED（处置待定）**。 |
| 新发现的 relay-scope 失效如何跟进？ | A 并入后续 relay 冲突迁移，先修完整任务 id 前置再证明跨 launch。B 单开小迁移票，保持本票研究边界。C 不修：明确跨 launch 只剩失效端到端，不能声称有人守。 | A/B 均可；本报告保留失败原件，未改 `.project-map/`；**INCOMPLETE（现行测试失效）**。 |

这些问题只给选项，不在研究票内替用户作裁定。不调用其他会话或旧 ticket 的授权来实施。

## 7. 本次补查、运行与交付检查

本次没有重跑 17 个套件，也没有启动后台、Herdr、hc core 或真实供应商 CLI/模型。补跑只为回答一个会改变覆盖结论的事实：“现行离线 relay 测试能否充当跨 attempt 去重替代”。

| 项目 | 结果与可重放证据 |
| --- | --- |
| 起点核对 | **PASS**：分支 `t222-legacy-suites`、HEAD 为报告首行完整版本，工作树开始干净。 |
| session 开始地图 | **PASS**：规定的 project_map.py status，0 problems、0 stale。未改地图/术语表。 |
| `test_relay_scope.ts` | **INCOMPLETE**：exit 1，5 场中 1 场通过、4 场失败；首场首次 receive 就 invalid_relay_request，effects=0，第二次交付断言未执行；`first.task='fixture'`、`next.task='fixture'`（`:15`～`:16`）与 C11 完整身份不符，第三项还出现内存拒绝对象的 undefined 与落库 JSON 比较差异。只据此判定测试不能替代跨 attempt 覆盖，不判定产品跨 launch 去重回归。失败详情保存在 [run.json](relay-scope/run.json)，精确命令/stdout/stderr/清理收据在 [command.json](relay-scope/command.json)。 |
| `test_relay_core.ts` | **PASS（仅离线请求边界）**：exit 0、failure=null、effect_count=5；见 [results.json](relay-core/results.json)、[command.json](relay-core/command.json)。不证明冲突、后台、PTY/hc 或模型行为。 |
| 夹具清理 | **PASS**：两个测试合计 6 个自有临时根目录均已删除，命令收据逐一列路径与 removed=true；原始文本事件、表数据、失败保存在上述 JSON，未覆盖。未产生后台服务。 |
| 编码 | **PASS**：本报告 UTF-8、无 BOM，保存后回读，中文/标识符无替换字符；路径/行号及提交保留原意。 |
| 结束地图、工作树范围 | 见 [SESSION-CHECKS.json](SESSION-CHECKS.json)：结束时地图与 git 状态核对。未 commit、未 push，产品、测试、`.project-map/`、其他 worktree/证据保持未写入。 |

精确重放（从本报告首行工作目录运行；输出参数换成新的空路径，已有原件不要覆盖）：

```sh
TMPDIR=/private/tmp node workbench/tests/test_relay_scope.ts \
  /Users/luckye/Documents/Code/a2a-worktrees/T-222/workbench/src/relay.ts \
  /Users/luckye/Documents/Code/a2a-worktrees/T-222-evidence/relay-scope-replay-NEW

TMPDIR=/private/tmp node workbench/tests/test_relay_core.ts \
  /Users/luckye/Documents/Code/a2a-worktrees/T-222-evidence/relay-core-replay-NEW
```

重放后从结果 JSON 取其实际 `root`，只清理该次创建的 `/private/tmp/t077-relay-scope-*` 或 `/private/tmp/a2a-relay-core-*` 根目录；本次真实命令和逐目录清理已记录，脚本没有为“变绿”改输入。

**最终状态：PASS（限定为研究报告完成）；当前旧套件保障 INCOMPLETE，受管 hc 新证明未开始，处置 BLOCKED 于用户裁定。**
