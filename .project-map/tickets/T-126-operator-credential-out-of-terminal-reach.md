---
id: T-126
title: 操作员凭据移出终端可见路径，终端改用专用 socket
type: build
status: open
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

- [ ] 真实入口：打包测试版里，项目终端的环境中没有后台数据目录与凭据路径；终端里 `a2a whoami`、`a2a request` 照常工作；界面批准照常工作。
- [ ] 在项目终端里用终端可见的信息调用 `role_request_decide`（专用 socket 加任何终端能拿到的身份）被拒绝并留记录。
- [ ] 界面关掉再开、后台常驻时，界面凭持久化的凭据重新连上。
- [ ] 旧位置凭据迁移后旧文件不存在，新文件为 0600。
- [ ] 修前版本（终端环境导出 `A2A_STATE`）在同一检查上失败。
- [ ] 已知边界写进 README：有意搜索磁盘的 agent 仍可能读到凭据。
- [ ] `project_map.py status` 0 问题。
