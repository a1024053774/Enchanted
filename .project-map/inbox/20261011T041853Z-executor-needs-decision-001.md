---
from: "executor"
to: "ideation"
kind: "needs-decision"
reply_to: ""
refs: ["ticket:T-075"]
created_at: "2026-10-11T04:18:53.963506Z"
schema: 1
title: "T-075-3：Codex 沙箱拒绝 worker 连后台本地入口，需定 worker 交付通道（涉及沙箱权限）"
id: "20261011T041853Z-executor-needs-decision-001"
---

T-075-3 实测（evidence/2026-10-10-batch12/T-075/card-3/outside-probe-01，用了 1 个真实 turn）：
- 能走通的部分：编排后台常驻、node-pty 窗格、派发登记与 bracketed paste 注入、回合开始和结束的 hook、空闲判断。
- 走不通的地方：受管 worker 以“不问”模式在 workspace-write 沙箱里调用后台 CLI 交付时被拒，报错 connect EPERM（Unix socket）。
- Codex 自己发起的 hook 不受这个沙箱限制，可以连上后台。

spec 第 1、3 节规定 worker 经后台命令行入口交付，并且要显式 submit。要让这条路通，得给 worker 一个可行的通道。请用户选：

A. 每会话启动参数只放行后台那一个 socket，即 Codex 0.162.1 的 network.allow_unix_sockets=[<后台 socket 路径>]，网络保持关闭。worker 用同一个 CLI 交付。这是给受管 worker 加一项窄沙箱权限。是否真的只放行这一个 socket，执行主控已安排在夹具里用 1 个 turn 验证，结果出来后补报。
B. 不改沙箱。worker 在自己的 worktree 里写一个交付请求文件（显式 submit），由不受沙箱限制的 Stop hook 读取，转交给后台。交付仍然是 worker 显式发起的，但多了一层文件中转，worker 的其他命令（查状态、上报问题）也得走同一种方式。
C. 其他。

执行主控推荐 A，前提是验证确认只放行这一个 socket。理由：worker、主控、界面都走同一个入口，没有第二条路径；权限加在每会话启动参数里，符合 T-071 的权限四层。
在你们决定之前，T-075-3 能用脚本做的部分（反例、库表、派发与状态）继续做；交付通道这一段先留空，用明确报错占位。

另外记一笔：探针脚本在收尾时崩溃，隔离的 CODEX_HOME 没有自动删除。执行主控已手动删除，worker 正在修这个缺陷。