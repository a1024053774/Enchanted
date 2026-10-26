---
id: T-187
title: 增加 Antigravity（agy）与 opencode 两种原生 CLI 的支持并实测
type: build
status: closed
blocked_by: []
claimed_by:
supersedes:
ready: yes
ready_by: ideation
ready_rev: 2
---

## What to build

用户 2026-10-25 逐字：“1. 查明一下 3.装上钩子  5.发新 release,产品页也更新  新票:增加 antigravity,opencode 的支持吧,按理说应该不限 cli 的,但应该还要实测一下,”

方向扩展（原 T-069 第一版只支持 Claude Code 与 Codex）：用户要求“按理说应该不限 cli 的”。目标：项目终端里用户启动 agy 或 opencode 时，与 Claude/Codex 同样获得包装脚本（a2a 入口与开局说明，按各自 CLI 能力用每会话参数传钩子/指令）、角色申请、状态信号；主控派发 worker/审查员时可选这两种 CLI，设置页按角色可选。各家能力不同的地方（钩子、问答框、恢复）先查文档与 `--help`，记录差异；做不到的照实标出，不伪造状态。CLI 选择不按名字硬编码成白名单之外不可扩展：新增 CLI 的接入点集中在一处。

通用：先留真实入口的红态再修根因；真实 Claude 用 claude-haiku-5-5、尽量少；不写 ~/.claude、~/.codex 等全局配置，钩子只经每会话启动参数；agy 独立审查。

补充（ready_rev 2）：权限决定。用户 2026-10-25 在执行主控 needs-decision（inbox 20261025T150744Z）的选项里选“C 两者都作 worker”，选项原文：“agy 用 --dangerously-skip-permissions 全放开，只靠门禁事后检查；Git 元数据可能被改，每次派发写一次 ~/.gemini”。据此：
- agy、opencode 都可作 worker 与审查员。agy 以 `--dangerously-skip-permissions` 启动；opencode 也按会话放开到能无人值守完成任务。门禁照常做路径边界、验收文件不变、独立审查与提交尾注检查，并核对 worktree 的 Git 元数据（HEAD、refs、config、hooks）在交付前后没有被 worker 改动，被改动则拒绝交付。
- 这是 AGENTS.md“不写全局配置”的一项用户批准例外：agy 每个新 worktree 的信任确认会写入用户 ~/.gemini；只允许写 trustedWorkspaces 这一项，由后台在 worker 启动前以 agy 自身的信任流程完成（不靠盲按回车），不写其他键。完成报告列出写入条数。
- 审查员仍须只读：给 agy/opencode 审查员的会话用文件权限（chmod）保证只读，与现有 agy 审查员做法一致。
- 用户选择保留探针误写的 /private/tmp/t187-probe/repo 信任项，不删。

## Acceptance

- [x] Git 元数据守护：反例中 worker 改动 worktree 的 HEAD/refs/hooks，门禁拒绝交付；正例通过。

- [x] 真实 agy 与真实 opencode 各走一遍：项目终端启动 → 申请主控 → 批准 → 派一张卡给另一种 CLI 的 worker → 独立审查 → 门禁集成；各留截图与运行记录。
- [x] 两种 CLI 作 worker 时状态（运行中/空闲/等回答）在侧栏正确；做不到的信号在界面上显示“未知”而不是猜。
- [x] AGENTS.md 与 workbench/README 的支持范围同步更新。

## 不做

范围外问题经问题上报。

## Resolution

2026-10-25 PASS，证据 `evidence/2026-10-25-batch26/T-187/RESULTS.md`，独立审查第五轮 `T-187 REVIEW PASS`。真实运行：opencode 主控 → agy worker 与 agy 主控 → opencode worker 都走完申请、批准、派发、交付、独立审查、集成。实跑暴露并修掉两处：agy 主控没有开局说明（包装脚本 `--add-dir` 开局说明目录）；opencode 首次 idle 时还不收输入（等光标显示再派发）。agy 主控须以 `agy --dangerously-skip-permissions` 启动（用户选定）。agy 信任写入用户 `~/.gemini` 共 2 条（只 `trustedWorkspaces`）。
