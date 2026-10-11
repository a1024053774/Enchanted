---
from: "executor"
to: "ideation"
kind: "needs-decision"
reply_to: "20261011T042325Z-ideation-revise-001"
refs: ["ticket:T-075"]
created_at: "2026-10-11T04:35:44.163256Z"
schema: 1
title: "T-075-3：只放行后台 socket 未生效（关闭托管网络代理时），按 rev 3 停下"
id: "20261011T043544Z-executor-needs-decision-001"
---

按 rev 3 做的单 turn 验证没有通过。证据：evidence/2026-10-10-batch12/T-075/card-3/outside-verify-03/probe（真实 Codex 累计 2/10 回合，执行主控在沙箱外跑）。

Codex 0.162.1 的启动参数：
-a never --sandbox workspace-write
-c network.allow_unix_sockets=["<后台 socket>"]
-c sandbox_workspace_write.network_access=false
-c features.network_proxy=false

结果：
- 沙箱里连后台 socket，仍然 EPERM。
- 对照组：连另一个 socket 被拒，连 TCP 也被拒。
- git 钩子里连后台 socket，同样 EPERM。
- 没有重试，没有提交。隔离 home 已删除。

后台入口上的门禁正反例 15/15 通过，窗格那条链路也是通的。现在只卡在 worker 怎么连到后台。

推断（还没验证）：二进制里 allow_unix_sockets 出现在托管网络代理的配置结构里，所以它很可能只在打开 features.network_proxy 时才生效。打开代理就会多出一个本地代理进程，网络改由代理按域名名单放行。

请用户选：
A2. 打开托管网络代理，域名名单留空，再加 allow_unix_sockets=[后台 socket]，用 1 个 turn 验证三件事：后台 socket 能连上；另一个 socket、任意 TCP、任意外部域名仍被拒；不需要额外的批准。验证不过就停。代价是 worker 会话多一个代理进程，网络改由代理把关，而不是沙箱直接拒绝。
B. 沙箱不动，worker 在 worktree 里写交付请求文件，由 Stop hook 转交给后台。用户之前要求 A 不成立时不要改走这条路，所以要改走这条路，需要用户明确同意。
C. 其他，比如这一版先由执行主控在沙箱外代 worker 调用 submit。这样就不符合“worker 显式通过后台交付”的要求，只能算临时办法。

在用户决定之前，T-075-3 暂停在交付通道这一段，其余部分已经做完的保持现状。