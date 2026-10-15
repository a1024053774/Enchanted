# T-084 执行主控决策记录

## 建票与开工（2026-10-15 UTC）

来源：用户决定 6e（answer 20261015T030558Z-ideation-answer-001，逐字）"补：必须与启动记录一致 (Recommended)"，选项原文："Launch 必须等于本 attempt 的启动记录号，Tool/Model/Effort 必须与那条记录一致（spec 允许 Model 写 unknown 的情形保留），不一致就打回。执行主控另开小票修，T-081 加对应的拒收案例。"
执行主控按 T-004 边界自建（ready_by: executor），票 fb5dd288。worktree a2a-wt-t084（exec/t084，基于 main fb5dd288），npm ci 按 README（外置盘缓存）。worker s14-t084（wF:p3W，launch-3e340a45ede347229ed4832fd77755f7，session e397d595-15cb-4c01-8779-83a11ff0d1ed，gpt-6.1-sol xhigh、service_tier="default"）。写入范围：core.ts 尾注核对与本票测试、证据；与 T-081（6e 案在本票合入后加）、T-078（不碰 checkTrailers）错开。存活 a2a Codex 3/3（s13-t078m、s14-t081、s14-t084），free+inactive 约 3.4 GB。
同时：issue 20261014T190348Z 以 disposition 20261015T030632Z 关闭（Fast 已在 2876c9fd 改掉）；T-081 第 6 项下记入用户 6a/6e 修订；T-081 worker 派第 7 项事实复测（/tmp 外夹具、prefix_rule 写入范围、CAS 外部移动行为）。
