# T-086 执行主控决策记录

## 建票与开工（2026-10-15 UTC）

来源：T-081 6e 回归（Grok wF:p30）发现 T-077 lifecycle 冲突套件两案（CONFLICT-ACTIVE-WRITEBACK、CONFLICT-ENDED-NEW-ATTEMPT）在 main 上因 T-084 新规则返回 trailer_identity_mismatch：test_worktree_lifecycle_e2e.py commit_worker 写 Model fixture、Launch thread_id。T-084 回归仅覆盖该文件 3 案。执行主控按 T-004 自建缺陷票 bb6c0ba3（ready_by executor），worktree a2a-wt-t086（exec/t086，基于 bb6c0ba3），npm ci（外置盘缓存），spawn-helper 755。worker：T-084 作者 Grok 会话 wF:p3Z（用户指定 Grok；无 A2A 启动记录，提交由主控代做）。写入范围：tests/acceptance 中写尾注的夹具与本票证据，不改 workbench/src。T-081 待本票合入后变基、全量重跑。

## 交付审阅、提交与独立审查（2026-10-15 UTC）

Grok wF:p3Z 交 T-086 READY：conflict_acceptance_host.ts 在 createThread 时写 worker-creations（启动记录）；test_worktree_lifecycle_e2e.py 新增 launch_record()，commit_worker 尾注取自该记录并核对与 attempt.delivery 一致。红态（基线两案 trailer_identity_mismatch）、绿态与冲突全套件 PASS；清点写尾注测试 17 项，11 组真实入口回归 PASS；test_task_cards_e2e 直接入口（不起 daemon，connect ENOENT）在基线 git archive 上同样 49 failures、trailer_identity_mismatch 0，判为既有。静态残余：run_worker_delivery.py 期望无 turn context 时钩子写 Effort unknown，门禁只放行 Model unknown（未实测）。
主控提交 d9dcc107（无 worker 尾注）。证据 28 MB，无单文件 >5 MB。独立审查：新开 fresh Grok wF:p44（cwd a2a-wt-t086），只读，仅写 independent-review-01.md。

## 返工 #13/#16 与第二轮审查 #17（2026-10-15 UTC，执行主控接续）

审查 01 NO_GO 报告提交 8f3d1b5e（exec/t086）。#13 派返工给 Grok wF:p3Z：完成条件分开启动记录与任务卡/thread_id/常量；补 tracer/widen；run_worker_delivery.py 按用户决定"只改脚本期望"（answer 20261015T131159Z-ideation-answer-001）。#16 催收尾。worker 报 T-086 READY：宿主为每个 attempt 写独有 launch/cli/model/effort，runtime_identity.launch 取记录 id；返工红/绿两案、冲突七案 PASS；M1–M4 verify 失败，M5 两案走不到 delivery 分支（未造路径）；tracer PASS，widen wide 并发时 widen_score_after_cas 5 秒等待超时、基线并发同样复现、单跑 PASS；run_worker_delivery.py 未运行。主控核对 diff（仅 conflict_acceptance_host.ts、run_worker_delivery.py 与证据；delivery.turn_id 在 core.ts:3402 存在），提交候选 c9e431aa。证据 120 MB，无单文件 >5 MB。
#17：新开 fresh Grok s15-t086-rev2（wF:p46，cwd a2a-wt-t086），只读，仅写 independent-review-02.md。

## 验收与合入（2026-10-15 UTC）

审查 02（s15-t086-rev2，fresh Grok）结论 PASS：三条均已解决，自建 M1–M4 在 verify 失败，M5 两案走不到 delivery 分支属实，七案重跑 OK，widen 并发超时为基线既有。提交审查报告后 exec/t086 变基到 main，变基前后 workbench/acceptance/scripts diff 为 0，main 快进到 e38b87cb1。T-086 关闭（Resolution 见票据）。下一步通知 T-081 变基、补 6e 拒收案、全量重跑。
