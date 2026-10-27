# T-194 独立只读审查（第 5 轮）

## STATUS

**NO_GO（本轮验收测试）**。R4-F1 的结果下标、R4-F2 的连接等待已在真实慢启动入口得到修复验证；R4-F3 的三个原始反例也已被拒绝，但记录一致性的证明仍有两个可复现缺口，不能将 R4-F3 整项关闭。没有据此确认生产门禁存在相同缺陷。

TARGET：`/private/tmp/t194-cand5`，HEAD `9eb634d91fcd64a8101d2b4c7ae53812bd26f7cc`。相对 `d1989e9` 仅修改 `workbench/tests/test_t194_mcp_entry_e2e.py`，93 行新增、39 行删除；生产路径无差异。`bf16c21` 仅作缺失 MCP 入口的红态对照，其 T-195 改动不在本轮范围。

范围是核对前三项发现、等待边界、比较器误放与误拒，以及当前环境的完整流程；不修候选、不提交、不改 ticket 或历史证据。验收依据来自主仓库只读的 [T-194 Acceptance](/Users/luckye/Documents/Code/a2a/.project-map/tickets/T-194-mcp-dispatch-entry.md) 和 [T-189 第 3 条](/Users/luckye/Documents/Code/a2a/.project-map/tickets/T-189-real-use-fixes-decisions.md)，未以新测试的输出充当需求。

沿用 **Ubiquitous language**：终端身份负责权限，原生会话号是调用方报告的数据。**Tracer bullet** 经过真实 Claude Code、MCP 子进程、socket 与后台数据库。按 **Deep modules** 核对，两入口仍经 `terminalCli.ts` 的同一 `send/requestAt` 调用后台门禁，未新增平行业务实现。

## FINDINGS

### R5-F1 · [P2] 比较器仍忽略关键门禁结果值与嵌套状态

位置：[semantic:254](/private/tmp/t194-cand5/workbench/tests/test_t194_mcp_entry_e2e.py:254)、[值投影:262](/private/tmp/t194-cand5/workbench/tests/test_t194_mcp_entry_e2e.py:262)；评分事实的同类缺口在 [same_scores:274](/private/tmp/t194-cand5/workbench/tests/test_t194_mcp_entry_e2e.py:274)。

每条记录只比较顶层字段名，以及顶层 `state`、`launch_overrides` 和去掉任务文件信息的卡。实际验收状态位于 `details.verification.state`，审查结论位于 `details.review.result.verdict`，完成条件结果也在其他字段中。这些不因任务 ID 或时间而变化的值均未比较。

用历史真实绿色数据库作为正向基线，从冻结候选 AST 执行其原函数。只改命令入口的一处证据，以下五个变体均仍被 `same_records` 接受：

- 首条 `completion_check.passed`：`true → false`。
- 首条 `completion_check.result.exit`：`0 → 1`。
- 首条 `verification_result.verification.state`：`passed → failed`。
- `review_result.review.result.verdict`：`可合并 → 需修改`。
- `dispatched.attempt.runtime_mode`：`workspace-write → read-only`。

这些变体保留事件类型、顺序、次数和字段名，因此最终 `same_gate_events` 的必需类型条件也不会补上这个缺口。另将评分 `facts.human_interventions` 从 0 改为 9，`same_scores` 仍接受；它现已正确比较 `data` 与列出的来源字段，但未比较非时间的评分事实。原基线与全部变体见 [predicate-audit-01.json](predicate-audit-01.json)。

影响：当前 PASS 仍可伴随两入口的验收、审查或派发记录语义不一致。这是验收判据的反例，未声称生产真的写出了上述错误记录。

最小修正：按事件契约比较必要结果值，包括嵌套状态、通过标志、退出码、审查结论和运行方式；对评分事实仅排除明确允许变化的时间等字段。保留真实 ID、路径、提交和时间的差异，不直接比较整份 JSON。将这些未参与编写新判据的反例放入现有比较器验收，要求逐一拒绝；同一检查在本完整入口测试末尾运行。

### R5-F2 · [P2] 重新验收归一化未验证区间内容，会吞掉额外派发或缺失验收

位置：[own:243](/private/tmp/t194-cand5/workbench/tests/test_t194_mcp_entry_e2e.py:243)，尤其 [区间删除:247](/private/tmp/t194-cand5/workbench/tests/test_t194_mcp_entry_e2e.py:247)。

候选限制了 `integration_compare_failed` 起点只能出现一次，但只要后面找到 `review_reused`，就删除两个标记及其中任意内容，没有核对区间是否确为契约允许的重新验收链。

在同一真实绿色基线上独立复现两种误放：

- 把一个重复 `dispatched` 插入这两个标记之间，比较器返回 `true`；同样的重复放在原派发位置则正确返回 `false`。
- 删除两个标记之间的所有记录，仅留下起止标记，比较器仍返回 `true`。

结果同样保存于 [predicate-audit-01.json](predicate-audit-01.json)。生产 [revalidateForIntegration:1976](/private/tmp/t194-cand5/workbench/src/gates/core.ts:1976) 会重新执行验收链，成功后才可能 [review_reused:2596](/private/tmp/t194-cand5/workbench/src/gates/core.ts:2596)；额外派发和空验收链均不能视为正常的分支前移差异。

最小修正：先验证该单一区间的允许类型、顺序、次数与成功结果，再将其从跨入口比较中归一化；异常记录或缺失验收应使判据失败。保留本轮“区间内重复派发”和“空区间”作为回归反例。只检查一次起点不足以证明区间符合契约。

## EVIDENCE

### 前轮发现逐项核对

| 项目 | 本轮判断 | 独立证据与范围 |
| --- | --- | --- |
| R4-F1，等待后结果下标错位 | **PASS：关闭** | 真实 `--slow-mcp` 会话完成两次 `+enchanted` 搜索，然后 select、MCP status、命令 status、角色申请。按 `waits + 1` 读取到了两份身份拒绝结果，角色确认及原生会话检查通过，没有原先的 JSON 解析崩溃。 |
| R4-F2，仍在连接时误判缺失 | **PASS：关闭本次复现分支** | 同一会话实际得到 `Some MCP servers are still connecting`，随后再次搜索并继续。缺失入口的 `bf16c21` 则搜索一次后在“主控没有 Enchanted 的 MCP 工具”断言失败，没有被等待放过。 |
| R4-F3，记录一致性判据接受不一致证据 | **部分关闭，整项 NO_GO** | 从候选原函数独立执行，评分 `3 → 1`、事件倒序、原位置重复 `dispatched` 三例全部拒绝，绿色原记录通过；本轮新反例仍被接受，见 R5-F1、R5-F2。 |

等待不是无条件重试：第一次先搜索；没有工具且最近结果不再报告连接中便拒绝；报告连接中时每次休眠 1 秒，最多搜索 30 次。原计划函数的 0、1、29、30 次边界检查见 [discovery-audit-01.json](discovery-audit-01.json)，30 次仍无工具会拒绝。该边界检查用合成 Messages 输入并记录休眠调用；不能将它写成实等 30 秒的真实 CLI 证据。上限计算的是搜索次数，注释中的“30 seconds”不是严格墙钟期限。

### 当前候选真实入口复跑

| 运行 | 结果 | 产物 |
| --- | --- | --- |
| 原样完整流程 | **INCOMPLETE** | [fullflow-01.json](fullflow-01.json)，前四项通过，随后交付等待失败。 |
| 候选自带 `--slow-mcp` | **INCOMPLETE；等待分支验证通过** | [slow-mcp-01.json](slow-mcp-01.json)，包含慢启动等待条件在内的前五项通过，随后交付等待失败。 |
| 真正缺失 MCP 的父提交 | **红态符合预期** | [parent-red-01.json](parent-red-01.json)，退出码 1，在目标入口缺失断言失败；保留脚本原始 `INCOMPLETE` 状态。 |

普通与慢启动运行的两任务均停在 `claimed`，worker 的真实 PTY 均有 `sandbox-exec: sandbox_apply: Operation not permitted`。未降低沙箱、代 worker 提交、修改权限或跳过门禁。启动调用序列、worker 错误路径、数据库状态和后台停止后 socket/PID 文件检查见 [runtime-readback-01.json](runtime-readback-01.json)。这与入口等待或记录比较器缺陷是不同停点。

精确命令、起止时间与退出码分别保存在 [fullflow-execution.json](fullflow-execution.json)、[slow-mcp-execution.json](slow-mcp-execution.json)、[parent-red-execution.json](parent-red-execution.json)。本轮使用 Node `v26.5.0`、Claude Code `2.1.311`，模型端是本地脚本化 Messages 服务。

可使用新 summary 名称复现，避免覆盖现有失败证据：

```sh
cd /private/tmp/t194-review5
python3 -B run_candidate_test.py test_t194_mcp_entry_e2e.py --summary /private/tmp/t194-review5/fullflow-replay.json
python3 -B run_candidate_test.py test_t194_mcp_entry_e2e.py --slow-mcp --summary /private/tmp/t194-review5/slow-mcp-replay.json
python3 -B run_candidate_test.py test_t194_mcp_entry_e2e.py --revision bf16c21 --summary /private/tmp/t194-review5/parent-red-replay.json
```

比较器与等待边界探针分别为 [audit_predicates.py](audit_predicates.py)、[audit_discovery.py](audit_discovery.py)。它们从冻结候选 AST 提取原函数，不改候选，也不将故意不一致的数据写回数据库；输出存在即拒绝覆盖。所有本轮新增产物均在 review5。

### 历史绿色及 Acceptance 的边界

已只读核对简报列出的五份历史证据，摘要见 [historical-summaries-01.json](historical-summaries-01.json)：普通绿色 9 项、慢启动绿色 10 项通过；后者报告等待 1 次；父提交及两个身份变异各在所述目标断言失败。本轮没有把脚本原有的红态状态改成 PASS。

对慢启动绿色夹具 `/private/tmp/t194-xgm7l250` 的数据库直接回读，两任务均为 `accepted`，verification 和 review 均为 `passed`，审查结论均为 `可合并`，完成命令退出码均为 0，见 [historical-readback-01.json](historical-readback-01.json)。该源码副本的 114 个生产文件，在仅移除明确的 6 秒启动延迟后，与冻结候选对应文件逐字节一致，见 [historical-source-comparison-01.json](historical-source-comparison-01.json)；未计算哈希。历史摘要 `revision` 为空、配置 `code_revision` 为 `fixture`，因此仍将运行时间与源码比对证据分开陈述。

| T-194 Acceptance | 判断 |
| --- | --- |
| 四家 CLI 的 MCP 支持实测记录 | **PASS（已有记录的版本与范围）**。候选 [四家记录](/private/tmp/t194-cand5/findings/2026-10-27-mcp-per-session.zh-CN.md) 存在，生产与第 4 轮无差异；沿用 [第 4 轮独立核对](/private/tmp/t194-review4/REPORT.md) 的限定结论，本轮没有重调其余三家供应商模型。 |
| 至少一家经 MCP 完成全流程 | **历史正向证据成立；本轮复跑 INCOMPLETE**。历史真实落库与对应生产源码已回查；本轮受 worker 沙箱限制，未完成交付之后的流程。 |
| 两入口门禁记录一致 | **验收测试 NO_GO**。新判据对正常基线及前三个反例表现正确，但仍误放关键结果差异和异常重新验收区间，未达到完整声明。 |

本轮没有发现所测正常差异被误拒：真实两任务基线通过，事件顶层的序号、时间、attempt 差异通过，评分经过时间差异通过；重新验收的实际额外链也按现规则归一化。这些正例不构成对所有正常并发时序的穷举证明。

## LIMITATIONS

- **NO_GO 针对验收判据，不能据此推断生产门禁错误。** 新反例只修改内存证据，证明当前检查的能力边界；本轮未构造生产门禁绕过。
- 当前完整复跑未进入审查、集成和最终记录比较，不能将前四／五项绿色称为全流程 PASS。历史绿色是独立保留的支持，不能替代本轮完整重验。
- 真实 CLI、MCP、socket、SQLite 证明本地入口与权限编排；脚本化 worker 和审查员不证明真实模型的理解、工程判断、审查质量或生产可靠性。
- 本轮覆盖状态编排、异步工具发现、终端身份、CLI 交互和本地交付记录；检索／记忆、媒体生成、生产外部写入为 N/A。未重跑生产无变更的生命周期套件，沿用第 4 轮六项复跑证据；未实等全部 30 次搜索，也未穷举协议与并发分支。
- 候选开始、结束的 HEAD 和 Git 状态检查见 [candidate-start.json](candidate-start.json)、[candidate-final.json](candidate-final.json)；既有未跟踪项 `workbench/node_modules` 保留。没有修改候选、提交、ticket 或历史文件。

下一步是在原测试中补齐结果语义比较与重新验收区间校验，保留这些失败证据，并在允许原 worker 沙箱路径的环境取得完整复跑。此报告只交付审查结论，不代为实施修复。
