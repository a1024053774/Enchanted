# T-040 A：主控决定 02 复验与负载资格（2026-10-08）

**INCOMPLETE，需要主控决定；没有接受 A。** 同一候选上第一组连续五轮恢复 9 项全部通过，45/45；负载复核发现第 4 轮末与第 5 轮前后有 Token Monitor / TokNotch 的重负载。之后在空闲窗口启动第二组，其第 1 轮仍为 9/9，但结束快照 CPU idle 降至 15.88%，环境门控停止后续轮次。共 54/54 业务通过，未出现新的业务失败；要求的“没有其他重负载时连续五轮”未满足，不能自行取消这个条件。

原首轮恢复失败、独立审查 FAIL 与计时证据保持原样。T-040 仍 open，A 的删除/原生验收复选框未勾选，没有修改地图中的接受状态。没有改产品、原断言或验收，也没有自动重试、停止用户应用或启动第三组。

## 同一候选与真实入口

a2a 运行起点 `39c838ce8041d48a452a88c4ffa22c5b00efe8e6`，代码候选 `1279adb73c06308fc71eebf35002628730f320d5`；恢复、helper、转接器、oracle、候选/合同及恢复规格逐字节相同，完整 acceptance 目录与候选无 diff。两组的 fork 均为 `28e2f1b4ca6634d4faba9bd921a55a51640407e4`，门禁源码、CLI、合同、构建入口与 bun.lock 和原 `d3b5bcc` 相同。绑定及源快照在 `candidate-source-binding.json`、`a2a-sources/`、`fork-sources/`。

每轮直接执行原 `acceptance/test_recovery_e2e.py --run-suite`。生产门禁、真实 Git、SQLite、分页 oracle 与受控故障屏障均保留；原 2 秒忙拒绝断言没有放宽，未加载计时钩子或 mutant。24 次实际忙拒绝观察为 0.176～0.240 秒，全部小于 2 秒。42 次 SIGKILL 均只针对夹具创建并核对的原生 CLI，返回 -9 且不再存活；未涉及 Herdr 或其他任务。

## 实际顺序运行结果

每轮前后保存 top 两次采样、仅含命令名的 ps 和 df。下表 idle 使用 top 一秒间隔的第二次采样；第一采样及全部原始输出仍保留。快照不是完整的持续监控。

| 组 / 轮 | 业务结果 | suite 时长（秒） | 开始 / 结束 CPU idle | 环境观察 |
| --- | --- | ---: | --- | --- |
| sequential-01 / 1 | PASS，9/9，0 failure / error | 31.156 | 81.84% / 81.70% | 快照未见重负载 |
| sequential-01 / 2 | PASS，9/9，0 failure / error | 31.686 | 79.74% / 81.80% | 快照未见重负载 |
| sequential-01 / 3 | PASS，9/9，0 failure / error | 31.405 | 82.73% / 82.19% | 快照未见重负载 |
| sequential-01 / 4 | PASS，9/9，0 failure / error | 29.593 | 81.42% / 10.80% | 结束时 Token Monitor 739.1% CPU |
| sequential-01 / 5 | PASS，9/9，0 failure / error | 32.822 | 12.28% / 15.19% | 开始时 Token Monitor 708.6%；结束时 TokNotch 333.3% / 355.5% CPU |
| sequential-02 / 1 | PASS，9/9，0 failure / error | 53.506 | 78.87% / 15.88% | 结束时 CPU idle 15.88%；其他 Node 进程 84.5% / 65.4% / 53.8% / 47.2% |

第一组五轮没有任何业务失败；其 `sequential-01/summary.json` 的 PASS 仅是业务结果。复核负载后，发现初步接受结论过早，已明确撤回，详见 `environment-qualification.json`。初步说明和数字核对记录原样保留为 `provisional-RESULTS-not-accepted.md`、`provisional-validated-results.json`，不作为接受结论；最终数字与环境资格为 `validated-results.json`。

第二组开始前的新快照 CPU idle 77.46%，没有单个 ≥100% CPU 的其他进程。为不重复遗漏环境条件，仅启动一组新的连续运行，并加保守环境门控：每轮前后的一秒区间 idle ≥70%，且无其他单个 ≥100% CPU 进程。原业务测试与 2 秒断言不改。第一轮从 idle 78.87% 开始，9/9 完成后 idle 降至 15.88%，因此停止，不启动后四轮或第三组。

第二组 `summary.json` 的 `failed_round=1` 表示资格门控未通过，不是测试失败：原测试 exit 0、9/9、0 failure/error，明确记录 `business_passed=true`、`workload_eligible=false`。结束快照中额外 Node 进程属于 Homebrew Node 26.5.0，不是 fork 入口固定的 Node 24.13.1；未核对其任务来源，不归因于 Token Monitor、B 部分或主控。没有对这些进程发信号。

## 交主控决定

[决定 02](../controller-decision-02.md) 第 2 条要求在没有其他重负载时完成连续五轮。B 部分已结束，但其他用户应用的负载在运行期间出现。现有 54 项通过可以保留为实际业务证据，不能自行替换规定的运行条件。

最小选项：主控明确接受本轮在额外负载下仍 54/54 的证据；或安排获授权的空闲窗口，再执行规定的五轮。是否临时暂停 Token Monitor / TokNotch 或其他外部任务由主控决定，worker 不自行回收它们。原根因仍 unknown，旧首轮失败与独立审查 FAIL 不改判，不宣布修复或长期可靠性提升。

原先尝试新增的接受 checkbox、Resolution 和地图 fog 已在提交前撤回，没有发布未满足条件的接受状态；本交付仅追加实际复验与未完成原因。

## 证据与复现

`sequential-01/` 五轮、`sequential-02/` 一轮各含 command.json、完整 stdout/stderr、trace、机器快照和 tar.gz。原 /tmp 目录及 Git/worktree 全部保留，没有登记 gitlink。真实 task、attempt、session_id、fence、spec_rev 与信号核对在 trace 中；没有新的可核对模型或 worker 受管 attempt/fence 信息，不编造。

两组输入脚本分别冻结为 `sequential-01-run-input.py`（原五轮记录器）、`sequential-02-run-input.py`（加环境门控的记录器）。当前 run-five.py 与第二组输入一致。它不在业务失败后自动重试，资格失败也立即停止。复现必须使用新 label，并先由主控解决运行条件：

```sh
python3 -B evidence/2026-10-08-batch4/T-040-A/recovery-repeat-01/run-five.py NEW_LABEL
```

本轮没有改 fork、验收、README、用户配置或历史失败记录，没有模型调用或 push。中文文件按 UTF-8、无 BOM、LF 回读；项目地图状态与 diff 检查保存于本目录。只提交本轮证据和实际 Resolution，主控日志保持其原有修改。
