# T-194 独立只读审查（第 4 轮）

## STATUS

**NO_GO（本轮测试修复）**。新增等待分支存在已复现的结果索引错位，且一次 ToolSearch 不能保证服务器已经连接；因此不能接受“启动竞态已消除”的结论。没有发现本轮新增生产代码缺陷。完整流程的本轮原样复跑为 **INCOMPLETE**：前四项通过，随后 worker 被沙箱阻断。整票三项 Acceptance 尚不能全部判为 PASS。

TARGET：`/private/tmp/t194-cand4`，`d1989e91161a908f0d051f241f86678f66649a09`。本轮新增提交仅修改 `workbench/tests/test_t194_mcp_entry_e2e.py`，7 行新增、1 行删除，原八项断言未改。已核对上一轮 `0586985` 与重基后的 `c511bd9`：T-194 的 `terminalMcp.ts`、`terminalCli.ts`、`transport.ts`、终端包装脚本、hooks、roles 无差异；T-195 的 `nativeLink.ts` 差异不在范围。

开始与结束 HEAD、Git 状态一致，唯一未跟踪项均为既有 `workbench/node_modules`。未修改候选、未提交，所有新增产物在 review4。依据为只读读取的 T-194 三项 Acceptance、T-189 第 3 条及现有终端角色契约。

沿用 **Ubiquitous language**：终端身份负责权限，原生会话号是调用方报告的数据。**Tracer bullet** 使用真实 CLI、MCP 子进程、socket 和后台状态验证入口。按 **Deep modules** 检查，MCP 和命令仍共用后台门禁，没有新增平行业务实现。

## FINDINGS

### R4-F1 · [P1] 新增等待成功后，固定索引使验收脚本崩溃

位置：[test_t194_mcp_entry_e2e.py:92](/private/tmp/t194-cand4/workbench/tests/test_t194_mcp_entry_e2e.py:92)、[状态结果读取:182](/private/tmp/t194-cand4/workbench/tests/test_t194_mcp_entry_e2e.py:182)、[角色结果读取:191](/private/tmp/t194-cand4/workbench/tests/test_t194_mcp_entry_e2e.py:191)。

`waited=True` 时实际调用为：额外 ToolSearch → 原 select ToolSearch → MCP status → 命令 status → request_role。新增第一个结果后，`results()[1:3]` 取到的是 select 搜索结果与 MCP status，而不是两次 status；角色结果的固定下标也随之错位。

[waited-discovery-01.json](waited-discovery-01.json) 已通过真实 Claude Code 复现：工具发现成功，两次 status 实际均拒绝无角色调用，角色申请也已发出；但 `without_role[0].text` 是工具搜索返回的空白，正则提取 JSON 时抛出 `AttributeError: 'NoneType' object has no attribute 'group'`，只完成第一项检查。这不是 worker 沙箱问题，尚未进入派发。

探针只在 review4 的源码副本中将 MCP 启动延迟 6 秒，并将第一次模型响应延迟 7 秒，让“初次模型请求看不到工具，实际执行 ToolSearch 时服务器已经就绪”稳定发生；原候选测试、八项断言及真实 CLI 工具结果未修改。脚本为 [run_waited_discovery.py](run_waited_discovery.py)。

最小修正：记录实际增加的发现步骤，并统一调整后续状态、角色及错误检查的结果偏移，保留原业务判据。修后必须重跑这个确实执行额外搜索的分支；已有绿色记录不能替代它。

### R4-F2 · [P2] ToolSearch 返回“仍在连接”时，脚本仍误判入口缺失

位置：[test_t194_mcp_entry_e2e.py:83](/private/tmp/t194-cand4/workbench/tests/test_t194_mcp_entry_e2e.py:83)。

`waited` 只表示会话文本中已出现搜索参数，不代表连接完成。[delayed-start-01.json](delayed-start-01.json) 中，真实 ToolSearch 明确返回：`Some MCP servers are still connecting: plugin:enchanted-a2a:enchanted`；下一次模型请求仍没有工具，脚本立即触发第 86 行的入口缺失断言。没有必要把服务永久缺失才能触发这个失败。

[run_delayed_start.py](run_delayed_start.py) 仅在隔离源码副本的 MCP 启动前加入 6 秒延迟，不修改模型或断言，退出码为 1。原始会话与提取结果见 [runtime-readback-01.json](runtime-readback-01.json)。这证明“一次 ToolSearch 等服务器连上”的前提在当前 Claude Code `2.1.311` 下不总成立；没有据此推断所有版本的行为。

最小修正：在测试启动阶段区分仍在连接、连接失败与已就绪但没有目标工具，使用有界就绪等待；不能把出现过查询字符串当作就绪信号。服务器仍缺失或超过明确期限必须继续失败。防回归应放在现有完整入口测试，覆盖慢启动与真正缺失两种结果；本轮没有绕过这个失败。

### R4-F3 · [P2，既有验收缺口] 记录一致性断言会接受不一致的证据

位置：[test_t194_mcp_entry_e2e.py:250](/private/tmp/t194-cand4/workbench/tests/test_t194_mcp_entry_e2e.py:250)、[事件投影:231](/private/tmp/t194-cand4/workbench/tests/test_t194_mcp_entry_e2e.py:231)。本轮未改这些断言，不归因于新增等待代码。

- `same_score_record` 从评分记录顶层取 `result`、`boundary_discipline` 等六字段，实际这些值在 `data` 内。两端顶层投影均为六个 null。只把命令入口的 `data.boundary_discipline` 从 3 改为 1，该断言仍为 true。
- `same_gate_events` 只保留选定事件的首次出现，再按固定 `own` 元组重新排序，主要比较字段名；反转命令入口全部事件，或增加一个重复 `dispatched`，断言仍为 true。上一轮报告已限制过它的证明范围，本轮用反例确认此限制。

[acceptance-predicate-audit-01.json](acceptance-predicate-audit-01.json) 保存三个反例。探针从当前候选 AST 直接执行原判据，输入来自绿色运行的只读数据库；只修改内存中的证据，不改候选或历史文件。预期拒绝来自第三项 Acceptance 的记录一致性要求，实际三个反例均被接受。这是验收判据缺口，不是已观察到生产记录被改错。

最小修正：比较非空的 `data` 评分字段；从实际事件顺序比较所声明的记录，并核对重复次数与必要语义值。任务、attempt、时间等天然不同字段以及第二次集成因分支前移产生的重新验收，应按明确契约归一化。目标测试须拒绝上述不一致反例，不能只维持绿色基线。

## EVIDENCE

### 本轮执行与反事实

| 检查 | 结果、原始产物与边界 |
| --- | --- |
| 冻结候选原样完整流程 | [candidate-fullflow-01.json](candidate-fullflow-01.json)：前四项 PASS，随后 `超时：T-1 交付`；测试退出码 1。两任务最终均为 `claimed`。两个 worker 的真实 PTY 均记录 `sandbox-exec: sandbox_apply: Operation not permitted`；没有修改沙箱、替 worker 提交或跳过门禁。 |
| 当前生命周期测试 | [candidate-lifecycle-01.json](candidate-lifecycle-01.json)：六项 PASS、退出码 0、测试 stderr 为空；EOF 撤回、安静结束、输出关闭、取消、正常批准、发送前中止均通过。 |
| 真正缺少入口的父提交 | [candidate-parent-red-01.json](candidate-parent-red-01.json)：对 `bf16c21` 使用当前测试，真实会话先调用 `ToolSearch(query="+enchanted")`，仍无 Enchanted 工具后在入口缺失断言失败，退出码 1。未放过真正缺失的入口；失败位于目标业务入口，不是环境初始化失败。 |
| 慢启动反例 | [delayed-start-01.json](delayed-start-01.json)：仍在连接却被判缺失；退出码 1，见 R4-F2。 |
| 等待后成功发现工具的反例 | [waited-discovery-01.json](waited-discovery-01.json)：入口已可用，但索引错位导致解析崩溃；退出码 1，见 R4-F1。 |
| 验收判据反例 | [acceptance-predicate-audit-01.json](acceptance-predicate-audit-01.json)：评分值改变、事件逆序、重复派发事件均未被对应断言拒绝。原绿色输入仍满足判据。 |

各运行的精确命令、起止时间和退出码保存在 [fullflow-execution.json](fullflow-execution.json)、[lifecycle-execution.json](lifecycle-execution.json)、[parent-red-execution.json](parent-red-execution.json)、[delayed-start-execution.json](delayed-start-execution.json)、[waited-discovery-execution.json](waited-discovery-execution.json)。运行版本：Node `v26.5.0`、Claude Code `2.1.311`。模型均为本地脚本化 Messages 服务，不调用供应商模型。

可在 review4 以新文件名复现，避免覆盖失败证据：

```sh
python3 -B run_candidate_test.py test_t194_mcp_entry_e2e.py --summary /private/tmp/t194-review4/fullflow-replay.json
python3 -B run_candidate_test.py test_t194_mcp_lifecycle_e2e.py --summary /private/tmp/t194-review4/lifecycle-replay.json
python3 -B run_candidate_test.py test_t194_mcp_entry_e2e.py --revision bf16c21 --summary /private/tmp/t194-review4/parent-red-replay.json
python3 -B run_delayed_start.py --summary /private/tmp/t194-review4/delayed-start-replay.json
python3 -B run_waited_discovery.py --summary /private/tmp/t194-review4/waited-discovery-replay.json
```

### 三项 Acceptance 的逐项判断

| Acceptance | 判断 | 依据及剩余缺口 |
| --- | --- | --- |
| 四家 CLI 的 MCP 支持实测记录 | **PASS（所记录版本与范围）** | 候选 [四家实测记录](/private/tmp/t194-cand4/findings/2026-10-27-mcp-per-session.zh-CN.md)；只读核对主仓库 `real-05-cand3.json` 的真实 Codex／opencode 六项 PASS，以及 agy 交互探针的 `NO_TOOL`、服务器 initialize/tools/list 和 print 模式回显。加上本轮 Claude 的真实入口，支持三家挂载、agy 继续命令入口的限定结论，不要求四家均成功。 |
| 至少一家经 MCP 完成申请、建卡、派发、交付、审查、集成 | **历史正向证据成立；本轮复跑 INCOMPLETE** | `green-10-v3test.json` 原八项 PASS；进一步只读回查其真实夹具数据库，两任务为 `accepted`、verification 为 `passed`、review 为 `passed`，见 [historical-boundary-readback-01.json](historical-boundary-readback-01.json)。这是实际落库的成功流程，不能因本轮沙箱失败而抹掉。但该绿色会话没有执行新增 `+enchanted` 等待分支，本轮也未取得冻结候选的完整绿色复跑。 |
| 同一操作经 MCP 与命令的门禁记录一致 | **INCOMPLETE（当前声明范围）** | 静态路径仍共用 `requestAt` 与后台同一 `gates.call`；绿色记录的所选字段集合、launch overrides、归属相同，独立回查两份实际 `data` 评分也确实相等。上述是正向支持；但现有判据不能证明声明的事件顺序、次数和必要值一致，R4-F3 的反例未被拒绝。不能把八项 PASS 外推成完整记录一致性保证。 |

`green-10-v3test.json`、`lifecycle-green-06.json`、`real-05-cand3.json` 的 `revision` 均为空。绿色全流程夹具配置的源码路径是 `/private/tmp/t194-dev2`，`code_revision` 为 `fixture`；本轮按简报的同生产源码说明结合 Git 对 T-194 路径的版本复核使用它们，没有把这些元数据写成已独立锁定 `d1989e9` 的运行证明。历史八项绿色与本轮四项绿色都未进入新增等待成功分支，见真实会话调用序列 [historical-entry-tools-01.json](historical-entry-tools-01.json) 和 [runtime-readback-01.json](runtime-readback-01.json)。

### 收尾

[candidate-start.json](candidate-start.json)、[candidate-final.json](candidate-final.json) 保存候选状态及只读项目地图检查；主仓库 status 始末均为 Problems 0、Stale living docs 0，候选 `git diff --check bf16c21 HEAD` 通过。开始时宽范围跨版本比较包含了范围外的 T-195 `nativeLink.ts` 差异，后用上列 T-194 明确路径复核，差异为空；未丢弃最初输出。

本轮五个隔离夹具的后台均已停止，control socket 与 daemon.pid 均不存在。所有 JSON 维持被测脚本的原始状态值，未将失败文件改成 PASS。

## LIMITATIONS

- **NO_GO 针对测试修复的可复现缺陷，不是已确认的生产门禁回归。** 完整流程未完成的环境原因、慢启动误判、发现后的索引错误是三个不同停点，不能互相替代。
- 两个启动探针使用真实 Claude Code、真实 MCP 与后台，只注入时序；其源码副本不是冻结候选的原样运行，不能作为冻结候选全流程绿色证据。原样运行另行保留。
- 本轮未重新调用真实 Codex、opencode、agy 供应商模型；四家结论依赖明确版本的已有实测记录。本地脚本化模型证明工具发现、传输、权限与门禁联通，不证明自然语言理解、独立工程判断或生产可靠性。
- Agent 产品边界覆盖状态编排、异步传输、终端权限、CLI 交互与本地交付记录；尚缺本轮成功交付后的完整重验。检索／记忆、媒体生成与生产外部写入为 N/A，本票不涉及。
- 本轮没有实等 600／660 秒，也未穷举全部工具、并发、重复请求或所有协议分支；沿用上一轮生命周期结论的范围，并以当前六项复跑补充，未扩大承诺。
- 报告和探针是本轮交付；候选、ticket、历史证据均未修订。后续最小动作是修复等待分支与结果关联，保持真正缺失入口的红态，并在允许原 worker 提交路径的环境取得完整绿色；第三项 Acceptance 还需补足能拒绝记录不一致的判据。
