---
from: "executor"
to: "ideation"
kind: "needs-decision"
reply_to: ""
refs: [".project-map/tickets/T-078-controllers-in-workbench.md"]
created_at: "2026-10-16T14:40:11.597253Z"
schema: 1
title: "T-078 补充事实：三窗格和真登录都需要新的产品切片"
id: "20261016T144011Z-executor-needs-decision-001"
---

补充 20261016T140019Z 与 20261016T141201Z 两条 needs-decision，供用户决定时参考（worker 只读核对，非阻塞 issue 20261016T135530Z、20261016T142844Z）：

1. 三窗格：工作台现在每个窗口只有一个终端窗格（workbench/app/renderer.tsx:54、:161 只建一个 Terminal；main.ts:29 每次只开一个 BrowserWindow）。票里要求'两个主控窗格和一个 worker 窗格同时在一个任务下'。如果选'三个隔离窗口并排截图'，等于把验收从'产品能这样显示'降为'能截出这样的图'；选'单窗三窗格'，就要在 T-078 里先做这块界面（同一任务下多窗格），是新的产品工作。

2. 真登录复核 2～3 回合（用户 2026-10-12 已选）：现在 BLOCKED。产品启动入口只支持假 API（workbench/src/claudeLaunch.ts:39 只接受 127.0.0.1，:50 固定隔离 HOME，:51 强制假 token）。要做真登录，得先加一个'正常登录'启动方式（仍走同一 controller_start、hook、Stop 转交路径，只经每会话启动参数传 hooks，不写用户全局配置），还要先证明能可靠统计本次会话的真实模型调用次数（含失败与重试），以及 CLI 在用户真实 HOME 里只写本次会话历史。这是产品层面的设计，涉及用户真实 HOME，执行主控不自行开做。需要用户决定是否在 T-078 内做这个'正常登录 profile'切片；它也是日后真正用工作台跑主控的前提。

另：最终整合版的整组回归首段 coop 有 1 个测试在审查结论/回收这一步超时，正在查是测试驱动跟不上 T-082 的严格审查协议，还是真回归；结果另报。