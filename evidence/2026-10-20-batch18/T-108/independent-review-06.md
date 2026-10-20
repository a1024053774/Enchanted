# T-108 第六轮独立审查（2026-10-20）

STATUS: INCOMPLETE

TARGET: `ee17cddf8c146ffb8cdaaa7d942ac610811cb915`，`exec/t108`，起点 `6411bdff8482ba47da207efa6a295a12666222aa`。开始与收尾 HEAD 一致；受审产品、测试与 Git 元数据未写入。

**指定产品行为与结构检查 PASS，未确认新的产品缺陷；整票的地图 0 问题条件仍为 INCOMPLETE。** 第五轮首答误拒与写流堵塞已在本轮独立反例和当前候选的真实 CLI／Electron 无模型原件中关闭。这里不把稀疏检出的地图缺口、未执行的补证脚本或已声明的 Codex 证据边界写成完整验收通过。

## EVIDENCE

按派发顺序读取主仓库 reviewer 角色卡、本 checkout 的 AGENTS.md、T-108 与 T-093（含 2026-10-20 版本裁定）、T-095、T-071，随后读 RESULTS、REAL-TURN-PLAN、CONFLICT-LINES 和前五轮报告。稀疏 checkout 未展开的材料用 `git show ee17cddf8:<路径>` 读取。产品用 `git diff 6411bdff8 ee17cddf8 -- <路径>`、`git show ee17cddf8 -- <路径>` 和当前提交原文核对；不把作者修复说明当作 oracle。

期望来自 ticket：结构化原生事实、未知不上调、答复写回原 PTY、唯一关联 answer、重复拒绝、每会话 hook、受管身份与门禁不变。用户原话“跑真实回合,版本不重要,以后肯定要经常更新 cli 版本的”只取代 Claude 精确发行号锁，不取消版本读取、隔离或凭据边界。用户不需要截图，本轮没有截图或录屏。

应用 project-map、evidence-first-testing、behavioral-acceptance-review、design-integrity-review 和 document-writing。按结构 skill 路由，将结构检查并入本次行为审查；没有子 agent。Ubiquitous language 沿用 launch、submission、prompt/turn、question、answer、attempt。Tracer bullet 实测经过 `Panes.signal → SQLite → 状态与问题投影 → answerQuestion → PTY 写入边界`；夹具提供的 PTY 和运行身份不算新启动 CLI 的证据。questions 模块集中承担关联、可信度、投影与按键协议，符合 Deep modules 的实质职责，没有新增浅包装层或第二门禁。

本轮临时根 **B = `/private/tmp/t108-review-06-skyothnq`**。候选和三个变异分别来自冻结 SHA 的 `git archive`；受控 hook 链接展开成普通文件，依赖复制并解引用，不建 worktree 或符号链接。Node 26.5.0、Python 3.9.6；Git 使用 `LC_ALL=C`，清除 `GIT_DIR`、`GIT_WORK_TREE` 和继承的供应商配置。完整 argv、输出、退出码在 `B/checks.json`、`extras.json`、`mutant-checks.json`、`unseen.json` 及同名 stdout/stderr；模型调用和供应商调用均为 **0**。

总脚本在 `/private/tmp/t108_review06_run.py`、`t108_review06_extras.py`、`t108_review06_mutants.py`、`t108_review06_unseen.py`。首脚本复制上一轮检查清单后，重复尝试独占创建 `stop-observation.stdout`，以 FileExistsError 中止；此前已完成的结果全部保留，没有覆盖重跑。中止后的变异与补充回归由另两份脚本完成，不把脚本中止称为产品失败。

### 第五轮反例与当前完整入口

原第五轮早到／晚到复现文件从 `/private/tmp/t108-review-05-1mrl278a/candidate/workbench/tests/` 原样复制到本轮 candidate，只替换被执行的候选版本。两者本轮均 rc=0：

```sh
B=/private/tmp/t108-review-06-skyothnq
env -u GIT_DIR -u GIT_WORK_TREE LC_ALL=C node "$B/candidate/workbench/tests/review05-early-native-confirmation.mjs" "$B/early-repeat.json"
env -u GIT_DIR -u GIT_WORK_TREE LC_ALL=C node "$B/candidate/workbench/tests/review05-late-native-confirmation.mjs" "$B/late-repeat.json"
```

- 早到：同题 PostToolUse 在第三键前确认，首答成功，仅发送“下箭头、Enter”，不再追加余下 Enter；answer 记录 1，后续 `next sentinel` 能进入原写流。
- 晚到：按键写完后再确认，首答与后续输入均成功，原三个按键保持。
- 默认合同的 **14 项作答生命周期**全部通过：还覆盖最后一键期间确认、确认后匹配 Stop、不同答案、确认后撤权／输入变化／未知、发送期间异常、记录拒绝、物理 PTY 异常、已排队输入，以及 shell 共用写流的拒绝与未知对照。
- 独立增加四个确认后反例：在原早到脚本相同位置确认后，分别设置新草稿、改变 inputGeneration、让身份检查抛错、设置持久的写入未知失败。四项均保持首答拒绝、无 answer_written；前三种普通拒绝后的独立输入可执行，持久失败后的输入无新增字节。输入、脚本、命令及结果在 `B/unseen.json`、`*-after-confirmation.json`。这里持久失败是状态边界注入；真实 pty.write 抛错及排队阻断由默认生命周期合同另证，未冒称实际 OS 写失败。

当前原生完整入口原件 `/private/tmp/t108-native-e2e-review05-01.json` 八项 PASS，fixture 为 `/private/tmp/t078-2-t108-yn32dr55`。本轮只读查询其 SQLite，launch.code_revision 与当前完整 SHA 一致，CLI 2.1.304。独立观察：

| seq | 事实 |
| --- | --- |
| 58、59 | 第一个 window_answer 收到并按原窗口 request_id／sequence 准入。 |
| 60 | 原题的 answer_intent。用户输入表只有一条关联 answer。 |
| 61、62 | 向原 PTY 写下箭头、Enter。 |
| 65 | 同 session／submission／turn／question 的原生 PostToolUse 确认“西区”。 |
| 67、68 | answer_written：confirmed=true、keys_written=2；**同一首答传输 ID 的 request_result.ok=true**。没有同 ID 的 request_rejected。 |
| 75 | 同 prompt 的 Stop 使原 submission idle。 |
| 83 | 同 launch 的后续随机 nonce 写入完成。本轮从原 trace 的指定新偏移读回了该 nonce。 |
| 87 | 后续重复作答被 question_not_pending 拒绝；它不是首答拒绝。 |

首答传输 ID 为 `8def0915-c7c9-4405-abc0-da0f365ebee1`，窗口 request_id 为 `ab3fa6ca-8a13-4093-b08e-8a5dc0fec0ab`；独立摘录在 `B/entry-answer-audit.json`、`entry-independent-verdict.json`。后续仅粘贴、不按 Enter，没有新增根模型回合。原件的退出清理、模型/供应商 0 也已核对。本轮没有另启动 Electron 或 CLI；当前 SHA 的现成完整入口原件与本轮独立反例共同支持关闭 F1-05，旧六项 PASS 不再被用作首答回执证明。

### 前四轮反例和 RULE

| 范围 | 本轮结果 |
| --- | --- |
| 第一轮缺 tool_name | PASS，`f1.json`：拒绝、保存当前关联未知事实、显示 unknown。完整无关工具仍忽略，明确旧回合／异 session／子 agent 不污染当前问题。 |
| 第二轮待答缺名、非法响应、旧答写入 | PASS，`pending-name.json`、`pending-response.json`、`pending-write.json`：问题 unknown，拒绝 answer，PTY 无新增。 |
| 第二轮 Stop 缺 stop_hook_active | PASS，`stop-active.json`：unknown、拒绝，active 保留，无完成或 transfer。 |
| 第三轮 PostToolUse 缺 cwd／transcript_path | PASS，`no-cwd.json`、`no-transcript.json`：显示和答复资格一起失效；完整对照 `complete-response.json` 正常 answered。 |
| 第三轮 Stop 缺 prompt_id | 原 `stop-no-prompt.json` 仍 rc=1：已观察拒绝、unknown、active 保留，之后旧观测脚本访问不存在的 question.status 而 TypeError。保留该异常；同输入的补正观测 `stop-observation.json` 与待答形态 `stop-no-prompt-pending.json` 均 PASS。 |
| 第三轮其他工具权限遮蔽旧问题 | PASS，`permission-pending.json`、`permission-valid.json`、`permission-missing.json`。Bash、独立 parallel-permission ID、缺工具名均撤销旧问题资格。 |
| 第四轮全部 forged-name 输入 | 五项全部 PASS：`review04-forged-name*.json`；仅名称、空参数、旧 ID 配 command／空参数、错误 ID、先有 Bash 后伪装均不能写入，unknown、answer/PTY 0。 |
| 正常同问题权限 | permission_self_full／matching_id／sending 全部 PASS。必须有完整一致的 questions，工具参数只有 questions；正常原生无 tool_use_id 的路径仍可作答。当前 CLI 原件 seq 53 也确认为该正常同题 PermissionRequest。 |

默认 questions 合同 **15 项主检查、429 项 failure_cases、14 项生命周期均 PASS**。本轮从 ticket 重建公共字段与对照清单，`B/matrix-audit.json` 核对基础网格 **350 项，无缺项、无失败**：

- 两家 CLI；PreToolUse、PostToolUse、PostToolUseFailure、Stop、PermissionRequest、UserPromptSubmit 六种事件逐项缺 cwd、transcript_path、session_id、prompt_id/turn_id。
- 工具事件额外缺 tool_name、tool_use_id、tool_input；PermissionRequest 缺 tool_name/tool_input。每项配完整当前、明确旧回合、异 session、子 agent 对照。PermissionRequest 的可选 tool_use_id 没被错误改成必填。
- 缺字段、非法 JSON／响应／时间、Stop 缺或非法 active、回答记录与逐键期间异常，均同时核对未知状态、问题资格、answer/PTY、active/prompt、无完成/transfer；后来的正常 Stop 也不能完成已不可信回合。
- 同问题权限用严格深相等作正向证明，不靠工具名或“没有反证”。完整 questions 混入 command/file_path、问题／选项夹带额外字段也有拒绝及非当前对照。
- Notification 未订阅，不能冒称已支持此提问入口；送达的未知当前事件被拒并撤销旧问题，`notification.json` 与 pending_unrecognized_hook 均 PASS。公共 envelope 在具体分流前检查。Codex PostToolUseFailure 是额外入口防守，不宣称该 CLI 实际发送它。

### 其他指定边界

| 项目 | 结论与证据 |
| --- | --- |
| 每会话 hook／语义 | Claude 的 --settings JSON 与 Codex 的 -c hooks.<事件> 注入。产品 diff 没有新增全局配置写入；初始化只作用于隔离目录。提问按结构化工具与 payload 识别，版本／控制字符／终端协议正则不是语义识别。未观察到全局写入路径。 |
| answer 与门禁 | window_answer 仍经窗口身份、sequence/request 防重和 assertCurrent；受管分支核对 current attempt/session/fence/spec/reclaimed。recordInput 经 appendUserInput 保存 form=answer、reply_to、target.request，受管输入继续派生 human_intervention。没有认领、提交、集成或锁释放旁路。真实主控原件只有一条 answer，正确指回问题和原 thread。 |
| 版本与隔离 | `version.json` 8 项、`profile.json` 4 项、`once.json` 4 项、`ports.json` 10 项、`restore.json` 22 项均 PASS。三处改动取消精确版本值，仍拒绝缺 CLI、取版本失败、空/非法/不匹配版本。O_NOFOLLOW、私有文件权限、manifest/进程身份、一次消费、auth_original_reads=1、隔离 HOME 禁写／网络／清理未被删。实际版本写入启动记录、version_probe、role_card_revision 和 facts。 |
| T-107 F2/F3 | sidebar 12 项 PASS。实际 daemon/socket/Panes/collector/SQLite/trace 的 readonly、identity 两场均 PASS，cleanup_complete=true；查询只用已保存事实，没有扫描新日志、写库或身份冲突上调。 |
| IPC | 32 项 PASS，旧 handler/bridge、窗口、iframe、历史只读、失效身份等拒绝保留，增加 answer；主进程队列拒绝后能继续的驱动合同 9 项 PASS。 |
| 合并回归 | T-078 Claude Stop／异 session、队列／中断／输入顺序、T-109 hierarchy 与 T-111 flow 均 rc=0/PASS，见 extras.json。 |
| Codex | hook 原件回放 5 项 PASS。来源是已安装 0.163.0 CLI 对本地假 API 的实际结构化 hooks；本轮没有活 Codex 或供应商模型。异步阻塞与多选写回仍未验证，README/计划已写明，界面不自动写回未验证协议。 |

## FINDINGS

没有新增已确认的可达产品缺陷。第五轮 F1-05 在本轮范围内关闭；前四轮指定反例未复发。

结构检查重点是 `panes.ts:758` 的共享队列、`:1181` 起的作答生命周期、`questions.ts:156` 的确认匹配及 `main.ts:108` 起的主进程队列。普通失败只释放排队位置，原调用者仍收到拒绝；实际物理写失败先记录 pane.failed，再重抛，队列入口和逐键检查会阻断后续字节。成功分支要求 intent 之后的同题原生答案严格相同，并保留身份、输入、回合与生命周期核对；不是吞掉 question_input_changed。匹配 Stop 已完成同一 submission 的收尾分支有精确 pane_idle/session/prompt 条件，不能拿旧回合或新执行者替代。没有重发、重试、第二 PTY、兼容双写或平行 API。扫描器 `B/design-locator.json` 无定位项仅作为辅助，不单独作 PASS 依据。

## COUNTEREXAMPLE

先取得候选 questions/sidebar 绿态，再在三个独立 git archive 副本各改一处。实际命令与退出码在 `B/mutant-checks.json`，替换文本在 `B/mutations.json`（其 command 字段沿用上一轮模板路径，**本轮实际执行路径以 mutant-checks.json 为准**）。三个失败均命中业务断言，不是初始化或依赖错误：

| 变异 | 单处错误 | 本轮拒绝 |
| --- | --- | --- |
| M1 | questionState 将不可信回合 unknown 改成 idle | `m1-idle.json` rc=1，pending_missing_tool_name 等断言 idle != unknown。 |
| M2 | answerQuestion 对 sending 直接成功 return | `m2-duplicate.json` rc=1，重复作答 Missing expected rejection。 |
| M3 | sidebarSnapshot 开头写 store.event | `m3-permission.json` rc=1，Sidebar read changed persisted tables or traces。名称沿用旧夹具，实际变异是侧栏写入。 |

例如重跑 M1 时从受审 checkout cwd 执行：

```sh
B=/private/tmp/t108-review-06-skyothnq
env -u GIT_DIR -u GIT_WORK_TREE LC_ALL=C node "$B/m1-idle/workbench/tests/test_t108_questions.mjs" "$B/m1-repeat.json"
```

## 真实回合、版本与计数

本轮只读元数据、facts、启动记录与事件，不读真实凭据、私有 HOME/debug 或请求正文；不重跑模型。摘录在 `B/real-original-readback.json`。

- `/private/tmp/t108-version-probe-01.json`：2.1.304 探针 PASS，model/vendor=0、扫描命中0、隔离 HOME 已删除。其 OS HOME 禁写／禁写反例沿用主控原件，本 reviewer 未新启动真实登录或 OS 探针。
- `/private/tmp/t108-real-01.summary.json`：一个根输入，六项 PASS，模型/供应商 **3 次**；代码版本是 `afcc78b0d856680491f0e99410b7ff9acec54dab`，不是本候选。它证明获批真实回合确实执行，不代替新候选的修复验收。实际版本 2.1.304，auth_original_reads=1、credential_scan.hits=0、isolated_home_removed=true、onboarding.state_intact=true。
- 请求账本重数为 5 request、5 outcome、3 次转发，counts_match=true。seq 1/2 是 HEAD /api/hello，本地401，不计模型请求；seq 3 是 06:28:16.801Z 的 POST /v1/messages，429，**已转发仍计调用**；seq 4 是 06:28:19.034Z 的提问请求，200；seq 5 是 06:28:30.273Z 的作答续接，200。
- 第一个 window_input 在 06:28:18.498Z，晚于 seq 3。因此额外一次推断为启动辅助请求，不是该根输入的重试；辅助请求的具体功能 unknown。账本不含正文，不能进一步命名。计划“预计2条”不是硬上限，实际3条没有漏记或改成2条。

## LIMITATIONS

- **地图条件 INCOMPLETE**：开始、收尾 status 均 rc=1，8 个稀疏 checkout 缺失链接，0 stale；收尾原文 `B/project-map-end.txt`。没有越权改地图/ticket 或借其他版本清零。该项是整票未能报告 PASS 的原因，不是本轮新增产品缺陷。
- 本 reviewer 未新跑活 CLI/Electron/真实登录；对当前 SHA 的完整入口采用主控提供的原件并独立读回。没有将它称为 reviewer 新执行的 GUI 实验。受管 worker 的完整操作锁生命周期没有另跑，结论限静态路径、合同和现有主控完整入口。
- 当前异常字段、送达但未知的 hook 和没有充分起始事实时的 unknown 有证据；整条 hook 传输静默丢失、全部时序与所有 CLI 版本未做故障注入，不声称通用可靠性。Codex 原件回放与未验证协议的缺口按已裁定范围保留。
- [REVIEW-OUTSIDE-06.sh](REVIEW-OUTSIDE-06.sh) 固定本候选，以 git archive、普通依赖复制、Python 3.9、内置盘 Electron 和本地假 API 复跑完整入口，并额外核对首答回执及早到/晚到对照。仅替换 archive 里测试的 Git 版本来源，不改产品、业务断言或 CLI。**本轮未执行**；zsh 语法与 Python 3.9 AST 检查 PASS。主控已有的当前 SHA 原件已满足所审修复的完整入口证据，不把待运行补证脚本冒称通过。
- 可选 ps 清单查询被沙箱拒绝，未用于验收，也未申请升级。实际 daemon 测试自带清理证明，原生入口只读采用其主控清理记录。
- 不调用模型／问题面板，不读真实凭据，不写全局配置，不申请升级；无 commit/checkout/reset/stash、submit、集成、push 或主仓库 .git 写入。仓库新增仅本报告和 REVIEW-OUTSIDE-06.sh；已有未跟踪报告、红态与异常原件全部保留。

## RULE

前四轮“异常事实同时撤销状态和作答资格”的网格，以及第五轮“最终 answered 不能替代首答成功回执与后续可用性”的检查，现已在默认合同与无模型完整入口中落实。本轮反例、候选绿态、业务变异拒绝及当前入口原件互相支持；没有提出新提示词治理规则或额外策略层。

产品审查范围 PASS；地图 0 问题仍未满足，整票结论保持 INCOMPLETE，由执行主控处理该现有验收缺口。

T-108 REVIEW INCOMPLETE
