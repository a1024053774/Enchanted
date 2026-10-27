---
id: T-197
title: 认领时的路径重叠交主控判断；已验收的 attempt 不再占路径
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

决定见 [T-196](T-196-path-judgement-by-controller.md)第 1 条；来源 [findings U11](../../findings/2026-10-27-two-real-uses.md)。

- 重叠时派发返回重叠清单（任务、attempt、文件），说明主控可写 `overlap_reason` 放行或等待；放行理由记入 `claim_path_check` 事件，界面任务页可见。
- 已验收（accepted）或已集成的 attempt 不再计入占用。
- 主控说明（SKILL.md、角色卡、`a2a help`）从“不传 `overlap_reason`”改为“看清单判断，放行必须写理由”。

## Acceptance

- [ ] 红态：同仓库 A 已验收未回收，派 B（路径与 A 重叠）被 `path_overlap` 拒。修后通过，事件记录 A 不计入。
- [ ] 两个进行中的任务重叠：不带理由仍拒并返回清单；带理由通过，理由在事件里。
- [ ] 空字符串或纯空白理由不算理由。

通用：先在真实入口留红态再修根因；独立审查。

## 不做

不在认领时判断语义冲突；真正冲突交给集成时的 Git 合并。

## Resolution
