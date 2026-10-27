---
id: T-194
title: MCP 派发入口，a2a 命令兜底
type: build
status: open
blocked_by: []
claimed_by:
supersedes:
ready: no
ready_by:
ready_rev:
---

## What to build

来源：[findings/2026-10-27-two-real-uses.md](../../findings/2026-10-27-two-real-uses.md)。决定见 [T-189](T-189-real-use-fixes-decisions.md)第 3 条。

- 先实测：Claude Code、Codex、agy、opencode 能否按会话（启动参数，不写全局配置）挂上 MCP 服务器；结果写进 findings。
- 后台提供 MCP 工具：申请角色、建卡、派发、查状态、验收与打分；参数有结构。工具实现调用同一个门禁入口，不复制门禁逻辑。
- 接不上 MCP 的 CLI 继续用 `a2a` 命令；两条入口的结果一致。

## Acceptance

- [ ] 四家 CLI 的 MCP 支持实测记录。
- [ ] 至少一家经 MCP 走通：申请主控 → 建卡 → 派发 → 交付 → 审查 → 集成。
- [ ] 同一操作经 MCP 与经 a2a 命令，门禁记录一致。

通用：先在真实入口留红态再修根因；不写 ~/.claude、~/.codex 等全局配置；独立审查。

## 不做

范围外问题经问题上报。

## Resolution
