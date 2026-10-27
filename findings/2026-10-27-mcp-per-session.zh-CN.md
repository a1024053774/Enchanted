# 四家 CLI 按会话挂 MCP 服务器（T-194 实测，2026-10-27）

为 T-194 先查清：Claude Code、Codex、opencode、agy 能否只为这一次会话挂上一个 MCP 服务器（启动参数或该会话自己的目录，不写全局配置），服务器拿得到什么环境，调用里带不带会话号。只记实测过的；推断单独标出。

版本：Claude Code 2.1.311，codex-cli 0.164.0，opencode v2.1.4，agy 1.4.8。探针是一个只记录收到的消息、只提供一个回显工具的最小 stdio MCP 服务器；之后用 a2a 自己的 `a2a mcp <cli>` 复核。

## 结论

| CLI | 按会话挂上的方式 | 服务器拿到的会话号 | 交互模式下模型能调用 | Enchanted 的做法 |
| --- | --- | --- | --- | --- |
| Claude Code | 插件 `plugin.json` 的 `mcpServers`（插件经启动参数 `--plugin-dir` 加载） | 环境变量 `CLAUDE_CODE_SESSION_ID` | 能；工具默认延迟加载，模型先经 ToolSearch 取到再调用 | 挂上 |
| Codex | 启动参数 `-c mcp_servers.<名>.command=…`、`args`、`env_vars` 等 | 环境里没有；每次 `tools/call` 的 `_meta.threadId`（另有 `x-codex-turn-metadata.thread_id`） | 能 | 挂上 |
| opencode | 环境变量 `OPENCODE_CONFIG_CONTENT` 里的 `mcp`（`type: local`） | 每次调用的 `_meta["ai.opencode/sessionID"]` | 能 | 挂上 |
| agy | 工作区目录里的 `.agents/mcp_config.json`（启动目录或 `--add-dir` 加的目录都可以） | 每次调用的 `_meta["antigravity.google/conversation_id"]` | **不能**（print 模式能） | 不挂，继续用 `a2a` 命令 |

## 各家细节

### Claude Code

- 插件里声明的服务器随插件加载，只对这次会话生效，不写 `~/.claude`。工具名形如 `mcp__plugin_enchanted-a2a_enchanted__<工具>`。
- 服务器进程的环境里有 `CLAUDE_CODE_SESSION_ID`，等于这次会话的 jsonl 文件名。
- 启动后先发 `server/discover`；回 `-32601`（方法不存在）不影响后续 `initialize`、`tools/list`。
- 工具默认不直接出现在模型的工具表里，模型要先调 ToolSearch（`select:<工具名>`）。T-194 的 e2e 用脚本化模型照此调用。

### Codex

- 服务器只拿到 `env_vars` 列出的环境变量；不列就拿不到 `A2A_TERMINAL*`，也拿不到 `CODEX_HOME`。
- 非交互的 `codex exec` 下，MCP 工具调用报“需要批准但策略是 never”；设 `default_tools_approval_mode="approve"` 后不再询问。可选值：auto、prompt、writes、approve。
- 工具超时默认 60 秒；角色申请要等用户批准最多 10 分钟，所以设 `tool_timeout_sec=660`。
- 环境里没有 `CODEX_THREAD_ID`（`a2a` 命令在 shell 工具里才有）；会话号取自每次调用的 `_meta.threadId`。T-194 的真实核对里，它等于隔离 `CODEX_HOME` 中 rollout 首行 `session_meta.id`。
- 在一个新的 `CODEX_HOME` 里首次启动时，Codex 对 Enchanted 经启动参数加的钩子弹出一次信任确认；选“Trust all and continue”后继续。这是钩子（T-133）的既有行为，不是 MCP 带来的。

### opencode

- `OPENCODE_CONFIG_CONTENT` 的 `mcp.<名>` 写 `{"type":"local","command":[…]}` 即可，只对这个进程生效。
- `opencode run` 默认连到已在运行的服务端，会忽略这个环境变量；加 `--standalone` 后生效。交互模式下直接生效。
- 每次调用的 `_meta` 带 `ai.opencode/sessionID`。a2a 目前不把它当角色申请的会话号（T-195 另从 OSC 7501 取 opencode 的会话号）。

### agy

- 读每个工作区目录里的 `.agents/mcp_config.json`，`--add-dir` 加的目录也算，所以 Enchanted 的说明目录可以带上它，不用写 `~/.gemini`。
- 启动后先发 `server/discover`，回 `-32601` 后照常 `initialize`、`tools/list`；回空结果也一样。
- agy 把每个服务器的工具定义缓存到 `~/.gemini/antigravity-cli/mcp/<服务器名>/<工具名>.json`。这是 agy 自己写进用户 HOME 的。
- print 模式（`agy -p`）下模型调用了工具并拿到结果；**交互模式下，服务器照样启动并返回了工具清单，模型却回答没有这个工具**。复现了四次：服务器放在启动目录或 `--add-dir` 目录，加或不加 `--dangerously-skip-permissions`，目录首次信任后或已信任，结果相同；e2e 里经 Enchanted 包装脚本也一样。
- 推断（未证实）：交互模式下工作区 MCP 工具没有进入模型的工具表；原因不明，可能是 agy 的缺陷或尚未开放的功能。
- 主控都在交互模式里，所以 agy 不挂 a2a 的 MCP 服务器，继续用 `a2a` 命令；这样也不会让 agy 往 `~/.gemini` 写我们的工具缓存。agy 包装脚本里写明了重新评估的条件。

## 对 T-194 的影响

- Claude Code、Codex、opencode 经包装脚本或插件挂上 `a2a mcp <cli>`；agy 不挂。
- 角色申请的会话号：Claude Code 取环境变量，Codex 取调用的 `_meta.threadId`；opencode、agy 不记会话号，与 `a2a request` 一致。
- 证据：`evidence/2026-10-27-batch28/T-194/`（Claude Code 全流程 e2e；Codex、opencode 真实 CLI 核对；agy 交互模式复现）。
