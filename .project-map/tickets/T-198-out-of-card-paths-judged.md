---
id: T-198
title: 交付里卡外改动的文件交主控判断，不再直接打回
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

决定见 [T-196](T-196-path-judgement-by-controller.md)第 2 条；来源 [findings U11](../../findings/2026-10-27-two-real-uses.md)。

- 交付检查算出卡外改动的文件，记入 `path_check` 事件，作为待主控判断的一项，不再以 `path_boundary_failed` 结束验收。
- 主控接受时写理由（记入事件）；打回走现有 revise。没有主控判断前不能集成。
- 卡外清单写进独立审查员的输入；任务页显示清单与主控理由。
- 验收文件不被改动（T-080）、Git 元数据守护仍硬拒，不受这一判断影响。

## Acceptance

- [ ] 红态：worker 改了一个卡外文件，现版本验收以 `path_boundary_failed` 结束。修后进入待判断，不带理由集成被拒，写理由后集成成功，理由在事件里。
- [ ] 主控选择打回时，worker 收到清单并可修订。
- [ ] 卡外改动碰到验收文件时仍硬拒（反例）。
- [ ] 审查员的输入里有卡外清单。

通用：先在真实入口留红态再修根因；独立审查。

## 不做

不改任务卡白名单本身的写法；不让 worker 自己放行。

## Resolution
