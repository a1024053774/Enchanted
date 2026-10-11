---
id: T-079
title: scripts/launch-worker 偶发 agent_pane_busy：等 shell 就绪再启动 agent
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

执行主控按 T-004 的边界自建的缺陷票。问题上报见 `20261011T020752Z-executor-issue-001`，构思主控在 assign `20261011T101846Z` 里要求自建。

现象：`scripts/launch-worker` 在新 pane 里先用 `herdr pane run` 写入 `export ...`，紧接着调用 `herdr agent start`，有时会被拒，报 `agent_pane_busy`（"agent target pane is not an available shell"）。batch12 的 5 次启动里出现了 2 次。目前的绕法是关掉 pane 再启动一次。执行主控观察到：`herdr pane split` 支持 `--env KEY=VALUE`，可以省掉 export 这一步；新 shell 本身也需要一两秒才能就绪。

## Acceptance

- [ ] 先取红态：在当前入口上重复启动，复现出 `agent_pane_busy`，保存失败记录与现场；如果复现不出来，就如实报告复现了几次、各条件是什么。
- [ ] 修复后，用同样次数的启动全部成功，启动记录仍然完整（同 T-073 的字段和尾注）。
- [ ] 不加盲目重试。等待只能依据 herdr 提供的结构化状态，并且有上限；超出上限按失败记录，不重试。
- [ ] 不改用户的 Herdr server 和全局配置；只关自己创建的 pane。

## 说明

- 只改 `scripts/launch-worker` 及其测试，和 T-076～T-078 的文件不重叠，可以并行。
- 授权来源：assign `20261011T101846Z-ideation-assign-001` 中“launcher 偶发 agent_pane_busy（020752Z）请按 T-004 边界自建缺陷票”；用户原话见该条目的“## 授权”。`ready_by: executor`。

## Resolution
