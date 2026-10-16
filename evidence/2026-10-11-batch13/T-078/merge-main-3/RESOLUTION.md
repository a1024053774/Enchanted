# 主控 #319：合并 T-082 与 T-078 的冲突核对

2026-10-16。**冲突文件内容与静态核对 PASS；合并提交 INCOMPLETE，留给主控；合并后的完整运行回归 INCOMPLETE／未运行。** 父提交为 T-078 `150ef6516f6ef5aaa6855631b770ce262991ffbf` 与 main `0e6c2b833f6da64243f71d670ea45bb9116fda4d`。原 rebase 已由主控中止，本轮只处理主控建立的 merge，不运行 commit、merge --continue、rebase、reset 或 push。A-14 现场未访问、未发键、未回收。

## 唯一冲突：relay.ts

冲突在 reviewer 与 worker/controller 的命令字段表，不在 pending 查询或意图去重中。处理如下：

1. reviewer 分支接受 `review_id/candidate_commit/verdict/findings/review_requirements/report`，取 T-082 的完整字段表；仍只允许 review_submit，后续仍经过真实 reviewRequest 严格解析与 review_id 身份核对。没有让 reviewer 使用 inbox/stop。
2. 其余分支保留 T-078 的 submit/status/issue、inbox_send/list/ack/ready；stop 仍仅在 controller 分支出现，controller 命令白名单、schema 2、launch/preset/project/task/spec_rev/native_session/prompt_id 核对均保留。没有把 worker/controller 退回 main 的三命令表。
3. `deferredInboxFeedback` 的真实 pending 结果查询、`claimDeliveredFeedback` 的 delivered 条目核对与先写意图去重、receive 的请求归属与已持久化结果回放均保留原文。

整个解决后的 relay.ts 与 T-078 父文件逐字比较，唯一变化就是给 reviewer 字段表增加两个字段；没有重写其他分支。原冲突文件保存在 relay-conflict-original.txt。

## 自动合并文件的逐段核对

| 文件 / 区域 | 保留与交汇判断 |
| --- | --- |
| core.ts：reviewAttempt 到 cleanupReviewWorktree | 与 main 的整个区域逐字相同：reviewer 身份使用 candidate_workspace；副本不携带 .git，链接审计与副本所有权核对保留；启动检查绑定实际副本、workspace-write、断网、排除 /tmp/TMPDIR、全新 home、无 resume/fork；结束时校验原候选、worker/review worktree 和共享 refs，确认停机/归档并清理两目录后才写 review_reclaimed。失败仍使审查作废、任务暂停并上报 |
| core.ts：review_submit、integrate | 两段分别与 main 逐字相同：完整 report 与 review_requirements 入库，workspace 必须绑定本次副本；integrate 仍在 task 操作锁中调用 requireReviewed，而后者要求本次 review_reclaimed，不能只凭已收到 verdict 提前集成 |
| core.ts：controller 登记、inbox 到 emergencyStop | 与 T-078 父文件的对应整段逐字相同：缺目标会话时追加 sender-visible pending，不造反馈；上线仅入 unknown 队列；真实刷新只认提交收据；ack/权限/created_at 语义不变。这些路径没有替代 reviewer 的身份或结束检查 |
| panes.ts：createReview、worker/reviewer 启动 argv 与 launch record | 与 main 对应区域逐字相同：reviewer 的 cwd 与记录 worktree 为本次 candidate_workspace，workspace-write、网络关闭、两项临时目录排除与审查字段保留；普通 worker 仍使用 attempt.workspace。Claude controller 通过独立 startController/claudeLaunch 路径启动，不借用 reviewer 参数 |
| panes.ts：dispatch/wake/readWakeDelivery/drain/release/screenKey | 与 T-078 父文件对应整段逐字相同。assertStartup 仍要求 unknown、无 active/failed/stopped/archived/writing/userDraft/pendingInputs；只是不因队列非空拒绝已批准首启键，三次检查位置不变。screenKey 不 drain，drain 仍要求 idle；控制键收据不算 delivered，只有 turn_submitted 才算送达 |
| panes.ts：Claude signal、daemon.ts、store.ts、claudeLaunch.ts、hookTrace.ts | 对应 signal 整段与后五文件分别保持 T-078 原文。reviewer Stop 仍经 daemon 的 reviewRequest → 请求文件 → relay → 门禁，controller Stop 的 pending 不回灌与延后原 I2 不进入 reviewer 反馈路径；reviewer 的 completedReview 仍在连接关闭后调用真实 reclaimReview |
| contracts/a2aGates.ts、qualityProtocol.ts | schema 与 A2AReview 保留 T-082 新字段；qualityProtocol.ts 整文件与 main 相同。reviewer 输出的两个新增字段不会在门禁解码前丢失，pending 仍使用原 inbox 契约 |
| daemon_acceptance_host.ts、workbench/README.md | host 保留 main 的 observed-facts 注入，同时保留此前的受控运行夹具；未编辑。README 同时保留审查新边界与本分支的 pending／首启队列说明。未拿 T-078 文档覆盖 T-082 的权限边界 |

可重跑的源码审计为 audit-merge.py；source-audit-03.json 的 16 项静态核对 PASS。它证明指定区域原文保留，不能替代行为检查。source-audit-01/02 为定位结束锚点时的脚本预检错误，均保留；修正只涉及审计脚本，没有为使比较通过而改产品代码。

本轮实际运行 `test_t082_review_protocol.ts`，输入是 T-082 留存的真实 reviewer JSON；12 项 PASS，原始命令、输出与 SQLite 保存在 protocol-local-01/。覆盖 report 不丢失、字段/类型/身份/严格 JSON 拒绝及真实 RequestRelay 转交，未启动 daemon、供应商 CLI、HTTP API 或模型。

六个相关 TypeScript 文件的 node --check 和显式冲突标记扫描均 PASS，详见 syntax-and-markers-01.json。注意：Node 对带原冲突标记的 TypeScript 文件也返回了 0，所以不能拿它作为冲突已解决的单独证明。relay-conflict-syntax.json 中“无法解析”的说明写错，真实观测 exit_code=0 未改写；后续显式标记检查与源码逐字核对补足这一限制，没有把它当产品红态。

**Tracer bullet**：合并后仍重证 pending → unknown 入队 → 六个批准首启键 → initial release → turn_submitted → delivered → 原 I2；并重证 reviewer 报告 → 结束检查 → review_reclaimed → integrate。**Deep modules**：screenKey、业务 drain、review 生命周期各维持原职责，没有新增入口或兼容分支。**Ubiquitous language**：pending、queued、delivered、control action 与 review_reclaimed 是不同收据，不相互替代。

## 合并提交后的回归

主控完成合并提交后，在沙箱外执行一个命令，输出必须使用尚不存在的目录：

```sh
python3 -B /Users/luckye/Documents/Code/a2a-wt-t078/evidence/2026-10-11-batch13/T-078/merge-main-3/run-regressions.py --output /Users/luckye/Documents/Code/a2a-wt-t078/evidence/2026-10-11-batch13/T-078/merge-main-3-outside-01
```

只读预检（本轮已实跑 PASS，完整输出在 regression-preflight-01.stdout.txt／stderr.txt）：

```sh
python3 -B /Users/luckye/Documents/Code/a2a-wt-t078/evidence/2026-10-11-batch13/T-078/merge-main-3/run-regressions.py --check-only --output /Users/luckye/Documents/Code/a2a-wt-t078/evidence/2026-10-11-batch13/T-078/merge-main-3-outside-01
```

脚本只在已提交的合并候选上执行，要求两个父版本均为 HEAD 祖先、没有进行中的 merge、源码与 HEAD 一致、外置构建盘存在。顺序运行，不并行占用内存；每段保留实际 argv、当前完整提交号、原始 stdout/stderr 和既有测试结果，任一失败即停，不重试。超时仅终止自己创建的运行器进程组，明确将可能的脱离进程组服务标为未知并交主控核对，不声称清理成功。

1. pending/local 的 11 组：离线 pending 链、在线立即投递、歧义拒绝、controller relay/真实入口、inbox domain、权限计数、epochs、空框声明、pane runtime、受管 inbox entry。
2. startup 领域候选 15 项与精确 M5；要求七个 release 前真实刷新时点仍 queued／无 delivered 历史／无 I2，M5 在新断言被拒。
3. startup 真实入口候选 14 项与精确 M5；六个键后逐一刷新、再 release/delivered/原 I2/ack。PTY 与供应商身份明确为 spy，不外推实际 Claude onboarding。
4. worker 收件箱真实 Electron／原生入口 14 项。
5. T-082 受控 tracer、四种启动边界变异（旧 read-only、错误工作目录、网络开启、/tmp 可写），各由真实门禁拒绝。
6. T-082 六个报告/结束关键用例：真实 report 原形经 Stop/relay 入库；审查目录外改动与共享 refs 变化均作废；review_requirements 的 workspace 错误拒绝；dirty/clean 两种结束核对前 integrate 均拒绝，正常结束核对后才允许集成。

T-082 的回归使用已合入 main 的现有检查，不启动真实 Codex，不复跑供应商网络/沙箱证明或已知源码审计会拒绝的旧 T-076 总 runner。没有修改 T-082 的测试或门禁。完整运行尚未执行，不能写 PASS。

本次 project-map status 为 Problems 0、Stale 3：合并中 main 已入索引的 intent.md 变化触发 CONTEXT.md、AGENTS.md、README.md 提示。保留 main 原文，不在解冲突阶段改治理文件；合并提交后须再查，若仍 stale 交主控处理。当前不能把地图检查写成 PASS。A-14 回收与 A-15 准备仍待本次合并和关键回归完成。
