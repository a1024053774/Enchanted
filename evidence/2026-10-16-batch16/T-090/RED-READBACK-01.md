# T-090-1 红态原件核对

2026-10-16。红态采集及核对 PASS；产品状态 INCOMPLETE，尚未修复。

原件：`/Volumes/WD-Elements/a2a-evidence/2026-10-16-batch16/T-090/red-01/`。仓库入口为 `red-01.json`、`red-01.archive.json`。主控在沙箱外执行 `run-host.py --phase red --label red-01`；worker 只读核对原件，未重跑宿主。

- 起点：`f08a280bdf6142443efd52d4897d2305fd68987f`。runner 检查产品 `core.ts` 仍为该提交原字节，测试期间源码无变化。
- 原方法：`test_submit_requires_clean_head_and_cannot_replace_frozen_candidate`，只运行此方法，未替换原业务方法；1 test、0 failure、1 error、0 skip。
- 候选 C：`11834f7be2819e8141edcf5bd6f90e105953f667`。
- `review_requested` seq 115：共享 refs 中 worker 分支已指向 `900e915ff58454af17760fb8d51f519a50c86590`，不等于 C。
- `review_result` seq 122：门禁已接受审查报告。
- 结束核对的 `command_result` seq 127：worktree list 中 worker HEAD 仍为 `900e915ff58454af17760fb8d51f519a50c86590`；审查 worktree detached HEAD 为 C。
- seq 129/131/133：审查 worktree 为 detached HEAD=C，status 为空。
- seq 135：worker HEAD 仍为 `900e915ff58454af17760fb8d51f519a50c86590`。
- `review_lifecycle_failed` seq 136：phase=`reclaim`，error=`review_worker_workspace_changed`；没有 `review_reclaimed`。

`focused/unittest.txt` 的 RuntimeError 是 legacy driver 等不到回收的后果。失败不是依赖、启动或协议错误。旧实现因 HEAD 比较短路，未执行本次结束核对的 worker status 命令，因此不补称已经实测 worker 干净。

按主控本轮要求，修复前还要运行三条反例的起点表现。`baseline` 阶段会再次核对起点与 core 原字节，运行 HEAD 改动、变脏和同提交切换分支三条真实入口反例；结果未到前不修改产品逻辑。
