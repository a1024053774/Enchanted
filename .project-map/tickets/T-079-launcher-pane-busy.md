---
id: T-079
title: scripts/launch-worker 偶发 agent_pane_busy：等 shell 就绪再启动 agent
type: build
status: closed
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

- [x] 先取红态：在当前入口上重复启动，复现出 `agent_pane_busy`，保存失败记录与现场；如果复现不出来，就如实报告复现了几次、各条件是什么。
- [x] 修复后，用同样次数的启动全部成功，启动记录仍然完整（同 T-073 的字段和尾注）。
- [x] 不加盲目重试。等待只能依据 herdr 提供的结构化状态，并且有上限；超出上限按失败记录，不重试。
- [x] 不改用户的 Herdr server 和全局配置；只关自己创建的 pane。

## 说明

- 只改 `scripts/launch-worker` 及其测试，和 T-076～T-078 的文件不重叠，可以并行。
- 授权来源：assign `20261011T101846Z-ideation-assign-001` 中“launcher 偶发 agent_pane_busy（020752Z）请按 T-004 边界自建缺陷票”；用户原话见该条目的“## 授权”。`ready_by: executor`。

## Resolution

2026-10-11，T-079-1 worker `s13-t079`：**PASS，待主控关闭**。ticket 保持 open，`ready_rev: 1`，起点 `ffe7ecb85e9e224d5917183b48754f15ac0c5ba6`。执行主控取得真实红态 10 次里 2 次 agent_pane_busy，以及代码候选 `8ab5177d09dcb25f57a50ad2166dc0006ea99ce3` 的绿态 10/10 started、busy=0；记录完整，所有自建 pane 关闭及隔离 home 删除有证据。修复采用 split 环境与 30 秒有界结构化等待，只调用一次 agent start；提交与夹具 worker 提交均带齐 9 项尾注。主控批准的夹具候选 `d8446fc982aed0309e7d4892760cbe4e69b694eb` 只改批准的环境与 process-info 夹具；逐 hunk 与源码比对证明业务断言原文、launcher 不变。`tests-20261011T110739Z-8b3a1a` 中旧套 7/7、新套 6/6 通过，起点反事实 1/1 按预期失败，无环境错误；当前交付源码与归档一致。红态外层工具退出 1 已查明为主控追加的 zsh 空 glob 检查，原始调用与独立复现保留。收尾地图复查为 0 problems、0 stale，退出 0；此前并行 T-076 导致的临时 stale 失败与 issue `20261011T111416Z-worker:s13-t079-issue-001` 保留交主控处置，本 worker 未修改 workbench 或地图。S 级 diff 审查与最终关闭交执行主控。证据与重放命令见 [RESULTS.md](../../evidence/2026-10-11-batch13/T-079/RESULTS.md)。

**执行主控关闭（2026-10-11）：PASS。** 交付提交为 a2a `8ab5177d`（修复）、`d8446fc9`（适配旧测试夹具）、`00fc3b71`（证据），三个提交都带 9 项尾注。

执行主控核对的内容：
- 红态和绿态都由执行主控在沙箱外运行。改前启动 10 次，有 2 次报 agent_pane_busy；改后启动 10 次，全部成功。证据在 `T-079/red-*`、`green-*`。
- 修复 diff 已审过，做法如下：
  - 环境变量改用 `pane split --env` 传入，去掉了原来的 export 步骤；
  - 用 herdr 的结构化接口 `pane process-info` 判断 shell 是否就绪，最多等 30 秒，不重试。
- T-073 的旧测试只改了假 Herdr 和环境读取，逐 hunk 核对，业务断言没有改动。
- 沙箱外运行 `tests-20261011T110739Z-8b3a1a`：T-073 旧套件 7/7 通过，新套件 6/6 通过，用起点版本做反事实 1/1 按预期失败。
- 证据合计 0.74 MB，没有超过 5 MB 的单个文件。
- 本卡是 S 级，没有另开独立审查，由执行主控审 diff。

已打分。
