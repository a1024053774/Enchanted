# T-090 主控记录

## 建票与开工 #1（2026-10-16 UTC）

来源：T-078 独立终审后在最终整合版上重跑原交付 8/9/18（review-followup-regressions-01），coop 段 test_submit_requires_clean_head_and_cannot_replace_frozen_candidate 报错。worker 诊断（F4-REVIEW-BOUNDARY-DIAGNOSIS-01）与两版本对照（review-followup-f4-compare-01）：合并 T-082 前 150ef6516 PASS，main 0e6c2b833 INCOMPLETE（review_worker_workspace_changed）。根因：T-082 新增的审查结束核对要求 worker HEAD == 冻结候选，而 T-082 票原文只要求"候选提交号不变、审查目录与 worker worktree 干净、共享仓库引用未变"；受保护验收要求候选冻结后 worker 再提交也不能替换 C。判为实现比要求收得更紧的缺陷，按 T-004 自建缺陷级票 T-090（ready_by executor）。
执行主控验收 T-082 时未整组重跑原交付 8/9/18，漏掉此回归——记为主控验收流程缺陷。
worktree /Users/luckye/Documents/Code/a2a-wt-t090（exec/t090，基于 main f08a280bd，按 T-088 改为稀疏检出 workbench、acceptance、scripts、.project-map、findings、evidence/2026-10-16-batch16）。worker s16-t090（wF:p4P，launch-b4da324aa23d48eda3c1cfcee621a6c5）。任务卡 task-card-T-090-1.md 经 scripts/dispatch 派发。Codex 会话 2 个（t078、t090）。
