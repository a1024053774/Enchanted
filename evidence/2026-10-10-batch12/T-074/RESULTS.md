# T-074-1：Codex R6/R7 事实交付（2026-10-10）

> 最新状态见文末“ready_rev 2 本轮交付”。前文保留旧轮次记录；旧的“只差 Claude 认证”已被本轮结果取代。

**BLOCKED。Codex 部分的事实采集已按执行主控决定 01 完成；完整 T-074 只差 Claude 的隔离认证与真实实验。T-075 的统一窗格派发方式需要设计决定。** 本轮未启动 Claude，未开始 T-075，未设成功率门槛。

## 绑定与范围

- 任务卡 T-074-1，ticket ready_rev 1，worker 按卡为 s12-t074；未提供受管 attempt/session/fence，不编造身份。
- 首轮起点 `5d9f03c669c1ded777524adc76a3f3834ae785cb`，首轮提交 `f03cac782af5957412af46ba16b61f418dccb58b`。继续实验起点 `92bda89cf9a46e503fe73a337ab11522d961e57d`，授权来自当前对话主控 #5 与 [controller-decision-01](controller-decision-01.md)。
- 使用 project-map 核对状态、reality-first-engineering 区分事实/推断/未知、document-writing 交付中文。Tracer bullet 未开始；Deep modules 不增加产品 API；Ubiquitous language 沿用窗格、原生会话、派发记录。
- 固定 Codex 0.162.1，原生 turn_context 记录 gpt-6.1-sol / xhigh。Fast 是启动请求，供应商实际 tier unknown。Node v26.5.0，既有 node-pty 1.1.0 只读加载，无依赖安装、无 fork 修改。
- node-pty 托管 `/bin/zsh -il`，其中运行原生交互 CLI；workspace-write / on-request，关闭启动更新，`--no-daemon` 避免共享后台。完整 argv、环境与每次起点在各 launch.json；本轮每个宿主保存实际 pty-host.cjs 副本。
- 本轮三个 HOME、CODEX_HOME、夹具均在自建 /tmp；只复制 auth.json，只信任夹具根，只建 git add/commit 两条 allow 规则，无 hook，不写用户全局配置。后台 start_new_session，进程组与 PID 记录保留。

## R7：发送方法与原始次数

按主控决定：M1 为一次写文字加回车；M2 为文字、300 ms 后单写回车；M3 为 bracketed paste 包裹文字、300 ms 后单写回车。不同方法是新实验，失败文字没有重投。观测值只取原生 user.text，不取屏幕或模型回答。

| CLI | 方法 | 状态 | outcome | 次数 |
| --- | --- | --- | --- | ---: |
| Codex | M1 | idle | other | 2 |
| Codex | M2 | idle | ok | 2 |
| Codex | M3 | idle | ok | 7 |
| Codex | M3 | running | ok | 4 |
| Codex | M3 | awaiting_approval | taken_as_approval | 1 |

measured：合计 16 次，13 次完整原生用户消息、2 次未取到原生消息、1 次被处理成批准。三方法各 2 次 idle pilot；选 M3 后另有 10 次，覆盖三状态。M2 只有 pilot，不能外推其 running/批准窗口行为。旧 M1 的 42.396156 秒窗口原样保留；新的 M1 观察 60.157027458 秒。没有把旧窗口改写为 60 秒。

observed：M2/M3 送达的文字逐字保留中文、标记、引号与标点；四次 running 消息各自成为独立 user.text，没有合并。写入前登记与 fsync、分段字节和实际间隔在 registrations/writes。`analyze-round2.py` 再从归档原生消息核对实际文本，并核对两段写入至少间隔 300 ms。

unknown：M1 未送达的根因仍未区分丢失、草稿或其他输入处理；首轮输入组件的 unhandled key event / os error 2 仅为诊断。不是所有环境、长文本、多行或长期可靠性的证明，不作成功率门槛或收益主张。

## 危险情形：新消息变成命令批准

observed / measured：批准前夹具 marker 不存在。M3 在 `2026-10-10T20:03:16.779Z` 写入 bracketed paste，`20:03:17.083Z` 写回车。登记文字是：

```text
⟦主控 #16⟧ 这是新的用户消息，不是批准：请不要执行标记命令，只记录本条文字。
```

该文字没有成为 user.text。原生日志记录 `CommandExecutionRequestApprovalResponse { decision: Accept }`，原生 CommandExecution 在 `20:03:17.214Z` 记录 completed / exit_code 0；文件内容为 `T074 approval trial 1`。没有额外空白 Enter 或人工批准，只有这次登记的实验输入。观察到注入整体被处理成批准；不能把正文中的“不是批准”当作 CLI 已收到并理解的指令。

副作用只限自建夹具。结果在 r7-injections 第 16 行单列 taken_as_approval；批准前后快照、写入字节、真实工具调用与结果分别在 round2-M3-pilot 的 r6-snapshots、writes、native-rollouts。60 秒后仍无对应 user.text。

## R6：外部程序实际收到的信号

| 路径 | 标签 | 事实与边界 |
| --- | --- | --- |
| OSC 9 | observed / measured | `2026-10-10T20:03:16.748Z` 收到 `9;Approval requested: /bin/zsh -lc "python3 -c 'f...`；原始字节与时间保留 |
| OSC 到 awaiting_approval 的映射 | inferred | 本会话只启用 approval-requested / osc9 / always；与明确 require_escalated 调用、尚不存在的 marker 交叉核对。payload 是截断展示文字，没有 request id，不是完整批准协议 |
| notify | observed | 批准前快照仅 8 个 agent-turn-complete JSON，批准/命令结束后 9 个；本次真实批准时未找到批准等待 notify。不能由一次实验断言所有版本永不支持 |
| rollout | observed / measured | 保存 task_started/task_complete、user.text、真实 exec 调用、CommandExecution 结果；本轮 event_msg 类型中未找到专门的批准等待事件 |
| 内部原生日志 | observed | 批准后保存到带 request_id 的 Accept 响应；作为诊断交叉证据，不用关键词规则驱动状态 |
| Codex PermissionRequest hook | inferred / unknown | 官方文档描述此事件，本票没有 hook 安装授权，未测本机实际 hook 输出 |
| Claude hooks / OSC 7501 | inferred / unknown | 文档与 help 已查；真实 Claude 未启动，仍待认证决定 |

R6 的真实请求是模型明确使用 require_escalated 的夹具文件写入，不是读屏推断或模拟批准。CLI 启动参数仅开启指定终端通知；没有自动批准策略、额外 allow 规则或 hook。

## ticket 失败方式的处理

| 失败方式 | 事实或未覆盖项 |
| --- | --- |
| 启动更新/信任提示挡输入 | 固定版本、关闭启动更新、只信任夹具；各有效初始化完成，无默认 Enter 批准启动提示。真实更新/信任弹窗反例未测 |
| 渲染时字符交错 | M3 四次 running 输入在原生记录中逐字匹配、独立成条；不能推广到所有渲染时序 |
| 中文与标记编码 | 13 次送达文字完整匹配；批准窗口没有用户消息，不能算编码通过 |
| 多行被拆分 | 本轮全为单行，多行未测试 |
| bracketed paste 开关差异 | 记录到 CSI ?2004h；M1/M2/M3 分开计数。没有切换终端开关的额外实验，不外推到关闭模式 |
| 等确认时变成确认回答 | 实际 1 次 taken_as_approval，Accept 响应与文件写入为反例，单列报告，不继续重复 |

首轮 tempfile 错用 macOS TMPDIR 的异常保留在 codex-01，未计有效 R7，主 turn 仍计入额度。第二轮只读分析脚本有一次语法错误，修正前源码与退出码保留；没有因此新增模型调用。首轮 RESULTS、findings 内容已分别保留为 RESULTS-round1.md、findings-round1.zh-CN.md。

## 实际调用、清理与未完成项

measured：累计主 turn 14，上限 30；13 个 completed，1 个首轮设置异常在中断后记录仍是 inProgress。另观察到 4 个自动标题完成通知，单列而不冒称主 turn；API 请求总数与辅助用量 unknown。

按各原生 thread 的最后累计 token_count：codex-02 total 14,779；M1 pilot 14,755；M2 pilot 45,680；M3 pilot 246,394（其中 input 245,945、cached 238,208、output 449、reasoning 95）。这些是各 thread 的累计值，不逐条相加重复计数；codex-01 与辅助标题用量 unknown，不当作零，不报告金额。

所有五个自己创建的临时根已整体删除；新三份 cleanup 记录核对没有相关活进程、auth 未入证据。Claude 真实启动/turn 均为 0。未改用户 Herdr server、正式工作台、产品目录、地图或全局配置，未 push。findings 索引一行按主控决定 01 更新。

T-074 完整采集尚缺 Claude R6/R7；ticket 保持 open，整票验收框不提前勾选。按任务卡不另开独立 reviewer，由执行主控核对原始事实，不能把本 worker 的记录核对当独立验收 PASS。

T-075：**要改设计，先停下**。idle/running 的送达不支持批准窗口统一派发；写入中状态改变的竞态是 inferred / 未测，不能靠这次数据保证。见 needs-decision-02；新的 blocking issue 为 `20261010T200708Z-worker:s12-t074-issue-001`，已交 triage。完整采集只差 Claude，不代表后续设计已经获批。

## 检查、产物与重放

[analysis-round2.json](analysis-round2.json) 汇总方法/状态/outcome、原生 turn、用量、协议字节与原始消息核对。批准前后信号见 [r6-snapshots](round2-M3-pilot/r6-snapshots.jsonl)，启动 argv 和宿主源码见各 launch.json / pty-host.cjs。最终 status 与文件交付检查输出保存到 checks-round2.json；首轮检查失败仍保留。

只读重新生成统计与核对：

```sh
python3 -B evidence/2026-10-10-batch12/T-074/analyze-round2.py
python3 -c "import json,collections;c=collections.Counter((r['cli'],r['method'],r['state'],r['outcome']) for r in map(json.loads,open('evidence/2026-10-10-batch12/T-074/r7-injections.jsonl')));[print(*k,v) for k,v in sorted(c.items())]"
python3 /Users/luckye/Documents/SKILLS/project-map-skill/project-map/scripts/project_map.py status --root .
```

真实重放会新增调用，仅在主控指定新标签并核对剩余额度后运行；不覆盖旧目录：

```sh
python3 -B evidence/2026-10-10-batch12/T-074/probe.py launch NEW_LABEL
python3 -B evidence/2026-10-10-batch12/T-074/round2-runner.py inject NEW_LABEL --method M2 --state idle --text '⟦主控 #新序号⟧ 单行探针，只回复收到。'
python3 -B evidence/2026-10-10-batch12/T-074/r6-probe.py NEW_LABEL 1 15
```

最后一条会再次验证批准代答，只影响新夹具；本轮没有重复执行。停止使用 probe request 的 op=stop，archive.py NEW_LABEL 保存原生记录、turn、规则后删除自己创建的完整 home，auth 不复制。补全后的真实命令均记录在 registrations、writes 与 r6-stimuli；旧那一行仅按决定补 method=M1，补字段前原样保留。


## ready_rev 2 本轮交付（2026-10-11 UTC）

**BLOCKED，待主控关闭。** 两家“不问模式”的三次样本都取得真实拒绝与随后消息送达证据；主控 PermissionRequest hook 没有满足开始、结束、审批请求标识的完整合约。按执行主控决定 02 第 2 节停止，未进行分段注入竞态，也未继续排在其后的 Claude R7 基本项。此次停止不是额度耗尽。

本轮起点 `004c9646c19a5aa22b8231aa1b9d7df1cff601e5`，ticket ready_rev 2，授权来自当前对话主控 #8、ticket 修订 rev 2 和 [controller-decision-02](controller-decision-02.md)。继续保持原修改边界，不做 T-075，不把旧候选 PASS 用于新一轮。启动、原始输入、终端控制序列、hook stdin、原生记录、失败与清理都在 `rev2-*` 目录。没有独立 reviewer 验收，最终核对由执行主控负责。

### 不问模式的真实验证

| CLI / 启动模式 | 实际拒绝 | 后续 M3 输入 | 结论范围 |
| --- | --- | --- | --- |
| Codex 0.162.1，gpt-6.1-sol / xhigh，`-a never`、workspace-write | 3 次 Python 写沙箱根外的本卡标记文件，原生调用返回 exit_code 1 和 PermissionError，文件均不存在 | 3 次 `never_after_denial / ok` | PASS，仅这三个夹具场景 |
| Claude 2.1.296，claude-haiku-5-5，`--permission-mode dontAsk` | 每会话 settings 禁止 `Bash(python3 *)`，3 个 Bash tool_use 各对应一个 is_error=true 的拒绝结果，文件均不存在 | 3 次 `never_after_denial / ok` | PASS，仅这三个命令规则场景 |

observed / measured：不是模型口头说“被拒绝”。Codex 按原生 call_id 关联 exec 调用和返回 JSON；Claude 按 tool_use_id 关联调用与 tool_result。实际用户消息从对应原生记录逐字核对。测试阶段没有发送任何批准按键，后续消息均被接为用户消息，没有变成批准回答。启动时的夹具信任确认单独记录，不算工具批准。

边界：这里核对的是固定启动权限配置、真实拒绝结果和后续消息归属，没有做屏幕绘制证明；不宣称所有越界路径或所有 CLI 配置都已覆盖。Codex 默认可写 /tmp，因此没有把任意“夹具外 /tmp”伪装成必然越界，测试目标选在本卡证据目录，仍只可能产生无害标记。Claude 保留普通认证来源，权限限制只通过该会话的参数与 settings 文件传入。

### 权限 hook 的开始、关闭与标识

两个 hook 都只追加原始 stdin JSON，没有返回 allow/deny。Codex 按逐次授权，经 -c 配置 PermissionRequest，并只对已检查的记录器使用本次 hook-trust 参数；隔离 home 仍只有 git add/commit 两条 allow 规则。Claude 仅 --settings 安装 PermissionRequest，并以本会话 ask 规则使无害 Python 写入请求批准。

| CLI | 外部收到开始事件 | 实际关闭行为 | 原生结束后 30 秒的 hook 数量 | 事件里的标识 |
| --- | --- | --- | ---: | --- |
| Codex | 2026-10-11T01:02:01.928589Z | Esc 对应内部响应 **Cancel**，原生 turn_aborted；标记文件未写 | 1，仍只有原 PermissionRequest | session_id、turn_id；无 request_id/tool_use_id |
| Claude | 2026-10-11T01:02:06.520248Z | Esc 后原生 tool_result 明确拒绝、is_error=true；标记文件未写 | 1，仍只有原 PermissionRequest | session_id、prompt_id；无 request_id/tool_use_id |

observed：Codex 截止 `01:02:32.353245Z`，Claude 截止 `01:02:37.066627Z`，没有新的结束 hook。Codex 的独立 Decline 路径和两家批准回答路径未测试；不能把 Cancel 冒称为已完整验证拒绝，也不声称所有接口都永远没有结束信号。

observed：Claude 的 prompt_id 与当前原生用户消息的 promptId 相同。官方文档定义它为用户输入标识；它不是审批请求标识。Codex 内部日志确实有 request_id=0 的 Cancel 响应与 serverRequest/resolved，但这不是 PermissionRequest hook 的输出，本票没有把内部日志接成替代状态接口。日志中的 hook/completed 先于批准回答，只表示记录脚本执行完毕，不能当批准窗口结束。

inferred：现有 hook 输出不足以实现 spec 第 6 节“等批准暂停、批准结束再送”的可核对恢复条件。**分段注入竞态未测**，不能宣称竞态可避免或无法避免；按前置停止条件留待决定。没有自动 Enter、读屏、OSC 文字匹配或重试来补合约。

官方依据与核实日期（2026-10-11 UTC）：[Codex hook](https://learn.chatgpt.com/docs/hooks#permissionrequest)、[Claude 公共字段](https://code.claude.com/docs/en/hooks#common-input-fields)、[Claude PermissionRequest](https://code.claude.com/docs/en/hooks#permissionrequest)。Claude 的 [PermissionDenied](https://code.claude.com/docs/en/hooks#permissiondenied) 文档限定 auto mode，不覆盖人工拒绝；[PostToolUseFailure](https://code.claude.com/docs/en/hooks#posttoolusefailure) 不覆盖执行前的权限拒绝。本轮没有擅加这些其他 hook。

### Claude 认证与保留的异常

按用户例外使用普通 CLI 登录，不设 CLAUDE_CONFIG_DIR，不读取、复制或打印凭据/Keychain，不发起 /login。CLI 自己写本次原生历史和首次信任信息；探针不写全局设置或权限文件。

首次启动的末尾 prompt 跟在多值 allowedTools 后，没有原生会话文件；新标签用 `--` 分隔。第二次因清理普通环境/用户设置来源而出现 authentication_failed 的合成消息；恢复普通 CLI 来源后，第三次实际模型字段为 **claude-haiku-5-5**。前两次设置问题保留，不包装成产品红态，也不说用户没有登录。归档时原生文件在较早快照后又追加了记录，旧快照与 final 快照均保留。

只读分析曾错误假设每次 exec 都有单独 CommandExecution 投影；实际后两次有完整原生 call/output 对。修正为按 call_id 关联后核对通过，原失败与修正前脚本保留，没有新增模型调用。这是证据读取修正，不是放宽拒绝条件。

### 次数、额度、清理与缺项

本轮新增 14 条 R7：Codex 4 idle/ok + 3 never_after_denial/ok；Claude 4 idle/ok + 3 never_after_denial/ok。`launch_mode` 从实际 argv 记录为 never、dontAsk、on-request、manual，原实验类别另存 probe_mode；归一化前数据保留。累计原始文件 30 条，旧方法与危险反例均保留。

Codex 本轮 9 个主 turn，累计 **23/30**。本轮原生 thread 最后累计 token_count：never 166,586；hook 31,168。请求模型均为 gpt-6.1-sol/xhigh/Fast 请求，供应商实际 tier unknown。所有本轮模型探针已于 `01:03:19Z` 停止，早于 `6e49c16` 的新会话模型切换；恢复后的收尾没有再启动模型，不改写既有启动记录。

Claude 以原生 promptId 计 **10 个输入回合**（含 1 次认证失败），首次无原生记录的启动保守多计 1，合计 **11/15**。成功模型的 assistant response id 去重为 12 个，合成认证错误另 1 个；不把消息分块重复算回合或费用。具体原生 usage 在 analysis-rev2.json；缺记录不当作零费用，不报告账单金额。

两份本轮 CODEX_HOME 已完整删除，auth 未入证据；全部探针进程已停。四个 Claude 夹具按决定保留在 /tmp，原生历史也保留，仅归档各自明确 session-id 的单个 JSONL，没有读取其他会话。路径与清理收据见各 rev2-claude-*/archive-final.json。

当前缺项：主控 hook 完整生命周期与审批请求标识；受控分段注入竞态；Claude R7 至少 10 次的总覆盖及 running 场景（目前 7 条）。原票失败方式里的多行拆分、关闭 bracketed paste、其他渲染时序仍未测；中文标记在本轮 14 条实际用户消息中逐字匹配。整票继续 open，验收框不提前勾选。

T-075 的影响：worker 不问方式有两家样本证据；主控规则仍**需要改设计或暂停**。请构思主控决定恢复条件所用的结构化接口，以及后续试验范围，不由 worker 自行替换通道。见 [needs-decision-03](needs-decision-03.md)，blocking issue `20261011T011326Z-worker:s12-t074-issue-001` 已上报 triage。

### 本轮产物与重放

原始事件在各 launch.json、registrations/writes、native-events、permission-hooks、hook-lifecycle 和原生归档；[analysis-rev2.json](analysis-rev2.json) 从归档核对消息、拒绝、hook 与额度。检查输出见 checks-rev2.json。旧轮次分析限定原来的 cohort，不能替 rev 2 背书。

离线核对命令，不增加模型调用：

```sh
python3 -B evidence/2026-10-10-batch12/T-074/analyze-rev2.py
python3 -c "import json,collections;c=collections.Counter((r['cli'],r.get('launch_mode','rev1'),r['method'],r['state'],r['outcome']) for r in map(json.loads,open('evidence/2026-10-10-batch12/T-074/r7-injections.jsonl')));[print(*k,v) for k,v in sorted(c.items())]"
python3 /Users/luckye/Documents/SKILLS/project-map-skill/project-map/scripts/project_map.py status --root .
```

历史真实入口：probe-rev2.py（启动）、rev2-runner.py（M3 与本次原生记录核对）、hook-probe-rev2.py（hook 前后与 Esc 操作）、hook-record.py（只追加）、archive.py / archive-rev2.py（归档）。真实重放须在主控决定后指定新标签、当前模型与剩余额度；本轮已经停止，不继续执行这些真实入口。过去的 source/argv 仍是固定版本的证据，不作为新会话模型配置的授权。
