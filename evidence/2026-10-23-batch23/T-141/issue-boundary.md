状态：INCOMPLETE。T-141-1 / a1，worker b23-t141。

1. 公共约定 COMMON.md 在派发指定路径与本 worktree 均不存在；已询问正确路径。
2. Codex 去掉 projects=untrusted 后，原启动器只在 Open restricted 后放行任务，不能覆盖用户已有 trusted 项目。已准备 workbench/tests/t141_probe_codex_start.py，以原生无模型 TUI 探针核对启动信号；尚无外部结果。候选不改变用户信任配置。
3. Claude 官方 sandboxing 文档说明 MCP 工具不在 Bash 文件沙箱内；放开用户 MCP 可以调用本机 MCP 服务，但它们的文件写入能力取决于服务自身。当前候选只保证原生文件工具和 Bash 边界，不能声称所有 MCP 工具均受 worktree 文件边界约束。若 ticket 的唯一硬边界包含 MCP 服务写入，需要用户另定其权限与隔离范围。
4. Claude 官方设置提供全域代理白名单、Unix socket 与本地网络放行；不等于已证明所有非代理原始 TCP 工具不受限制。新 e2e 实测公开 HTTPS curl；其他协议尚未验证。

来源（2026-10-23）：https://code.claude.com/docs/en/sandboxing （What runs outside the sandbox、Network isolation、Temporary directories）。
建议：由主控核对上述边界；真实临时目录、MCP 与启动信号由沙箱外脚本取得结果后再作验收结论。不得将当前源码/契约检查的 PASS 上调为整票 PASS。
