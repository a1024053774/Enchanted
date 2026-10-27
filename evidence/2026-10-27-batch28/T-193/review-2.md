# T-193 独立只读审查（第 2 轮，重开）

## STATUS

**NO_GO**。复现两处仍会改变额外目录授权对象的 P1 问题：恢复/冲突替换的预检与重新解析分离，以及首次派发的获批目录持久化过晚。另有一处 P2 变异检查入口失效。

审查对象：`/private/tmp/t193-dev2`，基线 `33debf82a195ee4c0f421bdc924f56578eb1c89f` 加工作区 T-193。开始保存的 [reviewed-candidate.diff](reviewed-candidate.diff) 为 73,321 字节；结束时与候选实时 diff、候选自带 `T-193.diff` 均逐字节相同，工作区状态也未改变，见 [candidate-verification.json](candidate-verification.json)。未修改候选或原仓库，未提交；全部新增产物在本审查目录。

判据来自 T-193、T-189 第 1 条、T-196 第 3 条及 brief：主控可管理多个已打开项目；每个任务仍绑定一个仓库；额外目录逐次指定并记录；恢复和自动替换不得悄悄换成另一个授权对象。按 **Ubiquitous language** 区分“项目设置的额外目录”和“本次派发的额外目录”。本轮以真实门禁、Git、SQLite 和生产启动构造组成 **Tracer bullet**；不实施修复或新增 **Deep modules**。

上一轮发现的复核结论：

| 原发现 | 本轮结论 |
| --- | --- |
| F1：reviewer 跟随被替换的获批目录，门禁只核对启动记录自洽 | 原复现场景 **PASS**。`panes.ts:834` 使用 attempt 的获批路径，目录消失、变文件、变成指向状态根的链接时，在保存新启动记录前拒绝；`core.ts:2485` 拒绝启动记录与 attempt 不同的目录列表。此结论不覆盖下述重新 claim 的遗漏。 |
| F2：run 保存原始别名，恢复后授权漂移 | **未从根因修好**。正常派发完成后确实保存真实路径，普通别名换目标场景 PASS；但 R1、R2 仍可让恢复重派授权另一个目录。 |
| F3：项目设置页面承诺 worker/reviewer/monitor 自动获得目录 | **PASS（源码核对）**。`app/ProjectSettings.tsx:34` 已说明普通终端选用、worker 逐次派发指定、monitor 无额外目录；与当前启动构造相符。README、角色卡和 help 的相关授权说明已同步。未重新打开 GUI。 |
| F4：T-123/T-140/T-141 回归仍要求旧行为 | 三个文件的旧判据已更新，所附摘要分别报告 **22/22/24 项 PASS**，详见证据与限制。但新增 T-193 测试的一个变异入口已失效，见 R3，不能把旧变异结果当作当前候选的完整反事实证明。 |

## FINDINGS

### R1 · P1：恢复和冲突替换只在 claim 之前预检，claim 会再次跟随链接并改写获批目录

位置：[workbench/src/gates/core.ts:1598](/private/tmp/t193-dev2/workbench/src/gates/core.ts:1598)；恢复预检在 [3253 行](/private/tmp/t193-dev2/workbench/src/gates/core.ts:3253)，冲突替换预检在 [1735 行](/private/tmp/t193-dev2/workbench/src/gates/core.ts:1735)。

恢复和冲突替换会先检查旧获批路径仍解析为自身，再调用 `claim()`。但 `claim()` 在 `checkClaimPaths`、读取集成基线、检查验收文件等异步操作之后，又调用 `extraDirectories()`，把传入的旧真实路径当作新的用户输入执行 `realpathSync()`。如果目录在这些异步操作期间被改成链接，新 attempt 就保存新目标。`Panes` 随后看到的是新目标的规范路径，因此新的启动前检查也会通过。

独立复现使用事先确定的 `initial` 与 `unrelated` 两个夹具目录：第一份 attempt 和启动参数只有 `initial`；在生产 `checkClaimPaths()` 完成时注入一次文件系统变化，将 `initial` 改成指向 `unrelated` 的链接；没有改动门禁返回值或候选文件。结果如下：

- run 恢复：新 attempt、run 的 dispatch 记录、生产 `--add-dir` 和 `sandbox_workspace_write.writable_roots` 都变成 `unrelated-data`。见 [launch-recovery-LRom1g/results.json](launch-recovery-LRom1g/results.json)。
- 冲突替换：通过 `dispatch → submit → verify` 真实门禁入口制造 Git 合并冲突，并令受控 worker 已停止。替换 attempt 的生产记录和两种可写目录参数都变成 `unrelated`。见 [lifecycle-bQxl2T/conflict-race.json](lifecycle-bQxl2T/conflict-race.json)。

这证明“新记录与新 argv 一致”仍不足以证明授权正确：它们已经一起偏离原获批路径。这里没有声称能绕过现存仓库/状态根保护；未获批的普通目录被授予启动参数权限，已违反本次配置正确性判据。

最小修正方向：在创建新 attempt 的根因层区分“首次用户输入的路径”和“内部重用的获批真实路径”；内部重用应保留原列表，并在落入新 attempt 时验证路径仍为自身且为目录、仍满足硬保护，不能重新解析成另一个授权对象。把上述异步间隔的路径变化加入恢复和冲突替换检查。

### R2 · P1：run 的获批目录到整个 dispatch 返回后才持久化，崩溃恢复仍会使用旧别名

位置：[workbench/src/gates/core.ts:3067](/private/tmp/t193-dev2/workbench/src/gates/core.ts:3067)；更早的 run 绑定持久化在 [1617 行](/private/tmp/t193-dev2/workbench/src/gates/core.ts:1617)。

`run_bound` 已保存 attempt/thread 绑定，但其 `dispatch.extra_directories` 仍是原输入；直到 worker 创建、身份绑定、claimed 状态保存、`startThread()` 返回，`runDispatch()` 才把列表换成 attempt 的获批真实路径。因此后台可在已有获批 attempt、却尚未保存规范目录的状态下退出。

独立探针在生产 `startThread` 调用边界让进程直接以 77 退出，保留真实 SQLite。退出前：原输入为 `alias → initial`；attempt 和生产启动参数均为 `[initial]`；落盘 run 仍为 `[alias]`、`phase=dispatching`、`outcome=running`。后台停止期间仅移除这个别名链接并在原位置创建普通目录，原来的 `initial` 保留。重新打开数据库并调用生产 `resumeRuns()` 后，旧 attempt 被回收，新 worker 的记录、`--add-dir` 和 writable roots 均获得 `[alias]`，与原获批的 `[initial]` 不同。

见 [crash-run.json](crash-run.json)、[退出前记录](crash-pujpjgz4/crash-before-normalize.json)、[恢复后记录](crash-pujpjgz4/crash-resume.json)。这次目录变化全部发生在两个进程之间，不依赖 R1 的并发时序。恢复探针在新派发之后主动请求关闭，以有界结束；最终 `daemon_stopping` 不代表整个 run 完成，但不影响已经构造了错误授权的新 worker 这一事实。

最小修正方向：首次获批真实路径应在 run 与 attempt 绑定时、任何 runtime 启动之前持久化，或恢复时以已绑定 attempt 的获批目录为权威；不能等整个异步派发成功返回后才建立这一持久化不变量。

### R3 · P2：`project-extra-dirs` 变异定位仍匹配旧代码，当前候选运行不到行为断言

位置：[workbench/tests/test_t193_multi_project_e2e.py:34](/private/tmp/t193-dev2/workbench/tests/test_t193_multi_project_e2e.py:34)，定位断言在 [80 行](/private/tmp/t193-dev2/workbench/tests/test_t193_multi_project_e2e.py:80)。

这个变异仍查找带 `.map(path => realpathSync(path))` 的旧 `extraDirectories` 声明，当前源码已改为直接使用 attempt 的获批列表。用候选原测试的 `--mutant project-extra-dirs` 实际执行变异准备，会以“变异定位必须唯一”中止，发生在启动后台和创建结果摘要之前。见 [mutation-preflight.json](mutation-preflight.json)。包装脚本只把临时夹具重定向到本审查目录，没有改变候选测试或定位逻辑。

这不是“坏实现被业务断言拒绝”，所附旧 `mutant-project-extra-dirs.json` 也不能证明当前反事实入口仍可运行。最小修正是更新定位，重新运行此变异，并确认失败点是 `no_extra_directory_unless_named` 等授权行为断言，而非准备阶段异常。

## EVIDENCE

### 本轮独立执行

以下命令均从 `/private/tmp/t193-review3` 执行；探针自动新建夹具，重复运行不会覆盖旧 JSON。`REPRODUCED` 表示确认缺陷，不是产品 PASS。

| 检查与命令 | 结果与产物 |
| --- | --- |
| `node probe.ts` | 退出 0，完成 25 个记录项；包括原 F1 拒绝、review gate 拒绝被改目录列表、monitor 无额外目录。见 [probe-1R1FrC/results.json](probe-1R1FrC/results.json)、[日志](probe-run-01.log)。其中 `resumeArgv` 和同仓库另一 checkout 两项只是观察，不计为额外验收通过。 |
| `node recovery_cases.ts <场景>`，场景为 `alias-retarget`、`canonical-relink`、`missing`、`file`、`recreate` | 五项 **PASS**。分别见 [别名换目标](recovery-smorVY/results.json)、[真实路径换链接](recovery-8epFYz/results.json)、[删除](recovery-ZrnUG4/results.json)、[换文件](recovery-V6ukXI/results.json)、[同路径重建](recovery-8I6ZTF/results.json)。模拟 CLI 生命周期，使用真实 Git/SQLite/停止恢复逻辑。 |
| `node recovery_cases.ts resume-race`；随后用 `node recovery_launch.ts resume-race` 核对生产启动构造 | 两次均 **REPRODUCED**，退出 0；[门禁结果](recovery-aCsSxB/results.json)、[生产 argv 结果](launch-recovery-LRom1g/results.json)、[日志](recovery-launch-race.log)。 |
| `node lifecycle_probe.ts <场景>`，场景为 `conflict-control`、`conflict-relink`、`conflict-missing`、`conflict-recreate`、`conflict-race` | 前四项 **PASS**，最后一项 **REPRODUCED**。见 [正常替换](lifecycle-rDm6UF/conflict-control.json)、[换链接拒绝](lifecycle-0lOE4X/conflict-relink.json)、[缺失拒绝](lifecycle-dIRUhi/conflict-missing.json)、[同路径重建](lifecycle-xSQf26/conflict-recreate.json)、[时序反例](lifecycle-bQxl2T/conflict-race.json)。第二轮日志为 `lifecycle-*-02.log`。 |
| `node lifecycle_probe.ts crash-write <新建夹具目录>`；紧接 `node lifecycle_probe.ts crash-resume <同一目录>` | 首进程按探针设计退出 **77**，恢复进程退出 **0**，结果 **REPRODUCED**；实际完整命令、stdout/stderr、退出码保存在 [crash-run.json](crash-run.json)。 |
| `python3 mutation_preflight.py` | 包装脚本退出 0，捕获候选变异准备阶段的断言失败；**REPRODUCED R3**，不是变异行为通过。见 [结果](mutation-preflight.json)、[日志](mutation-preflight.log)。 |
| `node /private/tmp/t193-dev2/workbench/tests/test_t141_launch_contract.mjs /private/tmp/t193-review3/t141-launch-contract.json /private/tmp/t193-dev2` | **PASS，2 项**，退出 0；[摘要](t141-launch-contract.json)。仅启动契约，不能代替原生沙箱检查。 |
| `git -C /private/tmp/t193-dev2 diff --check HEAD`；候选 diff 与状态前后直接比较 | **PASS**；[candidate-verification.json](candidate-verification.json)。未计算摘要或校验值。 |
| project-map `status`，开始与结束各一次 | 均为 Problems 0、Stale living docs 0；[结束输出](project-map-status.txt)。未改 ticket 或地图。 |

目录删除后在相同规范路径重建普通目录，当前实现允许启动，记录与参数仍使用原字符串。需求和当前契约采用路径，没有要求绑定 inode；本轮据此记录为路径一致性通过，不将“不同目录实体”自行增加成拒绝条件。

冲突探针首轮五个场景因受控 runtime 在 submit 时未设 `running=true` 而被 `identity_conflict` 拒绝，均为 **INCOMPLETE 的夹具失败**，不是候选缺陷。已保留 `lifecycle-*.log`、对应夹具 JSON 和 [首版探针](lifecycle_probe-v1.ts)；修正模拟运行状态后才得到上表第二轮结果。没有覆盖首轮记录。

### 所附证据与反事实核对

来源目录：[原仓库 T-193 证据](/Users/luckye/Documents/Code/a2a/evidence/2026-10-27-batch28/T-193)。本轮读取摘要及关键观测，并对照候选测试源码；未冒充本轮重跑。

- [green-03-relinked.json](/Users/luckye/Documents/Code/a2a/evidence/2026-10-27-batch28/T-193/green-03-relinked.json)：7 项 PASS，实际 reviewer 拒绝 `extra_directory_changed`，未记录状态根获批；其获批路径期望在链接变化前计算。
- [green-02-relinked.json](/Users/luckye/Documents/Code/a2a/evidence/2026-10-27-batch28/T-193/green-02-relinked.json)：保留的 INCOMPLETE；观测已是拒绝且无错误授权，但旧期望计算时机导致断言失败，不能计为 green。
- [red-base.json](/Users/luckye/Documents/Code/a2a/evidence/2026-10-27-batch28/T-193/red-base.json)：基线在跨已打开项目建卡/派发的业务断言失败。
- [mutant-home-project-only.json](/Users/luckye/Documents/Code/a2a/evidence/2026-10-27-batch28/T-193/mutant-home-project-only.json)：坏实现被跨项目行为断言拒绝。
- [mutant-follow-relinked.json](/Users/luckye/Documents/Code/a2a/evidence/2026-10-27-batch28/T-193/mutant-follow-relinked.json)：坏实现实际创建含状态根的 reviewer 启动记录，随后 review gate 拒绝；测试因错误目录已获批而失败，证明没有把事后拒绝误当作启动前保护。
- [mutant-project-extra-dirs.json](/Users/luckye/Documents/Code/a2a/evidence/2026-10-27-batch28/T-193/mutant-project-extra-dirs.json)：旧运行在未指定目录却继承项目设置的断言失败；当前入口适用性受 R3 限制。以上失败摘要写 `INCOMPLETE`，本报告仅在其有明确业务断言和观测时把它们视为反事实拒绝证据，不改写原状态。
- [T-140 回归](/Users/luckye/Documents/Code/a2a/evidence/2026-10-27-batch28/T-193/regression-t140_extra_dirs.json)：22 项 PASS，包含 worker/reviewer 对明确授权目录的写入与外部拒写、目录移除、monitor 无额外目录参数。monitor 两项只检查启动配置，没有证明其原生工具实际拒写。
- [T-141 回归](/Users/luckye/Documents/Code/a2a/evidence/2026-10-27-batch28/T-193/regression-t141_loosened_limits.json)：24 项 PASS，包括原生写边界、MCP、网络、提问答复、reviewer 校验。摘要记录基线和改动文件列表，与本候选清单吻合。
- [T-123 回归](/Users/luckye/Documents/Code/a2a/evidence/2026-10-27-batch28/T-193/regression-t123_project_identity.json)：22 项 PASS，包含项目同名任务隔离、矛盾 project 拒绝、迁移与各仓库集成。按 brief，这是在原仓库工作区运行的证据。

R1/R2 的修复后检查应以变化前已批准的真实路径为独立期望，在 run 恢复、Git 冲突替换、首次派发崩溃恢复三个入口断言“保持同一获批列表或明确拒绝”，并核对新 attempt、持久化 run 和生产启动参数。此类检查能直接捕获此次重复出现的“重新解析名字改变授权对象”，比新增一条文字规则更可靠。

## LIMITATIONS

- 本轮没有启动真实模型 CLI 或重跑完整 Electron/原生沙箱 e2e；brief 明确允许不重跑。所附绿态和回归摘要保留其来源与日期，未将其提升为本轮独立执行结果。摘要没有完整冻结 diff，不能仅凭相同基线或文件清单证明逐字节对应当前候选。
- 当前独立反例使用真实文件系统变化、Git、SQLite、门禁调用和生产启动参数构造；CLI 生命周期、进程身份由探针提供，生产启动记录在 PTY 创建前被截获。已证明错误授权进入配置，没有执行对未获批目录或状态根的破坏性写入，也不声称验证了原生 CLI 在该场景下的最终文件操作。
- R1 是确定性时序注入：完成生产 `checkClaimPaths()` 后只改变文件系统。它证明可达异步间隔存在，不给出日常使用中的发生概率。R2 使用独立进程退出与真实数据库重开，目录变化发生在后台停止期间。
- `Panes.restore()` 对有 attempt 的 worker/reviewer 明确拒绝直接恢复，要求回收重派。因此探针里单独调用 `resumeArgv()` 保留旧字符串的观察，不作为另一条可达的 worker 恢复缺陷。
- 此轮聚焦 brief 的配置正确性与四条修复，未评价真实模型理解能力、全部 CLI/操作系统组合、任意嵌套链接的运行期沙箱行为或性能。未扩展路径授权为 inode 身份契约。
- **放行条件未满足**：R1、R2 修复并补齐其失败先行的入口证据前，本候选保持 **NO_GO**；R3 也需修复后才能恢复该项反事实检查。
