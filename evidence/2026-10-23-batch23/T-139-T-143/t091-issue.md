任务卡要求 test_t091_pane_ipc.mjs 绿态，但此 oracle 在起点 ebbae7bd0 与当前候选上都失败于原有处理器枚举。

位置：workbench/tests/test_t091_pane_ipc.mjs:233，expectedHandlers 未包含当前已有的 a2a:archive-usage、decide-role-request、issues、metrics、records、reflect、retrospective-* 等处理器。

证据：同目录 pane-ipc-baseline-01.json 与 pane-ipc-01.json；两次都在进入本次视图语义检查之前失败。

该文件列为 oracle_paths，worker 不得修改。建议主控单独更新受保护 oracle 或明确验收处置；本 worker 保留失败，不把它记为通过。其余 T-139 检查继续。
