---
id: T-117
title: 用户新 Logo 接入应用、GitHub 与 Pages，重新打包发布
type: build
status: open
blocked_by: []
claimed_by: codex-direct
supersedes:
ready: yes
ready_by: executor
ready_rev: 1
---

## What to build

用户于 2026-10-21 提供两张透明 PNG，逐字要求：“你给我的 app 换上新 Logo,深浅都做,然后重新打包,更新 GitHub 以及 pages 上的图标.”

当前工具进程没有 HERDR_ENV=1。向用户明确询问“是否允许我这次直接在仓库里完成修改、验证、打包和发布，跳过 Herdr 派发？”，用户回复“允许”。本票由当前 Codex 直接执行，不派发 worker，不伪造 task/attempt/session/fence 或门禁验收记录。

目标：用户提供的深色标记用于浅色背景，白色标记用于深色背景；应用侧栏、macOS 图标、Pages 品牌与 favicon、GitHub README 一致使用它们。保留原图透明通道与形状，按标准入口打包 0.1.1、安装并发布新 Release，保留 0.1.0。

非目标：T-115 归因、T-116 夹具与版本测试、门禁行为、完整应用浅色主题、公证、全局 CLI 配置、Herdr 会话操作。

修改范围：本票与 T-116 状态记录、`workbench/app/` 品牌与打包入口、版本清单、`workbench/README.md`、`README.md`、`docs/` 品牌、`evidence/2026-10-21-batch19/T-117/`。保留 session 开始时的脏文件。

采用 Ubiquitous language：产品为 Enchanted，编排内核为 a2a。Tracer bullet 先从原图贯通页面与实际应用，再完成发布；不新增浅包装模块，遵循 Deep modules。

## Acceptance

- [ ] 两张原始 PNG 原样入库；应用与 Pages 的深浅色选择能通过真实浏览器／Electron 观察，旧入口被同一检查拒绝，截图和命令保留。
- [ ] Pages 桌面与窄屏、系统主题与手动覆盖正常；现有可点击演示回归通过。
- [ ] 标准打包入口生成 0.1.1，含自定义 icns；codesign 通过；真实启动并验证侧栏和 Dock 外观切换；安装到 `/Applications/Enchanted.app`，不改 bundle id 与用户数据位置。
- [ ] GitHub 首页、Pages 部署与新 Release 在线读回；下载产物与本地字节数一致；发布前扫描没有未豁免凭据。
- [ ] 清理本次成功构建的依赖、中间产物；大块运行证据归档外置盘；`project_map.py status` 无问题、无 stale living doc。

## Resolution

INCOMPLETE：执行中。
