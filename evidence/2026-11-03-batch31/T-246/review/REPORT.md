**阻塞**

- `workbench/src/panes.ts:2033`：`pane_status.native_session` 直接返回缓存的 `pane.native`，不核对当前前台。事件顺序：CLI A 已报告会话；A 退出、CLI B 成为前台；下一次 `watchWiring` 复查前读取状态，仍可得到 A 的会话。`native_link` 会先调用 `shellNative` 刷新，因此不能证明单独读取状态安全。现有端到端测试在每次读取 `native()` 前先调用 `link()`（`workbench/tests/test_t246_nested_cli_native_e2e.py:120`、`:129`），掩盖了该顺序。**未运行复现**。
- `workbench/src/panes.ts:374`、`workbench/src/byProcess.ts:20`：重启重建只按 PID 和当前存活状态关联历史报告，不区分进程实例。事件顺序：A 报告后退出，其 PID 被同一终端的新前台 CLI B 复用，B 尚未报告；后台重启时，A 的历史报告因该 PID 当前存活而被保留，并可能作为 B 的深度链接和会话显示。穷举测试明确未建模 PID 复用（`workbench/tests/test_by_process.ts:9`）。**未运行复现**。

**非阻塞**

- `workbench/src/panes.ts:824`：`pane.native` 为 `null` 时，`rememberOpen` 仍回退到旧的 `previous.native_session`。例如 A 的会话曾记录在布局中，A 退出后打开该普通终端，新的 `pane_layout_opened` 仍可记录 A 的会话；这与 `RESULTS.md` 对普通终端 `pane.native` 用途的描述需要区分。**未运行复现**。
- `evidence/2026-11-03-batch31/T-246/RESULTS.md:3` 的总体状态是 **INCOMPLETE**，没有宣称独立审查已通过。红态、两种端到端变异体的 JSON 与报告所述失败位置一致；但重启检查只断言链接，没有独立断言重启后的 `pane_status.native_session`。
- 终端主控身份检查需与普通终端状态分开看：`workbench/src/panes.ts:1429` 的 shell `processInfo` 返回空 `native_session`；本次未运行 T-121/T-133 身份场景，不能仅凭已有回归报告排除所有影响。

**验证与结论**

- 实际运行 `node workbench/tests/test_by_process.ts`：**PASS**，穷举长度 0～6，共 1,111,111 个序列；该结果不覆盖上述 PID 复用及真实状态读取时序。
- 未启动后台、Electron 或 CLI 测试；上述阻塞项均为只读推导，尚需按具体事件顺序复现。

**NO_GO**：当前证据不足以证明所要求的前台会话不变式。
