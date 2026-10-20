STATUS: NO_GO

TARGET: `afcc78b0d856680491f0e99410b7ff9acec54dab`，起点 `6411bdff8482ba47da207efa6a295a12666222aa`，分支 `exec/t108`。

2026-10-20，T-108 第一轮独立 reviewer。结论：**需修复 F1**。正常提问与作答路径有实证，三个错误实现也被现有断言拒绝；但另外构造的缺字段输入在未修改候选上仍显示“运行中”，违反本票的明确反例条件。不能据正常路径通过给整票 PASS。

EVIDENCE:

- 按派发顺序读取了主仓库 reviewer 角色卡、本 checkout 的 AGENTS.md、T-108/T-093/T-095/T-071，以及 RESULTS、REAL-TURN-PLAN、CONFLICT-LINES。稀疏 checkout 的 T-108/T-093 没有同日裁定追加，因此另读 `/Users/luckye/Documents/Code/a2a/.project-map/tickets/` 中这两票的 2026-10-20 裁定。版本判断按用户逐字“跑真实回合,版本不重要,以后肯定要经常更新 cli 版本的”，没有把旧精确版本锁当作验收条件。
- 用 `git show afcc78b0d:<路径>` 和 `git diff 6411bdff8 afcc78b0d -- workbench/src workbench/app workbench/tests` 读取原文；开始与结束的 HEAD 都为上述完整 SHA。起始工作区干净；最终只新增本报告和 REVIEW-OUTSIDE-01.sh。未写候选、地图、术语表或 Git 元数据，未建子 agent，未提交或调用模型。
- 一次性副本来自 `git archive afcc78b0d workbench evidence/2026-10-20-batch18/T-108/native-hook-samples.json`，保留在 `/private/tmp/t108-review-01-ja7ea3bs`。原仓库 Git hook 的符号链接展开为普通文件；依赖复制时解引用，没有创建符号链接或 worktree。Node 26.5.0；Python 3.9.6；测试设置 `LC_ALL=C` 并清除 `GIT_DIR`、`GIT_WORK_TREE`。所有测试数据与临时 Git 仓库均在 /tmp。
- 使用 behavioral-acceptance-review 重建 oracle；按 design-integrity-review 检查真实调用、恢复归属和结构成本；按 evidence-first-testing 先取得候选绿态，再做变异；报告按 document-writing 检查 UTF-8。没有另开审查 agent。

必审项的结果：

| 项目 | 结论与边界 |
| --- | --- |
| 每会话 hook 与未知状态 | **NO_GO，F1**。Claude 的 `claudeLaunch.ts:65` 经 `--settings` 传 hooks；Codex 的 `panes.ts:513` 经 `-c hooks.<事件>` 传入。候选没有新增全局配置写入。`tool_input` 缺字段会记录 unverified 并显示未知，但 `tool_name` 缺失提前静默返回，仍显示运行中。完全没有事件送达的故障，本轮没有独立注入，不宣称全覆盖。 |
| 提问、作答、回落 | **PASS（已验证路径）**。独立合同 12 项通过；真实回合的 SQLite 原件有同一问题的 opened、answer_intent、三次 PTY 按键、answered、匹配 prompt_id 的 Stop 和 pane_idle；一条 answer 的 reply_to、target.request 与 target.thread 关联原问题、原窗格。发送中和已答后重复均有拒绝证据。 |
| 受管 worker 门禁 | **PASS（静态与合同边界）**。`daemon.ts:263` 的 assertCurrent 核对当前 attempt/session/fence/spec/reclaimed，在写入前及逐键写入时调用；`recordInput` 仍调用门禁 `appendUserInput`，该方法对受管 attempt 追加 human_intervention。没有 answer 自行认领、submit、集成或恢复 attempt 的路径。实际 worker 生命周期与作答的一体化真实 CLI 场景没有新跑。 |
| 三处版本变动 | **PASS（审查范围）**。只把发行号等值改为合法版本值及本次观测值核对，保留私有 session/manifest 等值、进程身份、auth_original_reads=1、一次消费、隔离与 HOME 禁写、网络策略和清理。缺 CLI、探针失败、版本取不到/不合法及不匹配仍拒绝；独立版本合同和恢复拒绝合同通过。真实启动记录的 cli_version 为 `2.1.304 (Claude Code)`，role_card_revision 为 `T-093/normal-login/2.1.304`，最终 facts 的 cli_version/internal_state_version 均为 `2.1.304`。 |
| 模型请求计数 | **PASS**。1 个根输入、3 条生成请求，账本与事实摘要对得上；额外一条是根输入之前的启动辅助请求，返回 429，详见下表。其具体辅助用途未保存，不能进一步命名。 |
| 结构化信号与 Codex 缺口 | **PASS（边界明确）**。工具名、session、prompt/turn、tool_use_id、cwd、transcript 原件用于关联；没有用屏幕文字或正则判断提问意图。版本格式与控制字符校验中的正则不承担语义识别。Codex 为真实安装的 0.163.0 CLI 在本地假 API 下产生的 hook 原件回放；本轮回放通过，未冒称供应商真实模型或活 PTY 的新证据。异步阻塞未知、多选写回未验证均已明示。 |
| T-107 F2/F3、IPC | **PASS**。实际 daemon/socket/Panes/SQLite/trace 的 identity 与 readonly 模式通过，两个场景均正常关闭。侧栏 projection、只读写入变异也通过判别。IPC 仍保留旧 handler/bridge 及身份、跨窗口、iframe、历史只读等拒绝检查，只增加 answer。 |
| 结构审查 | **NO_GO，F1 为静默降级缺口**。questionFromHook 的异常边界由信号入口记录 unknown 后重新抛出，PTY 写失败由 Panes 记录未知失败，没有新增重试、兼容实现或第二门禁。questions.ts 承担字段核对、事件投影与 CLI 按键协议，属于 Deep modules 的实质责任。F1 在进入这些核对前丢弃异常形状。 |

真实回合原件核对：

- `/private/tmp/t108-real-01.summary.json` 标明候选完整 SHA、1 次根输入、model_calls=3、vendor_calls=3、六项 PASS。独立只读核对 `/private/tmp/t108-real-a4e5c18d14/state/state.sqlite3` 的 launch、hook 与问题事件，以及该 launch 的 `forwarder/journal/requests.jsonl`，会话身份和时序一致。
- journal 有 5 个 request 与 5 个 outcome。前两个是无 bearer 的 `HEAD /api/hello`，本地拒绝为 401；后三个是被转发的 `POST /v1/messages`，全部纳入 model_calls，包含失败请求。不是把根输入数当成 API 次数。

| 序号 | 发起时间（UTC） | 请求体声明字节 | 结果 | 独立判断 |
| --- | --- | --- | --- | --- |
| 3 | 06:28:16.801 | 278 | 429 | 启动辅助请求；它早于首次终端粘贴 06:28:18.571、根提交 06:28:18.788 和 UserPromptSubmit 06:28:19.001。不是该根输入的重试。 |
| 4 | 06:28:19.034 | 23015 | 200 | 根输入后的提问生成；之后出现 PreToolUse/AskUserQuestion。 |
| 5 | 06:28:30.273 | 23656 | 200 | PostToolUse 确认答案后的续接；随后 Stop。 |

第 3 条的具体功能仍 unknown：账本只保留请求路径、大小、时间及结果，没有正文；隔离 HOME/debug 已随正常清理删除。根据时间可确定它是启动辅助流量，不能把它进一步写成某种特定探测，也不能漏记其 429。本 reviewer 未读任何真实凭据，未为查明用途补跑模型。

主控提供的另两份原件也已读取：无模型完整入口 `/private/tmp/t108-native-e2e-03.json` 六项 PASS；版本探针 `/private/tmp/t108-version-probe-01.json` PASS、模型/供应商调用 0、credential_scan_hits=0、isolated_home_removed=true。探针记录当前版本、生成的 onboarding/trusted cwd 与 OS 拒绝检查。真实 facts 保留 HOME 禁写的 C/F/D 策略、auth_original_reads=1、隔离 HOME 清理和凭据扫描 0。以上属于对主控运行原件的审查，本 reviewer 没有重新读取原始 auth 或重跑登录。

FINDINGS:

- **[P1] F1 — `workbench/src/panes.ts:1032`：缺少 tool_name 的工具 hook 被当成无关工具静默丢弃，状态仍为运行中。**
  - 独立期望来自 T-108 Acceptance：“hook 不触发或字段缺失时显示‘未知’而不是运行中/空闲”，以及 T-071 的未知不上调约束。
  - 输入：已关联当前根 submission 的合法 UserPromptSubmit，随后送入同 session/prompt/cwd/transcript/tool_use_id、含合法 questions 的 PreToolUse，仅省略 `tool_name`。用实际 `Panes.signal → SQLite → agentState`；无模型，PTY/进程身份为受控边界。
  - 结果：`questionTool(undefined)` 为 false，1032 行直接 return，既不拒绝也不追加 native_question_unverified。`questionState` 找不到缺口事实，侧栏继续采用已有 turn_start_signal，输出 `running`。问题条目也没有生成。
  - 证据：`/private/tmp/t108-review-01-ja7ea3bs/missing-tool-name.json`，rc=1，业务断言为 `running != unknown`。这是**原候选失败**，不是变异失败、依赖失败或夹具崩溃。
  - 最小修正方向：在分类“无关工具”前核对工具事件的必要字段；当前根事件字段不足时保存可投影的未知事实并拒绝，合法的具名无关工具仍可忽略。保留既有身份/过期 hook 拒绝语义；不要用屏幕文字补判。增加此字段缺失反例，要求候选拒绝上调；现有 `test_t108_questions.mjs:76` 只测 `tool_input` 缺 questions，无法覆盖这个提前返回。
  - 重放命令（保留的 /tmp 源码与夹具）：

```sh
env -u GIT_DIR -u GIT_WORK_TREE LC_ALL=C node \
  /private/tmp/t108-review-01-ja7ea3bs/candidate/workbench/tests/review_missing_hook_field.mjs \
  /private/tmp/t108-review-01-ja7ea3bs/missing-tool-name-repeat.json
```

COUNTEREXAMPLE:

先运行未变异候选，再在三个独立副本分别改一处。期望来自 ticket 的 unknown、重复拒绝和侧栏只读约束。变异文件与精确替换文本保存在 `/private/tmp/t108-review-01-ja7ea3bs/mutations.json`；所有失败都命中业务断言。

| 变异 | 单处错误 | 同一检查的结果 |
| --- | --- | --- |
| M1 | questions.ts:60 把缺字段的 unknown 改成 idle | 原候选 questions 合同 rc=0；M1 rc=1，`Missing question fields must remain unknown`，idle != unknown。 |
| M2 | questions.ts:52 收到 answer_intent 后仍保持 waiting | 原候选 rc=0；M2 rc=1，在发送中重复答复的 `assert.rejects` 报 Missing expected rejection；不是 setup 失败。 |
| M3 | sidebarSnapshot 起点额外 `store.event('sidebar_read', ...)` | 原候选 projection 与实际 daemon readonly 均 rc=0；M3 两者均 rc=1，`Sidebar read changed persisted tables or traces`；daemon cleanup_complete=true。 |

精确命令（`B` 为上述独立临时根；每次输出换一个新文件名）：

```sh
B=/private/tmp/t108-review-01-ja7ea3bs
env -u GIT_DIR -u GIT_WORK_TREE LC_ALL=C node "$B/candidate/workbench/tests/test_t108_questions.mjs" "$B/candidate-questions-repeat.json"
env -u GIT_DIR -u GIT_WORK_TREE LC_ALL=C node "$B/m1-unknown-idle/workbench/tests/test_t108_questions.mjs" "$B/m1-repeat.json"
env -u GIT_DIR -u GIT_WORK_TREE LC_ALL=C node "$B/m2-duplicate/workbench/tests/test_t108_questions.mjs" "$B/m2-repeat.json"
env -u GIT_DIR -u GIT_WORK_TREE LC_ALL=C node "$B/candidate/workbench/tests/test_t107_sidebar.mjs" "$B/candidate-sidebar-repeat.json"
env -u GIT_DIR -u GIT_WORK_TREE LC_ALL=C node "$B/m3-sidebar-write/workbench/tests/test_t107_sidebar.mjs" "$B/m3-repeat.json"
env -u GIT_DIR -u GIT_WORK_TREE LC_ALL=C T107_DEPENDENCIES="$B/node_modules" node --experimental-vm-modules "$B/candidate/workbench/tests/review_t107_daemon_readonly.mjs" "$B/daemon-readonly-repeat.json" "$B/candidate" readonly
env -u GIT_DIR -u GIT_WORK_TREE LC_ALL=C T107_DEPENDENCIES="$B/node_modules" node --experimental-vm-modules "$B/candidate/workbench/tests/review_t107_daemon_readonly.mjs" "$B/daemon-identity-repeat.json" "$B/candidate" identity
env -u GIT_DIR -u GIT_WORK_TREE LC_ALL=C T107_DEPENDENCIES="$B/node_modules" node --experimental-vm-modules "$B/candidate/workbench/tests/review_t107_daemon_readonly.mjs" "$B/m3-daemon-repeat.json" "$B/m3-sidebar-write" readonly
```

`review_t107_daemon_readonly.mjs` 只把原测试的一条 symlinkSync 改为 cpSync/dereference，以遵守不建符号链接；产品与断言没改。副本依赖是复制的普通文件。该 harness 真实启动 daemon/socket，但 CLI/PTY 身份由夹具提供，不能推成真实 CLI 生命周期证明。

其他已运行绿态均为 rc=0，摘要在临时根：candidate-codex.json（5 项）、candidate-ipc.json（原 IPC 拒绝及新 answer）、candidate-version.json（8 项）、candidate-profile.json（4 项）、candidate-restore.json（恢复拒绝与原变异）。命令分别为 `node [--experimental-vm-modules] "$B/candidate/workbench/tests/<脚本>" <新摘要>`；脚本依次是 test_t108_hook_replay.mjs、test_t091_pane_ipc.mjs、test_t091_claude_version.mjs、test_t093_launch_profile.ts、test_t096_restore.mjs。Codex 命令另外带 `--samples "$B/candidate/evidence/2026-10-20-batch18/T-108/native-hook-samples.json" --summary <新摘要>`。这些依赖原 Git 历史的检查从本 checkout cwd 运行，仅执行 git show，不写主仓库 .git。

LIMITATIONS:

- **INCOMPLETE：项目地图 0 问题条件未满足。** 会话开始与结束的 `python3 /Users/luckye/Documents/SKILLS/project-map-skill/project-map/scripts/project_map.py status --root .` 都是 rc=1、8 项缺失链接、0 stale living docs；与交付记录所述稀疏检出缺口一致。没有越权补齐地图或把结果上调为 0。
- 本 reviewer 模型/供应商调用均为 0；没有启动 Electron 或申请沙箱升级。需要主控沙箱外执行的独立无模型完整入口已写入 `REVIEW-OUTSIDE-01.sh`，**尚未执行**；zsh 语法及内嵌 Python 3.9 AST 已通过。它重新 git archive 冻结候选、复制依赖、不建链接，使用内置盘 Electron 和本地假 API；只替换测试中 archive 缺失的 Git 版本来源，不改产品或业务断言。它不能替代 F1 修复。
- 本轮未独立重跑 OS 沙箱的 HOME 写入反例或供应商回合；隔离结论来自差异审查及主控所给原件，不声称新取得 OS 层绿态。未调用问题面板、未读取真实凭据，也未重复凭据内容扫描。
- T-108/T-093 同日裁定来自主仓库最新 ticket，候选内的日期报告仍停留在“待外部运行”的截止点；本报告明确引用随后产生的原件，不改写旧记录。

RULE:

F1 应由信号入口合同检测：在 `workbench/tests/test_t108_questions.mjs` 加入当前根 hook 缺 tool_name 的输入，并经真实状态投影断言 unknown；在 T-108 完成条件中运行。现有“只测 questions 字段缺失”的测试不足。修复后定向重跑该反例与现有重复、过期身份、无关具名工具的合同，再交执行主控验收；本 reviewer 不修复、不重新自审、不集成。

T-108 REVIEW NO_GO
