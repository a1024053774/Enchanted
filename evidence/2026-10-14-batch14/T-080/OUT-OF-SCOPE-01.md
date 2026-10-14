# 范围外发现：T-073 启动 argv 断言与当前启动器不一致

状态：INCOMPLETE（静态发现，非阻塞；未运行该启动/尾注场景）。发现者：T-080 worker `s14-t080`，当前任务 `T-080/a1`。

位置：`acceptance/test_herdr_traceability_e2e.py` 的 `Contract.assert_trailers` 仍断言启动 argv 含 `service_tier="fast"`，且完整列表没有 `--no-daemon`；当前 `scripts/launch-worker` 明确添加 `--no-daemon`，默认 `--service-tier default`。这些差异在 T-080 开工版本已存在，本票没有修改启动参数或上述旧断言。

影响：将来运行整个 T-073 套件时，调用该辅助断言的启动/尾注测试可能因旧期望拒绝当前策略。它不属于本票的验收文件保护或打分 schema 决定；本 worker 不调整该断言。本票全量阶段仅运行其中三个打分方法，所用事实夹具已补 `oracle`，并新增写入 schema=2 的业务断言；其余 T-073 启动/尾注方法未运行，不计入通过范围。

建议：主控按当前启动策略另开缺陷级 ticket，确认正确 argv 后保留当前失败并修正相应测试；不把本条静态发现当作实跑失败，也不通过更改当前启动参数来迎合旧断言。

按本会话要求，沙箱外写入交主控。需登记到主仓收件箱时，由主控运行（无需阻塞 T-080）：

```sh
scripts/inbox --root /Users/luckye/Documents/Code/a2a send --from worker:s14-t080 --to triage --kind issue --title 'T-073 启动 argv 断言与当前启动器不一致' --body-file /Users/luckye/Documents/Code/a2a-wt-t080/evidence/2026-10-14-batch14/T-080/OUT-OF-SCOPE-01.md --ref file:acceptance/test_herdr_traceability_e2e.py#L117
```
