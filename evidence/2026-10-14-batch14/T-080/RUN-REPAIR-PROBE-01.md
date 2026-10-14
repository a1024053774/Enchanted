# T-080 run 打回最小对照（2026-10-14）

状态：INCOMPLETE。final-02 原件保留，本轮未重试旧运行；生产代码、现有夹具与业务断言均未修改。final-03 全量入口须等本对照读回后再准备。

当前事实：

- `final-02/t076-quality-red-contracts/red_run_reject_preserves_worker/database-readback.json` 的 `oracle_check` passed=true、modified=[]。随后 `completion_check` exit=1，`delivery_rejected` 的 check=completion、count=1、stopped=false、failure.error=oracle_failed。
- 修复消息绑定原 launch/attempt/rejection。ACK 的 `pane_idle` 为 orchestration seq=62，修复消息的 `turn_submitted` 为 seq=71；最后窗格 busy、turn=fixture-turn-3，其 active.dispatch 正是该修复消息，failed=null、stopped=false、queued=[]。原 worker 未被回收。
- `worker_submit` 停止 ACK 后轮询实时 idle；此时修复消息可以已被队列取走，进入下一回合。这解释了观察到的 harness_error，但尚不能替代指定的原产品对照。
- `test_quality_chain_e2e.py`、`quality_chain_host.ts`、`controlled_quality_pty.ts`、生产 `panes.ts`/`daemon.ts` 及 `core.ts` 的整个 `run` 方法与 cdf8fe9b 相同。当前卡已通过创建、认领、提交及 oracle 检查，没有卡格式拒收。

待证伪判断：原夹具等待短暂 idle 的条件存在时序竞争，T-080 的检查耗时变化可能改变出现概率。需要 cdf8fe9b 原产品在同一合法时序下的证据，才能据此修夹具；不能只因看到 busy 就放宽断言。

从 worker worktree 运行一次：

```sh
python3 -B evidence/2026-10-14-batch14/T-080/probe_run_repair_outside.py --output evidence/2026-10-14-batch14/T-080/run-repair-probe-01
```

脚本只跑 `red_run_reject_preserves_worker`。先冻结 cdf8fe9b 原产品，再冻结当前候选；两者各用自己的合法任务卡夹具，不向生产解析器添加兼容路径。两个子运行串行，各自使用新仓库、socket、受控进程和有限期限，不复用 `/private/tmp/q76-a0c76owi`。

探针在受控 ACK turn-2 的 Stop 之前等待真实门禁完成打回并将修复消息排队，固定 final-02 已观察到的时序。它不替换门禁返回、验收结果、数据库、队列或业务断言，也不延长原 run 的 8 秒期限。原 `worker_submit` 的 idle 轮询保持不变。

对照本身的 PASS 仅表示两个版本均出现同一 harness_error，且有原 attempt 未回收、主分支未推进、匹配的 ACK idle 事件和随后修复 turn-3 的独立读回。它不是产品验收 PASS。任一版本未到达指定时序、出现其他错误或清理失败，就保留 INCOMPLETE，不重试、不据此修正预期。

需要读回 `result.json`、两侧 `observation.json`、`ack-repair-barrier.json`、数据库与 Git 读回。若结果支持夹具归因，最小修正应等待绑定 ACK 身份的持久结束事件，并核对修复回写和原 worker 保留；不把任意 busy 状态视为成功。修后再准备新的 final-03 全量和提交命令。

本地已做 Python 3.9 语法、`--help`、既有事件字段与 `git diff --check` 核对。证据无单文件超过 5 MB；最大现存文件为 final-02 的 T-075 run 归档（4,139,512 字节）。socket/Git 元数据写入对照未运行，按 #134 交主控执行。
