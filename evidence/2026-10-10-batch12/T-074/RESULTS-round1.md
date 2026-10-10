# T-074-1：首轮 R6/R7 事实报告

**BLOCKED，待主控关闭。** 第一条 idle 注入在原生消息记录中未证实送达，已按任务卡停止；R7 数量与状态覆盖、R6 真实批准、Claude 实验均未完成。没有开始 T-075，不设成功率门槛，不做自动 Enter 或兜底重试。

## 绑定与边界

- task card：T-074-1；ticket ready_rev：1；本会话名称按卡为 `s12-t074`，worker。
- 开工 a2a main HEAD：`5d9f03c669c1ded777524adc76a3f3834ae785cb`。没有收到受管 task/attempt/session/fence，未伪造门禁身份；按卡提交本地事实报告，主控负责核对与关闭。
- canonical：`intent.md` 第三阶段、`native-cli-orchestration-2026-10-10.md` 第 5、6、12、13 节；范围见 [PLAN](PLAN.md) 与批次任务卡。
- Codex：固定实际二进制路径及完整 argv 在 [codex-02/launch.json](codex-02/launch.json)；版本 0.162.1。原生 turn_context 记录模型 gpt-6.1-sol、effort xhigh；`service_tier="fast"` 是请求配置，供应商实际 tier **unknown**。
- 终端：Node v26.5.0，既有 node-pty 1.1.0（只读加载相邻 fork 的依赖）；`/bin/zsh -il -c <Codex>; exec /bin/zsh -il`，PTY 160×45，UTF-8。没有改 fork 或安装依赖；外置盘挂载后才启动，无缓存回退。
- 后台用 `start_new_session=True`，host 与 PTY 的不同进程组保存在 process-events；只停自己的进程。工作目录、CODEX_HOME、shell HOME 与 ZDOTDIR 都是自建目录；有效运行在 `/tmp`。只复制 auth.json，trust 只限夹具根，规则只有 git add/commit，无 hook。收尾删除完整临时 home，凭据未入证据/Git。

## R7 原始次数与截止点

| CLI | idle | running | awaiting_approval | 合计 |
| --- | ---: | ---: | ---: | ---: |
| Codex | 1 次 other | 0 | 0 | 1，要求至少 10，未完成 |
| Claude Code | 0 | 0 | 0 | 0，未真实启动 |

observed：初始化主回合已完成（rollout 第 17 行 task_complete），随后没有新的回合开始。外部在 `2026-10-10T19:49:31.927Z` 追加、fsync 登记，`19:49:31.932Z` 写入文字与回车：

```text
⟦主控 #1⟧ 中文编码探针一。只回复收到，不调用工具。
```

measured：观察 42.396156 秒，截止 `2026-10-10T19:50:14.324071+00:00`。归档原生记录只有初始化用户消息，没有这条登记文字。结果保存为 `outcome=other`、`observed_text=null`。不能区分 lost、草稿或其他拦截，不能编造 CLI 实际收到的文字。记录来自 native `response_item` 的 `user.text`，不来自终端显示或模型自报。

observed：原生内部日志记录最初几个字符的 unhandled key event，以及输入组件的 `ERR: No such file or directory (os error 2)`；该日志是诊断，不是成功送达 oracle。根因 unknown，没有根据关键词把它分类成某个状态。终端 raw 保留，状态与消息核对不读屏。

**危险情形单列：等确认时注入被当作确认的回答——unknown，未测试。** 没有触发批准弹窗，不能写“未发生”或“0 次风险”。

## R6：各路径的实际证据

| 路径 | 标签 | 本轮外部收到了什么、何时收到 |
| --- | --- | --- |
| notify 主回合 | observed / measured | `agent-turn-complete` JSON，`2026-10-10T19:49:11.651426+00:00`；原生结束为 `19:49:11.576Z`，本机接收差约 75 ms；不作延迟可靠性主张 |
| notify 自动标题 | observed | 另一 thread/turn 的完成 JSON，`19:49:16.198123+00:00`；辅助调用单列，不能当 worker 主回合 |
| notify 等确认 | unknown | 尚未真实触发批准，不能说“未找到信号” |
| OSC 9 | unknown | 仅配置 approval-requested / osc9 / always；没有批准发生，未测到此信号 |
| rollout | observed / unknown | 测得 task_started、task_complete、user.text、token_count；等确认相关事件未测 |
| Codex PermissionRequest hook | inferred / unknown | 官方文档有该事件；无 hook 授权，本轮没有安装或验证本机固定版本的实际输出 |
| Claude hooks / OSC 7501 | inferred / unknown | 官方文档有 PermissionRequest、2.1.295 起 OSC 7501；本机 2.1.296 只查 help/version，不调用模型 |

文档来源与核实日期见 [中文报告](../../../../findings/native-cli-signals-injection-2026-10-10.zh-CN.md)。notify 的真实输入参数与完整 JSON、每个控制序列、rollout 接收时间分别在 notify.jsonl、terminal-controls.jsonl、native-events.jsonl。没有用 app-server 无头调用或屏幕正则补上 R6。

## ticket 的失败方式逐项处理

| 失败方式 | 本轮处理与限制 |
| --- | --- |
| 更新或信任提示挡输入 | 固定版本、关闭启动更新、预先只信任夹具；有效运行初始化完成，未用 Enter 默认批准启动提示。真实提示反例未测 |
| 渲染时字符交错 | 只写一次，保留原始终端流与登记；没有对应原生消息，交错与否 unknown，未补发 |
| 中文与标记编码 | 写 UTF-8；日志能记录 `⟦`、`主`、`控`；完整消息原生送达仍 unknown，不将局部字符解码当通过 |
| 多行被拆成多条 | 本轮是单行，多行未测；停止后未扩展用例 |
| bracketed paste 开关差异 | 记录到 CLI 发出的 CSI `?2004h`；失败输入没有加 bracketed-paste 包装。另一模式未测，未将切换模式当兜底重投 |
| 等确认文字变成批准回答 | 单列 unknown / 未测试；原计划副作用限夹具，但因先前失败没有触发或批准 |

另有探针设置异常：首次 `codex-01` 的 tempfile 沿用 macOS TMPDIR，没有在 `/tmp`；主动停止，0 次 R7 注入，原始启动与未结束 turn 保留。修正启动器显式 dir `/tmp` 后建立独立 `codex-02`，不是失败 R7 文字重投。该异常不计有效覆盖。

## 实际调用与清理

observed：本轮显式启动两个原生主回合（设置异常 1、有效初始化 1）；前者在停止时原生 DB 仍是 inProgress，后者 completed。另有一次自动标题的完成通知。因此观察到至少 3 个原生/辅助 turn，不能冒称 API 请求总数是 3。

有效初始化主回合 token_count：input 14,747（cached 12,160）、output 32（reasoning 22）、total 14,779。设置异常与辅助标题用量 unknown，未把缺记录当 0；没有 API 金额或总成本结论。Claude 真实启动、真实 turn 均为 0。

[codex-01/cleanup.json](codex-01/cleanup.json)、[codex-02/cleanup.json](codex-02/cleanup.json)记录清理前没有相关活进程，并确认完整自建临时根已删除。auth.json 没有复制到归档。CLI help/version 另在空 `/tmp` home 中重放，生成路径为空，见 checks.json。

## 完成条件核对

1. 卡上原始计数命令退出 0，输出 `codex idle other 1`；数量少于 10，三状态覆盖缺两项：**未通过**。
2. R6 未实际触发批准；各结论已有标签、argv、时间与原始输出：**未完成**。
3. 中文报告已保存；对 T-075 的影响是**先停下**，不擅定新设计。Claude 认证方式、预计 12–14 个主 turn / 建议上限 16 见 needs-decision，未获批准。
4. status 是 **Problems (0)、Stale living docs (1)**，退出 1。新增报告触发 findings/README.md 索引 stale；该文件超出卡的“仅新增一份报告”边界，已交主控处理，未自行修改。不能把它写成完整 PASS。

任务卡明确本事实报告不另开独立审查，由执行主控核对原始记录；本轮未开 reviewer，也没有独立验收 PASS。ticket 保持 open、验收框保持 unchecked，Resolution 写待主控关闭。

中文与标记字符已回读，UTF-8 无 BOM、无替换字符；Python AST、Node 语法与 JSON/JSONL 解析检查通过。全量 staged diff-check 报原始终端流中的 CR/padding 为 trailing whitespace；原始字节保留，不清洗。排除两份 pty.raw 后单独核对源文件、报告与结构化记录的空白错误，结果见 diff-checks.json。这些仅是交付文件检查，不替代未完成的真实批准与注入覆盖。blocking issue `20261010T195439Z-worker:s12-t074-issue-001` 已经 scripts/inbox 发给 triage，收据在 issue-receipt.json；收件箱条目由执行主控登记入 Git，本 worker 不把共享收件箱一起提交。

## 产物与重新生成的命令

只读分析可重放，不新增模型调用：

```sh
python3 -B evidence/2026-10-10-batch12/T-074/analyze.py --label replay-01
python3 -c "import json,collections;c=collections.Counter((r['cli'],r['state'],r['outcome']) for r in map(json.loads,open('evidence/2026-10-10-batch12/T-074/r7-injections.jsonl')));[print(*k,v) for k,v in sorted(c.items())]"
python3 /Users/luckye/Documents/SKILLS/project-map-skill/project-map/scripts/project_map.py status --root .
```

checks.py 保存本轮上述计数/status 与两个 CLI help/version 的 argv、完整输出、退出码。已有检查输出不会覆盖；若重做，先由主控指定新的证据标签或目录。

真实重放入口（**本轮已停止；需主控批准新实验后才执行**）：

```sh
python3 -B evidence/2026-10-10-batch12/T-074/probe.py launch NEW_LABEL
python3 -B evidence/2026-10-10-batch12/T-074/probe.py status NEW_LABEL
python3 -B evidence/2026-10-10-batch12/T-074/probe.py request NEW_LABEL --json '{"op":"inject","state":"idle","text":"⟦主控 #1⟧ 中文编码探针一。只回复收到，不调用工具。"}'
```

host 自动保存 launch/process、输入登记/写入、终端 raw/控制序列与 native-events；notify.py 保存通知。停止使用 request 的 `op=stop`，必须先核对自己启动的身份；`archive.py NEW_LABEL`保存原生记录、规则、turn 状态并删除自己创建的完整 home，不复制凭据。`analyze.py`将本轮归档用户消息与登记逐字比较，生成 r7-injections 与 analysis；没有模拟 CLI 或自造成功消息。

交付提交通过 Git 记录确定，不在本文提前填入未产生的 SHA；终端回执绑定实际提交。新决定见 [needs-decision-01](needs-decision-01.md)。
