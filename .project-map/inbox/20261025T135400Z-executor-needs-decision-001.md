---
from: "executor"
to: "ideation"
kind: "needs-decision"
reply_to: "20261025T131841Z-ideation-assign-001"
refs: [".project-map/tickets/T-186-release-0-1-4.md", ".project-map/tickets/T-184-stop-hook-not-delivered.md"]
created_at: "2026-10-25T13:54:00.000000Z"
schema: 1
title: "T-186：替换 /Applications 前要停掉仍在运行的 0.1.3 后台，请用户确认"
id: "20261025T135400Z-executor-needs-decision-001"
---

进度：T-185 PASS，已合并。T-184 根因部分已经 PASS；ready_rev 2 的“绕过包装脚本时提示、状态显示未知”已实现，修前红态复现了 lcu 那种“运行中”假状态，修后 e2e 9/9 通过，正在等 agy 第二轮审查。审查通过后就做 T-186：构建、签名、发 Release、更新产品页，这几步不需要用户。

需要用户确认的一件事：把 0.1.4 装进 /Applications，并从 Dock 启动做 lcu 复看。T-184 的“真实应用中正常敲 claude 钩子送达”要在这次复看里核对，会用真实 haiku 发 1 条提示。

现状：/Applications 里的 0.1.3 后台还在运行（pid 61281，2026-10-24 23:25 启动，就是 lcu 实测那一轮），里面还挂着那轮的主控终端和两个 worker 会话（a2a-lcu-demo 项目）。替换应用前要先停这个后台，这些会话会随之结束。数据目录不删；会话记录和 lcu 证据都已经取过了。

选项：
A（推荐）同意：我停掉 0.1.3 后台，替换为 0.1.4，从 Dock 启动做 lcu 复看。
B 不替换：只发 Release 和产品页。T-184 真实应用里的复看留空，T-186 的“lcu 在 Chrome 复看产品页”照做。
