# T-106 / a1：创建入口前提核对

2026-10-19。**BLOCKED**。依派发第 5 条，发现“起主控”需要超出界面薄层的新设计后停止实现。

本次没有改产品、门禁、测试、任务卡、地图或用户全局配置；只有本目录的诊断脚本与文本摘要。未 submit、未 push。没有运行后台、Electron 或 Claude，没有读取正常登录凭据。真实模型根回合 0，假 API 请求 0；没有截图。

## 绑定与范围

- task `T-106`，attempt `a1`，分支 `exec/t106`。
- session `46c7c0a5-076f-48e7-adc0-4aea62a637a9`，launch `launch-d83c474a34f148c19f8e35e9bd60ff71`。Herdr 派发环境没有 fence/spec_rev，不推断其值；需求版本取 T-106 `ready_rev: 1`。
- 核对代码：`41b779c104d1fbf39f40bf285575e9f295367d98`，Node `v26.5.0`。
- 目标：先做 **Tracer bullet**，从空库经界面注册项目，再由主控补任务卡，用户确认后通过现有命令注册任务。
- 非目标：派 worker、修改任务卡校验规则、放宽主控权限、建立临时占位任务或另一套创建路径。
- 验收：同一份门禁库中出现用户确认的项目/任务；任务确认前不存在、拒收原因可见、取消没有残余。
- **Ubiquitous language** 沿用 `CONTEXT.md` 的项目、任务、任务卡、主控与启动记录。没有把占位任务改称项目来绕过合同。
- **Deep modules**：现有缺口位于门禁存储、主控身份与请求权限；不能由一个界面包装隐藏成已具备的能力。

## 阻塞事实

| 类型 | 定位 | 观察及影响 |
| --- | --- | --- |
| observed | `workbench/src/gates/cli.ts:15`、`workbench/src/contracts/a2aGates.ts:29` | 完整命令集合没有独立项目注册命令。`create` 是任务注册，需要 task、repo、branch、card-version；不能用它单独注册空项目。 |
| observed | `workbench/src/gates/core.ts:325`、`workbench/src/panes.ts:117` | `listProjects()` 从 tasks 表取 DISTINCT project_id；`ensureProject()` 是空实现。首个任务创建前，没有可供列表显示的独立项目记录。 |
| observed | `workbench/src/daemon.ts:334`、`workbench/src/gates/core.ts:1011` | `controller_start` 先查询已有任务；不存在就返回 `unknown_task`，尚未进入启动或凭据处理。`controller_prepare` 也有同一前提。 |
| observed | `workbench/src/claudeLaunch.ts:30`、`workbench/src/gates/core.ts:351`、`workbench/src/relayFiles.ts:28` | manifest、启动记录、主控登记、主控请求上下文均绑定 task/spec_rev；不是删掉界面中的 task 参数就能支持无任务主控。 |
| measured | `workbench/src/gates/cli.ts:204`；[CLI 摘要](cli-baseline-01.json) | 合成主控环境调用实际 CLI，`card_template`、`card_validate`、`card_save`、`create` 全部退出 1，details 为 `Error: worker_command_forbidden`。本地检查发生在连接后台之前。 |
| observed | `workbench/src/relay.ts:110` | 即使跳过 CLI，本轮 Stop 转交合同也只允许主控的 inbox/stop 请求，不包含任务卡或注册命令。直接扩大白名单属于权限变化。 |
| inferred | 上述调用链 | 需求中的“空项目 → 起主控 → 草稿 → 用户确认 → 首个任务”无法仅用现有入口的薄层实现；必须先决定并实现缺少的项目记录、无任务主控身份与受限草稿请求合同。 |

没有创建占位任务：那会违反“确认前库里不能有这个任务”和“取消不留残余”。也没有从主控环境删除身份变量、传入 operator 凭据或直接写库来绕过权限。

## 已执行的最小探针

```sh
python3 evidence/2026-10-19-batch17/T-106/probe_cli.py --summary evidence/2026-10-19-batch17/T-106/cli-baseline-01.json
```

脚本退出 0，表示四次实际 CLI 调用都准确复现了上述拒绝；摘要状态仍为 **BLOCKED**。输入为合成主控身份、未创建的隔离 state 路径与未创建的 card 路径。未启动 agent，不涉及认证、daemon socket、PTY 或模型。原始命令和短响应均在摘要中。

这只是当前 CLI 权限阻塞的运行证据；不是任务创建的 Electron 红态、主控正常登录验证或完整假 API 验收。尚未形成产品候选，不宣称红绿态已齐全。

重放时使用新的摘要文件名，脚本拒绝覆盖既有结果；例如：

```sh
python3 evidence/2026-10-19-batch17/T-106/probe_cli.py --summary /private/tmp/t106-cli-replay-01.json
```

此命令可在沙箱内执行，不需要主控运行沙箱外脚本。本次未产生需要沙箱外执行的步骤；也没有真实模型启动命令待运行。

## 按验收逐项核对

| T-106 验收 | 状态 | 说明 |
| --- | --- | --- |
| 空库 Electron → 项目 → 主控草稿 → 确认注册，及 CLI 同库对照 | BLOCKED | 缺少独立项目注册、无任务主控和主控草稿命令合同。未实现、未运行。 |
| 确认前无任务、缺字段拒收可见、取消无残余 | INCOMPLETE | 没有草稿 UI 候选，未运行这些反例。 |
| 实际模型回合与 manifest 预算 | INCOMPLETE | 实际根回合 0。依派发顺序，假 API 流程通过后才报真实回合计划；目前未到该步骤，未请求真实回合批准。 |
| 不绕过门禁、不写用户全局配置 | PASS | 本次只读产品代码并执行本地 CLI 拒绝探针，写入限本目录摘要。 |
| `project_map.py status` 0 问题 | INCOMPLETE | 起止均退出 1：稀疏 checkout 缺 `findings/` 中 5 个文件与 `.grilling/a2a-gui-client.md`，共 8 个诊断；stale living docs 0。未扩大 checkout 或改地图。 |
| IPC 名称集合与原拒绝检查 | INCOMPLETE | 未修改 IPC，也未改原合同测试；没有产品变更，未复跑旧测试来代替 T-106 验收。 |

## 主控下一步

建议先补前置设计/规格，明确三件事：独立项目的注册与存储；首个任务之前的主控身份和启动合同；主控生成草稿所需的最小命令范围及用户确认边界。它们需要同时覆盖 CLI、daemon、启动记录和请求转交，不能由本 worker 就地发明。

由主控确认前置方案与执行范围后，T-106 再继续项目 Tracer bullet 和假 API 草稿验证。此报告不关闭 T-106，不修改验收条件，不提交未经批准的真实模型计划。
