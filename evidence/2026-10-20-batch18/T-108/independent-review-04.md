# T-108 第四轮独立审查（2026-10-20）

STATUS: NO_GO

TARGET: `f3a4a5416213e912076437cfd8ce6f69a0e3091f`，分支 `exec/t108`，起点 `6411bdff8482ba47da207efa6a295a12666222aa`。含 main 合并 `d42e8b3fa`（T-109、T-111）。开始及交付前 HEAD 相同。

前三轮缺字段反例已经修复；本轮发现 **F1-04：同问题权限例外可被只有工具名的声明绕过**。未变异候选会把带 Bash 参数的伪造 AskUserQuestion 权限事件视为同一个问题，继续接受旧答复并写入 PTY。需修复；正式 388 项 PASS、正常完整入口 PASS 和三项变异被拒，不能覆盖此反例。

## EVIDENCE

按派发顺序读取主仓库 reviewer 角色卡、AGENTS.md、T-108（含用户选项和同日版本裁定）、T-093 同日裁定、T-095、T-071，以及 RESULTS、REAL-TURN-PLAN、CONFLICT-LINES、前三轮审查。稀疏目录里不存在的受控文件通过 `git show f3a4a5416:<路径>` 读取。用 `git show --format=fuller --stat f3a4a5416`、`git diff 6411bdff8 f3a4a5416`、`git diff d42e8b3fa f3a4a5416` 阅读候选原文。没有把作者的测试结果当成答案。

oracle 来自 ticket：每会话 hook、结构化信号、未知不上调、answer 绑定原问题与原 PTY、重复拒绝、受管 worker 不绕门禁；#29 明确要求“其他工具的权限请求、缺 tool_name、无法核实的，都作废旧问题”，并要求不能被伪造 tool_name 绕过。版本按用户逐字“跑真实回合,版本不重要,以后肯定要经常更新 cli 版本的”，没有要求恢复精确发行号锁。

使用 project-map、evidence-first-testing、behavioral-acceptance-review、design-integrity-review、document-writing。按结构 skill 路由将结构检查并入行为审查，没有另开 agent。Ubiquitous language 沿用 question、answer、submission、prompt/turn、launch、attempt；Tracer bullet 经过真实 `Panes.signal → SQLite → questionState/agentState → answerQuestion → PTY 写入边界`。身份与 PTY 为夹具提供，不能据此声称新跑了原生 CLI 或 Electron。questions.ts 集中事实关联、投影、准入与按键协议，属于有实质责任的 Deep modules；问题是其权限例外判定过宽。

本轮临时根 **B = `/private/tmp/t108-review-04-3ptvrpke`**。候选与三个变异各自从冻结 SHA 的 `git archive` 提取，不建 worktree；受控 hook 链接展开成普通文件，依赖普通复制并解引用，没有新建符号链接。Node 26.5.0、Python 3.9.6。Git 使用 LC_ALL=C，清除 GIT_DIR/GIT_WORK_TREE，历史合同从本 checkout cwd 只读 git show。候选、输入、命令、输出、退出码和失败现场均保留，未覆盖前三轮现场。

### 前三轮反例与正常合同

| 检查 | 本轮结果与产物 |
| --- | --- |
| 第一轮 F1 缺 tool_name | **PASS**，`B/f1.json`：拒绝 question_tool_name_required，保存可投影未知事实，显示 unknown。复用第一轮输入。 |
| 第二轮 F1-02 缺名、非法响应 | **PASS**，`B/pending-name.json`、`pending-response.json`；待答问题变 unknown。`pending-write.json` 用相同作答输入验证 answer 新增 0、PTY 写入 0。 |
| 第二轮 F2-02 Stop 缺 stop_hook_active | **PASS**，`B/stop-active.json`：拒绝、unknown。 |
| 第三轮 F1-03 PostToolUse 缺 cwd/transcript_path | **PASS**，`B/no-cwd.json`、`no-transcript.json`：unknown、问题 unknown、answer 0、PTY 0；`complete-response.json` 完整对照 answered、running、重复作答拒绝。 |
| 第三轮 F2-03 Stop 缺 prompt_id | **PASS（原输入，观测断言补正）**，`B/stop-no-prompt-pending.json` 正常通过。running-only 的原复现 `B/stop-no-prompt.json` 已观察到拒绝 claude_prompt_id_required、unknown、active 保留、answer/PTY 0，但随后错误访问不存在的 question.status 而 rc=1。保留该原件；只将该断言改为 question 不存在，并补无完成断言，事件输入不变，`B/stop-no-prompt-observation.json` rc=0。未把夹具 TypeError 算产品缺陷或业务红态。 |
| 第三轮 F3-03 权限遮蔽 | **PASS（原输入）**，`B/permission-pending.json`、`permission-valid.json`：缺名和完整 Bash 权限均阻断旧问题；answer/PTY 0。同问题例外另见 F1-04。 |
| 正式问题合同 | **PASS**，`B/questions.json`：15 个主检查、388 个场景。状态、问题、answer 准入与逐键准入共同读取 currentTurnTrust；未知粘在 submission 上，后续普通工具不能恢复。 |
| 其他 hook | **PASS（合成已测）**，`permission-missing.json` 与 `notification.json`。Notification 本次没有订阅；合成输入被 unsupported_hook 拒绝且 unknown，不再静默留 running。六类已实现 hook 的公共字段均经过同一 envelope，详见矩阵核对。完全没有 hook 送达的故障本轮未重新注入，不能把字段矩阵称作传输故障全覆盖。 |
| Codex 原件回放 | **PASS**，`B/codex.json`，5 项；原件来自实际 0.163.0 CLI 对本地假 API 的交互。不是供应商真实模型或本轮活 PTY。异步是否阻塞、多选协议仍未验证并未开放写回。 |
| IPC | **PASS**，`B/ipc.json`：组合 questions-flow 合同，旧 handler/bridge 及跨窗口、iframe、历史只读、身份拒绝保留；answer、flow 等增量接入。未删旧接口。 |
| 侧栏 | **PASS**，`B/sidebar.json` 12 项；实际 daemon/socket/Panes/SQLite/trace 的 `daemon-readonly.json`、`daemon-identity.json` 均 PASS、cleanup_complete=true。读取不收集新日志、不写库；辅助来源与异 session 冲突不被上调。 |
| 版本、隔离与恢复 | **PASS（差异与局部）**，`B/version.json` 8 项、`profile.json` 4 项、`once.json` 4 项、`ports.json` 10 项、`restore.json` 22 项。缺 CLI、版本失败、空/非法版本及本次观测不一致仍拒绝；一次消费、身份、恢复拒绝保持。未新跑真实凭据或 OS HOME 禁写反例。 |

异常 Stop 在正式合同中同时断言：active 和原 prompt/turn 保留、stopInProgress=false、transfer=0、无 pane_idle/pane_completion_held；随后完整 Stop 也不能把不可信回合完成。拒绝路径没有门禁交付或操作锁释放调用。这是实际 signal 的合同与调用路径检查，不是新跑真实受管 worker 的操作锁生命周期。

正常 answer 由绑定窗口的 IPC 进入 window_answer，沿用 daemon.ts 的 assertCurrent，在记录前与每次写键前核对 window、attempt/session/fence/spec、回收等身份。recordInput 经 appendUserInput 保存 form=answer、reply_to 与 target.request；受管 attempt 的输入仍派生 human_intervention。没有新增 claim、submit、integration 或恢复旁路。主控的真实原件支持唯一 answer 的实际链接；本轮未新跑完整受管 worker 生命周期。

Claude hooks 在 claudeLaunch.ts:66–71 经 --settings，Codex 在 panes.ts:518 经 -c hooks.<事件>，候选没有新增全局配置写入。配置构造保留隔离 HOME/CLAUDE_CONFIG_DIR/CODEX_HOME；测试初始化的主题设置在 /tmp 隔离目录。语义识别只看结构化事件名、工具名与关联字段，不读屏、不靠自然语言正则或关键词。版本格式及控制字符正则不承担语义识别。

### RULE 矩阵逐项核对

独立按要求列出预期名称，再核对输出，见 `B/matrix-audit.json`。两家 CLI × 六类 hook × 各字段 × missing/complete/old/foreign/child，共 **350 项**，缺项 0，均 PASS：

- 六类：PreToolUse、PostToolUse、PostToolUseFailure、Stop、PermissionRequest、UserPromptSubmit。Codex 的 PostToolUseFailure 是额外合成防御覆盖，本次实际启动未订阅它。
- 每类公共关联字段：cwd、transcript_path、session_id、Claude prompt_id/Codex turn_id。工具 hook 另含 tool_name、tool_use_id、tool_input；PermissionRequest 另含 tool_name、tool_input。
- missing 同时断言 unknown、当前关联未知事实、问题不可答、answer/PTY 零后续写入、无完成/transfer、原 active 保留；完整对照证明正常事件仍能运行/完成/解题；明确旧回合、异 session、子 agent 对照保留当前问题及合法作答。
- 另 38 场覆盖 running-only Stop 字段、JSON/时间错误、响应错误、记录期间及首键/后续键前撤销、同问题权限正反例。已写出的按键不被抹掉，撤销后不再写。

但 `permission_self_no_content` 将“tool_input={} 且无 tool_use_id”直接定义为正例。该断言不是独立的“同一个问题”证明；它正好放过下面的未知或伪造来源，不能仅以矩阵项数宣称 RULE 完整落实。

## FINDINGS

### [P1] F1-04：只有工具名声明就能进入同问题权限例外，旧问题仍可写入 PTY

位置：`workbench/src/questions.ts:108–121`，尤其 `:115–120`；真实调用在 `workbench/src/panes.ts:1084–1090`。

建立合法 UPS 和待答 AskUserQuestion 后，发送当前 session/prompt/cwd/transcript 全部正确的 PermissionRequest：

```json
{"hook_event_name":"PermissionRequest","tool_name":"AskUserQuestion","tool_input":{"command":"printf sentinel"}}
```

上例省略 tool_use_id；公共字段由夹具提供，与当前根一致。只把原 Bash 权限请求的 tool_name 声称为 AskUserQuestion，参数仍是 Bash command。questionPermission 只在字段存在时比较 tool_use_id 和 questions；两者都不存在时，直接以当前唯一 pending 问题作为匹配结果。validateHookEnvelope 仅要求 tool_input 是对象，因此接受 command 对象。

未变异候选的实际结果（`B/forged-name.json`）：signal 不拒绝，追加 native_question_permission；侧栏 **waiting_user_answer**、问题 **waiting**；旧 answer 成功记录 **1 次**，PTY 写入 **3 次**（下箭头、Enter、Enter）。没有 native_question_unverified/permission_wait。业务断言 unknown 失败，rc=1。

对照与扩展：

| 输入差异 | 结果 |
| --- | --- |
| 原第三轮 Bash 请求，带 parallel-permission ID | `B/permission-valid.json` PASS：unknown、answer/PTY 0。 |
| 声称 AskUserQuestion，仍带错误 parallel-permission ID | `B/forged-name-wrong-id.json` PASS：question_permission_mismatch、unknown、answer/PTY 0。 |
| 声称 AskUserQuestion，删除该可选 ID，仍带 command | `B/forged-name.json` 失败：waiting、answer 1、PTY 3。 |
| 同上，先明确送入 PreToolUse(Bash, parallel-permission, command) | `B/forged-name-after-bash.json` 仍失败：waiting、answer 1、PTY 3。完整的无关工具 hook 被正常忽略，没有改变问题。 |
| 声称 AskUserQuestion，tool_input={}，无 ID | `B/forged-name-empty.json` 同样放行；正式 no_content 正例也接受它。 |
| 声称 AskUserQuestion，复制旧问题 ID，但仍是 command 参数 | `B/forged-name-matching-id.json` 同样放行。 |
| 真正同问题，完整 questions 内容且关联一致 | 正式 permission_self_full/matching_id/sending 均 PASS；本候选实际 CLI 完整入口也有同问题 PermissionRequest 的原件。 |

这不是声称无凭据攻击者能伪造 launch token，也没有实际批准 Bash 命令。已证明的是：**在已认证当前 hook 入口，无法核实/相互矛盾的工具事实仍被认作可答问题**，旧按键能够进入 PTY，违反本次明确边界；同一可信度接口只能保证消费方一致，不能弥补生产事实被错误标成可信。

最小修正方向：同问题权限例外需要正向证明它与保存的问题一致；保留真实 CLI 样本中“无 tool_use_id、但完整 questions 内容相同”的正常路径。缺少可验证问题内容、只有名称/旧 ID，或带其他工具参数的事件，应走未知并撤销作答。不要要求 CLI 实际不提供的 ID，不要一律阻断合法同问题请求，也不要增设屏幕/正则猜测、全局 hook 或第二条 API。

### 结构审查

统一 envelope、明确非当前事件先隔离、异常事实追加后重抛，是在事实归属层修复；没有新增重试、兼容实现、双写、平行 API 或第二门禁。异常 catch 未把失败吞成成功。设计扫描器 findings=[] 仅是工作树定位结果，不能证明候选已提交代码无问题。

本轮确认的结构问题就是 questionPermission 的“缺可核对证据仍默认匹配”分支；应在现有模块收紧该例外。无需新增抽象、策略引擎或另一套问题状态。

## COUNTEREXAMPLE

先取得未变异候选 questions/sidebar 的绿色，再对三个独立 archive 各改一处。精确替换、完整命令与退出码在 `B/mutations.json`；都命中业务断言，非依赖或导入失败。

| 变异 | 单处错误 | 拒绝结果 |
| --- | --- | --- |
| M1 | questionState 将不可信回合 unknown 改成 idle | `B/m1-idle.json` rc=1，pending_missing_tool_name 等场景 idle != unknown。 |
| M2 | answerQuestion 对 sending 提前成功 return | `B/m2-duplicate.json` rc=1，重复答复 assert.rejects 报 Missing expected rejection。 |
| M3 | sidebarSnapshot 起点追加 store.event | `B/m3-permission.json` rc=1，Sidebar read changed persisted tables or traces。目录名是夹具标签，实际变异为侧栏写入。 |

三项变异能被拒绝，证明这些断言有效；F1-04 是未变异候选的新反例，说明现有完成检查仍不足以覆盖权限例外。

命令与重放（输出须使用新文件名，避免覆盖证据）：

```sh
B=/private/tmp/t108-review-04-3ptvrpke
# 历史合同从受审 checkout cwd 运行，仅只读 git show。
env -u GIT_DIR -u GIT_WORK_TREE LC_ALL=C node "$B/candidate/workbench/tests/test_t108_questions.mjs" "$B/questions-repeat.json"
env -u GIT_DIR -u GIT_WORK_TREE LC_ALL=C node "$B/candidate/workbench/tests/review04-forged-name.mjs" "$B/forged-repeat.json"
env -u GIT_DIR -u GIT_WORK_TREE LC_ALL=C node "$B/candidate/workbench/tests/review04-forged-name-after-bash.mjs" "$B/forged-after-bash-repeat.json"
env -u GIT_DIR -u GIT_WORK_TREE LC_ALL=C node "$B/candidate/workbench/tests/review04-stop-no-prompt-observation.mjs" "$B/stop-observation-repeat.json"
env -u GIT_DIR -u GIT_WORK_TREE LC_ALL=C node "$B/m1-idle/workbench/tests/test_t108_questions.mjs" "$B/m1-repeat.json"
env -u GIT_DIR -u GIT_WORK_TREE LC_ALL=C node "$B/m2-duplicate/workbench/tests/test_t108_questions.mjs" "$B/m2-repeat.json"
env -u GIT_DIR -u GIT_WORK_TREE LC_ALL=C node "$B/m3-permission/workbench/tests/test_t107_sidebar.mjs" "$B/m3-repeat.json"
```

前三轮原复现及所有局部检查的完整 argv/退出码见 `B/checks.json`；新反例、Codex、实际 daemon 的命令见 `extras.json`；观测补正和先发 Bash 的命令见 `controls.json`。复制旧复现输入，只在需要时补正观测断言；产品源码未动。自己的辅助脚本在 `/private/tmp/t108-review04-*.py`，原始失败和 stderr 均保留。

## 真实原件、版本与调用计数

本 reviewer 新增模型/供应商调用均 **0**。只读核对主控提供的摘要、SQLite 的 launch/问题/answer/Stop、login_facts，以及 forwarder 请求元数据；没有读取真实登录凭据、私有 auth、已删除 HOME/debug 或请求正文。选择性回读见 `B/originals-readback.json`。

- 当前无模型完整入口 `/private/tmp/t108-native-e2e-review03-01.json` **PASS**，6 项、模型/供应商 0；命令记录的 git rev-parse 正是本轮完整 SHA。实际 CLI 的同问题 PermissionRequest 带完整 questions、不带 tool_use_id。DOM answer→原 PTY→PostToolUse→同 prompt Stop/idle、唯一 answer 链接及重复拒绝成立，测试 CLI/daemon 均确认退出。它证明正常边界，不覆盖 F1-04 的坏输入；本 reviewer 未重复运行 Electron。
- 早期 `/private/tmp/t108-native-e2e-03.json` 为旧六项 PASS，不替本候选背书。
- `/private/tmp/t108-version-probe-01.json` **PASS**，实际 2.1.304，模型 0、凭据扫描 0、隔离 HOME 删除。真实回合 `/private/tmp/t108-real-01.summary.json` 为 6 项 PASS、1 根输入、3 次模型调用；启动记录 code_revision 是 **afcc78b0d856680491f0e99410b7ff9acec54dab**，不是当前 SHA。版本 cli_version=`2.1.304 (Claude Code)`，role_card_revision=`T-093/normal-login/2.1.304`；事实 auth_original_reads=1、扫描命中 0、隔离 HOME 删除。
- 三处精确锁的改动仅改为实际版本结构核对及与本次 manifest 等值；动态版本进入启动记录/facts。session/manifest、私有文件/O_NOFOLLOW、一次消费、身份、隔离路径、OS HOME 禁写策略、网络边界及清理检查未随之放宽。局部拒绝合同和恢复合同本轮通过；真实 OS 禁写结论来自主控原件，不冒称 reviewer 新测。

真实请求账本（UTC）：

| sequence | 时间 | 请求/结果 | 解释 |
| --- | --- | --- | --- |
| 1、2 | 06:28:16.314、16.538 | HEAD /api/hello，401 | 本地拒绝，不计生成。 |
| 3 | 06:28:16.801 | POST /v1/messages，429 | 已转发并计入生成调用；早于首次 window_input 06:28:18.498 及根 UPS，因此推断为启动辅助流量，非该根输入重试；具体功能 unknown。 |
| 4 | 06:28:19.034 | POST /v1/messages，200 | 根输入后的提问。 |
| 5 | 06:28:30.273 | POST /v1/messages，200 | 答复后的续接。 |

5 request、5 outcome、model_requests=3、counts_match=true；429 未被删掉。计划预计 2 条不是请求硬上限，实际 3 条照实统计。没有为了查辅助请求用途补跑模型。

Codex 回放的许可与缺口写在 REAL-TURN-PLAN/RESULTS/样本来源：实际 CLI 对本地假 API 的结构化原件，新增真实回合 0。未冒称供应商真实模型、活 CLI 同步性、异步阻塞或多选全部通过。

## LIMITATIONS

- 地图条件 **INCOMPLETE**：开始/结束 status 都 rc=1，8 个既有稀疏检出缺失链接、0 stale；收尾原文 `B/project-map-end.txt`。未改地图或 ticket 使其变绿。
- 本 reviewer 未新跑 Electron、真实登录、OS HOME 禁写反例或完整受管 worker 生命周期；当前完整入口采用主控提供的同 SHA 原件，真实模型采用旧 SHA 原件并明确分层。
- 沙箱外无模型复跑脚本为 [REVIEW-OUTSIDE-04.sh](REVIEW-OUTSIDE-04.sh)，固定当前 SHA、git archive、普通复制依赖、Python 3.9、内置盘 Electron 43.4.1、隔离 HOME、仅本地假 API。仅把 archive 无 .git 时的测试版本来源替成冻结 SHA；产品、业务断言不改。zsh 语法及 Python 3.9 编译检查 PASS，**脚本未执行**。它即使通过也不能关闭 F1-04。
- 没有截图、录屏、问题面板、子 agent、模型或真实凭据读取，没有申请升级、全局配置写入、submit、集成、push。在受审仓库没有 commit/checkout/reset/stash 或 .git 写入；现有 Git 合同内部仅在自身 /tmp 夹具初始化/提交/切换测试分支。
- 仓库写入仅本报告与 REVIEW-OUTSIDE-04.sh；前三轮未跟踪文件及全部异常产物保留。已有关闭进程、Codex effort 问题不在本轮修复范围；F1-04 属派发明确要求的权限边界，交执行主控处理，未使用问题面板。

## RULE

连续出现的类别仍是“无法核实的事实没有撤销旧问题资格”。公共字段矩阵已覆盖此前三轮实例，但同问题权限例外把证据缺失写成了正例。应由机械合同在 test_t108_questions.mjs 默认运行：正常 CLI 的完整 questions、无 tool_use_id 仍可答；Bash 权限 unknown；将 Bash 的 tool_name 改成 AskUserQuestion 并删除 ID，或仅复制旧 ID 而保留 command/空参数，必须 unknown、question unknown、answer 0、PTY 0、无完成/transfer；同时保留旧回合/异 session 的隔离对照。去掉或收紧 no_content 正例的依据，以本冻结候选取得该检查的业务红态。无需新增提示词或治理规则。本 reviewer 只报告，不修复、不提交。

T-108 REVIEW NO_GO
