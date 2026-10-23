---
from: "executor"
to: "ideation"
kind: "needs-decision"
reply_to: ""
refs: [".project-map/tickets/T-141-loosen-managed-limits.md", ".project-map/inbox/20261023T123914Z-worker:b23-t141-issue-001.md"]
created_at: "2026-10-23T12:47:30.163448Z"
schema: 1
title: "T-141：用户 MCP 服务的文件写入不受 worktree 沙箱约束，与“文件写入范围当硬边界”冲突"
id: "20261023T124730Z-executor-needs-decision-001"
---

状态：T-141 仍在进行（INCOMPLETE），本条不阻塞其余部分。

事实（T-141 worker 上报，引 https://code.claude.com/docs/en/sandboxing “What runs outside the sandbox”）：Claude Code 的文件沙箱只约束原生文件工具和 Bash；MCP 服务是独立进程，它们能写哪里取决于服务自身。去掉 `--strict-mcp-config` 后，worker 会加载用户 Claude 里配置的 MCP，这些服务的写入不受 worktree / 请求目录 / 额外目录的边界约束。

冲突：用户原话（T-141 ticket 第 16 行）“4. 网络全开,去掉--strict-mcp-config,codex 和用户自己的一致,文件写入范围当硬边界”。两项同时成立时，“唯一硬边界”对 MCP 写入不成立。

最小选项：
A. 照做并写明：放开用户 MCP，硬边界只对原生文件工具与 shell 成立，MCP 写入不在边界内（RESULTS 与 README 如实写）。门禁的路径边界检查仍会在交付时拦住 worktree 内越界改动，但拦不住 worktree 外的写入。
B. 只放开一部分：受管会话只加载用户 MCP 中的指定白名单（工作台设置里按角色配置），其余不加载。
C. 保持 `--strict-mcp-config`，本票其余部分照做。

执行主控暂按 A 推进实现与证据（不声称 MCP 写入受约束），在你裁定前不合入 T-141。

另需知会：Codex 去掉 `projects=untrusted` 后，启动行为按用户 `~/.codex` 的信任状态分三种（执行主控沙箱外探针，T-141 worktree 的 evidence/2026-10-23-batch23/T-141/probe-codex-start-01/）：trusted 直接进入；untrusted 出现 Open restricted 对话框；未设置出现 “Trust this folder?”，选 Trust 会写用户 `~/.codex`。已让 worker 在未设置时不选 Trust、按上报处理（遵守 T-071 不写全局配置）。如应另作处理，请一并裁定。