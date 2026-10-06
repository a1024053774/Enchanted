# Spec: Herdr A2A 确定性协作实验（2026-10-05）

## Problem

当前 Herdr 多 Agent coding 工作流把一部分协作协议交给模型记忆。模型忘记 skill、会话恢复或终端状态含义不明确时，旧会话或未验收结果可能被误认为有效交付，主控还要承担大量转述和补救。

## Solution

围绕 Herdr 建立受管理的 Codex 实验闭环：主控在批准范围内分派和回收 worker；worker 只处理 task/attempt；只读 monitor 记录运行轨迹；claim、submit、acceptance 和 integration 由外部状态和门禁校验。首轮只收集探索性基线和失败证据，不把一次运行当成可靠性提升证明。

## Decisions

- [T-001 Goal and destination](../tickets/T-001-goal-and-destination.md)
- [T-002 First experiment contract](../tickets/T-002-first-experiment-contract.md)
- [T-003 Roles and evidence](../tickets/T-003-roles-and-evidence.md)
- [T-004 Major-decision stop boundary](../tickets/T-004-major-decision-stop-boundary.md)

## Test seam

候选最高 seam 是真实 Herdr agent 入口：通过受管理的 Codex prompt/生命周期读取产生 task/attempt 轨迹，再用独立验收命令核对明确代码版本和结果。首个代表性 task、确切 Herdr CLI/API 命令和独立 oracle 尚未从当前现场确认，由 [T-005 First seam and baseline](../tickets/T-005-first-seam-and-baseline.md) 先做只读研究；在它关闭前不切实现 ticket。

## First experiment contract

- 输入：一个中等难度、可独立验收的当前 coding task，以及固定的起始版本和环境清单。
- 观察：controller、worker、monitor 的模型/CLI/Herdr/skill 版本，task/attempt/claim/submit/验收/integration 事件，人工介入和失败。
- 负例：旧 session、过期规格、未通过验收或无法核对的候选。
- 期望：负例被拒绝并进入可诊断、可恢复的暂停；终端 `idle`/`done` 或自然语言“完成”不能单独通过。
- 结论：仅报告基线事实和失败证据；收益或可靠性提升需要后续独立对照实验。

## Out of scope

- 第二 CLI 的互操作验证；
- 通用 A2A 平台、多机调度和生产部署；
- 自动解决语义冲突或自动批准不可逆外部操作；
- 未经证据证明必要的 Herdr 核心分叉。
