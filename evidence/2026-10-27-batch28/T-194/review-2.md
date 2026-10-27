# T-194 独立只读审查（第 2 轮）

## STATUS

**NO_GO**。第 1 轮 F1 的权限生命周期缺陷已修复，本轮真实入口验证为 **PASS**；但确认 1 项 P2：EOF 中止后的回包仍写入 stdout，客户端已关闭读取端时触发未处理的 `EPIPE`，服务器以退出码 1 崩溃。该场景中申请已撤回，没有重新激活角色。完整交付链本轮因执行环境的沙箱限制为 **INCOMPLETE**。

TARGET：`/private/tmp/t194-cand2`，`a6c65f77512b93de84d5e51480a40495c5fd7ec9`。仅审相对 `87c30f0` 的 T-194 差异，重点复核 `494d859 → a6c65f7` 的四文件修复；不审父提交本身。开始和结束时 HEAD、Git 状态一致，唯一未跟踪项均为既有 `workbench/node_modules`。未修改候选、未提交；产物均在本审查目录，主仓库仅作只读参考。

验收依据：T-194 三项 Acceptance、T-189 第 3 条、既有“调用方停止等待即撤回角色申请”的契约，以及 [MCP 2025-06-18 stdio 关闭顺序](https://modelcontextprotocol.io/specification/2025-06-18/basic/lifecycle#stdio)。后者要求客户端先关闭服务器输入，再等待退出。官方 SDK 的[关闭说明](https://ts.sdk.modelcontextprotocol.io/v2/serving/stdio#shut-down-cleanly)也明确描述 EOF 中止在途请求，关闭后不再回答。

沿用 **Ubiquitous language**：终端身份负责权限，原生会话号是调用方报告的数据。用真实后台、终端与 MCP 子进程的 **Tracer bullet** 检查关闭边界；按 **Deep modules** 检查门禁与撤回规则是否仍由原有后台承担。

## FINDINGS

### F2 · P2 · EOF 后仍写入中止回包，stdout 读取端关闭时发生未处理的 EPIPE

位置：[terminalMcp.ts:80](/private/tmp/t194-cand2/workbench/src/terminalMcp.ts:80)、[terminalMcp.ts:113](/private/tmp/t194-cand2/workbench/src/terminalMcp.ts:113)；关闭处理在 [terminalMcp.ts:91](/private/tmp/t194-cand2/workbench/src/terminalMcp.ts:91)。

`input.close` 中止了在途调用，但异步回调随即进入 `catch`，仍通过 `write` 向 stdout 发 `outcome_unknown`。代码没有记录传输已关闭，也没有处理 stdout 的异步 `error` 事件。`try/catch` 只能覆盖同步抛出，不能接住这里由流发出的未处理事件。

独立复现使用冻结候选的真实后台、真实项目终端凭据和真实 `node terminalCli.ts mcp codex` 进程，完成标准初始化后：

1. 调用 `request_role(executor)`，从后台确认申请为 `pending`。
2. 客户端先关闭子进程 stdin，随后立即关闭其 stdout 读取端，等待服务器退出。没有发送逐项取消通知或进程信号。
3. 后台申请进入 `ended/asker_gone`，迟到批准返回 `request_not_pending`，终端角色仍为空。
4. 子进程 stderr 出现 `Unhandled 'error' event`、`Error: write EPIPE`；栈指向 `terminalMcp.ts:80` 与 `:113`，退出码为 **1**。

主证据：[probe-v2-lifecycle-02.json](probe-v2-lifecycle-02.json)，`cases.eof_closed_stdout`；独立分次导出的 [stderr](lifecycle-02-eof_closed_stdout.stderr.txt)。第 1 次探针以先关 stdout 再关 stdin 的顺序也得到相同结果，保留于 [probe-v2-lifecycle-01.json](probe-v2-lifecycle-01.json)。第 2 次使用输入先关闭的顺序，排除了关闭顺序解释。

客户端保留 stdout 读取端时，申请同样撤回，服务器退出码为 0，但仍发出关闭后的错误回包；见同一 JSON 的 `eof_readable_stdout`。因此这不是后台撤回失败，而是 MCP 传输关闭没有覆盖结果写回。

影响：客户端结束会话时服务器发生可复现的未处理异常，留下崩溃日志和非零退出码。**本轮没有观察到该异常导致角色重新生效、后台 run 被回滚或重复执行**，故不沿用 F1 的 P1 级别。

最小修正方向：由 `serveMcp` 的传输生命周期记录关闭状态，关闭时统一中止调用，并停止向已关闭会话写成功或错误回包；对 stdout 断开引起的流错误做明确的传输终止处理。继续复用现有后台撤回，不加角色状态机、重试或备用 API，也不泛化为吞掉所有错误。

负责层：`terminalMcp.ts`。复验时点：下一次候选验收前。可执行防回归检查应放入现有 `test_t194_mcp_lifecycle_e2e.py`：真实进程、待批申请、stdin EOF 后关闭 stdout 读取端，断言申请撤回、迟到批准拒绝、角色为空，同时没有未处理异常且正常退出。该用例会在本候选上失败。现有测试 [第 91 行](/private/tmp/t194-cand2/workbench/tests/test_t194_mcp_lifecycle_e2e.py:91)只关闭 stdin，收集退出码但未断言，也没有读取 stderr，因而四项绿色不能证明此边界。

### 第 1 轮 F1 · 本轮关闭：PASS

修复落在正确的根因层：

- `terminalMcp.ts:91` 在 readline 关闭时 abort 当前调用；`transport.ts:31` 销毁对应后台 socket；`daemon.ts:280` 的原有 `asker.gone` 将待批申请撤回。协议层没有复制角色状态机。
- [transport.ts:29](/private/tmp/t194-cand2/workbench/src/transport.ts:29)在创建连接前拒绝已中止信号，覆盖确认调用开始时调用方已经停止的情况；正常申请和确认仍共用同一个 signal。
- 独立探针两次均确认 EOF 后 `ended_reason=asker_gone`、`confirmed_at=null`、迟到批准失败、终端无角色；通知取消、正常拒绝、正常批准及确认均通过。已确认角色在 MCP 会话 EOF 后仍保留，符合身份绑定终端、后台工作继续的边界。

“批准已返回、确认尚未发出”的精确调度窗口没有通过真实后台确定性卡住；本轮依据代码调用链、已中止信号的真实 socket 检查及去掉该检查的反事实支持这一部分，不把它描述成完整竞态穷举。

## EVIDENCE

### 本轮执行与独立证据

全部命令、进程退出码和业务状态见 [execution-index.json](execution-index.json)。Node 为 `v26.5.0`；模型相关运行均使用隔离 HOME 和本地脚本化 Messages 服务，无供应商模型调用。业务结果来自后台状态、真实 socket、进程退出和原始 stderr，不依据模型自报完成。

| 检查 | 结果与边界 |
| --- | --- |
| 独立生命周期与权限伪造 | [probe-v2-lifecycle-02.json](probe-v2-lifecycle-02.json)：取消、拒绝、正常批准、会话 sentinel `review2-sentinel-4`、EOF 撤回均 **PASS**；未持角色时伪造参数中的 `command` 与 operator `identity` 仍返回 `approved_role_required`。关闭 stdout 的退出处理为 **NO_GO**，见 F2。 |
| 候选新增回归 | [candidate-lifecycle-01.json](candidate-lifecycle-01.json)：四项 **PASS**，进程退出码 0、测试 stderr 为空。第 4 项为调用 `requestAt` 的窄范围 socket 检查，前三项走真实后台、终端与 MCP 入口。 |
| 旧版本反事实 | [candidate-lifecycle-red-01.json](candidate-lifecycle-red-01.json)：`494d859` 在“关闭输入后申请撤回”检查超时，进程退出码 1。JSON 状态是 **INCOMPLETE**，不能改称整个场景成功；其具体失败证明旧行为未满足撤回断言。 |
| 保留在途调用的坏变体 | [candidate-lifecycle-mutant-close-01.json](candidate-lifecycle-mutant-close-01.json)：去掉 close 时 abort 后，同一撤回检查超时，进程退出码 1。发生在业务断言，而非缺依赖或程序无法启动。 |
| 已中止仍发送的坏变体 | [candidate-lifecycle-mutant-aborted-01.json](candidate-lifecycle-mutant-aborted-01.json)：前三项通过，第 4 项观察到 1 次连接并失败，进程退出码 1；真实 socket 边界拒绝了该坏实现。 |
| 后台断开、不重放 | [probe-boundaries-v2-01.json](probe-boundaries-v2-01.json)：故障对端接收请求后断开，真实 MCP 返回 `outcome_unknown`，观察期只收到一次请求，**PASS（传输故障注入范围）**。不据此判断业务写入是否发生。 |
| 包装脚本参数与环境 | 同一边界报告：Codex 用户显式 `-c ...tool_timeout_sec=23` 位于注入的 660 之后；未注入或改写 `developer_instructions`；opencode 默认 MCP 配置、用户配置透传、显式 `--standalone` 透传均 **PASS**。对端是只回显 argv/指定环境的本地 stub，未重测真实 CLI 配置解析。 |
| 正常等待的 run | [probe-v2-run-wait-01.json](probe-v2-run-wait-01.json) 的 `WaitLive`：真实后台、真实 Claude worker，脚本化模型保持未交付；MCP 等待约 12.77 秒后返回 `run_deadline`，后台 run 为 `outcome=deadline`，进程正常退出，**PASS（有界等待与超时路径）**。 |
| EOF 后后台 run 独立推进 | 同一报告的 `WaitEOF`：真实后台 run 已保存后关闭 MCP stdin，子进程以 0 退出；此时数据库 run 仍为 `running`，约 12.66 秒后按自己的期限进入 `deadline`。每个任务只存在一个 run，终端角色仍为 executor，**PASS（有界断开与超时路径）**。该检查不等同于交付成功或实等 660 秒。 |
| 冻结候选全流程重跑 | [candidate-fullflow-01.json](candidate-fullflow-01.json)：前四项（真实 Claude 工具表、两入口无角色拒绝、申请生效、原生会话号独立核对）通过；worker 提交调用报 `sandbox-exec: sandbox_apply: Operation not permitted`，之后等待交付超时。整次 **INCOMPLETE**、进程退出码 1，未进入后续审查与集成，未调整沙箱绕过。 |
| 完整 run 交付探索 | [probe-v2-run-01.json](probe-v2-run-01.json)：同一沙箱错误阻断提交，**INCOMPLETE**、进程退出码 1；其 EOF 子场景尚未执行。之后的独立有界检查只证明上面明确列出的等待与断开行为。 |

### 新测试的判据与反事实审查

前三项的期望来自角色契约：停止等待撤回、正常取消撤回、用户批准后经确认生效；第 4 项来自同一契约在传输上的必要条件：已停止的确认调用不能再发送。预期没有从生产输出或生产常量生成；夹具只负责创建后台、终端及凭据。申请 id、后台角色状态和 socket 连接都是从外部观察，独立探针另使用了新的会话 sentinel。

本轮重跑旧版本与两种坏变体均在目标检查失败。既有 `lifecycle-mutant-aborted-still-sent.json` 的最初三项结果确为 **PASS**，说明旧测试漏掉发送前中止；后续增加第 4 项，`lifecycle-mutant-aborted-still-sent-02.json` 才因实收连接失败。两次证据均保留，不能只引用后一次而隐去原先的存活变体。

第 4 项以 socket 对端隔离 `requestAt` 有明确理由：真实批准／确认之间的窗口过窄，不能靠随机调度稳定命中。它证明发送前检查，不能代替整个批准竞态、真实 CLI 超时和全部 run 路径的端到端验收。

### 第 1 轮其余 PASS 项的 v2 复核

`494d859 → a6c65f7` 只有 MCP EOF abort、`requestAt` 的发送前中止检查、README 一句与生命周期测试；工具表、包装脚本、会话号来源、门禁和后台 run 代码均未改动。

- **同一门禁、无平行路径：PASS（静态所审路径）。** `terminalMcp.ts:86` 将工具参数映射到原有 `send`；`terminalCli.ts:114` 固定终端信封凭据；后台仍核对角色与项目后进入 `gates.call`。本轮伪造参数检查补足了真实入口证据。
- **异常不伪装成功、不重放：PASS（已测取消／后台断开）。** 新修复未新增吞异常、重试、备用调用或平行 API。现有 `catch` 将未知结果保留为 `outcome_unknown`；关闭后继续写回属于 F2。非法 JSON 静默忽略是已有行为，本轮不据此给完整 JSON-RPC 合规结论。
- **CLI 挂载与原生会话号：保留第 1 轮限定结论。** 本轮真实 Claude 前四项再次通过，Codex/opencode 包装参数再测通过。四家实测记录、真实 Codex/opencode 申请／拒绝、agy 交互模式 `NO_TOOL` 的既有材料仍支持原来的兼容取舍；没有重跑真实 Codex、opencode、agy 或真实供应商模型，不宣称新版本普遍兼容。会话号仍不是认证信息。
- **全流程与两入口记录：既有证据保留，本轮未完成重验。** 只读仓库 `evidence/2026-10-27-batch28/T-194/green-08.json` 的八项为 PASS，测试观察集成文件、后台确认、worker 归属和评分，强于模型自报。但 `revision=null`，不能单凭文件名绑定本冻结候选。本轮因沙箱限制未完成后半程。`same_gate_events` 仍只比较选定事件的首次出现与字段集合，以及部分卡片、启动参数、评分值，不能扩大成全部原始事件顺序、次数和字段值完全相同。
- **文档与配置边界：PASS（静态核对）。** README 新句符合已测 EOF 撤回行为；Codex 工具批准模式不替代 Enchanted 角色批准。用户显式 `-c` 的优先级不能扩大成所有配置文件同名字段都优先。新增生产路径未见写用户全局配置；本轮也未写入用户配置。

复现 F2（使用新文件名，避免覆盖）：

```sh
cd /private/tmp/t194-review2
python3 -B probe_v2_lifecycle.py --summary /private/tmp/t194-review2/probe-v2-lifecycle-replay.json
```

该探针的退出码 0 表示采证完成；业务判定在 JSON 中为 `NO_GO`，被测 MCP 子进程退出码为 1。其他运行的精确命令与退出码见 `execution-index.json`；`run_candidate_test.py` 仅把临时目录限制在本报告目录，坏变体在独立源码副本中执行，不修改冻结候选。

## LIMITATIONS

- 尚未修复 F2；本次授权为只读审查。下一轮应修复关闭后的结果写回，再通过真实进程回归，不以增加泛化兜底或只检查角色为空代替退出质量检查。
- 没有实等 120／600／660／720 秒边界，没有穷举批准／确认调度、撤权竞态、并发请求、全部工具或完整 MCP 协议。12 秒 run 检查只覆盖正常等待、EOF 后继续推进与自身超时，不证明长时交付成功。
- 本轮完整交付链与成功 run 的重跑均受当前执行环境限制。保存了错误、超时结果和现场，没有关闭沙箱或将其转成 PASS；既有绿色报告不能替代当前候选的完整复验。
- 两次生命周期探针最初共用了 stderr/stdout 辅助文件名；各次完整回包与 stderr 始终独立保存在 `probe-v2-lifecycle-01.json`、`-02.json`。已按各次 JSON 分别导出 `lifecycle-01-*`、`lifecycle-02-*`，并保留实际执行脚本 `probe_v2_lifecycle.executed-01.py`、`executed-02.py`；当前复现脚本已按 summary 名区分辅助文件。结论以分次 JSON 为主证据。
- 所有检查使用隔离数据；后台均经夹具停止，收尾时所核对夹具的 control socket 与 daemon.pid 均已不存在。没有用全局进程扫描作退出证明。
- `git diff --check 87c30f0 HEAD` 退出码 0；项目地图只读 status 开始和结束均为 Problems 0、Stale living docs 0。这些是静态与治理检查，不替代行为验收。
