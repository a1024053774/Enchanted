# T-152 整链走查与待批准计划

状态：**INCOMPLETE**。2026-10-23，worker `b23-t152`，task `T-152-1` / attempt `a1`。本轮按执行主控 #10 只读走查，只新增本文；不改代码、不运行新夹具、不补第四轮脚本。代码基线及 03 的被测版本均为 `b3521197e7032219e2affc3481a31e9daae4bccb`。

**结论：03 的直接阻断是旧 Stop 输入缺少现行 hook 来源字段，不是现行产品取消了门禁回执回合。** 同类缺口共三条输入路径：worker/ACK Stop、reviewer Stop、held-socket reviewer Stop。源码仍实现原来的请求转交、回执排队、ACK 完成、独立审查、结束核对和持锁集成；目前没有证据支持“必须在本文件重写大半条业务流程”。但原共享基类也不能直接当作现行全绿基线：启动、配置、证据采集和 hook 信封均有过时假设，前几轮只逐层处理，未提前完整核对。本次把剩余确定缺口列全；是否继续按局部迁移执行，交执行主控决定。

目标：核对 good_submission 到集成各步的输入、命令、事件、身份及结束条件；非目标：产品修复、共享基类迁移、真实 CLI/模型证明、验收放行。审计完成条件是给出可复核来源、运行事实与静态推断的边界，以及改动规模，不是让测试转绿。

## 03 的已观测事实

摘要：`outside-03-NM4823lV/SUMMARY.json`。T-141 reviewer 契约 PASS，其余 10 项均 harness_error，零业务断言，清理失败为 0。绿态原始记录：`/private/tmp/t152-753dx2lx/run/tracer_review_copy/`；夹具：`/private/tmp/q76-o0vstoqj/c-fo2tzvft`。以下只读查询针对该绿态样本，不把其余 9 个案例当成独立完成了下游路径。

1. worker 已自动进入 busy，turn 和 active.nativeTurn 均为 `fixture-turn-1`；此前启动问题已通过本入口。
2. `command-0023.stdout.bin`：submit 返回 `ok=true, queued=true, delivered=false`，写入 `delivery-1.json`。这只是排队回执，不是交付成功。
3. `command-0025.stdin.json` 的 Stop 只有 session_id、turn_id、hook_event_name、last_assistant_message，缺 cwd 与 transcript_path。
4. **`command-0025.stdout.bin` 已明确返回 `ok=false, error=question_origin_unverified`**。SQLite 的事件 46 为 hook_received，47 为 native_question_unverified，48 为 request_rejected；该 request 已携带正确的 delivery-1.json 内容。relay_requests 与 relay_results 均为 0 行；没有进入 relay.receive，更没有执行门禁 submit。
5. control/writes.jsonl 只有开受限目录 Enter、任务 paste、任务 Enter 三次写入。随后 ACK 等待超时是上一步 Stop 拒绝的后果，不是 ACK 命令被删除的证据。

读回方法（路径取上述夹具；不重新运行后台）：查看 `case.json` 的 command 23/25 及其 stdin/stdout；SQLite 查询 `SELECT seq,time,type,data FROM orchestration_events WHERE type IN ('hook_received','native_question_unverified','request_rejected') ORDER BY seq`，以及 `SELECT count(*) FROM relay_requests` / `relay_results`。原摘要和原始现场均保留，本轮不覆盖或归档它们。

## 逐步对照

标记：**运行**＝03 已经过此步并留有现场；**静态**＝读到现行生产路径，尚未由本套件运行验证；**阻断**＝可定位的输入不符。表中的“现行”指上述固定代码版本，不替其他 checkout 的后续改动背书。测试短文件名均在 `workbench/tests/`，生产短文件名均在 `workbench/src/`。

| 步骤 | 测试/基类期望（文件:行） | 现行生产路径（文件:行） | 对照结论 |
| --- | --- | --- | --- |
| 0. host 与任务身份 | `test_quality_chain_e2e.py:97–128` 造 Codex home/旧 reviewers 配置；`test_task_cards_e2e.py:55–65` 卡片短名；本地 `test_t082_review_boundary_e2e.py:30–37` 已适配完整 task id 与 reviewer role 字段。 | `gates/core.ts:1140–1151` 在 runtime 下解析项目任务身份；`panes.ts:648–652` 要求 reviewer_role_card/revision，T-127 不再预建独立 reviewer home。 | **运行**：当前局部适配已越过 card_save/create/dispatch；共享原配置仍过时，未改共享文件。 |
| 1. start_worker | `test_quality_tracer_e2e.py:26–29` → `test_quality_chain_e2e.py:195–198,218–222` 保存卡、create、dispatch，然后 release_worker。 | `gates/core.ts:1515–1601` 在 task/claims 锁下冻结卡片、建 attempt/worktree、createThread、绑定 runtime identity，落 claimed；`panes.ts:1075–1077` 排队任务提示。 | **运行**：03 已建立受管 worker、当前 attempt 和实际任务回合。无需重写 claim/dispatch。 |
| 2. 首次放行 | 原 `test_quality_chain_e2e.py:224–232` 调已删 pane_release；本地 `test_t082_review_boundary_e2e.py:39–46` 已改为绑定 launch/native 并等 busy/turn、codex_startup_ready。 | `panes.ts:929–942` 只在启动 native ready、前台身份成立且无 active 时设 idle/drain；`test_t141_startup_signal.mjs:28–46` 保证首次信号与后续 Stop 区分。 | **运行**：03 已通过；保留当前局部覆盖，不恢复 pane_release。 |
| 3. 回合扫描 | 共享 `controlled_quality_pty.ts:63–75` 在后续 Enter 追加 task_started 与 turn_context；专用 `t152_review_host.ts:30–40` 已补普通输出。基类要求 fixture-turn-1。 | `panes.ts:797–801` 的 onData 调 scan；`panes.ts:1018–1071` 只从本 workspace 的根 rollout 绑定 turn/model/effort；`status:1366–1380` 只读状态。 | **运行**：03 的 turn/nativeTurn 已绑定；不是本轮 ACK 缺失的根因。 |
| 4. Git 提交 | `test_quality_chain_e2e.py:200–216` 在 worker worktree 写结果、单独 git add/commit，尾注 task/attempt/session/native/launch；工具/模型/effort 为夹具输入。 | `gates/core.ts:2170–2199` 在 verify 时按真实 delivery facts 核对尾注；`4013–4020` 在 submit 时保存实际观察 facts。 | **运行到提交**：03 已有候选提交，完整 task 身份已适配。**静态后置条件**：尾注尚未经过 verify；模拟工具版本和 native model/effort 在夹具内部一致，不是原生 CLI 实测。 |
| 5. worker_submit 排队 | `test_quality_chain_e2e.py:254–262` 用 worker env 调 submit，要求 queued=true。 | `gates/cli.ts:207–214` 识别会话身份并走 queueSessionRequest；`relayFiles.ts:41–76` 保存带 task/attempt/session/fence/spec_rev 的独占请求文件。 | **运行**：command 23 已排队；不能据 queued=true 推定 gate submit 已执行。此路径仍存在。 |
| 6. worker Stop 转交 | `test_quality_chain_e2e.py:247–252` 造 Stop；`263` 调用但没有先检查返回 ok。 | `gates/cli.ts:185–192` 读请求文件；`panes.ts:1395–1444` 记录 hook 并做通用验证；`questions.ts:52–64` 要求 session、cwd、精确 transcript_path 与当前 turn；`paneRecovery.ts:49–67` 定位唯一根日志。 | **已复现阻断**：旧 Stop 缺 cwd/transcript_path，先被 question_origin_unverified 拒绝，尚未进入转交。`gate()`（基类:173–193）会正常返回业务错误对象；worker_submit 随后不读这次结果而等待 ACK，遮住了直接原因。 |
| 7. relay 与门禁 submit | 基类期望 Stop 后能在 `relay_result`（:281–287）的 SQLite join 中读到本 launch/request_id 的结果。 | `daemon.ts:754–778` 匹配 Stop 后逐文件 relay.receive；`relay.ts:100–107,123–157` 核对 schema、文件身份和绑定，执行并持久化一次结果；`daemon.ts:779–812` 取 active caller；`gates/core.ts:3940–4056` 核对 attempt/fence/spec、运行身份、候选/干净 worktree、delivery facts，落 submitted。 | **静态，03 未到达**：这条路径仍完整存在。当前请求文件的 schema/身份已在 command 25 的 request_rejected 原始输入中看到；不能把尚未执行的 gate 宣称成功。 |
| 8. 注入门禁回执 | `worker_submit:257,265` 预期下一原生回合；`test_quality_chain_e2e.py:292–296` 将 source=gate 视为门禁消息。 | `daemon.ts:120–121` 仍定义仅确认、不用工具的反馈文本；`814–824` 对非 replayed、非延迟 inbox 结果调用 panes.dispatch(source=gate)；`panes.ts:1188–1202` 登记 dispatch_queued，`1222–1254` 只有 idle 等条件满足才写 paste/Enter。 | **静态**：回执注入没有被删除；matched Stop、实际 relay receipt 和 pane 可用是前提。03 是前提失败，不能据“三次写入”推导业务流程已换掉。 |
| 9. worker 结束 → ACK 开始 | 基类在 `stop_turn` 后等 busy/ack_turn（:265），期待回执是一个新 turn。 | `panes.ts:1538–1554` 转交仍在 active 时执行，随后清 active、落 pane_idle；`daemon.ts:911–920` 仅在成功 signal 的连接 close 后 drain；`transport.ts:37–44` 正常 CLI 收到响应后关闭写半边。 | **静态**：队列反馈先登记、原回合先 idle、socket close 后才提交下一回合，与基类顺序相符。现有 PTY 输出规则也覆盖回执 Enter。未运行验证 ack_turn 的准确绑定。 |
| 10. ACK Stop 与完成 | `worker_submit:266–278` 再调用 stop_turn，要求该 ACK submission/session/turn 对应唯一 pane_idle，然后读 relay_result。 | ACK Stop 同样经过 `questions.ts:52–64`；`relay.ts:83–98` 对仍在目录里的原请求返回 replayed=true；`daemon.ts:814,824` 不为 replay 再排回执；`panes.ts:1548–1550` 清该 active。 | **静态同型阻断**：同一个旧 stop_turn 也缺 ACK 的来源字段。完整信封后，原基类“唯一 ACK 结束”和持久结果检查可以保留；不应跳过 ACK 或改成仅等 idle。 |
| 11. verify / 机械检查 | 本地 `test_t082_review_boundary_e2e.py:86–90` 在 good_submission 成功后显式 verify，要求 reviewing/review 对象。 | `gates/core.ts:1702–1749` 冻结 G/C/M、独立验证 worktree；`1829–1843,1861–1866,1883–1903` 执行完成条件、红态/规则与尾注检查，再 requestReview。 | **静态**：仍是现行入口；本场景 G 是 C 的祖先，M=C（:1747–1749），后续比较主分支与 candidate 的断言有源码依据。不能用 03 给这串机械检查背书。 |
| 12. 建审查副本与会话 | 共享 `Tracer.start_review:34–65` 的网络/home/pane_release 已过时，但被本地 `test_t082_review_boundary_e2e.py:86–111` 覆盖；本地要求候选副本 cwd、现行 argv 与 native ready。 | `gates/core.ts:2448–2505` 冻结 worker boundary/refs、建 detached 审查目录与非 Git 副本、发任务卡/完成条件/2～5 变异请求；`panes.ts:648–661` 用现行 reviewer role 配置建新会话并 dispatch；`gates/core.ts:2383–2398` 核对启动边界。 | **静态**：本地已覆盖过时启动假设；当前配置提供必需字段。没有发现另一个必须绕开门禁的启动步骤；新会话与副本仍由产品创建。 |
| 13. reviewer Stop / report | `test_quality_tracer_e2e.py:68–86` 构造绑定任务/候选的 review_packet，再用只有 session/turn/last_message 的 Stop 送出。 | 通用 hook 先经 `questions.ts:52–64`；通过后 `daemon.ts:756–769` 严格解析完整最后消息，保存 review request；`qualityProtocol.ts:34–63` 核对字段及报告节；`gates/core.ts:3886–3938` 核对独立身份、cwd、候选、workspace，保存 review_result/verified。 | **确定的静态阻断**：继承的 send_review 也缺 cwd/transcript_path，会在 reviewRequest 之前被拒绝。包的顶层字段、完整 task id、report 容器及 workspace 绑定与当前结构一致，未发现必须重写 packet 的理由。 |
| 14. held-socket 结束窗口 | 本地 `test_t082_review_boundary_e2e.py:289–331` 自建 Stop 信封，保持客户端写半边开放，先收 completedReview，再尝试 integrate；:327–329 要求 review_end_check_required。 | `daemon.ts:839` 返回 completedReview，`:911–920` 把 reclaimReview 放在 signal 连接 close 后；`gates/core.ts:2402–2416,4073–4076` 在持锁 integrate 中要求 matching review_result 和 review_reclaimed。 | **确定的静态阻断**：此处直接构造的 Stop 同样缺 cwd/transcript_path，未到 held 窗口就会拒绝。补完整来源输入后，原 held-socket 窗口仍与现行实现相符；不能拿失败/任意 error 替代 completedReview 或结束前拒收。 |
| 15. 审查结束核对与清理 | 本地 :233–281、333–341，继承 `wait_review_reclaimed:88–90`：有效结果回收；refs/外部脏变更作废并保留副本；workspace 错误不落结果。 | `gates/core.ts:2530–2558` 持锁核对 reviewer idle、stop/archive/readback；`2603–2635` 核对副本身份、共享 refs、审查目录与 worker 的冻结边界；`2638–2667` 确认删除副本与审查 worktree，最后写 review_reclaimed；失败走 lifecycle_failed/paused。错误 workspace 在 `3929–3931` 拒绝，`daemon.ts:815–820` 转成审查协议失败。 | **静态**：仍有效；不能删这些检查换绿。当前受控 PTY 的 kill/onExit 机制还在（controlled_quality_pty.ts:78–91）；尚无本票的新真实结束证据。 |
| 16. 集成 | 本地 :342–345 在干净结束后用同一 score_file 再 integrate，要求 HEAD=candidate；脏结束保持 base。score_file 来自 `test_quality_tracer_e2e.py:100–106`。 | `qualityProtocol.ts:66–81` 接受该 score 形状；`gates/core.ts:3540,3568–3587` 校验操作员/持 task 锁，`:4059–4079` 核对 verified/verification/quality/review/score，`:4116–4144` 处理分支变化与 G→M 意图，`:1970–2019` CAS 快进，`:4160–4176` 读回 integrated/accepted 与评分。 | **静态**：现行契约支持原正负对照。这里用隔离操作员凭据跑受控门禁，不证明真实主控角色申请、真实 native 沙箱或模型判断。集成、CAS 和 score 都不能提前省掉。 |
| 17. fixture 关闭与证据 | 原 `QualityCase.close_fixture:583–652` 假设请求目录全为文件；本地 :113–203 已改递归采集，保留数据库/Git 快照、PID/退出/凭据检查。 | 当前 `panes.ts:755–759` 为临时文件建立独立 .a2a-tmp；生产 stop/archive 与门禁结束核对是上述独立步骤，不能用 fixture 的 daemon_stop 替代。 | **运行到失败后关闭**：03 cleanup_failures=0；只证明失败现场的夹具关闭，不能说审查结束已通过。T-090 三例仍继承本链（test_t090_review_worker_boundary_e2e.py:16–26），须一起复跑。 |

## 已确定的剩余修改集合（计划，未实施）

1. 在本文件中统一构造现行 Codex Stop 输入。来源必须来自本次夹具已知的 attempt.workspace / reviewer candidate_workspace 和受控原生日志 `record['log']`；不能使用任意存在的日志路径，不能关闭 validateHookEnvelope 或伪造成功结果。`controlled_quality_pty.ts:31–47` 已为每次 launch 提供 native/log，`paneRecovery.ts:49–67` 的根日志定位与其 cwd/session 一致。
2. 局部覆盖 `stop_turn`，同时覆盖 worker 首轮与 ACK：补 cwd/transcript_path，保留本次 session/turn/Stop；如果 signal 返回错误，立即以带错误详情的 HarnessFailure 结束，避免把直接拒绝藏成 ACK 超时。由此可以继续复用 inherited worker_submit 的排队、ACK 和唯一结束检查，无需重写它。
3. 局部覆盖 `send_review`，为 reviewer Stop 加同一完整来源信封；保留最后消息 JSON、真实 signal/relay、状态读回及既有失败检查。
4. 修改本地 integration_window 的原始 socket Stop 构造，使其使用同一完整信封。保持原 socket 生命周期、completedReview、结束前明确拒收、脏/干净两种对照和后续集成断言。

这三条路径必须一批修改，不能只修 worker 后再逐处撞。旧失败会令当前 submission 的 trust 变 unknown（`questions.ts:35–45`、`panes.ts:1555–1558`）；不得在已经被旧 hook 污染的原 fixture 里重试并声称恢复，后续必须新建隔离现场。

**规模估计（静态估算，不是承诺）：** 若保留当前已迁移的局部 host/cleanup，不再引入其他需求，新增/改动可执行代码约 **35～65 行**：一个在三个真实使用点共用的 Stop 信封构造、两个局部方法覆盖、held-socket 输入接线；删除/替换约 3～8 行。共享基类、产品、现有业务断言、worker_submit / review_packet / verify / reclaim / integrate 均不需要复制或改写。另需一个新编号运行脚本和实际运行后的证据记录。无需现在就引入新测试框架或平行门禁。

**范围成本必须明说：** 相对起点，之前已经在目标 Python 文件累计 +167/-9 行（净 +158），另加 53 行专用 host、126 行本票 runner，尚未计 132 行原始报告 JSON 输入。这已经远多于最初两个网络参数断言的迁移；主要来自禁止改共享文件后产生的本地启动/清理覆盖。因此“接下来不必重写大半流程”不等于此前改动很小。若执行主控认为这些夹具迁移已超出授权，应先交用户裁定，不能靠本计划自行扩大范围。

## 验证与停止点

- **已知事实：** 03 在 hook 校验处拒绝；回执处理、结束核对和集成机制仍在生产路径。**推断：** 完整迁移三处信封后可以保留原业务链；未执行过这些下游步骤，不能认定没有其他环境/时序问题。
- 如获继续授权，先用全新 fixture 跑一个正常 `tracer_review_copy`，每步读回 queued file、匹配 Stop、relay_result、source=gate 的 dispatch、ACK 唯一 pane_idle、review_result、review_reclaimed 和物理副本删除。它是既有生产路径的 **Tracer bullet**，不能用 mocked gate verdict 代替。
- 若这条完整正例失败，先报告明确阶段、输入与原始错误，不批量把 10 个同型 harness_error 当红态；不得顺手修改产品或共享基类。只有正例完整走通后，才扩到所有保留场景、8 个变异与 T-090/T-141 回归，随后重新跑完整绿态。每个 mutant 仍须命中特定业务断言；任意 setup/hook/cleanup 错误均是 INCOMPLETE。
- **Deep modules：** 继续复用当前门禁；Stop 构造只统一真实重复输入，不新增执行策略/兼容层。**Ubiquitous language：** 区分“排队回执”“门禁回执回合”“ACK Stop”“审查结束核对”；queued 不是交付，Stop 不是集成。
- 主控/用户的下一步决定：允许上述有限夹具迁移，或另切共享测试基础设施票、重新分配范围。本文只提供证据与估算，不替主控作选择。
- 本轮 project_map status：起始与交付前均为 0 problems、0 stale living docs；命令为 `python3 /Users/luckye/Documents/SKILLS/project-map-skill/project-map/scripts/project_map.py status --root .`。本轮不新增或关闭 ticket，不改地图。

按主控 #10 要求，提交后回复 **PLAN** 并停止，等待答复；不实施上述计划。
