# T-084 执行主控决策记录

## 建票与开工（2026-10-15 UTC）

来源：用户决定 6e（answer 20261015T030558Z-ideation-answer-001，逐字）"补：必须与启动记录一致 (Recommended)"，选项原文："Launch 必须等于本 attempt 的启动记录号，Tool/Model/Effort 必须与那条记录一致（spec 允许 Model 写 unknown 的情形保留），不一致就打回。执行主控另开小票修，T-081 加对应的拒收案例。"
执行主控按 T-004 边界自建（ready_by: executor），票 fb5dd288。worktree a2a-wt-t084（exec/t084，基于 main fb5dd288），npm ci 按 README（外置盘缓存）。worker s14-t084（wF:p3W，launch-3e340a45ede347229ed4832fd77755f7，session e397d595-15cb-4c01-8779-83a11ff0d1ed，gpt-6.1-sol xhigh、service_tier="default"）。写入范围：core.ts 尾注核对与本票测试、证据；与 T-081（6e 案在本票合入后加）、T-078（不碰 checkTrailers）错开。存活 a2a Codex 3/3（s13-t078m、s14-t081、s14-t084），free+inactive 约 3.4 GB。
同时：issue 20261014T190348Z 以 disposition 20261015T030632Z 关闭（Fast 已在 2876c9fd 改掉）；T-081 第 6 项下记入用户 6a/6e 修订；T-081 worker 派第 7 项事实复测（/tmp 外夹具、prefix_rule 写入范围、CAS 外部移动行为）。

## 供应商容量阻塞（2026-10-15 UTC 03:1x–03:2x）

首次派发后 s14-t084 报 "■ Selected model is at capacity. Please try a different model."，任务未开始；窗格随后出现一条非主控发出的 "继续"（按人工输入记录），同样报容量不足。等待 5 分钟后主控重发任务书一次，仍报同一错误。按计划不再重试、不换模型（用户只允许 gpt-6.1-sol）。同一模型的 s13-t078m、s14-t081 运行中未受影响，推测为新会话无容量分配（推断，未核实）。状态 BLOCKED（外部容量）；窗格 wF:p3W 保留 idle，不回收，待用户或容量恢复后再决定。

## 退避后第三次（2026-10-15 UTC 03:4x）

退避 10 分钟后给 s14-t081 与 s14-t084 各发一次"继续"：s14-t081 恢复工作；s14-t084 仍 "Selected model is at capacity"（共三次，任务从未开始）。T-084 BLOCKED（外部容量），不再自动重试、不换模型；窗格 wF:p3W 保留 idle。等用户决定：继续等待、关闭该会话后重开新会话一次、或暂缓 T-084。

## 用户指示重开会话（2026-10-15 UTC）

用户原话（本会话直接回答）："反正这个对话没做什么，重新换个新对话执行这个任务"。关闭 s14-t084（wF:p3W，idle，无交付、worktree 无改动）。新开 s14-t084b：wF:p3Y，launch-db23395ebc994f2286e1adba1e70316b，attempt a2，session 35b1eada-b8bc-4cdf-8fe7-997088b14355，argv 同前（gpt-6.1-sol xhigh、service_tier="default"、--no-daemon）。重派任务书。

## a2 会话中途容量不足（2026-10-15 UTC）

s14-t084b 开工后读代码途中报 "Selected model is at capacity"；退避 3 分钟后催一次，仍报同一错误。按约定停止自动重试，BLOCKED（外部容量），交用户决定。已做的只读调研未落文件，worktree 无改动。

## 改用用户开的 Grok 会话（2026-10-15 UTC）

用户原话（本会话直接输入）："我开了个 grok,你 084 用 grok 做"。Grok 窗格 wF:p3Z（agent grok，session 01a13da2-f879-7410-8da3-9d9f17550679），屏幕显示 Grok Build 1.0.52、Grok 4.7 (xhigh)、always-approve，cwd 为 a2a 主 checkout。该会话由用户启动，非 scripts/launch-worker，无 A2A 启动记录；always-approve 无沙箱与逐次批准，约束只能写在任务书：只在 a2a-wt-t084 工作、不 commit/push、不写全局配置、不碰 Herdr server、不调真实模型 API。提交由主控执行，提交无 A2A worker 尾注（无启动记录可绑定），如实记为用户指定的非受管 worker 产出。
s14-t084b 窗格 wF:p3Y 已不存在（非主控关闭），a2a-wt-t084 无改动。派发经 scripts/dispatch（batch 2026-10-15-batch15，--agent wF:p3Z）。

## Grok 交付审阅、提交与独立审查（2026-10-15 UTC）

Grok（wF:p3Z）交 T-084 READY：checkTrailers 加 4 行（attempt.delivery 存在时 Launch=delivery.launch_id、Tool=delivery.cli、Model=delivery.model 或字面量 unknown、Effort=delivery.effort，码 trailer_identity_mismatch），README 同步。经真实 cli.ts + 受控宿主：红（main 上四种伪造均放行）、绿（四种拒收，match/unknown 过，none 记 1 次人工介入）、变异（逐行删除各放行对应一案）。作者自报局限：无 delivery 的 attempt 仍只要求非空；受控宿主 model/effort 与任务卡相同，不能单独证明比较对象非任务卡；spawn-helper（gitignore）权限改 755。
主控在 a2a-wt-t084 提交 882638b3（无 A2A worker 尾注：Grok 非 launch-worker 启动、无启动记录；提交说明写明）。证据 6.8 MB，无单文件 >5 MB。
独立审查：Codex 当前无法启动，按用户"用 Grok"的方向新开 Grok 窗格 wF:p41（cwd a2a-wt-t084，Grok 4.7 xhigh，always-approve，无作者历史），只读，仅可写 independent-review-01.md；冻结候选 882638b3，基线 fb5dd288。

## 独立审查 01：NO_GO（测试完成条件）与返工（2026-10-15 UTC）

审查员 Grok wF:p41（fresh、只读）报告 independent-review-01.md：checkTrailers 四行在受管 submit 上与用户决定一致（重跑绿态、基线红态、Launch 删行变异）。需修复：
- 发现 1（P2）：绿态无 Effort=unknown 拒收案；把 2002 行改为也放行 unknown，套件仍 PASS。
- 发现 2（P2）：受控宿主把记录 model/effort 抄自任务卡、测试 209 行又要求二者相等，把 Model 比较换成 task.card.executor.model 套件仍 PASS；审查员拆开宿主证明当前实现比的是记录。
- 发现 3（P2，事实）：只 claim 的 submit 无 delivery，伪造四项可通过尾注核对与审查到 verified；integrate 被 score_provenance_required 拒，主分支不动；票据"拿不到记录就停下"未在运行时发生。属设计问题，交构思主控问用户，本轮不改。
审查员只写了报告；其 /tmp 探针脚本与输出由主控复制进 independent-review-01-probe/（3.4 MB），与报告一并提交 b4470100（无 worker 尾注）。发现 1、2 退回作者 Grok（wF:p3Z）返工。
