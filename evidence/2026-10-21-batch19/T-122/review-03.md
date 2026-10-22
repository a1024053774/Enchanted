# T-122 独立审查 03（候选 c13befd85，父 3cf6e2c8d）

审查者：本 session 新开的只读审查子会话（Claude，干净上下文），2026-10-21。用本地脚本化接口驱动真实 Claude Code 2.1.307，未调用真实模型。探针脚本与输出见 `review-03-probe/`（现场原在 `/private/tmp/t122-review03/`）。下面按原报告的编号与严重程度整理要点。

**总体结论：需修复。**

## 发现

1. **高：沙箱外的 `git commit` 会执行项目自己的钩子，钩子内容 worker 可改。**
   - `hook.py` 的 `forward()` 在沙箱外转发仓库原钩子。仓库的 `core.hooksPath` 指向 worktree 内时（husky），钩子就是 worktree 里 worker 能写的文件。
   - runB：写 `.husky/pre-commit` 后单独执行 `git commit`，钩子在 worktree 外建了文件。
   - runB2：用 `.husky/post-commit` 移动了 `main`。
   - pre-commit、lefthook 读 worktree 里的配置，机制相同，未实测。
   - Codex 走同一条转发；probe-05 NOTES 写的“仓库原有钩子 worker 不可写”不成立。
2. **中：reviewer 要求 `argv[0]` 与 worker 相同。** `argv[0]` 是 realpath，带 Claude 版本号；两次启动之间 Claude 一旦更新，合法 reviewer 就会被误拒，与 T-118 冲突。
3. **中：N7 新加的 reviewer 核对条件没有反例或变异测试。**
4. **低：“拼接命令留在沙箱里”的说法不准确。** runD：只由 `git add`/`git commit` 拼成的一行同样在沙箱外运行，各段都带尾注，没有安全影响。
5. **低：其他 Git 写操作在沙箱里全部失败。** runC：`git stash`、`restore`、`checkout --`、`rm`、`mv`、`reset` 都失败。派发提示要求“被拒就上报并结束”，worker 可能因此中止任务。
6. **低：证据问题。**
   - `review-02.md` 引用的 `RESULTS.md` 不存在。
   - `e2e-green-08` 没有绑定代码版本。审查者在 c13befd85 上补跑通过（`review-03-probe/green-c13befd85.json`）。
7. **未核实**：T-112 native 回归，审查时还在跑。

## 审查者核实无问题的点

- runA：26 种 shell 注入写法全部留在沙箱里。
- runD：`\git`、`command git`、`"git"` 等写法都留在沙箱里。
- runC：伪造的尾注都被钩子替换成正确值。
- git-lfs 3.7.1 不执行 `.lfsconfig` 里的 clean。
- 正常交付需要的写入都由沙箱外的 add/commit 完成。
- T-084 mutants-05 与声称一致。
- 红态 `e2e-red-08-candidate2`、变异 `git-excluded-broad-08`、`dotgit-file-writable-07` 与声称一致。

## 处理（候选 4）

1. 用户裁定“worker 提交不跑项目钩子”：
   - `hook.py` 只保留 prepare-commit-msg 尾注钩子，删除 `forward()` 和其余 25 个钩子链接；
   - 门禁在 submit 时把本 worktree 下跳过的项目钩子记为 `project_hooks_skipped`；
   - Claude 与 Codex 相同；
   - e2e 加 husky 反例：基线里跟踪 `.husky/pre-commit`，仓库设 `core.hooksPath=.husky`，worker 改写这个钩子去移动 main、在外面建标记文件。
2. 去掉 `argv[0]` 相等的要求，可执行文件只记录。e2e 加正例 `--reviewer-case other-executable-path`：reviewer 经链接路径启动同一个 Claude。
3. e2e 加 `--reviewer-case model-differs|fast-differs|hook-prefixed`，期望门禁以 `review_launch_boundary` 拒绝；配套门禁变异 `gate-reviewer-model-unchecked`、`gate-reviewer-fast-unchecked`、`gate-reviewer-hook-includes`。
4. 改正 README、ticket、probe-05 NOTES 里的表述。
5. 派发提示补上替代做法：普通 `mv`/`rm` 后 `git add <路径>`；恢复文件用 `git show HEAD:<路径> > <路径>`。
6. 写 RESULTS.md；e2e 最终绿态用 `--revision` 绑定代码版本。T-112 native 回归 09 在 4831d5a71 上通过。
