# T-194 独立只读审查（第 1 轮）

## STATUS

**NO_GO**。确认 1 项 P1：MCP 客户端按 stdio 关闭流程结束输入后，待批申请没有撤回；用户此后批准时，服务器仍会确认角色，然后退出，留下已生效的执行主控身份。

TARGET：`/private/tmp/t194-cand`，`494d859067a0d39c31007ddc1ba5e2edacb28a95`；仅审相对 `87c30f0` 的 T-194 差异。开始与结束时 HEAD 一致，候选唯一未跟踪项均为既有 `workbench/node_modules` 链接。未改候选、未提交、未改项目地图或用户配置。

验收依据为 T-194 的三项 Acceptance、T-189 第 3 条，以及终端角色申请“调用方停止等待即撤回”的既有契约。沿用 Ubiquitous language：**终端身份**是权限边界，**原生会话号**是 CLI 报告的数据，两者不能混同。既有全流程是 Tracer bullet 证据；本轮另走真实后台和公开 MCP 入口检查停止边界。按 Deep modules 检查业务规则归属，没有要求协议适配层另建门禁。

## FINDINGS

### F1 · P1 · MCP 输入 EOF 没有终止在途角色申请，关闭后仍可激活角色

位置：[terminalMcp.ts:88](/private/tmp/t194-cand/workbench/src/terminalMcp.ts:88)、[terminalCli.ts:143](/private/tmp/t194-cand/workbench/src/terminalCli.ts:143)。后续确认发生于 [terminalCli.ts:126](/private/tmp/t194-cand/workbench/src/terminalCli.ts:126)。

`serveMcp` 只在 `notifications/cancelled` 时 abort 对应请求，没有在输入流 EOF／readline 关闭时 abort 在途请求。`main` 收到 `end` 只设置返回码，仍打开的后台 socket 继续维持进程，并继续执行申请后的确认步骤。

这是真实关闭路径：MCP stdio 客户端先关闭服务器输入，再等待退出，必要时才发信号；并不要求先发送逐项取消通知。[MCP 2025-06-18 生命周期规范](https://modelcontextprotocol.io/specification/2025-06-18/basic/lifecycle#stdio) 明确列出这一顺序；[官方 TypeScript SDK 的 stdio 说明](https://ts.sdk.modelcontextprotocol.io/v2/serving/stdio#shut-down-cleanly) 也说明 EOF 会关闭连接并中止在途请求。

独立复现使用冻结候选的真实后台、真实项目终端凭据、真实 `node terminalCli.ts mcp codex` 子进程；无模型或供应商调用。完成 `initialize`／`notifications/initialized` 后：

1. 调用 `request_role(executor)`，后台出现 `pending`。
2. 关闭 MCP 子进程 stdin，保留 stdout 仅供采证；等 1 秒。
3. 后台记录仍为 `pending`。用隔离夹具的 operator 批准，返回 `ok: true`。
4. MCP 服务器自行发送 `role_request_confirm`；`terminal_whoami.role` 变成 `executor`，申请变成 `approved`，随后服务器以退出码 0 退出。

预期：EOF 应断开该申请的后台连接，使申请进入 `ended/asker_gone`，之后不能批准或确认；终端仍无角色。实际：关闭后的申请可生效，并占住角色。**没有复现“无需用户批准即可拿角色”**；缺陷在于已关闭请求仍能被批准并确认。

原始结果：[probe-lifecycle-02.json](probe-lifecycle-02.json)，字段 `cases.eof_then_approval`；对应 [stdout](probe-lifecycle-02.stdout.txt)、[stderr](probe-lifecycle-02.stderr.txt)。脚本退出码 0 表示探针完成，JSON 的业务判定是 `NO_GO`。

复现命令（使用新文件名，保留已有证据）：

```sh
python3 -B /private/tmp/t194-review1/probe_lifecycle.py --summary /private/tmp/t194-review1/probe-lifecycle-replay.json
```

最小修正方向：在 MCP 传输关闭时统一 abort 当前在途调用，关闭对应后台连接；关闭后的角色申请不得继续确认。继续复用后台现有撤回逻辑，不增加一套角色状态机，也不取消已经独立在后台推进的任务。回归检查应通过真实入口覆盖“待批 → stdin EOF → 撤回 → 迟到批准被拒”，并保留现有通知取消正例。

## EVIDENCE

### 本轮独立检查

| 检查 | 结果与依据 |
| --- | --- |
| 同一门禁入口、无复制业务逻辑 | **PASS（限定所审路径）**。普通工具在 `terminalMcp.ts:86` 仅覆盖 `command` 后调用 `send`；`terminalCli.ts:114` 固定终端凭据；后台 `daemon.ts:367` 核对角色、项目与命令范围，再于 `:396` 调用原门禁。`request_role` 与命令入口复用 `requestRole` 的申请／确认流程。没有发现平行门禁或业务兜底。 |
| 参数不能替换终端权限 | **PASS（探针范围）**。未获角色时，在 MCP `status` 参数里伪造 `command: role_request_confirm` 和 operator `identity`，仍返回 `approved_role_required`。工具参数中的 `command` 被映射覆盖，`identity` 没有覆盖请求信封的终端凭据。见 `probe-lifecycle-02.json` 的 `forged_arguments_without_role`。 |
| 会话号真实性与权限用途 | Claude 来自服务器环境，Codex 来自每次调用的 `_meta.threadId`；两者都是调用方可报告的数据，**不能视为认证信息**。探针的伪造 `sentinel-forged-thread-194` 确实进入申请记录，但没有因此获得角色。`roleRequests.ts:84` 仅做格式核对；实际授权仍依赖终端 token、UI 批准和确认。会话号还用于额度日志选择与钩子会话匹配，伪造可影响这些记录的准确性；本轮未发现它可扩大终端权限。 |
| 取消通知 | **PASS**。对真实后台申请发送 `notifications/cancelled`，MCP 返回 `outcome_unknown`，申请进入 `ended/asker_gone`，未确认。见 `probe-lifecycle-02.json` 的 `cancel_notification`。 |
| 传输关闭 | **NO_GO**，见 F1。正常取消通知通过不能替代 EOF 检查。 |
| 后台断开、不重放 | **PASS（传输故障注入）**。一个 Unix socket 对端收取请求后立即断开；真实 `a2a mcp codex` 返回 `outcome_unknown`。观察窗口内只收到一次请求，无重试。见 [probe-boundaries-02.json](probe-boundaries-02.json) 的 `daemon_disconnect`。该检查不证明后台是否已完成业务写入，正因此结果必须保持未知。 |
| 包装脚本 | **PASS（参数／环境边界）**。执行候选的真实包装脚本，接收端为仅打印 argv 和指定环境变量的本地 stub。Codex 用户显式 `-c ...tool_timeout_sec=23` 排在注入的 660 后；既有 `developer_instructions` 未被重写。opencode 默认注入独立服务器和 MCP 配置；用户已有 `OPENCODE_CONFIG_CONTENT` 或显式 `--standalone` 时原样透传，不注入 MCP，继续可用命令入口。见 `probe-boundaries-02.json`。 |

Codex 的取舍在代码和 README 中均有明示：`default_tools_approval_mode="approve"` 取消的是这一服务器的 CLI 工具批准框；Enchanted 的角色批准和后台门禁仍保留。`tool_timeout_sec=660` 给最多 600 秒的角色申请留出余量；对于可能超过 660 秒的 `run`，工具超时不意味着后台任务回滚，应查 `status`，不重放。`requestAt` 对角色申请的 socket 期限为 720 秒，但后台角色等待本身仍限 600 秒。本轮没有实等这些长时限，也没有重测真实 Codex 的配置解析。

“用户配置优先”需保持准确范围：Codex 用户显式 `-c` 位于注入参数之后；其配置文件里同名 `mcp_servers.enchanted` 字段会受到包装脚本启动参数覆盖，不能泛称所有用户文件配置都优先。opencode 在透传用户配置的分支不保证自动挂上 enchanted，这是代码明确选择。新增路径中没有发现向真实 `~/.claude`、`~/.codex` 或 `~/.gemini` 写配置的操作；本轮探针只使用报告目录内的隔离 HOME。

新增工具异常边界把异常保留为带原因的 `outcome_unknown`，没有伪装成功、自动重试或改走另一套 API。解析非法 JSON 时会直接忽略该行；本轮没有把这一行为外推为完整 JSON-RPC 合规性结论。已确认的生命周期遗漏归于 F1。

### 既有验收证据与反事实

以下路径相对只读仓库 `/Users/luckye/Documents/Code/a2a/evidence/2026-10-27-batch28/T-194/`；本轮读取证据与对应候选测试源码，没有重跑真实模型。

| 材料 | 支持的结论与边界 |
| --- | --- |
| `green-07-on-t195v3.json`，8 项检查 | 真实 Claude 交互 CLI、插件、后台、终端和受管 worker／reviewer 走通申请、建卡、派发、交付、审查、集成；模型为脚本化 Messages 服务。观察角色确认记录、集成分支文件、worker 归属和打分，超过“模型自报成功”的证据强度。 |
| `red-87c30f0.json`、`red-3be2a96.json` | 修前真实 CLI 工具表没有 enchanted 工具，检查在该边界失败。它们的 JSON 状态为 `INCOMPLETE`，不能当通过；具体失败支持入口缺失的红态。 |
| `mutant-grant-not-confirmed-02.json` | 去掉确认步骤后，`mcp_role_takes_effect` 因没有确认事件失败；不是仅因依赖缺失或进程崩溃。 |
| `mutant-session-not-reported-02.json` | 去掉会话号后，`mcp_role_carries_cli_and_session` 对照 CLI 自己的 JSONL 会话号失败。 |
| `real-04.json` | 真实 Codex、opencode 交互模式经包装脚本出现本终端申请，拒绝后没有角色；Codex 会话号等于其独立 rollout 记录。Codex 使用隔离 HOME，记录了钩子信任批准和该 HOME 删除。这里只证明申请／拒绝边界，不证明这两家各自完成全流程或等待满 10 分钟。 |
| `real-red-b6c2600.json` | 修前真实 Codex 没有可调用的 enchanted 入口，申请不出现；该失败没有被抹去。 |
| `real-03-opencode-agy.json`、`agy-interactive-probe/` | agy 交互模式没有调用工具；服务端日志证明已完成初始化和工具清单交换，交互输出为 `NO_TOOL`，print 输出能拿到 `terminal_whoami` 回显。支持对所测 agy 1.4.8 保留命令入口。不能据此确定 agy 内部根因，也不能保证所有后续版本均不可用。 |

`findings/2026-10-27-mcp-per-session.zh-CN.md` 对三家挂载、agy 不挂、会话号来源及 agy 内部原因属于推断的说明，与上述代码和证据基本一致。保留 agy 不挂的决定有依据；本轮未逐一重建文中“四次复现”的全部变量组合。

README 的挂载方式、Codex 批准模式和超时数值与代码一致。“取消或后台断开返回未知、不重放”覆盖已测通知和后台断开路径，但未覆盖 F1 的 EOF。另需准确理解“门禁记录相同”：测试 `test_t194_mcp_entry_e2e.py:215` 对比的是选定事件的首次出现、字段集合，以及部分卡片、启动参数和评分值；`records()` 按固定 `own` 顺序重组，不能证明所有原始事件的顺序、次数及全部字段值都相同。代码复用同一门禁提供了额外静态支持，绿色检查本身没有证明更宽的主张。

## LIMITATIONS

- 按 brief 未重跑真实供应商模型、真实 UI 全流程或长达 600／660／720 秒的超时；没有穷举全部工具、撤权竞态、所有 Codex／opencode 配置组合及完整 MCP 协议。
- 既有绿色报告的 `revision` 为 `null`，不能仅凭文件名把每项旧观察严格绑定到 `494d859`。本轮新探针明确使用冻结候选绝对路径；它们补足停止／传输边界，不替代全部旧全流程证据。
- `probe-lifecycle.json` 是未做初始化握手的初探，保留；F1 以完成标准握手的 `probe-lifecycle-02.json` 为主证据。首次执行脚本保存在 `probe_lifecycle.executed-01.py`。
- 边界探针首轮 `probe-boundaries.json` 虽写了 `PASS`，后台线程在 Python 3.9 上出现未捕获的 `socket.timeout`；本轮将该次视为 **INCOMPLETE**，不据此背书。原脚本和诊断保存在 `probe_boundaries.executed-01.py`、`probe-boundaries-01.stderr.txt`。修正探针的异常收集后，第二次退出码 0、stderr 为 0 字节，得到 `probe-boundaries-02.json`；没有改候选。可用 `python3 -B /private/tmp/t194-review1/probe_boundaries.py --summary /private/tmp/t194-review1/probe-boundaries-replay.json` 复现到新文件。
- 探针复用既有 Fixture 创建隔离后台和终端，断言与 EOF 输入由本轮独立编写；没有访问用户登录凭据、调用真实模型或修改全局配置。隔离后台已停止，现场和失败证据均保留在本目录。
- `git diff --check 87c30f0 494d859` 退出码 0。项目地图只读 `status` 开始与结束均为 Problems 0、Stale living docs 0；该结果描述主仓库地图，不能替代候选行为验收。

恢复验收的最小条件：修复 F1 后，以同一真实入口证明 EOF 撤回、迟到批准被拒，并确认通知取消和正常申请／确认仍成立。本轮只提交审查结果，不实施修复。
