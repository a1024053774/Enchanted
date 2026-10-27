# T-193 独立只读审查（第 3 轮）

## STATUS

**NO_GO**。R1 仍会在内部复用时重新解析并改变获批目录；另复现 Claude worker 在启动构造的异步间隔内放过已改变目标的路径。两项均属于本次本地桌面工作台的配置正确性问题。

审查对象：`/private/tmp/t193-dev2`，基线 `33debf82a195ee4c0f421bdc924f56578eb1c89f` 加冻结工作区改动。保存的 [reviewed-candidate.diff](reviewed-candidate.diff) 为 74,185 字节，与候选 `T-193.diff` 及结束时实时 diff 逐字节相同；工作区状态未变，`git diff --check HEAD` 退出 0。见 [candidate-verification.json](candidate-verification.json)。未修改候选或原仓库，未提交；本轮产物仅在 `/private/tmp/t193-review4`。

判据来自 T-193、T-189 第 1 条、T-196 第 3 条及本轮 brief：主控可操作多个已打开项目；每个任务仍只绑定一个仓库；额外目录由每次派发明确指定并记录；内部恢复、冲突替换和随后启动须保持原获批路径，或明确拒绝。按 **Ubiquitous language** 区分项目设置、派发输入的别名、获批真实路径、启动参数。本轮 **Tracer bullet** 使用真实门禁、Git、SQLite 和生产启动构造；没有修复代码或引入 **Deep modules**。

| 上轮发现 | 本轮结论 |
| --- | --- |
| R1：恢复/冲突替换的预检与重新解析分离 | **NO_GO，未从根因修好**。旧异步间隔反例已被拒绝，但 `approved=true` 仍无条件再次解析，见 F1。 |
| R2：run 获批目录持久化过晚 | **PASS，原缺陷关闭**。目录与 `run_bound` 一起保存，位于 runtime 启动之前；独立进程崩溃、数据库重开及别名替换后，仍派发原获批目录。该结论不覆盖 F1 对新绑定的再次污染。 |
| R3：`project-extra-dirs` 变异定位失效 | **PASS，定位缺陷关闭**。本轮独立核对定位唯一；所附新变异结果实际进入业务断言并因默认继承项目目录而失败。未在本轮重跑完整变异 e2e。 |

## FINDINGS

### F1 · P1：`approved=true` 仍再次解析目录，恢复和冲突替换可以一起改写授权记录与启动参数

位置：[workbench/src/gates/core.ts:2162](/private/tmp/t193-dev2/workbench/src/gates/core.ts:2162)。首次核对位于 [2159 行](/private/tmp/t193-dev2/workbench/src/gates/core.ts:2159)，内部调用分别来自 [1739 行](/private/tmp/t193-dev2/workbench/src/gates/core.ts:1739) 的冲突替换和 [4049 行](/private/tmp/t193-dev2/workbench/src/gates/core.ts:4049) 的 run 重派。

`approved` 分支先要求 `realpathSync(path) === path`，随后却与首次用户输入共用无条件的 `.map(path => realpathSync(path))`。目录若在这两次文件系统查询之间被换成链接，第二次解析就把新目标作为返回值。同步调用之间没有 JavaScript 的 `await`，但不阻止其他进程改变文件系统。因此修复缩短了窗口，没有建立“内部复用不得改变获批列表”的不变量。

独立反例在初次派发前建立 `initial` 和 `unrelated` 两个目录，最初只批准 `initial`。恢复/替换时，探针调用真实 `realpathSync()`，在其已返回 `initial` 后将该目录改成指向 `unrelated` 的链接，然后将真实返回值原样交回生产检查；不改写查询结果、门禁结果或候选文件。

实际观察：

- **run 恢复**：第二个 attempt、持久化 run 的 `dispatch.extra_directories`、生产 `--add-dir` 和 `sandbox_workspace_write.writable_roots` 全部变成 `unrelated-data`。见 [结果](launch-recovery-5TRQ0e/results.json)、[日志](resume-sync-race.log)。
- **Git 合并冲突自动替换**：经 `dispatch → submit → verify` 产生真实冲突，原 worker 已停止；替换 attempt 的启动记录、`--add-dir` 和 writable roots 全部变成 `unrelated`。见 [结果](lifecycle-Kwgygh/conflict-sync-race.json)、[日志](conflict-sync-race.log)。

两次均违反事先确定的判据“保留原获批目录或拒绝，不得产生新授权目标”，退出 1 是业务断言失败。后续 `Panes` 检查无法拦截：它收到的已经是 `unrelated` 的规范路径，新记录与新 argv 仍自洽。

最小修正方向：内部复用分支在验证原获批路径仍为自身、仍是目录且满足硬保护后，返回原获批路径列表；只有首次用户输入做规范化，不再用后一次解析的结果替换已获批对象。保留这两个入口的反例，并核对 attempt、run 和启动配置。

这也直接否定 `core.ts:1564–1565` 的 “kept as they are, never resolved again” 注释及 brief 中“不再重新解析”的说明。不能仅凭新增 `approved` 参数认为 R1 已关闭。

### F2 · P1：Claude worker 在目录检查之后等待 Git，启动记录生成前未再次拒绝已改变目标的路径

位置：[workbench/src/panes.ts:850](/private/tmp/t193-dev2/workbench/src/panes.ts:850)。目录检查位于 [836 行](/private/tmp/t193-dev2/workbench/src/panes.ts:836)，启动记录交给 store 位于 [903 行](/private/tmp/t193-dev2/workbench/src/panes.ts:903)。

Claude worker 在目录通过检查后，还要 `await workerGitDenied(launchWorkspace)` 执行真实 Git 查询，然后构造 Claude argv，再写启动记录、创建 PTY。这个异步间隔之后没有目录复核。即使 F1 修复，首次正常派发也能到达该路径。

独立探针通过真实门禁首次派发，仅给 `initial`。在生产 `workerGitDenied()` 的真实 Git 查询完成、解析 Git common dir 时，探针只把 `initial` 换成指向 `unrelated` 的链接，保留 Git 和文件系统查询的真实返回值。生产启动构造继续到达 `store.launch` 边界：

- attempt 的获批列表仍是 `[initial]`；
- 启动记录、`--add-dir`、Claude shell 沙箱 `allowWrite` 都包含 `[initial]`；
- 同一时刻该路径实际解析为 `unrelated`；没有 `extra_directory_changed` 拒绝。

见 [结果](lifecycle-fniurs/launch-claude-window.json)、[日志](launch-claude-window.log)。本轮在 PTY 创建前截获记录，没有运行原生 CLI 写文件，因此结论限定为：**启动配置在进入持久化/启动边界时已经包含改变了目标的目录，现有检查未履行启动前拒绝条件**。不把它扩大为已证明原生沙箱最终向该目标写入。

同一探针关闭路径变化时，生产启动记录正常构造，额外目录及其真实目标均为原 `initial`，见 [正常对照](lifecycle-6ZEmBk/launch-claude-control.json)。因此这不是“总是拒绝”或夹具启动失败造成的差异。

最小修正方向：把启动前的目录校验放到异步配置准备完成之后、记录和 PTY 启动之前；保持原列表，变化时拒绝，不能重新解析并接受新目标。该修正关闭本次确定的异步空档，不应据此承诺路径在原生子进程运行期间永远不变。

## EVIDENCE

### 本轮独立执行

命令从 `/private/tmp/t193-review4` 执行。脚本会创建新的隔离夹具；没有改候选代码。主要运行的 argv、退出码与日志位置保存在 [checks-run.json](checks-run.json)，三项失败反例的独立判定在 [counterexamples.json](counterexamples.json)。

| 检查与命令 | 结果 |
| --- | --- |
| `node probe.ts` | 退出 0，完成 25 个记录项。覆盖输入检查、任务隔离、明确派发目录、reviewer 对消失/文件/链接的拒绝、review gate 对目录列表不符的拒绝、monitor 无额外目录。[结果](probe-bILWY7/results.json)。其中单独 `resumeArgv` 和另一 linked checkout 两项仅为观察，不计额外验收通过。 |
| `node recovery_launch.ts <场景>`，场景为 `alias-retarget`、`canonical-relink`、`missing`、`file`、`recreate`、`resume-race` | 六项 **PASS**，均退出 0。原别名换目标仍使用获批真实路径；真实路径换链接、删除或变文件明确拒绝；同路径重建普通目录允许；上一轮在 `checkClaimPaths` 之后换链接的异步反例已拒绝。见 [别名](launch-recovery-qoC6Qj/results.json)、[换链接](launch-recovery-if9cw7/results.json)、[删除](launch-recovery-8UM7P6/results.json)、[文件](launch-recovery-KFJPVG/results.json)、[重建](launch-recovery-8gCy6k/results.json)、[原异步反例](launch-recovery-ODCX1Q/results.json)。 |
| `node lifecycle_probe.ts <场景>`，场景为 `conflict-control`、`conflict-relink`、`conflict-missing`、`conflict-recreate`、`conflict-race` | 五项 **PASS**，均退出 0。真实 Git 冲突下正常替换和同路径重建保持原目录，链接/缺失及原异步反例拒绝。见 [正常](lifecycle-LvHOK9/conflict-control.json)、[换链接](lifecycle-DbMye6/conflict-relink.json)、[删除](lifecycle-uJ3Gsp/conflict-missing.json)、[重建](lifecycle-D0eXim/conflict-recreate.json)、[原异步反例](lifecycle-zpi7rx/conflict-race.json)。 |
| `node lifecycle_probe.ts crash-write /private/tmp/t193-review4/crash-xgj9frxf`，随后 `node lifecycle_probe.ts crash-resume /private/tmp/t193-review4/crash-xgj9frxf` | 首进程在生产 `startThread` 边界按设计退出 **77**；第二进程退出 **0，PASS**。退出前 attempt 与落盘 run 都已为 `[initial]`；后台停止期间只把原别名改成普通目录，恢复后的生产记录和 argv 仍为 `[initial]`。[退出前](crash-xgj9frxf/crash-before-normalize.json)、[恢复后](crash-xgj9frxf/crash-resume.json)。重放时先换一个新的空夹具目录。 |
| `node recovery_launch.ts resume-sync-race`；`node lifecycle_probe.ts conflict-sync-race` | 两项退出 **1**，业务断言捕获 F1；原获批目录已变成新目标，无关准备异常不存在。 |
| `node launch_window.ts`；`node launch_window.ts control` | 路径变化场景退出 **1**，业务断言捕获 F2；正常对照退出 **0，PASS**。 |
| `node /private/tmp/t193-dev2/workbench/tests/test_t141_launch_contract.mjs /private/tmp/t193-review4/t141-launch-contract.json /private/tmp/t193-dev2` | 退出 0，**PASS，2 项**。[摘要](t141-launch-contract.json)。仅启动契约，不代替原生沙箱检查。 |
| 从当前测试 AST 读取 `MUTANTS`，逐个检查当前源码中的匹配数量 | 三个定位均唯一；`project-extra-dirs` 能生成预期坏实现。[结果](mutation-locators.json)。未启动后台。 |
| project-map `status`、候选 diff 与状态核对 | 原仓库地图开始与结束均 Problems 0、Stale living docs 0；[结束输出](project-map-status.txt)。候选精简副本没有 `.project-map`，首次对副本执行 status 得到缺文件错误，随后改用 brief 指定的原仓库票据与地图；没有在副本初始化地图。候选完整性见 [核对结果](candidate-verification.json)。 |

探针复用上一轮脚本，只在本轮副本调整输出目录与契约断言，并增加本轮时序场景。原失败证据、候选和上一轮目录均未覆盖。遵循 evidence-first-testing 的独立 oracle 要求：期望在路径变化前确定，不从新 attempt 或新 argv 回推答案。三个反例 JSON 的 `status=INCOMPLETE` 是继承探针的统一异常处理；原始状态原样保留。这里依据记录中的明确业务断言失败和生产观测判为 **NO_GO**，不是将其改称通过，也不是忽略环境错误。

### 所附真实入口与回归证据

来源：[原仓库 T-193 证据目录](/Users/luckye/Documents/Code/a2a/evidence/2026-10-27-batch28/T-193)。以下仅为本轮读取、核对，未冒充本轮重跑。

- [green-04-claim-approved.json](/Users/luckye/Documents/Code/a2a/evidence/2026-10-27-batch28/T-193/green-04-claim-approved.json)：7 项 PASS，覆盖跨已打开项目建卡和派发、侧栏归属、未指定额外目录不给、未打开项目拒绝及说明、明确目录进入启动记录/参数、reviewer 拒绝被换链接的目录。测试走真实后台、socket、终端身份和交互 CLI，模型接口为脚本化夹具；不证明模型理解能力。
- [mutant-project-extra-dirs-02.json](/Users/luckye/Documents/Code/a2a/evidence/2026-10-27-batch28/T-193/mutant-project-extra-dirs-02.json)：虽然摘要状态为 INCOMPLETE，但跨项目派发已完成，worker 实际拿到 `settings-extra`，明确失败于 `no_extra_directory_unless_named`；这次确为业务反事实，不再是定位准备失败。当前测试第 34 行定位与候选源码唯一匹配，R3 的具体缺陷关闭。
- [review2-fix-probes/summary.json](/Users/luckye/Documents/Code/a2a/evidence/2026-10-27-batch28/T-193/review2-fix-probes/summary.json)：观察字段与本轮复跑相符。旧 `resume-race`、`conflict-race` 现在拒绝；崩溃恢复保持 `initial`；`file` 的拒绝码已改为 `extra_directory_changed`。这些旧断言的失败不是新产品缺陷；但它们不覆盖本轮 F1 的两次同步查询之间或 F2 的启动间隔。
- [T-123 回归](/Users/luckye/Documents/Code/a2a/evidence/2026-10-27-batch28/T-193/regression-t123_project_identity.json)、[T-140 回归](/Users/luckye/Documents/Code/a2a/evidence/2026-10-27-batch28/T-193/regression-t140_extra_dirs.json)、[T-141 回归](/Users/luckye/Documents/Code/a2a/evidence/2026-10-27-batch28/T-193/regression-t141_loosened_limits.json)：分别报告 22、22、24 项 PASS。它们为已有回归证据，当前候选比上轮仅改变 `core.ts`、契约注释和变异定位；没有本轮重新运行这三个完整 e2e 的记录。monitor 的无额外目录启动参数检查不等于原生拒写证明。

### 说明、反事实与后续验收条件

产品页、角色卡、help 与 README 对“项目设置不自动授权 worker、逐次指定、reviewer 沿用 worker 的列表、monitor 无额外目录、额外目录改动不进审查与集成”的主要说明与源码一致；GUI 未重开。`A2ARun.dispatch` 注释与当前 `run_bound` 持久化时机一致。R1 的“不再解析”注释则与代码、实际观察不一致，已列 F1。README 第 8 行“改卡冲突后重派……沿用”应明确限定自动合并冲突替换；普通 `revise` 后重新 `dispatch` 没有内部 approved 列表，仍需本次显式指定，不能读成改卡重派自动继承。

**COUNTEREXAMPLE：**本轮候选自己就是 F1/F2 的已知坏实现：两个目录在输入中事先独立确定，路径变化场景使契约断言失败；不注入变化的恢复、冲突和 Claude 启动对照通过。现有 green e2e 及旧异步探针全部通过，仍未拒绝本轮反例，不能作为放行的充分条件。

**RULE：**这是重复出现的“预检后重新解析或继续启动，授权对象漂移”。应在恢复、冲突替换、Claude 启动三个入口保留机械检查：变化前确定获批列表；在生产文件系统/异步边界改变路径；断言保持原列表或启动前拒绝，同时核对 attempt、落盘 run、启动记录与 argv。已有 e2e 没有覆盖这些注入点；应把本轮反例并入 T-193 的真实门禁及启动构造回归，而不是只补一条文字规则。

## LIMITATIONS

- brief 允许不重跑完整 e2e；本轮没有重跑完整 Electron、真实模型 CLI、原生文件沙箱或三个完整回归。所附摘要的 `revision=null`，没有完整冻结 diff，因此不能仅凭摘要证明逐字节对应当前候选。
- 本轮使用真实文件系统、Git、SQLite、生产门禁和启动构造，CLI 生命周期与运行时身份由探针提供，启动记录在 `store.launch` 边界截获，未创建 PTY。所谓“生产启动记录”指生产代码构造并传到该边界的记录，不声称它已由真实 CLI 执行或已经造成范围外写入。配置正确性反例已成立，原生最终效果仍未测。
- F1 是两次同步文件系统查询之间的确定性时序注入，F2 是真实异步 Git 查询边界注入。探针保持底层查询返回值，只改变隔离夹具；它们证明存在该交错顺序，不估算日常发生概率，不声称已在未插桩后台中随机撞中该竞态。
- 目录在同一规范路径重建后允许继续，符合当前路径契约；本轮没有扩展成 inode 绑定。也不评价原生 CLI 启动后的任意嵌套链接和运行期路径变化。
- `Panes.restore()` 不直接恢复有 attempt 的 worker/reviewer，要求回收重派；单独 `resumeArgv()` 观察不是另一条可达恢复缺陷。
- 审查范围是本地桌面工作台的配置正确性，不是完整系统安全评估或模型能力验收。**F1、F2 修复并由相同入口反例证明关闭前，保持 NO_GO。**本轮不实施修复。
