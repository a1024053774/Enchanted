---
id: T-187
title: 增加 Antigravity（agy）与 opencode 两种原生 CLI 的支持并实测
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

用户 2026-10-25 逐字：“1. 查明一下 3.装上钩子  5.发新 release,产品页也更新  新票:增加 antigravity,opencode 的支持吧,按理说应该不限 cli 的,但应该还要实测一下,”

方向扩展（原 T-069 第一版只支持 Claude Code 与 Codex）：用户要求“按理说应该不限 cli 的”。目标：项目终端里用户启动 agy 或 opencode 时，与 Claude/Codex 同样获得包装脚本（a2a 入口与开局说明，按各自 CLI 能力用每会话参数传钩子/指令）、角色申请、状态信号；主控派发 worker/审查员时可选这两种 CLI，设置页按角色可选。各家能力不同的地方（钩子、问答框、恢复）先查文档与 `--help`，记录差异；做不到的照实标出，不伪造状态。CLI 选择不按名字硬编码成白名单之外不可扩展：新增 CLI 的接入点集中在一处。

通用：先留真实入口的红态再修根因；真实 Claude 用 claude-haiku-5-5、尽量少；不写 ~/.claude、~/.codex 等全局配置，钩子只经每会话启动参数；agy 独立审查。

## Acceptance

- [ ] 真实 agy 与真实 opencode 各走一遍：项目终端启动 → 申请主控 → 批准 → 派一张卡给另一种 CLI 的 worker → 独立审查 → 门禁集成；各留截图与运行记录。
- [ ] 两种 CLI 作 worker 时状态（运行中/空闲/等回答）在侧栏正确；做不到的信号在界面上显示“未知”而不是猜。
- [ ] AGENTS.md 与 workbench/README 的支持范围同步更新。

## 不做

范围外问题经问题上报。
