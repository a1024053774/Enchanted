# T-078 离线角色待投递：独立审查

STATUS: PASS

TARGET: 产品／测试候选 `7039840565754f7999b27061191b6506e61ef9d2`；冻结记录 `4b48664fd689aab8d52a8721098939067928847e`；基线 `887d85cdb37889941f1ed26836d4c94b277ab5fa`。

本次冻结候选的“离线角色留存待投递”独立审查结论为 **PASS**。冻结 diff、实现与验收对应关系、基线红态、5 个错误实现和相关入口回归已独立核对；执行主控 #302 回传的真实 Electron／node-pty／worker 收件箱回归 14 项全部通过，已读原始输出和持久化读回，补齐原 INCOMPLETE 的运行时缺口。未确认候选产品缺陷。

审查辅助脚本在全部检查结束后发生收尾错误，整体 exit 1，作为辅助脚本缺陷单独保留，不能把脚本整体写成 PASS。本结论只覆盖上述冻结差异，不代表整张 T-078 完成或批准 A-14。本报告未执行供应商 CLI、模型 API、submit、集成或产品仓库提交；未复制 auth、写全局配置、请求沙箱升级或开启子 agent。

## 独立性与范围

先读取主仓 reviewer 角色卡，再从当前用户派发及 `20261016T012505Z-ideation-answer-001.md` 重建要求；两份作者交接只作为定位线索。执行 `git rev-parse HEAD 703984056 4b48664fd 887d85cdb` 核对上述完整版本。开始和结束的 project-map status 均退出 0，Problems=0、Stale living docs=0。原有三个未跟踪清理证据目录保持原样。

**Tracer bullet** 为离线 send → pending → controller_start → unknown 排队 → release → 实际写出 → I2 → ack。**Deep modules** 的投递、锁、收据仍由 gates／Panes 拥有；daemon 负责接线，relay 负责原请求与反馈意图的关联。**Ubiquitous language** 按用户要求区分请求 queued、投递 pending／queued／delivered 和另追加的 ack。

`git diff --name-only 887d85cdb..703984056 -- . ':!evidence'` 仅有：

- 产品：`workbench/src/gates/core.ts`、`workbench/src/daemon.ts`、`workbench/src/relay.ts`。
- 检查：`test_t078_a13_rehearsal.ts`、`test_t078_inbox_entry.py`、`t078_worker_inbox_scenario.py`、`t078_09b_i1_driver.py`。
- 文档：`workbench/README.md`。

三份产品文件合计新增 96 行、删除 14 行。core 的改动限定于 inbox 投递、恢复与结果判定；daemon 新增 controller_start 恢复接线、pending 反馈筛选和 delivered 后结算；relay 新增待反馈查询与持久意图去重。reviewer 启动、T-082、协议定义、模型预算、权限合同、公开命令路由均未改。daemon 的 reviewer 分支只因前方代码增行而移动。I1 driver 两处仅允许创建缺少的父目录，已有输出目录仍拒绝覆盖。没有 operator 代发 send／stop／ack，也没有新增业务入口。`703984056..4b48664fd` 在 workbench／acceptance／scripts／fixtures 没有差异。

## 用户原话与 #299 裁定

判断：#299 与用户原话可以一致，未发现需要否决的冲突。用户讨论的条件是“目标角色没有会话时”，同时明确 protocol 与预算不变；因此 pending 阶段零反馈、实际 delivered 后保留原有那一条 I2，是对这两个约束的连贯解释。它不授权新增反馈根、重做 send 或把 pending 当 delivered。延后时点是主控对原话的解释，不能写成用户另外逐字批准过 I2 时点。

候选恰按这一解释实现：daemon:319 精确过滤成功的 pending；daemon:32–54 只在 delivered 后向原 launch 派发；relay:57–64 在任何 await／dispatch 前同步保存一次意图。意图存在、结果未知时不再次派发。原 `relay_results` 不更新。真实双 Claude 的预算和 Messages 数仍未在本次审查运行中证明。

## EVIDENCE：验收逐项对应

独立副本根目录：`/private/tmp/t078-pending-review-01-68n7wjv3/`。`snapshot.json` 保存版本和提取范围；只用 `git archive` 解出 workbench、acceptance、scripts、fixtures，另外读取 4 份必要的历史 hook 载荷。未归档整个仓库。依赖仅通过副本根下的 node_modules 链接读取现有依赖；构建输出没有移动、替换或链接。

以下行号均指冻结候选，`rehearsal` 指 `workbench/tests/test_t078_a13_rehearsal.ts`。

| 验收要求 | 实现与检查 | 独立结果／反事实 |
| --- | --- | --- |
| 无角色会话仍保存原条目，按 request_id 可查 pending，零反馈 | core:2696–2700、2937–2944；relay:7–10；daemon:319；rehearsal:277–314 读真实 relay_results 和发送方事件 | candidate-pending-01 的第 5 项 PASS；baseline-pending-01 精确红态：undelivered、ok=false、wake_undelivered、反馈 1，exit 1；M1／M2 拒绝 |
| 上线只入队，首启 unknown 零业务字节 | daemon:220–228；core:2666–2683；Panes.startController／dispatch／drain；rehearsal:337–360 走真实 controller_start，只替换 native spawn 与 liveness | 第 7 项 PASS：queue=1、writes=0、delivery=queued、I2=0；重复恢复仍一份。M4／M5 精确失败 |
| 只有 turn_submitted 后才 delivered，I2 恰一条且关联原 request／entry | panes:536–544、550–572；core:2624–2637；daemon:32–54、376–397；relay:51–65；rehearsal:362–387 | 第 8／9 项 PASS，paste=1、CR=1、原 send=1。中文 sentinel 独立按 delivery.message 找到目标 turn_submitted.seq=28，原 key 的反馈意图 seq=29；pending gate dispatch=0。M4 拒绝 |
| 原条目 created_at 不变 | core 只追加投递收据，不更新原 inbox；紧急停止在 core:2967 仍读取 stop.created_at；rehearsal:326、368 | 原发送回执、最终 inbox 条目 created_at 相同；sentinel SQLite 读回再次确认。投递收据自己的时间变化不等于原条目时间变化 |
| ack 来自实际接收者，重复 ack 不新增条目／wake，越权拒绝 | core:2780–2825；rehearsal:390–416 通过实际 inbox 文件／Stop 转交 | 第 10–12 项 PASS；只有一份 executor ack、一份 ack wake，ideation 的伪造 ack 返回 recipient_required |
| 有会话的路径仍投递，歧义仍报错 | core:2689–2707；rehearsal:288–294、317–320 | regressions-01/online 和 ambiguous 各 6 项 PASS；独立读回 online 最终 state=delivered。在线排练断言本身容许 queued，故不能单靠该断言证明立即送达 |
| bare pending／unknown 历史不自动重送 | core:2656–2657、2672、2683；rehearsal:328–360 预置两种不确定历史，核对 inboxDispatch 不存在 | 第 7 项 PASS；M3 将 bare pending 当可恢复后，queue=2 而期望 1，业务断言失败 |
| 原身份、旧 Stop、launch／preset／project／spec 等校验保留 | 原 relay.receive、panes.caller 和 gates.call 入口未削弱；controller-relay 用独立 foreign 值逐字段检查 | controller-relay 22 项、controller-entry 6 项 PASS；离线排练旧 Stop 不建条目，错误 launch exit 2 且仍只有一条 stop |

基线用候选完成条件覆盖测试文件、产品保持基线原样；不是用基线旧断言证明新语义。基线首先在离线契约处失败，后续上线与 I2 不可达，不能声称它执行了后半链。后半链缺接线／提前反馈的反事实由 M4、M5 单独证明。ack 去重、身份反例与既有时钟规则是未改变的要求，不要求它们在正确基线上失败。

## COUNTEREXAMPLE：5 个错误实现

每个变异从同一精确候选重新复制，均未改检查。完整替换文本在 `mutations.json`，逐次命令、退出码、时长和失败断言在 `mutant-runs.json`；每个输出目录保留原始命令回执、失败上下文及 SQLite。统一再现形式为在对应副本目录执行：

```sh
node workbench/tests/test_t078_a13_rehearsal.ts /新的绝对输出目录 --recipient-offline
```

| 变异副本 | 修改 | 实跑结果及正确失败点 |
| --- | --- | --- |
| m1-false-delivered | 将无会话分支的 pending 收据改成 delivered | exit 1；离线契约实际 delivered／feedback=1，预期 pending／0 |
| m2-pending-feedback | 移除 Stop 回执的 isPendingInboxResult 筛选 | exit 1；pending 正确，但 feedback_count=1，预期 0 |
| m3-bare-pending-replay | waitingForRole 不再要求 reason=role_session_missing | exit 1；真实 controller_start 后队列 2，预期 1；说明捕获了不确定写入重送 |
| m4-I2-before-write | daemon 允许 queued 结算，relay 允许 queued 认领反馈 | exit 1；目标仍 unknown 时 I2=1，预期 0；没有靠依赖失败或崩溃拒绝 |
| m5-no-startup-delivery | 移除 controller_start 的 resumeControllerInbox 调用 | exit 1；上线队列 0，预期 1 |

完成条件对以上 5 种核心错误实现够格；不推论为所有故障或完整真实 CLI 协议均已覆盖。

## 独立运行记录

Node 为 `v26.5.0`。所有 native controller 进程和 PTY 观察都是边界 spy；daemon、socket、请求文件、Stop 入口、relay、SQLite、gates、controller_start 与队列均使用候选生产代码，没有替换 pending 或反馈业务逻辑。

- 主链命令：在 `candidate/` 执行 `node workbench/tests/test_t078_a13_rehearsal.ts /private/tmp/t078-pending-review-01-68n7wjv3/candidate-pending-01 --recipient-offline`，exit 0，13 项 PASS。基线以同一命令形态在 `baseline/` 执行，exit 1；原始 stdout／stderr 和 `candidate-run.json`、`baseline-run.json` 均保存。
- `regressions-01/runs.json`：在线 6、歧义 6、controller-relay 22、controller-entry 6、inbox-domain 11、empty-declaration 17、pane-runtime 11 项均 PASS，逐条命令和输出目录可读回。
- 权限计数首次缺两份历史载荷而 exit 1，原 `regressions-01/permission.stderr` 保留；只从候选读取所需载荷后，在全新 `permission-02/` 重跑，3 项 PASS。`epochs-01/` 7 项 PASS。
- `sentinel-candidate/` 只把输入正文换成含随机标记、中文、两行和连续空格的正文；原 13 项检查 exit 0。独立额外读回见 `sentinel-checks-04.json`：正文落库完整，按既有末尾 CR/LF 移除规则写出一次；原 request 的持久结果仍为 pending，entry.created_at 未变，真实写出收据先于同 key 的 I2 意图。
- sentinel 首次附加断言错误地要求 PTY 保留末尾换行，失败说明保留在 `sentinel-postcheck-01-failure.json`；只读 SQLite `mode=ro` 打开失败，随后内存反序列化方案因本机 Python 缺接口失败，最后 `immutable=1` 读取保存库成功。没有改运行产物或据此重新运行产品来掩盖失败。

再现时每次选择新输出目录；已有输出按测试设计拒绝覆盖。5 个变异的实际命令也可直接从 `mutant-runs.json` 读取，不能覆盖已经保存的红态目录。

## 沙箱外运行回传与独立读回

执行主控 #302 回传目录为 `/private/tmp/t078-pending-review-outside-01.V0jciq`。本次读取 `controller-run.log`、四段 stdout／stderr／exit-code、`runtime-command-result.json`、`worker-inbox/results.json`、构建记录、原始输入／反馈字节及 inbox／dispatch 读回。下面保存足够核对的摘要；该目录后续可由主控按其原计划处置，本报告没有删除它，也没有复制完整现场。

| 阶段 | 原始证据 | 独立核对结果 |
| --- | --- | --- |
| 01 冻结核对 | 01-freeze.stdout.txt、.exit-code.txt | exit 0；candidate=`7039840565754f7999b27061191b6506e61ef9d2`，freeze=`4b48664fd689aab8d52a8721098939067928847e` |
| 02 源码副本 | 02-snapshot.stdout.txt、.exit-code.txt | exit 0；只解出 workbench／acceptance／scripts／fixtures，读取既有依赖；另逐字比较副本 core.ts、daemon.ts、relay.ts、worker 场景检查与候选 Git 内容，一致 |
| 03 真实运行 | 03-runtime.stdout.txt、.exit-code.txt、runtime-command-result.json | exit 0；status=PASS，14 项，9.132 秒；real_model_turns=0；stderr 为空 |
| 04 冻结复核 | 04-source.stdout.txt、.stderr.txt、.exit-code.txt | exit 0；diff 输出为空，运行期间受审源码未变 |
| 脚本收尾 | controller-run.log、final.exit-code.txt | 四段完成后，第 106 行未绑定变量错误；主控报告实际脚本 exit 1。final.exit-code.txt 的 0 是报错前保存的检查汇总值，不是 shell 实际退出码 |

实际运行命令如下，cwd 为 `/Users/luckye/Documents/Code/a2a-wt-t078`：

```sh
/Library/Developer/CommandLineTools/usr/bin/python3 -B /private/tmp/t078-pending-review-outside-01.V0jciq/candidate/workbench/tests/test_t078_input_entry.py --source /Users/luckye/Documents/Code/a2a-wt-t078 --backend-source /private/tmp/t078-pending-review-outside-01.V0jciq/candidate --output /private/tmp/t078-pending-review-outside-01.V0jciq/worker-inbox --worker-inbox
```

产品后端为精确候选副本；前端和客户端为已核对产品内容相同的原工作树。结果记录 source_revision=`4b48664fd689aab8d52a8721098939067928847e`、product_diff 为空、Node=`v26.5.0`，setup_complete／cleanup_complete／operator_credential_removed 均为 true。构建使用标准命令创建新 slot `/Volumes/WD-Elements/a2a-workbench/t078-input-t78-kgf2ph75/dist`；无旧构建替换。实际接收器是确定性原生程序，Claude 未启动，两个 controller_prepare 只是静态记录。

14 项原始检查均为 PASS：

| 检查 | 摘要 |
| --- | --- |
| window_input_reaches_pty | expected-input.bin 与 observed-input.bin 逐字相同，41 字节 |
| user_input_and_intervention | 一条中文 message 和一条关联同 input_id／attempt 的人工介入 |
| empty_callback_is_observation_only | 空回调仅观察事件，未生成输入；随后 CR 单独到达 PTY |
| anonymous_role_spoof_rejected_before_append | caller_identity_required，inbox 前后不变 |
| controller_prepare_is_static | 两条静态准备记录，只有一个 worker 接收器实际运行 |
| worker_client_queues_inbox_commands | 7 个 request_id 均非空且不同；会话 capability 存在，operator credential 不存在 |
| worker_issue_records_real_sender | from 为实际 worker，伪造 ideation 无效，正文含中文与非 BMP 字符仍保留 |
| worker_assign_spoof_denied | invalid_direction |
| worker_list_uses_real_scope | 只看到本人未确认条目，不泄露 foreign-message |
| worker_ack_is_owned_and_idempotent | 两次请求共一条 ack；投递均为 pending／role_session_missing |
| worker_ready_is_role_denied | controller_required |
| worker_foreign_ack_is_denied | recipient_required |
| worker_stop_receipts_are_delivered_once | 7 份真实回执，2 份 pending 不回灌，另 5 份同批反馈，重复旧 Stop 不重发 |
| revoked_worker_inbox_is_rejected | stale_attempt，未追加越权 inbox |

按外部 request_id 独立交叉核对原始反馈字节和 dispatch 读回：

- ack-one=`3a94223d-e457-4530-bbf5-7a532b9080da`，ack-two=`2ac16e46-dee5-4080-aa08-bb7671b8a1a2`；两者均未出现在 worker 的原始反馈字节或原七份请求的反馈 dispatch 中。
- 另五份 issue=`86d3a23a-82c2-4199-83ca-5ac065a3325b`、assign=`4f8655e2-7a1d-4c80-9abe-4e9d2f0109a6`、list=`e87fb024-6d2a-409f-bd22-c5be52744f84`、ready=`072f82a8-e87e-4599-96c2-fc09f80c219d`、ack-foreign=`3dfd0530-d641-4c8f-b187-22287d82d6e8` 均出现在同一条 gate feedback，按这组 request_id 关联恰好一批。
- 持久 ack.id=`f44d8c7f-3e70-4b72-8c92-6418ea33b273`，from=`worker:59595387-1537-40ed-8f82-6d64e3e70e3a`，reply_to=`owned-message`；只有一条，最终投递仍 pending。
- 原七份请求及重复旧 Stop 检查时反馈字节数为 5539。随后撤销 attempt 的负例另产生 stale_attempt 反馈，最终保存字节为 5974，最终 gate dispatch 总数为 2；它不是原七份请求的重复反馈。审查者附加读回最初错误地要求全程 gate 总数为 1，断言失败；随后按原 request_id 集合区分两个阶段完成核对，未改输出或重跑产品。另一次摘要提取将 dispatch.data 误当含 id 字段而报 KeyError，仅为读回工具错误。

## FINDINGS：按严重度

未确认本次冻结产品差异中的 P0／P1／P2 缺陷。

辅助脚本发现 **[P2] REVIEW-PENDING-OUTSIDE-01.sh:106**：`$TASK_FINAL` 后直接紧邻中文分号与文字，当前 Bash 将非 ASCII 字符并入未加大括号的变量名；`set -u` 因此在四段检查完成后报错。第 34、57 行的失败收尾提示存在相同写法，未在这次成功检查路径触发。最小修正是对相邻中文标点前的变量使用 `${TASK_FINAL}`／`${TASK_RC}`。本次只更新审查报告，保留原脚本与失败日志，不修写或伪装这次运行的实际 exit 1；不需要为该输出行重跑产品检查。这是 reviewer 自己交付的辅助脚本缺陷，不在冻结产品提交内。

结构审查：产品 diff 没有新增 catch、吞异常、兼容分支、平行业务 API 或不确定写出重试。core:2716 的宽 catch 是基线已有的外部投递边界，记录 undelivered／unknown 和原因后返回，未转换成成功。新恢复仅允许明确 role_session_missing 的无 thread／message 收据；每条仍持有原操作锁。relay 的反馈意图是先登记、结果不明则不重送。daemon 新函数调用的是既有 gates／Panes，不形成第二条 send 路径。测试的收尾宽 catch 和关闭句柄兜底已存在于基线；本候选只加长扩展场景的总期限，并保留每个原生命令 5 秒期限。

## LIMITATIONS 与结论边界

1. 沙箱外运行时缺口已由上节本次冻结对象的新运行补齐；不再依赖历史 `09b-pending-runtime-01` 的提交前 revision 标签。本报告保留必要摘要，未把外部脚本整体 exit 1 改称 0。
2. 该运行时夹具会在自己的 /tmp Git 仓库创建并提交测试基线；产品仓库只读。它不启动供应商 CLI、认证或模型。该行为在脚本开头明示，供执行主控核对。
3. 双真实 Claude、完整 09B／A-14、供应商模型、紧急停止真实两分钟链、整票截图与原门禁 8／9／18，本次均未运行。现有证据不能替代它们；本次也不裁定整张 T-078 可交付。
4. 在线入口的候选实测为 delivered，但排练断言容许 queued；这项单独断言的证明力度有限。反馈意图已保存但结果未知的“不重发”完成条件，本次有实现与静态调用序证明，未另做进程崩溃实跑。不得把 5 个变异的通过范围外推到这两项反事实。

RULE: 本次未确认产品重复缺陷，不新增治理规则。辅助脚本的同类收尾输出应使用带大括号的变量展开；`bash -n` 只能验证语法，不能证明 `set -u` 的实际展开能成功。本次 PASS 仅绑定上述冻结候选；候选变化后需要重新绑定审查对象，不能复用此通过结论。

T-078 PENDING REVIEW DONE
