---
id: T-038
title: 任务窗口与门禁状态界面
type: build
status: open
blocked_by: [T-036]
claimed_by: s2-t038
supersedes:
---

## What to build

在 Synara 桌面版中按"项目 → 任务 → agent 会话"展开：一个项目下有多个任务，每个任务窗口并排显示属于它的多个 thread，并显示门禁状态（claimed、submitted、verified、accepted 及失败原因）与人工介入标记。先核实 Synara 是否已有 thread 分组；没有就由 a2a 保存任务与 thread 的归属，不改上游 thread 结构。界面对受管任务的操作只调用门禁核心。视觉沿用 Synara 主题与组件。设计见 [spec](../specs/synara-m1-2026-10-07.md) 的"层级模型""界面"。

## Acceptance

- [ ] 隔离数据目录中的桌面版截图或录屏：一个项目下至少两个任务，其中一个任务含至少两个 agent 会话（例如 worker 与 reviewer），并显示门禁状态。
- [x] 门禁状态取自门禁核心的真实状态：经门禁 CLI 推进一个夹具任务时，界面状态随之变化（含一次失败原因）；有截图与对应 CLI 输出。
- [x] 任务与 thread 的归属在重启后保持；上游 thread 表结构未改。
- [x] 上游文件改动清单；`typecheck`、`lint` 通过。
- [x] 外观由用户判断，不在本 ticket 内宣称通过。

## Resolution

INCOMPLETE，待主控关闭。实现已提交至 fork `ad13b72c5faeb5fb601c3d40b7090d746f4f2758`，采用主控批准的独立 membership；不改原生 ProjectTask、thread schema 或 T-037 独占文件。dev Chrome 的真实门禁 CLI 闭环、失败原因、两会话、GUI 保存/CAS 与重启均有 PASS 证据，typecheck/lint/格式检查通过，见 [RESULTS](../../evidence/2026-10-07-synara-batch2/T-038/RESULTS.md)。

按 [决定 05](../../evidence/2026-10-07-synara-batch2/T-038/controller-decision-05.md) 做了基线/候选 CUA 交替三次：两边首轮失败、后两轮通过，不修不稳定上游测试。基线 Electron 同样出现空白，候选根入口可渲染，任务窗口导航的弹窗等待失败；原生桌面任务窗口仍 INCOMPLETE，未勾首项。采用获准 dev Chrome 证据并说明区别，不宣称外观通过。observer 三态与人工介入已有明确标注夹具的有效截图；T-037 合并后的真实复验由主控安排。

冻结候选的 [独立审查](../../evidence/2026-10-07-synara-batch2/T-038/independent-review.md) 返回 INCOMPLETE，有限声明范围内无确认缺陷。按主控补充，审查后用同一候选再次尝试 Electron 任务窗口；导入弹窗点击 Not now 后未关闭，未进入任务窗口，见 [现场、命令与原因](../../evidence/2026-10-07-synara-batch2/T-038/post-review-electron.md)。未改代码，不计 PASS，第一项保持未勾选。
