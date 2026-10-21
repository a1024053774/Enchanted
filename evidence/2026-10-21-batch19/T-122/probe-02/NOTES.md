# T-122 探针 02：worker 不加载用户自己的 Claude 设置

2026-10-21，Claude Code 2.1.306，claude-haiku-5-5，`-p --output-format stream-json --verbose --include-hook-events`，cwd 为探针 01 的 worktree。

背景：用户 `~/.claude/settings.json` 里有 PermissionRequest、PreToolUse、Stop 等钩子（vibe-island、stop_checks.py、tokentracker），以及插件。worker 若加载它们，PreToolUse 的 allow 可能绕开权限边界，Stop 钩子可能阻断回合结束。`--bare` 能跳过钩子，但不读 OAuth 与钥匙串，订阅登录不能用。

重跑：`claude -p --model claude-haiku-5-5 --setting-sources <来源> --permission-mode dontAsk --output-format stream-json --verbose --include-hook-events "Reply with the single word ok."`

| `--setting-sources` | 钩子事件 | 插件 | MCP | 结果 |
| --- | --- | --- | --- | --- |
| `user,project,local`（默认） | SessionStart×2、UserPromptSubmit、Stop×3，都是用户钩子 | usage-statusbar、drawio 与 4 个内置 | notion、claude.ai Claude Docs | success |
| `local` | 无 | usage-statusbar 与 3 个内置 | claude.ai Claude Docs | success（正常登录可用） |

结论：worker 用 `--setting-sources local`，用户级钩子与插件不加载，登录照常；再加 `--strict-mcp-config` 去掉账号级 MCP。项目的 `.claude/settings.json` 也不加载（不在来源里）。worktree 是新建的，没有 `settings.local.json`。
