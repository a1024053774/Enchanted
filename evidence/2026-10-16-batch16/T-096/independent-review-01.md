STATUS: FAIL
TARGET: 11b32303bebf276d20026a6e718719d15f5d4068

结论：**NO_GO（需修复）**。确认一处窗格集恢复缺陷：明确关闭最后一个窗格后，空集被当作“没有保存过布局”，重新打开工作台会重新加入当前 worker。指定的七场原生实跑证据成立，但没有覆盖这个边界，不能据此给整个候选 PASS。

本审查为 T-096／attempt a1／writer s16-t096 的独立只读审查，比较起点为 `3c9016d02`。开始先读共享仓库 reviewer 角色卡，再以 `git show main:.project-map/tickets/T-096-restore-panes-and-sessions-after-restart.md` 读取最新 ticket；核对时共享仓库 main 为 `8e5a976a6844abfa905de311db993473a21348c8`。答案来自 ticket、用户当前派发和裁定 B：两个主控按原启动参数续接；worker 保留“未恢复”，不启动、不重绑定、不改 attempt；不改门禁。RESULTS、运行脚本和新增测试只用于定位与核对。

使用 project-map、behavioral-acceptance-review、design-integrity-review、evidence-first-testing 与 document-writing。没有子 agent，没有模型调用、沙箱升级、commit、checkout、reset、stash、push、submit 或集成。候选源码保持原样；仓库只新增本报告和 `REVIEW-OUTSIDE-01.sh`。

EVIDENCE:

- **冻结版本：PASS。** 开始及完成前 HEAD 均为指定完整 SHA，初始工作区干净。真实绿态使用的 `f2b96001daea2653b01fdbbb0aba4d43387b3b7c`、version-b-02 使用的 `752dc62a179cb0fca8a18670a24b507d1bff471b` 与冻结候选之间，`workbench/src/` 和 `workbench/app/` 均无差异；没有拿不同产品实现的旧结论替本候选背书。red-b-05 所用 main `fbba0002481941ea566d395bc9caa01d790b6689` 与起点在上述产品目录也无差异。
- **原件核对：PASS，范围如下表。** 根目录为 `/Volumes/WD-Elements/a2a-evidence/2026-10-16-batch16/T-096/`。直接读取 before／after、实际 argv、终端读回、合成历史、fake API 请求和 SQLite 事件；SQLite 连同 WAL／SHM 先复制到自己新建的 `/tmp` 目录再查询，未打开原件的可写连接。独立核对结果保存于 `/tmp/t096-review-01-nbuugbud/raw-audit-02.json`。

| 原件 | 独立核对结果 |
| --- | --- |
| red-b-05 | command-47 的原始 JSON／stdout 为 `daemon_call_failed`、`socket exists; query its owner, do not replace it`，退出 1；没有第二 epoch 回执，初始化按键为 0。它证明 main 的死端点阻止重启；**没有观察到第二轮空窗口**，不把产品 NO_GO 写成恢复成功。 |
| tracer-b-05 | 初次实际 argv 等于启动记录；续接实际 argv 只把 `--session-id` 换成 `--resume`，其他每个字段保持相等；原 session／task／role／launch 一致。独立随机 nonce 出现在恢复后 `terminal`，重启前终端没有该 nonce；明确关闭窗格有持久事件。 |
| three-b-01 | 两个主控分别满足上述实际 argv、session 与历史 nonce 条件；新 shell／leader 回执存在。完整 gate-before／gate-after task 相等，包括 current_attempt。worker 显示“未恢复”、只读，无 `pane_restored`，receiver 只有首次启动的一份记录。 |
| no-argv-b-02 | 原始事件明确拒绝 `restore_argv_missing`；窗口显示“未恢复”、只读，无成功事件。 |
| version-b-02 | 明确拒绝 `restore_version_mismatch`；窗口显示“未恢复”、只读，无成功事件；正常退出请求和退出确认均有回执。 |
| no-session-b-01 | 明确拒绝 `restore_session_missing`；窗口显示“未恢复”、只读，无成功事件。该目标没有预置合成历史，原生 session 文件不存在，没有用新会话补位。runner 对已有文件提供改名保留，但本场未找到 `.missing-session-original`，不声称实际执行过改名。 |
| isolation-b-01 | 构思主控因缺 argv 拒绝，执行主控继续按实际原参数恢复并显示自己的历史 nonce；失败窗格无成功事件，worker 未恢复，完整 gate task／attempt 前后相等。首轮界面部分顶层身份字段尚未出现，核对使用同一原始条目里的 snapshot.launch，未把缺字段当成已核对。 |

- **逐屏批准：PASS。** 七场共八个实际初始化的主控 profile、48 次成功写键；每个 profile 严格是主题 ArrowUp／ArrowDown／Enter、须知 Enter、信任 ArrowDown／Enter。逐一比较 `*.startup-keys.json`、SQLite 的 intent／written 事件、`*.approval.json` 和 `*.key-receipt.json`：launch、session、directory、screen_id、key、purpose、selected_label、authorization_ref 均相符，intent 在 written 之前，批准者为 executor。原始屏文件存在，主题／须知／隔离工作区内容与批准用途相符；其后有单独的 startup-ready 批准。原始流包含终端定位控制码，文字检查去除控制码及空白，不改原件。额外的未成功尝试／批准文件仍保留，未计作成功写键。记录见 `/tmp/t096-review-01-nbuugbud/approval-audit.json`。
- **模型回合：PASS，限本次假 API 场景。** 七场 `fake-api-requests.json` 均无 POST，恢复路径不派发提示词或旧队列。历史 user／assistant 对是停止后写入的合成夹具；nonce 证明原生 CLI 显示指定 session 的历史，不是模型生成能力证明。
- **旧失败原件：PASS（保留性）。** red-b-01／tracer-b-01 的 NoneType 失败、no-argv-b-01 的初始化未完成、version-b-01 的收尾未完成仍保留原始 INCOMPLETE 摘要及外置盘目录；没有因后续重跑／清理而改成 PASS。version-b-02 没有重现 version-b-01 那次准确竞态，旧拒绝点缺少 ps 回执的未知仍成立。
- **结构：除下述空集 fallback 外，未确认其他结构缺陷。** `paneRecovery.ts:11` 从记录复制 argv，只替换 session 选择器；`panes.ts:208` 先拒绝 managed attempt，再检查主控、旧进程、argv、task、版本、原生 session 和 trace。版本探针与 PTY 均用原记录的可执行文件／环境，没有默认模型、裸 resume 或新 session 补位。恢复失败按窗格写明确失败事件，清理未确认时保存 `restore_cleanup_unconfirmed` 和原因；不是吞掉失败后成功。启动成功前要求实际前台 executable 的 leader。worker 的 Codex argv 构造仍用于保存原生 session 元数据，恢复入口在此前已拒绝 worker。
- **状态归属：PASS，空集语义另见发现。** 打开／显式关闭通过 operator 请求即时追加 `pane_layout_opened`／`pane_layout_closed`；窗口退出只关闭视图凭据。打开集和原生 session 绑定由同一 SQLite 事件流推导，launch/profile 仍是配置来源；resume_argv 是完整性对照，没有第二套可写 profile。恢复的内存队列为空。以 **Ubiquitous language** 沿用“主控、worker、attempt、launch、未恢复”；新增 helper 承担参数和会话文件验证，未发现另造浅层平行 API 的 **Deep modules** 问题。单主控 **Tracer bullet** 和两主控加 worker 的原件均已核对。
- **端点与 runner：PASS（所覆盖分支）。** transport 拒绝活动／未知 owner、活动 socket、非 socket，并在异步探针后复核 PID 文件；现有合同覆盖这些拒绝。runner 的进程身份变化不准许直接发信号，已接受正常退出后的特定错误仅等待自有 Popen 退出并确认 PID 消失。真实 process-tree-green-01 四场及其原始观察存在：自然退出子进程未收信号，Z 后回收，存活替代命令未收信号，独立 cleanup 均完成；red-02 仍为 INCOMPLETE。此结论不扩大为所有操作系统竞态都已证明。
- **边界：PASS（代码和记录路径检查）。** 从起点到候选没有 `workbench/src/gates/` 变更，没有 Herdr 改动。实跑记录中的 HOME／CLAUDE_CONFIG_DIR／CODEX_HOME 均指向隔离夹具；恢复使用这些原记录环境。没有发现写用户 `~/.claude`／`~/.codex` 的新增路径；本审查也未写它们。没有全局目录写入监视器，因此不声称独立证明了供应商进程的所有文件系统副作用。

独立执行的合同与回归均经 git archive 副本运行，进程／PTY／Electron 边界由夹具提供，未启动真实原生应用：

| 检查 | 结果与证明范围 |
| --- | --- |
| test_t096_restore.mjs | PASS；真实 SQLite／session 文件，两个主控、三个拒绝、worker 不启动、attempt 不变、关闭记录排除、零输入写入。 |
| test_t096_daemon_restart.mjs | PASS；clean／dead／alive／unknown／PID 文件变化／活动 socket／非 socket；已知坏起点被拒绝。 |
| test_t091_pane_ipc.mjs | PASS；原有键绑定、跨窗口／iframe 拒绝、序列号、输出路由、旧 attempt、关闭竞争仍成立；原有两个坏版本仍被原断言拒绝。新增关闭／恢复断言没有覆盖空集。 |
| test_t091_claude_version.mjs、test_t091_driver_selection.mjs、test_t091_start.mjs | PASS；版本拒绝及变异、明确窗格选择和全文输出、三份 launch 转发。 |
| test_t078_controller_window.ts、test_t078_screen_key.ts | PASS；主控 nullable attempt、旧 worker／撤销／spec 拒绝，以及主题／信任逐键限制。 |
| project_map.py status | 开始和完成前均为退出 0、0 problems／0 stale living docs。 |

首个 archive 副本缺 `effect`，恢复合同首跑未执行成功；接入仓库现有 node_modules 的只读来源后通过，未安装依赖、未把缺依赖算红态。独立 PTY 断言最初误用了 shell 参数索引 2，修正为 `-c` 后的索引 3，再先确认候选通过才做最终变异。两次审查工具错误的日志保留在临时证据目录，不混入产品缺陷。

FINDINGS:

- **[P2] workbench/app/main.ts:167 — 已保存的空窗格集被默认选择覆盖。** `saved = launches.length > 0` 无法区分“从未保存过”与“用户明确关闭全部”；下一行把空集改为 `[undefined]`。可达路径是当前 worker 仍在后台运行 → 只打开该窗格 → 点击“关闭窗格”，确认 pane_layout 已为空 → 关闭并重开 Electron，不传 `--launch`。这符合后台常驻的日常使用方式。`daemon.ts:253` 对未指定 launch 的 snapshot 返回 current_attempt 的 worker；`main.ts:88` 又把它 `pane_layout_open` 落盘，已关闭的窗格重新出现。独立检查实际 main/preload 的 IPC 路径，断言 `Explicitly closed final pane must stay absent when app reopens` 失败于 **1 !== 0**。这不是初始化／依赖失败，也不依赖模型或 UI 时序。最小修正是从现有事件流保留“明确空集”的含义，允许空窗格视图；只有从未建立布局时使用默认选择，不能再按集合长度判断。需增加“关闭最后一格→退出／重开→仍为空”的业务回归。本审查没有实现修复。

COUNTEREXAMPLE:

三个单处变异均只修改 `/tmp` 的 panes.ts 副本，先确认冻结候选通过，再运行同一业务断言。每份变异源码、完整命令、stdout、stderr、退出码和 JSON 均保留。

| 变异 | 现有合同 | 独立业务断言 |
| --- | --- | --- |
| M1：恢复交给 PTY 的命令只保留可执行文件、`--resume`、session，事件仍记完整 argv | **错误地 PASS**；原测试第 90 行比较的是事件 argv，没有检查所捕获的 spawn 参数。 | **拒绝，退出 1**：`Actual PTY command must carry the supplied model and effort sentinel`。独立新增断言使用夹具输入的 model／effort sentinel 检查实际交给 PTY 的命令。 |
| M2：把 `pane_restore_failed` 事件名改成 `pane_restored` | **拒绝，退出 1**。 | 同样拒绝：`A failed pane must not have a success receipt`。 |
| M3：recover 开头把 task.current_attempt.state 改成 ready | **拒绝，退出 1**。 | 同样拒绝：`Worker attempt must remain byte-for-byte unchanged`。 |

M1 是局部合同测试的证据缺口，不等于真实端到端 oracle 失效：`run_restart.py:463` 另有内核实际 argv 与外部输入的逐字段比较，本次原件也已独立核对；该比较会拒绝 M1 的参数差异。本轮用独立 PTY 边界断言机械拒绝 M1，没有假称在真实 Claude 上运行了变异。建议把这个廉价断言纳入现有合同用例，避免事件自证。

完整可复现命令：

```sh
sh evidence/2026-10-16-batch16/T-096/REVIEW-OUTSIDE-01.sh
```

脚本重新 git archive 指定冻结 SHA 到新 `/tmp` 目录，不建 worktree。先跑候选基线，再跑三种变异和空集探针；期望输出 **NO_GO**、退出 **1**，且 results.json 同时确认三个变异被业务断言拒绝、空集缺陷复现，才表示复现成功。初始化失败或单独的退出 1 不能当作反例。本审查已实际运行脚本，结果在 `/tmp/t096-independent-replay-5m83hpmx/results.json`，三个独立变异断言均拒绝，空集缺陷复现。脚本语法检查通过。它不启动真实 Electron／daemon／CLI，无须逐屏批准；本轮没有必须交主控在沙箱外执行才能确立的发现。

LIMITATIONS:

- 七场真实 Electron／daemon／Claude 是主控此前运行的原件，本审查只读核对；新执行的是合同级检查。没有重新真实登录、真实模型回合或全局写入监视。
- 空集缺陷已在实际 main/preload 模块、替代 Electron／transport 边界重现；已核对真实 daemon 的默认 worker 选择规则。未声称完成了该新增边界的真实 Electron 重跑，也未声称后台同时重启时会启动 worker CLI。
- 只对本冻结候选和裁定 B 作结论；worker 自动续接／门禁重绑定不在范围内。没有检查真实模型对权限／上下文的理解能力。
- 只核对相关 T-078／T-091 回归及本票原生原件，没有跑全仓测试，也不把已有局部通过扩大成完整回归通过。未重跑已经归档的失败场景。

RULE:

- 现有测试有“关闭一格后删除”的规则，但缺少集合边界 **0**。在 T-091 IPC／T-096 布局合同入口加入“关闭最后一格后重新打开”的检查即可捕获本发现，不需要新增权限规则或平行状态表。
- 本票完整 argv 契约已有真实内核读回 oracle；局部测试还应核对实际 spawn 输入，防止日志正确、行为错误。无需新增文字规则替代机械断言。

T-096 REVIEW NO_GO
