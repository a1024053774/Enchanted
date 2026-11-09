# T-259 归档中断修正版

当前交付状态：INCOMPLETE，等待一次针对性独立复审和用户批准安装。此报告接续 RESULTS.md；首候选独立审查是 FAIL，不改写其结论。首次审查和主控复现见 `../review-01/REVIEW.md`、`controller-reproduced.json`。

生产范围仍为 core.ts 原 reclaim 入口与 README。首候选在真实归档后、保存 reclaimed 前中断，重启后的 runtime 不含已归档窗格，导致 unknown_pane。修正版在归档前保存已核对的 stopped 快照及 orchestration_events 位置；重启时只接受相同 task/attempt/launch 在该位置之后的 pane_archived，再走同一创建身份、原 dispatch 和未发送检查。没有归档证据就仍走正常 runtime 读取，不因 unknown_pane 放行。正常门禁完成保存与已有 cleanupAttempt 保持；不改 panes、schema 或公开接口。

这次先固定以下不变量再检查：

1. 只有原 attempt 的完整创建与停止事实允许回收；缺记录、错身份不释放路径。
2. 输入已登记、已发送或未知时拒绝，包括恢复期间新增输入记录。
3. 释放必须发生在可核实的归档之后；早于当前回收意图的归档不能作证。
4. 在停止、归档或完成记录边界中断后，重试完成同一 attempt；不重发任务、不要求已归档 runtime 重新出现。
5. 已完成回收的重试不再调用 stop/archive；脏文件保留，未完成清理可继续。

| 证据 | 结果 |
| --- | --- |
| `green-04.json` | PASS，46 场景、310 项检查、errors=[]。新增归档前中断、归档后中断、脏文件、缺意图、过期归档位置、异 attempt 归档、错 shell、恢复期间输入、完成保存后清理前中断。 |
| `e2e-green-04.json` | PASS，9 项真实 daemon/socket/PTY 普通重启回收检查。 |
| `e2e-archive-gap-01.json` | PASS，11 项真实入口检查，包括真实 pane_archived 落盘后异常、重启、原 attempt 续办及重新派发。 |
| `mutant-session-02.json`、`mutant-input-02.json`、`mutant-release-02.json` | FAIL，原三个已知坏实现仍各自命中业务断言，errors=[]。 |
| `mutant-archive-order-01.json` | FAIL，忽略归档位置后接受过期归档证据，命中必须保留原路径的业务断言，errors=[]。 |
| `regression-t253-02.json`、`regression-t170-fast-02.json` | PASS，修正版重跑原生身份绑定与正常失败启动回收。 |

归档后故障主控先在首候选复现 FAIL，再在修正代码复跑独立脚本得到 PASS；原始脚本归档于 review-01。新维护入口为 `python3 workbench/tests/test_t259_preparing_reclaim_e2e.py --archive-gap --summary <新的输出路径>`。新变异入口为 `python3 workbench/tests/run_t259_checks.py --mutant ignore-archive-order --summary <新的输出路径>`。其余命令见 RESULTS.md，输出使用新文件名。两条 E2E 和完整边界测试都自动清理自己创建的后台、私有 core 和临时夹具。没有模型调用。

结构自查（design-integrity-review，按项目规则由实现者完成）：PASS。`design-scan-02.json` 是定位工具，非通过证明。持久化恢复归 core 门禁负责：它已经拥有创建、attempt、锁与归档记录；补的是同一回收的中断阶段，不增加新 API、异常吞噬或失败重试。仅有原 attempt 的明确完成事实允许省去已完成的 runtime 操作，所有身份与输入拒绝条件重跑。独立审查发现的归档窗口已由真实入口红绿覆盖。首候选自查未发现这一行为缺陷，已明确保留其局限，不冒称独立证明。

Works：310 项边界、普通入口及归档中断入口通过；父版与四种变异可判红。

No regression：定向 T-253、T-170 检查通过；没有全历史套件、完整模型交付或正式安装通过结论。

Risk / undo：原 JSON 解析异常来源仍未知；活进程、缺少证明或有输入的准备会话继续拒收。首候选安装包从未运行或安装，已保存版本和大小后清理。正式应用未改，修正版待复审及用户批准。
