# T-122 探针 01：Claude Code worker 的写入边界

2026-10-21，Claude Code 2.1.306，模型 claude-haiku-5-5，`-p` 模式（权限判定与交互模式同一套）。夹具在 `/private/tmp/t122-probe`：主仓库 `repo`、worktree `wt`（分支 work）、旁边的 `outside`。

重跑：`zsh t122_probe.sh`（第一轮）；第二轮命令见下，settings 见 `settings-2.json`。

## 第一轮（settings.json：允许规则写成 `Write(/private/tmp/...)`）

| 步骤 | 结果 |
| --- | --- |
| Write 工具写 worktree 内 | 被拒（don't ask mode）：单斜杠路径规则没匹配上 |
| Write 工具写 worktree 外 | 被拒 |
| Bash 写 worktree 外 | 沙箱拒绝，`operation not permitted` |
| Bash 写 worktree 内并 `git commit` | 成功（沙箱放行了主仓库 `.git`，worktree 的 Git 元数据在那里） |
| Bash `touch $HOME/...` | 沙箱拒绝 |

## 第二轮（settings-2.json：`Edit(//private/tmp/t122-probe/wt/**)`）

| 步骤 | 结果 |
| --- | --- |
| Write 工具写 worktree 内 | 成功 |
| Edit 工具改 worktree 内 | 成功（文件内容为 `in2`） |
| Write 工具写 worktree 外 | 被拒，记入 `permission_denials` |
| Write 工具经 `wt/../outside` 写外面 | 被拒，记入 `permission_denials` |

## 结论

- `--permission-mode dontAsk` + 允许 `Edit(//<worktree>/**)`、`Bash`、`Read` + `sandbox.enabled`、`allowUnsandboxedCommands: false`、`filesystem.allowWrite: [<主仓库>/.git]`：文件工具与 shell 的写入都限在 worktree（加 Git 元数据）内，没有批准窗口。
- 绝对路径的权限规则必须写成 `//` 开头。
- Claude Code 会在 worktree 里建空目录 `.claude/.cc-writes`；Git 不跟踪空目录，`git status --ignored` 为空，不进候选。
- 没覆盖：交互模式下的同一组合（T-122 真实入口会覆盖）；网络限制。
