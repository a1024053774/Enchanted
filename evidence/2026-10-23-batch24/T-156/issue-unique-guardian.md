T-156-1/a1：需要构思主控决定，当前停止删除。

已在起点 8933ee0f4e4667a6f927e18975fe2cb8cc58729b 实跑两旧入口：旧 runner exit 1/INCOMPLETE，正常 tracer 七条通过，但第一个旧变异锚点不存在；bootstrap exit 0/PASS，四项全过。详见同目录 BASELINE.json 与 COVERAGE.md。

`workbench/tests/test_t078_quality_host_bootstrap.py:71–100` 是共享 `QualityCase.start_host → quality_chain_host.ts` 两代隔离 operator 凭据创建、state/kind/0600 和清理的唯一直接守护者。T-152 覆盖了 start_host/close_fixture 并使用另一个 host；cards bootstrap 测另一条路径，不能证明这个 host 仍调用创建函数。删除 quality_chain_host.ts 中的 createOperatorCredential 调用是可区分这些入口的静态反例，本轮未注入该变异，不据此声称红态已跑。

bootstrap 在第 16、113 行仍导入/调用旧 runner 的 run_case，因此旧 runner 也不能单删。按卡禁止迁移，两个目标文件均未动，HISTORICAL.md 未改。

建议最小选项：保留唯一守护者；或由构思主控明确退役这部分历史 host 覆盖后删除两文件；若要迁移则需另行授权。当前任务不能自行决定。

另有既存 findings/README.md stale，超出本任务范围，已在会话告知。原始 /private/tmp/t156-baseline-ytdo105d、/private/tmp/t082-boundary-fnhqyya9 与未改写的 outside-01-rdfqsz3d/SUMMARY.json 待主控按 T-088 归档；不在本交付中删除现场。
