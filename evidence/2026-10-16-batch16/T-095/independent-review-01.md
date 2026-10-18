STATUS: PASS

TARGET: `bef1b55e331b7c078820b908a3eba17feea478e7`；产品 `faa2b9b3b9ac6195012fc8ea88e6e6d73dee2bf4`；起点 `3c9016d0230223945f0e16543b230a047c2ad032`。T-095 / a1，独立 reviewer，2026-10-18。

EVIDENCE:

- **结论口径。** PASS 限于本票与用户裁定 B 的完成条件：修前没有独立等待状态；有机械标记时两形态能显示“等待主控回答”并带身份；普通 working 不误报等待；跳过及回答后离开等待；地图无问题。第 4 回合提供两形态真实绿态，第 5 回合提供真实已回答及离开等待证据。没有将“必须 idle / native clear / 解析出 resolved”加入 B 的验收，也没有宣称所有折叠待答都能检出。
- **独立标准。** 直接读取主 checkout 的 reviewer 角色卡，以及 main `0e92f78ec6824265cdfcbb9387ba4b454d7eee7f` 的 T-095 原文和裁定；同时读取 MAP、CONTEXT、intent、任务卡、REVIEW-REQUEST、RESULTS、DIRECTION、三份 FROZEN 和 READY。答案来自 ticket、“识别不到报未知”的要求、本次用户指定的双来源规则及原件；实现者报告和测试只作定位与补充证据。
- **冻结与范围。** 用 `git show`、`git diff 3c9016d02 bef1b55e` 阅读产品、测试、直接调用者及记录模块。非 evidence 变更仅 `scripts/agent-status`、`scripts/native_questions.py`、`scripts/test_agent_status.py`。`git diff faa2b9b3 bef1b55e -- scripts` 为空。审查开始和结束 HEAD 均为目标完整 SHA；审查前工作区干净。
- **本次执行。** 0 个真实模型回合、0 次真实 Herdr 操作、0 个子 agent。副本由 `git archive` 建立，不建 worktree。候选及原件未改动；派生产物全部保留在 `/tmp/t095-independent-review-01-s9de0cug/`。仓库只新增本报告和 `REVIEW-OUTSIDE-01.sh`。

五个真实 run 的根目录均为 `/Volumes/WD-Elements/a2a-evidence/2026-10-16-batch16/T-095/`。直接核对 `run.json`、命令 argv / stdout / exit、启动记录、原生日志头与事件，没有把仓库中的派生输入 JSON 当成原件。

| 原件目录 | 文件数 / 字节数 | 当时版本与现场投影 | 当前冻结候选独立回放 |
| --- | --- | --- | --- |
| `red-20261018T110936Z-f4d263d1` | 156 / 148251 | 起点 3c9016d02；无新入口、无新状态投影；两形态原值均 blocked | 折叠 unknown；展开等待；skip 后 unknown |
| `green-20261018T125458Z-76e72ee1` | 169 / 163147 | 504abc34a；两形态及 skip 后均 unknown | 等待 / 等待 / unknown |
| `green-independent-20261018T131803Z-9e55a235` | 225 / 197119 | 96464ecf4；两形态及 skip 后三阶段均 unknown | 等待 / 等待；skip 后即时、30 秒、60 秒均 unknown |
| `green-anchor-independent-20261018T135446Z-2626001e` | 225 / 196652 | faa2b9b3b；等待 / 等待；skip 后三阶段 unknown | 与现场状态、原因一致 |
| `answered-20261018T165159Z-ee1a8372` | 225 / 178811 | 66b824a5b，产品代码与 faa2b9b3 相同；unknown / 等待；A 后三阶段 unknown | 与现场状态、原因一致 |

当前候选对前三份原件的回放属于回归，不能改写它们原版本的失败。第 4、5 回合在产品冻结后生成；没有据这两份原件修改产品。第 2 回合曾先展开再折叠，第 4、5 回合的首次折叠前未展开是操作者声明，不能补称自动按键日志。

独立回放器直接按原始命令的 `--format text` 选择 visible / detection 字节，用明确的假 Herdr 运输这些原件，再以子进程调用归档候选的真实 `scripts/agent-status`。四个有启动记录的 run 仅在 /tmp 重定位 native_store 和索引路径，保留 worker、launch、pane、terminal、UUID、cwd；red 没有原始 launches，只能由原始 start 回复和日志头重建，并明确标记为重建记录。日志按现场投影记下的 native.bytes 截取；red 无此截止点、answered 答后三项也没有，只能使用最终归档，不能声称精确复原当时落盘边界。外层读屏也不能代替未单独保存的产品内部每次读屏。

独立回放 **21 项 PASS**；另有 7 项独立正反判据全部通过，以及 1 项“真实普通 working 屏幕 + 发问前日志前缀 + 明确运输替身”的组合检查通过。候选先通过，再构造变异。所有入口调用只允许 get/read，核对未改启动记录与日志副本。

**红态 PASS。** 起点没有 `scripts/agent-status`，对起点 scripts 搜索独立状态值和中文标签均无匹配。另审读并执行 `replay-before-status.py`，其所有供应商/Herdr 子进程均替换为原始回复，只使用新建假凭据；原采集器 38 个命令按顺序完成。折叠 command 020–025、展开 026–031 的原始 stdout 保持一致，原值分别为 blocked / blocked，无“等待主控回答”。这是 B 要求的红态，不是将入口不存在的启动错误当作红态，也不补称复现了 10-17 的 working。

**绿态 PASS，覆盖限制单列。** 第 4 回合 command 021 / 023 两屏第 3 行均有 `? 1 question · 18s`；028 / 030 两屏第 8 行均有同条 `⌃] skip`、`⇧→ main prompt`。前后 get 均 blocked，实际投影 026 / 033 都为等待，exit 0，身份完整。第 5 回合折叠 command 021 / 023 只有 Working 和普通输入框，022 的 ANSI 原件也无 question 锚点；不是候选漏匹配了已有计数标记。此样本按规则只能 unknown，属于**屏幕来源未提供标记的识别覆盖限制**。不能进一步断言是 Codex 渲染、Herdr 读取还是时序导致，也不能估计出现频率。

ticket 同时明确要求“识别不到报未知”。因此第 5 回合没有推翻第 4 回合已经取得的两形态正判，也没有授权只凭 blocked 或 native pending 判等待；本次判两形态绿态成立。这个 PASS 不包含“所有默认折叠问题均可自动发现”的更强承诺，单看第 5 回合折叠也绝不能写成等待正判成功。

**回落 PASS。** 第 4 回合 skip 后 040 / 047 / 054 均 unknown / screen_native_conflict，前后 Herdr 为 working，屏幕无面板；第 5 回合 A 后 040 / 047 / 054 均 unknown / native_user_response_uncorrelated，前后独立采集的 Herdr 为 done，屏幕为 Worked for 59s，无面板。两次都没有卡在等待。该结论同时依赖原件身份与实际 UI，不是只见一个 unknown 字符串就宣称真实已回答。

第 5 回合 `native-bound.jsonl` 的机械关联独立核对如下：

- 第 12 条请求 call 为 `call_678d50e5fcee4210b64a0cdfe24fd617`；第 15 条只是 accepted 回执。
- 第 24、25 条的固定 `send_user_message_question_reply` 包围块内是 JSON，answer 为 A；对 questionItemId 作 JSON 解码，得到 `["request_user_input_async","call_678d50e5fcee4210b64a0cdfe24fd617",0]`，对应唯一请求及第 0 个问题。第 25 条的 thread、turn 与请求一致。
- 第 27 条为公开 ANSWER_RECEIVED，第 30 条同 turn task_complete。这里确有应答与 turn 完成，不能写成“无应答事件”；turn 完成本身也不替代问题关联。
- `native_questions.py:130` 将此 UserMessage 记作未关联，`:169` 抛 native_user_response_uncorrelated；`agent-status:203` 因此在读屏和完整 identity 输出前退出。其后状态 unknown 符合 B。支持该机械格式是可改进项；**不是本票裁定 B 所禁止的“答完仍等待”缺陷**。原生解析完整性仍未完成，不能把本次 PASS 写成 native clear / resolved 已实现。`:131` 的旧注释也不能用来否认原件里的 call 关联字段。

**普通 working 反例 PASS。** 阅读原始 `ordinary-working-agent-before.json`、after、visible、detection：前后 s16-t095 / wF:p68 / terminal / native UUID 一致，原值 working，屏幕底部为活动行、空输入框、模型栏、快捷键栏，无等待锚点。独立组合检查输出 working / current_activity_frame；运输身份和无 pending 日志是明确组合，未冒称新的真实运行。既有合同的 thinking、command-context、真实普通屏幕、仅 raw working 不足以正判等检查也通过。外置盘既有 ordinary 真实入口输出为 working；它是历史补充证据，不代替本次候选检查。

**身份与副作用 PASS（在可核对范围内）。** 对五个 run 的前后 get、原始 start、日志头逐项核对 worker、launch、pane、terminal、native UUID 与 cwd；red 的记录重建限制已单列。四个归档启动记录完整；第 5 回合答后产品 identity=null 是提前返回的缺失，原始外层采集身份一致，二者分开记录。产品按 launch 定位，只读绑定 UUID 的索引和日志头，不按文件名猜；重读 launch、两次 live 状态代次及两次 native 状态均有保护。错 worker、pane、terminal、cwd、native 更换和记录更换均有合同反例。

候选 diff 没有改 Herdr、dispatch、launcher、workbench、gates 或全局配置。生产入口只有 get/read、只读 SQLite 与文件；没有状态写回、自动答题或后台服务。探针历史代码写的是隔离 HOME，通过每会话 argv 配置；审查本身没有读取用户 auth 或操作全局配置。正则只解析 CLI 活动文案、快捷键及计数标记，不解释问题正文、选项内容或用户意图。

**结构审查 PASS。** 按 design-integrity-review 核对可达调用、归属、架构和比例：

- 唯一生产入口承担“launch → 真实只读来源 → 状态投影”这条 Tracer bullet；dispatch 原本没有监视循环，本次不另添第二套投影或状态存储。
- 按 Deep modules，native_questions 的小接口隐藏索引、日志身份、完整性和事件关联，具有实际复杂性；不是单纯转发包装。`isolated_session` 只服务隔离探针的初次绑定，不是生产读取时的猜测回退。
- 超时、输入/来源异常与冲突由状态读取边界输出 unknown、诊断原因及 exit 2；没有吞异常后返回成功、自动重试、兼容旧布局的平行路径或以空结果伪造 clear。未识别 A 应答是明确暴露的功能限制，没有被成功输出掩盖。
- Ubiquitous language 保持“等待主控回答”及 waiting_controller_answer。旧候选快照、探针和回放器均在 evidence 中，不是第二个产品入口。
- scanner 工作区扫描返回空列表，但冻结提交已在 HEAD，不能据此证明完整提交无问题；以上判断来自对基线完整 diff 与调用链的人工审读。

既有冻结合同另独立执行：**85 项 PASS，exit 0**。这只是补充证据，独立判据没有引用其生产常量或答案。项目地图开始及结束均 **0 problems / 0 stale living docs**。

主要复核产物：

| 产物（均在 `/tmp/t095-independent-review-01-s9de0cug/`） | 内容 |
| --- | --- |
| `review_checks.py`、`review-results.json` | 独立原件读取器、21 项回放、7 项正反判据、3 个变异的逐项结果 |
| `checks/` | 各次真实入口 stdout、stderr、调用记录、原始输入副本、临时索引与启动记录 |
| `boundary-facts.json` | 五个 run 的文件数、字节数、历史投影、版本、身份及 A 关联字段 |
| `reports/before-status.json` 及 stdout / stderr / command 文件 | 修前采集器的 38 条原件回放 |
| `reports/independent-ordinary.json` | 普通 working 独立组合检查 |
| `reports/candidate-contract-85.json` | 本次候选合同的全部 85 项结果 |
| `reports/map-final.*`、`head-final.*`、`product-unchanged.*`、`product-from-faa2b9b3.*` | 状态、冻结身份和产品未变检查 |

实际执行命令（均不连接真实 Herdr / 模型）：

```sh
PYTHONDONTWRITEBYTECODE=1 python3 /tmp/t095-independent-review-01-s9de0cug/review_checks.py
PYTHONDONTWRITEBYTECODE=1 python3 evidence/2026-10-16-batch16/T-095/replay-before-status.py --report /tmp/t095-independent-review-01-s9de0cug/reports/before-status.json
PYTHONDONTWRITEBYTECODE=1 python3 /tmp/t095-independent-review-01-s9de0cug/candidate/scripts/test_agent_status.py --report /tmp/t095-independent-review-01-s9de0cug/reports/candidate-contract-85.json
python3 /Users/luckye/Documents/SKILLS/project-map-skill/project-map/scripts/project_map.py status --root .
```

前三条须在新目录 / 新报告名复现，禁止覆盖本次记录。独立回放器的 HERE 是所在目录；复现时将它复制到新的 /tmp 目录，并将下列 `git archive` 解到该新目录的 `candidate/`，即可用相同入口重建全部原件回放及变异：

```sh
git archive bef1b55e331b7c078820b908a3eba17feea478e7 scripts/agent-status scripts/native_questions.py scripts/launch_records.py scripts/record_io.py scripts/test_agent_status.py evidence/2026-10-16-batch16/T-095
```

FINDINGS:

- 没有确认的、违反本票与裁定 B 的必修缺陷。第 5 回合折叠缺锚点是可观测覆盖限制；应答格式未解析是原生投影的改进项，二者均不能写成已解决。
- 不采纳 worker “完整投影不通过，因此整票必为 NO_GO”的额外门槛；也不把 worker 旧 NO_GO 改成历史 PASS。本报告是按最新验收标准对冻结候选独立作出的新结论。

COUNTEREXAMPLE:

候选先通过全部独立判据，再在 /tmp 的归档副本中各改一处。没有改测试答案，三种错误都以业务状态断言 `business_assertion=false` 被拒，非依赖缺失、崩溃或空集合。每个变异仍通过两个正常正判，说明检出不是把入口整体破坏。

| 变异 | 单处改动 | 被拒的独立场景及结果 |
| --- | --- | --- |
| `mutant-one-sided` | agent-status:226，锚点 AND blocked 改为 OR | 只有 blocked、两屏冲突、只有屏幕锚点三例，本应 unknown，却等待 / exit 0；均拒绝 |
| `mutant-foreign-worker` | agent-status:100，跳过 name 不相等检查 | 同样真实面板，get 的 worker 改为 another-worker；本应 unknown，却等待 / exit 0；拒绝 |
| `mutant-ignore-native-conflict` | agent-status:242，将 pending 分支条件改为 False | 第 4 回合真实 skip 后 native pending 与 working 屏幕冲突；本应 unknown，却 working / exit 0；拒绝 |

每个副本跑相同 7 项，完整 argv、实际 stdout 与失败判据位于 `review-results.json`、`checks/<变异名>/`；变异源码保留在同名目录。完成条件能够拒绝这三种明显错误实现。

LIMITATIONS:

- **无标记的折叠待答只能 unknown。** 第 1、5 回合有此真实样本；第 4 回合正判不证明通用检出率。若目标变成默认折叠必检出，需要另行确定可观测来源和验收，不得在本候选里用 blocked 或 pending 单独补判。
- **跳过无解决事件。** 第 4 回合从 89498 字节 / 20 条增长到 96693 字节 / 27 条后，仍只有问题 accepted、sleep 返回等后续记录，没有可关联的答案或 skip 解决事件；unknown 是保守结果。不能称 native 已解决。
- **回答存在但格式未支持。** 第 5 回合最终 99578 字节 / 30 条，答案关联与 turn 完成已核实；现解析器拒绝此格式，答后三项未读屏、identity=null。按 B 回落通过，完整原生解析仍未完成。同一日志未新增可识别解决记录时，后续读取仍可能 unknown；未验证后续提问的恢复。
- **3 秒超时根因未定。** 已直接读取外置盘 `offline-native-anchor-repair-20261018T134759Z/reports/contract-final.json` 的 working-command-context，以及 archives-final.json 的 archive-red-expanded：时间分别为 13:41:32.542819Z、13:41:32.547032Z，均首个假 Herdr get 超时，unknown / herdr_timeout / exit 2。不能据同时发生归因并发，也不能补称真实 Herdr 生产超时。本次串行通过不证明根因解决。生产每次 get/read 默认 3 秒，超限会暂时遮住真实等待，调用方须保留 unknown 及诊断。
- **证据层级。** 本次是候选真实进程入口对已归档真实边界的回放，以及少量明确组合/变异；不是新真实模型运行，不证明负载可靠性、收益或所有 UI 布局。身份缺失与现场截止不可得部分如上单列，没有以回放代替原现场。
- **审查工具失败已保留。** 首轮独立读取器误将 visible ANSI 命令覆盖了 text 命令，导致 unreadable_screen；失败输出与首版读取器保存在 `checks-ansi-misselection/`、`review_checks-first-ansi-misselection.py`。修正为仅选 `--format text` 后重新取原件运行；这不是产品红态，也没有改产品使其通过。
- 本次 /tmp 原件、副本和失败均未删除；依 T-088 后续由执行主控归档。外置盘只读成功，无待执行的沙箱外核查，`REVIEW-OUTSIDE-01.sh` 仅记录这一事实；本审查没有申请升级、commit、checkout、reset、stash、push、submit 或集成。

RULE:

- 本次没有需新增规则的重复违约发现，不建议据此修改治理文件。若后续扩展应答解析，应以第 5 回合的真实机械 JSON 为输入，补错 call / thread / turn / 问题索引反例，继续拒绝用普通用户文本、accepted 或 task_complete 单独清除等待；这不是本次 PASS 的附加前置条件。

T-095 REVIEW PASS
