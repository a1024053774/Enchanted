# T-040 A：主控决定 02 的连续五轮复验（2026-10-08）

**PASS，仅限 A 部分，按主控决定以“已知未复现的一次超时”接受。** 原恢复 9 项在同一候选上连续顺序运行 5 次，45/45 全部通过，没有失败、补跑或自动重试。原 2 秒忙拒绝断言、产品和测试保持原样；首轮失败与独立审查 FAIL 不改判，超时原因仍 unknown。T-040 整体保持 open，首次日常分派不在本交付范围。

接受依据为 [主控决定 02](../controller-decision-02.md) 第 2 条及本轮五次实际结果；没有把独立审查结论替换为 PASS，也不称为缺陷修复或长期可靠性证明。

## 候选与运行条件

a2a 运行起点 `39c838ce8041d48a452a88c4ffa22c5b00efe8e6`，代码候选 `1279adb73c06308fc71eebf35002628730f320d5`；恢复、交付 helper、转接器、oracle、候选与合同源码和恢复规格逐字节相同。完整 `acceptance/` 与该候选无 diff。fork 五轮均为 `28e2f1b4ca6634d4faba9bd921a55a51640407e4`，门禁源码、CLI、合同、构建入口和 bun.lock 与原 `d3b5bcc` 一致。绑定和源快照在 `candidate-source-binding.json`、`a2a-sources/` 与 `fork-sources/`。

B 部分对照已由主控确认结束。本轮没有施加 CPU 负载、启动构建或加载计时钩子；每轮前后保存 top 两次采样、只含命令名的 ps 和 df。实际快照的 CPU idle 范围为 3.17%～82.73%；快照中的进程信息和内存、swap、磁盘记录均保留，不把这些快照当作全时段监控。未停止其他进程，未读写用户 Codex/Synara 数据，未启动模型或 push。

## 五轮结果

每次使用新的 /tmp 隔离 fixture；上一轮实际完成并确认通过后才启动下一轮。各目录均包含 command.json、trace.json、stdout/stderr、machine-before/after.json 和完整 fixture 归档。下表时长为外部单调时钟，包含整个 suite，不是单个忙调用：

| 顺序 | 结果 | suite 时长（秒） | CPU idle 快照范围 | 原始目录 |
| --- | --- | ---: | --- | --- |
| 1 | PASS，9/9，0 failure / 0 error | 31.156 | 76.10%～81.84% | `sequential-01/round-01/` |
| 2 | PASS，9/9，0 failure / 0 error | 31.686 | 75.59%～81.80% | `sequential-01/round-02/` |
| 3 | PASS，9/9，0 failure / 0 error | 31.405 | 73.17%～82.73% | `sequential-01/round-03/` |
| 4 | PASS，9/9，0 failure / 0 error | 29.593 | 10.80%～81.42% | `sequential-01/round-04/` |
| 5 | PASS，9/9，0 failure / 0 error | 32.822 | 3.17%～39.52% | `sequential-01/round-05/` |

原并发 verify/integrate 2 秒断言在两项活跃锁场景中共观察 20 次，返回时间为 0.176～0.188 秒，全部小于 2 秒；实际拒绝仍为 operation_busy。原恢复场景还覆盖真实 verify 中断、CAS 前/后中断、外部引用改变/删除、撤销和规格变化。35 次 SIGKILL 注入均在保存的本次 Popen PID、原生 CLI 路径、state/task 身份核对后执行，退出 -9 且未继续存活；不涉及 Herdr 或其他任务。

新的通过记录只证明这五轮在记录条件下满足原合同。它不解释首轮两个并发 CLI 同时超过 2 秒的历史结果，不将负载/I/O/内存推断补称为根因。

## 保留的异常与接受边界

原失败保留在 `../after-recovery/`，原独立审查 FAIL 保留在 `../独立审查.md`。160 次计时观察和时钟先导失败保留在 `../timing-01/`，全部没有改写。旧报告的当时 INCOMPLETE / NO_GO 是日期记录；本次 PASS 来自主控明确的接受策略及满足该策略的五轮证据。

根据决定 02，将“恢复忙拒绝的一次未复现超时，原因未知，再现时用单调时钟标记定位”记入项目地图 fog。没有增加重试、第二门禁或放宽断言。T-040 只接受 A 部分；第一次日常派发与整体切换仍由主控执行。

原 /tmp 根目录和 Git/worktree 均保留，归档不跟随 symlink，未登记 gitlink。模型与受管 worker attempt/fence 未获得新的可核对身份，不编造；测试 task、attempt、session_id、fence、spec_rev 和完整代码提交均在各轮 trace 内。

## 复现与收尾

```sh
python3 -B evidence/2026-10-08-batch4/T-040-A/recovery-repeat-01/run-five.py NEW_LABEL
```

label 必须全新。脚本五轮顺序运行，任意一次失败立即停止，不覆盖旧结果。复现应先确认没有其他重负载，并保持绑定的 fork / 验收源码。父命令、环境与版本在 `sequential-01/run-input.json` 和各轮 command.json；汇总为 `summary.json`、`round-results.jsonl`、`validated-results.json`。

中文文本按 UTF-8、无 BOM、LF 回读；源码和原断言无 diff，末次项目地图与 diff 检查另行保存。只提交本轮证据、A 部分 Resolution / checkbox 和指定 fog；不提交主控持续写入的日志。
