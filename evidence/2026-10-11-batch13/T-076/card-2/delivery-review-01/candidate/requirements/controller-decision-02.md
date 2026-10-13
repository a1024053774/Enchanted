# T-076-2 执行主控决定 02：手工 claim 回归夹具的来源

时间：2026-10-11；对应 `ISSUE-legacy-claim-provenance.md`、收件箱 `20261011T184331Z-worker:s13-t076-2-issue-001`。

## 结论：批准选项一（夹具准备迁到受控 dispatch），附条件

依据：T-070 规定派出去的活一律是受管任务；`records/scores.jsonl` schema=1 的 launch_id/cli/model/effort 必须来自 worker 实际启动记录，不能凭空补造（PLAN §5.2）。没有受管启动来源的手工 claim 不能产出合规评分，因此门禁拒绝其集成与现有合同一致，不是新的产品取舍。本决定只改夹具准备方式，不放宽生产门禁，不新增 test mode。

条件：

1. 只迁移需要完整集成的旧成功场景的准备步骤；claim 竞争、持久化、任务隔离、fence、撤销、冻结候选等断言保留原真实 claim 入口。Recovery 9 项业务断言、Git/oracle 屏障与 CAS 次数不变。
2. 实施前交准确清单：文件、helper、method、原准备方式与新准备方式，编号续 F05 起；我批准后再改。
3. 新增一条显式反例：手工 claim（无受管启动来源）在合法 review 与评分齐备时，integrate 仍被拒绝、留拒绝事件、引用不动。预期来自本决定与 PLAN §5.2，不取自实现输出；须在已知坏变异体（如跳过 delivery 来源检查）上命中。
4. 夹具报告逐例标明"手工 claim"或"受控 dispatch"，不混称；F04 的证据层标注同样适用。
5. 不伪造 delivery、launch 或 passed 状态。

"手工 claim 怎样打分并集成"若将来需要支持，属于产品合同，由构思主控另定；本卡不做。此结论在 T-076 完成报告中列出，供构思主控知悉。

## reviewer-green-01 结果

沙箱外运行 exit 0，status PASS：reviewer-fault-green 3/3（REVIEW-CREATE/RESTART/RECLAIM 转绿）、reviewer-normal-paths 3/3、completed-review-score-recovery 2/2；无 >5MB 文件。
