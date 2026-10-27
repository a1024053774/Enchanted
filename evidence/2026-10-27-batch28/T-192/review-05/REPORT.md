# T-192 独立审查第 5 轮

STATUS: NO_GO  
RELEASE: NO_GO  
**结论：需修复。**

第 4 轮 Q1 的“原 verify 拒绝漏折叠、归给新 worker”已在本轮检查的生产控制流中修好。仍发现 1 条 P3 展示问题：真实事件会从 A 切到 B 再回到 A，而 TaskRecord 只在每个 attempt 首次出现时显示标题，后续属于 A 的步骤落在 B 的标题下。现有新增替换夹具把其中一条生产上属于 A 的事件写成了 B，未覆盖这一问题。

## TARGET：对象与边界

- 仓库：`/Users/luckye/Documents/Code/a2a`，HEAD `c76e2ab2a7dfd5fe0692ff9f1150ef586354a4d0`，候选为本目录 `change.diff`。开始、结束均核对补丁的 14 个文件：受控文件比较实际 diff 正文，两个新增文件比较全文，全部一致。比较时忽略 Git `index` 元数据行的缩写长度差异，没有计算摘要、校验值或指纹。
- 目标：核对 Q1 的关联、折叠和展示，抽查 N1～N4、F1～F6、R1～R5，运行指定检查并核对文案。验收依据为 BRIEF、T-192、T-189、U07/U08；前四轮报告和 RESULTS 用于界定待复验反例，现有测试不作为唯一 oracle。
- 非目标：实现修复、修改任务或地图、构建发布、派发真实 agent、全站审查。仓库全程只读，没有 checkout、切分支，也没有连接或操作 `/private/tmp/t190` 的后台、应用和状态库。
- 使用 project-map、behavioral-acceptance-review、evidence-first-testing、frontend-production 的相关只读流程；design-integrity-review 因触及验收证据，按其路由并入行为验收审查。中文报告按 document-writing 保存并回读。未另派审查员。
- **Ubiquitous language**：任务、执行尝试（attempt）、验收、会话、窗格分别指不同对象。**Deep modules**：`task_history` 仍是既有事件表的只读投影，未发现本候选新增平行可变门禁或自动重试。**Tracer bullet**：既有 green4 是交付、验收打回、撤销、回收、记录页的一条切片，不能替代真实审查与集成全流程。

## FINDINGS：确定问题

### S1 · P3：从 B 返回 A 的时间线步骤没有 A 的标题，视觉上归入 B

**位置：`workbench/app/TaskRecord.tsx:73`、`:75`。新增可见步骤：`workbench/src/gates/taskHistory.ts:51`。生产依据：`workbench/src/gates/core.ts:1726`、`:1729`、`:1747`、`:1748`。**

**具体输入/状态 → 错误结果：** A 的 worker 已结束，A 的 verify 合并冲突；`writeConflict()` 创建 B 后，生产事件顺序为：

```text
A：验收合并失败 → 合并冲突 → 回收 → 撤销
B：认领 → 启动 worker
A：conflict_worker_replaced
B：rejected(verify, merge_conflict, details.attempt=A)
```

最后一条拒绝已正确折叠。`save(..., attempt)` 显式将 `conflict_worker_replaced` 归给原 A；投影也保留 A。但组件的 `first` 判断使用整个 steps 的首次出现位置，所以最后这条 A 的步骤没有标题，也没有逐行 attempt 标识。实际组件输出成为：

```text
第 2 次执行尝试 · B
认领
启动 worker
合并冲突后更换 worker · 新执行尝试 B
```

A 更换自身 worker 的记录因此出现在 B 的标题下，看起来是 B 又更换成 B。替换失败也有同一机制：B 已建立，生产 claim 在启动检查中因 `run_blocked` 失败，`writeConflict()` 写 A 的 `conflict_rework_unknown`，再向 A 上报 `worktree：run_blocked`；该上报在界面中仍落在 B 的标题下。原始事件和结构化投影的 attempt 没有丢失，问题是展示归属，因此定 P3。

**证据类型：生产控制流局部重放 + 实际 TSX 组件转换执行。** [core-path-final-review5.json](core-path-final-review5.json) 的 replace / replace-failed 保存了完整事件及投影；[render-final-review5.json](render-final-review5.json) 保存组件逐行文本。组件检查退出 1，两条业务断言分别指出成功与失败路径返回 A 时缺少 A 标题；stderr 为空，不是导入、编译或环境失败。hooks 与 JSX 宿主被替代，未启动 Electron 或浏览器。

**最小修复方向：** 保留事件顺序，在 attempt 发生切换时重新标明其身份；或真正按 attempt 分组。沿用统一的 A=第 1 次、B=第 2 次编号，不把重新出现的 A 编成第 3 次。无需修改生产事件、增加 API 或改写历史。

**现有检查为何没检出：** `evidence/2026-10-27-batch28/T-192/history_check.ts:67` 把 `conflict_worker_replaced` 的事件行 attempt 写成 B，真实 `core.ts:1729` 则显式写 A；`:70` 仅断言步骤存在，没有核对归属或组件标题。`row-attempt` 变异能证明拒绝的修复，但不能证明时间线分组正确。建议在同一修复中校正该夹具，并增加 A→B→A 的组件身份断言。

## EVIDENCE：Q1 与拒绝详情专项

### Q1 的关联与折叠

通过真实 `A2AGates.call()` → `request()` → `verifyCandidate()` → `writeConflict()` → `save/event()` → `task_history` 路径，在内存 SQLite 中重放。保留生产身份核对、验收控制流、撤销、拒绝捕获和投影；Git/进程、清理、成员登记及替换 claim 边界使用受控替代。claim 的成功与失败顺序另对照生产 `core.ts:1557`～`:1679`，没有把替代边界当成真实 worker 验收。

| 场景 | 实际结果 | 判断范围 |
| --- | --- | --- |
| 同 attempt 冲突，中间有反馈与清理 | 冲突结果和文件步骤保留，最后 merge_conflict 拒绝只折叠一次 | PASS，局部生产控制流 |
| 替换成功，当前 attempt 已是 B | 原始 rejected 行归 B，详情中的验收快照归 A；投影按 A 关联并隐藏重复拒绝，更换步骤保留且其结构化归属为 A | Q1 折叠 PASS；组件归属见 S1 |
| 替换在创建 B 前失败 | 当前 attempt 为 null；unknown 和 A 的问题上报写入，原拒绝带 A 的快照，仍正确折叠 | PASS，注入 path_overlap 边界失败 |
| 替换在 B 已建立后失败 | 当前 attempt 为 B；unknown 和 A 的问题上报保留，重复 merge_conflict 折叠；独有 run_blocked 原因仍由问题上报显示 | 折叠 PASS；组件归属见 S1 |
| 打回后重复 verify 两次 | 两次均返回 repair_submission_required，两条新拒绝均可见 | PASS，真实局部 call 入口 |
| A 冲突未消费，B 自己在验收前 git_failed，详情无 attempt | B 的新拒绝保留在 B，不能被 A 的冲突隐藏 | PASS，真实局部 call 入口及边界注入 |
| A 冲突之后，B 自己完成条件失败 | B 的验收失败与打回 oracle_failed 可见；仅 B 自己重复的拒绝被折叠 | PASS，生产验收/打回控制流，命令边界替代 |
| B 自己路径检查失败，拒绝详情无 attempt | 生产 checkPaths 写 path_boundary_failed；B 的路径失败、验收失败和打回可见，重复拒绝正确折叠 | PASS，生产 checkPaths，Git 路径列表替代 |

另运行投影哨兵：新交付、新 verification_result 会清除原折叠资格；不同错误、不同 attempt、同码第二次拒绝保持可见。现有 own 反例还覆盖 A 冲突之后 B 的独立 merge_conflict 拒绝不会被 A 折叠。上述结果不证明真实 Git 冲突、worker 启动、反馈送达或清理成功。

### 所有 verify 拒绝是否都有 `details.attempt.attempt_id`

**没有。** `core.ts:4417`～`:4420` 原样保存 Refusal.details，没有给所有错误补 attempt。需要区分事件外层的 `details`，以及其中保存拒绝详情的内层 `details`：投影实际读取 `event.details.details.attempt.attempt_id`。

- **携带完整验收对象 v 的路径：** 合并冲突 `:1851`、完成条件失败 `:1954`、执行结果未知 `:1913`。v 的 attempt 是验收开始时的 structuredClone，故即使后面替换 worker，仍指向 A。这是 Q1 修复成立的关键。
- **没有统一 attempt 对象的路径：** 早期 not_submitted、stale_attempt 等状态/身份拒绝；repair_submission_required 的 repair 对象；冲突后的 conflict_rework_required 的 rework 对象；Git 结果；路径检查的 `{forbidden}`；oracle 检查的 `{modified}`；尾注的 `{commit,trailers}`；部分质量错误的专用详情。未知质量失败的包装也不保证带 attempt。`checkThread` 的身份冲突详情则可能包含 attempt，不能按错误大类一概而论。
- **回退的后果：** 缺少该字段时 `taskHistory.ts:79` 使用事件行 attempt。正常同 attempt 的这些拒绝写入时 current_attempt 未变化，故本轮 B 的真实 path_boundary_failed、早期 git_failed 与重复 verify 反例都归属正确。缺少字段并不会自动触发跨 attempt 折叠，也不会清除 A 的 open 项。
- **边界：** 若某条旧事件/其他写入路径在更换 worker 后把原 A 的拒绝写成 B，同时详情缺少原验收身份，现投影只能按 B 展示，不能还原 A。但本轮审查到的正常 writeConflict 返回路径最后固定抛 `Refusal('merge_conflict', v)`，即使内部替换失败并写 unknown，仍携带 A；未找到当前 Q1 真实路径会落入这一缺失身份情形。不把不可证实的历史输入列为第二条产品缺陷。

### 编号与分组

`TaskRecord.tsx:30` 依 steps 的 attempt 首次出现顺序生成编号。真实事件里 A 的认领先于 B，因此本轮两条组件路径的编号都是 A=1、B=2；审查报告引用的编号也使用同一数组。没有发现本轮修复把 B 排成第 1 次或凭空增加 attempt。**编号正确不等于每条记录展示在正确标题下**，返回 A 的分组缺陷见 S1。

## COUNTEREXAMPLE：运行命令与产物

环境 Node `v26.5.0`。先执行以下复制，之后才在副本运行会覆盖结果的 mutants.sh：

```sh
cp -R /Users/luckye/Documents/Code/a2a/evidence/2026-10-27-batch28/T-192 /private/tmp/t192-review5/copy
cd /private/tmp/t192-review5/copy
node history_check.ts > /private/tmp/t192-review5/history-check-review5.json
bash mutants.sh
```

history_check 退出 0，status=PASS、failures=[]。mutants.sh 包装脚本退出 0；10 个内部 node 检查均退出 1，其生成 JSON 全部可解析、status=FAIL，且均有对应业务失败：integration-c、no-quiet、no-reclaim、last-review-only、drop-all-verify、any-previous-failure、feedback-breaks-fold、fold-not-consumed、row-attempt、no-rule-check。没有把脚本退出 0 当成变异通过。`row-attempt` 的失败为“the replaced worker's attempt does not show the old verify refusal”。结果文件在 [copy](copy/)，仓库中的原文件未改。

本轮额外探针从工作区执行，均保存 stdout/stderr：

```sh
cd /private/tmp/t192-review5
node core-path-final-review5.mjs > core-path-final-review5.json 2> core-path-final-review5.stderr
node own-verification-real-path-review5.mjs > own-verification-real-path-review5.json 2> own-verification-real-path-review5.stderr
node entry-review5.mjs > entry-review5.json 2> entry-review5.stderr
node fold-review5.mjs > fold-review5.json 2> fold-review5.stderr
node render-final-review5.mjs > render-final-review5.json 2> render-final-review5.stderr
```

前四项分别退出 0，最后一项退出 1，原因仅为 S1 的两条标题业务断言。按钮的 busy 禁用/解除、点击回调，以及删除 disabled 的反事实检测均通过。render 探针没有使用修复代码，没有修改候选组件。

部分探针复用了第 4 轮保留的搭建脚本，再加入本轮输入与独立身份断言；不是重新运行真实外部系统。工作区也保留了较早的 core-path、render、own-verification 输出；较早 own-verification 使用自定义 path_forbidden 哨兵，最终证据改用生产 checkPaths 的 path_boundary_failed，未覆盖前一份结果。结论以文件名含 final 或 real-path 的产物为准。

## 旧问题抽查

| 项目 | 本轮实际检查结果 |
| --- | --- |
| N1 | 同 attempt 真实反馈序列折叠通过；不同错误、重复同码、新交付、新验收清除资格的哨兵通过。替换路径 Q1 已修，展示仍有 S1。 |
| N2、F6 | 源码一致：`docs/index.html:55` 已按“是否打开窗格”区分整页与底部记录，并说明打开 worker 按钮；renderer 的 paneKeys 分支相符。未运行产品页演示。 |
| N3 | busy 仍由 renderer 传入 `TaskRecord.tsx:92` 的 disabled；实际转换组件中 true 禁用、false 恢复并可调用回调；删除 disabled 的变异被检出。没有真实原生 UI 忙碌交互复验。 |
| N4 | 副本中十份 green4 JSON 全部完整可解析；verify 明确为 oracle_failed，revoke/reclaim 成功，history 的任务为 ready/current_attempt=null，末 11 步与 UI/12 相符。旧 green2/green3 截断回执分别仍为 250/400 字节，解析失败，原样保留。实际查看 UI/11、12，支持已有回收记录页面；不是本轮重跑真实旅程。 |
| F1 | 内存 SQLite、生产 call 入口对 closed 执行 revoke、revise、claim、dispatch，四者都拒 task_closed，状态保持 closed。锁用占位，未测试锁竞争。 |
| F2 | 零窗格使用轮询的 TaskRecord，并生成当前 worker 的按钮；旧静态门禁栏只在有窗格时渲染。未恢复自动跟随。 |
| F3 | 验收前 git_failed、无关失败之后 git_failed 仍显示；merge_failed 两种详情结构及冲突文件映射保留。B 的自身路径/完成条件失败未被 A 隐藏。 |
| F4 | red_check/rule_check 映射与现有投影断言仍在，no-rule-check 变异被业务断言检出。未真实运行红态/规则检查全链路。 |
| F5 | 真实导出夹具的两次审查、首份问题与建议、各份报告断言通过；last-review-only 变异失败。组件仍逐份渲染报告。未实际展开旧报告截图中的第一份审查。 |
| R1 | 按钮传具体 launch，经 selectAgent → select-agent → changeView({task,launch})，避开无显式 launch 的已存空布局恢复分支；没有重新引入 refresh 方案。源码核对，未本轮真实回收再派发。 |
| R2、R3 | firstAttempt/onAttemptStarted 不存在；effect 只读数据，按钮动作按当前渲染生成，busy 当前值控制禁用。旧基线和旧回调机制未恢复。未重放全部 React/IPC 时序。 |
| R4 | 无关 integrate 拒绝后 verify/git_failed 的现有反例仍通过；不同 attempt、不同错误不误折叠；any-previous-failure 被检出。 |
| R5 | README 已限定同次验收、同码、一次性折叠，写明替换后的原验收身份关联；与本轮已查投影行为相符。其“每个 attempt 的时间线”在 S1 的回返序列中尚未充分实现。 |

关闭显示方面，实际查看 UI/01 的“已关闭”任务格，核对 green-close/green2-tasks-beta 的 closed 及 gateStateNames 映射；本轮未从原生 UI 执行 close。产品页的整页/底部布局措辞未发现本轮回退。RESULTS 前面各轮的旧处理文字属于历史记录，末尾已明确更新为 Q1 本次处理，并声明 UI/11、12 来自修前构建；没有将旧构建截图当作 Q1 修复后的新截图。

## LIMITATIONS：未检查与证据层级

- 未启动 Electron、连接真实 socket、派发 worker/reviewer、制造真实 Git 冲突、跑完整 build、测试并发锁/崩溃恢复、读屏、性能、移动端或发布。局部生产控制流与组件宿主替代只证明其对应逻辑，不证明外部边界。
- green4 的真实新 attempt 没经过审查、打分和集成；这些内容的已有界面证据来自注入真实历史事件的夹具。已回收记录页与关闭任务格有既有证据支持，当前候选完整原生 UI/全生命周期仍为 INCOMPLETE。
- 实际查看旧截图只有 UI/01、11、12；未重看其余截图，不能把前轮看过的内容说成本轮独立确认。
- Agent 产品本轮范围是编排事件顺序、异步状态、attempt 身份与界面展示；未扩大成模型能力、完整权限、安全或部署审计。检索、媒体生成等为本轮 N/A。
- project-map status 开始和结束均退出 0，Problems(0)、Stale living docs(0)；结束输出见 [project-map-status-end.txt](project-map-status-end.txt)。这只证明地图脚本结果，不替代人工文案与行为核对。

## RULE：重复失败类应由什么检查拦住

历史关联已经连续多轮出问题。本轮缺口可机械检测：在现有 T-192 回归入口保留生产控制流产生的 A→B→A 序列，同时断言每条时间线记录的可见 attempt 标识与投影身份一致、编号稳定，并覆盖替换成功及 B 已建立后的替换失败。不要仅核对拒绝数量和更换步骤存在，也不要继续使用把生产 A 事件写成 B 的夹具替代身份验证。只读审查未新建票或修改测试；建议实现方在 T-192 修复与现有验收入口中落实这一检查。

**最终结论：需修复。原 Q1 的拒绝折叠修复有效；修复 S1 后再对该变更范围复验。**
