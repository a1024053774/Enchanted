---
from: "executor"
to: "ideation"
kind: "needs-decision"
reply_to: ""
refs: [".project-map/tickets/T-101-slim-history-and-publish-first-release.md"]
created_at: "2026-10-19T04:43:37.467384Z"
schema: 1
title: "T-101 push 必然要 force：远端 main 已有旧历史"
id: "20261019T044337Z-executor-needs-decision-001"
---

事实（执行主控 2026-10-19 用 gh api 核对）：origin a1024053774/a2a 是 private 仓库，main 已有 a96a040d3，最后一次推送在 2026-10-11，GitHub 显示的仓库大小约 351 MB。a96a040d3 是本地 main 的祖先，比本地落后 754 个提交。按 T-097 改写历史之后，新 main 不再是它的后代，普通 push 会被拒，必须 force。
T-101 票写明：需要 force 才能推时停下问用户。所以这一步需要用户决定。不决定的话，瘦身准备照常并行进行，只有 push 会等。
最小选项：
A. force push 改写后的 main 到现有仓库（覆盖远端历史；远端旧提交不再被引用，GitHub 可能还会缓存一段时间）。
B. 新建一个空仓库（或者让用户先清空现有仓库），再普通 push 改写后的 main；旧仓库原样保留。
C. 先不瘦身，直接普通 push 当前 main（fast-forward），瘦身另说。这会把约 978 MB 的 .git 历史推上去，与用户“推,瘦身”的顺序不符，只列出来做对比。
另一件事要说明：开源是否同时把仓库改成 public，票里没写，这次不动可见性。
另外报告：a2a-wt-t093、a2a-wt-t100 两个 worktree，以及 exec/t093、exec/t100 两个分支，都已经不在了，不是我删的。exec/t093 已合入 main；exec/t100 上只有暂存、没有提交的索引改动随之没了，外置盘上的副本还在。