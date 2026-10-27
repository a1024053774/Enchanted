---
id: T-191
title: 侧栏按 CLI 显示图标与名称；agy、opencode worker 状态取回合信号
type: build
status: closed
blocked_by: []
claimed_by:
supersedes:
ready: no
ready_by:
ready_rev:
---

## What to build

来源：[findings/2026-10-27-two-real-uses.md](../../findings/2026-10-27-two-real-uses.md)（U04、U05、U09）。决定见 [T-189](T-189-real-use-fixes-decisions.md)。

- 每个 agent 行前显示所属 CLI 的图标（Claude Code、Codex、agy、opencode），标签不再把后两家写成“未知”；CLI 识别集中在 `terminalClis` 一处。
- worker、审查员的状态对 agy、opencode 取 OSC 7501 回合信号（与主控一致），不再只看窗格是否存活。图标来源与许可在 README 写明。

## Acceptance

- [x] 四种 CLI 的 worker 在侧栏各显示正确图标与名称。
- [x] agy worker 交付后回到空闲时侧栏显示空闲（修前同场景一直转圈）。

通用：先在真实入口留红态再修根因；不写 ~/.claude、~/.codex 等全局配置；独立审查。

## 不做

范围外问题经问题上报。

## Resolution

2026-10-27 进展（INCOMPLETE，未关闭）：用户 2026-10-27 “我刚刚新建了终端,还没开 agent 任务这个状态就动起来了,我我想要这个状态是监控 agent 状态的. 还有要加上对应 agent 的 logo”。已实现：普通终端状态取前台 CLI（无 CLI 为空闲，agy/opencode 取 OSC 7501，Claude/Codex 获批角色前未知）；四家 CLI 图标（LobeHub，MIT）；受管会话 CLI 名取启动记录；终端行副标题只显示 CLI 名。U05 更正为非缺陷（见 findings）。证据：`evidence/2026-10-27-batch28/T-190/ui-check-round2`、`ui-check-round3`。
未验证：普通终端里 agy/opencode 回合进行中转圈、结束回到空闲（第 3 轮 opencode 无可用模型，BLOCKED）。

2026-10-27 关闭：第 4 轮四家 CLI worker 图标与名称 PASS，agy、opencode worker 交付后空闲 PASS；普通终端 agy、opencode 回合 running → idle 经后台探针与界面截图确认。证据见 [T-190 RESULTS.md](../../evidence/2026-10-27-batch28/T-190/RESULTS.md) 第 4 轮。
