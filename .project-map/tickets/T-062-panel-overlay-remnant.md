---
id: T-062
title: 修复任务窗口里残留的浮层，它盖住问题上报面板的标题
type: build
status: open
blocked_by: []
claimed_by:
supersedes:
ready: yes
ready_by: ideation
ready_rev: 1
---

## What to build

T-055 的面板截图（`evidence/2026-10-09-batch8/T-055/round4/panel-final-*.png`）左上有一个浮层，像新手导览的残留，盖住了"问题上报"标题的一部分。查明它是产品缺陷还是隔离 dev 环境才有的导览，是产品缺陷就修；是环境问题则说明依据并让验收截图不再带它。用户要求修复："浮层这个要修复"。

## Acceptance

- [ ] 复现并查明来源（产品还是 dev 环境），保存证据与重放命令。
- [ ] 修复后任务窗口里该浮层不再遮挡面板标题；真实 dev UI 截图（含有问题上报时）作证，外观由用户判断。
- [ ] 若是产品缺陷：先红后绿的界面用例；既有套件、typecheck、lint 通过，上游文件改动列清单。

## 说明

- 授权来源：用户 2026-10-09 说"浮层这个要修复"；与 T-057 同改任务窗口时，同一文件同一时间只能有一个写入者，由执行主控安排。

## Resolution
