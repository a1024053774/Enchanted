---
id: T-116
title: 原生测试夹具在高负载下不稳定，以及 T-112 合入后 test_t091_claude_version 失效
type: build
status: out-of-scope
blocked_by: []
claimed_by:
supersedes:
ready: no
ready_by: executor
ready_rev: 1
---

## What to build

2026-10-21 用户裁定：本票搁置，不继续 Claude 版本检查相关工作。原始发现与验收条件保留作为历史现场，不代表当前执行授权；重新启动本票须先确认范围。

来源：T-115 的 repeat-02 与独立审查 01（evidence/2026-10-20-batch18/T-115/）。这是执行主控在已批准范围内自建的缺陷级票（T-004）。

1. `workbench/tests/test_t091_claude_version.mjs` 在 main 上失败，报 `Unexpected module boundary: ./executionSettings.ts`：T-112 加了 executionSettings.ts，这个测试的模块边界白名单没有跟着更新，T-112 合并回归时也没有跑到它。要求：按真实的模块依赖更新白名单（不能放宽成接受任意模块），恢复它对 controller_version_mismatch 的变异检查。
2. T-110 真实入口在高负载下的两类夹具不稳定：
   - 某个红态运行结束时，Electron 窗口清理超过 10 秒（window_cleanup_error），导致整次中止；
   - `t110_notifications_scenario.py:37` 读 `before_highlight['agents'][agent_id]` 时 KeyError：agent 在高亮前快照之后才出现在侧栏。
   修测试的完成条件或快照时机，不放宽断言，不在产品里加重试。
3. T-115 的 RUN-OUTSIDE-REPEAT-01.sh 有一处 P2：只要目标文本命中，就判为 REPRODUCED。要改成：时间线分类完整、归到产品路径或测试动作路径时才判 REPRODUCED，否则保持 INCOMPLETE。

## Acceptance

- [x] test_t091_claude_version.mjs 在 main 上 PASS，删掉 controller_version_mismatch 检查的变异仍然被拒。
- [ ] 两类夹具不稳定都有修前红态（可以注入延迟），修后在 T-115 的负载条件下重复运行中不再出现。
- [ ] 重复脚本的判定有用例覆盖（分类不完整时为 INCOMPLETE）。
- [ ] `project_map.py status` 0 问题。

## Resolution

不再做（状态 out-of-scope），2026-10-23。验收条件没有达成，不记为 closed。用户 2026-10-23 逐字：“都关掉吧”（对“T-115、T-116 建议两张都关，不再投入”的回复）。

1. `test_t091_claude_version.mjs`：已由 T-118 解决，不再是问题。T-118 去掉了版本比较，并改写了这个测试。2026-10-23 在 main（`23d4445a2`）上运行：PASS；把版本比较加回去的变异被拒绝（`Updated CLI version must be accepted: controller_version_mismatch`）。
2. T-110 夹具在高负载下的两种不稳定：没有修。它们只是 T-115 的前置工作，随 T-115 一起关闭。`t110_notifications_scenario.py:37` 读高亮前快照的代码还在；以后再用 T-110 真实入口做负载测试时，要先处理这一处。
3. 重复脚本判定太松的问题：没有修，同上。
