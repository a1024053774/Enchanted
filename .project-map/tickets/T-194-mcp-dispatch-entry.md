---
id: T-194
title: MCP 派发入口，a2a 命令兜底
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

来源：[findings/2026-10-27-two-real-uses.md](../../findings/2026-10-27-two-real-uses.md)。决定见 [T-189](T-189-real-use-fixes-decisions.md)第 3 条。

- 先实测：Claude Code、Codex、agy、opencode 能否按会话（启动参数，不写全局配置）挂上 MCP 服务器；结果写进 findings。
- 后台提供 MCP 工具：申请角色、建卡、派发、查状态、验收与打分；参数有结构。工具实现调用同一个门禁入口，不复制门禁逻辑。
- 接不上 MCP 的 CLI 继续用 `a2a` 命令；两条入口的结果一致。

## Acceptance

- [x] 四家 CLI 的 MCP 支持实测记录。
- [x] 至少一家经 MCP 走通：申请主控 → 建卡 → 派发 → 交付 → 审查 → 集成。
- [x] 同一操作经 MCP 与经 a2a 命令，门禁记录一致。

通用：先在真实入口留红态再修根因；不写 ~/.claude、~/.codex 等全局配置；独立审查。

## 不做

范围外问题经问题上报。

## Resolution

2026-10-27 PASS。`a2a mcp <cli>` 是 stdio MCP 服务器，工具与 `a2a` 命令同一组、经同一终端身份与门禁入口；Claude Code 经插件、Codex 经包装脚本的 `-c`、opencode 经 `OPENCODE_CONFIG_CONTENT` 按会话挂上，不写全局配置；agy 1.4.8 交互模式拿不到工作区 MCP 工具，继续用 `a2a` 命令。会话结束（输入关闭或输出不再被读）时撤回待批的角色申请、中止在途调用、不再写回包。实测见 [findings](../../findings/2026-10-27-mcp-per-session.zh-CN.md)；真实 Claude Code 经 MCP 走通申请主控到集成并与 `a2a` 命令比较全部门禁事件（25 个反例被拒），真实 Codex、opencode 走通申请与拒绝；红态、变异与生命周期测试，独立审查 8 轮（Codex 6 轮、agy 2 轮，前 6 轮的问题已修，第 7 轮的 P3 已修，第 8 轮无发现），见 [RESULTS](../../evidence/2026-10-27-batch28/T-194/RESULTS.md)。
