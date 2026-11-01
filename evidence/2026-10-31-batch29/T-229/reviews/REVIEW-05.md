STATUS: FAIL

FINDINGS:

- [P1] [gates/cli.ts:233](/Users/luckye/Documents/Code/a2a/workbench/src/gates/cli.ts:233)、[daemon.ts:1022](/Users/luckye/Documents/Code/a2a/workbench/src/daemon.ts:1022) — 期限只取消客户端连接，后台仍处理已经过期的提交。现存 `r6-request-hangs-claude.json`、`r6b-request-hangs-codex-03.json` 已证明：模型没收到 `failrec`，但 `observed.inputs` 各有一条该文字，`observed.observer="healthy"`。这会为被阻断的提交派生人工介入；Claude 还会在 [panes.ts:2148](/Users/luckye/Documents/Code/a2a/workbench/src/panes.ts:2148) 建立没有真实回合、等不到对应 Stop 的 busy 状态，阻住后续派发。REPORT:79 和注释承认了现象，但没有解决影响。至少应把同一绝对期限传到后台，在记录和回合修改前拒绝过期请求；[测试:228](/Users/luckye/Documents/Code/a2a/workbench/tests/test_t229_worker_input_e2e.py:228) 应检查没有虚假记录和回合，目前这一支提前返回，跳过了这些断言。

EVIDENCE:

- 开始、结束逐字比较：`candidate.files` 范围内的工作区 diff 均等于 `candidate.patch`；HEAD 为 `59815ea30e3811d2e449bf5c67b7c70b050081ec`。
- 已读 T-229、T-206、T-216、前四轮审查、REPORT、候选及直接调用路径。两家钩子配置都是 10 秒（`panes.ts:142、1070`）；8 秒 AbortSignal 经 `transport.ts:31` 销毁连接，异常由 `cli.ts:239` 输出阻断并返回 0。
- `request-hangs` 在测试源码副本的 `handle` 前等待 30 秒（测试:76）。两份 `no-deadline` 摘要均失败于 `unrecorded_submission_not_sent_to_model`，实际模型输入含 `failrec`，属于业务断言失败。
- `unknown_pty_queued` 修订有效：`t108_answer_lifecycle_contracts.mjs:45–54` 实际排入两次输入，首次 PTY 写入抛错，随后断言只写过第一条、第二条未记录。独立运行摘要两边均为 12 PASS、两个 `shell_*` INCOMPLETE。
- `r6-claude.json`、`r6b-codex.json`：编辑、历史重发、派发排除、已认领全文再次提交均通过；`claims=2`、`human_interventions=3`。认领查询见 `panes.ts:538–544`；人工介入仍由 `gates/core.ts:574–617` 在记录事务内派生。
- `r5-agy.json`、`r5-opencode.json` 保留草稿文字及 `{text_uncertain:true}`，没有 keys。红态及认领、重复记录、草稿编辑、阻断和观察状态变异均有对应业务失败。
- 第六轮磁盘写满、启动超时与重跑结果和现存摘要、`runs.log` 一致；未把启动失败算成业务通过。T-108 的 429 项名称及状态集合两边一致，均为 254 PASS。未发现新增重试、兼容分支或平行阻断路径。

LIMITATIONS:

- 未运行测试、启动服务或连接 hc／供应商；未读取已删除的夹具库。
- 8 秒仅从 `requestAt` 起算。stdin 读取、trace 初始化和首次解析在期限外，首段异常仍返回 2（`cli.ts:197–216`）；现存证据没有证明初始化异常或总耗时超过 10 秒时仍能阻断。正常受管 worker 不读取操作员凭据，也未启用 HookTrace。
- 未实测旧库恢复、Tab 补全、Codex 忙中排队；agy/opencode 使用替身。
- REPORT:88 的“复制到第 8 秒、负载约 7.5”未找到现存独立日志支持。`fixtures-status.md` 也未列出 `r6b-*` 摘要中的新夹具目录，无法核实 REPORT:89 所述后续清理状态。