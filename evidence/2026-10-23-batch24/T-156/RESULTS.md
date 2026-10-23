# T-156-1 / a1 交回决定

状态：**INCOMPLETE / NEEDS-DECISION**。已完成两个旧入口在当前起点的实跑取证和逐项覆盖对照；发现唯一守护者后按卡停止删除。两个目标文件、HISTORICAL.md、产品代码及其他测试均未修改。

- 起点：`8933ee0f4e4667a6f927e18975fe2cb8cc58729b`；分支 `exec/t156`；worker `b24-t156`。
- [BASELINE.json](BASELINE.json)：主控 #26 沙箱外实跑结果的小摘要。legacy runner exit 1 / INCOMPLETE；其中正常 tracer 七条断言通过，但四个旧变异均未运行。quality bootstrap exit 0 / PASS，四项通过。原始总脚本 rc=0 仅说明采集完成。
- [COVERAGE.md](COVERAGE.md)：逐项检查、现行具体断言、覆盖差异、历史证据版本和未重跑边界。
- [local-checks-01.json](local-checks-01.json)：目标文件无修改、四个相关模块实际 import、引用核对、脚本 AST 与 UTF-8 无 BOM/LF 检查通过。没有删除，删除后回归不适用。
- 上报：`20261023T223604Z-worker:b24-t156-issue-001`，blocking；正文 [issue-unique-guardian.md](issue-unique-guardian.md)。inbox 条目由规定入口追加，不纳入 worker 提交。

唯一直接守护者是 bootstrap 的共享 QualityCase/quality_chain_host 两代 operator 凭据路径与实际创建/清理检查。T-152 覆盖了共享方法并使用专用 host，cards bootstrap 则检查另一条 host 路径。旧 runner 的业务检查已有替代或已废止，但 bootstrap 仍导入它的 run_case；不获准迁移就不能单删 runner。

待主控决定是否保留这部分检查、明确退役，或另行授权迁移。未声称独立验收通过，未 submit 到其他 attempt，也未集成；本轮按卡的 NEEDS-DECISION 分支交回，最终门禁由执行主控处理。

T-088 交接：完整原始 `/private/tmp/t156-baseline-ytdo105d`、失败变异副本 `/private/tmp/t082-boundary-fnhqyya9` 和工作区 `outside-01-rdfqsz3d/SUMMARY.json` 均保留未改写，待主控归档。原始 SUMMARY 内嵌完整 run，未把它当小摘要加入提交；本提交仅保存可复现命令与精简结果。已由旧 runner 自行归档/移除的正常 q76 fixture，其 tar 位于原始 baseline 目录，详情见 BASELINE.json。

项目状态仍为既存 `findings/README.md` stale，超出本任务边界，未修；其余结构问题为 0。此次仅新增调查证据，没有测试候选变更，因此没有发起新一轮 behavioral-acceptance-review；T-152 历史 PASS 不替本轮覆盖或待决定结论背书。
