# T-122 探针 05：只让单独的 git add / git commit 走沙箱外

2026-10-21，Claude Code 2.1.307。`scripted.py` 用本地脚本化接口驱动真实 claude（`-p`），不调用模型。

起因：独立审查 02 第 1～5 条。用户选定的做法是：
- 整个 Git common dir 和 worktree 的 `.git` 文件都对沙箱 deny；
- 只有单独的 `git add`、`git commit` 列入 `sandbox.excludedCommands`，与 Codex 那两条前缀规则相同；
- 先用探针确认拼接命令和 `git -c` 前缀都不会被放行，探针不过就改用门禁代提交。

设置：
- `excludedCommands: ["git add *", "git commit *"]`；
- `denyWrite: [<common dir>, <worktree>/.git]`；
- 提交钩子用 `workbench/hooks/`，环境与受管 worker 相同（`A2A_*`、`GIT_CONFIG_*`）。

Claude 自己的说明是 excludedCommands “a convenience, not a security boundary”（二进制内 schema 描述），所以每一种绕法都实测。

## 第 1 批（`actions.py`，`run-1.txt`）

- 单独的 `git add`、`git commit` 成功，提交带全部 A2A 尾注。
- 以下拼接形式整条留在沙箱里：
  - `&&`、`;`、`|`、`||`、换行；
  - `$(...)` 与反引号；
  - 函数定义；
  - 重定向到 worktree 外（被拒）。
- 下列写入在沙箱里都被拒，refs 不变：
  - replace ref、覆盖对象、`info/exclude`、`main.lock`、新分支；
  - Python 写或改名 worktree 的 `.git` 文件。

这一批的风险命令都在末尾加了 `; echo`，测的其实是“拼接命令”。

## 第 2 批（`actions2.py`，`run-2.txt`）：每种风险写法单独成一条命令

- 走沙箱外并成功，尾注齐全：`git commit --no-verify`（尾注由 prepare-commit-msg 写入，`--no-verify` 不跳过它）、`--amend`、`-m "s; git update-ref ..."`（引号里的分号不算拼接）。
- 留在沙箱里而失败：`git -c core.hooksPath=/dev/null commit`、`GIT_CONFIG_COUNT=0 git commit`、`GIT_DIR=… GIT_WORK_TREE=… git commit`。
- `export GIT_CONFIG_COUNT=0 GIT_DIR=…` 之后再单独 `git commit`：提交仍落在本 attempt 分支，`export` 不带到下一条命令。
- `cd <主 checkout>`：Claude 回报 “Shell cwd was reset to <worktree>”，随后的提交仍落在本 attempt 分支。
- `git add <worktree 外>` 被 git 拒；`git commit … > <worktree 外>` 的重定向被沙箱拒。
- main 始终不变。

## 第 3 批（`actions3.py`，`run-3.txt`）：不受沙箱管的文件工具

Write 与 Edit 改 worktree 的 `.git` 文件都被拒（Claude 自带的 `.git` 保护；Edit 规则 `Edit(/<worktree>/**)` 不能放行它），Write 改 common dir 也被拒。写 worktree 里的普通文件照常成功。

## 结论

补充（e2e 07）：不 deny worktree 的 `.git` 文件时，沙箱同样拒写它（红态候选 2 与变异 `dotgit-file-writable` 都是 `operation not permitted: .git`），所以实现只 deny common dir。


探针通过，采用“git add/commit 走沙箱外”（`workbench/src/panes.ts` 的 `claudeArgv`、`workerGitDenied`）。剩余的沙箱外面：
- 单独的 `git add`、`git commit` 以 worker 环境在沙箱外运行，会执行 a2a 的提交钩子和仓库原有钩子，以及用户自己 `~/.gitconfig` 定义的 filter（如 git-lfs），作用对象是 worktree 里的文件；
  - 更正（审查 03）：原写“仓库原有钩子在 `.git/hooks`，worker 不可写”不成立。`core.hooksPath` 可指向 worktree 内（husky），钩子也可调用 worktree 里的代码；审查 03 实测能写出 worktree、移动 main。候选 4 起受管提交不再执行项目钩子。
  - 更正（审查 03）：只由 `git add`/`git commit` 拼成的一行同样在沙箱外运行；混入其他命令的才留在沙箱里。
- `--amend` 只能改写本 attempt 分支。

重现：`PROBE_ACTIONS=actions2.py zsh run.sh /private/tmp/<新目录> <仓库>/workbench/hooks/`（`PROBE_ACTIONS` 省略为第 1 批）。
