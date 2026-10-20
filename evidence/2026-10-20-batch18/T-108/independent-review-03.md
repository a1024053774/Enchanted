# T-108 第三轮独立审查（2026-10-20）

STATUS: NO_GO

TARGET: `93fe03dcd54535bc3b48d58e30a6244bf697fca1`，分支 `exec/t108`，起点 `6411bdff8482ba47da207efa6a295a12666222aa`。开始与收尾核对的 HEAD 相同。

第一轮 F1、第二轮 F1-02/F2-02 的精确输入已通过；但缺字段的覆盖仍不完整，另有权限等待被旧问题覆盖的状态冲突。以下三个发现均在未变异候选上复现。**需修复，不能用正常路径或变异检查通过给整票 PASS。**

## EVIDENCE

按要求先读主仓库 reviewer 角色卡、AGENTS.md、T-108/T-093/T-095/T-071，再读 RESULTS、REAL-TURN-PLAN、CONFLICT-LINES、两轮审查与修复记录。稀疏 checkout 的 T-108/T-093 未含同日版本裁定，另外读取 `/Users/luckye/Documents/Code/a2a/.project-map/tickets/` 中两票的 2026-10-20 裁定。判断版本时采用用户原话“跑真实回合,版本不重要,以后肯定要经常更新 cli 版本的”，不要求恢复 2.1.302 精确锁。

用 `git show HEAD:<路径>`、`git show --format=fuller --stat HEAD`、`git diff 6411bdff8 HEAD` 和 `git diff a6c7c161b HEAD` 读取候选原文。oracle 来自上述 ticket、T-071 的未知不上调与每会话配置合同，以及 workbench README 的字段／归属不明显示未知、权限等待不误报的约定；没有把修复说明或新测试的绿色当成答案。

使用 project-map、behavioral-acceptance-review、design-integrity-review 与 document-writing；结构审查依 skill 路由并入本次行为审查，没有另开 agent。Ubiquitous language 沿用 question、answer、submission、prompt/turn、launch、attempt。Tracer bullet 的新实测经过 `Panes.signal → SQLite → questionState/agentState → answerQuestion → PTY 写入边界`；PTY 和进程身份由夹具提供，不能当成真实 CLI／Electron 的新验收。

临时根 **B = `/private/tmp/t108-review-03-st5sb0ku`**。候选及三个错误实现均从冻结 SHA 的 `git archive` 提取，没有 worktree；仓库 hook 链接展开成普通文件，依赖复制并解引用，没有新建符号链接。Node 26.5.0、Python 3.9.6。所有测试命令使用 `LC_ALL=C`，清除 `GIT_DIR`、`GIT_WORK_TREE` 及继承的 A2A／供应商配置；历史合同从本 checkout cwd 只读 `git show`。原件、失败输出和夹具保留在 /tmp，没有覆盖前两轮现场。

### 原发现与正常合同

| 检查 | 本轮结果 |
| --- | --- |
| 第一轮缺 tool_name 精确输入 | **PASS**，`B/f1.json`：拒绝 question_tool_name_required，保存未知事实，侧栏 unknown。复用前轮输入与拒绝断言。 |
| 第二轮待答时缺 tool_name／非法 tool_response | **PASS**，`B/pending-name.json`、`B/pending-response.json`：问题变 unknown；`B/pending-write.json` 再跑第二轮作答输入，拒绝答复、answer 记录 0、PTY 写入 0。仅把旧复现脚本“继续作答”的观测改成应拒绝断言，事件输入未变。 |
| 第二轮当前 Stop 缺 stop_hook_active | **PASS**，`B/stop-active.json`：拒绝 stop_hook_active_required，侧栏 unknown。 |
| 正式缺字段／时序矩阵 | **PASS**，`B/questions.json`：原 15 项及新增 8 场均通过；包括记录期间、首键前、后续键前撤销资格，已经写出的键保留而后续零写入。异常 Stop 不调用 transfer，不清 active/prompt，不进入 stopInProgress，不产生 pane_idle／pane_completion_held；代码在该拒绝路径没有操作锁释放或门禁交付调用。不是另一次真实操作锁生命周期实验。 |
| 合法无关工具与拒绝隔离 | **PASS（已测字段）**：完整 Read 等工具仍忽略；旧 prompt、异 session、子 agent 不撤销当前有效问题；旧 Stop、stop_hook_active=true 保留未匹配语义。没有把一切拒绝无差别映射到当前问题。下面发现涉及“缺失”，不要求把明确异身份或明确旧回合当作当前事件。 |
| Codex 原件回放 | **PASS**，`B/codex.json`，5 项。原件来自已安装 0.163.0 CLI 对本地假 API 的交互；不是供应商真实模型，也不是本轮活 PTY。异步阻塞未知、多选协议未验证仍明示，未开放这些作答路径。 |
| IPC | **PASS**，`B/ipc.json`，28 项。旧 handler／bridge 与跨窗口、iframe、只读历史、身份拒绝保留；只新增 answer。 |
| 侧栏 | **PASS**，`B/sidebar.json`，12 项；实际 daemon/socket/Panes/SQLite/trace 的 `B/daemon-readonly.json`、`B/daemon-identity.json` 均 PASS、cleanup_complete=true。查询没有收集新日志或写库，身份冲突没有被上调。 |
| 版本／隔离合同 | **PASS（差异及局部）**，`B/version.json` 8 项、`profile.json` 4 项、`once.json` 4 项、`ports.json` 10 项、`restore.json` 22 项。三处精确发行号改动没有删掉 session/manifest 等值、私有文件/O_NOFOLLOW、一次消费、auth_original_reads=1、隔离路径、HOME 禁写策略、网络边界或清理检查。缺 CLI、探针失败、版本空／不合法和本次观测不匹配仍拒绝，启动记录保留实际版本。 |

正常作答仍由绑定窗口的 `window_answer` 进入原 `answerQuestion`。`daemon.ts:263` 的 assertCurrent 在记录前与逐键写入前核对 window、attempt/session/fence/spec/reclaimed；`recordInput` 经 `appendUserInput` 保存 form=answer、reply_to 与 target.request，受管 attempt 仍派生 human_intervention。没有新增 claim、submit、integration 或恢复 attempt 的旁路。实际 worker 完整生命周期与问题作答的一体化真实 CLI 场景本轮未新跑。

Claude hooks 经 `claudeLaunch.ts:65` 的 `--settings`，Codex 经 `panes.ts:513` 的 `-c hooks.<事件>`。候选没有新增全局配置写入；终端主题等初始化只写隔离夹具。语义识别使用结构化事件名、工具名及 session/prompt/turn/cwd/transcript/tool ID，不读屏或用自然语言关键词推断。版本格式、控制字符的正则不承担语义识别。

## FINDINGS

### [P1] F1-03：来源字段缺失被记成无关联诊断，待答问题仍可写入 PTY

位置：`workbench/src/questions.ts:18`、`workbench/src/panes.ts:1041`、`:1058`；投影条件在 `questions.ts:63`。

先用合法 UPS 和 PreToolUse 建立当前根问题，再送同 session、当前 prompt、同 tool_use_id 的 PostToolUse，带合法的问题字段和答案响应，仅分别省略 **cwd** 或 **transcript_path**。没有异 session、旧 prompt 或 agent_id。完整事件对照会确认 answered、侧栏 running，并拒绝重复答复；只有缺字段的两个输入失败。

`questionHookBinding` 在返回关联之前抛 question_origin_unverified；catch 保存的 native_question_unverified 只有 reason、event、tool_use_id、question=null，没有 session/submission/turn。投影因此不使问题失效：状态仍 waiting_user_answer，问题仍 waiting；之后 answerQuestion 成功记录 1 次输入并向 PTY 写 **3 次按键**。daemon 的 request_rejected 也不会补上未知状态或撤销资格。

证据：`B/no-cwd-response.json`、`B/no-transcript-response.json` 均 rc=1，命中 waiting_user_answer != unknown；完整对照 `B/complete-response.json` rc=0、answered、后续 PTY 零写入。较早的 `no-cwd.json`／`no-transcript.json` 未提供响应体，保留但不作为“只缺一个字段”的主要证据。

影响与修正方向：字段不全不能证明原生问题仍在等待，旧问题的按键资格却被保留。应区分“明确属于另一身份／旧回合”与“当前关联信息缺失”；在不接受事件、不放宽身份检查的前提下，保守撤销可关联当前问题的正向状态及作答资格。不能只给已完整构造的 binding 才允许记录有效的未知事实。

### [P1] F2-03：Stop 缺 prompt_id 仍走静默未匹配分支

位置：`workbench/src/panes.ts:1090`、`:1098`。

已确认当前根 UPS 后，送同 session/cwd/根 transcript 的 Stop，stop_hook_active=false，仅缺 prompt_id。新校验依赖 current，而 current 又要求 prompt_id 等于当前值；字段缺失因此绕过未知处理。signal 正常返回，只写 turn_end_signal 与 stop_not_matched，侧栏仍 **running**。待答问题存在时，同类输入还保留 waiting 和作答资格，PTY 收到 3 次按键。

主要证据：`B/stop-no-prompt-running.json`，rc=1、running != unknown；该输入不带工具字段，确认不是工具事件解析问题。`B/stop-no-prompt.json` 是有待答问题的补充观测。active/prompt 仍保留，没有观察到错误完成；缺陷是未将失去关联能力的 Stop 降为未知。

修正方向：缺少必需关联字段与“字段完整、明确属于旧回合”的 Stop 分开处理。缺字段拒绝并保存可投影的未知事实，同时不得完成回合、调用 transfer 或释放锁；继续保留合法过期与异 session 的既有语义。原 F2-02 只补 stop_hook_active，不足以覆盖这一提前分流。

### [P1] F3-03：PermissionRequest 被旧问题状态遮蔽，旧答复仍可进入权限等待中的 PTY

位置：`workbench/src/panes.ts:1064`、`workbench/src/sidebar.ts:22`，以及 `panes.ts:1149` 的 answer 资格检查。

当前根问题 waiting 后送入同 session/prompt/cwd/transcript 的 PermissionRequest。缺 tool_name 的输入与字段完整的 Bash 权限请求都保存 permission_wait；但 agentState 先返回 questionState，尚未读取 permission_wait，故仍显示 waiting_user_answer。question 投影未撤销，answerQuestion 也未核对 permission，接受旧问题答复，记录 1 次输入并写入 3 次 PTY 按键。

证据：`B/permission-pending.json` 与 `B/permission-valid-pending.json`，rc=1、waiting_user_answer != unknown。字段完整的对照证明并非只缺 tool_name 才出现。前轮“无待答问题时 PermissionRequest 得到 unknown”的输入本轮仍 PASS（`B/permission.json`），无法覆盖这个状态优先级冲突。

已证明的是收到权限等待事实后仍可注入旧问题按键；没有声称在真实 CLI 中执行了某项权限批准，也没有用这个夹具证明两种原生工具的并发出现频率。修正应在当前回合的冲突／权限等待处理层同时影响展示与作答资格，保留普通提问的正常路径；不能只调整侧栏标签。

### 其他 hook 与结构审查

Notification 未在本次 Claude/Codex 启动参数中订阅，也没有适配分支。继承第二轮合成 Notification 输入仍得到 unsupported_hook，状态 running（`B/notification.json`，rc=1）。这是未订阅路径的边界，不声称真实 CLI 曾发来这个失败，不重复列为第四个 P1。UserPromptSubmit 的非空唯一 prompt_id、登记正文核对及未登记输入处理仍在。

按 design-integrity-review 核对了真实调用、故障归属、结构成本与改动比例。入口保存事实后重新抛异常的层次合理，没有新重试、全局 hook、兼容实现、并行 API 或第二门禁。questions.ts 集中字段核对、事件投影与按键协议，具备 Deep modules 的实质责任。本轮结构缺陷是遗漏失败关联和状态优先级；扫描器输出 findings=[] 仅是工作树定位结果，不能覆盖已提交候选或推翻上述复现。

## COUNTEREXAMPLE

先确认未变异候选的 questions、sidebar 合同均 rc=0，再从同一冻结 SHA 的 archive 分别改一处。精确替换与命令保存在 `B/mutations.json`。三者均 rc=1，命中业务断言，不是依赖缺失或夹具崩溃。

| 变异 | 单处错误 | 被拒证据 |
| --- | --- | --- |
| M1 | questions.ts 将无待答问题时 unverified 的 unknown 改成 idle | `B/m1-idle.json`：running_stop_missing_active 断言 idle != unknown。 |
| M2 | answerQuestion 对 status=sending 提前成功 return，接受重复答复 | `B/m2-duplicate.json`：重复答复的 assert.rejects 报 Missing expected rejection。 |
| M3 | sidebarSnapshot 起点追加 store.event('sidebar_read', …) | `B/m3-sidebar.json`：Sidebar read changed persisted tables or traces。 |

这些变异能被拒绝，但同一完成检查仍放过 F1-03/F2-03/F3-03，说明“变异通过”不能替代缺字段与状态冲突矩阵。

重放命令如下，摘要必须换新文件名，不能覆盖已有结果：

```sh
B=/private/tmp/t108-review-03-st5sb0ku
# 每条命令均清除 GIT_DIR/GIT_WORK_TREE，Git 使用 LC_ALL=C。
env -u GIT_DIR -u GIT_WORK_TREE LC_ALL=C node "$B/candidate/workbench/tests/test_t108_questions.mjs" "$B/questions-repeat.json"
env -u GIT_DIR -u GIT_WORK_TREE LC_ALL=C node "$B/candidate/workbench/tests/review_missing_hook_field.mjs" "$B/f1-repeat.json"
env -u GIT_DIR -u GIT_WORK_TREE LC_ALL=C node "$B/candidate/workbench/tests/review_pending-missing-name.mjs" "$B/pending-name-repeat.json"
env -u GIT_DIR -u GIT_WORK_TREE LC_ALL=C node "$B/candidate/workbench/tests/review_pending-invalid-response.mjs" "$B/pending-response-repeat.json"
env -u GIT_DIR -u GIT_WORK_TREE LC_ALL=C node "$B/candidate/workbench/tests/review_stop-missing-active.mjs" "$B/stop-active-repeat.json"
env -u GIT_DIR -u GIT_WORK_TREE LC_ALL=C node "$B/candidate/workbench/tests/review03-pending_name_write.mjs" "$B/pending-write-repeat.json"
env -u GIT_DIR -u GIT_WORK_TREE LC_ALL=C node "$B/candidate/workbench/tests/review03-no-cwd-response.mjs" "$B/no-cwd-repeat.json"
env -u GIT_DIR -u GIT_WORK_TREE LC_ALL=C node "$B/candidate/workbench/tests/review03-no-transcript-response.mjs" "$B/no-transcript-repeat.json"
env -u GIT_DIR -u GIT_WORK_TREE LC_ALL=C node "$B/candidate/workbench/tests/review03-complete-response-control.mjs" "$B/complete-response-repeat.json"
env -u GIT_DIR -u GIT_WORK_TREE LC_ALL=C node "$B/candidate/workbench/tests/review03-stop-no-prompt-running.mjs" "$B/stop-no-prompt-repeat.json"
env -u GIT_DIR -u GIT_WORK_TREE LC_ALL=C node "$B/candidate/workbench/tests/review03-permission-valid-pending.mjs" "$B/permission-repeat.json"
env -u GIT_DIR -u GIT_WORK_TREE LC_ALL=C node "$B/m1-idle/workbench/tests/test_t108_questions.mjs" "$B/m1-repeat.json"
env -u GIT_DIR -u GIT_WORK_TREE LC_ALL=C node "$B/m2-duplicate/workbench/tests/test_t108_questions.mjs" "$B/m2-repeat.json"
env -u GIT_DIR -u GIT_WORK_TREE LC_ALL=C node "$B/m3-sidebar/workbench/tests/test_t107_sidebar.mjs" "$B/m3-repeat.json"
```

其他命令的完整 argv／退出码见 `B/checks.json`、`B/boundary-checks.json`；输出和 stderr 各自保留。实际 daemon harness 仅以普通复制取代原测试的依赖 symlink，产品及断言未改。变异和扩展输入只在临时副本，不改正式测试。

## 真实原件与调用计数

本 reviewer 模型／供应商调用均为 **0**。只读核对主控给出的三个摘要，以及真实现场的 SQLite、launch_records 与 forwarder/journal/requests.jsonl，没有读取原始登录凭据、私有 auth 或已删除 HOME/debug。

真实回合原件六项 PASS，属于 **afcc78b0d856680491f0e99410b7ff9acec54dab**，不能当作本轮候选的重跑。启动记录的 cli_version=`2.1.304 (Claude Code)`，role_card_revision=`T-093/normal-login/2.1.304`；问题、唯一 answer 的 reply_to/target.request/thread、原生答案与同 prompt 的 Stop/idle 一致。选择性只读核对保存于 `B/real-original-readback.json`。

| sequence | 时间 UTC | 请求与结果 |
| --- | --- | --- |
| 1、2 | 06:28:16.314、16.538 | HEAD /api/hello，本地无 bearer 拒绝 401，不计生成请求。 |
| 3 | 06:28:16.801 | POST /v1/messages，声明 278 字节；转发后 429，已计入调用。 |
| 4 | 06:28:19.034 | POST /v1/messages，23015 字节；200，根输入后的提问生成。 |
| 5 | 06:28:30.273 | POST /v1/messages，23656 字节；200，答案后的续接。 |

额外第 3 条早于首次 window_input（06:28:18.498）及根 UPS（06:28:19.001），因此可判为**启动辅助请求，不是该根输入的重试**；其具体功能 unknown。账本没有请求正文，不能进一步命名。计划预计 2 条不等于请求硬上限；实际 1 个根输入、3 次转发生成请求，失败的 429 也计入，5 条 request／5 条 outcome 与 facts 的 counts_match=true 对账一致，没有凑成 2 次。

`/private/tmp/t108-native-e2e-03.json` 是六项 PASS、模型/供应商 0 的既有完整入口；`/private/tmp/t108-version-probe-01.json` 是 PASS、版本 2.1.304、扫描命中 0、隔离 HOME 已删除。真实 facts 保留 auth_original_reads=1、HOME 禁写 C/F/D 策略、隔离 HOME 删除、扫描命中 0。这些是主控执行原件核对，不是本 reviewer 新取得的 OS／真实 CLI 边界证据；不重跑模型查辅助请求用途。

## LIMITATIONS

- **INCOMPLETE：地图 0 问题条件未满足。** 开始与结束 status 都 rc=1、8 项稀疏检出缺失链接、0 stale；结束原文在 `B/project-map-end.txt`。没有修改地图或其他文件让它变绿。
- 当前候选未独立运行 Electron／原生 CLI 完整入口。沙箱外无模型补证脚本为 [REVIEW-OUTSIDE-03.sh](REVIEW-OUTSIDE-03.sh)，固定本轮 SHA，重新 git archive，普通复制依赖，内置盘 Electron 43.4.1，只用本地假 API；仅替换 archive 没有 .git 时测试取得代码版本的来源，不改产品或业务断言。zsh 语法与内嵌 Python 3.9 AST 均 PASS，**脚本未执行**。即使该脚本绿，也不能关闭本报告反例。
- 未新跑 OS 禁写真实 HOME 的反例；隔离结论限定为差异、局部合同和既有原件。没有新增全局配置写入，也没有声称本轮新取得真实 HOME 前后清单。
- 未调用问题面板、模型、真实凭据、截图或录屏；未申请沙箱升级。没有 commit、checkout、reset、stash、submit、集成、push 或主仓库 .git 写入。本轮仓库写入仅本报告与 REVIEW-OUTSIDE-03.sh，前两轮未跟踪报告和脚本均保留。
- 既有关闭进程与 Codex effort 问题已有 triage 记录，本轮没有修复或扩大范围。F1-03/F2-03/F3-03 属本次明确要求的 hook／状态／作答审查范围，交执行主控处理。

## RULE

这是连续三轮出现的“异常事实没有同时撤销状态和写入资格”。应由 T-108 的机械合同覆盖，而不是再补一条提示词：在 `t108_hook_failure_contracts.mjs` 增加公共来源字段逐项缺失（至少 cwd、transcript_path、prompt_id）与“已有待答问题后 PermissionRequest”的输入，均同时断言侧栏 unknown、问题不可答、answer 零新增、PTY 零后续写入、无 completion／transfer。每种缺失配完整当前、明确旧回合、明确异 session／子 agent 对照；完成条件默认经 test_t108_questions.mjs 运行，并用修前候选取得业务红态。权限等待的显示与写入资格必须同源检查。由执行主控登记和落实，本 reviewer 不改产品、测试、ticket 或治理文件。

T-108 REVIEW NO_GO
