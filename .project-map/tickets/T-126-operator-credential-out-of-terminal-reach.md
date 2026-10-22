---
id: T-126
title: 操作员凭据移出终端可见路径，终端改用专用 socket
type: build
status: closed
blocked_by: [T-125]
claimed_by:
supersedes:
ready: yes
ready_by: executor
ready_rev: 1
---

## What to build

来源：[T-125](T-125-operator-credential-storage.md) 用户选 A（逐字：“T-121 选 A”）。

- 操作员凭据持久化为 `~/Library/Application Support/Enchanted/` 下的 0600 文件（测试版、隔离数据目录各用自己的位置），不放在后台数据目录里。
- 编排后台另开一个只接受终端身份的 socket；项目终端的环境里只有这个 socket 路径和终端令牌，不再导出 `A2A_STATE`，也不出现后台数据目录。
- 专用 socket 上，操作员命令和窗口命令一律拒绝；原 socket 不变。
- 现有安装迁移：旧位置的凭据移到新位置，旧文件删除。

## Acceptance

- [x] 真实入口：打包测试版里，项目终端的环境中没有后台数据目录与凭据路径；终端里 `a2a whoami`、`a2a request` 照常工作；界面批准照常工作。
- [x] 在项目终端里用终端可见的信息调用 `role_request_decide`（专用 socket 加任何终端能拿到的身份）被拒绝并留记录。
- [x] 界面关掉再开、后台常驻时，界面凭持久化的凭据重新连上。
- [x] 旧位置凭据迁移后旧文件不存在，新文件为 0600。
- [x] 修前版本（终端环境导出 `A2A_STATE`）在同一检查上失败。
- [x] 已知边界写进 README：有意搜索磁盘的 agent 仍可能读到凭据。
- [x] `project_map.py status` 0 问题。

## Resolution

2026-10-22 PASS，最终候选 87453d496（README 补充 ce05e1b4）。项目终端经后台另开、只接受终端身份的专用 socket 连接（`A2A_TERMINAL_SOCKET`），环境里不再有 `A2A_STATE`、数据目录与凭据路径；非终端身份在核对身份前即被拒绝并记录（`socket: "terminal"`），原 `control.sock` 不变。桌面应用的操作员凭据移到 `~/Library/Application Support/<产品名>/`（显式 `--state` 时为 `<数据目录>-credentials/`），已有安装启动时迁移，旧文件删除，新文件 0600。证据：打包测试版三阶段运行 23 项通过（修前版本泄漏数据目录 → 迁移并重连运行中的旧后台 → 终端命令、界面批准、终端自批被拒并有记录、关开界面重连）；源码端到端与单元各有修前版本或变异的红态。见 [候选 1 RESULTS](../../evidence/2026-10-22-batch20/T-126/candidate-1/RESULTS.md)、[候选 2 RESULTS](../../evidence/2026-10-22-batch20/T-126/candidate-2/RESULTS.md)。独立审查：候选 1 由 agy（gemini-3.8-flash-high）审出一条 P2、两条 P3，修了 P2（启动失败时清理临时 socket 目录），两条 P3 有理由不改（`candidate-2/review-01-disposition.md`）；候选 2 复审 PASS，无发现（`candidate-2/review-02.md`）。已知边界写进 README：有意搜索磁盘的 agent 仍可能读到凭据；受管 worker 与 controller 的环境仍有 `A2A_STATE`（数据目录里已无操作员凭据）。
