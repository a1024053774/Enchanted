---
id: T-180
title: L07：首次派发默认新建 enchanted/xxx 工作分支，前缀可在设置里改
type: build
status: closed
blocked_by: []
claimed_by:
supersedes:
ready: yes
ready_by: ideation
ready_rev: 1
---

## What to build

来源：findings/2026-10-25-lcu-real-use.md；用户 2026-10-24 逐字：“然后你再用 lcu 测试一下软件看看能不能发现其他问题”。

用户 2026-10-25 逐字：“新建 enchanted/xxx,这个分支前缀在设置里也要能改”。目标：用户没有指定工作分支时，主控派发自动从当前分支新建 `enchanted/<名称>` 工作分支并告知用户（名称规则由你定、写明），不再停下来问；用户指定了就用用户的；不动 main/master，不 push。设置页新增“工作分支前缀”（默认 `enchanted/`），改后对新任务生效。门禁仍校验工作分支合法。

通用：先在真实 Electron 隔离实例复现并留红态，再修根因；真实 Claude 用 claude-haiku-5-5；不加重试掩盖未知；不用正则判断意图；agy 独立审查。

## Acceptance

- [x] 真实 Electron：不指定分支时首次派发直接成功，分支名为 enchanted/…；改设置前缀后新任务用新前缀。
- [x] 用户指定分支时照用；主分支不被改动。

## 不做

范围外的问题经问题上报，不顺手改。

## Resolution

2026-10-25，PASS。记录见 [RESULTS.md](../../evidence/2026-10-25-batch25/T-180/RESULTS.md)。主控建任务不写 branch 时，后台定工作分支：本仓库已有任务就沿用；否则用“前缀 + 项目名”（默认 enchanted/，如 enchanted/demo），同名分支已存在直接用，不存在就从当前 HEAD 新建；不动 main、不切换、不 push；回执 work_branch 写明分支名与是否新建，skill 要求主控转告用户。用户指定 branch 照用，门禁照旧校验。设置页新增“工作分支前缀”，非法前缀不保存；改前缀只影响之后还没有任务的项目（门禁一个仓库一个工作分支）。红态复现 L07，修后两次 PASS 13/13，两个变异被拒，T-131 回归 PASS；agy 审查 PASS（P2：沿用旧同名分支的取舍已记录）；合并后复跑 PASS。真实模型下主控是否不再停下来问，未在本票验证。
