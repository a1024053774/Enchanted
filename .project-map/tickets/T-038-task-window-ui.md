---
id: T-038
title: 任务窗口与门禁状态界面
type: build
status: closed
blocked_by: [T-036]
claimed_by: s2-t038
supersedes:
---

## What to build

在 Synara 桌面版中按"项目 → 任务 → agent 会话"展开：一个项目下有多个任务，每个任务窗口并排显示属于它的多个 thread，并显示门禁状态（claimed、submitted、verified、accepted 及失败原因）与人工介入标记。先核实 Synara 是否已有 thread 分组；没有就由 a2a 保存任务与 thread 的归属，不改上游 thread 结构。界面对受管任务的操作只调用门禁核心。视觉沿用 Synara 主题与组件。设计见 [spec](../specs/synara-m1-2026-10-07.md) 的"层级模型""界面"。

## Acceptance

- 原第 1 项（隔离数据目录中的桌面版截图或录屏：一个项目下至少两个任务，其中一个任务含至少两个 agent 会话，并显示门禁状态）未达成，2026-10-08 由主控移交 [T-042](T-042-desktop-task-window.md)，见 Resolution；不计入本 ticket 的通过。
- [x] 门禁状态取自门禁核心的真实状态：经门禁 CLI 推进一个夹具任务时，界面状态随之变化（含一次失败原因）；有截图与对应 CLI 输出。
- [x] 任务与 thread 的归属在重启后保持；上游 thread 表结构未改。
- [x] 上游文件改动清单；`typecheck`、`lint` 通过。
- [x] 外观由用户判断，不在本 ticket 内宣称通过。

## Resolution

INCOMPLETE，待主控关闭。实现已提交至 fork `ad13b72c5faeb5fb601c3d40b7090d746f4f2758`，采用主控批准的独立 membership；不改原生 ProjectTask、thread schema 或 T-037 独占文件。dev Chrome 的真实门禁 CLI 闭环、失败原因、两会话、GUI 保存/CAS 与重启均有 PASS 证据，typecheck/lint/格式检查通过，见 [RESULTS](../../evidence/2026-10-07-synara-batch2/T-038/RESULTS.md)。

按 [决定 05](../../evidence/2026-10-07-synara-batch2/T-038/controller-decision-05.md) 做了基线/候选 CUA 交替三次：两边首轮失败、后两轮通过，不修不稳定上游测试。基线 Electron 同样出现空白，候选根入口可渲染，任务窗口导航的弹窗等待失败；原生桌面任务窗口仍 INCOMPLETE，未勾首项。采用获准 dev Chrome 证据并说明区别，不宣称外观通过。observer 三态与人工介入已有明确标注夹具的有效截图；T-037 合并后的真实复验由主控安排。

冻结候选的 [独立审查](../../evidence/2026-10-07-synara-batch2/T-038/independent-review.md) 返回 INCOMPLETE，有限声明范围内无确认缺陷。按主控补充，审查后用同一候选再次尝试 Electron 任务窗口；导入弹窗点击 Not now 后未关闭，未进入任务窗口，见 [现场、命令与原因](../../evidence/2026-10-07-synara-batch2/T-038/post-review-electron.md)。未改代码，不计 PASS，第一项保持未勾选。

决定 06 的 [一轮有限复验](../../evidence/2026-10-07-synara-batch2/T-038/round6/RESULTS.md) 已完成：dev Chrome 两边未复现 `_nonReactive`，候选任务窗口入口可用；Electron 直接导航仍未完成加载，记录 WebSocket 帧头异常与连接拒绝。未改代码，第一项仍未通过，保持 INCOMPLETE；按主控要求本轮结束即交接。

**主控关闭（2026-10-08，Claude Code）：第 2–5 项 PASS，第 1 项未达成，转入 [T-042](T-042-desktop-task-window.md)。** fork 分支 `a2a-t038` 的 `ad13b72`，证据 `bd967be`。主控核对：独立 membership 以门禁 task id 为身份，不碰原生 ProjectTask 与 thread 表（51 列前后一致）；dev Chrome 中真实门禁 CLI 闭环的五个状态与 oracle 失败原因有截图；表单 type=button 缺陷与并列会话 Loading 均先红后绿；observer 三态与人工介入只用明确标注的协议夹具，未冒称真实订阅。CUA 用例经基线/候选交替各 3 次两边同样不稳定，记为上游；Electron 基线同样空白，候选根页面可渲染但任务窗口在隔离 Electron 中未能到达（导入弹窗不关闭、直达 /a2a 时 WS 帧头异常与连接被拒绝），原因未定。`a2a-t038` 尚未合入 `a2a`：须等 T-039 交接后由主控合并，并在合并后复验 observer 与人工介入的真实显示（T-042）。基线 worktree `~/Documents/Code/synara-t038-baseline` 于 2026-10-08 因内置盘空间不足由主控删除（基线为 `a9cc30c`，可随时重建）。
