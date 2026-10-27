# T-195 独立只读审查（第 2 轮）

## STATUS

**NO_GO**。第 1 轮 F3 的读取失败问题已修复；F1、F2 只关闭了部分场景，尚未在身份拥有层完整关闭。本轮确认 5 条发现，其中 4 条可能给出错误的可用链接，1 条导致新进程已经报告会话号仍持续置灰。

冻结对象：`/private/tmp/t195-cand2`，提交 `b6c2600b2ea95d0dbeb703cb07754e9b57aad326`；范围为相对 `c7f2a92` 的 T-195，重点核对相对 `ac78313` 的 v2 修复。开始与结束的 HEAD 一致，受控文件和暂存区无差异；既有未跟踪的 `workbench/node_modules` 链接保留。未修改候选、原仓库、ticket、用户配置或既有证据，未提交。新增探针、合成数据、构建产物与报告均在本审查目录。

验收依据：原仓库 T-195 ticket、T-189 第 4 条，以及本轮 brief。复制文本应包含 CLI 名、当前原生会话 ID 和对应记录路径；不能确定时应置灰并说明原因。沿用 **Ubiquitous language**，区分启动记录、agent 会话、原生会话及 CLI 进程，不把文件存在或进程同名当成当前身份的证明。

第 1 轮发现的逐条结论：

| 原发现 | 本轮结论 | 依据 |
| --- | --- | --- |
| F1：会话变化后仍给旧号 | **未完全关闭** | 终端查询已不再读取历史角色申请；普通的新 hook 能更新 Claude ID，Codex 已记录第二线程事件时会禁用。但受管 Claude 直接信任被拒绝的 hook，恢复后的 Codex 收集器又可能根本不产生第二线程事件。见 R4、R5。 |
| F2：同终端 opencode 重启继承旧号 | **未完全关闭** | 已绑定旧 PID 与新 PID 不同时，常规查询正确禁用；但 OSC 的 PID 是异步观察时补上的，并非报告发送者的身份，可把旧报告重新绑定给新进程。另有同 ID 重启后无法恢复可用的问题。见 R1、R2。 |
| F3：agy 读不了被当作不匹配 | **该缺陷已关闭** | 两库之一持有真实 SQLite 排他锁，以及另有损坏库时，都返回不可用并明确写“读不了”；未再挑出另一库冒充唯一匹配。此结论不代表 agy 当前会话识别整体通过，见 R3。 |

## FINDINGS

### R1 · P1 · OSC 报告的异步前台查询可倒序覆盖，也可把旧进程的 ID 绑定给新进程

位置：[panes.ts:319](/private/tmp/t195-cand2/workbench/src/panes.ts:319)，关联第 350–357、359–376 行。

`onData` 收到带 ID 的 OSC 后，每次独立调用异步 `foreground()`，完成时只核对 `front.cli === reported.app`，再把查询得到的 PID 写到报告上。没有报告序号或进程代次核对。`shellNative()` 后面的 PID 相等检查不能发现此前已经绑错的 PID。

独立反例见 [probe-01.json](probe-01.json)：

1. `opencode_foreground_results_reordered`：依次送入 `ses_A`、`ses_B` 两条真实 OSC 字节串；让第二次前台观察先完成，再完成第一次。最终返回 `available:true, session:ses_A`，覆盖了较新的 `ses_B`。
2. `old_osc_observed_after_same_name_restart`：进程 301 发出 `ses_A`，前台观察尚未完成；同名进程 302 已启动且从未报告 ID。观察返回 302 后，代码保存 `{pid:302, session:ses_A}`，查询返回可用的旧会话。

探针调用实际 `startShell()` 注册的 `onData` 回调，只控制 PTY 和前台观察 Promise 的完成顺序；没有改候选。第一例证明倒序覆盖，第二例证明“当前观察的进程”不能替代“报告它的进程”。本轮没有测量真实 opencode 出现该时序的频率。

修复方向：在 Panes 的现有身份拥有层保留报告顺序和可验证的进程代次；过期观察不得更新绑定。不能确认发出报告的实例时禁用，不能在异步完成后仅凭同名 CLI 给报告补上新 PID。回归检查应控制两次观察的逆序完成，并覆盖退出后立即重启。

### R2 · P2 · 新进程恢复同一 opencode 会话时，有效报告被去重，链接持续置灰

位置：[panes.ts:319](/private/tmp/t195-cand2/workbench/src/panes.ts:319)。

启动第二个进程后，如果它报告的 ID 与上一进程相同，`pane.nativeReport?.session !== reported.id` 为假，根本不再观察前台，也不更新 PID。之后所有同 ID 报告都被跳过，而 `shellNative()` 一直因旧 PID 不匹配返回空报告。

复现经过真实 node-pty、zsh、现有 opencode shim、macOS 进程观察器和 OSC 解析，CLI 是只实现该协议的最小替身。见 [pty-03.json](pty-03.json) 的 `real_pty_restart_resume_same_session`：

1. 第一个进程报告 `ses_resume`，链接可用，保存 PID 28300。
2. 退出并在同一终端重新启动。新进程首次无 ID 时正确置灰。
3. 新进程再次报告 `ses_resume`，原始 trace 中确有这条 OSC；当前前台 PID 为 28367。
4. 查询仍置灰，原因却说“还没报来会话号”；绑定仍停在 PID 28300。

同一原生会话跨进程恢复是有效输入，不能要求每次进程启动都产生不同 ID。候选 facts 也记录了 `opencode --session <ID>` 这一入口，但本轮未启动真实 opencode 执行恢复命令。

修复方向：只在完整进程绑定和会话号均相同时去重；新实例报告相同原生 ID 时仍须完成归属核对。将“同 ID 恢复”加入现有重启场景，不能只测 `ses_first → ses_second`。

### R3 · P1 · agy 按终端启动目录查记录；用户 `cd` 后会复制另一目录的旧会话

位置：[nativeLink.ts:61](/private/tmp/t195-cand2/workbench/src/nativeLink.ts:61)，关联第 89–109 行。

终端的 `record.worktree` 是 `startShell()` 时保存的目录，后续 `cd` 不更新它。agy 分支忽略当前进程的会话归属，直接按这个旧目录找唯一数据库。

真实 PTY 复现见 [pty-03.json](pty-03.json) 的 `real_pty_agy_after_cd`：在终端启动目录 A 留一份旧会话 `previous-at-shell-start.db`；另一份合成记录 `current-in-other-cwd.db` 指向 B；通过 `shellInput()` 执行 `cd B; agy`，确认 agy 在前台。查询却返回 `available:true`，会话和记录都是 A 的旧记录。判据允许返回 B 的记录，或在无法确定时禁用；返回 A 的旧记录违反两者。

另一个独立反例 `agy_unique_previous_record_before_new_is_written` 说明，即使没有 `cd`，新实例尚未写出自己的库时，目录中唯一的旧库也会立即变成“当前会话”。第 1 轮 F3 的异常处理修好了，但“一个匹配文件就证明属于当前实例”仍缺少依据。

修复方向：不能把启动目录的唯一匹配升级为当前原生会话身份。需要当前 CLI 实例与记录的可验证关联；拿不到关联就禁用并说明原因。只改为读取当前 cwd 仍不足以解决同目录的新实例尚未写出记录这一窗口。

### R4 · P1 · 恢复后的受管 Codex 只扫描旧文件，新线程禁用条件不会被触发

位置：[nativeLink.ts:43](/private/tmp/t195-cand2/workbench/src/nativeLink.ts:43)；直接原因在 [panes.ts:1243](/private/tmp/t195-cand2/workbench/src/panes.ts:1243)，恢复初始化见第 690、708–712 行。

v2 依赖 `native_record` 中出现不同的根线程 `session_meta` 才禁用旧链接。但恢复路径给 pane 设置 `nativeFile`，收集器随后固定只读该文件，不再发现工作区里新建的其他根线程文件。因此查询新增的保护分支看不到它需要的事实。

`restored_codex_new_root_file` 按恢复路径的字段构造 monitor pane：旧线程已绑定，`nativeFile` 指向旧 rollout，offset 在其末尾；随后在同一工作区创建第二份完整、文件名与 ID 对应的 `source:'cli'` rollout。调用实际 `Panes.scan()` 后没有新线程事件，`nativeLink()` 仍返回旧线程的可用链接。见 [probe-01.json](probe-01.json)。

同一探针随后仅补入第二线程的 `native_record`，`codex_if_new_meta_event_exists` 就正确禁用。这一配对证明问题在收集器与查询之间的事实缺口，而非查询条件拼写或记录文件没准备好。该用例是文件与恢复状态夹具，没有声称本轮实际恢复过真实 Codex 并执行 `/new`。

修复方向：在现有运行身份/收集器拥有层识别新根线程并失效旧绑定；让恢复与首次启动使用同一条身份变化事实。不要只在复制函数里判断一条恢复路径不会产生的事件。回归应先恢复，再创建第二根线程文件，经收集器到查询完整复验。

### R5 · P1 · 受管 Claude 的复制身份读取原始 hook 日志，被拒绝的旧/子会话 hook 仍能覆盖当前 ID

位置：[nativeLink.ts:28](/private/tmp/t195-cand2/workbench/src/nativeLink.ts:28)；原始事件先写后验证的位置为 [panes.ts:1674](/private/tmp/t195-cand2/workbench/src/panes.ts:1674)，排除旧/子事件见第 1693–1711 行。

`hook_received` 是入口日志，不是通过归属验证的会话变更事件。查询却扫描全部日志，选最后一个 JSON 中非空 `session_id`；不检查该 hook 是否被拒绝、来自子 agent、属于哪个 prompt，或是否应改变当前原生会话。

更贴近现状的配对探针见 [hooks-01.json](hooks-01.json)，源码为 [probe-hooks.mjs](probe-hooks.mjs)：

1. 保持启动记录及 `pane.native` 为 `old-startup`，符合当前代码在 `/clear` 后没有更新这两处绑定的状态；外部场景指定 Claude 已切到 `new-current`，两份合成 transcript 均存在。
2. 经实际 `Panes.signal()` 报告新会话。状态路径拒绝 `hook_native_session_mismatch`，但复制查询因原始日志返回 `new-current`。
3. 随后送入旧会话的子 agent hook；`signal()` 明确拒绝 `hook_origin_or_turn_mismatch`。
4. 查询仍把这条被拒绝的入口日志当成身份来源，返回 `available:true, session:old-startup`。

这是已拒绝事件仍影响复制结果的确定反例；本轮没有用真实 Claude 触发这组延迟/子 agent 回调。较早的 [probe-01.json](probe-01.json) 还保留了另一个显式当前绑定夹具的同类反例。

修复方向：由已有身份拥有层确认当前根会话的变更及失效，复制查询读取该投影。不能将修复做成忽略所有不同 ID 的 hook，否则又会阻断 `/clear`；也不能把入口日志当成绕过归属校验的第二条身份路径。

## EVIDENCE

### 本轮独立检查

全部使用 Node `v26.5.0`；SQLite 文件、会话内容与 CLI 替身均为本审查构造的合成数据。

| 检查 | 实际结果 | 产物 |
| --- | --- | --- |
| 实际 `nativeLink()`、`Panes.scan()`、`Panes.signal()`；真实 SQLite；可控 PTY/观察时序 | 16 项：10 PASS、6 FAIL，退出 1 | [源码](probe-v2.mjs)、[结果](probe-01.json)、[stderr](probe-01.stderr) |
| 真实 PTY、zsh、shim、macOS 进程观察；合成 CLI 和记录库 | 3 项：1 PASS、2 FAIL，退出 1，无运行异常 | [源码](probe-pty.mjs)、[结果](pty-03.json)、[stderr](pty-03.stderr) |
| 实际 signal → 原始事件 → nativeLink 配对 | 1 PASS、1 FAIL，退出 1 | [源码](probe-hooks.mjs)、[结果](hooks-01.json)、[stderr](hooks-01.stderr) |
| 标准 renderer/main/preload 构建 | PASS，退出 0；有超过 500 kB 的 chunk 提示 | [命令](build-01.json)、[stdout](build-01.stdout)、[stderr](build-01.stderr) |
| 候选冻结状态 | HEAD 不变；受控工作区和暂存区差异均为 0 | [初次保存](candidate-check.json)、[报告后复核](candidate-check-final.json) |
| 原仓库 project-map status，开始与结束 | 均退出 0，Problems 0、Stale living docs 0；未改地图 | [结束输出](map-status-end.txt) |

真实 PTY 的 `shell_child_fails_closed` 通过：运行 `sh -c 'opencode; :'` 后，观察器识别到的前台进程组 leader 是 `sh`，子 CLI 的 OSC 未被冒认为 shell 自己报告的身份，查询禁用。这只证明该场景没有错误可用链接；当前实现不支持从这类包装 shell 识别有效子 CLI，原因文本笼统地说“前台没有四家 CLI”。

直接探针还通过了普通 opencode 不同 PID/不同 ID 的更换、终端 Claude hook 更新、CLI 退出与新 PID 后旧 hook 失效、Codex 第二线程事件已经存在时禁用，以及 agy 锁库和损坏库的错误说明。异步 OSC 的两个 FAIL 是可控调度证据，不是靠重复运行碰到一次后丢弃其他结果。

保留的中间结果：

- [pty-01.json](pty-01.json) 复现前两条 PTY 失败；[当时源码](probe-pty-01.mjs) 对 agy 的预期比契约更严格，后来明确允许“不可用且说明原因”，未改变候选。
- [pty-02.json](pty-02.json) 仍复现这两项，随后对子 shell 的等待超时。原因是探针误要求 `argv[0]` 必须以 `/sh` 结尾，实际为 `sh`；[当时源码](probe-pty-02.mjs) 保留。修正这一夹具判据后才得到 `pty-03`，未将超时称为产品失败或完整通过。
- [probe-v2-01.mjs](probe-v2-01.mjs) 保存第一次直接探针的源码；当前 `probe-v2.mjs` 与其相同。

复现命令如下；必须换用未使用的夹具目录及输出文件，保留已有失败证据：

```sh
node /private/tmp/t195-review2/probe-v2.mjs /private/tmp/t195-review2/fixtures-replay > /private/tmp/t195-review2/probe-replay.json 2> /private/tmp/t195-review2/probe-replay.stderr
node /private/tmp/t195-review2/probe-pty.mjs /private/tmp/t195-review2/pty-replay > /private/tmp/t195-review2/pty-replay.json 2> /private/tmp/t195-review2/pty-replay.stderr
node /private/tmp/t195-review2/probe-hooks.mjs /private/tmp/t195-review2/hooks-replay > /private/tmp/t195-review2/hooks-replay.json 2> /private/tmp/t195-review2/hooks-replay.stderr
```

构建实际命令为 `node app/build.mjs --slot review2`，cwd 为候选 `workbench`，`TMPDIR/TMP/TEMP` 均设为本审查目录下的 `build-root`。输出保存在 `build-root/a2a-build-review2/dist`；重跑必须使用新的构建 slot。

### 既有绿态、红态和 mutant

只读审计了原仓库 `evidence/2026-10-27-batch28/T-195/` 的指定 JSON 及候选测试源码：

- `green-06.json` 的确记录 12 项 PASS。真实 Claude 的两条指定 prompt 分别定位到不同 transcript ID；退出后禁用。真实 Codex/Claude worker 的首次记录核对仍有价值。它没有覆盖本轮的同 ID 恢复、观察逆序、`cd`、恢复后第二线程或被拒绝的 hook。
- `green-05.json` 保留的是 `FileNotFoundError`：记录尚未存在。v2 现在对受管 Claude 的已选路径检查存在性，本轮构建和直接探针没有复现那条初始错误；不把这一点扩大为所有文件系统故障已验收。
- `red-ac78313.json` 在终端 Claude 等待报号处超时；它证明 v1 没有满足新增的终端场景，不能单独证明真实 `/clear` 后返回旧 ID 这一更细的断言被命中。
- `mutant-report-of-any-process.json` 去掉查询时 PID 比较后，确实在 `opencode_restart_does_not_inherit` 上返回上一实例 ID 并触发断言。`mutant-unread-is-mismatch.json` 确实在锁库场景返回另一库并触发断言。两份文件状态字段虽为 `INCOMPLETE`，其 `error` 和已保存结果包含预期的业务反例；没有把它们算成绿态。
- `green-06` 和这些 mutant 摘要没有绑定完整的本次冻结提交（正常运行 `revision:null`）；本报告将其作为留存的外部证据，不宣称它们逐字运行了本次候选。

替身忠实覆盖了“首报无 ID、后报有 ID、进程占据前台、退出”这些已记录的 opencode 协议事实，以及 agy 的 SQLite 锁冲突。它们没有证明真实 CLI 的实例归属、内部 protobuf 格式和写库时序。尤其既有 agy 替身只占前台，测试先造 `conv-one` 再启动它，然后把唯一库当正例；这预设了待证明的当前归属。opencode 替身的两次运行只用不同 ID，也不会暴露 R2。

### 结构、调用链及说明一致性

复核了会话行右键 → preload → main IPC → `native_link` → clipboard 调用链；菜单项根据 `available` 阻止复制，并有置灰样式和原因文字。v2 没有改变这条 UI 路径；本轮未操作 Electron 窗口或剪贴板。按 **Tracer bullet** 的验收要求，后续修复仍需经过真实右键复制并读回结果，后台夹具不能替代这一层。

新增数据库异常边界属于查询层把原生库读取故障转为不可用原因的职责，未发现用重试掩盖该错误；第 1 轮的裸吞异常已移除。问题主要是身份事实的归属和两条读取路径不一致：终端经 Panes 查询进程绑定；受管 Claude 却绕过该拥有层，从未经验证的入口日志推导当前身份。按 **Deep modules** 的原则，修复应收回现有身份模块，而非继续给复制功能叠加猜测分支。`native_link` 本身仍是一个后台查询入口，没有另造一套门禁。

README “前台换了进程就不再沿用旧号”受 R1 限制，“只给现在这个会话”受 R3–R5 限制。README 所说“记录路径取自轨迹归档已认得”也不完整：受管 Claude 的新 ID 可以通过 `claudeRecord()` 扫描找到，`TrajectoryArchive.sources()` 的该分支仍只认启动 `native_session`。facts 和 README 仍把 Codex 的 `pane_native_session` 说成 hook 报号，实际绑定由 `Panes.scan()` 从 rollout `session_meta` 产生；终端 Codex 才走新增的 hook 报号路径。报告不改这些只读文件。

同类失效绑定再次出现，建议通过项目现有流程建 task，将 R1–R5 的反例接入 T-195 验收入口：报告逆序、实例更换与同 ID 恢复、目录变更、恢复后新根线程、被拒绝 hook 不得改变身份。已有 `--mutant` 机制可继续验证这些断言能拒绝对应坏实现；本审查不建票或改测试。

## LIMITATIONS

- 未重跑依赖登录和真实模型的完整 e2e；符合 brief 的允许范围。本轮真实 PTY 用最小 CLI 替身，不能称为真实 opencode/agy 恢复或会话切换验收。
- R1 使用可控前台观察边界证明时序缺陷；未测真实 CLI 的回调延迟分布。R4 使用真实收集器和 SQLite/rollout 夹具；未完整恢复真实 Codex 后执行新线程操作。R5 使用真实 signal 验证与查询，但回调由合成输入构造。
- 未重新验证四家 CLI 的真实记录内部格式；没有读取或复制用户真实 `~/.claude`、`~/.codex`、opencode、agy 的会话内容，也没有修改全局配置或运行真实模型。
- 未测试 Electron 中右键、键盘、悬停、屏幕阅读器和剪贴板读回；构建通过只证明标准构建完成。没有新建或修改候选测试来形成“修后绿态”。
- “F3 已关闭”仅指读取失败与不匹配的区分；“shell 子进程通过”仅指本轮包装 shell 场景保持禁用。两者均不代表当前身份识别或所有子进程组合完整通过。
- 三次真实 PTY 探针均完成退出处理；结束时追加的系统进程清单检查被 sandbox 拒绝执行 `ps`（`PermissionError: Operation not permitted`），因此未独立核对全系统残留进程数。候选冻结状态、报告 UTF-8 编码及链接存在性检查已在该错误之前完成，见 [report-check.json](report-check.json)。
- 本轮结论是拒绝当前冻结候选；没有实施修复，也不替未来候选预先给出通过结论。
