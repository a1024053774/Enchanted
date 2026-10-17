# 09C 第3场回收材料（只写未跑）

> **主控 #374 追加当前状态：** 本套已逐步执行完，全部PASS、root已删，原签字/输出已入库；下文为#373准备记录，不能再次运行。实际来源：[finish](../09c-attempt-3-cleanup-01/result.json)、[独立审阅](../09c-attempt-3-raw-readback-01/review.json)、[tar核对](../09c-c3-tar-check-01/result.json)、[冻结核对](closeout-frozen-check.json)。大块原件留外置盘，停后SQLite读0。

本场业务与worker原件复核PASS；**归档/回收尚未执行**，不能把本计划写成cleanup PASS。仅使用原owner九身份，capture-owner只扩展evidence_trees，其他字段逐项不变。

root `/private/tmp/t078-2-09c-run-kwp5kj5g`；daemon40012，target shell/leader40103/40105，API ideation/executor40009/40010，ideation shell/CLI40231/40233，executor40818/40819。数值来自原收据，当前存活及PID/argv/lstart/父链由步骤01/06实时双读；worker没有在本机ps实测。caffeinate仅按原窄规则单列，不能替代原受管进程，仍须消失。

执行主控逐项核对后签cleanup-approval.json，再按序整文件执行；不能拼接成跳过签字的自动回收：

1. `01-DRY-RUN.txt`：原九身份/拓扑/批准核对；不采集、不停机、不发信号、不删root。任何不符BLOCKED保留。
2. `02-CAPTURE.txt`：daemon仍活着时，标准raw-retention一致只读事务导出live-rows，捕获全部HTTP请求/响应/meta、完整hooks、目标baseline/received、原许可屏/签字/动作与计时/一次性意图。新增树涵盖本场后生成的完整读屏目录、整个preparation、worker live-06的task-boundary快照和root/permission-intents。认证头从未进入HTTP捕获接口；结构敏感值按原规则脱敏，留字节span映射；不包含HOME、认证文件、环境或原SQLite/WAL。
3. `03-TAR-READBACK.txt`：从tar重新计POST7/1、roots4/1、PermissionRequest3/0，unfinished均空；readback.json签字留空。不能用成功响应数或HTTP日志行数代替POST原件。
4. `04-TAR-CHECK.txt`：同一只读核对器换成tar原件入口，核对请求/SSE/工具/UPS/Stop/三许可、完整屏、原request→relay→stop、早拒绝、>120秒后中断、目标单Esc、无ack、原attempt未reclaim及原clock。仅读tar与已保存owner，不打开现场SQLite。输出09c-c3-tar-check-01；任何缺件或错绑必须失败。
5. 执行主控独立检查tar全部成员/脱敏span、扫描真实凭据、核对04与标准重数。由review-template另写 `09c-attempt-3-raw-readback-01/review.json`，填实际counts、status/credential_scan=PASS并签字；同时另签readback.json。正常业务字段名hook_authorization/turn_authorization和系统提示中的authorization不是认证头，若扫描命中须逐项说明，不能无条件忽略。未审阅不得填PASS。
6. `05-SAVE-MANIFEST.txt`：把轻量bundle.archive.json与逐原件指针树入口保存到本目录；payload留外置盘，每原件自己的pointers/<logical>.archive.json仍保留。
7. `06-FINISH.txt`：先拒绝缺/错tar核对与签字，再调用原标准finish。再次验证全成员类型/字节、源原件稳定、九身份/拓扑；持久独占shutdown-intent后认证daemon_stop→panes.shutdown，正常关闭两Claude/target、确认辅助进程消失；两原API各一次SIGTERM、全部原PID实际缺席。停后仅查文件/归档，SQLite读取0；全过才删exact root。不直接给角色/target/helper发信号，不强杀、不重启、不重复不确定停机、不删slot。

外置staging：`/Volumes/WD-Elements/a2a-evidence/2026-10-11-batch13/T-078/09c-attempt-3-capture-01/`；tar：同批 `09c-attempt-3-raw-01/scene.tar.gz`；逐原件指针在tar父目录pointers。未挂载就拒绝，不回退内盘。所有输出目录全新，原件集合/字节变化即停，不先停机再补归档。

当前现场使用NativeRuntime；daemon/API的创建者已退出、由launchd收养，不是排练DirectChildRuntime，不接管外来PID waitpid。Z只保存原ps并等待实际缺席，持续存在则BLOCKED。

归档与回收实跑后，主控将新输出/签字再提交并更新终审冻结候选；本轮候选不冒称已归档或已回收。原第1/2场与探针/排练失败均保留，不因第3场PASS改判。
