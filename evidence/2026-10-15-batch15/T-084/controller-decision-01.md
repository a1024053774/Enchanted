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
