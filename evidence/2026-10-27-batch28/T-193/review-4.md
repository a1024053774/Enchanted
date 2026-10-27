# T-193 独立只读审查（第 4 轮）

## STATUS

**PASS（本轮本地桌面工作台配置正确性审查）**。第 3 轮 F1、F2 已从所指出的根因修复，相同路径变化反例和正常对照均通过。本轮没有发现新的阻断性授权对象漂移路径。README 仍有一处非阻断说明歧义，见 D1；本结论不代表完整系统安全或模型能力验收。

**TARGET：**`/private/tmp/t193-dev2`，基线 `33debf82a195ee4c0f421bdc924f56578eb1c89f` 加冻结工作区改动。保存的 [reviewed-candidate.diff](reviewed-candidate.diff) 为 74,541 字节，审查开始、结束的实时 diff 与候选 `T-193.diff` 逐字节相同；HEAD、工作区状态未变，`git diff --check HEAD` 退出 0。见 [candidate-verification.json](candidate-verification.json)。未修改候选或原仓库，未提交；产物只写本轮目录。

判据独立取自 [T-193](/Users/luckye/Documents/Code/a2a/.project-map/tickets/T-193-controller-multi-project.md)、T-189 第 1 条、T-196 第 3 条和本轮 brief：主控可操作多个已打开项目；每任务仍只绑定一个仓库；额外目录逐次指定；恢复、冲突自动替换和启动不得把获批路径重新解释为新授权目标，变化时保留原列表或拒绝。按 **Ubiquitous language** 区分项目设置、派发别名、获批真实路径和启动配置。**Tracer bullet** 穿过真实门禁、Git、SQLite 与生产启动构造；本轮只审查，没有新增 **Deep modules** 或其他产品实现。

## FINDINGS

### F1 复核：PASS，内部复用不再产生新的获批目标

[core.ts:2163](/private/tmp/t193-dev2/workbench/src/gates/core.ts:2163) 现在明确分支：首次派发输入才做真实路径规范化；`approved=true` 在核对后从原列表去重并返回，不使用后一次 `realpathSync()` 的结果替换授权对象。原列表仍需存在、为目录、解析为自身，并满足仓库及数据目录的硬保护。

两个内部入口均使用这一分支：run 恢复经 [core.ts:4050](/private/tmp/t193-dev2/workbench/src/gates/core.ts:4050) 传入已落盘的获批列表；合并冲突自动替换经 [core.ts:1740](/private/tmp/t193-dev2/workbench/src/gates/core.ts:1740) 传入原 attempt 的列表。run 在 `run_bound` 时、启动之前保存该列表的修复仍保留。

本轮原样复跑第 3 轮同步交错：真实查询先返回原路径，探针随后把该路径换成指向无关目录的链接，再将查询原返回值交回生产代码。结果如下：

- [恢复结果](launch-recovery-DieYi0/results.json)：新旧 attempt 及 run 的获批目录均仍是 `initial-data`；恢复报 `extra_directory_changed`，没有第二条启动记录。
- [冲突替换结果](lifecycle-HaZR9W/conflict-sync-race.json)：真实 `dispatch → submit → verify` 产生 Git 冲突；替换 attempt 仍记录 `initial`，`conflict_rework_unknown` 保存 `extra_directory_changed`，没有替换 worker 的启动记录。
- 额外通过生产使用的 Node SQLite 以只读方式回读两组数据库，断言各自两个 attempt 都只保存原目录，见 [persisted-approval-readback.json](persisted-approval-readback.json)。这一步避免只看启动数量就漏掉授权记录已经被污染的情况。

因此这次修复建立了“内部复用不得改写获批列表”的不变量，而不只是缩短两次查询之间的窗口。`claim` 注释中的“不再解析”应理解为“不再用解析结果重写列表”；检查仍会调用 `realpathSync()`，与代码中的注释上下文一致。

### F2 复核：PASS，启动检查已位于全部异步准备之后

[panes.ts:902](/private/tmp/t193-dev2/workbench/src/panes.ts:902) 的校验位于 CLI 版本查询、Claude `workerGitDenied()`、argv 及记录构造之后，紧接 `store.launch(record)`。到 PTY 创建之间没有新的 `await`。各 CLI 的 worker/reviewer 共用这个位置；monitor 直接使用空额外目录列表。

复跑第 3 轮 Claude 空档反例：在真实异步 Git 查询完成的 `workerGitDenied()` 边界，把已批准的 `initial` 换成指向 `unrelated` 的链接，不伪造查询结果。

- [变化场景](lifecycle-RNcMXN/launch-claude-window.json)：派发明确返回 `ok=false, error=extra_directory_changed`；attempt 仍记录原目录；到达 `store.launch` 的记录数为 **0**。
- [正常对照](lifecycle-hJoOse/launch-claude-control.json)：派发成功，启动记录、`--add-dir`、Claude `allowWrite` 与该时刻的真实目录均为原获批目标。

所附 `review3-fix-probes/summary.json` 中变化场景的 `INCOMPLETE` 来自旧探针提前断言“派发成功”。本轮只将该断言改为事先确定的契约“变化场景必须拒绝、正常场景成功”，保留同一注入点及零启动记录断言；未修改产品或把原失败证据改写为通过。

### D1 · P3，非阻断：README 没有清楚区分自动冲突替换与普通改卡重派

位置：[workbench/README.md:8](/private/tmp/t193-dev2/workbench/README.md:8)：“改卡冲突后重派的 attempt 沿用原 attempt 的目录。”这句话容易被理解为普通改卡重派也自动继承目录。实际只有内部 run 恢复与合并冲突自动替换传入 `approved`；普通新 `dispatch` 未指定时仍得到空列表。

本轮经真实门禁执行 `dispatch（给目录）→ revise → reclaim（旧 attempt）→ dispatch（不给目录）`，结果新 attempt 的列表为 `[]`，见 [revise 结果](revise-faOmpt/results.json)。产品行为符合逐次授权；歧义可能让主控漏传目录，导致预期的额外目录不可写，不会额外授予新目录。

建议 T-193 说明维护者在关闭 ticket 前改为：“run 恢复和合并冲突自动替换沿用原获批目录；普通改卡后的新 dispatch 仍须显式指定。”复核条件是上述两种流程及这句说明一致。本轮只记录，不改候选。

## EVIDENCE

### 本轮独立执行

运行环境：Node `v26.5.0`。从 `/private/tmp/t193-review5` 执行，脚本每次创建新的隔离夹具。主要命令、退出码及日志在 [checks-run.json](checks-run.json)，结果索引在 [checks-summary.json](checks-summary.json)。19 次主检查均为预期退出：18 次退出 0，1 次故障注入按设计退出 77。

| 命令或场景 | 结果与范围 |
| --- | --- |
| `node probe.ts` | 退出 0，25 个记录项；覆盖同名任务的项目解析、矛盾 project 拒绝、目录输入及硬保护、去重、明确给目录/未给目录、worker/reviewer 身份限制、reviewer 对失效路径的拒绝、review gate 拒绝不符列表、monitor 空列表。[结果](probe-23EzSs/results.json)。其中 `resumeArgv` 与另一 linked checkout 两项只作观察，不计为验收通过。 |
| `node recovery_launch.ts <场景>`：`alias-retarget`、`canonical-relink`、`missing`、`file`、`recreate`、`resume-race`、`resume-sync-race` | 七项 PASS。别名换目标仍使用原规范目录；规范目录换链接、缺失、变文件均拒绝；同路径重建普通目录允许；原异步与同步竞态均拒绝。各自结果路径见运行日志。 |
| `node lifecycle_probe.ts <场景>`：`conflict-control`、`conflict-relink`、`conflict-missing`、`conflict-recreate`、`conflict-race`、`conflict-sync-race` | 六项 PASS。通过真实 Git 合并冲突触发自动替换；正常及同路径重建保持原列表，其余场景拒绝新启动。 |
| `node lifecycle_probe.ts crash-write /private/tmp/t193-review5/crash-42deei_0`，随后 `node lifecycle_probe.ts crash-resume /private/tmp/t193-review5/crash-42deei_0` | 首进程在 `startThread` 边界按设计退出 77；第二进程退出 0。run 在崩溃前已落盘真实路径；停止期间替换输入别名，恢复仍用原目录。[退出前](crash-42deei_0/crash-before-normalize.json)、[恢复后](crash-42deei_0/crash-resume.json)。重放需给一个新的空夹具目录，保留现有现场。 |
| `node launch_window.ts`；`node launch_window.ts control` | 两项退出 0；变化场景拒绝且零启动记录，正常对照成功，见 F2。 |
| `node /private/tmp/t193-dev2/workbench/tests/test_t141_launch_contract.mjs /private/tmp/t193-review5/t141-launch-contract.json /private/tmp/t193-dev2` | 退出 0，2 项 PASS；是启动配置契约检查，不替代原生沙箱检查。[摘要](t141-launch-contract.json)。重放使用新的摘要文件名。 |
| `node revise_probe.ts`；`node readback.mjs` | 均退出 0；分别核对 D1 的普通重派行为及 F1 的落盘 attempt 列表。[日志](revise-probe.log)、[数据库回读日志](persistence-readback-node.log)。 |
| 从当前测试 AST 读取 `MUTANTS`，逐个核对源码匹配数 | 三个定位仍各自唯一，见 [mutation-locators.json](mutation-locators.json)；未在本轮启动完整变异 e2e。 |
| project-map `status`、冻结候选核对 | 原仓库地图开始和结束均 Problems 0、Stale living docs 0；[结束输出](project-map-status.txt)。候选完整性检查见 STATUS。 |

探针期望来自变化前确定的原目录，不从新 attempt 或启动 argv 反推。F1 两项除启动数量外，还独立核对持久化列表；F2 保留成功对照，排除“总是拒绝也能通过”。

### 所附真实入口与回归证据：已读取核对，本轮未重跑

来源：[原仓库 T-193 证据目录](/Users/luckye/Documents/Code/a2a/evidence/2026-10-27-batch28/T-193)。提取的状态、检查项及原始错误见 [supplied-evidence-summary.json](supplied-evidence-summary.json)。

- [green-05-launch-check.json](/Users/luckye/Documents/Code/a2a/evidence/2026-10-27-batch28/T-193/green-05-launch-check.json)：7 项 PASS。跨已打开项目建卡派发与侧栏归属、未指定不给、未打开项目拒绝并说明、仓库硬保护、显式目录进入记录/argv、已换链接目录不授予。测试使用真实后台、socket、终端身份、交互 Claude CLI，模型接口为脚本化夹具。
- [mutant-follow-relinked-02.json](/Users/luckye/Documents/Code/a2a/evidence/2026-10-27-batch28/T-193/mutant-follow-relinked-02.json)：原状态为 INCOMPLETE，实际已通过前六项，明确失败于 `relinked_directory_never_granted`。坏实现生成的 reviewer 启动记录含数据目录，业务断言捕获；不是定位或启动准备失败。review gate 随后拒绝不等于此前从未生成错误启动配置。
- [T-140 新回归](/Users/luckye/Documents/Code/a2a/evidence/2026-10-27-batch28/T-193/regression-t140_extra_dirs-02.json)：22 项 PASS，包含设置界面、追加事件、明确给目录后的 shell/文件工具及 reviewer 写入、未给目录后的拒写、monitor 空目录启动配置。
- [T-141 新回归](/Users/luckye/Documents/Code/a2a/evidence/2026-10-27-batch28/T-193/regression-t141_loosened_limits-02.json)：24 项 PASS，包含原生写边界及临时目录、用户配置继承、审批拒绝与问题处理、MCP、网络、reviewer 配置及坏结果拒绝。
- [T-123 回归](/Users/luckye/Documents/Code/a2a/evidence/2026-10-27-batch28/T-193/regression-t123_project_identity.json)：22 项 PASS，是较早的项目隔离与迁移回归记录。其新跨项目判据只拒绝显式 project 与完整 task id 矛盾的请求，与 T-193 一致。
- [review3-fix-probes/summary.json](/Users/luckye/Documents/Code/a2a/evidence/2026-10-27-batch28/T-193/review3-fix-probes/summary.json)：所附修后复跑观察与本轮一致；本轮以自己的输出和断言为 F1、F2 关闭证据。

**COUNTEREXAMPLE：**第 3 轮冻结候选及其 [NO_GO 报告](review3-REPORT.md) 提供 F1、F2 的已知坏实现红态；本轮保留相同注入点重放后转绿。另有所附 `red-base.json` 在跨项目业务断言失败，`mutant-project-extra-dirs-02.json` 在默认继承项目目录的业务断言失败。原摘要中的 INCOMPLETE 原样保留；这里只将明确的业务断言失败认作反事实证据，不把环境异常当红态。

### 说明与调用链核对

项目设置页、worker/reviewer/monitor 角色卡、`a2a help`、终端插件说明的主要授权描述与代码一致：项目设置不自动授权 worker，派发明确给目录，reviewer 沿用 worker 列表，monitor 不得额外目录，额外目录改动不经门禁审查与集成。README 的重派描述按 D1 澄清。

源码中首次规范化只有 `extraDirectories(..., approved=false)`；内部恢复/替换只核对和保留旧列表；生产启动构造直接使用 attempt 列表，review gate 对比 reviewer 列表与 attempt，未发现另一处把旧路径解析为新授权列表的入口。`Panes.restore()` 在任何 CLI 执行前拒绝有 attempt 的记录，worker/reviewer 必须经门禁回收重派；`resumeArgv()` 单独保留旧字符串不是一条可达的受管恢复绕过。

**RULE：**此前反复出现的失败类是“检查后重新解析或跨异步空档继续启动，授权对象漂移”。建议 T-193 测试维护将本轮三个时序反例及正常对照纳入常规回归，分别断言恢复/冲突替换的 attempt、run 落盘列表，以及启动记录/argv 保留原列表或在启动前明确拒绝。当前完整 e2e 的 `follow-relinked` 变异能证明另一种跟随链接错误被捕获，但不替代这三个时序检查。本轮只建议，不新增 ticket 或修改测试。

## LIMITATIONS

- 按 brief，本轮未重跑完整 e2e、Electron 界面、真实模型或原生 CLI 沙箱。所附真实入口回归是外部既有证据，不能冒称本轮运行。T-141 记录了基线与脏文件清单，其余多份摘要 `revision=null`；这些记录没有完整冻结 diff，不能仅凭摘要证明与当前候选逐字节一致。
- 本轮探针使用真实文件系统、Git、SQLite、门禁和生产启动构造；运行时身份和 CLI 生命周期由夹具提供，`store.launch` 边界截获记录并停止，未创建 PTY。结论覆盖配置构造、授权列表持久化和拒绝条件，不声称真实 CLI 已执行记录或已证明最终写入效果；agy/opencode 没有本轮原生复跑。
- 时序注入保留底层真实返回值，只改变本轮隔离目录；证明对应交错顺序，不估计日常发生概率。校验和 PTY 启动不是文件系统原子操作；本轮未扩展为对抗任意外部进程在最终同步检查后继续换链接、运行期路径变化、任意嵌套链接或 inode 绑定的安全承诺。同一规范路径重建普通目录仍允许，符合本轮路径契约。
- 路径变化被拒后可能留下 `preparing` attempt/worktree，冲突替换记录 `repair.state=unknown`；证据保留该状态。本轮验证的是拒绝授权漂移，没有把它当作任务成功、已自动回收或完整恢复流程通过。
- 附加持久化回读最初使用 Python SQLite 只读 URI 时，两次均报 `unable to open database file`；原始记录保留于 [persistence-readback-python-error.json](persistence-readback-python-error.json)。随后使用产品同款 Node SQLite 只读回读成功。未将 Python 环境错误计为产品红态，也未重跑或覆盖原业务场景。
- 本轮 PASS 限于 brief 指定的配置正确性审查。完整系统安全、模型判断能力、原生运行期授权，以及 T-193 ticket 的最终关闭不在本轮结论内；D1 文案澄清仍由实现侧处理。
