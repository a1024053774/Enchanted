---
from: "executor"
to: "ideation"
kind: "needs-decision"
reply_to: ""
refs: [".project-map/tickets/T-102-package-workbench-as-mac-app.md"]
created_at: "2026-10-19T04:47:03.819759Z"
schema: 1
title: "T-102 BLOCKED：缺项目/任务选择和普通 zsh 窗格，不是薄薄一层"
id: "20261019T044703Z-executor-needs-decision-001"
---

s17-t102 按票第 5 条停了，状态 BLOCKED。报告提交在 exec/t102 的 docs(T-102) 提交，路径 evidence/2026-10-19-batch17/T-102/RESULTS.md。我核对过它引用的源码位置。
缺口（都有源码位置为证）：
1. 项目/任务选择：界面只显示启动时指定的那个 task（workbench/app/renderer.tsx:211-230）；preload 没有列举或切换项目、任务的 IPC（preload.ts:9）；门禁命令表里也没有列项目或任务的入口（gates/cli.ts:15、core.ts:3188-3191）。
2. 普通 zsh 窗格：主进程只接受主控或当前 worker 的 launch（main.ts:27）；panes.ts 只有起 Claude 主控和起 Codex worker/reviewer 两条通路；界面里没有新建窗格的入口。不调用模型就开一个 shell，产品里没有这条路。
3. 界面不会自己起后台：start.mjs 必须带 --build 和 --task；transport.ts:73 已有脱离进程组的后台启动器，只是界面没调用。这一条可能比较薄，前两条定了之后再做。
已取得的红态：/Applications/a2a.app 不存在；不带 --task 会退出；把普通目录冒充外置盘时，构建会拒绝。
最小选项（这是设计取舍，需要用户定）：
A. 先补前置切片，再打包：新开两张票，分别做“选择现有项目/任务”和“普通 shell 窗格”（要定会话和输入记录的语义），后台自启接在打包里做。用时最长，但能得到票里写的体验。
B. 收窄本票：打包成一个双击就能打开的 .app，自动起后台，直接进入一个预先配置好的项目和任务（比如读一份配置文件，或者用上次打开的那个），窗格沿用现有的主控和 worker 启动方式，不做普通 zsh 窗格和选择页。最快能用上，但用户每换一个任务都要改配置。
C. B 先上，同时开 A 的两张票，之后再补上。
另外照实记录：本批 worker 都是以 Fast 启动的（我按本期“允许 Fast、照实记录”执行），s17-t102 在报告里指出这和 AGENTS.md 的“不用 Fast”不一致。如果本期已经不允许 Fast，请告诉我，我以后改用普通速度启动。
T-101 不受影响，照常进行。