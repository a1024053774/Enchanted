# T-077-1 CAS 屏障驱动修复交接（2026-10-11）

状态：**INCOMPLETE**。check-03 原始失败保持不变；分类为夹具控制错误。本轮只修两个测试驱动的放行方式，没有修改产品代码或业务断言。

## 失败发生在哪里

依据 `outside-green-03/readbacks/t-l4hcbnz0.json`、该批 `fixtures.tar.gz` 中的两个 Git wrapper `.done.json` 及实际命令收据：

1. 第一个 intent `21966abd-5864-4d0e-a933-6e11e1e0a6fa`：事件 85～89 记录 `start` → `start: ok` → `update … G0`/`prepare` → 无 prepare 成功响应 → 退出 128。对应真实 Git 已执行，stdout 为 `start: ok\n`；外部作者已把工作分支推进到 G1。
2. 门禁在事件 94 记录一次已知失配，随后完成新验收。事件 121 和 129 分别记录第二次完成条件与 passed verification，新 G 为外部提交 `04780f31b6b61bc856935da9bf2c9a8bc958a4ba`，新 M 为 `866e150659a8add1306f32245d331713e778a79f`。
3. 失败来自**第二个** intent `bfacd33d-a644-4857-b148-2977423fbe9b`：事件 154～156 只有 `start`、空响应及退出 125。对应 wrapper 记录 `executed_real_git=false`、空 stdin/stdout，没有启动真实 Git。

因此不是“竞争被放在 prepare 之后”，也不是候选漏读第一次 `start: ok`。第一次安全失配已经触发重验。第二次是夹具主动 abort；产品返回 `needs_reconciliation` 符合安全边界。

## 根因与修复

冻结的 `acceptance/test_recovery_e2e.py` 中 `GIT_BARRIER.barrier()` 会在独立 release 文件或 `release-all` 出现时结束等待；**没有该次独立 release 文件时固定返回 `abort`，不读取 release-all 的内容**。W11 驱动把 release-all 写成 `continue`，误以为后续 wrapper 会正常执行。它实际上是供清理使用的退出信号。

修复：第一层 wrapper 已到达屏障后，把 fixture 的 Git 路由原子地恢复到已登记的真实 Git 可执行文件，再仅给第一层 wrapper 写它自己的 `continue` release。第一层进程已启动，不受后续路由变更影响；后面的验收和 Git 事务直接运行真实 Git。oracle 的 release-all 语义不同，仍用于明确释放后续 oracle。

修复位置为 `workbench/tests/test_worktree_lifecycle_e2e.py` 的 CAS case 和 `workbench/tests/test_cas_race.py` 的 W11 驱动；没有改冻结 GIT_BARRIER、恢复断言、门禁阶段判定或重验条件。后者仍要求已确认的 prepare 前失配及无未知 I/O，prepare 后或结果未知仍需核对。

`check-03-diagnosis.json` 保存了结构化原始事件摘录和 wrapper 记录，并证明当前 19 个产品源码文件与失败批次归档逐字节一致；两个测试文件中的所有 assert/check/contract 调用 AST 与失败批次相同。原始 `result.json` 的自动 `business_red=true` 标签不被改写；它表示断言失败，本次归因以完整协议轨迹为准。

## 下一次运行

```sh
bash /Users/luckye/Documents/Code/a2a-wt-t077/evidence/2026-10-11-batch13/T-077/outside-sandbox.sh check-04
```

全部使用新输出目录：

- `outside-red-04`：修正后的同一 W11 信号在冻结起点上仍应为业务红态，避免用夹具错误代替功能红态。
- `outside-green-04`：同一信号在候选上应通过。first CAS 失配、新 G 上重验、双方提交和外部内容都要保留。
- `outside-regression-02-{coop,recovery,run,cas,cards}`：继续尚未运行的 8/9/18、CAS 1 项及任务卡 15 项。

任一阶段失败即停，保留 stdout/stderr 和全部现场。之前 green-03 的另外三项已经通过；本轮只修 CAS 驱动，不重复那三项。原 check-03 的回归 01 各组没有运行，不能列为通过。

本轮仅完成静态/范围检查，新的业务运行尚未执行；真实 Codex 用量仍为 0/4。按任务卡交给执行主控在沙箱外运行，不申请提权。
