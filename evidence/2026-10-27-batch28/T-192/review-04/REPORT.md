# T-192 独立审查第 4 轮

**状态：NO_GO。结论：需修复。**

N2、N3 已修；N4 所指出的截断回执与真实回收记录页缺口已补上相应材料。N1 的同 attempt 路径已修，但冲突后替换 worker 时仍会漏折叠，并把旧验收的拒绝显示在新 attempt 下。本轮确定问题 1 条，严重度 P3；没有发现本轮使已查的 F1～F6、R1～R5 原反例回退。

## TARGET：对象与边界

- 候选：`/private/tmp/t192-review4/change.diff`，基于 HEAD `c76e2ab2a7dfd5fe0692ff9f1150ef586354a4d0` 的未提交修改及两个新增文件。开始、结束均逐字核对受控文件 diff 和两个新增文件，均与给定候选一致；未计算摘要或校验值。
- 验收来源：T-192、T-189、`findings/2026-10-27-two-real-uses.md` U07/U08；另对照前三轮报告的问题与 RESULTS 的处理记录。现有测试只作为证据，不作为唯一 oracle。
- 目标：核对 N1～N4、实际事件路径和两条任务页验收，抽查旧问题。非目标：实现修复、派发 agent、修改任务或重新构建、发布。
- 仓库始终只读；没有 checkout、切分支，也没有连接、操作或重启 `/private/tmp/t190` 下的后台与应用。旧 `replay/` 未改，新重放文件在本工作区 `replay4/`，报告只写本文。
- **Ubiquitous language**：区分任务、执行尝试（attempt）、验收（verification）、运行会话与打开的窗格。**Deep modules**：`task_history` 是既有事件表的只读投影，本轮未发现第二套可变门禁；剩余问题需要正确关联验收身份，无需新增平行 API。**Tracer bullet**：green4 提供了真实派发、交付、验收打回、撤销、回收后查看记录的一条切片，不等于真实审查与集成全流程。

## FINDINGS：剩余问题

### Q1 · P3：冲突替换 worker 后，旧 verify 拒绝被归到新 attempt，仍重复展示

**位置：`workbench/src/gates/taskHistory.ts:75`～`:81`。根因关联：`workbench/src/gates/core.ts:1726`、`:1851`、`:4420`、`:1103`；展示关联：`workbench/app/TaskRecord.tsx:73`～`:77`。**

**失败场景：** attempt A 已交付，verify 的合并发生冲突，A 的 worker 会话已经结束。生产 `writeConflict()` 回收并撤销 A，经 claim/dispatch 创建 replacement attempt B，然后返回。原 verify 仍抛出 `merge_conflict`。捕获分支写 rejected 时没有传入原 attempt，`event()` 从库里读取的 current_attempt 已是 B。

实际事件与投影结果为：

```text
A: verification_result(state=merge_failed)
A: verification_conflict(files=[novel.txt])
A: conflict_rework_intent → conflict_replacement_intent
A: reclaimed → verification_worktree_removed → revoked
B: claimed → dispatched
A: conflict_worker_replaced
B: rejected(input.command=verify, error=merge_conflict)

显示：
A: 验收 · 合并失败；合并冲突 · novel.txt；回收；撤销
B: 认领；启动 worker；门禁拒绝 · verify：merge_conflict
```

**错误结果：** B 尚未交付或验收，就在 B 的时间线下出现验收拒绝；它实际属于 A 的同一次冲突，也已由 A 的结构化冲突步骤表达。整理器只查 `open.get(event.attempt)`，因此 B 匹配不到 A 的待折叠记录。`conflict_worker_replaced` 本身又不显示，页面没有说明这条拒绝的真实归属。问题限于展示与关联，不证明 worker 替换或实际门禁状态被破坏，因此定为 P3。

`RESULTS.md:84` 与 README 已承认换 worker 后不折叠；这说明行为已知，不能把同一次验收变成 B 的验收事实，也不能据此认定 N1 整体修复。

**证据：** 本轮通过生产 `A2AGates.call()`、`verifyCandidate()`、`writeConflict()`、`invalidate()`、`save/event()` 和 `task_history` 重放，SQLite 在内存中。Git/CLI、清理、成员登记和新 worker 创建边界被替代，未运行真实 Git 冲突或真实 worker；生产分支与事件归属逻辑未替代。原始结果见 [core-paths-real.json](replay4/core-paths-real.json)。独立断言“尚未交付的新 attempt 不应显示旧验收的 merge_conflict”退出 1，见 [replacement-contract.stderr](replay4/replacement-contract.stderr)，不是启动或依赖失败。

**最小修复方向：** 拒绝事件应绑定发起该次 verify 的 attempt，或投影按拒绝中保留的 verification/attempt 身份关联同一次验收。保留事件表原始记录；不要改成“跨 attempt 只要错误码相同就隐藏”。修复后重放替换成功、替换失败、不同验收同码拒绝，确保不误折叠新 worker 自己的错误。建议由 T-192 实现方在合并前处理。

## EVIDENCE：N1～N4 逐项核对

| 项目 | 结论 | 本轮证据及界限 |
| --- | --- | --- |
| N1 同次失败折叠 | 部分 PASS，整体需修复 | 正常同 attempt 冲突夹有反馈/清理时，只有“验收·合并失败”和带文件的“合并冲突”；不同错误保留；同码第二次拒绝保留；新交付、新验收结果清除待折叠记录。替换 worker 仍有 Q1。 |
| N2 产品页第 3 步 | PASS（源码） | `docs/index.html:55` 改为按打开的窗格区分，写明整页记录和“打开 worker 会话”，不再承诺运行 worker/reviewer 必然并排。与 renderer 的 paneKeys 分支一致。未运行产品页演示。 |
| N3 busy 禁用 | PASS（源码、局部组件） | renderer 在零窗格分支传入同一个 busy；`TaskRecord.tsx:92` 使用 `disabled={busy}`。编译生产组件后，busy=true 时 disabled=true，false 时恢复可点，点击能调用传入动作；docked 不出现按钮。删除 disabled 的已知坏变异被断言检出。不是原生 UI 忙碌交互测试。 |
| N4 证据补齐 | 指定缺口已补；完整生命周期仍有限 | 两份截断文件保留，新增十份 green4 JSON 均完整可解析；同一任务/attempt/launch/候选可以关联，真实撤销/回收后的 history、任务列表与 UI/11、12 一致。真实审查、打分、集成未在该条新旅程发生，不能据夹具旧记录宣称发生过。 |

### 实际门禁路径专项

1. **同 worker 的合并冲突：PASS（局部生产控制流）。** 生产路径写入 conflict、rework、feedback intent/delivered、清理、rejected；本轮结果只显示两条冲突相关步骤，N1 原反例不再复现。
2. **冲突反馈失败、`conflict_rework_unknown`：没有发现独有原因被本次折叠吞掉。** 注入 sendGateFeedback 抛出异常后，生产代码写 unknown，并经 lifecycleIssue 写 issue_issue。投影保留“上报问题 · worktree：conflict_external_unknown”，只折叠重复的 verify/merge_conflict。unknown 事件正文不直接出现在时间线，本轮仅确认错误码可见，不宣称记录页显示完整异常正文。
3. **打回后重复 verify：PASS（局部入口）。** 预置 completion/oracle_failed 打回及其首次拒绝后，再调用生产 verify 两次，均返回 `repair_submission_required`，两条新拒绝都显示。另有独立哨兵验证同码第二条拒绝、不同错误、新交付、新 verification_result、不同 attempt 的独立拒绝不会被错误折叠。
4. **冲突后 worker 被替换：反例成立，见 Q1。** 仅按 attempt 匹配避免了跨 attempt 误隐藏，却没有解决同一次 verify 的事件归属。现有九个变异和 history_check 没覆盖这条路径。

### green4 与 RESULTS 的一致性

已核对十份 green4 JSON 的结构与关键字段，结果如下：

- `green4-status-submitted.json`：`lcu+T-2` 为 submitted，候选 `0933c7eebdd5443339367d3419cc0c911ea3f3b6`，attempt 为 `73676ed3-8787-4b43-9e9c-8e7fa7b58dbb`，launch 为 `23a1ca9c-04d5-4d9f-a366-1771cf4d3766`。
- `green4-launch.json`：task、attempt、launch 与上项一致；CLI 为 Claude Code，完整 argv 含 `--model claude-haiku-5-5 --effort low`。这是启动配置记录，不证明模型供应商实际服务档位。
- `green4-verify.json`：`ok=false,error=oracle_failed`，verification 为 `271f8d03-8d0c-4b45-a816-ac68eb52ce32`，C 为上述候选；完成条件 `/usr/bin/python3 check_readme.py` 退出 2，stderr 明确为文件不存在。与 RESULTS:73 一致，不能称该候选验收通过。
- `green4-answer-issue.json`：问题记录关联相同 attempt、候选和 verification，包含 worker 不自行修改验收程序的说明，以及主控要求变基的回复。两份 dispatch correction/reminder 保存了后续更正文案；`ok:true` 仅证明派发请求已登记，不独立证明 worker 实际读到或执行。
- revoke、reclaim、tasks-after-reclaim、history-after-reclaim 均为 `ok:true`；任务为 ready、current_attempt=null。history 中第五次执行尝试从认领、启动、交付，到路径/验收文件检查、完成条件失败、验收失败、打回、上报、撤销、回收，与 RESULTS:76 和 UI/12 相符。history 没有重复显示 seq 406；但它是投影输出，本身不能证明原始 seq 406 的内容。
- 实际查看 UI/11：`lcu / T-2` 的待认领整页记录，任务卡、结果、尾注、审查列表可见，没有 worker 打开按钮；UI/12 的第五次尝试末尾与上述步骤一致。截图不能单独证明“从任务格点击”的操作过程。
- RESULTS:74 所说独立脚本的基线退出 1、候选退出 0，以及 worker 屏幕上的沙箱拒绝、最终进程退出，没有在这十份回执中独立闭合；本轮没有访问运行现场去补证，不将这些叙述记为已复验。

两份旧异常证据仍分别为 250、400 字节，JSON 解析均报字符串未终止：`green2-claim-while-viewing.json`、`green3-dispatch-while-viewing.json`。本轮没有覆盖它们，也没有把开头的 `ok:true` 当作完整成功回执。

## 旧问题抽查

| 编号 | 本轮实际抽查结果 |
| --- | --- |
| F1 closed 被重开 | PASS（局部生产入口）：以 green-close 的 closed 任务调用 revoke、revise、claim、dispatch，均拒 `task_closed`，任务仍 closed。操作锁用占位，没有测试真实锁竞争。 |
| F2 零窗格状态与 worker 入口 | PASS（源码范围）：零窗格显示轮询的 TaskRecord，并传当前 agents 生成的打开动作；旧静态门禁栏只在有窗格时显示。没有恢复自动跟随。 |
| F3 独有 verify 错误、merge_failed 形状 | 旧反例 PASS：验收前 git_failed、无关 integrate 拒绝之后的 git_failed 都由现有检查保留；两种 verification_result 形状和冲突文件映射仍在。替换路径的新展示问题见 Q1。 |
| F4 red/rule 检查 | PASS（投影）：对应映射仍在，现有断言通过，删除 rule_check 的变异失败。没有真实执行这两类检查的全链路复验。 |
| F5 历次审查、报告与建议 | PASS（投影、渲染源码）：真实导出夹具的两次审查及第一份建议均保留；last-review-only 变异失败；TaskRecord 逐份渲染正文与建议。已看 UI/06，未操作展开第一份报告。 |
| F6 产品页承诺 | PASS（源码）：按打开的窗格区分，见 N2。 |
| R1 已存空布局 | 原故障机制未恢复：按钮传具体 launch，走 selectAgent；prepareSelection 的显式 launch 分支避开空 saved 布局。没有本轮真实回收后再派发的 UI 操作。 |
| R2 首读 attempt 被当基线 | 原故障机制未恢复：没有 firstAttempt/onAttemptStarted；每次渲染按当前 loaded.task 与 agents 计算按钮。局部按钮探针首读即带当前 attempt。 |
| R3 轮询持有旧 busy 回调 | 原故障机制未恢复：effect 只更新数据；动作在当前渲染生成，busy 通过 prop 禁用。没有在轮询内导航。 |
| R4 任意前一失败隐藏 verify | 原反例 PASS：无关失败不产生折叠资格；不同错误和不同 attempt 的拒绝保持可见。不能将这一点扩大成所有事件关联正确，见 Q1。 |
| R5 README 无条件隐藏 verify | PASS（旧问题）：README:1092 已说明有限折叠与逐次审查。它也记载换 worker 不折叠，不能代替 Q1 的修复。 |

## 两条验收的判断

1. **已回收的票进入后不是空页：现有隔离证据支持这一具体场景。** green4 同一真实 attempt 的交付、验收打回、撤销、回收回执，与 UI/11、12 的非空记录页相符，较第三轮已补足关键材料。任务卡、历史检查与审查等内容的投影/渲染也有分项支持。不过新旅程的真实审查、打分、集成没有发生；旧结果是注入真实事件的夹具。加上 Q1 尚存，不能将“门禁全程、每个 attempt 归属正确”整体判为 PASS。
2. **关闭后任务格显示“已关闭”：PASS（既有隔离证据范围）。** 本轮实际查看 UI/01 的已关闭任务格；green-close 为 closed，green2-tasks-beta 也为 closed；renderer 的任务格仍使用含 closed→已关闭 的 gateStateNames；F1 局部入口复验通过。没有本轮重新构建或从原生 UI 执行 close；当前候选与旧截图构建的完整绑定仍为 INCOMPLETE。

未要求一张验收失败的任务产生不存在的审查或集成记录，也未把未经本轮验证的完整生命周期写成 PASS。

## COUNTEREXAMPLE：重放与产物

环境 Node `v26.5.0`。下列命令在 `/private/tmp/t192-review4` 执行；生产仓库不写入。

```sh
cd /private/tmp/t192-review4/replay4
node history_check.ts ./taskHistory.ts > history-check-review4.json
bash mutants.sh > mutants-review4.log
```

history_check 退出 0、PASS、failures=[]；九个变异的 node 检查分别退出 1，均为业务断言失败：integration-c、no-quiet、no-reclaim、last-review-only、drop-all-verify、any-previous-failure、feedback-breaks-fold、fold-not-consumed、no-rule-check。包装 bash 自身退出 0 不代表变异通过。原脚本及夹具复制到新目录后执行，没有改写仓库旧结果。

```sh
node replay4/core_paths_real.mjs > replay4/core-paths-real.json
node replay4/replacement_contract.mjs
node replay4/entry_check.mjs > replay4/entry-check.json
node replay4/button_check.mjs > replay4/button-check.json
node replay4/fold_sentinels.mjs > replay4/fold-sentinels.json
```

- core_paths_real 退出 0，记录 delivered、unknown、replace 三条路径。replacement_contract 退出 1，准确拒绝当前候选的错误归属；stdout/stderr 已保存在同目录。
- entry_check 退出 0：关闭终态四入口和打回后两次 verify 的断言通过。
- button_check 退出 0：busy 禁用/恢复、点击动作、docked 无按钮通过；删除 disabled 的反事实被检出。此探针替代 hooks/JSX 渲染环境，没有真实 DOM 或 Electron IPC。
- fold_sentinels 退出 0：同码重复、不同错误、新交付、新验收结果、不同 attempt 等哨兵断言通过。
- 先前较窄的 `core_paths.mjs` 和输出也保留，未用后来的生产 verifyCandidate 重放覆盖它。最终 Q1 依据为 `core_paths_real.mjs`。
- project-map status 开始、结束均退出 0，Problems(0)、Stale living docs(0)；结束输出在 `replay4/project-map-status-end.txt`。这不代替人工核对文案。

## LIMITATIONS 与后续检查

- 本轮没有启动 Electron、连接真实 socket、派发 worker/reviewer、制造真实 Git 冲突、运行完整 build、检查并发锁/崩溃恢复、读屏或性能；相关结果不报告 PASS。
- 实际查看截图 UI/01、06、11、12；没有重看其他截图。对旧图的其他内容不增加本轮独立确认。
- Agent 产品本轮涉及编排状态、异步更新、attempt/会话身份与界面入口；检查限定于本补丁及直接调用方，不是全权限、模型能力或外部副作用审计。检索、部署发布、媒体生成在本轮为 N/A。
- 未改实现、测试或票；未知构建来源、完整生命周期与界面忙碌交互仍明确保留为限制，不额外推断产品故障。

**RULE：** 历史折叠已反复出现关联缺陷。应在现有 history_check 或门禁入口回归中覆盖“原 worker 会话结束 → 冲突 → 创建新 attempt → 原 verify 返回拒绝”，以独立身份断言核对归属；只扩充相邻事件样例或同码变异不足以覆盖它。先保留当前反例，再验证修复，并保留不同 attempt 独立错误不得隐藏的正例。

**最终结论：需修复。**
