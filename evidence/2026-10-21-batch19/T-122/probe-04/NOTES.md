# T-122 探针 04：Claude worker 的 Git 写入范围与设置来源

2026-10-21，Claude Code 2.1.306，`claude-haiku-5-5` `-p` 模式（真实模型，几次短调用）；`effective_config.py` 用本地假接口，不调用模型。起因：独立审查 01 第 1、2、4 条。

## 1. linked worktree 里，Claude 的沙箱自己把主仓库整个 `.git` 设为可写

`git_scope_probe.sh <目录> files|dirs|nogit|deny`：仓库 + 两个 attempt worktree（`a2a/T-1-a1`、`a2a/T-2-a1`），在 T-1 的 worktree 里依次跑 7 条命令。

| 变体 | allowWrite（主仓库部分） | 提交 | 移动 main | 移动 T-2 分支 | 新建分支 | 写另一 worktree | pack-refs |
|---|---|---|---|---|---|---|---|
| files（`run-files.txt`） | objects、本 gitdir、本分支 ref/lock/reflog | 成功 | **成功** | **成功** | 成功 | 拒 | 成功 |
| dirs（`run-dirs.txt`） | objects、本 gitdir、`refs/heads/a2a/` | 成功 | **成功** | **成功** | 成功 | 拒 | 成功 |
| nogit（`run-nogit.txt`） | 只有 objects 与本 gitdir | 成功 | **成功** | **成功** | 成功 | 拒 | 成功 |
| deny（`run-deny.txt`） | 同 nogit，另加 denyWrite：除本分支外每个已有 ref 及 reflog、packed-refs、HEAD、logs/HEAD、refs/a2a、refs/tags、refs/remotes、其他 worktree 的 gitdir | 成功 | 拒 | 拒 | 成功 | 拒 | 拒 |

前三个变体里，denyWrite 设的是 `/tmp/claude-501`，结果每条 Bash 都因 Claude 自己写 `cwd-*` 文件被拒而返回 1，但命令本身已经执行。所以 TMPDIR 不能收回。

`effective-nogit.json`（`effective_config.py` 读 Claude 在系统提示里报告的沙箱配置）：allowOnly 里有我们没给的 `<仓库>/.git`。denyWrite 进入 `denyWithinAllow`，所以能收回。

结论（实现于 `workbench/src/panes.ts` 的 `workerGitDenied`）：
- 用 deny 变体。新建分支名仍可创建；它不影响集成，与后续 attempt 同名时 `worktree add` 失败即拒。
- `$TMPDIR`（`/tmp/claude-501`，该用户所有 Claude 会话共用）仍可写，记为限制。

## 2. `--setting-sources local` 在 linked worktree 里也加载主 checkout 的 `.claude/settings.local.json`

`local_settings_probe.sh`：主 checkout 与 worktree 各放一个带 SessionStart 钩子的 `.claude/settings.local.json`。
- `local`：两个钩子都执行（`run-local-settings.txt`）。
- `PROBE_SOURCES=""`（`--setting-sources ""`）：都不执行（`run-no-sources.txt`），Claude 正常结束，`--settings` 的沙箱配置照样生效。

结论：worker 与 reviewer 改用 `--setting-sources ""`。e2e 的 `no_user_or_project_settings_loaded` 用夹具 HOME 的用户钩子和主 checkout 的本地钩子做行为检查；变异 `user-settings-loaded` 改回 `local`，被这一检查抓到。

重现：`zsh git_scope_probe.sh /private/tmp/<新目录> deny`；`PROBE_SOURCES="" zsh local_settings_probe.sh /private/tmp/<新目录>`。
