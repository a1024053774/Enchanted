# 任务卡 T-141-1

先读 `evidence/2026-10-23-batch23/COMMON.md`（公共约定）和 `.project-map/tickets/T-141-loosen-managed-limits.md`（ticket 全文，用户原话在里面）。

| 字段 | 内容 |
| --- | --- |
| 编号 | T-141-1 |
| 来源 | `.project-map/tickets/T-141-loosen-managed-limits.md`，ready_rev 1（提交 ebbae7bd0） |
| 目标 | 受管会话：网络全开；Claude worker/reviewer 去掉 `--strict-mcp-config`，能用用户 Claude 里配置的 MCP；Codex 与用户自己的 `~/.codex` 一致，不再用 `-c` 覆盖信任、沙箱细节与工具，只保留写入范围这一个沙箱约束；`-a never` 保留，需要审批或判断的事 worker 经 `issue` 上报到问题面板，执行主控用现有 `answer`/`disposition` 接口回复，worker 收到后继续。文件写入范围（worktree、请求目录、T-140 的额外目录；Git 公共目录禁写与两条 git 例外）是唯一硬边界。门禁不变。 |
| 非目标 | 门禁检查串（路径边界、验收文件不可改、红态、独立审查）的任何放宽；改用户的 `~/.claude`、`~/.codex` 等全局配置（a2a 不写全局配置，T-071）；`terminal_open`（T-142）；流程页（T-144）；AGENTS.md 的同步（ticket 写明由构思主控在本票关闭时做，你不改）。 |
| 修改边界 | 允许：`workbench/src/panes.ts`、`workbench/src/claudeLaunch.ts`、`workbench/src/gates/**` 中只限“审查员/worker 启动参数核对”随启动参数变化的对应更新、`workbench/roles/**`、`workbench/terminal/plugin/**`（如涉及 issue 上报用法）、`workbench/README.md`、`workbench/tests/**` 新文件、`evidence/2026-10-23-batch23/T-141/**`。禁止：`.project-map/**`、`AGENTS.md`、`CONTEXT.md`、验收文件，以及门禁其他检查。 |
| 验收文件（oracle_paths） | `workbench/tests/test_t140_extra_dirs_e2e.py`、`workbench/tests/test_t131_parallel_workers_e2e.py`、`workbench/tests/test_t132_issues_panel_e2e.py` |
| 红态命令 | 新 e2e 加 `--revision <起点>`：worker 访问外网失败、或 Codex 启动 argv 仍带 `network_access=false`。 |
| 任务类型 | 构建与基础设施（权限） |
| 复杂度 | M |
| 执行器 | Codex `gpt-6.1-sol`，`model_reasoning_effort="high"`，`service_tier="default"` |
| 起点 | 见派发消息 |
| 唯一写入者 | Herdr agent `b23-t141`，worktree `/Users/luckye/Documents/Code/a2a-wt-t141`，分支 `exec/t141` |

## 完成条件与交付

1. 新 e2e（如 `workbench/tests/test_t141_loosened_limits_e2e.py`），真实后台 + 真实 Electron：
   - 真实 Claude worker（`claude-haiku-5-5`，脚本化接口驱动工具调用）与真实 Codex worker 各一次 `curl` 一个公开地址成功。
   - Claude worker 实测能调用用户 Claude 里配置的一个 MCP 工具。夹具里怎样提供“用户配置的 MCP”（隔离 HOME 里的配置，或实测读取用户真实配置但不写它），写清楚依据；不得写用户的 `~/.claude`。
   - 真实 Codex worker 遇到要审批的动作：不卡在审批上，经 `issue` 上报，问题面板出现该条，执行主控经现有接口回复，worker 收到并继续（用户原话：“-a never 应该可以吧,让他通过我们软件的问题上报界面来上报,然后执行主控可以通过这个接口来回复他们”）。
   - 写入范围外的路径仍写失败（Claude 与 Codex 各一条）；T-140 额外目录仍可写。
   - 启动 argv 完整记录；门禁不按这些参数拒绝。
2. Codex 侧：真实入口的 Codex home 按 AGENTS.md“真实 Codex 验收”（/tmp 隔离 CODEX_HOME，只复制 auth.json 等）或产品既定的用户 `~/.codex`（T-127），哪种适用写明；测试结束删除隔离 home。
3. 已知问题（T-140 worker 上报 20261023T101123Z）：普通 Codex worker 的 `/tmp`、`$TMPDIR` 默认可写，T-140 移除额外目录撤不掉它。本票把写入范围定为唯一硬边界，请核对 Codex 与 Claude 的默认临时目录可写性，写进 RESULTS.md；若要收紧，同时给 CLI shell 准备可写临时目录并取得独立红绿证据；若判断应保留，写明理由与影响。拿不准就上报。
4. 红态 `--revision <起点>` 失败；至少两个变异（例如网络仍关；`-a never` 但 issue 回复送不到 worker）。
5. 回归：T-140、T-131、T-132 的 e2e 绿态；`test_t091_pane_ipc.mjs` 与起点同样、不更差。
6. RESULTS.md 与 RUN-OUTSIDE 脚本按公共约定。RESULTS.md 末尾列出 AGENTS.md 中需要构思主控同步的条目（关网络、Codex untrusted、T-075 socket 放行说明）的原文位置，不要自己改 AGENTS.md。
