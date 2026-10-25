---
id: T-183
title: 不带 branch 的 create 被门禁拒绝时，后台新建的工作分支留在仓库里
type: build
status: open
blocked_by: []
claimed_by:
supersedes:
ready: yes
ready_by: executor
ready_rev: 1
---

## What to build

来源：T-181 真实 haiku 复跑（`evidence/2026-10-25-batch25/T-181/RESULTS.md`“发现的范围外问题”）。T-180 的缺陷级修补，执行主控按 T-004 边界自建。

现象：主控第一条命令里卡保存被拒、create 随之失败，但后台在门禁拒绝前已经新建了 `enchanted/demo`；第二次 create 收到 `reason: existing`，主控据此告诉用户“沿用已有分支（没有新建）”，与事实不符。

目标：不带 branch 的 create 失败时，本次调用新建的工作分支不留下（只在它仍指向新建时的提交时删除），下一次成功的 create 如实报告 `created: true`。

## Acceptance

- [ ] 真实后台：不带 branch、卡版本不存在的 create 被拒后，仓库里没有新分支；之后正常 create 回执 `created: true, reason: default`。
- [ ] T-180 原有场景不回归。

## 不做

不改门禁 create 的校验；用户指定 branch 的路径不变。
