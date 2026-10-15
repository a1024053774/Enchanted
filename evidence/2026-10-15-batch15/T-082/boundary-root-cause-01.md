# T-082 launch-boundary root cause

outside-command-02-01 的 `wrong-workspace` 变异把 reviewer 实际 argv 的 `-C` 改为审查 worktree，但门禁仍返回 `ok: true`。读回的原因是：`Panes.createPane()` 的启动记录原先把 `worktree` 写成 `attempt.workspace`，而 `reviewLaunch()` 只比较这个记录字段和 `live.workspace`，没有核对 `launch.argv` 中 `-C` 的值。于是记录字段与实际启动 argv 分离，错误工作目录未被发现。

修复：启动记录现在保存实际 `launchWorkspace`；`reviewLaunch()` 额外要求 `argv[-C] === review.candidate_workspace`。runner 改为四个变异逐项执行并记录全部结果，不再因第一枚变异失败提前退出。
