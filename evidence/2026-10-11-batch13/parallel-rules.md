## 并行规则（本批第二轮起有 2～3 个 worker 同时工作）
- 你在**自己的 git worktree** 里工作，不碰主 checkout `/Users/luckye/Documents/Code/a2a`；那里归执行主控和另一个 worker 使用。你的 worktree 路径和分支名写在任务卡的“唯一写入者”一栏。`workbench/node_modules` 已经由执行主控装好（离线安装，缓存在外置盘），你不需要也不要重新安装。
- 只在你的分支上提交。git add、git commit 各自单独执行，不加前缀。
- 交付前，先把分支变基到最新的 `main` 上：`git -C <你的 worktree> rebase main`。冲突由你解决：只能保留双方的意图，不能删掉对方的行为来让冲突消失。变基之后，在变基后的代码上重跑本卡的完成条件和 8/9/18 回归，然后再交付。最后由执行主控把你的分支快进合并进 `main`。
- 下面这些文件只由执行主控写：本批的 `dispatch.jsonl`、`panes.txt`、`controller-poll.log`，以及 `.project-map/MAP.md`。ticket 你只写自己那一张的 Resolution。
- 沙箱外的 `outside-sandbox.sh` 放在你本卡的证据目录里，脚本里的路径一律用你自己 worktree 的绝对路径。
