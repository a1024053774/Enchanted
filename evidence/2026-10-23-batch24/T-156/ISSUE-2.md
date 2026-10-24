# T-156-2：范围外历史脚本仍导入旧 runner

状态：**INCOMPLETE，待执行主控判断验收范围**。不阻塞卡内代码与本地验证；全仓“无残留导入”的完成条件尚未满足。

全仓 `git grep` 发现 `evidence/2026-10-16-batch16/T-090/run-host.py:215` 仍执行 `from run_t082_boundary import materialize`。该脚本第 213～230 行运行旧启动变异（包括已经废止的网络关闭契约），不是现行 T-152 runner。删除旧文件后，历史脚本混用当前源码会在该处导入失败。此前 COVERAGE.md 只检查了 workbench/scripts/acceptance，这个历史脚本未包含在当时的调用者结论里。

任务卡只允许修改新测试、删除两旧文件、HISTORICAL.md 与本证据目录，禁止修改其他 evidence 和 `.project-map/**`。因此未修改 T-090，也未用 `scripts/inbox send` 写入被禁止的 `.project-map/inbox/`；在本允许目录保存问题正文，并通过本次主控会话请求裁定。

建议主控确认“无残留导入”是否限定现行入口，历史脚本按日期记录保留、复跑时取得当时 revision；若要求全仓字面无导入，则需另行授权处理该历史脚本，不能在本卡中自行改写。完整检索命令与输出见 [LOCAL-2.json](LOCAL-2.json)。

## 主控 #42 裁定

执行主控原文：“ticket 验收写的是‘删除不得让任何**现行**测试的导入断掉’。evidence/2026-10-16-batch16/T-090/run-host.py 是日期证据脚本，按其当时 revision 复跑，不算现行入口；不改它。”

按此裁定处理：T-090 原文件保持原样，HISTORICAL.md 注明历史引用与复跑 revision 要求。该问题不再阻塞现行入口验收；原发现及原始检索输出保留。
