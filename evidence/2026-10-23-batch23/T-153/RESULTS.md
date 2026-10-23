# T-153-1 / a1：交付测试迁移

状态：**INCOMPLETE**。02、03 均取得有效通知变异红态，但绿态分别被独立 reviewer 指出 oracle 缺口。第四轮已完成全合同本地扫查，两份 oracle 均拒绝 151 个变异、接受两个正对照；完整绿态及新候选独立审查仍待 04。若第四轮仍发现新的 oracle 缺口，按主控 #15 停下交构思主控，不继续循环。

分支 `exec/t153`，起点 `b058e3a7585ccc85df190e90c01b52756c9d076e`。唯一修改的测试为 `workbench/tests/run_worker_delivery.py`；没有新增辅助模块，没有修改产品代码、共享基类或其他测试。

## 检查清单与改动

逐条原断言、判定、新期望与来源见 [INVENTORY.md](INVENTORY.md)；原始 assert 文本及命令清单见 [pre-edit-inventory.json](pre-edit-inventory.json)。该清单在修改测试前生成，静态诊断不是产品红态。

1. 删除唯一已删命令 `pane_release` 的调用（T-127，主控指出的 `282906b9e`）；仍观察领导进程，首条任务由原生 ready 自动放行。共享基类保持原样。
2. 按 T-118 用独立执行的安装 CLI `--version` 核对 Tool 尾注，保留其余八项尾注逐字核对，以及实际 turn_context → delivery → 尾注的模型/强度检查。
3. 按 T-141 将原生 sandbox_policy 的网络期望从 false 改为 true；保留 model 与 approval_policy=never。没有从当前运行结果取期望。
4. 按现行 spec §3.5–7、T-070/T-072，verify 后等待新的 reviewer、候选绑定报告及 review_reclaimed，再带 score-file 集成。仍检查 G/C/M、双父 merge、主分支回读、host 文件及独立 oracle。
5. 按 T-123，首次 card_save 与 create 都带同一 --project B-fixture；卡号使用符合来源 ticket 序号约定的 T-153-1。此后使用 create 返回的完整 task id 调用门禁、注入请求并核对尾注；回放检查绑定同一个 launch 的 delivery，不再要求旧全局键 `id:delivery`。全路径逐项核对见 [IDENTITY-AUDIT-02.md](IDENTITY-AUDIT-02.md)。
6. 保留错误身份/不完整请求拒绝、status/issue 转交、交付只处理一次、真实两个 worker 回合、单批单通知、原生通知文本只出现一次、无审批等待、queue 为空、独立 diff 指标。
7. 收据回合仍不得调用工具；额外要求其 task_started/task_complete 区间完整，在区间内检查所有 function_call/custom_tool_call，避免工具记录缺 turn_id 时空匹配。
8. 运行接口改为 `--summary <新路径>`，拒绝覆盖。支持 `--revision` 的隔离源码与 `--mutant repeat-feedback`，均不修改 checkout 产品源码。summary 中记录候选版本、目标版本/变异、命令、授权和原始现场路径。
9. 旧累计 turn-budget 和已不存在的早期决定05不再充当授权。主控运行时显式给当前授权文件；每场 worker 最多两回合、reviewer 最多两回合，不重试。模型 `gpt-6.1-sol`、high、普通速度，完整 argv 在运行现场保存。
10. 根据 AGENTS.md 的内置盘构建裁定移除旧的挂载前置条件。原始夹具、数据库、长日志留在 /tmp，不进入仓库；停止与隔离 home 删除仍经现有退出确认辅助函数。主控另按 T-088 归档，本次未作外置盘归档。

## 已运行

[local-checks-01.json](local-checks-01.json) 保存精确命令、退出值及输出；原始夹具在 `/tmp/t153-local-7hqzrlbo` 和相应测试报告指向的 /tmp 目录。

| 检查 | 结果 | 范围 |
| --- | --- | --- |
| test_relay_cli.py | PASS，exit 0 | 真实 CLI 将 submit/status/issue 写入请求文件，无后台替身。 |
| test_relay_core.ts | PASS，exit 0，failure=null | 请求重复、错误身份、不完整、in-flight 不重执行及追加式记录；只证明 relay 层。 |
| test_hook_turn_facts.py | PASS，exit 0，5 场 | 真实 Git hook；包括不同请求模型、最新回合、辅助会话忽略与缺上下文。 |
| Python compile、--help、zsh -n、git diff --check | PASS | 语法与接口检查；不能替代完整链路。 |
| session 开始 project_map status | PASS，Problems 0、stale 0 | 初始地图健康；结束读数另存 status-end.txt。 |

## 待主控沙箱外运行

首轮 [outside-01-JVDho4I0/summary.json](outside-01-JVDho4I0/summary.json) 由主控运行：两场均在 card_save 因 unknown_task 失败，0 模型回合；三项相关回归均 exit 0。首轮输出保持原样，不当作产品红态。

02 的 [summary.json](outside-02-18rhLiEc/summary.json) 已有 retained_check_red=true；绿态在 reviewer 报“需修复”后结束，未集成。原始拒收保持原样，提取的报告见 [review-findings-02.json](review-findings-02.json)。该判断有效，不是产品或流程缺陷。

03 的 [summary.json](outside-03-Ad2MYLoU/summary.json) 同样 retained_check_red=true；绿态 reviewer 发现“只校验第一行”仍通过 24 项，报告见 [review-findings-03.json](review-findings-03.json)，原拒收保留。

运行新的 [RUN-OUTSIDE-04.sh](RUN-OUTSIDE-04.sh)，显式传入主控对新一轮真实回合和启动 hook 的授权文件；不复用已执行的授权：

```zsh
zsh evidence/2026-10-23-batch23/T-153/RUN-OUTSIDE-04.sh /绝对路径/本轮授权.md
```

04 先核对 MUTATION-SWEEP-04.json 的逐类通过结果，并直接比对当前 ORACLE 与实际被测快照 MUTATION-ORACLE-04.py 的完整文本；本地扫查或文本核对不通过时不启动模型。随后做零模型注册检查，重跑通知变异、绿态及三个相关回归，不复用旧候选结论。每次建新的 `outside-04-XXXXXXXX/`，保存各场 JSON、命令、输出、实际回合核对和总 summary。两场最大预留仍为 8 回合（每场 worker ≤2、reviewer ≤2），按 02/03 轨迹预计需 5 回合，实际以新现场为准；失败不重跑，不进入第五轮。新预算与启动 hook 由主控另写授权，本 worker 未启动 04。隔离规则保持原样。

变异只在 /tmp 源码副本移除“回放不再次反馈”的条件。有效红态必须同时满足：exit 1、NO_GO、contract_failure、failure_id=STOP-BATCH-ONE-NOTICE、两个真实 worker 回合已完成、隔离 home 已删除。启动、CLI 用法、超时、未分类断言或清理失败均不计红态。02 已满足此判据，但不能把它上调为新候选完整通过。

独立 behavioral-acceptance-review 需由主控对冻结候选和沙箱外结果安排新的只读审查；worker 不把自查写成独立结论。没有修改产品异常处理或添加产品 fallback/兼容路径。

## 主控 #11 后的注册验证

精确命令和现场路径分别见 [registration-02.json](registration-02.json)、[registration-03.json](registration-03.json)、[registration-04.json](registration-04.json)。完整诊断见 IDENTITY-AUDIT-02：首个尝试在 /bin/ps 被沙箱拒绝；第二个尝试揭示卡号缺序号；第三个已通过真实 card_save/create/status，检查完整 id=`B-fixture+T-153-1`、尚无 attempt/candidate，0 模型回合。三次最终状态都是 BLOCKED（进程退出核对缺权限），不是完整运行 PASS。各自原始 raw/commands.json 和 stop.json 保留在 summary 指向的 /tmp 目录；RUN-OUTSIDE-02 会保存新的清理核对记录。

--setup-only 对完整交付路径只加一个分支：注册成功后结束；else 内原有交付、审查、集成和保留断言顺序不变。注册模式不复制 auth.json、不派发、不安装原生会话 hook。

## 02 实际使用的真实回合

通过 [COUNT-OUTSIDE-02.py](COUNT-OUTSIDE-02.py) 核对停止后的 SQLite 副本，并与 all-events-before-stop.json 交叉比较；只计每个 launch 绑定的主原生会话的唯一 task_started/task_complete，对照 turn_submit_intent，三者一致。逐个 turn id、launch/native session 与现场路径见 [turn-count-02.json](turn-count-02.json)。

| 02 场次 | worker | reviewer | 合计 |
| --- | --- | --- | --- |
| registration | 0 | 0 | 0 |
| repeat-feedback | 2 | 0 | 2 |
| green（需修复） | 2 | 1 | 3 |
| 总数 | 4 | 1 | **5** |

02 最大预留 8，算术余量 3；授权 02 限一次运行，余量不自行用于 03。这里统计的是原生任务回合，不是单回合内的模型 API 请求、工具调用或 token 成本。重算命令：

```zsh
python3 -B evidence/2026-10-23-batch23/T-153/COUNT-OUTSIDE-02.py --run evidence/2026-10-23-batch23/T-153/outside-02-18rhLiEc --summary /tmp/t153-turn-count-new.json
```

## 主控 #14 后的 oracle 补强

期望仍来自原夹具卡，未从候选输出来抄答案；原五组用例保留，新增缺失字段、非整数 minutes 和非法 name，合计 24 组。每个非法输入同时要求 normalize 抛指定 ValueError、实际 CLI 退出 2 且错误 JSON 精确相等；所有成功和错误输出必须恰为一行。外部 oracle 与仓库 acceptance.py 仍由同一个 ORACLE 源生成。reviewer 提示词、mutation_checks 和交付断言均未修改。

[CHECK-ORACLE-03.py](CHECK-ORACLE-03.py) 只复制 02 独立交付候选的 src 到新的 /tmp 目录，分别用两份 oracle 跑正例与八个已知坏实现：缺失 minutes 默认 0、浮点/字符串/null minutes 强制接受、bool 校验删除、name 强制转字符串、成功多行 JSON、错误多行 JSON。保留原候选和 02 reviewer 的报告，不重新生成或改写旧证据。

- 修改前：[oracle-before-03.json](oracle-before-03.json)，NO_GO、exit 1；两份旧 oracle 都放过缺失/浮点/字符串/null minutes、name 强制转换和成功/错误多行 JSON 七个变异；原候选通过，已有 bool 检查能拒绝其变异。
- 修改后：[oracle-after-03.json](oracle-after-03.json)，PASS、exit 0；两份新 oracle 都接受同一原候选，报告 24 cases passed，并拒绝全部八个变异（16 次拒绝）。只证明夹具 oracle 的这组反事实，不替代 03 的真实交付验收。
- 本轮本地工作新增模型回合：0。

复现时请使用新的 summary 路径；旧 oracle 加 --oracle-revision 55acb1b612ab29490159894d4e93e5a0a8db063e：

```zsh
python3 -B evidence/2026-10-23-batch23/T-153/CHECK-ORACLE-03.py --candidate /private/tmp/a2a-B-zoe_ikff/state/worktrees/B-fixture/T-153-1-a1 --summary /tmp/t153-oracle-new.json
```

## 第四轮：全合同本地变异扫查

先写 [MUTATION-PLAN-04.md](MUTATION-PLAN-04.md)，再用同一个 sweep 对旧 24 项 oracle 取得 [MUTATION-BASELINE-04.json](MUTATION-BASELINE-04.json)（NO_GO），然后改 ORACLE。新结果为 [MUTATION-SWEEP-04.json](MUTATION-SWEEP-04.json)（PASS）；原始报告保留在 MUTATION-SWEEP-04-raw.json，最终报告只附加实际副本 diff，不改检查结果。输入、命令、变异补丁、每个字段/非法值/行位置及两份 oracle 的结果均在 JSON 中；被测 oracle 原文固定为 MUTATION-ORACLE-04.py。

| 合同类别 | 变异数 | 新 oracle 杀死结果（每个分别跑外部 oracle 与 acceptance.py） |
| --- | --- | --- |
| minutes 19 类、name 14 类非法输入 × 首/中/末 | 99 | 99/99；每格还先运行 CLI 证明该变异确实接受了本应拒绝的输入。 |
| 两字段分别仅检查首行/中间行/末行 | 6 | 6/6，覆盖 03 发现的结构性缺口。 |
| 去空白、合并、排序 | 8 | 8/8；含单侧 trim、内部空格被删除、合并覆盖、遗漏/倒序/忽略大小写排序。 |
| total、空数组、JSON 数值类型 | 6 | 6/6；包括 False==0、0.0==0 不能再蒙混通过。 |
| duration 格式与进位 | 5 | 5/5；分钟无补零、小时多补零、错误除数、无进位、分钟不取余。 |
| 0/59/60/61/119/120/125/6001 各边界 | 8 | 8/8。 |
| normalize 异常类型、精确消息、返回错误对象 | 6 | 6/6。 |
| CLI 退出码、错误 JSON、多行/额外 stdout、只向 stderr 输出 | 13 | 13/13，成功与错误分别覆盖。 |
| 合计 | **151** | **两份 oracle 各运行 151 次，共 302 次拒绝**。 |

另有两个正对照：03 原候选不改动、CLI 仅在 stderr 写诊断；两份 oracle 均通过，分别报告 116 cases passed，共四次成功。stderr 控制例避免把“结果不读 stderr”误写成“stderr 必须为空”。所有变异源码先编译并独立导入；只有 oracle 明确 AssertionError、exit 1 才计杀死，导入失败和超时不计。所有副本只改变 src/normalize.py 或 src/report.py；生产源码、审查提示词、mutation_checks 与原有交付断言未修改。

旧 oracle 的基线中，99 个逐格绕过与六个单行校验变异全部存活；还漏掉内部空白、大小写排序、数值类型和部分 duration 边界。基线报告保留了未分类异常，不把非断言失败误计为成功杀死。新 oracle 仍保留原五组输入，补成 116 组；每个非法值都在首/中/末，成功与错误都跑实际 CLI，校验 ValueError 类型/消息、退出 0/2、精确 JSON、单行 stdout 且无附加输出。

复现命令（零模型回合，summary 使用新路径；重做旧基线时加 --oracle-revision 6d9bca18cf99b2c88acd8cabc9c120f503c6d337）：

```zsh
python3 -B evidence/2026-10-23-batch23/T-153/MUTATION-SWEEP-04.py --candidate /private/tmp/a2a-B-m884crxt/state/worktrees/B-fixture/T-153-1-a1 --summary /tmp/t153-sweep-new.json
```

### 机械验证边界

| 合同项 | 能证明什么、不能证明什么 |
| --- | --- |
| 字段合法性、聚合、排序、total、duration、异常、CLI 协议 | 本地已证明列出的有限 JSON 等价类和 151 个已知错误实现被区分。不能证明所有字符串、任意大小整数、任意长度列表或任意错误程序都已穷尽；也不替独立 reviewer 判断完成条件充分性。 |
| 双字段同时非法、非法顶层/行容器、坏 JSON stdin | 卡片没有规定这类输入的错误优先级或完整行为，本轮不新增期望。NaN/Infinity 不属于标准 JSON 输入。 |
| 只改两个文件、验收文件不改 | [SCOPE-03.json](SCOPE-03.json) 已独立核对 03 候选 Git diff 恰为两个允许文件。04 仍由真实 verify 的路径/oracle 门禁机械检查；reviewer 的无 Git 副本与函数 oracle 不能独立证明历史或瞬时文件写入。 |
| 不访问网络、不启动子 agent、不做范围外活动 | 角色卡、运行参数和已采集事件能提供约束及观察，函数/CLI oracle 不能证明整个宿主机上从未发生这些活动；本次不新增监控或把未知报通过。 |
| 模型判断与审查通过 | 本地扫查不等于真实 reviewer 已通过。第四轮若仍以新 oracle 缺口拒收，停止并交构思主控裁定绿态判据，不能继续补到模型同意。 |

### 真实回合累计

[turn-count-03.json](turn-count-03.json) 用停止后的数据库与停机前捕获交叉复核：03 注册 0、变异 worker 2、绿态 worker 2 + reviewer 1，合计 5；与 02 的 5 累计 **10 个真实原生回合**。01 与本轮本地扫查均为 0。旧授权只限各自那一次运行，算术余量不自行复用。

## 范围外上报

已通过 `scripts/inbox send` 上报 `20261023T193353Z-worker:b23-t153-issue-001`（非阻塞）：被索引的 native-cli spec §5:118 仍写旧 socket/关网络契约，与 T-075 最终文件交付通道及 T-141 网络裁定冲突。正文见 [issue-spec-network.md](issue-spec-network.md)。本任务依据已授权的 T-153/T-141 继续，未修改规格。收件箱条目留在本 worktree `.project-map/inbox/`，不纳入允许路径以外的测试交付提交。
