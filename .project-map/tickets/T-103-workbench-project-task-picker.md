---
id: T-103
title: 工作台界面：列出并切换项目与任务（项目/任务选择页）
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

来源：T-102 的 needs-decision（收件箱 `20261019T044703Z-executor-needs-decision-001`）。用户 2026-10-19 逐字选项："A 先补功能再打包"。

现状（执行主控核对过源码）：界面只显示启动时指定的那个 task（`workbench/app/renderer.tsx:211-230`）；preload 没有列举或切换项目、任务的 IPC（`preload.ts:9`）；门禁命令表里也没有列项目或任务的入口（`gates/cli.ts:15`、`core.ts:3188-3191`）。

按 tracer bullet 做一条薄切片，贯穿存储 → 编排后台命令 → IPC → 界面：

1. 编排后台加两个只读命令：列出项目、列出某项目下的任务（含门禁 task id、状态）。数据来自后台已有的 SQLite 库，不另存一份；不改门禁语义，只读，不走认领/验收路径。
2. preload 暴露这两个调用；界面左侧"项目 → 任务"列表，选中任务后切换到该任务的窗格视图（沿用现有窗格渲染）。界面按 spec 的"项目 → 任务 → 会话"组织。
3. 不带 `--task` 启动时默认进入选择页，不再退出；带 `--task` 的现有行为保持。
4. 创建项目、创建任务不在本票（只列现有）；库里没有任何项目时显示空状态和提示，不报错。
5. 界面文案用中文，走 `frontend-production` 里去 AI 味的要求。

## Acceptance

- [x] 红态：当前不带 `--task` 退出，界面无列表。绿态：真实 Electron + 真实后台，库里有 ≥2 个项目、每项目 ≥2 个任务的夹具，列表与库一致，切换任务后窗格内容跟着变。
- [x] 反例：库为空显示空状态；当前库中任务不存在时，刷新后不再出现；列表命令不改库（前后库字节不变）。
- [x] 真实入口截图加复现命令入证据。
- [x] 不动门禁入口与操作锁语义；`project_map.py status` 0 问题。

## 不做

不做创建/删除项目与任务；不做搜索；不改窗格托管逻辑。

## 裁定（2026-10-19，验收口径）

执行主控 needs-decision（收件箱 `20261019T071357Z-executor-needs-decision-001`）：原反例"任务被门禁移除后刷新不再出现"写错，门禁没有移除任务的入口（revoke 只撤回执行）。用户选项逐字："A 改口径,接受现有证据 (Recommended)"，选项原文："改成“当前库中任务不存在时,刷新后不再出现”。产品审查无缺陷、三个变异都被拒、真实端到端 9 项 PASS,可直接合入。"

## Resolution

2026-10-19，执行主控。PASS。exec/t103 以 `--no-ff` 合入 main（883a449f0），没有 push。

- 候选 1acfeccf8（worker s17-t103）。新增两个只读命令：列项目、列任务；4 个窗口级 IPC；左侧“项目 → 任务”列表。不带 `--task` 启动时进入选择页，带 `--task` 时保持原行为。
- 真实 Electron 加真实后台：9 项 PASS，证据 `evidence/2026-10-19-batch17/T-103/run-20261019T063741Z-summary.json`，截图在外置盘同名 run 目录。覆盖：
  - 已知坏版本的三项红态；
  - 两个项目、四个任务的列表与库一致，跨项目往返和键盘切换后窗格跟着变；
  - 空库显示空状态；任务从当前库移除后，刷新即不再出现（按裁定 A）；
  - 列表命令不改库：库与 WAL 字节完全一致；
  - 显式 `--task` 启动保持原行为。
- 合同测试：test_t091_pane_ipc.mjs 和 test_electron_e2e.py 的 window_contract 从写死数量改为显式名称集合。历史基线保留原合同；原有拒绝检查没有削弱。四组 PASS（contracts-20261019T065323Z-summary.json）。合入后在 main 上重跑 test_t091_pane_ipc.mjs，结果 PASS。
- 独立审查 01（s17-t103-r1）：没有发现产品缺陷，三个单处变异都被拒绝；审查补充的沙箱外复验 PASS。唯一缺口是“经门禁移除”的口径，已由用户裁定 A 关闭。
- 环境限制（已写入 workbench/README）：
  - npm ci 装出的 node-pty spawn-helper 缺执行位，按 README:319 手工改为 755；
  - Electron 43 不再在安装时下载程序，需要显式安装；
  - 外置盘（USB APFS）上的 Electron 二进制会挂起，Electron 必须从内置盘运行。
- 后续：T-104 第二段要解决与本票在 daemon.ts、gates/cli.ts 上的合并冲突。
