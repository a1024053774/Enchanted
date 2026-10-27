# T-194 独立只读审查（第 6 轮）

## STATUS

**NO_GO（记录一致性的验收判据）**。第 4、5 轮共 11 个原始反例现在全部被拒绝；但扩大检查后，仍复现了无上下文归一化和重新验收起止事件未校验两类误放。不能关闭第三项 Acceptance。没有据此确认生产门禁写出了错误记录。

TARGET：`/private/tmp/t194-cand6`，HEAD `1c673a4b473f6f3ad778574cc08a842b5f4697c1`。相对第 5 轮 `9eb634d` 只改 `workbench/tests/test_t194_mcp_entry_e2e.py`，93 行新增、32 行删除。`bf16c21` 中的 T-195 不在审查范围。始末 HEAD、受控文件状态一致，既有未跟踪项 `workbench/node_modules` 保留。未修改候选、ticket、历史证据或提交。

验收依据是主仓库只读的 [T-194](/Users/luckye/Documents/Code/a2a/.project-map/tickets/T-194-mcp-dispatch-entry.md) 三项 Acceptance、T-189 第 3 条及门禁的身份绑定契约；新增测试不是需求来源。**Ubiquitous language**：终端身份负责权限，原生会话号是调用方报告的数据。**Tracer bullet** 核对真实 Claude Code → MCP／命令 → socket → 后台／SQLite。按 **Deep modules** 检查，两入口仍经 `terminalCli.ts:115` 的同一 `send/requestAt` 调用后台，没有新增平行业务门禁。

## FINDINGS

### R6-F1 · [P2] 归一化消除了任务内部的绑定关系，并整体删除仍有业务含义的证据

位置：[占位规则](/private/tmp/t194-cand6/workbench/tests/test_t194_mcp_entry_e2e.py:274)、[全局排除键](/private/tmp/t194-cand6/workbench/tests/test_t194_mcp_entry_e2e.py:282)、[递归归一化](/private/tmp/t194-cand6/workbench/tests/test_t194_mcp_entry_e2e.py:289)。

允许两任务使用不同的 ID、提交和路径，不意味着任意 UUID、提交或绝对路径都等价。现在所有匹配值都变成同一个占位符，既不验证值属于该任务，也不保留同一任务内的引用关系。从真实绿色记录只改命令入口的一处字段，以下不一致仍被接受：

- `completion_check.result.cwd` 改为 `/private/tmp/unrelated-repo`；第一次验收及重新验收中分别修改，均通过。
- `trailer_check.trailers.attempt` 改为无关 UUID；该任务其他 attempt 引用保持原值，仍通过。
- `path_check.paths` 从该任务的 `b.txt` 改为另一任务的 `a.txt`，卡内允许路径仍是 `b.txt`，仍通过。
- `integrated.intent.C` 改为 40 个 `1`，其他候选提交引用保持原值，仍通过。
- 评分的 `attempt` 改为无关 UUID，`same_scores` 仍通过。

此外，排除理由没有被约束到具体字段及允许差异：`revalidation` 和 `shared_refs` 在任意嵌套位置都整项删除。将 `integrated.intent.attempt.revalidation.misses` 从 1 改为 9，或仅从审查快照删除**该任务自己的** verification ref，比较器仍通过。前者不是耗时，后者也不是另一任务多留下的 ref。

证据：[predicate-audit-01.json](predicate-audit-01.json)、[exclusions-audit-01.json](exclusions-audit-01.json)。这些探针只改内存中的记录；未修改数据库，也未证明生产存在对应绕过。

最小修正：使用已知的本任务／attempt／verification／review 对应值作具名映射，先核对内部绑定，再归一化跨任务差异。路径只替换已知夹具根和已声明任务文件，保留目录用途及相对结构；不要按字符串外形抹除任意值。`shared_refs` 仅排除已确认来自另一任务的附加项；`revalidation` 单独核对状态、次数和绑定后再归一化。保留上述反例，在现有完整入口测试末尾要求拒绝。

### R6-F2 · [P2] 重新验收起止事件只核对类型，内容仍被整段吞掉

位置：[区间校验与删除](/private/tmp/t194-cand6/workbench/tests/test_t194_mcp_entry_e2e.py:259)，尤其第 260、263、267 行。

新代码正确校验了 `inner` 的类型、顺序、次数、嵌套结果和成功状态，但 `integration_compare_failed` 与 `review_reused` 两个端点的 `details` 没有参加校验，随后与区间一起删除。

同一真实绿色基线中，每次只改一处，以下五例的 `same_records` 均仍为 `true`：起点 `misses: 1 → 4`；起点 `review_reuse_binding.fence: 1 → 999`；终点 `review.state: passed → needs_fix`；终点 `review.result.verdict: 可合并 → 需修改`；终点 `task.state: verified → paused`。事件类型、顺序及内部成功链完全保留。

这些值决定该区间能否被视为正常重新验收：生产 `core.ts:1990` 在 misses 达到 4 时暂停，不再继续验收；`core.ts:2592` 的审查复用要求已通过且绑定当前候选，成功后任务为 `verified`。只看到两个事件名不足以证明这些条件。

证据：[predicate-audit-01.json](predicate-audit-01.json) 的五个 `marker_*`／`reused_*` 用例。最小修正是删除区间前核对两个端点的状态、次数及 task／attempt／candidate／verification／review 关联；保留新旧反例，不能只增加另一个事件类型条件。

## EVIDENCE

### 前轮发现与本轮判据探针

| 项目 | 结果 |
| --- | --- |
| R5-F1 原始反例 | **原反例已关闭，整类问题未关闭**。完成条件 passed、退出码、验收状态、审查结论、运行方式、评分 facts 的六例均被拒绝；R6-F1 是仍会丢失语义的其他字段。 |
| R5-F2 原始反例 | **区间内部缺口已修复，整段归一化仍未关闭**。区间内重复派发、空区间均被拒绝；额外修改区间内完成条件、退出码、运行方式、验收状态的四例也被拒绝；端点仍有 R6-F2。 |
| 第 4 轮三个反例 | 改评分、倒序、原位置重复派发，全部拒绝。 |
| 正向与误拒检查 | 历史普通、慢启动两份数据库的记录与评分均通过当前原函数；额外四个正例（耗时、事件顶层身份／时间、PID、ISO 时间变化）均通过。本轮未复现误拒，未穷举正常时序。 |
| 独立反事实 | 用 `git show 9eb634d:…` 取得第 5 轮原函数，对同一数据库执行同一组 11 个原反例：8 个仍误放；当前候选全部拒绝。见 [round5-predicate-counterfactual.json](round5-predicate-counterfactual.json)。 |
| 新增检查总计 | 主探针 30 例：4 个正常差异均接受；26 个反例中 15 个拒绝、11 个误放。排除键探针另有 2 个反例，均误放。原函数由 AST 提取执行，没有重写比较逻辑。 |

### 本轮真实完整入口复跑

命令及起止时间、退出码见 [fullflow-execution.json](fullflow-execution.json)，原输出见 [fullflow-01.log](fullflow-01.log)。环境为 Node `v26.5.0`、Claude Code `2.1.311`，模型端是本地脚本化 Messages 服务。

**INCOMPLETE**：[fullflow-01.json](fullflow-01.json) 前四项通过：MCP 工具可见、无角色时两入口同样拒绝、角色确认生效、CLI 与原生会话号正确。随后按原期限等待交付，退出码 1，错误为 `超时：T-1 交付`。两任务均为 `claimed`，两名 worker 的真实 PTY 都记录 `sandbox-exec: sandbox_apply: Operation not permitted`，见 [runtime-observation-01.json](runtime-observation-01.json)。没有降级沙箱、代 worker 提交或跳过门禁。

后台已按夹具原有清理流程停止，socket、PID 文件均不存在，见 [runtime-final-01.json](runtime-final-01.json)。本轮未进入交付后的审查、集成和最终记录比较。

### 历史证据与整票 Acceptance

已回读简报列出的六份 v5test JSON，见 [historical-summaries-01.json](historical-summaries-01.json)：`green-13` 的失败保留；`green-14` 9 项通过；`green-15` 10 项通过、等待 2 次；红态在入口缺失失败；两个变异分别在会话号与角色确认的目标断言失败。未把红态脚本原有的 `INCOMPLETE` 改成 PASS。

进一步只读回查两份绿色数据库：任务均为 `accepted`，verification／review 均为 `passed`，审查结论为“可合并”，完成命令均退出 0；每任务各一次派发、交付、审查结果、集成和评分，第二集成任务有两轮验收。见 [historical-readback-01.json](historical-readback-01.json)。慢启动源码副本中 `src`、`terminal`、`hooks`、`roles` 的 76 个受控文件与候选逐字节相同，仅对 `terminalCli.ts` 去除明确注入的 6 秒延迟；见 [historical-source-comparison-01.json](historical-source-comparison-01.json)。普通绿色没有独立源码副本，未把其可变开发目录视为冻结快照。

| T-194 Acceptance | 判断及证据边界 |
| --- | --- |
| 四家 CLI 的 MCP 支持实测记录 | **PASS（记录的版本与范围）**。候选四家实测文档存在；`real-05-cand3.json` 的 Codex／opencode 六项通过；agy 交互探针记录服务器 initialize、tools/list 后模型回答 `NO_TOOL`，支持其继续命令入口的限定结论；Claude 有本轮真实入口及历史全流程。未重新调用其余三家供应商模型。 |
| 至少一家经 MCP 走通完整链 | **历史正向证据充分；本轮复跑 INCOMPLETE**。历史真实 CLI、MCP、socket、落库与生产源码比对支持 Claude 的本地全流程；本轮受 worker 沙箱限制，不能声称当前环境完整重验通过。 |
| 两入口门禁记录一致 | **NO_GO（验收判据）**。两份实际正常样本通过当前比较，旧反例已拒绝，但新增 13 个不一致反例仍误放，不足以关闭该项。 |

复现时指定新产物名称，保留原证据：

```sh
cd /private/tmp/t194-review6
python3 -B run_candidate_test.py test_t194_mcp_entry_e2e.py --summary /private/tmp/t194-review6/fullflow-replay.json
python3 -B audit_predicates.py /private/tmp/t194-review6/predicate-replay.json
python3 -B audit_exclusions.py /private/tmp/t194-review6/exclusions-replay.json
python3 -B audit_round5_counterfactual.py /private/tmp/t194-review6/round5-replay.json
```

防止同类问题再次出现的机械检查：在现有完整入口测试的最终判据检查中，同时保留正常差异正例和身份绑定、目录用途、起止状态、持久化次数与本任务 ref 的负例；两类输入必须分别接受和拒绝。该建议是后续修复的验收要求，本轮没有实施。

## LIMITATIONS

- NO_GO 是验收测试的可复现误放，不是已确认的生产门禁缺陷；反例在内存中构造，不作为生产真实失败报告。
- 本轮完整流程未到达最终比较。慢启动、父提交和两个生产变异未在本轮重复运行；上述结论明确依赖保留的历史证据。未重跑无生产变化的生命周期套件，未穷举协议、并发及等待上限。
- 脚本化模型验证本地编排、权限、异步发现、真实 CLI 交互和交付记录，不能证明真实模型理解、工程判断、审查质量或生产可靠性。检索／记忆、媒体生成和生产外部写入为 N/A。
- 历史摘要 revision 为空、夹具 code_revision 为 `fixture`，因此将源码比对与运行元数据分开陈述，不补称历史运行直接绑定当前提交。
- 审计辅助脚本的两次初始化错误及修正保留于 [predicate-setup-failure.txt](predicate-setup-failure.txt)，未计为候选失败或负例拒绝证据。系统 `ps` 被沙箱拒绝；清理只核对夹具清理返回及 socket／PID 文件消失，未声称完成全进程枚举。
- 项目地图始末均为 Problems 0、Stale living docs 0；候选 `git diff --check bf16c21 HEAD` 通过。状态证据见 [candidate-start.json](candidate-start.json)、[candidate-final.json](candidate-final.json)。报告只交付审查，不代为修复。
