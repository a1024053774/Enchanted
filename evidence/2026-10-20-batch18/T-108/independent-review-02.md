# T-108 第二轮独立审查（2026-10-20）

STATUS: NO_GO

TARGET: `a6c7c161ba101f4dc58870ace9dfa3ae4b1e8fe4`，起点 `6411bdff8482ba47da207efa6a295a12666222aa`，分支 `exec/t108`。开场与收尾 HEAD 相同；未改候选，未提交、集成、push 或开子 agent。

第一轮 F1 的原始输入已经通过，但不能关闭整个缺字段问题：待答问题已经存在时，当前根事件的字段错误仍不会使问题失效；另有当前 Stop 缺字段后保留“运行中”的同类分支。两个问题均在未变异候选复现，结论为 **NO_GO**。

EVIDENCE:

审查顺序按派发要求执行：主仓库 reviewer 角色卡、本 checkout 的 AGENTS.md、T-108/T-093/T-095/T-071，以及候选的 RESULTS、REAL-TURN-PLAN、CONFLICT-LINES、F1-RESULTS。用 `git show a6c7c161b:<路径>` 和 `git diff 6411bdff8 a6c7c161b` 核对原文，并定向比较 `afcc78b0d..a6c7c161b`。同日版本裁定读取主仓库最新 T-108/T-093，稀疏分支内的 ticket 尚未含该裁定。

独立期望来自 T-108：当前事件字段缺失或 hook 失败要显示“未知”；答复送入原窗格，只有一条关联问题的 answer，重复拒绝；不写全局配置，不绕过受管 attempt。T-071 要求结构化信号、每会话参数与未知不上调；T-095 允许无充分解决证据时回落至 unknown。版本裁定只取消精确发行号限制，不取消隔离、身份、凭据或版本读取检查。

本次使用 project-map、evidence-first-testing、behavioral-acceptance-review、design-integrity-review 与 document-writing。结构审查按 design-integrity-review 的路由并入行为验收审查；本 session 已是新上下文的独立 reviewer，没有再委派审查。Ubiquitous language 沿用 question、answer、submission、prompt/turn、launch、attempt。Tracer bullet 的实际 CLI/Electron 链仅核对已有原件，本轮不调用模型。

临时根为 `/private/tmp/t108-review-02-6g6q0g48`（下文记作 B）。候选与三个单处变异副本均由同一冻结 SHA 的 `git archive` 提取；没有建 worktree。仓库链接展开成普通文件，依赖复制并解引用，没有新建符号链接。Python 为系统 3.9，Node 为 26.5.0；命令清除 `GIT_DIR`/`GIT_WORK_TREE`，Git 使用 `LC_ALL=C`。运行现场与失败摘要保留在 /tmp，不覆盖旧结果。

| 必审项 | 结论与证据 |
| --- | --- |
| 原 F1 精确输入 | **PASS**。复用第一轮 `review_missing_hook_field.mjs` 的输入，仅增加捕获预期拒绝及 unknown 事实断言；当前根 UPS 后，PreToolUse 缺 tool_name，得到 `question_tool_name_required`、一条 native_question_unverified、侧栏 unknown。`B/candidate-f1-02.json`，rc=0。输入没有改成另一类缺字段。第一轮原脚本保存为 `B/first-round-original.mjs`。 |
| F1 的现有正式合同 | **PASS（局部）**。`B/candidate-questions-02.json`，rc=0，15 项；完整无关工具仍忽略，Claude 三种工具事件及 Codex 缺名拒绝，过期 prompt、异 session、子 agent 不生成新问题，重复、撤权、输入变化仍拒绝。新增边界反例见 F1-02。 |
| 每会话 hook、全局 HOME | **静态与既有原件核对 PASS；本轮 OS 边界复跑 INCOMPLETE**。Claude 仅在 `--settings` 增加三种工具 hook；Codex 仅追加 `-c hooks.PreToolUse`/`hooks.PostToolUse`。没有新增全局配置写入。正常登录的 C/F/D HOME 禁写策略与实际版本核对、session/manifest 等值、凭据读取一次均保留。异常 hook 的状态降级并非全部通过，见两项发现。 |
| 提问与作答 | **正常合同 PASS**。Panes 保留 active submission，原 PTY 接收按键；原生 PostToolUse 确认后才记 answered。daemon 的 window_answer 复用窗口身份、sequence/request 防重、assertCurrent，再调用 appendUserInput，form=answer、reply_to/target.request=question。受管 worker 仍核对 current attempt/session/fence/spec/reclaimed；appendUserInput 仍派生 human_intervention，不调用任何交付或集成入口。对撤销身份、输入变化和重复答复的检查通过；异常后仍可作答的缺口见 F1-02。 |
| 三处版本放宽 | **PASS（差异与合同）**。claudeLaunch、ClaudeLogin.prepare、claudeLoginSession.prepare 取消 2.1.302 精确锁，保留非空版本结构检查；运行 `--version` 必须与本次 manifest 相等。缺 CLI、探针失败、版本不符仍拒绝。`B/candidate-version-02.json` 8 项、`candidate-profile-02.json` 4 项、`session-once.json` 4 项、`port-policy.json` 10 项、`candidate-restore-02.json` 均 PASS。没有改凭据来源、O_NOFOLLOW、私有文件权限、auth_original_reads=1、隔离路径、HOME/网络策略或清理判据。 |
| 模型次数 | **PASS（照实计数）**。主控原件 1 个根输入、3 次生成请求；第三条额外流量发生于根输入前，429 也被计入，详见下表。具体辅助用途 unknown。 |
| 结构化识别、Codex 边界 | **PASS（边界明确）**。不从屏幕或自然语言关键词推断提问；识别使用 hook_event_name、tool_name、session/prompt/turn、cwd/transcript 与 tool ID。正则用于版本结构及控制字符拒绝。Codex 0.163.0 原件来自真实 CLI 加本地假 API；本轮 `B/candidate-codex-02.json` 五项 PASS，是回放，不是新真实模型或活 PTY 证明。异步是否阻塞未知、多选写回未验证，RESULTS/REAL-TURN-PLAN 与 UI 禁用均明确。 |
| T-107 F2/F3、IPC | **PASS（当前候选）**。projection 合同和实际 daemon/socket/Panes/SQLite/trace 的 readonly、identity 两场均 PASS，cleanup_complete=true；侧栏写入变异在两层都失败。sidebarSnapshot 只读已持久化事实，不扫描原生日志。IPC 合同 PASS，旧 handler/bridge 与跨窗口、iframe、过期 launch、历史只读等拒绝保留，只增加 answer。 |
| 结构问题 | **NO_GO**。没有新增重试、兼容实现、第二门禁或无证据 fallback。questions.ts 汇集字段校验、事件投影和按键协议，属于承担实质责任的 Deep modules；确认的问题是异常事实未进入已有问题的投影，以及 Stop 的不匹配分支未区分字段错误与过期事件。 |

FINDINGS:

**[P1] F1-02 — `workbench/src/questions.ts:55`、`:66` 与 `workbench/src/panes.ts:1035`：已有问题时，当前根 hook 缺字段虽被拒，问题仍可继续作答。**

- 输入先产生合法 UPS 和 AskUserQuestion/PreToolUse，确认 waiting_user_answer。随后送入同 session、prompt、cwd、transcript、tool_use_id 的 PostToolUse，只删除 tool_name，其余问题字段齐全。
- signal 拒绝 `question_tool_name_required`，并追加 native_question_unverified；但 projectQuestions 不处理该事实，questionState 仅在“没有未解决问题”时才读取它。已有问题仍为 waiting，侧栏仍报 waiting_user_answer，而不是 ticket 要求的 unknown。
- `B/candidate-pending-missing-name-02.json`，rc=1，业务断言为 waiting_user_answer != unknown。追加的 `B/pending-name-write.json` 还确认：同一坏 hook 之后 answerQuestion 仍成功，测试 PTY 收到 **3 次按键写入**。没有通过制造 setup 错误来判失败。
- 同类输入：当前 PostToolUse 的 tool_response 为非法 JSON `"{"`。JSON.parse 位于已有 catch 之外，抛 SyntaxError，未追加 unknown/resolved 事实，状态仍 waiting_user_answer；`B/candidate-pending-invalid-response-02.json`，rc=1。
- 影响：已有问题在原生完成信号不可验证后仍被视为可作答，用户可能向已变化的原生界面发送旧问题按键。真实外部界面是否已变化没有在本测试中断言；已证明的是失去有效确认后仍允许按键。
- 最小修正方向：由已校验身份的当前根事件记录与问题/submission/turn 绑定的未知事实，让问题投影和作答资格同时失效；把当前问题响应解析失败纳入同一处理。必须继续忽略完整的无关工具，并保留旧 prompt/异 session 的拒绝语义；不能把一切拒绝都无差别投影到当前问题。

**[P1] F2-02 — `workbench/src/panes.ts:1084`、`:1086` 与 `workbench/src/sidebar.ts:60`：当前 Stop 缺 stop_hook_active 被当成未匹配事件静默返回，侧栏保留“运行中”。**

- 在已确认 UPS 的当前根上送入同 session/prompt/cwd/transcript 的 Stop，仅缺少 stop_hook_active。active 与 prompt 身份完全相同，非过期或异会话输入。
- `matched` 因字段缺失而 false；只追加 turn_end_signal 和 stop_not_matched，signal 正常返回，不拒绝；没有可投影的未知事实。agentState 继续依据旧 UPS 显示 running。
- `B/candidate-stop-missing-active-02.json`，rc=1，业务断言为 running != unknown。这是现有 Stop 分支的同类缺口，非 a6c7c161b 新增代码；本轮派发明确要求一并检查，且违反 T-108 的未知状态完成条件，因此不能用“旧代码”排除。
- 最小修正方向：区分当前根的格式不全与合法的过期/不匹配 Stop；前者拒绝并留下可投影的 unknown，后者保持既有拒绝/忽略语义。不得靠异常 Stop 完成回合、解除操作锁或触发交付。

其他 hook 类型的定向检查：

| 类型与输入 | 观察 |
| --- | --- |
| PermissionRequest，当前 prompt 身份齐全、缺 tool_name | `permission_wait` 令状态为 unknown，rc=0；没有出现 F1 那种“缺工具名直接忽略”的分支。摘要 `B/candidate-permission-missing-tool-02.json`。没有声称它会展示一个字段齐全的问题。 |
| Notification | Claude/Codex 本次启动参数均未订阅该事件，当前没有 Notification 适配。合成 permission_prompt Notification 送到 signal 会被 unsupported_hook 拒绝，状态仍 running（`B/candidate-notification-02.json`）；它没有失败降级事实。此项是未订阅路径的边界检查，不冒称真实 CLI 运行中发生过该失败，也不据此重复计算一个独立 P1。 |
| UserPromptSubmit | 现有非空且唯一 prompt_id、登记正文核对仍在；未登记且无 active 的返回只保存 unregistered，不创建正向 running 证据。合法过期/异身份的拒绝不可为了未知降级而放宽。 |

COUNTEREXAMPLE:

先确认未变异候选的对应合同 rc=0，再分别只改一处。精确替换文本在 `B/mutations.json`；所有失败均命中业务断言。

| 变异 | 单处错误 | 同一检查的结果 |
| --- | --- | --- |
| M1 | questions.ts 无待答问题时，将 unverified 的 unknown 改为 idle | test_t108_questions rc=1，`idle != unknown`，命中缺名状态断言；`B/m1.json`。 |
| M2 | answer_intent 投影由 sending 改为 waiting，容许发送中的问题再答 | test_t108_questions rc=1，重复答复 `assert.rejects` 报 Missing expected rejection；`B/m2.json`。 |
| M3 | sidebarSnapshot 增加一次 store.event 写入 | projection 及实际 daemon readonly 都 rc=1，`Sidebar read changed persisted tables or traces`；`B/m3.json`、`B/m3-daemon.json`，后者 cleanup_complete=true。 |

这三种错误实现能被已有合同拒绝，但正常合同仍放过 F1-02/F2-02，因此完成条件的实现检查仍需补齐。

精确命令如下。已生成的摘要不可覆盖；重跑时使用新的输出名。涉及历史版本的合同从本 checkout cwd 执行，只用 git show 读取历史，不写共享 Git 元数据。

```sh
B=/private/tmp/t108-review-02-6g6q0g48
env -u GIT_DIR -u GIT_WORK_TREE LC_ALL=C node "$B/candidate/workbench/tests/review_missing_hook_field.mjs" "$B/candidate-f1-02.json"
env -u GIT_DIR -u GIT_WORK_TREE LC_ALL=C node "$B/candidate/workbench/tests/test_t108_questions.mjs" "$B/candidate-questions-02.json"
env -u GIT_DIR -u GIT_WORK_TREE LC_ALL=C node "$B/candidate/workbench/tests/review_pending-missing-name.mjs" "$B/candidate-pending-missing-name-02.json"
env -u GIT_DIR -u GIT_WORK_TREE LC_ALL=C node "$B/candidate/workbench/tests/review_pending_name_write.mjs" "$B/pending-name-write.json"
env -u GIT_DIR -u GIT_WORK_TREE LC_ALL=C node "$B/candidate/workbench/tests/review_pending-invalid-response.mjs" "$B/candidate-pending-invalid-response-02.json"
env -u GIT_DIR -u GIT_WORK_TREE LC_ALL=C node "$B/candidate/workbench/tests/review_stop-missing-active.mjs" "$B/candidate-stop-missing-active-02.json"
env -u GIT_DIR -u GIT_WORK_TREE LC_ALL=C node "$B/m1-unknown-idle/workbench/tests/test_t108_questions.mjs" "$B/m1.json"
env -u GIT_DIR -u GIT_WORK_TREE LC_ALL=C node "$B/m2-duplicate/workbench/tests/test_t108_questions.mjs" "$B/m2.json"
env -u GIT_DIR -u GIT_WORK_TREE LC_ALL=C node "$B/candidate/workbench/tests/test_t107_sidebar.mjs" "$B/candidate-sidebar-02.json"
env -u GIT_DIR -u GIT_WORK_TREE LC_ALL=C node "$B/m3-sidebar-write/workbench/tests/test_t107_sidebar.mjs" "$B/m3.json"
env -u GIT_DIR -u GIT_WORK_TREE LC_ALL=C T107_DEPENDENCIES="$B/node_modules" node --experimental-vm-modules "$B/candidate/workbench/tests/review_t107_daemon_readonly.mjs" "$B/daemon-readonly.json" "$B/candidate" readonly
env -u GIT_DIR -u GIT_WORK_TREE LC_ALL=C T107_DEPENDENCIES="$B/node_modules" node --experimental-vm-modules "$B/candidate/workbench/tests/review_t107_daemon_readonly.mjs" "$B/daemon-identity.json" "$B/candidate" identity
env -u GIT_DIR -u GIT_WORK_TREE LC_ALL=C T107_DEPENDENCIES="$B/node_modules" node --experimental-vm-modules "$B/candidate/workbench/tests/review_t107_daemon_readonly.mjs" "$B/m3-daemon.json" "$B/m3-sidebar-write" readonly
```

其余绿态命令为 `env -u GIT_DIR -u GIT_WORK_TREE LC_ALL=C node --experimental-vm-modules "$B/candidate/workbench/tests/<脚本>" <摘要>`：test_t091_pane_ipc.mjs、test_t091_claude_version.mjs、test_t093_launch_profile.ts、test_t096_restore.mjs；摘要分别为 candidate-ipc.json、candidate-version-02.json、candidate-profile-02.json、candidate-restore-02.json。session_once 用 `node .../test_t093_session_once.ts "$B/session-once.json"`；端口策略用 `/usr/bin/python3 -B .../test_t093_forwarder_port_policy.py "$B/port-policy.json"` 并设 PYTHONDONTWRITEBYTECODE=1。Codex 使用 `node .../test_t108_hook_replay.mjs --samples "$B/candidate/evidence/2026-10-20-batch18/T-108/native-hook-samples.json" --summary "$B/candidate-codex-02.json"`。

实际 daemon harness 复用第一轮保存的版本，仅将依赖 symlink 改成普通复制；产品和断言不改。它确实启动 socket、门禁、Panes、SQLite 与 trace，但 PTY 身份由夹具提供，不能作为活 CLI 的新证明。

真实回合原件核对（本 reviewer 模型调用 0）：

读取 `/private/tmp/t108-real-01.summary.json`，并只读查询 `/private/tmp/t108-real-a4e5c18d14/state/state.sqlite3`、对应 login-audits 的 facts.json 和 forwarder/journal/requests.jsonl。启动记录的 code_revision 为 **afcc78b0d856680491f0e99410b7ff9acec54dab**；不是 a6c7c161b。其 launch/session、问题/原生答案、Stop/idle、唯一 answer 引用一致；cli_version 为 `2.1.304 (Claude Code)`、role_card_revision 为 `T-093/normal-login/2.1.304`，facts 内版本均为 2.1.304。原件六项 PASS，只支持其实际运行的版本。

| 账本 sequence | 时间（UTC） | 请求 | 结果与解释 |
| --- | --- | --- | --- |
| 1、2 | 06:28:16.314、16.538 | HEAD /api/hello | 无 bearer，本地拒绝 401；未冒充生成请求。 |
| 3 | 06:28:16.801 | POST /v1/messages，声明 278 字节 | 转发后返回 429，已计入 model_calls。它早于首次 window_input 的 06:28:18.498 和根 UPS hook 收到的 06:28:18.997，属于启动辅助请求，不是该根输入的重试。具体用途 unknown。 |
| 4 | 06:28:19.034 | POST /v1/messages，23015 字节 | 200，根输入后的提问生成。 |
| 5 | 06:28:30.273 | POST /v1/messages，23656 字节 | 200，原生答案后的续接，随后 Stop。 |

5 条 request、5 条 outcome，facts 的 received_requests/ledger_requests=5、model_requests=3、counts_match=true；摘要 vendor_calls=3，root_inputs_attempted=1。计划“预计 2 条”不是调用硬上限，不能删掉启动辅助流量凑数。账本没有正文，私有 HOME/debug 已清理，不能把辅助请求进一步命名为某项特定探测。本轮没有为查用途补跑模型或读取真实凭据。

同时读取 `/private/tmp/t108-native-e2e-03.json`（六项 PASS、model_calls/vendor_calls=0）及 `/private/tmp/t108-version-probe-01.json`（PASS、2.1.304、凭据扫描命中 0、isolated_home_removed=true）。真实 facts 保留 auth_original_reads=1、C/F/D 策略、凭据扫描命中 0 和隔离 HOME 清理结论。这些是主控运行原件；不是本 reviewer 新执行的 OS/CLI 边界测试。

LIMITATIONS:

- 当前候选的新增反例都经过实际 `Panes.signal → SQLite → agentState`，未模拟其实现方法；但运行时身份和 PTY 是受控边界。未独立重跑 Electron、正常登录或真实模型。真实回合不重跑，符合派发约束。
- 当前候选的无模型完整入口补证已写入 [REVIEW-OUTSIDE-02.sh](REVIEW-OUTSIDE-02.sh)，尚未执行。脚本固定 a6c7c161b、git archive、依赖普通复制、Python 3.9、内置盘 Electron、隔离 HOME 与本地假 API；不读取登录凭据、不调用供应商模型。只把 archive 缺少 .git 的测试版本来源替换为冻结 SHA，产品和业务断言不改。zsh 语法和 Python 3.9 AST 检查通过；即使它随后 PASS，也不能关闭本文两项缺陷。
- 开始与结束的 project_map status 都 rc=1：8 项稀疏 checkout 缺失链接、0 stale living docs。T-108 的“0 问题”条件 **INCOMPLETE**，没有越权补地图。RESULTS/REAL-TURN-PLAN 是当时的截止记录，本报告单独引用随后产生的原件，不改写旧记录。
- 首批局部运行在复制依赖前缺 effect；version/restore 首次又缺 `--experimental-vm-modules`。这些是 setup 失败，不算红态；已生成的失败摘要 candidate-version.json、candidate-restore.json 保留，随后用新输出名取得绿态。新增 hook 反例及三种变异均在依赖完整的候选通过后运行，以业务断言判断。
- 没有截图、没有调用问题面板、没有读真实凭据或重扫其正文，没有写全局配置。已存在的第一轮报告、脚本及 /tmp 现场均保留。只新增本报告、第二轮沙箱外脚本及自己的 /tmp 文件。

RULE:

这是 F1“异常字段不能保留正向状态”的重复类别。现有正式检查只在问题出现之前注入缺字段，无法验证问题出现后的失败。应在 test_t108_questions.mjs 增加“待答问题存在时，当前根 PostToolUse 缺名/响应解析失败 → question unknown、作答拒绝、PTY 零写入”，以及“当前 Stop 缺 stop_hook_active → 拒绝且 unknown”。同时保留“旧 prompt/异 session 不污染当前问题”和“完整无关工具忽略”的对照，并在 T-108 的无模型完成条件中运行。这可以机械检查，无需新增提示词规则、全局 hook 或策略引擎。本 reviewer 不修复、不提交、不自行集成。

T-108 REVIEW NO_GO
