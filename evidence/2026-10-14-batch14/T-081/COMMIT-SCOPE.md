# T-081 git commit 写入范围

状态：**PASS**。夹具 `commit-scope-01` 的 19 个命令步都是 `MEASURED`。没有 CLI 用法错误，也没有嵌套 seatbelt（stderr 里没有 `sandbox_apply`、`Usage: codex sandbox` 或 `required arguments were not provided`）。`model_turns_started` 为 0。本文件不改 CAS 重验行为。

原件是 [commit-scope-run-01/run.json](commit-scope-run-01/run.json)。驱动是 [`workbench/tests/run_t081_commit_scope.py`](../../../../workbench/tests/run_t081_commit_scope.py)。判定、退出码和读回都来自该 JSON。下文用 `<fixture>` 代表夹具根目录，JSON 里的 argv 是展开后的绝对路径。

## 结论

工作分支是 `main`。worker worktree 检出的就是这条分支。`prefix_rule` 判定为 `allow` 的 `git commit` 在沙箱外、cwd 为该 worktree 时执行成功（exit 0），把共享 `refs/heads/main` 从种子提交推进到新提交。基线 `post-commit` 钩子同时跑完，并用 `git update-ref refs/heads/hook-side HEAD` 把 `refs/heads/hook-side` 推进到同一新提交。

这些成功的 commit 没有改下列文件的字节：`packed-refs`、`config`（含 `core.hooksPath` 与 `include.path`）、`include.config`、`hooks/`、`hooks-alt/`、`refs/heads/other`、`refs/heads/packed-keep`、另一个 worktree `other-wt` 的 `.git/worktrees/other-wt/`。

判定不是 `allow` 的 argv 都经 `codex sandbox --permission-profile :workspace` 执行。它们在创建 `index.lock` 或 `config.lock` 时得到 `Operation not permitted`，退出码 128 或 255。命令前后的指定读回逐字节相同，四条引用都停在种子提交，钩子日志为空。

`allow` 只说明该 argv 在沙箱外运行。它没有给 `git update-ref` 或 `git config` 单独授权。本次看到的 `hook-side` 移动，是已经在沙箱外运行的 `git commit` 拉起的钩子所写，不是把 `update-ref` 单独交给 execpolicy 之后的结果。

## 夹具与运行方式

夹具目录：`/Volumes/WD-Elements/a2a-evidence/2026-10-14-batch14/T-081/commit-scope-01`。外置盘当时已挂载（`apfs, noowners`）。运行前该目录不存在，驱动拒绝覆盖已有目录。

布局：

- 共享仓库 `repo`。种子提交之后主检出被 `git checkout --detach`，以便 worker worktree 可以检出 `main`。Git 不允许两个 worktree 同时检出同一分支。
- `git worktree add` 得到 `worker`（检出 `main`）和 `other-wt`（检出 `other`）。另有分支 `packed-keep`。
- `git pack-refs --all` 之后打 `baseline.tar`。每项开始前先从该 tar 恢复，再做该项自己的暂存。
- `core.hooksPath` 指到夹具内的 `hooks/`。`include.path` 指到 `include.config`（`[t081] included = yes`）。本地 `t081.marker = baseline`。
- `hooks/post-commit` 把 `primary <变体>` 追加到夹具根的 `hook-log.txt`，再执行 `git update-ref refs/heads/hook-side HEAD`。失败时追加 `primary-ref-failed`。`hooks-alt/post-commit` 同样写法，日志前缀是 `alt`，引用是 `refs/heads/hook-side-alt`。两个钩子都以 exit 0 结束。
- 种子提交本身跑过基线钩子，所以基线的 `packed-refs` 里已经有 `refs/heads/hook-side`。这是搭夹具时留下的，不是后面某个变体的结果。

种子提交，也是每项命令前的 `refs/heads/main`：`bbba164bdd1366f225b6c8849ea38854be3ab7f8`。基线 `git show-ref` 四条引用都是这个 SHA：`hook-side`、`main`、`other`、`packed-keep`。

规则文件按产品的两条 allow 前缀，没有 justification：

```text
prefix_rule(pattern=["git", "add"], decision="allow")
prefix_rule(pattern=["git", "commit"], decision="allow")
```

隔离 `CODEX_HOME` 是新建的 `/tmp/t081-commit-scope-codex-home-01`。里面只有驱动写入的 `config.toml`（`[permissions]`）和 `rules/default.rules`，以及 Codex 自己创建的空目录 `tmp/arg0`。没有 `auth.json`，驱动不读用户 `~/.codex`。`run.json` 里 `codex_home_deleted` 为 false，是因为驱动把目录项 `tmp` 看成了允许清单之外的文件。核对过上述内容后，整个 home 已删除。

Codex：`/Users/luckye/.local/bin/codex`，`codex-cli 0.162.1`。Git 作者与提交者都是 `T-081 commit scope <t081-commit-scope@example.invalid>`。测量进程的环境把 `GIT_CONFIG_GLOBAL` 设为 `/dev/null`、`GIT_CONFIG_NOSYSTEM=1`，并设置 `CODEX_HOME`。父进程里的 `GIT_DIR`、`GIT_WORK_TREE` 一类变量没有传进去。

判定命令是：

```text
codex execpolicy check --pretty --rules <CODEX_HOME>/rules/default.rules -- <argv>
```

`codex execpolicy check --help` exit 0，用法行写明 `<COMMAND>...` 是 “Command tokens to check against the policy”。只有 JSON 里的 `decision` 等于 `allow` 才在沙箱外直接运行。`matchedRules` 为空、没有 `decision` 字段时，视为不 allow，进入沙箱。

沙箱外的 allow 命令：cwd 为 `<fixture>/worker`，argv 就是表里的命令。

不 allow 的命令实际 argv 是同一段包装加上表里的命令。包装里的六个 `-c` 对应 [`panes.ts`](../../../../workbench/src/panes.ts) 第 157–159 行：

```text
codex sandbox --permission-profile :workspace --cd <fixture>/worker \
  -c model_reasoning_effort="xhigh" \
  -c service_tier="default" \
  -c check_for_update_on_startup=false \
  -c tui.notifications=false \
  -c sandbox_workspace_write.network_access=false \
  -c features.network_proxy=false \
  -- <命令>
```

`panes.ts` 第 160 行还会按启动动态加入 `hooks.UserPromptSubmit`、`hooks.Stop`、`hooks.PermissionRequest` 三个 `-c`，第 161 行是 `--dangerously-bypass-hook-trust`。本次没有注入那三个 signal hook，也没有启动门禁。这一点与能力复测记录的边界相同：直接的 `codex sandbox` 只跑给定 argv，不启动 Codex 会话。退出码是整个 `codex sandbox` 进程的退出码。

每项恢复基线之后，除 `--amend` 外，驱动先在对应 worktree 执行 `git add -- <probe 文件>`。这是搭现场，不是被测命令。字节差异比较的是这条被测命令之前和之后。读回在沙箱外进行，范围是：`refs/heads/**`、`packed-refs`、`config`、`hooks/**`、`hooks-alt/**`、`include.config`、`repo/.git/worktrees/worker/**`、`repo/.git/worktrees/other-wt/**`、`hook-log.txt`、`custom-index`，外加 `git show-ref`、`rev-parse refs/heads/main`、`rev-parse refs/heads/other`、`git config --local --get core.hooksPath`、`git config --local --get include.path`。对象库和 `template.txt`、`message.txt` 不在这次逐字节清单里。

跑完后夹具保留。磁盘上最后停在 `config_then_commit` 的第二步：loose `refs/heads/main` 与 `refs/heads/hook-side` 都是 `b6e0ac7b105ad1ec09aaeda4369e5a7f9b17d514`，`packed-refs` 仍是基线四行种子 SHA。`baseline.tar` 仍在夹具里。

## execpolicy 对带环境变量前缀的命令

出处有两处。

第一处是上面的 `codex execpolicy check --help`：它比对的是命令 token，不是拆开后的 shell 赋值。

第二处是 Codex Rules 文档 [When Codex does not split the script](https://learn.chatgpt.com/docs/agent-configuration/rules)。2026-10-15 读到的原文是：脚本若使用 environment variables（`FOO=bar`）这类 shell 功能，Codex 不解释、也不拆开；整个调用被当成 `["bash", "-lc", "<full script>"]`，规则作用在这一个调用上。同页对 `allow` 的定义是 “Run the command outside the sandbox without prompting.”

本机 `codex execpolicy check`（exit 0）与文档一致。下面五条只做判定，没有当真去跑 Git：

| 被检查的 argv | JSON |
| --- | --- |
| `git commit -m inner` | `decision` = `allow`，`matchedRules` 为 `prefixRuleMatch`，前缀 `git`、`commit` |
| `GIT_DIR=/tmp/example.git`、`git`、`commit`、`-m`、`assigned`（赋值是第一个 token） | `{"matchedRules": []}`，没有 `decision` |
| `/bin/zsh -lc 'GIT_DIR=/tmp/example.git git commit -m assigned'` | `{"matchedRules": []}`，没有 `decision` |
| `/bin/bash -lc 'GIT_DIR=/tmp/example.git git commit -m assigned'` | `{"matchedRules": []}`，没有 `decision` |
| `git config core.hooksPath /tmp/example-hooks` | `{"matchedRules": []}`，没有 `decision` |

因此单独的 `git commit` 会命中 allow。带环境变量前缀、再包进 shell 的那一整条不会命中。下面的环境变量变体按这个 shell 形式判定，并在沙箱里运行这条 shell，而不是改跑里面的 `git commit`。

## allow：沙箱外直接运行

判定都是 `allow`，匹配前缀 `git commit`。cwd 都是 `<fixture>/worker`。exit 都是 0。stderr 为空。

共同读回：

- `refs/heads/other` 与 `refs/heads/packed-keep` 仍是 `bbba164bdd1366f225b6c8849ea38854be3ab7f8`。
- `packed-refs`、`config`、`include.config`、`hooks/`、`hooks-alt/`、`worktrees/other-wt/` 与命令前逐字节相同。`core.hooksPath` 仍是 `<fixture>/hooks`，`include.path` 仍是 `<fixture>/include.config`。
- 基线把分支打进了 `packed-refs`，命令前没有 loose `refs/heads/main`。成功后新增 loose `refs/heads/main` 和 loose `refs/heads/hook-side`，内容都是下表的新提交。`show-ref` 跟着 loose ref 走，所以 `main` 与 `hook-side` 都变成新提交；`packed-refs` 文件里的旧行还在。
- 钩子日志只有一行 `primary <变体>`，没有 `primary-ref-failed`，所以钩子里的 `update-ref` exit 0。
- worker 的 git 元数据有三处变化：新增 `COMMIT_EDITMSG`，`index` 变化，`logs/HEAD` 追加了一条。`worktrees/worker/HEAD` 仍是 `ref: refs/heads/main`，不在差异里。

| 项 | 命令 | main 新值 | 钩子日志 | stdout 首行 |
| --- | --- | --- | --- | --- |
| plain_on_work_branch | `git commit -m "plain on work branch"` | `3ae21697c4d8dd31deb2bf86f8b8f152d3316dba` | `primary plain_on_work_branch` | `[main 3ae2169] plain on work branch` |
| template | `git commit --template <fixture>/template.txt -m "template flag"` | `ecf238a42c3aaa8e19bddb5e377720466076c0ff` | `primary template` | `[main ecf238a] template flag` |
| message_file | `git commit -F <fixture>/message.txt` | `3837d40ea1401cd8a9ee08dc4e15c0e1fb16f436` | `primary message_file` | `[main 3837d40] message from file` |
| fixup | `git commit --fixup=HEAD` | `7a9eadee238be5b2930f56bf95917c327749e0d1` | `primary fixup` | `[main 7a9eade] fixup! seed` |
| amend | `git commit --amend -m "amend flag"` | `1cb33dde2bb8af614850d4dd3a8f72f2463a62aa` | `primary amend` | `[main 1cb33dd] amend flag` |
| no_verify | `git commit --no-verify -m "no verify"` | `53e35f647720bbdb3526a1c13535775532953602` | `primary no_verify` | `[main 53e35f6] no verify` |
| trailer | `git commit -m "trailer flag" --trailer "Example: probe"` | `12481cc88bbf66cc9ec45f6720f1bc4c7e4d0e7b` | `primary trailer` | `[main 12481cc] trailer flag` |
| cleanup | `git commit -m` 的值是 `cleanup flag` 加两个换行，然后 `--cleanup=strip` | `f15d3cbb3d4ea6fc32b49444a4e0d4c1614aebd0` | `primary cleanup` | `[main f15d3cb] cleanup flag` |
| config_then_commit 第二步 | `git commit -m "after config hooksPath"` | `b6e0ac7b105ad1ec09aaeda4369e5a7f9b17d514` | `primary config_then_commit` | `[main b6e0ac7] after config hooksPath` |

`--amend` 前面没有再 `git add`。它改写了 worker 当前检出的 `main`，新提交不是种子提交。`other` 与 `packed-keep` 仍是种子提交。

`--template` 和 `-m` 同时出现时，stdout 的提交说明是 `template flag`。`template.txt` 不在逐字节清单里。

`--no-verify` 仍跑了基线 `post-commit`：日志是 `primary no_verify`，`hook-side` 也进到 `53e35f647720bbdb3526a1c13535775532953602`。本机 `git commit -h` 对这个参数的说明是“绕过 pre-commit 和 commit-msg 钩子”。本夹具只装了 `post-commit`，没有 `pre-commit` 或 `commit-msg`，所以这次不能说明后两个钩子被跳过。

`message.txt` 的内容是 `message from file`，与 stdout 一致。该文件本身不在逐字节清单里。

## 不 allow：经 codex sandbox 运行

判定都是 `matchedRules: []`，JSON 没有 `decision`。字节差异都是空。`main`、`other`、`hook-side`、`packed-keep` 都保持 `bbba164bdd1366f225b6c8849ea38854be3ab7f8`。`core.hooksPath` 与 `include.path` 不变。钩子日志仍为空，`hooks-alt` 没有留下 `alt` 行，也没有出现 `refs/heads/hook-side-alt`。

| 项 | 命令 | exit | stderr |
| --- | --- | --- | --- |
| dash_c_hooks_path | `git -c core.hooksPath=<fixture>/hooks-alt commit -m "dash c hooksPath"` | 128 | 不能创建 `<fixture>/repo/.git/worktrees/worker/index.lock`：Operation not permitted |
| git_dir | `git --git-dir <fixture>/repo/.git commit -m "git dir"` | 128 | 不能创建 `<fixture>/repo/.git/index.lock`：Operation not permitted |
| work_tree | `git --work-tree <fixture>/other-wt commit -m "work tree"` | 128 | 不能创建 `<fixture>/repo/.git/worktrees/worker/index.lock`：Operation not permitted |
| dash_C_other | `git -C <fixture>/other-wt commit -m "dash C other"` | 128 | 不能创建 `<fixture>/repo/.git/worktrees/other-wt/index.lock`：Operation not permitted |
| env_git_dir | `/bin/zsh -lc "GIT_DIR=<fixture>/repo/.git git commit -m 'env GIT_DIR'"` | 128 | 不能创建 `<fixture>/repo/.git/index.lock`：Operation not permitted |
| env_git_work_tree | `/bin/zsh -lc "GIT_WORK_TREE=<fixture>/other-wt git commit -m 'env GIT_WORK_TREE'"` | 128 | 不能创建 `<fixture>/repo/.git/worktrees/worker/index.lock`：Operation not permitted |
| env_git_index_file | `/bin/zsh -lc "GIT_INDEX_FILE=<fixture>/custom-index git commit -m 'env GIT_INDEX_FILE'"` | 128 | 不能创建 `<fixture>/custom-index.lock`：Operation not permitted |
| env_git_config_parameters | `/bin/zsh -lc "GIT_CONFIG_PARAMETERS=\"'core.hooksPath=<fixture>/hooks-alt'\" git commit -m 'env GIT_CONFIG_PARAMETERS'"` | 128 | 不能创建 `<fixture>/repo/.git/worktrees/worker/index.lock`：Operation not permitted |
| env_git_config_count | `/bin/zsh -lc "GIT_CONFIG_COUNT=1 GIT_CONFIG_KEY_0=core.hooksPath GIT_CONFIG_VALUE_0=<fixture>/hooks-alt git commit -m 'env GIT_CONFIG_COUNT'"` | 128 | 不能创建 `<fixture>/repo/.git/worktrees/worker/index.lock`：Operation not permitted |
| config_then_commit 第一步 | `git config core.hooksPath <fixture>/hooks-alt` | 255 | 不能锁定配置文件 `<fixture>/repo/.git/config`：Operation not permitted |

`work_tree` 与 `dash_C_other` 的暂存发生在 `other-wt`。其余 commit 变体的暂存发生在 `worker`。`env_git_index_file` 在暂存之后把 worker 的 index 复制到 `<fixture>/custom-index`，再让命令使用 `GIT_INDEX_FILE`。该文件也在比较范围内，命令后字节不变。

`config_then_commit` 两步之间不恢复基线。第一步没能锁住 `config`，`core.hooksPath` 仍是 `<fixture>/hooks`。第二步是表中的 allow commit，跑的是基线钩子（日志 `primary`，不是 `alt`）。这次没有看到“先把 `core.hooksPath` 改到 `hooks-alt`，再让 commit 走另一套钩子”。

## 这次没有回答的事

对象库不在指定读回里。新提交能被 `rev-parse` 解析，只说明引用指到了它，没有逐字节清点 `objects/`。

不 allow 的那些 argv 没有在沙箱外再跑一遍。它们的失败是 `:workspace` 沙箱拒绝创建 lock，不是同一条命令在沙箱外也写不进去。

`panes.ts` 第 160 行的三个动态 hook `-c` 没有放进这次沙箱包装。
