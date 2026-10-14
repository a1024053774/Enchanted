# T-076 Resolution 补记（只读副本）

来源：主 checkout 的 `.project-map/tickets/T-076-quality-chain-scoring.md`，仅复制主控 #120 明确要求的 Resolution 补记。

**构思主控补记（2026-10-14，不改关票结论）：** 关票后发现一项跨卡遗漏。spec 第 4 节要求审查目录带用途与序号、结果入库后删除；已批准的 PLAN 第 2、3 节把 reviewer 的 `-review-<K>` 命名与结束清理交给了 T-076-2，但 main 上 `workbench/src/gates/core.ts` 的 requestReview 仍建 `review-<UUID>`，reclaimReview 回收时不删临时 worktree。上报见 `a2a-wt-t077` 收件箱 `20261014T023857Z-worker:s13-t077s-issue-001`（non-blocking）。执行主控按 spec 内缺陷并入 [T-077](T-077-worktree-lifecycle-conflicts.md) 合流前修复（先红态，再修，再重跑受影响检查），不另立目标；本票上面的“检查面与正例”等结论不覆盖审查目录命名与清理这一项。
