---
id: T-190
title: 项目随时可移除；失效项目不拖累其他项目的认领
type: build
status: open
blocked_by: []
claimed_by:
supersedes:
ready: no
ready_by:
ready_rev:
---

## What to build

来源：[findings/2026-10-27-two-real-uses.md](../../findings/2026-10-27-two-real-uses.md)（U01、U02、U03）。决定见 [T-189](T-189-real-use-fixes-decisions.md)第 2 条。

- 移除不再因“有门禁任务”或“有窗格”拒绝；只从列表隐藏，库里任务与记录保留；同一目录再打开时恢复显示。有未回收 attempt 时，界面问“一并回收 / 保留”。
- 认领前的路径冲突检查只比较同一仓库的 attempt，不对其他项目的仓库执行 git；目录不存在的项目在侧栏标“目录不存在”。
- 现场处理：第二次使用时为绕过缺陷新建的 `/private/tmp/a2a-lcu-demo` 空仓库，修复后经用户同意再删。

## Acceptance

- [ ] 反例：某项目的仓库目录被删且有未回收 attempt，另一个项目照常认领成功（修前同场景报 spawn git ENOENT）。
- [ ] 有门禁任务的项目能从列表移除，重新打开同一目录后任务与记录回来。
- [ ] 有未回收 attempt 时移除会询问，选回收则经门禁回收。

通用：先在真实入口留红态再修根因；不写 ~/.claude、~/.codex 等全局配置；独立审查。

## 不做

范围外问题经问题上报。

## Resolution

2026-10-27 进展（INCOMPLETE，未关闭）：用户 2026-10-27 “空仓库删掉”“验收的时候开启 codex 在你侧边栏,用 6.1 terra 模型来执行 computer use 实操测试”。已实现：认领前路径检查跳过已不存在的仓库（`gates/core.ts`）；移除不再受任务约束，运行中终端与未回收 attempt 返回问题由界面询问（`daemon.ts`、`store.removedProjects`、`RemoveProjectDialog`）；重新打开同一目录以原项目号恢复；项目行“目录不存在”。证据：`evidence/2026-10-27-batch28/T-190/`（隔离后台红态 `spawn git ENOENT`、绿态；Codex 第 2 轮界面 1～5 项 PASS）。
未完成：“回收并移除”的真实正例；新版本未装到 /Applications；`/private/tmp/a2a-lcu-demo` 空仓库要等装上新版再删（现在删会让 0.1.5 的认领再次全部失败）。
