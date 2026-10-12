# T-077-1 实施计划（2026-10-11，待执行主控批准）

状态：**INCOMPLETE**。已完成规格与起点代码核对；尚未实现、运行红态或启动真实 Codex。实施有两项阻塞，见第 2 节。本文件交回后停止，等待执行主控答复。

2026-10-11 主控 `⟦主控 #20⟧` 进展：已读取并逐字节留档 [controller-decision-01.md](controller-decision-01.md)。原 PLAN 获批，B1 按该决定获本次 hook 授权；B2 改为“断言白名单先批后改”。下方第 12 节为待批准白名单；第 2 节保留原始发现及当时状态。目前只修改计划/证据，未改产品或测试，真实回合仍为 0/4。

任务：T-077-1；来源 T-077，`ready_rev: 1`；worker：`s13-t077`；分支：`exec/t077`；唯一写入 worktree：`/Users/luckye/Documents/Code/a2a-wt-t077`。起点完整提交：`14b57d22a84bcaebfa91c5051b9909b53a570fac`，开始时工作区干净。派发依据为本会话 `⟦主控 #18⟧`。

## 1. 目标、边界与依据

目标是实现 T-077 What to build 1～6：命名、按表清理与隐藏引用、认领路径交集、冲突回写、R8、检出工作区保护及上报。完成条件逐条取自 [T-077](../../../.project-map/tickets/T-077-worktree-lifecycle-conflicts.md) 与原生 CLI spec 第 3、4、12 节；第 13 节 R8 和既有恢复契约约束异常边界。

非目标：T-076 的质量串实现、真实 reviewer 编排与打分；T-078 的主控与收件箱；面板 UI；存储迁移。只用现有表、JSON 记录与追加事件，不建表、改 DDL 或迁移 membership。不修改 `acceptance/test_*.py`、`scripts/`、spec、地图、全局配置或主 checkout。ticket 只在获准实施后的交付阶段写 Resolution，保持 open、待主控关闭。

已读取：本仓库 AGENTS、CONTEXT、第三阶段 intent、MAP、T-077、T-076、T-075 的验收与修订；相关 spec；门禁核心与 CLI/schema、任务卡路径规则、daemon、Panes、store、任务卡与 CAS 测试、旧 8/9/18 相关断言及后台适配运行器。session 开始 `project_map.py status` 为 0 problems、0 stale。

采用 **Ubiquitous language**：task、attempt、受管身份、原生会话、交付、验收、集成、回收各自保留含义。回合结束不等于原生会话结束；回收窗格不等于验收通过；文本冲突不等于 CAS 落空。

采用 **Deep modules**：Git 生命周期与状态变更由 `A2AGates` 负责；Panes 只负责已绑定会话的观察与投递。不另建生命周期服务、第二套集成入口或策略引擎。

## 2. REALITY GATE：INCOMPLETE

下列事实来自起点源码静态核对，尚无本卡运行测量。

| 分类 | 事实及影响 |
| --- | --- |
| observed | `core.ts:2209` 使用随机 attempt 路径并 detached；verify 在随机目录中运行；没有按 S3 表清理的实现。 |
| observed | `taskCards.ts:pathAllowed` 已定义文件精确匹配、末尾 `/` 的目录前缀、`.` 全仓和 deny 优先，不支持 glob。交集必须沿用同一集合语义。 |
| observed | `core.ts:2422` 将所有合并命令非零退出视为 `merge_conflict`，没有冲突回写；submit 的候选冻结检查不允许修复后换 C。 |
| observed | `core.ts:1194` 起已有 Git 引用事务和 `read-tree -n/-m -u` 保护检出目录；缺少 S3 要求的问题上报，不能把已有保护说成本卡新增。 |
| observed | `panes.ts:113` 的单 worker 限制按 Map 大小计算，已归档的旧窗格也占名额；结束会话后开新 attempt 需要修正这一处生命周期判定。 |
| observed | T-076-1 正在另一个 checkout 修改 core/daemon/panes；本分支尚无它的变更。不得假定其接口已存在。 |
| inferred | 现有 events、attempts/verifications 的 JSON 和 issue/inbox 记录可承载 S3，不需要改变存储结构。JSON 的新增业务字段须随状态事件一起保存。 |
| unknown | 下述 B1/B2 的处理决定、T-076-1 最终接口与代码版本；在批准前不运行依赖这些决定的实验。 |

### B1：无 hook 与当前真实入口不相容（阻塞真实场景）

本卡要求真实 Codex“无 hook”。当前 `panes.ts:116` 强制要求 `hook_authorization`，`:140–141` 用启动参数安装三个 Codex hook；`:153–154` 还注入 Git 尾注 hook。`daemon.ts:41–44,73–99` 与 `cli.ts:171–180` 的 B 通道只在 Stop hook 后转交显式请求。完全无 hook 无法按当前生产入口完成受管交付。

建议最小选项：执行主控明确本卡是否允许**仅本次启动参数中的现有会话 hook，以及现有尾注 hook**，隔离 HOME 不复制或落盘用户 hook 配置。若“无 hook”包含这些，真实场景保持 BLOCKED，需另行决定交付通道；本卡不实现新通道、不伪造 Stop、不由主控代交 worker 候选、不自行修改权限。

### B2：新语义与禁止修改的旧断言冲突（阻塞完整验收）

静态矛盾至少包括：

- `acceptance/test_coop_e2e.py:456–474`：一次 G 变化必须立即 `integration_conflict`，引用和 reflog 不动；R8 要求自动在新 G 上重验。
- `acceptance/test_run_e2e.py:236–247`：自动 run 已集成且 reclaimed 后仍读取 worker 目录，并要求目录存在；S3 要求已集成且干净的删除。
- `acceptance/test_coop_e2e.py:348`：撤销后目录保留；S3 清理表要清理干净的撤销 attempt，执行时机也须一致。
- 允许修改的 `workbench/tests/test_task_cards_e2e.py:152,395` 和 `test_cas_race.py` 也分别假定验收目录继续存在或 CAS 立即拒收。修改这些业务预期仍须按任务卡先交主控确认。

`test_recovery_e2e.py:561` 要求保留中断验收目录，这与“未知不删”、保留故障证据一致，拟保留该断言和行为，不把所有目录保留断言一概废除。

建议由执行主控列明需修订的历史断言及授权范围，或由独立切片更新验收后交给本卡复跑。本 worker 不改禁区、不在适配器中跳过/替换业务方法、不伪造目录或返回值、不保留旧行为开关来凑 8/9/18 全绿。未解决时只报告 INCOMPLETE，不能交付整卡 PASS。

这两项按任务卡“需要改业务断言／权限或验收冲突就停下”的规则上报。本次只完成可审阅计划；不将项目旧记录视为新增授权。

## 3. 命名、清理与隐藏引用

### 命名及实现位置

拟在 `workbench/src/gates/core.ts` 的 claim/dispatch、verify、reclaim/revoke 及结束路径实现；类型/CLI 的新增必要参数在 `contracts/a2aGates.ts`、`gates/cli.ts`。不修改存储层。

- 将 spec 的 `<项目>` 落为后台现有 worktree 根下的项目命名空间：`<state>/worktrees/<project_id>/`；worker 目录为 `<任务卡号>-a<N>`，分支为 `a2a/<任务卡号>-a<N>`。目录不放进用户 checkout，避免引入未跟踪目录。此为待主控审阅的具体落点。
- N 使用 task 已有且只增不减的 claim fence；撤销、失败与重启后不复用序号，attempt UUID/session/fence 的身份职责保持原样。核对现有 fence 的全部写入点后再落代码。
- 验收为同目录下 `<任务卡号>-a<N>-verify-<K>`，detached；K 根据该 attempt 已持久验收意图单调递增。reviewer 后续使用 `-review-<K>`，由 T-076-2 接入同一命名和结束清理能力；本卡不启动真实审查会话。
- 创建前检查目录、分支与登记身份；已有但不能核对的目录不覆盖、不接管。使用 Git 自身路径/ref 校验，失败保存 intent 与诊断。

### 清理表与时机

所有清理绑定显式 task/attempt/session/fence，持有同一任务操作锁；先核对注册 worktree、实际 HEAD、分支、工作区状态与进程所有权，再操作。机械失败、未知和 dirty 均进入保留与 issue，不做强制删除。

| spec 清理行 | 拟实现流程 |
| --- | --- |
| 已集成、干净 | 已提交、会话 idle/停止确认、窗格回收完成后，先保存隐藏引用并读回，再 `git worktree remove`，最后删除已核对且指向预期 tip 的 worker 分支名；保留全部事件。集成完成但 worker 尚忙时不删。 |
| 打回、撤销、放弃、干净 | attempt 确认结束、不再承载修复回合后，先保留隐藏引用，再删目录；按清理表保留分支名。同一 attempt 内仍要修复的打回只记回写状态，不抢先删活跃 worker 的目录。放弃命令与打分接口接 T-076 的终结路径，不另做第二套打分。 |
| 任何结局、有未提交改动或未知 | 不删目录或分支；问题条目含状态、路径、HEAD、原 attempt 和失败证据，交执行主控。未跟踪文件、索引改动、合并中、权限失败、路径或身份变化分别覆盖。 |
| 验收/审查临时目录 | 结果、逐命令输出、G/C/M、冲突文件和必要差异已存入现有持久记录后删除已完成用途的临时目录。失败现场先完整保留证据；中断/副作用未知或进程仍运行时保留原目录，不假定记录了 interrupted 就可删。reviewer 结果落库由 T-076-2 通知同一结束接口。 |

隐藏引用固定为 `refs/a2a/attempts/<任务卡号>/a<N>`，指向待清理 worker 的已核对 HEAD。已集成路径要求 HEAD 与已交付 C 一致；不一致视为待核对，不能用“Git 干净”掩盖未交付提交。撤销/放弃允许保留尚未 submit 的干净提交。更新引用使用期望旧值，读回引用和提交对象后才能移除目录。写引用失败则不删；删除失败保留引用和失败事件；重复清理必须读回已有结果，不能重写另一 attempt 的引用。

验收目录删除后、集成前，M 可能尚未由工作分支引用。拟用用途专属的内部引用 `refs/a2a/verifications/<任务卡号>/a<N>/v<K>` 保住已存结果对应的 M，避免 GC 使已验证对象消失；它不替代规定的 attempt 隐藏引用。冲突失败没有 M，须先存冲突原始信息，不能制造通过引用。

S5 前上报使用现有 issue/inbox 表，来源标为 system、收件人为执行主控，refs 绑定原身份。复用现有追加写能力，不伪装为 worker 的 `raiseIssue`，不要求一个已退出 worker 的 active caller；`issues`/`inbox_list` 可读回。本卡不会改 `scripts/inbox`，开发发现仍通过该脚本报告。

## 4. 路径交集与理由

认领入口在创建 attempt/worktree/窗格之前检查；claim、dispatch 和 run 的 dispatch 都经过同一逻辑。比较同一真实 Git 仓库的活跃 attempt，不能只按 project 显示名比较，否则一个仓库登记成两个项目会漏检。拟核对 Git common dir 作为仓库身份，并在现有 SQLite 主库短事务内完成“读取活跃占用 → 检查 → 保存 claim 意图”，避免两个 task 各持自己的操作锁同时通过。事务不跨 Git 或网络 await，不增加锁表。

判定用路径集合运算，不靠扫描现存文件：尚未创建的路径也可能冲突。每个 allow 是单文件、目录子树或全仓；两两求交，减去双方 deny。两个文件只在相等时交；文件与目录按 `/` 边界判断；两个目录取更深的子树；`.` 为全集。若交集是文件且被任一 deny 排除，则不冲突；交集是目录时，只有被 deny 覆盖整棵子树才消除，不能因当前目录为空判无交集。`src/` 与 `src-other/` 不相交，`src` 与 `src/` 按现有“文件/目录”规则区分。不增加 glob 或内容含义分类器。

活跃占用覆盖 preparing、claimed、submitted、verifying、verified、integrating、修复中以及身份/退出未知的 attempt；已撤销但未确认退出的旧执行者仍占用。确认终结并回收的历史 attempt 不继续阻挡。

拟增加 `--overlap-reason`（最终名称与 T-076 接口协调后固定），仅执行主控入口可带，空白理由不算授权。无理由默认拒绝，留下冲突 task/attempt、双方卡快照、交集与路径规则；有理由允许并记原文、调用者来源和放行的冲突集合。worker 转交的允许命令集不扩成认领权限。不能在发现新的第三个交集后沿用旧记录来静默放行。

## 5. 文本冲突回写与新 attempt

以真实 `git merge` 结果及 `git ls-files --unmerged -z` 判定文本/内容冲突；非冲突 Git 错误、锁/权限失败不能一律包装成可修复冲突。

1. verify 在最新 G 上生成 M；发生冲突时，先保存 verification、G/C、冲突文件、Git 输出和原始差异。工作分支与 worker worktree 均不由程序改写。
2. 给原 attempt 记一次明确的修复请求，解除该次候选的“只能重交同 C”限制；旧 submit/verification 记录保持。普通 submitted 状态仍禁止无原因换候选。
3. 经 T-076 的 gate 投递能力发 `⟦门禁 #序号⟧`：列明冲突、已观察到的工作分支头，要求 worker 基于最新头整理、自己解决取舍、重跑完成条件、提交并显式重交。发送前再次核对 original attempt，未知投递不盲重发。
4. 同一原生会话仍活跃且身份相符时继续原 attempt；回合变化接 T-076-1 的原生会话/进程与交付回合分离，不放宽身份验证。忙时排队，不把回合 Stop 当作原生会话结束。
5. 仅在原生会话结束可证实时，经同一门禁终结旧 attempt、保留候选与现场，再从最新 G 开新 attempt、新 UUID/session/fence/worktree/分支。新 worker 获得旧 C 和冲突说明，自行形成带新 attempt 尾注的提交；程序不自动 cherry-pick、rebase 或择取 ours/theirs。Panes 只解除“已确认归档的 pane 仍占活跃名额”这一限制，不借机实现多窗格 UI。
6. 旧 run 的 verify/integrate/reclaim 继续绑定旧 attempt；它返回 superseded/待处理，不能因为 current_attempt 改变而接管新 worker。重复 verify、重复回写请求不能多建新 attempt。
7. 新 C 必须重跑整串；本卡接回 T-076 机械检查和后续 reviewer 入口，不复制一套质量串。

基线衔接：`checkPaths` 与 `checkTrailers` 当前都从原 `attempt.base_commit` 计算。冲突整理会把其他任务已集成的提交带入 C，不能将其误记为当前 worker 越界。拟保留 claim 的原始 base/card 快照，在明确冲突修复请求中另记门禁观察到的工作分支基线，重交时校验其与 C、当前工作分支的祖先关系；仅对该交付新增的 worker 提交核对路径/尾注，并继续检查新 G→M 的净改动。不能由 worker 任填一个 base 排除违规提交，也不能简单删掉尾注或路径检查。此处与 T-076-1 紧密重叠，合流前由主控核对具体 diff 与反例。

## 6. R8 与 T-076-2 衔接

在一次集成编排中显式处理确定的 CAS 失配，不做通用 catch/retry。第 1、2、3 次已确认失配分别保存计数、旧/新 G、C、verification/intent 与 attempt 后，重新在新 G 上创建 M、重跑所有机械检查；第 **4** 次失配停止，不启动第 4 次自动重验，追加 issue，交执行主控。

连续计数与原 attempt、候选 C、spec/card 快照组成的重验链绑定，存在既有 JSON/追加事件中；重启或客户端重发 integrate 不把计数归零，同一失败 intent 的恢复不重复计数。成功集成结束链；worker 有依据地重交新 C 开新链并重审。卡/spec 变化使旧证据失效。

集成前读回 G 已变化，和 Git 引用事务 prepare 明确 CAS 失败，均需覆盖；后者只有证明引用事务未提交、检出目录未改写时才可重验。持久 pending intent 中断后出现第三值、命令结果丢失、目录已改但记账未知，仍走既有 `needs_reconciliation`，不能算普通 R8 自动覆盖。Git 非 CAS 错误不计数也不重试。

从现有 verify/integrate 的锁内代码提取必要的内部执行段，让显式 verify 和 R8 使用同一质量串；不在持有操作锁时递归请求同一门禁导致自锁，不在重验间释放所有权给另一执行者。状态查询仍可用。

T-076-2 尚未实现真实 reviewer。本卡仅预留业务衔接：重验输入/结果带 `candidate_commit`、attempt/session/fence、spec/card、当前 verification、重验原因及已有 review 的引用。沿用审查只适用于 **C 与上述合同/身份均未变** 的 CAS 重验；G/M 变化不允许沿用机械检查。C 改变、文本冲突重交、规格或 attempt 改变均请求 fresh review。T-076-2 负责生产/核对审查结论与会话独立性，本卡不接收一个裸 `review_passed` 布尔值替代它。

此阶段可用内部边界的独立假记录证明“同 C 选择沿用／变 C 要重审”的路由，但必须标为接口测试，不能称真实审查完成。T-077 的真实审查沿用部分在 T-076-2 接上后需联验；在此之前 ticket 保持 open，并在 RESULTS 逐项写清 INCOMPLETE。

## 7. 检出工作区检查

复用 `integrationWorktree`、`checkIntegrationHead`、`advanceWorkBranch` 和 `checkIntegratedContent`。目标分支在其他 worktree 检出时只在该目录快进；更新前核对检出身份，引用事务 prepare 锁定预期 G，再 dry-run 双树更新、真实更新、提交引用事务、读回内容。禁止 stash、reset 用户目录或改写 Git 配置。

覆盖修改：tracked 的 unstaged/staged 修改、删除与候选新增路径上的未跟踪文件均必须拒绝，新增 system issue；拒绝后逐字节比较文件和 index，并比较 status、ref/reflog。与集成路径不重叠的修改按 spec 第 3 节和现有行为保留并允许快进；不能把 ticket 中“有未提交改动”扩成不分覆盖关系的一刀切。目标目录在核对后换分支、出现多个匹配或无法读取时停止并保留 intent。

已有拒绝行为在起点应当通过；本卡新增的“拒绝并上报”整体验收在起点应红。对已存在的保护用定向变异体验证检测能力，不伪称起点缺少保护。

## 8. 实施顺序与红态／反例

先等计划和 B1/B2 处理决定。所有验收预期从本表及 ticket/spec 写定，再实施。**Tracer bullet** 首先做一条真实 CLI→后台→claim 命名→提交/验收→集成→回收→隐藏引用读回的生产路径，再扩大到拒绝、冲突和竞争；不先做完一个独立“生命周期层”。

拟在 `workbench/tests/` 新建 S3 端到端运行器与案例，复用现有短 `/tmp` 后台生命周期夹具，不改变旧业务断言。每条新行为先在冻结起点运行同一信号，保存失败，再修改生产代码。冻结起点可用只读源码快照加候选测试运行；不要切换/重置本工作分支或覆盖已有失败文件。启动、导入、socket、缺依赖错误都不是业务红态。

| 项 | 起点预期红态与候选正例 | 反例／独立读回 |
| --- | --- | --- |
| 命名 | claim 得 `T-077-1-a1`、指定分支；下一 attempt 是 a2；verify 目录带用途与序号且 detached | 重启/撤销/创建失败后不复用；预占目录/分支不覆盖；不同项目任务不串用 |
| 已集成清理 | 集成且干净，回收后目录和分支名消失，规定隐藏引用可 `git show` | 未确认停止、HEAD 不符或原 attempt 已换不能删；重复清理不影响新 attempt |
| 打回/撤销/放弃清理 | 各一个终结正例，隐藏引用存在、目录删除，原始事件保留 | 活跃修复回合不删；错 attempt 不删；隐藏引用写入失败不删 |
| dirty/unknown 保留 | 脏、未知各有不删与 issue 正例；比较原始文件、index、refs | 省略 dirty 检查、引用保存后错误清另一个目录的变异体必须失败 |
| 验收/审查用途清理 | 已存完成结果后删除，M 与结果可读；review 用途只验证接口 | 中断 oracle、未知输出保留；未存结果不能清理；保留故障工件 |
| 路径交集 | 同仓两任务无理由拒绝，有理由放行并读到原文；无交集正常通过 | 文件/目录/`.`/deny、空目录未来路径、同仓不同 project、相邻前缀；并发 claim 屏障保证至多一个无理由占用者 |
| 活会话冲突 | 真正同文件冲突写回原 worker；C2 重交、全部检查再跑后集成 | Git 权限/锁错误不作为文本冲突；旧 fence/session、未经回写擅换 C、伪造整理基线拒收；不改两边内容来“自动解决” |
| 已结束会话冲突 | 确认结束后新 attempt 获得冲突背景；旧身份失效 | busy/unknown 不等同 ended；旧 run 不接管新 attempt；重复回写不产生重复 attempt |
| R8 | 独立 Git 写者制造 1～3 次 CAS 失配后成功，机械检查逐轮作用于新 M | 第 4 次停止、issue、引用不被盲写；同失败重放不重计；非 CAS 错误和 unknown pending 不重验 |
| 审查接口 | 同 C 的 CAS 重验沿用同一有效 review 引用；C2 明确要求重审 | attempt/spec/card 变化拒用旧结论；机械检查失败不能因旧 review 放行；不声称完成真实 reviewer 验收 |
| 检出工作区 | 主 checkout 和 linked worktree 各有覆盖型 dirty 拒绝及 issue | 文件/index 字节不变；无覆盖 dirty 保留；目标切换、未跟踪碰撞、中断恢复不退化 |
| 回归 | B2 获解决后重跑 8/9/18、任务卡与后台门禁正反例、CAS/目录更新中断 | fence、CAS 期望旧值、操作锁既有反事实仍有效；不得用旧候选的通过背书 |

单独测试集合交集时，先列出上表中的文件/目录/deny/空路径/同仓并发失效方式，再用手写期望集合；测试不调用生产 `pathAllowed` 来计算答案。其余优先真实 CLI/Git/SQLite。

脚本制造并发提交只改独立夹具，屏障放在已有可观察 Git 操作边界。记录每轮 G/C/M、Git 父关系、命令结果、完成条件运行标记、数据库事件和 issue；R8 与状态回读断言不依赖模型自报。

## 9. 至少一个真实 Codex 冲突场景与预算

前提：B1 已明确、T-076-1 的多回合身份/重交接口已合流。固定当前产品要求的 CLI 版本（起点是 `codex-cli 0.162.1`），被测 worker 为 `gpt-6.1-sol`、xhigh、`-c 'service_tier="fast"'`、`check_for_update_on_startup=false`；不是本卡实现 worker 的 Astra。记录完整启动 argv、请求 tier 和实际可观测字段，不能把请求当实际供应商 tier 证明。

夹具为 `/tmp` 独立仓库中的小型时间汇总程序：worker 修复跨小时、重复名称合并及非法输入处理；独立并发作者在相同函数同一行增加“允许首尾空格”的合同既定行为，同时改一份不在 worker allow 范围的文件，并带另任务的合法尾注。两份改动必须都保留。oracle 在工作树外，使用卡上预先写定的输入/输出与退出码，不给模型一份待抄的完成文件；至少包含跨小时、重复名称、空白、非法值和未改路径断言。

1. 主 turn 1：真实 worker 完成首次 C1、提交并显式 submit。独立脚本在 claim 基线之后提交 G1，确保验收形成真实同文件冲突。
2. 主 turn 2：若沿用现有 B 通道，是首次异步交付回执确认；等其确认为 idle 后发起 verify，门禁保存冲突并自动回写，不由测试直接注入一份“正确修复”。
3. 主 turn 3：同一真实 worker 接收冲突说明，自己基于 G1 整理、解决冲突、执行完成条件、提交 C2 并显式重交。独立 oracle 与 Git 读回证明 C2 同时保留双方行为、未越界，门禁重跑整串后集成。
4. 主 turn 4：C2 的异步回执确认。之后不再自动派发新回合；未知状态或失败立即交主控，不申请额外模型重试。

预算上限 **4 个被测主 turn，包含回执回合**，所有 attempt 合计；当前消耗 0/4。已结束会话的新 attempt 场景首先用受控运行时验证，不额外开真实 Codex；如真实主场景耗满，不把这一脚本证据写成第二个真实场景。独立代码审查不与被测 worker 混算，但其启动由执行主控安排，不能借审查额度增加被测回合。

`CODEX_HOME` 在 `/tmp`：只复制 `auth.json`，只信任核对过的夹具根，只放行 `git add`/`git commit` 两条规则。hook 在 B1 答复前不安装。认证文件不进 Git/归档；结束核对所有自建进程已退出，再删整个隔离 HOME。只记录路径和删除结果，不输出凭据。

## 10. 预计与 T-076-1 的冲突位置

以下是本起点函数/区段，不假定主 checkout 的未提交内容：

| 文件/位置 | 本卡改动 | 必须保留 T-076 意图 |
| --- | --- | --- |
| `gates/core.ts:GateRuntime`、`checkThread/observeRun` | gate 冲突投递、原生结束判定、新 attempt 衔接 | 原生会话/领导进程与交付回合分离、身份负例 |
| `core.ts:claim/dispatch`（约 2177～2273） | 命名、路径占用事务、理由、冲突后重建 | 启动记录、模型/强度与尾注环境、卡快照 |
| `core.ts:submit`（约 2300～2361） | 只有明确修复请求允许 C2、整理基线校验 | T-076 的重交状态机、回合绑定，不能各做一条允许换 C 的分支 |
| `core.ts:checkPaths/checkTrailers/verify`（约 1242～1290、2364～2493） | 排除已集成基线贡献、冲突保存/回写、用途目录清理、同串重验 | 完成条件、红态、规则式检查、打回计数、尾注检查顺序与各自证据 |
| `core.ts:integrate/run/reclaim/invalidate` | R8、dirty issue、终结清理、旧 run 绑定 | 打分/放弃和拒绝回写，原锁及中断恢复 |
| `daemon.ts:signal`（约 73～99） | 复用 gate 回写并保证冲突通知与回执顺序 | 现有 relay 身份与幂等；不得引入重复回合 |
| `panes.ts:createThread/dispatch/readThread/archiveThread` | 只回收活跃名额、已结束会话判据、冲突消息 | T-076 的多回合身份、请求模型来源、回执/打回预算计数 |
| `contracts/a2aGates.ts`、`gates/cli.ts`、README | 必要字段与 overlap 理由、状态/命令说明 | T-076 新参数/错误语义和文档，不另造兼容入口 |

自己的 worktree 是唯一写入区。实现前与主控确认 T-076-1 的合流时机；交付前 `git -C /Users/luckye/Documents/Code/a2a-wt-t077 rebase main`，逐处保留两边意图。变基后的完整候选再跑本卡完成条件与 8/9/18；若业务断言冲突未解决，停下报告，不通过删除他人行为解决。

## 11. 沙箱外运行、证据与交付

批准实施后准备 `evidence/2026-10-11-batch13/T-077/outside-sandbox.sh`，仓库路径全部使用本 worktree 的绝对路径；分阶段参数至少区分起点红态、候选绿态、真实冲突、变异体和变基后回归，每次输出到不存在的新目录。脚本运行前检查挂载、版本、依赖和短 socket 路径，不重装依赖。

需要主控在沙箱外运行的项：

- CLI/socket→真实后台的所有集成测试、后台重启和终止；后台必须独立进程组。
- node-pty 的 zsh/Codex、`ps` 领导者核对、归档和只针对自建进程的信号。
- `/tmp` 夹具的并发 Git 写者、故障屏障、后台/命令中断恢复。
- 真实 Codex 认证副本与经明确批准的会话配置、原生轨迹收集、结束清理。
- 大文件外置盘归档；本卡无 UI 改动，不预定 Electron 验证；若验收要求追加 Electron，先在该脚本列明，不自行扩大。

沙箱内做阅读、计划、允许范围编辑、文本/离线纯逻辑检查与 diff。脚本就绪后只报告 `T-077 OUTSIDE-SANDBOX READY` 并停下，由执行主控跑；本 worker 不申请提权、不尝试绕过 socket/进程限制。

最终冻结候选后，做一次 fresh-context 只读独立审查（按任务卡配置由执行主控安排），使用 behavioral-acceptance-review 核对独立 oracle、反事实和证据边界；必要的 R8 结构风险也一并检查，不重复开审。发现产品问题先红态再修，修复 diff 交执行主控审，不自行反复追审。

RESULTS 用中文，按 T-077 每项列 PASS/INCOMPLETE/BLOCKED，含完整候选提交、真实回合消耗、环境与命令、起点红态、绿态、反例和未完成边界。原始失败只追加，不覆盖。运行前后保存 Git/SQLite 独立读回；证据工件带精确重放命令。单文件超过 5 MB 的原始输出压缩或放 `/Volumes/WD-Elements/a2a-evidence/2026-10-11-batch13/T-077/`，不把内嵌 repo 加成 gitlink；不归档隔离 auth。

收尾检查：`find evidence/2026-10-11-batch13/T-077 -type f -size +5M`、diff 范围、Git 尾注、`project_map.py status --root .`。如 README 更新导致地图 Verified 待同步，上报主控处理，不越界改 MAP。git add、git commit 各自独立执行，只提交本卡授权文件，不 push。

本次计划交付后停止，不提交实现、不更新 ticket 状态、不进入真实验收。下一行动的负责人为执行主控：处理 B1/B2、确认计划及 T-076 合流接口后再下达实施指令。

## 12. 断言白名单（W01～W16，待主控批准）

本节依主控决定 01 提交审阅，**尚不授权修改断言**。行号固定对应起点 `14b57d22a84bcaebfa91c5051b9909b53a570fac`；变基后同时按方法名定位，不把行号漂移理解为授权扩大。涉及 `acceptance/` 的改动仅申请下列两个文件的指定位置；`test_recovery_e2e.py` 整份不改。

### 12.1 独立预期的规范原句

下表代号直接用于白名单的“依据”列，不以当前实现返回值生成预期。

| 代号 | 规范与原句 |
| --- | --- |
| S-N | 原生 CLI spec 第 4 节：“目录 `<项目>/<任务卡号>-a<序号>`，分支 `a2a/<任务卡号>-a<序号>`”；“验收与审查用的 worktree 在其后加用途与序号，detached”。主控决定 01 已批准 `<state>/worktrees/<project_id>/`。 |
| S-I | 同节清理表：“已集成”“干净”“删目录与分支名；提交留隐藏引用 `refs/a2a/attempts/<任务卡号>/a<序号>`；事件与历史全留”。 |
| S-E | 同节清理表：“打回、撤销、放弃”“干净”“留隐藏引用，删目录”。T-070 冻结契约改动：“清理干净的 worktree、提交留隐藏引用，取代‘保留所有 worktree’（D25）”。 |
| S-U | 同节清理表：“任何结局”“有未提交改动或状态未知”“不删，上报到面板”。 |
| S-V | 同节清理表：“验收、审查用的”“结果存库后删”。主控决定 01 同意“额外的隐藏引用 `refs/a2a/verifications/...`，用来让已验证的 M 不被回收”。 |
| S-R | spec 第 3 节第 7 步：“CAS 落空（分支已变）时自动重新验收：机械检查在新的 M 上重跑；审查结论绑定候选提交号，候选不变时沿用。”T-077 Acceptance：“连续 CAS 落空到第 4 次时停止自动重新验收并上报”。 |
| S-P | spec 第 3 节第 1 步：“允许路径与活跃 attempt 有交集时默认拒绝派发，执行主控要并行须写理由，记下来。” |
| S-G | spec 第 3 节第 7 步：“CAS 把工作分支从 G 推进到 M，不 push”；第 3 节末：“锁、fence、CAS、attempt 绑定与中断恢复的语义不变。” |

记号：C 是夹具在调用门禁前独立读出的候选；G1 是独立外部作者提交；H 是清理前独立读出的 worker HEAD；A(N) 是规定的 attempt 隐藏引用；V(N,K) 是已批准的验收用途引用。不得通过“忽略所有 `refs/a2a/*`”实现断言迁移。引用比较使用 `git show-ref` 解析后的**完整映射**，明确预期添加/删除的每个引用名和目标，其他引用逐项不变。原始输出仍保存，不以哈希比较替代内容读回。

### 12.2 业务断言迁移

| 编号 | 文件、方法、起点行号 | 旧断言/前提 | 拟采用的新断言 | 依据与对应红态 |
| --- | --- | --- | --- | --- |
| W01 | `acceptance/test_coop_e2e.py`，`test_baseline_change_after_verification_rejects_integration`，456～474 | G 变化一次后 integrate 必须失败 `integration_conflict`，ref/reflog 不动且未 accepted。 | 同一次 integrate 在 G1 上重新完成机械检查后成功；C 不变，新 verification 的 G=G1，M 同时以 G1/C 为祖先，独立分页 oracle 在新 M 再运行一次；外部文件字节保留，工作分支=M，reflog 仅多一次最终集成，重放不再增加。方法名可改成 `test_baseline_change_after_verification_revalidates_and_integrates`。 | S-R、S-G。红态 R-W01：起点立即返回 conflict，未产生新的完整验收；不把单纯错误码变化当作绿态。 |
| W02 | `acceptance/test_coop_e2e.py`，`test_identity_gates_and_revocation_reject_old_verified_attempt`，343～348 | 已 verify 的干净手工 claim 被 revoke 后目录仍存在。 | revoke 后原目录不存在，A(N)=撤销前已提交 C 且对象可读，原 worker 分支按清理表保留；task 仍 ready、候选和 verification 清空，原有 session/fence/spec/旧 attempt 拒绝及事件前缀断言不变。 | S-E。红态 R-W02：起点保留目录且无 A(N)。 |
| W03 | `acceptance/test_run_e2e.py`，`test_run_entry_point_completes_registered_task`，219～220、236～247；其调用者 `test_transient_tool_activity_keeps_same_thread_owner` 复用同一组断言 | run 已 reclaimed 后仍读 worker `pager.py`，并要求 worker 目录存在。 | 在 submit 前保存独立候选的 `pager.py` 字节；完成后主 checkout 文件/index/HEAD 与 C 一致，worker 目录和分支均不存在，A(N)=C、对象可读；原独立分页 oracle、单 prompt、只关闭自身线程、原生领导者/辅助进程身份断言全部保留。 | S-I、S-G。红态 R-W03：起点目录仍在且无规定分支清理/隐藏引用；两种线程情形分别留结果。 |
| W04 | `acceptance/test_run_e2e.py`，`test_done_without_submit_hits_deadline_and_cannot_accept_committed_candidate`，324～333 | timeout 后所有 refs 与启动前完全相等，仍从 worker 目录 HEAD 读未 submit 的 C。 | 集成分支和原有引用/reflog 不动；只允许本次 claim 创建的具名分支及终结清理保存的 A(N)，二者指向夹具已知 C；确认回收后干净目录删除，C 经 A(N) 读回。`candidate_commit is None`、oracle 零次、run_deadline、不得 accepted 与只关自身线程不变。 | S-N、S-E、S-G。红态 R-W04：起点没有 A(N)、目录未清；不能将保存一个提交说成已 submit 或已集成。 |
| W05 | `acceptance/test_run_e2e.py`，`test_replacement_attempt_is_not_verified_integrated_or_closed_by_old_run`，425～427 | 旧 attempt 已显式 reclaimed，仍要求旧/新两个目录都在。 | 旧目录已删、A(old)=清理前 H（该场景无新提交时为已知 base）；replacement 目录及其候选内容不变。417～419 的旧 run 恢复前后 ref/reflog 相等、未启动 oracle、原 run 绑定 old、只关 old 线程全部保留。 | S-E、S-G。红态 R-W05：起点旧目录不删且缺隐藏引用。 |
| W06 | `acceptance/test_run_e2e.py`，`test_oracle_failure_is_not_success_and_reclaims_only_owned_thread`，442～450 | oracle 失败并结束回收后，所有 refs 不变且坏候选目录保留。 | 集成分支/reflog、其他 worker 分支和已有引用不变；只允许本 attempt 的 A(N)=预先已知坏 C，以及实际已生成并有持久验收记录的 V(N,K)=C；已确认终结的干净 worker 目录删除，候选对象仍可读。原真实 oracle 非零、run 失败且未 accepted、只关闭自有线程断言不变。若 T-076 将此夹具改为继续修复中的非终结 attempt，则不套用本行，而交主控协调，不把活跃 worker 删掉。 | S-E、S-V、S-G。红态 R-W06：起点终结后仍留目录且无 A(N)；反例为机械失败绝不能集成。 |
| W07 | `acceptance/test_run_e2e.py`，`test_reclaim_guard_targets_history_and_rejects_foreign_and_unknown_attempt`，536～539、565～567 | 首次回收历史 old 不允许任何 ref 变化；结束时 old/current/replacement/foreign 四目录均在。 | 当前 task 状态、集成分支/reflog、current/foreign 的引用不变；只允许为 old 保存 A(old)=预先记录 H。最终 old 与已撤销的手工 current 目录消失，各自隐藏引用保留；replacement/foreign 目录与进程仍在。重放 old 的 `unchanged()` 和跨任务/未知 ID 拒绝断言不动。 | S-E、S-G。红态 R-W07：起点 old/current 目录未清且缺对应引用；不能只改成“某目录消失”而放过误删 foreign。 |
| W08 | `workbench/tests/test_task_cards_e2e.py`，`test_tracer_merges_G_and_C_and_integrates_once`，147～153 | verify 返回后通过尚存的验收目录 HEAD 读 M。 | 完成结果已在库中，验收目录消失；V(N,K)=M，Git 对象与树可读，仍严格核对父提交为 [G,C]、主工作分支未在 verify 阶段变化、集成字节与幂等性。 | S-N、S-V。红态 R-W08：起点目录留下、用途隐藏引用缺失。 |
| W09 | `workbench/tests/test_task_cards_e2e.py`，`test_missing_trailer_reverification_deduplicates_action`，390～400 | integrate 在 G 变化后拒收，再由测试显式 verify/integrate。 | 一次 integrate 自动重验后成功，保存新 verification/G/C/M；`user_inputs` 与已有 inputs 完全相等，`human_intervention` 仍恰好一次，外部 host 字节保留；重放 integrate 不再验收或追加干预。 | S-R。红态 R-W09：起点不自动重验；去掉干预去重的变异体仍应失败。 |
| W10 | `workbench/tests/test_task_cards_e2e.py`，`test_card_validation_versions_and_claim_snapshot`，287～296 | revise 后再从即将被清理的旧 worker 目录读 HEAD，才测试 stale_attempt。 | revise 前保存 C 和旧身份；revise 后断言目录不存在、A(N)=C，再用**同一个预存 C** 做原 stale_attempt 负例。所有卡版本、writer/session、源卡冻结及 v2 oracle_failed 检查不变。 | S-E。红态 R-W10：新清理断言在起点失败；不得因读不存在目录的夹具错误而跳过旧身份负例。 |
| W11 | `workbench/tests/test_cas_race.py`，`test_external_write_between_read_and_cas_is_preserved`，20～35 | 真正 CAS 写入前发生一次外部提交后，reply=false、ref 恒等 external、task 未 accepted。 | 首次 CAS 明确失败时不改写 G1；随后同次 integrate 自动新验收，最终 ref=M，G1 是 M 祖先且 external.txt 原字节保留，C 也为 M 祖先；新 oracle 调用发生在新 M，计数为一次重验。修改屏障驱动使其只阻塞预定第一次 CAS，不因第二次 CAS 无人释放而伪超时。 | S-R、S-G。红态 R-W11：起点不自动重验；去掉 CAS 期望旧值的变异体必须因丢 G1/未在新 M 验收而在业务断言失败。测试模块说明同步改为 R8，不能将最后 ref=G1 继续作新契约。 |

W01/W09/W11 的成功正例只证明 1 次竞争可恢复；另增独立 R8 夹具证明连续第 4 次停止、issue、计数重放与中断边界，不能以修改上述三项替代上限验收。

### 12.3 为保留原场景所需的夹具/检查入口调整

以下项也请求逐条批准，不能借“不是 assert”规避白名单。新增测试本身仍先红后绿。

| 编号 | 文件、起点行号 | 旧前提 | 拟调整及保持的约束 | 依据与红态/反例 |
| --- | --- | --- | --- | --- |
| W12 | `acceptance/test_coop_e2e.py:275～322`，并发认领测试 | alpha 的成功 attempt 保持活跃时，在同仓同路径再测 beta 的 4 路认领，原来无需并行理由。 | alpha 轮完成全部原断言后，经 revoke 正常终结并核对其隐藏引用，再开始 beta；每轮 4 客户端、唯一 winner、持久身份和 duplicate-create 无副作用断言原样。不要给所有 claim 默认补理由。 | S-P、S-E。红态 R-W12：新增跨任务无理由交集拒绝的端到端信号在起点错误放行；alpha 清理在起点失败。测试本身仍是 8 项，不将两个子场景合并掉。 |
| W13 | `acceptance/test_coop_e2e.py:161～162`（仅 helper 签名/显式参数转发），`acceptance/test_run_e2e.py:526,531,546`（历史回收测试的三个调用点） | 历史 old 未回收时另 claim current、并行 dispatch foreign/replacement，都没有路径交集理由。 | helper 仅增加默认空的可选理由；仅这三处明确传非空理由，说明保留多个活跃 attempt 是为了验证历史回收不能误关 current/foreign，核对事件中的理由原文与交集身份；其他 claim/dispatch 不隐式放行。 | S-P。红态 R-W13：独立信号先用无理由 claim 检出起点错误放行，再验证带理由记录，不能把旧 CLI 不认识参数的语法错误当红态。原历史/跨任务身份检查不变。 |
| W14 | `workbench/tests/daemon_acceptance_adapter.py:291～294`，`wait_barrier` | oracle 工作目录必须位于 `<state>/verification/`，与新命名不相容。 | 要求目录精确等于该 fixture 当前持久 verification.workspace，位于批准的项目目录且名称符合 task/attempt/verify 序号；仍核对后台 generation/PID、子进程 ppid、release 所属控制目录、未退出客户端。不得降为“在 /tmp 内就行”。 | S-N、S-G。R-W14 与命名红态共用真实 CLI 信号；夹具反例另造不同项目、不同 attempt 或非当前 verification 目录，必须拒绝。这只是故障目标安全校验迁移，不修改 recovery 的业务断言。 |
| W15 | `workbench/tests/run_daemon_acceptance.py:58～68,275～280` 的旧固定门槛和 CAS claim 名 | T-075 runner 要求三份断言对 `7bcfe7d9` 零 diff，并按旧 CAS 失败 claim 识别变异体。 | **保留该文件不改**，新增 T-077 runner 调用同一后台适配类和获准后的原 8/9/18 方法；记录全部 Git diff 和逐 hunk W 编号。CAS 反事实核对新 W11 的 G1 祖先/文件保留/新 M 完整验收，而不是旧 reply=false。不复用 T-075 的静态身份、日期或 PASS。 | 主控决定 01：“每改一条断言，都要配一个新的红态……用 git diff 逐 hunk 标明它对应白名单的哪一条。”R-W15：带一个白名单外断言改动的冻结副本必须被交付审计拒绝；CAS 变异体因具体业务信号失败。 |
| W16 | `acceptance/test_coop_e2e.py:173～178`，claim helper 的路径/HEAD检查 | 仅要求目录在 `<state>/worktrees` 下，未断言项目目录、任务/序号与具名分支。 | 保留原目录存在、隔离于 repo、base/HEAD 与身份字段检查；增加精确项目目录、`<task>-a<N>`、`symbolic-ref HEAD=refs/heads/a2a/<task>-a<N>`，本夹具的 project 先验等于 task（后台适配器 `cli_argv` 明确传入的参数）。预期 task/序号从夹具先验输入和成功认领次数确定，不从生产路径解析反推。 | S-N。红态 R-W16：起点随机 detached worktree 在路径和分支断言失败，属于业务红态。 |

### 12.4 明确不申请修改的检查

- `acceptance/test_recovery_e2e.py:560～562` 的旧中断验收目录保留，以及 `:708～710` 的中断后撤销/改版现场保留，均保持。结果未知不能因清理表被当成已完成用途；本卡不改整份 recovery 测试。
- `acceptance/test_run_e2e.py:144～152` 的通用 `unchanged()` 全量检查、`:417～419` 的旧 run 不动新 attempt/ref、`:551` 的历史回收重放、错 task/attempt 的拒绝与无副作用检查不变。W04/W06/W07 仅针对明确发生生命周期变化的指定断言，不能扩成通用忽略隐藏引用。
- 任何错误 fence/session/spec、未经修复请求换 C、缺少 submit、原独立分页 oracle 的输入/输出、CAS 第三值未知、操作锁和中断恢复断言不变。T-076 的变更独立按其批准范围处理，本白名单不授权改它的预期。
- `workbench/tests/test_task_cards_e2e.py:327～360` 的非覆盖 dirty 放行/内容保留、覆盖型 dirty 拒绝，以及非 fast-forward 拒绝等既有检查不变；本卡另增 issue 读回和 index/文件字节对照。

### 12.5 红态保存、diff 审核和停止点

批准后，每个 R-W 编号都有独立案例 ID、argv/cwd、冻结起点/候选源码清单、退出码与原始 stdout/stderr；同一场景可承载相关行，但必须逐项保存断言结果。读不存在目录、导入失败、未启动后台、CLI 不识别新参数均不算契约红态。夹具本身变更的红态与产品业务红态分开标注。

优先在 `workbench/tests/` 增加 focused contract cases 取得红态，再按获准白名单改旧方法，使既有 8/9/18 可在新契约下复跑；不修改已保存的起点或旧报告来换取全绿。新 S3 runner 必须保持 8/9/18 的完整用例数、不跳过、不 monkeypatch 业务断言。

后续 `assertion-hunks.md` 将逐个列出 `git diff --unified=3 <起点> -- <文件>` 的 hunk 头、所属 W 编号和对应红/绿工件；除批准的 W01～W16 外出现新受影响断言时，另提交白名单修订，不自行扩大。

当前停止点：只提交这份白名单与决定原文留档，尚未改任何源码/断言、未启动后台或真实 Codex。按主控决定 01 原文“写完白名单后回复 `T-077 WHITELIST READY` 并停下”，等待主控批准。

## 13. 首批红态准备（主控 #22 之后）

状态：**INCOMPLETE**。[主控决定 02](controller-decision-02.md) 已批准 W01～W16，并原文复制留档。新增 `workbench/tests/test_worktree_lifecycle_e2e.py`，13 个显式案例覆盖首批命名、清理、路径交集、issue 与一次 R8；没有改产品源码或旧断言。检查计划和逐案预期见 [HANDOFF-red-01.md](HANDOFF-red-01.md)。

`outside-sandbox.sh red-01` 已备好，等待主控在沙箱外运行。当前只通过 AST、Shell 语法和文档/差异检查，业务红态尚未取得，真实 Codex 用量 0/4。得到对应红态后再实现首批行为；其他场景继续各自先红后绿。

## 14. 首批实现待验收（主控 #28 之后）

状态：**INCOMPLETE**。主控 #28 已确认 red-01；本 worker 独立读回了同一份原始收据，13 项均为业务红态、0 errors。已实现首批生命周期、路径交集与 issue 上报，并按获准白名单修改相应断言；逐 hunk 对照见 [assertion-hunks.md](assertion-hunks.md)。

候选尚未跑绿态。`outside-sandbox.sh check-01` 先验证 12 项生命周期，再对起点原始产品快照补 R8 第 4 次失配红态，说明见 [HANDOFF-check-01.md](HANDOFF-check-01.md)。R8 和冲突回写仍未实现；未运行完整 8/9/18、真实 Codex 场景或最终审查。真实用量 0/4，等待主控在沙箱外运行；本轮没有提交或合并。

## 15. R8 候选待验收（主控 #31 之后）

状态：**INCOMPLETE**。green-01 的 12 项全绿、red-02 的上限红态均已独立读回。已实现锁内共用验收、R8 持久计数与第 4 次停止、明确 CAS 失败和未知 intent 的分流，并迁移 W01。原生身份等已提交接口已从 main 的 `42e2b8ed` 读取，但尚未变基合入。

`outside-sandbox.sh check-02` 已准备，见 [HANDOFF-check-02.md](HANDOFF-check-02.md)：先跑 2 项 R8 候选绿态，再补 5 项起点红态，为剩余白名单迁移准备独立证据。当前尚未执行此批，后续工作与真实预算保持原范围，真实用量 0/4。

## 16. 白名单迁移与完整回归准备（主控 #38 之后）

状态：**INCOMPLETE**。green-02、red-03 已核对；剩余 W05/W07/W09/W11 与 W13 指定调用点已按红态迁移。W15 的独立范围核对和新回归入口已准备，原恢复断言与通用无副作用检查保持。

`outside-sandbox.sh check-03` 先跑剩余 4 个定点绿态，再跑完整交付 8、恢复 9、编排 18、CAS 补充 1、任务卡 15。具体边界见 [HANDOFF-check-03.md](HANDOFF-check-03.md)。当前仅完成离线检查，尚未执行新回归；不改产品代码，不增加真实回合，等待执行主控在沙箱外运行。

## 17. CAS 夹具修复待复验（主控 #40 之后）

状态：**INCOMPLETE**。green-03 三项通过，CAS case 失败，后续回归未执行。已定位为第二个 Git wrapper 被 release-all 的清理语义 abort；第一次 prepare 失配及随后重验均有原始证据。只修两个测试驱动的放行方式，19 个产品源码与业务断言不变；完整诊断及来源绑定见 `check-03-diagnosis.json`。

`outside-sandbox.sh check-04` 重新跑修正夹具的 W11 起点红态、候选绿态，再继续 8/9/18 与补充回归，均用新输出名。见 [HANDOFF-check-04.md](HANDOFF-check-04.md)。本轮无产品修复、无安全边界放宽，真实用量保持 0/4，等待执行主控运行。

## 18. cards 收证据修复（主控 #43 之后）

状态：**INCOMPLETE**。red-04 / green-04 及 regression-02 的 8/9/18/CAS 完整收据已核对。cards 15 项测试通过，但 runner 误读不存在的 artifact.state，未写最终收据。只按已确认的 cards `root/state` 布局修正派生记录，不改产品/断言，不补写旧 run.json。`outside-sandbox.sh cards-03` 仅重跑 cards 到新目录，见 [HANDOFF-cards-03.md](HANDOFF-cards-03.md)。真实用量 0/4。

## 19. 冲突流程红态准备（主控 #44 之后）

状态：**INCOMPLETE**。cards-03 完整收据 PASS，15/0/0/0、收证据错误为空；加上 regression-02 的 8/9/18/CAS，冲突实现前的候选回归齐全。本轮仅新增七个冲突场景与受控原生会话边界，没有修改冲突产品代码或旧断言。

`outside-sandbox.sh conflict-red-01` 在冻结起点上运行活会话回写/重交、已结束会话新 attempt、未知会话与未知投递、非内容 Git 错误、重交后路径及尾注反例。最后两项的起点失败首先发生在重交入口，后续拒绝断言尚不能算取得反事实证据。具体预期、产物、复现命令与限制见 [HANDOFF-conflict-red-01.md](HANDOFF-conflict-red-01.md)。等待执行主控在沙箱外运行；真实用量保持 0/4，真实启动准确 argv/home/hook 另交逐次批准。

## 20. 冲突候选待绿态（主控 #47 之后）

状态：**INCOMPLETE**。已读回 conflict-red-01：7 项业务红态，失败数依次 3/1/1/1/1/1/1、0 errors、`red_confirmed=true`。现实现冲突证据保存、原 worker 回写、确认结束后的新 attempt，以及新 C 的独立基线检查。把原 claim/dispatch 代码提取为唯一认领实现，新 attempt 继续检查当前路径占用；没有第二套创建通道。

额外在 Panes 实现前取得四项受控边界红态：归档释放名额、按工作目录绑定 rollout、区分确认结束与进程替换、gate 消息入原队列。这四项候选已通过，不调用真实 ps、socket、PTY 或模型，限制和命令见 [PANES-BOUNDARY.md](PANES-BOUNDARY.md)。CLI 七项绿态仍未运行，`outside-sandbox.sh conflict-green-01` 交主控运行。真实用量仍 0/4；独立审查、与 T-076-1 合流及变基后的完成条件和回归均待后续。详见 [HANDOFF-conflict-green-01.md](HANDOFF-conflict-green-01.md)。

两份旧窗格探针的合成 `session_meta` 缺少 cwd，本轮按任务卡的夹具错误修复条款只补该字段，不改其断言。范围审计只允许两处精确元数据替换，并用反转原断言的反例检查没有放宽范围；本次沙箱外脚本将复验这两个直接受影响的探针。

## 21. 变基后统一复验（主控 #51、#53、#54）

状态：**INCOMPLETE**。变基前 conflict-green-01 的 7 项 CLI 场景和两份旧探针已通过。主控在沙箱外发起并继续变基；两处源码冲突按双方意图处理，记录见 `rebase-resolution-01/RESOLUTION.md`。当前候选 `446f25c3de00925dfcc2f1c3f1375713676e166b` 基于 main `457e02a8`，完整保留 T-076-1 的稳定身份与停机行为，T-076-2 尚未合入。

`outside-sandbox.sh rebase-01` 固定上述候选，合并运行全部 S3 25 项（含冲突 7 项）、8/9/18、CAS、cards，以及合流直接影响的窗格、身份和停机检查；不修改产品或旧断言，不重复冲突子集。各阶段前后核对同一源码，失败即停。详见 [HANDOFF-rebase-01.md](HANDOFF-rebase-01.md)。真实用量 0/4，真实冲突和同一 home 的历史记录隔离验证、独立审查及最终交付仍未完成。

## 22. shutdown 合成元数据修正（主控 #58）

状态：**INCOMPLETE**。rebase-01 除 shutdown 的首次原生身份绑定用例出现 1 error 外，其余各组均通过。T-076-1 的真实 0.162.1 启动记录、native 轨迹首行与原始事件共同证明 session_meta.cwd 存在，并与 `-C`、launch.worktree 完全相等；失败的 shutdown 合成记录缺此字段。仅让 PTY stub 从实际 spawn options 传入 cwd，原断言与产品身份条件不变。

`outside-sandbox.sh rebase-fix-02` 只重跑 shutdown、identity、Panes，各 4 项，新输出为 `outside-rebase-fix-02/`，保留旧失败。证据提取、根因和准确命令见 [HANDOFF-rebase-fix-02.md](HANDOFF-rebase-fix-02.md)。真实用量仍 0/4，待执行主控运行。

## 23. 真实场景逐次启动材料（主控 #61）

状态：**INCOMPLETE**。rebase-fix-02 的 shutdown、identity、Panes 均通过。修正和回归证据已提交为 `93094e7be82c21448c460436c360ffb0f75a3412`，尾注齐全，产品代码没有新增变化。

按主控 #51/#61，把第 9 节原拟的同会话冲突场景改为一个两 attempt 的真实场景，同时覆盖历史根日志隔离：第一会话交付/回执后确认空闲，再结束其已核对的原生领导者；第二次获批后由原门禁的冲突处理创建新 attempt，在同一隔离 home 中运行。旧 rollout 保持原路径、原字节；新会话启动前后都不能把旧 UUID 绑定为新身份。两次各 2 个主 turn，共 4 个，不增加真实探针。

**Reality gate（仅准备边界）**：observed—真实 0.162.1 的 cwd 与 -C 一致、B 通道每次交付有一个回执回合；measured—生产 Panes 的两组完整 argv 与审批计划一致，未批准第二次/第三次无法到达 PTY spawn，4 项离线检查通过；独立 oracle 的已知好坏函数检查 4 项通过。unknown—真实 worker 能否在预算内完成两次交付与冲突整理、复用 home 时的实际身份归属。上述未知由同一个真实场景检验，失败即停；离线检查不替真实结论。

为提前给出完整 argv，测试 host 仅预分配两个公开 launch UUID，保留独立随机 token 与真实 attempt/session/native 身份；这一测试输入控制方式也交主控审核。真实执行仍使用生产 serve/Panes/Gates、真实 PTY 和原生 CLI，未改产品身份条件。完整命令、隔离 home、hook、停止和清理条件见 [REAL-APPROVAL-01.md](REAL-APPROVAL-01.md)，机器可读计划为 `real-plan-01.json`。`real-01` 和 `real-02` 各须本次批准引用，第一阶段在第二次审批前停止，不自动连跑。当前真实用量 **0/4**。

## 24. 真实失败后的 relay 作用域修复（主控 #66）

状态：**INCOMPLETE**。两次真实运行已用 **4/4**，第二个 worker 已提交 C2 并写请求，但 relay 把新 attempt 的 `delivery` 与旧 launch 的请求当作同一个 state 全局键，拒收发生在 submit 门禁之前。隔离 home 已由主控删除，旧运行保持失败原状；不追加真实回合。已复制本次主控批准 03 留档。

只读归档核对表明两个 launch 各自观察到不同的原生 UUID 与匹配工作目录，旧 rollout 字节完全保留。持久化 a2 native 为 null 符合 relay 未调用 submit 补绑定的路径。没有找到跨 attempt 唯一 request_id 的规范要求；结合每 attempt 独立请求目录、身份幂等契约及 #66 明确验收场景，修复作用域为 launch。

修复前先取得两个定点业务红态；随后只改 relay 按既有 launch/request_id 字段查 intent、新 key 包含 launch，保留旧 key 的结果与 pending intent。5 项定点绿态、原 relay/CLI 检查和 3 个变异体均已完成。下一条 **Tracer bullet** 复验经真实 CLI→后台→Panes/relay→门禁→Git，PTY/进程边界受控：旧会话结束后的冲突创建新 attempt，使用同一请求编号交付、重验并集成。沙箱外脚本 `relay-check-01` 先跑仅还原 relay 的反事实，再跑候选，0 个真实模型回合。详细诊断、证据层级、命令与限制见 [HANDOFF-relay-check-01.md](HANDOFF-relay-check-01.md)。等待执行主控运行。

## 25. relay 夹具字段修正（主控 #72）

状态：**INCOMPLETE**。relay-check-01 在 preimage 阶段误读 status 顶层 launch，1 error、0 failures，尚未取得后台业务红态。现改读原始返回中已有的 `task.current_attempt.runtime_identity.launch`；整例静态核对还修正三个 pane 命令误带 `--task` 的 helper 用法。产品源码与原业务断言不变，失败原文保留。

preimage/候选的完整字段清单、生产位置和归档实值核对见 `relay-field-audit-01/audit.json`，静态核对 PASS，不代表后台运行通过。`outside-sandbox.sh relay-check-02` 改用新输出目录，先重跑 preimage，再跑候选；详细说明见 [HANDOFF-relay-check-02.md](HANDOFF-relay-check-02.md)。真实回合仍为 4/4，本轮不启动真实 Codex，等待执行主控运行。

## 26. relay 修复提交后的统一回归（主控 #73）

状态：**INCOMPLETE**。relay-check-02 的 preimage 业务红态确认，候选完整闭环 PASS。修复、测试与相关证据已提交为 `da44c6733f5046f7c645028352859a80070f15b9`，尾注齐全。

`outside-sandbox.sh relay-regression-01` 固定本提交，一次执行 S3 全部 25 项（含冲突 7 项）、8/9/18、CAS、cards、完成条件中的窗格/原生记录/身份/停机检查，以及 relay 交付闭环、scope/core/cli 和全库去重变异体。每组只跑一次，失败即停，产物改用新前缀。准备范围审计 PASS，行为回归待主控运行，详见 [HANDOFF-relay-regression-01.md](HANDOFF-relay-regression-01.md)。真实预算保持 4/4；用户答复前不准备新的真实运行，独立审查留到真实场景之后。本轮 READY 后停止等待。
