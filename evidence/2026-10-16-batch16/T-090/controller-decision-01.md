# T-090 主控记录

## 建票与开工 #1（2026-10-16 UTC）

来源：T-078 独立终审后在最终整合版上重跑原交付 8/9/18（review-followup-regressions-01），coop 段 test_submit_requires_clean_head_and_cannot_replace_frozen_candidate 报错。worker 诊断（F4-REVIEW-BOUNDARY-DIAGNOSIS-01）与两版本对照（review-followup-f4-compare-01）：合并 T-082 前 150ef6516 PASS，main 0e6c2b833 INCOMPLETE（review_worker_workspace_changed）。根因：T-082 新增的审查结束核对要求 worker HEAD == 冻结候选，而 T-082 票原文只要求"候选提交号不变、审查目录与 worker worktree 干净、共享仓库引用未变"；受保护验收要求候选冻结后 worker 再提交也不能替换 C。判为实现比要求收得更紧的缺陷，按 T-004 自建缺陷级票 T-090（ready_by executor）。
执行主控验收 T-082 时未整组重跑原交付 8/9/18，漏掉此回归——记为主控验收流程缺陷。
worktree /Users/luckye/Documents/Code/a2a-wt-t090（exec/t090，基于 main f08a280bd，按 T-088 改为稀疏检出 workbench、acceptance、scripts、.project-map、findings、evidence/2026-10-16-batch16）。worker s16-t090（wF:p4P，launch-b4da324aa23d48eda3c1cfcee621a6c5）。任务卡 task-card-T-090-1.md 经 scripts/dispatch 派发。Codex 会话 2 个（t078、t090）。

## 红绿、整组回归与对照 #2–#12（2026-10-16 UTC）

红态 red-01 PASS（原用例以 review_worker_workspace_changed 失败）；基线 boundary-baseline-01 PASS；修复 0bcc5ab66（core.ts：审查开始时把 worker HEAD/分支/status 存入 review_requested 事件的 worker_boundary，结束时按 review_id 取回核对未变，不再要求 worker HEAD==候选）。
整组回归：02 测试宿主 ready 文件读取竞态（worker 修为完整写入后发布，18dd12c29；源码副本改回内置盘 /tmp）；02 recovery 2 例 verify 超时；03 run 组 4 例短时限失败；04 recovery 2 例回收慢于 driver 期限（事件无门禁拒收码）；05 run 组 1 fail + 1 error。主控先后把 03/04 归因于用户其他项目构建（sitecraft-ai tsc/next-build）的负载，05 的负载日志显示负载尖峰（1 分钟 58.7）与 run 组开始重合，该归因不可靠，已更正。
对照：recovery 两用例在 main-before-T082 271ac55d8、main-T082 0e6c2b833、T090 18dd12c29 上单独运行均 PASS；run 组 18 在三版本上单独运行均 18/0/0 PASS。结论：偶发、短时限敏感，不是 T-090 引入。偶发失败另报非阻塞 issue 20261016T162759Z。
在 T-090 版本上 coop 8、recovery 9、run 18 分别在不同运行中完整通过，尚未在同一次整组运行里一起通过（如实记录）。剩余步骤 green-remaining-01 PASS：CAS 1、cards 15、worker 三反例（HEAD 改、变脏、分支改仍被拒）、T-082 七场景与四启动变异；三条"删掉 worker 检查"的反事实按预期失败。
#12：fresh 独立 reviewer s16-t090-rev（wF:p4Q）审冻结候选 ca6ac9aa3，含变异检查。Codex 会话 3 个（t078、t090、t090-rev）。

## 验收与收尾 #13（2026-10-16 UTC）

审查 01 INCOMPLETE 的两项（沙箱内变异未到业务断言、README stale）由主控补证：沙箱外按 reviewer 设计的三变异执行，全部以业务断言失败；README 补注。审查 02 PASS（e89ccaa34，产品与测试同 ca6ac9aa3）。合入 main 89a1915f1（--no-ff），status 0/0，打分 score-ff7303c80b2741848fb1542bfe608ec5（边界 3、工程 2），票关闭（Resolution）。回收：s16-t090（wF:p4P）、s16-t090-rev（wF:p4Q）均 idle、交付已提交后关闭窗格；worktree a2a-wt-t090 移除，分支 exec/t090 删除（已合入）。非阻塞 issue 20261016T162759Z（偶发短时限失败）保持开放。
