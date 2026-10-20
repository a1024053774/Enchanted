# T-108 第五轮独立审查（2026-10-20）

STATUS: NO_GO

TARGET: `f533fd16e608cb73f666246700206fe28e21503c`，分支 `exec/t108`，起点 `6411bdff8482ba47da207efa6a295a12666222aa`。开始与结束核对同一冻结候选。只读审查，不实现、不提交、不派发子 agent。

**前四轮反例已通过，但发现新的正常作答时序缺陷 F1-05：原生已确认答案，原作答请求却失败，并使该窗格后续输入持续失败。当前候选的六项完整入口 PASS 漏检了这次首答拒绝，整票不能通过。** 地图 0 问题条件另为 INCOMPLETE。

## EVIDENCE

按派发顺序读取主仓库 reviewer 角色卡、本 checkout 的 AGENTS.md、T-108/T-093（含 2026-10-20 用户版本裁定）、T-095/T-071，随后读取 RESULTS、REAL-TURN-PLAN、CONFLICT-LINES 和四轮报告。稀疏 checkout 未展开的文档用 `git show f533fd16e:<路径>` 读取；用 `git diff 6411bdff8 f533fd16e -- <相关路径>` 及当前提交原文核对产品和测试，未以作者会话或修复说明代替合同。

oracle 来自 ticket：结构化原生事实、未知不上调、答复写回原窗格、唯一关联 answer、重复拒绝、受管身份与门禁不变、每会话 hook、隔离与凭据边界不变。用户原话“跑真实回合,版本不重要,以后肯定要经常更新 cli 版本的”取代 Claude 精确发行号限制；没有要求恢复旧二进制。用户不需要截图，本轮没有截图或录屏。

应用 project-map、evidence-first-testing、behavioral-acceptance-review、design-integrity-review、document-writing。结构审查按 skill 路由并入行为审查，未另开 reviewer。Ubiquitous language 沿用 launch、submission、prompt/turn、question、answer；Tracer bullet 经实际 `Panes.signal → SQLite → 状态投影 → answerQuestion → PTY 写入边界`，身份与 PTY 由夹具提供，不能冒称新启动 CLI。questions 模块有实际事实校验与投影职责，符合 Deep modules；未因文件拆分本身判缺陷。

本轮临时根 **B = `/private/tmp/t108-review-05-1mrl278a`**。候选及三个变异均独立来自冻结 SHA 的 `git archive`；仓库 hook 链接展开成普通文件，依赖普通复制并解引用，不建 worktree 或符号链接。Node `26.5.0`，Python `3.9.6`。测试使用 `LC_ALL=C`、清除 `GIT_DIR`/`GIT_WORK_TREE` 和继承的供应商配置；历史合同从受审 checkout cwd 只读 Git 历史。脚本、输入、stdout/stderr、原异常和退出码均留在 B；总运行脚本 `/private/tmp/t108_review05_run.py`，补充运行脚本 `/private/tmp/t108_review05_extras.py`。模型/供应商调用均为 **0**。

### 前四轮反例复跑

从第四轮副本复制前几轮已保存的审查脚本到本轮 archive，原事件形状不改。不是只运行产品新加的矩阵。

| 范围 | 本轮结果与证据（均相对 B） |
| --- | --- |
| 第一轮缺 tool_name | PASS，`f1.json`；拒绝、保存关联的未知事实、侧栏 unknown。正式合同继续覆盖完整无关工具忽略及明确旧回合、异 session、子 agent 隔离。 |
| 第二轮待答缺工具名、非法响应、旧答写入 | PASS，`pending-name.json`、`pending-response.json`、`pending-write.json`；问题 unknown、拒绝答复、answer/PTY 零新增。 |
| 第二轮 Stop 缺 stop_hook_active | PASS，`stop-active.json`；未知且拒绝，active 保留。 |
| 第三轮 PostToolUse 缺 cwd/transcript_path | PASS，`no-cwd.json`、`no-transcript.json`；显示与问题同时 unknown、answer/PTY 0。完整对照 `complete-response.json` PASS，answered。 |
| 第三轮 Stop 缺 prompt_id | 原 `stop-no-prompt.json` 保留 rc=1：已观察到拒绝、unknown、active 保留、PTY 0，随后旧脚本读取不存在的 question.status 而 TypeError。第四轮已补正观测的同输入 `stop-observation.json` rc=0；待答形态 `stop-no-prompt-pending.json` rc=0。不能把旧脚本的观测错误称为产品红态或悄悄删掉。 |
| 第三轮其他工具权限遮蔽旧问题 | PASS，`permission-pending.json`、`permission-valid.json`、`permission-missing.json`；完整 Bash、parallel-permission ID、缺名等输入均撤销旧答资格。 |
| 第四轮全部 forged-name 输入 | 五项全部 PASS：`review04-forged-name.json`、`review04-forged-name-after-bash.json`、`review04-forged-name-empty.json`、`review04-forged-name-matching-id.json`、`review04-forged-name-wrong-id.json`。每项均 unknown、问题 unknown、answer/PTY 0；只有工具名称、复制旧 ID、空参数或 command，均不能继续作答。 |
| 正常同问题权限 | PASS，默认矩阵的 permission_self_full、permission_self_matching_id、permission_self_sending。完整 questions 一致、可无 tool_use_id；答复记录 1、PTY 边界写键 3。当前真实 CLI 完整入口也保存该同问题 PermissionRequest 原件，见后文。 |

全部 argv/退出码在 `B/checks.json`、`B/extras.json`。例如：

```sh
B=/private/tmp/t108-review-05-1mrl278a
# 从受审 checkout cwd 运行；历史合同只读 git show。
env -u GIT_DIR -u GIT_WORK_TREE LC_ALL=C node "$B/candidate/workbench/tests/test_t108_questions.mjs" "$B/questions-repeat.json"
env -u GIT_DIR -u GIT_WORK_TREE LC_ALL=C node "$B/candidate/workbench/tests/review04-forged-name.mjs" "$B/forged-repeat.json"
env -u GIT_DIR -u GIT_WORK_TREE LC_ALL=C node "$B/candidate/workbench/tests/review04-stop-no-prompt-observation.mjs" "$B/stop-repeat.json"
```

### RULE 的覆盖核对

默认 `test_t108_questions.mjs` 为 **15 项主检查、429 项 failure_cases，全部 PASS**。`B/matrix-audit.json` 按外部重建的字段与对照清单逐项核对，基础网格 350 项，无缺项或失败：

- Claude 与 Codex 分别覆盖 PreToolUse、PostToolUse、PostToolUseFailure、Stop、PermissionRequest、UserPromptSubmit；每种逐项缺 cwd、transcript_path、session_id、prompt_id/turn_id。
- 三种工具事件额外逐项缺 tool_name、tool_use_id、tool_input；PermissionRequest 缺 tool_name/tool_input；每个字段配 missing、完整当前、明确旧回合、异 session、子 agent 五组。PermissionRequest 的 tool_use_id 是原生可省字段，不能误作必需字段；其提供错误 ID、复制 ID 无内容等另有反例。
- Claude Stop 缺/非法 stop_hook_active、运行中与已有问题两类；非法 JSON、非法 received_at、非法响应、记录期间与逐键写入期间失效均有检查。拒绝场景同时检查状态、问题资格、answer/PTY、active/prompt、transfer、stopInProgress 和无 pane_idle/completion；后续正常 Stop 仍不能完成不可信回合。
- 额外权限网格拒绝名称伪装、缺内容、command、复制 ID、questions 混入 command/file_path、问题/选项内额外字段；配旧回合/异 session/子 agent 对照。questions.ts:108 起的同问题例外用完整内容的深相等和单一 questions 参数做正向证明，没有缺内容默认匹配。
- Notification 当前未订阅（Claude 启动参数订阅六类，Codex 五类），不冒称其是已支持提问入口；已保存的 `notification.json` 和默认 pending_unrecognized_hook 均证实送达的当前未知事件被拒并使旧问题 unknown。公共 envelope 校验在事件分流之前。Codex PostToolUseFailure 的网格是额外入口防守，未冒称 CLI 会发该事件。

上述网格关闭了前四轮的特定缺陷，但**没有覆盖合法原生确认在写键尚未结束时到达**；它不能作为新 F1-05 的通过证据。

### 其余检查

| 范围 | 本轮核对 |
| --- | --- |
| 每会话 hook | Claude 经 claudeLaunch.ts 的 `--settings` JSON，Codex 经 panes.ts 的 `-c hooks.<事件>`；diff 没有新增全局配置写入。初始化只写隔离 HOME/配置目录。版本、控制字符和终端协议正则不用于提问语义识别。整条 hook 静默丢失未另做独立故障注入。 |
| answer 与门禁 | window_answer 沿原窗口身份、sequence/request 防重和 assertCurrent，受管路径核对 attempt/session/fence/spec/reclaimed；appendUserInput 保存 form=answer、reply_to、target.request 并保留 human_intervention 派生。未新增 claim/submit/integration 或锁释放旁路。正常记录/链接与重复拒绝通过；首答回执与写流缺陷见 F1-05。 |
| 版本/隔离 | `version.json` 8 项、`profile.json` 4 项、`once.json` 4 项、`ports.json` 10 项、`restore.json` 22 项 PASS。三处版本放宽仅由精确值改成有效实测版本，并核对与 manifest 相等；缺 CLI、无法取得版本、空/非法/不匹配版本仍拒绝。私有文件/O_NOFOLLOW、manifest/进程身份、一次消费、auth_original_reads=1、隔离路径、HOME 禁写、网络和清理条件未删。实际版本写入 launch/version_probe/role_card_revision/facts。 |
| T-107 F2/F3 | `sidebar.json` 12 项 PASS；真实 daemon/socket/Panes/SQLite/trace 的 `daemon-readonly.json`、`daemon-identity.json` PASS，cleanup_complete=true。侧栏只读已保存事件，查询没有扫描新日志或写库；身份冲突不上调。 |
| IPC | `ipc.json` 32 项 PASS，原 handler/bridge 及跨窗口、iframe、历史只读、过期身份等拒绝保留，增加 answer；合入 main 的 flow 合同同时保留。 |
| 合并回归 | T-078 Claude Stop/异 session、队列/中断/输入顺序，T-109 hierarchy、T-111 flow 均 rc=0/PASS；命令及输出在 extras.json 和同名 stdout。 |
| Codex | `codex.json` 5 项 PASS，原件来源为已安装 0.163.0 CLI 对本地假 API 的结构化 hook；不是供应商真实模型或本轮活 CLI。异步阻塞与多选写回未验证，文档/计划已声明，未冒称通过。 |
| 结构 | 扫描器 findings=[] 只是定位结果。统一事实关联和 currentTurnTrust、异常记录后重抛没有新增兜底重试/平行 API/第二门禁。F1-05 是把正常终结事实当成异常，使现有拒绝后停止写流的保护被错误触发；不应以吞掉所有异常来修复。 |

## FINDINGS

### [P1] F1-05：合法原生确认早到，作答被误拒并污染后续终端写流

位置：`workbench/src/panes.ts:1198`（只接受 sending）、`:1205`（逐键间等待）、`:758`（失败 Promise 成为后续写流前提）。验收漏检位置：`workbench/tests/t108_questions_driver.mjs:35` 附近只回 clicked，`run_t108_native_e2e.py:111` 起只等待已回答/idle，不核对首个 window_answer 的最终回执与下一次输入。

**真实边界的现成反例**来自本候选主控刚跑的 `/private/tmp/t108-native-e2e-review04-01.json`，不是旧 SHA，也不是变异。其 `fixture=/private/tmp/t078-2-t108-350ywzx4`，SQLite launch.code_revision 与 git rev-parse 均为本轮完整 SHA。只读回查 `orchestration_events` 得到：

| seq | 原件事实 |
| --- | --- |
| 61、62 | 首个 window_answer 收到并准入；request id `c4f9bf54-8b52-4ba2-b1a9-e28a0d454954`。 |
| 63 | 原题的 answer_intent；用户输入表中只有一条关联 answer。 |
| 64、65 | 原 PTY 写入下箭头、Enter。 |
| 68 | CLI PostToolUse 确认“西区”，问题 answered。 |
| 70 | **同一个首答请求 request_rejected：question_input_changed**；没有 native_question_answer_written。 |
| 74 | 同 prompt 的 Stop 正常使 pane_idle。原六项验收仍给出 PASS。 |

原件回读：`B/current-entry-readback.json`、`B/current-entry-answer-audit.json`（独立判 NO_GO）。问题已正常答完并不能证明最初 API 操作成功；首答不是重复请求，不能把这次拒绝当作正确的重复防重。

**本轮定向复现**用未变异 candidate，合法 UPS → PreToolUse → answerQuestion。在原 PTY 已收到“下箭头、Enter”之后、预设第三键前的身份核对处，送入同题、同 session/prompt/tool ID 的合法 PostToolUse；无权限异常、字段缺失、用户改输入或身份撤销。

```sh
B=/private/tmp/t108-review-05-1mrl278a
env -u GIT_DIR -u GIT_WORK_TREE LC_ALL=C node "$B/candidate/workbench/tests/review05-early-native-confirmation.mjs" "$B/early-repeat.json"
env -u GIT_DIR -u GIT_WORK_TREE LC_ALL=C node "$B/candidate/workbench/tests/review05-late-native-confirmation.mjs" "$B/late-repeat.json"
```

`B/early-native-confirmation.json` rc=1：question=answered、answer 记录 1、PTY 两键；首答 error=question_input_changed；随后正常 `userInput('next sentinel')` **再次同错误被拒，PTY 没有新增字节**。命中独立业务断言“原生已确认的有效答案应成功”，不是导入/依赖失败。`B/late-native-confirmation.json` rc=0：把完全相同的原生确认延后到写键完成，首答与后续输入均成功，下一段文本进入 PTY。输入内容相同，改变的是确认时序。

根因：原生确认将 sending 变成 answered，下一次写键校验却把它判为输入变化；serializeWrite 会保留拒绝 Promise，因此后续操作根本不会执行。该保护本来用于未知写入，合法成功却进入了同一路径。界面可能已经移除问题、侧栏继续运行或空闲，而终端写流实际已坏，影响后续主控使用。

最小修正方向：在现有 answerQuestion 生命周期区分“同一答案已被当前原生事实确认”和“未知/撤权/输入变化”；合法确认提前终结尚余选择键并成功结束该操作，同时保留当前回合可信度、身份及异常输入的原有拒绝。不要对所有 question_input_changed 做成功兜底，不要跳过实际未知写入，不要重发答案或另建 PTY/API。需用早到/晚到确认与异常失效三类对照重新证明首答回执、后续输入和重复拒绝。

## COUNTEREXAMPLE

先取得未变异候选的 questions/sidebar 绿态，再从三个独立 git archive 各改一处，产品本体和受审 worktree 未改。`B/mutations.json` 保存精确替换和实际命令；`B/checks.json` 保存退出码。

| 变异 | 单处错误 | 拒绝证据 |
| --- | --- | --- |
| M1 | questionState 把不可信回合 unknown 改成 idle | `m1-idle.json` rc=1，pending_missing_tool_name 等业务断言 idle != unknown。 |
| M2 | answerQuestion 对 sending 直接成功 return | `m2-duplicate.json` rc=1，重复答复 Missing expected rejection。 |
| M3 | sidebarSnapshot 起点追加 store.event | `m3-permission.json` rc=1，Sidebar read changed persisted tables or traces；目录名为历史夹具标签，实际变异是侧栏写入。 |

三项变异均被拒，证明相应断言有效；它们未覆盖正常确认早到，故不能替 F1-05 背书。

## 真实回合、版本与计数

只读核对主控提供的摘要、launch、问题/answer/Stop、facts 和请求**元数据**，没有读取真实 auth、请求正文或已删除 HOME/debug。摘录在 `B/original-summaries.json`、`B/originals-readback.json`、`B/real-entry-answer-audit.json`。

- 当前候选无模型完整入口六项原报告 PASS，模型/供应商 0、假 API 两次、CLI/daemon 均确认退出；其首答回执实际上 NO_GO，详见 F1-05。旧 `/private/tmp/t108-native-e2e-03.json` 不替本候选背书。
- 2.1.304 版本探针 PASS、模型 0、扫描命中 0、隔离 HOME 删除。OS HOME 禁写及禁写反例采用主控探针原件，本 reviewer 未新运行真实登录/OS 边界。
- 真实模型回合六项 PASS、根输入 1、模型/供应商调用 **3**；code_revision=`afcc78b0d856680491f0e99410b7ff9acec54dab`，明确不是本候选。真实首答 request_result.ok=true、随后重复 answer 被 question_not_pending 拒绝；它支持旧候选那一次较晚确认时序，不能反驳当前反例。
- 实际 cli_version=`2.1.304 (Claude Code)`、role_card_revision=`T-093/normal-login/2.1.304`；facts.auth_original_reads=1、credential_scan.hits=0、isolated_home_removed=true、onboarding.state_intact=true。没有放宽为读不到版本也启动，未读取凭据补证。

请求账本（UTC）全部保留：

| sequence | 请求时间与结果 | 统计与解释 |
| --- | --- | --- |
| 1、2 | 06:28:16.314、16.538，HEAD /api/hello，401 | 本地拒绝，不计模型请求。 |
| 3 | 06:28:16.801，POST /v1/messages，429 | 已转发，必须计入调用。早于首次 window_input（06:28:18.498）和根 UPS，故推断为启动辅助请求，非该根输入的重试；具体功能 unknown。 |
| 4 | 06:28:19.034，POST /v1/messages，200 | 根输入后的提问请求。 |
| 5 | 06:28:30.273，POST /v1/messages，200 | 作答后的续接。 |

5 request、5 outcome，model_requests=3、counts_match=true，失败 429 未被漏计。计划“预计 2 条”并非请求硬上限；实际三条已照实报告。没有为查辅助请求用途重跑模型或扩大凭据读取。

## LIMITATIONS

- 项目地图 Acceptance 的 0 问题 **INCOMPLETE**：开始/结束均 rc=1，8 个既有稀疏 checkout 缺失链接、0 stale。未越权修改地图或 ticket 来清零。收尾原文另保存到 B/project-map-end.txt。
- 本 reviewer 未新启动 Electron 或真实登录，不重跑模型；现成当前 SHA 的 CLI/Electron 原件足以证明 F1-05 的真实拒绝，后续输入阻断由本轮实际 Panes/SQLite/PTY 边界对照证明。未冒称一次新的活 CLI 后续输入实验、完整受管 worker/操作锁生命周期实验或全部丢失 hook 的故障注入。
- [REVIEW-OUTSIDE-05.sh](REVIEW-OUTSIDE-05.sh) 固定本候选、git archive、普通复制依赖、Python 3.9、内置盘 Electron、本地假 API和隔离 HOME。除了 archive 无 Git 的测试版本来源，只新增审查夹具与独立核对首答回执；不改产品或原业务断言。内含早到/晚到对照和真实入口首答审计，**本轮未执行**；zsh 语法及 Python 3.9 编译检查 PASS。它预期会拒绝本候选，不能因为原六项 PASS 而上调结论。
- 不调用问题面板、不读真实凭据、不写全局配置、不申请升级；没有 commit/checkout/reset/stash、submit、集成、push 或主仓库 .git 写入。现有未跟踪报告及异常产物保留。版本合同内部临时 Git 操作仅发生在它们自己的 /tmp 夹具。
- 仓库写入仅本报告和 REVIEW-OUTSIDE-05.sh。新的 F1-05 在本次指定正常作答/状态回落与验收审查范围内，交执行主控处理；未自行修复。既有进程关闭/Codex effort 问题已有记录，不在本轮扩修。

## RULE

前四轮“异常事实必须同时撤销正向状态和作答资格”的规则现已在公共字段网格及权限正向证明中落地，已列原反例通过。新 F1-05 暴露另一种验收盲点：**不能用后端最终 answered/idle 代替最初用户操作的成功回执与后续可用性**。

应在默认 test_t108_questions.mjs 增加合法 PostToolUse 在末键前/后到达的对照，要求首答成功、余键不误注入、后续输入仍可写、重复仍拒绝；保留异常 hook/撤权期间逐键拒绝。无模型完整入口按真实 request id 核对首次 window_answer 最终 ok，并在同一窗格追加一次无模型后续操作验证写流；不能只等待问题消失和 idle。当前冻结候选已经为这些检查提供业务红态及实际 CLI 反例，无需新增提示词治理、全局 hook、重试或另一个接口。修复后应重新取得该真实入口证据，本 reviewer 不修复或再次自审。

T-108 REVIEW NO_GO
