# T-212 独立审查第一轮原文（agy，gemini-4-argon-high，--mode auto，只读）

来源：agy 会话 4b1b5b95-1a3d-45e5-af36-179f39acd6f4 的最后一步回复，2026-10-31 由主控从本地会话库导出；账号邮箱已脱敏。主控核对见 REVIEW-agy-r1-controller-check.md。

---

# T-212 独立审查报告（只读核查）

---

## 一、审查意见汇总（按严重度排列）

### 1. [阻塞] Core 自身崩溃（`screen: "inexact"` 与 `hc_connection_lost`）未被当作终端已死/未知报错处理，反而冒充正常恢复并在侧栏维持运行/空闲状态

- **文件与行号**：
  - [`panes.ts`](file:///Users/luckye/Documents/Code/a2a-review/T-212-r1/candidate/workbench/src/panes.ts#L625-L636)（[`PaneRegistry.recover`](file:///Users/luckye/Documents/Code/a2a-review/T-212-r1/candidate/workbench/src/panes.ts#L611-L645)）
  - [`panes.ts`](file:///Users/luckye/Documents/Code/a2a-review/T-212-r1/candidate/workbench/src/panes.ts#L325-L366)（[`PaneRegistry.attachShell`](file:///Users/luckye/Documents/Code/a2a-review/T-212-r1/candidate/workbench/src/panes.ts#L325-L366)）
  - [`panes.ts`](file:///Users/luckye/Documents/Code/a2a-review/T-212-r1/candidate/workbench/src/panes.ts#L1697-L1709)（[`PaneRegistry.status`](file:///Users/luckye/Documents/Code/a2a-review/T-212-r1/candidate/workbench/src/panes.ts#L1697-L1709)）
  - [`panes.ts`](file:///Users/luckye/Documents/Code/a2a-review/T-212-r1/candidate/workbench/src/panes.ts#L2114-L2117)（[`PaneRegistry.terminalAlive`](file:///Users/luckye/Documents/Code/a2a-review/T-212-r1/candidate/workbench/src/panes.ts#L2114-L2117)）
  - [`sidebar.ts`](file:///Users/luckye/Documents/Code/a2a-review/T-212-r1/candidate/workbench/src/sidebar.ts#L224-L225)、[`sidebar.ts`](file:///Users/luckye/Documents/Code/a2a-review/T-212-r1/candidate/workbench/src/sidebar.ts#L240-L241)（[`sidebarSnapshot`](file:///Users/luckye/Documents/Code/a2a-review/T-212-r1/candidate/workbench/src/sidebar.ts#L170-L303)）
  - [`round2-crash-observation.json`](file:///Users/luckye/Documents/Code/a2a-review/T-212-r1/evidence/round2-crash-observation.json#L1-L16)
- **为什么**：
  - [ticket.md](file:///Users/luckye/Documents/Code/a2a-review/T-212-r1/ticket.md#L25) 明确要求：“core 自身崩溃时历史已丢、`screen` 为 `inexact`，后台把这种情况当作终端已死/未知报错，不冒充完整恢复。”[spec/hc-runtime-2026-10-31.md](file:///Users/luckye/Documents/Code/a2a-review/T-212-r1/spec/hc-runtime-2026-10-31.md#L40) 也明确规定：“后台把 `screen: \"inexact\"` 或丢失原终端当作 core 崩溃，按‘运行中连接断开、结果未知’处理，不冒充完整恢复。”
  - T-211 实测结果（[spec/RESULTS.md](file:///Users/luckye/Documents/Code/a2a-review/T-212-r1/spec/RESULTS.md#L32)）已证实：当 `hc core` 被 `SIGKILL` 后拉起新 core 收养 holder 终端时，该终端仍返回 `state === "live"`、PID 不变，但 `screen === "inexact"` 且 core 侧历史已丢。
  - 候选代码在两处路径上违反了该要求：
    1. **重连收养路径（`screen: "inexact"`）**：[`PaneRegistry.recover`](file:///Users/luckye/Documents/Code/a2a-review/T-212-r1/candidate/workbench/src/panes.ts#L625-L636) 只检查了 `terminal && terminal.pid === pid`，**未检查 `terminal.screen === "exact"`**，直接调用 `attachShell()` 并写 `shell_reattached`；在 [`PaneRegistry.attachShell`](file:///Users/luckye/Documents/Code/a2a-review/T-212-r1/candidate/workbench/src/panes.ts#L330-L366) 中，第 330 行先无条件向 `traces/<launch>/pty.raw` 追加 `"\x1bc"`（导致前端 xterm.js 回放时把崩溃前已落盘的旧输出也一并清空），第 364-365 行对 `terminal.screen !== "exact"` 仅写一条 `shell_screen_inexact` 事件，既不设 `pane.failed`，也不报错，而是将该终端作为 `lifecycle: "running", failed: null` 的正常终端放回 `this.panes`，完全冒充了完整恢复。
    2. **运行中断开路径（`hc_connection_lost`）**：当后台运行期间 core 崩溃断开 viewer socket 时，[`attachShell`](file:///Users/luckye/Documents/Code/a2a-review/T-212-r1/candidate/workbench/src/panes.ts#L359-L362) 调 `this.recordFailure(pane, "hc_connection_lost", error)` 设置了 `pane.failed`，但 `pane.stopped` 仍为 `false`。[`PaneRegistry.status`](file:///Users/luckye/Documents/Code/a2a-review/T-212-r1/candidate/workbench/src/panes.ts#L1699) 只看 `!pane.stopped` 不看 `pane.failed`，仍返回 `lifecycle: "running"`；[`PaneRegistry.terminalAlive`](file:///Users/luckye/Documents/Code/a2a-review/T-212-r1/candidate/workbench/src/panes.ts#L2116) 也仍返回 `true`；[`sidebarSnapshot`](file:///Users/luckye/Documents/Code/a2a-review/T-212-r1/candidate/workbench/src/sidebar.ts#L224-L241) 对主控终端和普通项目终端均未检查 `pane?.failed`，导致 core 崩溃断开后侧栏仍把终端标为 `idle` 或 `running`，而不是 `unknown`。
    3. 证据文件 [`round2-crash-observation.json`](file:///Users/luckye/Documents/Code/a2a-review/T-212-r1/evidence/round2-crash-observation.json#L1-L16) 自身也标记为 `"status": "INCOMPLETE"`。
- **建议怎么改**：
  - 在 [`panes.ts:629`](file:///Users/luckye/Documents/Code/a2a-review/T-212-r1/candidate/workbench/src/panes.ts#L629) 及 [`attachShell`](file:///Users/luckye/Documents/Code/a2a-review/T-212-r1/candidate/workbench/src/panes.ts#L326)（写入 `"\x1bc"` 之前）检查 `terminal.screen === "exact"`；若 `terminal.screen !== "exact"`，在 `recover()` 中走失败分支（记录 `shell_screen_inexact` 与 `shell_exit_unconfirmed`，不向 `pty.raw` 追加 `"\x1bc"`，不挂载进 `this.panes`，不写 `shell_reattached`）。
  - 在 [`panes.ts:1699`](file:///Users/luckye/Documents/Code/a2a-review/T-212-r1/candidate/workbench/src/panes.ts#L1699) 中，当 `pane.record.role === "shell" && pane.failed` 时返回 `lifecycle: "unknown"`；在 [`panes.ts:2116`](file:///Users/luckye/Documents/Code/a2a-review/T-212-r1/candidate/workbench/src/panes.ts#L2116) [`terminalAlive`](file:///Users/luckye/Documents/Code/a2a-review/T-212-r1/candidate/workbench/src/panes.ts#L2114-L2117) 中加入 `!pane.failed`；在 [`sidebar.ts:224-225, 240-241`](file:///Users/luckye/Documents/Code/a2a-review/T-212-r1/candidate/workbench/src/sidebar.ts#L224-L241) 中，当 `pane?.failed` 或 `pane?.lifecycle !== "running"` 时状态返回 `"unknown"`。
  - 在 [`test_t212_shell_hc_e2e.py`](file:///Users/luckye/Documents/Code/a2a-review/T-212-r1/candidate/workbench/tests/test_t212_shell_hc_e2e.py) 中增加对 `hc core` 发 `SIGKILL` 后的端到端验证，断言运行中断开与重连遇到 `screen: "inexact"` 时均报错并标为 `unknown`，不冒充恢复。

---

### 2. [阻塞] 验收条目 5 缺少“在项目终端里启动真实 Claude Code、经 `a2a request` 申请主控、批准生效且侧栏状态不出现新‘未知’”的真实入口证据

- **文件与行号**：
  - [ticket.md](file:///Users/luckye/Documents/Code/a2a-review/T-212-r1/ticket.md#L33)（验收条目 5）
  - [`evidence/REPORT.md`](file:///Users/luckye/Documents/Code/a2a-review/T-212-r1/evidence/REPORT.md#L154)
  - [`test_t121_role_request_e2e.py`](file:///Users/luckye/Documents/Code/a2a-review/T-212-r1/candidate/workbench/tests/test_t121_role_request_e2e.py#L60-L61)、[`test_t121_role_request_e2e.py`](file:///Users/luckye/Documents/Code/a2a-review/T-212-r1/candidate/workbench/tests/test_t121_role_request_e2e.py#L248-L382)
  - [`test_t107_live_sidebar_e2e.py`](file:///Users/luckye/Documents/Code/a2a-review/T-212-r1/candidate/workbench/tests/test_t107_live_sidebar_e2e.py#L89-L110)、[`test_t107_live_sidebar_e2e.py`](file:///Users/luckye/Documents/Code/a2a-review/T-212-r1/candidate/workbench/tests/test_t107_live_sidebar_e2e.py#L177)
  - [`scripted_claude.py`](file:///Users/luckye/Documents/Code/a2a-review/T-212-r1/candidate/workbench/tests/scripted_claude.py#L256-L277)（[`request_confirmed_controller`](file:///Users/luckye/Documents/Code/a2a-review/T-212-r1/candidate/workbench/tests/scripted_claude.py#L256-L277)）
- **为什么**：
  - 验收条目 5 要求：“在项目终端里启动 Claude Code 并经 `a2a request` 申请主控、界面批准后生效（T-119 流程不变）；侧栏状态与改前一致或更准，不出现新的‘未知’。”
  - Worker 在 [`evidence/REPORT.md:154`](file:///Users/luckye/Documents/Code/a2a-review/T-212-r1/evidence/REPORT.md#L154) 将 [`t121-regression-04/summary.json`](file:///Users/luckye/Documents/Code/a2a-review/T-212-r1/evidence/t121-regression-04/summary.json) 与 [`t107-regression-04/summary.json`](file:///Users/luckye/Documents/Code/a2a-review/T-212-r1/evidence/t107-regression-04/summary.json) 列为该条证据，但核对源码与原始输出后发现：
    1. 在 [`test_t121_role_request_e2e.py:60-61`](file:///Users/luckye/Documents/Code/a2a-review/T-212-r1/candidate/workbench/tests/test_t121_role_request_e2e.py#L60-L61) 中，`claude` 只是一个两行假 shell 脚本（把参数写进文件即退出）；第 254-352 行的 `a2a request executor` 是直接在 zsh 命令行里执行的，没有 `CLAUDECODE=1` 和 `CLAUDE_CODE_SESSION_ID`，请求体里 `cli: null, native_session: null`。第 380-382 行只断言了 `role_label == "执行主控"`，根本未检查 `state`（此时因 `cli: null` 侧栏状态实际为 `"unknown"`）。
    2. 在 [`test_t107_live_sidebar_e2e.py:89-110`](file:///Users/luckye/Documents/Code/a2a-review/T-212-r1/candidate/workbench/tests/test_t107_live_sidebar_e2e.py#L89-L110) 中，[`request_confirmed_controller`](file:///Users/luckye/Documents/Code/a2a-review/T-212-r1/candidate/workbench/tests/scripted_claude.py#L256-L277) 是由 Python 测试脚本直接向 `control.sock` 发不带 `cli` 的 `role_request`，根本没有在项目终端里启动 Claude Code；且 [`test_t107_live_sidebar_e2e.py:177`](file:///Users/luckye/Documents/Code/a2a-review/T-212-r1/candidate/workbench/tests/test_t107_live_sidebar_e2e.py#L177) 恰恰断言两个主控终端的状态都是 `"unknown"`（`"terminal_controllers_unknown_not_upgraded": True`）。
    3. 在 [`test_t184_unwired_cli_e2e.py:134-161`](file:///Users/luckye/Documents/Code/a2a-review/T-212-r1/candidate/workbench/tests/test_t184_unwired_cli_e2e.py#L134-L161) 中，终端 B 绕过包装脚本用绝对路径启动 Claude Code（侧栏为 `"unknown"`），终端 N 虽经包装脚本启动了真实 Claude Code 却未执行 `a2a request`（侧栏也为 `"unknown"`）。
  - 因此，整个 `evidence/` 中没有任何一次测试运行覆盖了“在 hc 项目终端里经包装脚本启动真实 Claude Code（配合本地脚本化模型）→ 会话内执行 `a2a request` → 界面批准并确认生效 → 侧栏状态为 `running`/`idle` 而非 `unknown`”。
- **建议怎么改**：
  - 在 [`test_t212_shell_hc_e2e.py`](file:///Users/luckye/Documents/Code/a2a-review/T-212-r1/candidate/workbench/tests/test_t212_shell_hc_e2e.py)（或独立端到端测试）中，在 hc 项目终端里通过 [`workbench/terminal/bin/claude`](file:///Users/luckye/Documents/Code/a2a-review/T-212-r1/candidate/workbench/terminal/bin/claude) 包装脚本启动真实 Claude Code CLI（连接本地脚本化 Messages 接口），在 Claude 工具调用回合内执行 `a2a request executor`，经批准与 `confirm` 后，断言侧栏中该主控行的 `cli == "claude"`，且状态在回合中为 `"running"`、在 `Stop` hook 触发后变为 `"idle"`，全程不出现 `"unknown"`。

---

### 3. [阻塞] [`workbench/README.md`](file:///Users/luckye/Documents/Code/a2a-review/T-212-r1/candidate/workbench/README.md) 与 [`roleRequests.ts`](file:///Users/luckye/Documents/Code/a2a-review/T-212-r1/candidate/workbench/src/roleRequests.ts) 注释未同步更新，文档内部自相矛盾且与代码行为不一致

- **文件与行号**：
  - [`workbench/README.md`](file:///Users/luckye/Documents/Code/a2a-review/T-212-r1/candidate/workbench/README.md#L14) vs [`workbench/README.md`](file:///Users/luckye/Documents/Code/a2a-review/T-212-r1/candidate/workbench/README.md#L210)、[`workbench/README.md`](file:///Users/luckye/Documents/Code/a2a-review/T-212-r1/candidate/workbench/README.md#L316-L317)
  - [`roleRequests.ts`](file:///Users/luckye/Documents/Code/a2a-review/T-212-r1/candidate/workbench/src/roleRequests.ts#L60)
- **为什么**：
  - Worker 在 [`workbench/README.md:14`](file:///Users/luckye/Documents/Code/a2a-review/T-212-r1/candidate/workbench/README.md#L14) 新增了：“后台重启只断开项目终端的 viewer，接回原 hc 终端与原 pid；终端专用 socket 地址保持不变，`a2a` 身份继续有效。”
  - 但同一份文档的 [`workbench/README.md:316-317`](file:///Users/luckye/Documents/Code/a2a-review/T-212-r1/candidate/workbench/README.md#L316-L317)（`## 普通终端` 节）仍保留改前旧描述：“后台重启保留普通终端的打开集，但不自动拉起 zsh；历史快照返回 `lifecycle: ended`。”这与第 14 行、[`panes.ts:625-635`](file:///Users/luckye/Documents/Code/a2a-review/T-212-r1/candidate/workbench/src/panes.ts#L625-L635) 以及 [`test_t104_shell_e2e.py:271`](file:///Users/luckye/Documents/Code/a2a-review/T-212-r1/candidate/workbench/tests/test_t104_shell_e2e.py#L271)（断言后台重启后 `snapshot["pane"]["lifecycle"] == "running"`）直接矛盾。
  - 同时，[`workbench/README.md:210`](file:///Users/luckye/Documents/Code/a2a-review/T-212-r1/candidate/workbench/README.md#L210) 仍写着：“终端关闭或后台重启后身份结束，侧栏保留最近一次确认生效的主控角色并标‘已结束’”，[`roleRequests.ts:60`](file:///Users/luckye/Documents/Code/a2a-review/T-212-r1/candidate/workbench/src/roleRequests.ts#L60) 注释也仍写着 `// A closed terminal or a restarted daemon ends every role request it held.`。而在代码中，[`RoleRequests`](file:///Users/luckye/Documents/Code/a2a-review/T-212-r1/candidate/workbench/src/roleRequests.ts#L61-L78) 通过 `this.alive(roleRequest.launch)`（即 [`panes.terminalAlive(launch)`](file:///Users/luckye/Documents/Code/a2a-review/T-212-r1/candidate/workbench/src/panes.ts#L2114-L2117)）判断角色是否结束；后台重启接回原 hc 终端后 `terminalAlive` 返回 `true`，主控身份继续有效（[`test_t212_shell_hc_e2e.py:224-228`](file:///Users/luckye/Documents/Code/a2a-review/T-212-r1/candidate/workbench/tests/test_t212_shell_hc_e2e.py#L224-L228) 也正是这样验证的）。
- **建议怎么改**：
  - 更新 [`workbench/README.md:210`](file:///Users/luckye/Documents/Code/a2a-review/T-212-r1/candidate/workbench/README.md#L210)、[`workbench/README.md:316-317`](file:///Users/luckye/Documents/Code/a2a-review/T-212-r1/candidate/workbench/README.md#L316-L317) 以及 [`roleRequests.ts:60`](file:///Users/luckye/Documents/Code/a2a-review/T-212-r1/candidate/workbench/src/roleRequests.ts#L60) 的注释，统一改为：后台重启接回原 hc 终端并保持 `lifecycle: running` 与已生效主控身份；仅在终端关闭或原 hc 终端无法完整恢复时结束身份。

---

### 4. [非阻塞] [`panes.ts`](file:///Users/luckye/Documents/Code/a2a-review/T-212-r1/candidate/workbench/src/panes.ts) 保留了旧路径兼容条件分支与不可达的死代码

- **文件与行号**：
  - [`panes.ts`](file:///Users/luckye/Documents/Code/a2a-review/T-212-r1/candidate/workbench/src/panes.ts#L625-L642)（[`PaneRegistry.recover`](file:///Users/luckye/Documents/Code/a2a-review/T-212-r1/candidate/workbench/src/panes.ts#L611-L645)）
  - [`panes.ts`](file:///Users/luckye/Documents/Code/a2a-review/T-212-r1/candidate/workbench/src/panes.ts#L2259-L2286)（[`PaneRegistry.terminate`](file:///Users/luckye/Documents/Code/a2a-review/T-212-r1/candidate/workbench/src/panes.ts#L2256-L2293)）
- **为什么**：
  - 在 [`panes.ts:625`](file:///Users/luckye/Documents/Code/a2a-review/T-212-r1/candidate/workbench/src/panes.ts#L625) 中，[`startShell`](file:///Users/luckye/Documents/Code/a2a-review/T-212-r1/candidate/workbench/src/panes.ts#L254-L323) 写下的 `shell_created` 事件必定携带 `hc_terminal` 与 `hc_session`。此处写 `if (start?.data.hc_terminal)` 并在不满足时滑落到第 638-642 行的旧进程检查路径，属于对旧无-hc 事件格式的静默兼容分支。
  - 在 [`panes.ts:2259-2272`](file:///Users/luckye/Documents/Code/a2a-review/T-212-r1/candidate/workbench/src/panes.ts#L2259-L2272) 中，`if (pane.record.role === "shell")` 分支末尾已经 `return`，但第 2275 行和第 2285 行仍残留了改前的两行 `if (pane.record.role === "shell") await this.confirmShellExit(pane);` 死代码。
- **建议怎么改**：
  - 将 [`panes.ts:625`](file:///Users/luckye/Documents/Code/a2a-review/T-212-r1/candidate/workbench/src/panes.ts#L625) 的 `if (start?.data.hc_terminal)` 改为 `check(typeof start?.data.hc_terminal === "string" && start.data.hc_terminal.length > 0, "shell_hc_terminal_missing")`（缺失即报错走失败分支，不滑落旧分支）；删除 [`panes.ts:2275`](file:///Users/luckye/Documents/Code/a2a-review/T-212-r1/candidate/workbench/src/panes.ts#L2275) 与 [`panes.ts:2285`](file:///Users/luckye/Documents/Code/a2a-review/T-212-r1/candidate/workbench/src/panes.ts#L2285) 两处不可达的死代码。

---

### 5. [非阻塞] [`test_t104_shell_e2e.py`](file:///Users/luckye/Documents/Code/a2a-review/T-212-r1/candidate/workbench/tests/test_t104_shell_e2e.py) 删掉了外置盘挂载与归档路径断言，与 [`AGENTS.md`](file:///Users/luckye/Documents/Code/a2a-review/T-212-r1/candidate/AGENTS.md) 规则不一致

- **文件与行号**：
  - [`change.diff`](file:///Users/luckye/Documents/Code/a2a-review/T-212-r1/change.diff#L699-L705) / [`test_t104_shell_e2e.py`](file:///Users/luckye/Documents/Code/a2a-review/T-212-r1/candidate/workbench/tests/test_t104_shell_e2e.py#L46-L50)
  - [`AGENTS.md`](file:///Users/luckye/Documents/Code/a2a-review/T-212-r1/candidate/AGENTS.md#L88)
- **为什么**：
  - Worker 为配合任务书（[`brief.md:96-114`](file:///Users/luckye/Documents/Code/a2a-review/T-212-r1/brief.md#L96-L114) 要求证据写入 `../T-212-evidence/`），在 [`test_t104_shell_e2e.py`](file:///Users/luckye/Documents/Code/a2a-review/T-212-r1/candidate/workbench/tests/test_t104_shell_e2e.py#L46-L50) 中直接删掉了 `assert os.path.ismount('/Volumes/WD-Elements')` 与 `assert str(args.archive.resolve()).startswith('/Volumes/WD-Elements/')`，而 [`AGENTS.md:88`](file:///Users/luckye/Documents/Code/a2a-review/T-212-r1/candidate/AGENTS.md#L88) 仍写明“运行归档放在外置盘 `/Volumes/WD-Elements/a2a-test-runs/`，缺盘直接报错”。
- **建议怎么改**：
  - 若项目级证据目录约定已调整，应由主控同步更新 [`AGENTS.md:88`](file:///Users/luckye/Documents/Code/a2a-review/T-212-r1/candidate/AGENTS.md#L88)；否则不应在单个回归测试里静默删掉归档路径检查。

---

## 二、九项核对清单逐项核查结果

### 1. 根因层改动、票面“要做什么”与“不做”边界
- **根因层与“要做什么”**：
  - 新增 [`hcDistribution.mjs`](file:///Users/luckye/Documents/Code/a2a-review/T-212-r1/candidate/workbench/src/hcDistribution.mjs#L1-L45) 与 [`hc.ts`](file:///Users/luckye/Documents/Code/a2a-review/T-212-r1/candidate/workbench/src/hc.ts#L1-L196)，由 [`PaneRegistry`](file:///Users/luckye/Documents/Code/a2a-review/T-212-r1/candidate/workbench/src/panes.ts#L221-L366) 管理 Enchanted 私有 `hc core`（`state_dir: <runtimeRoot>/hc-state`、`config_dir: <runtimeRoot>/hc-config`）及项目终端（`role === "shell"`）的创建、viewer 流桥接、尺寸同步与显式销毁。
  - 改动位于终端运行时根因层；除上述阻塞项 1（`screen: "inexact"` 与 `hc_connection_lost` 未按崩溃/未知处理）外，其余票面“要做什么”均已落位。
- **“不做”边界核查**：
  - 未把 worker、审查员、监视器或主控预设窗格迁到 hc（[`panes.ts:1357-1431`](file:///Users/luckye/Documents/Code/a2a-review/T-212-r1/candidate/workbench/src/panes.ts#L1357-L1431) 仍走 `node-pty`）。
  - 未移除 `node-pty` 依赖。
  - 未引入 Herdr UI、workspace/board 概念或自动重连重试循环。
  - 未连接或修改用户自己的 Herdr 与 `hc` 默认 `default` core。

### 2. 八条验收条目的真实入口证据、红绿态核对
- **红态核对（改前代码 `4cb88bba7`）**：
  - [`evidence/red-02/run.json`](file:///Users/luckye/Documents/Code/a2a-review/T-212-r1/evidence/red-02/run.json#L1-L120) 与 [`evidence/red-02.log`](file:///Users/luckye/Documents/Code/a2a-review/T-212-r1/evidence/red-02.log#L1-L26) 在 `git_head: "4cb88bba77bb6581c016c17ef03c32528f7eb5bd"` 上运行 `workbench/tests/test_t212_shell_hc_e2e.py`。
  - 失败方式与票面完全一致：后台重启前打开的终端 PID 为 `83530`（父进程为后台 daemon `83529`，而非 `hc terminal-holder`），后台重启后 `restarted_snapshot.pane.lifecycle == "ended"`（期望 `"running"`），`hc-state/core/core.sock` 不存在，按 `AssertionError: {'before_pid': 83530, 'after_pid': 83530, 'after_lifecycle': 'ended', ...}` 失败（[`red-02.log:25`](file:///Users/luckye/Documents/Code/a2a-review/T-212-r1/evidence/red-02.log#L25)）。
- **绿态核对**：
  - [`evidence/round2-screen-04/run.json`](file:///Users/luckye/Documents/Code/a2a-review/T-212-r1/evidence/round2-screen-04/run.json#L1-L195) 运行同一测试入口 `workbench/tests/test_t212_shell_hc_e2e.py` 并通过。
  - 各验收条目的逐条核查见第三节。

### 3. 测试区分度与反向（变异）验证
- **独立期望与反向验证**：
  - [`evidence/round2-screen-negative-01/run.json`](file:///Users/luckye/Documents/Code/a2a-review/T-212-r1/evidence/round2-screen-negative-01/run.json#L1-L22)：注入画面篡改后，[`test_t212_shell_hc_e2e.py:194-200`](file:///Users/luckye/Documents/Code/a2a-review/T-212-r1/candidate/workbench/tests/test_t212_shell_hc_e2e.py#L194-L200) 的 `after_screen == before_screen` 断言立即以 `AssertionError: screen mismatch after daemon restart` 失败。
  - [`evidence/token-negative-01/run.json`](file:///Users/luckye/Documents/Code/a2a-review/T-212-r1/evidence/token-negative-01/run.json#L1-L40)：验证篡改 token 后 `a2a status` 被后台以 `shell_token_mismatch` 拒绝。
  - [`evidence/socket-negative-01/run.json`](file:///Users/luckye/Documents/Code/a2a-review/T-212-r1/evidence/socket-negative-01/run.json#L1-L21)：验证超长 runtimeRoot 触发 `hc_socket_path_too_long`（131 > 103 字节）。
  - [`evidence/round2-boundaries-negative-01/run.json`](file:///Users/luckye/Documents/Code/a2a-review/T-212-r1/evidence/round2-boundaries-negative-01/run.json#L1-L32)：验证 [`test_t212_hc_boundaries_e2e.py`](file:///Users/luckye/Documents/Code/a2a-review/T-212-r1/candidate/workbench/tests/test_t212_hc_boundaries_e2e.py) 的断言在坏实现上会失败。
- **被放宽或缺失的检查**：
  - 缺少对 `hc core` 崩溃（`screen: "inexact"` 及 `hc_connection_lost`）的测试断言（见意见 1）。
  - 缺少项目终端内启动真实 Claude Code 走 `a2a request` 并核对侧栏非 `unknown` 的测试断言（见意见 2）。
  - [`test_t104_shell_e2e.py`](file:///Users/luckye/Documents/Code/a2a-review/T-212-r1/candidate/workbench/tests/test_t104_shell_e2e.py#L46-L50) 删去了外置盘挂载断言（见意见 5）。

### 4. 设计纯度（Fallback、重试、双写、平行 API、吞异常、旧路径残留）
- [`hcDistribution.mjs`](file:///Users/luckye/Documents/Code/a2a-review/T-212-r1/candidate/workbench/src/hcDistribution.mjs#L15-L44) 与 [`hc.ts`](file:///Users/luckye/Documents/Code/a2a-review/T-212-r1/candidate/workbench/src/hc.ts#L1-L196) 无重试、无回退到 `PATH` 或 `default` core、无平行 API。
- [`panes.ts:625`](file:///Users/luckye/Documents/Code/a2a-review/T-212-r1/candidate/workbench/src/panes.ts#L625) 存在 `if (start?.data.hc_terminal)` 兼容条件分支，[`panes.ts:2275, 2285`](file:///Users/luckye/Documents/Code/a2a-review/T-212-r1/candidate/workbench/src/panes.ts#L2275) 存在两行不可达旧代码（见意见 4）。
- [`panes.ts:364-365`](file:///Users/luckye/Documents/Code/a2a-review/T-212-r1/candidate/workbench/src/panes.ts#L364-L365) 对 `terminal.screen !== "exact"` 只记事件不报错，实质上把不完整恢复放行成了正常终端（见意见 1）。

### 5. 边界与安全逐点核查
1. **不连、不改用户自己的 Herdr 与 hc `default` core**：
   - **通过**。[`hc.ts:43-49`](file:///Users/luckye/Documents/Code/a2a-review/T-212-r1/candidate/workbench/src/hc.ts#L43-L49) 固定把 `XDG_STATE_HOME` 与 `XDG_CONFIG_HOME` 指到 `<runtimeRoot>/hc-state` 与 `<runtimeRoot>/hc-config`，且加 `--core core`。[`round2-boundaries-02/run.json`](file:///Users/luckye/Documents/Code/a2a-review/T-212-r1/evidence/round2-boundaries-02/run.json#L43-L61) 实测验证了外部用户 `default` core（PID `67275`）与假 Herdr 进程（PID `67281`）在后台启停、关窗格与崩溃清理后依然存活且快照未变。
2. **Core 启动环境剥离与终端 `env -u` 还原**：
   - **通过**。[`hc.ts:15-31`](file:///Users/luckye/Documents/Code/a2a-review/T-212-r1/candidate/workbench/src/hc.ts#L15-L31) 的 [`cleanCoreEnv`](file:///Users/luckye/Documents/Code/a2a-review/T-212-r1/candidate/workbench/src/hc.ts#L22-L31) 剥离了 `A2A_*`、`GIT_CONFIG_*`、`HC_*`、`CLAUDE*`、`CODEX*`、`GEMINI*`、`OPENCODE*`、`ELECTRON_RUN_AS_NODE`。
   - [`panes.ts:276-288`](file:///Users/luckye/Documents/Code/a2a-review/T-212-r1/candidate/workbench/src/panes.ts#L276-L288) 在终端命令前加了 `/usr/bin/env -u XDG_STATE_HOME -u XDG_CONFIG_HOME`，当用户原有 `XDG_STATE_HOME` / `XDG_CONFIG_HOME` 非 `undefined`（含空串）时通过 `XDG_STATE_HOME=...` 精确还原。[`round2-boundaries-02/run.json`](file:///Users/luckye/Documents/Code/a2a-review/T-212-r1/evidence/round2-boundaries-02/run.json#L20-L42) 实测验证了非空值还原、空串（`""`）还原、未设置时 `unset` 以及污染变量剥离。
3. **Socket 路径上限含 holder 后缀**：
   - **通过**。[`hc.ts:36-41`](file:///Users/luckye/Documents/Code/a2a-review/T-212-r1/candidate/workbench/src/hc.ts#L36-L41) 计算 `<runtimeRoot>/hc-state/core/core.sock.holder.00000000.sock` 的 UTF-8 字节长度并校验 `<= 103`（`hc_socket_path_too_long`），[`socket-negative-01/run.json`](file:///Users/luckye/Documents/Code/a2a-review/T-212-r1/evidence/socket-negative-01/run.json#L1-L21) 已验证。
4. **固定版本与 SHA-256 校验不符即报错、不回退**：
   - **通过**。[`hcDistribution.mjs:4-44`](file:///Users/luckye/Documents/Code/a2a-review/T-212-r1/candidate/workbench/src/hcDistribution.mjs#L4-L44) 固定锁死 `0.1.15` 与 SHA-256 `677f2064d6d1289cd4f00b89e47c9942dc99f4ef597a7933ad26598521ed3b28`，校验路径存在、可执行位、SHA-256 及 `--version` 输出，任一不符立即抛错。[`round2-boundaries-02/run.json`](file:///Users/luckye/Documents/Code/a2a-review/T-212-r1/evidence/round2-boundaries-02/run.json#L62-L67) 验证了被篡改二进制与被篡改版本均直接报错退出。
5. **Token 在后台只存哈希，`hc` 私有 registry 明文副本永不复制进证据**：
   - **通过**。[`panes.ts:138-167`](file:///Users/luckye/Documents/Code/a2a-review/T-212-r1/candidate/workbench/src/panes.ts#L138-L167) 在 `<runtimeRoot>/shell-credentials/<launch>.json` 中只存 `token_sha256`（`sha256:<hex>`），[`daemon.ts:397`](file:///Users/luckye/Documents/Code/a2a-review/T-212-r1/candidate/workbench/src/daemon.ts#L397) 用 `timingSafeEqual` 比对哈希。
   - [`hc_evidence.py:13-53`](file:///Users/luckye/Documents/Code/a2a-review/T-212-r1/candidate/workbench/tests/hc_evidence.py#L13-L53) 显式排除 `hc-state` / `hc-config` / `terminals.json` 并扫描拦截 `64` 位 hex 明文 token。[`round2-evidence-boundary.json`](file:///Users/luckye/Documents/Code/a2a-review/T-212-r1/evidence/round2-evidence-boundary.json#L1-L7) 扫描确认证据目录中 `forbidden_files: []`、`secret_hits: []`。
6. **打包时 `hc` 二进制签名与许可证随附**：
   - **通过**。[`package-mac.mjs:62-97`](file:///Users/luckye/Documents/Code/a2a-review/T-212-r1/candidate/workbench/app/package-mac.mjs#L62-L97) 复制 `hc`、`LICENSE`、`THIRD-PARTY-NOTICES` 到 `Contents/Resources/bin/hc/`，并对 `hc` 单独执行 `codesign --force --sign -` 后再整体签名 `.app`，随后运行 `codesign --verify --deep --strict`。[`round2-packaged-runtime-04/run.json`](file:///Users/luckye/Documents/Code/a2a-review/T-212-r1/evidence/round2-packaged-runtime-04/run.json#L1-L45) 实测验证了打包产物签名通过且双击等价启动（`PATH="/usr/bin:/bin:/usr/sbin:/sbin"`）下能正常拉起私有 `hc core` 与项目终端。
7. **测试启动的后台服务脱离调用者进程组，测试只用脚本化模型**：
   - **通过**。[`test_t212_shell_hc_e2e.py:106`](file:///Users/luckye/Documents/Code/a2a-review/T-212-r1/candidate/workbench/tests/test_t212_shell_hc_e2e.py#L106) 使用 `start_new_session=True` 启动后台并断言 `daemon_ps["ppid"] == 1`（[`round2-screen-04/run.json:38-44`](file:///Users/luckye/Documents/Code/a2a-review/T-212-r1/evidence/round2-screen-04/run.json#L38-L44)）；新增测试完全不调用外部模型，回归测试均使用本地 [`scripted_claude.py`](file:///Users/luckye/Documents/Code/a2a-review/T-212-r1/candidate/workbench/tests/scripted_claude.py)。

### 6. 文档、角色卡、命令说明与代码行为一致性
- **不通过（阻塞）**：
  - [`AGENTS.md`](file:///Users/luckye/Documents/Code/a2a-review/T-212-r1/candidate/AGENTS.md#L25)、[`CONTEXT.md`](file:///Users/luckye/Documents/Code/a2a-review/T-212-r1/candidate/CONTEXT.md#L22)、[`README.md`](file:///Users/luckye/Documents/Code/a2a-review/T-212-r1/candidate/README.md#L58)、[`.project-map/MAP.md`](file:///Users/luckye/Documents/Code/a2a-review/T-212-r1/candidate/.project-map/MAP.md#L121-L130) 已更新；角色卡（[`worker.md`](file:///Users/luckye/Documents/Code/a2a-review/T-212-r1/candidate/workbench/roles/worker.md)、[`reviewer.md`](file:///Users/luckye/Documents/Code/a2a-review/T-212-r1/candidate/workbench/roles/reviewer.md)、[`monitor.md`](file:///Users/luckye/Documents/Code/a2a-review/T-212-r1/candidate/workbench/roles/monitor.md)）与 [`a2a`](file:///Users/luckye/Documents/Code/a2a-review/T-212-r1/candidate/workbench/terminal/bin/a2a) 命令说明与本票范围一致。
  - 但 [`workbench/README.md:210, 316-317`](file:///Users/luckye/Documents/Code/a2a-review/T-212-r1/candidate/workbench/README.md#L316-L317) 与 [`roleRequests.ts:60`](file:///Users/luckye/Documents/Code/a2a-review/T-212-r1/candidate/workbench/src/roleRequests.ts#L60) 仍保留“后台重启后普通终端返回 `lifecycle: ended`、主控身份随后台重启结束”的旧说明，与同文件第 14 行及代码实际行为直接冲突（见意见 3）。

### 7. 受管窗格 `node-pty` 路径与项目终端单一路径核查
- **通过**：
  - 受管窗格（worker、审查员、监视器、预设主控）在 [`panes.ts:1357-1431`](file:///Users/luckye/Documents/Code/a2a-review/T-212-r1/candidate/workbench/src/panes.ts#L1357-L1431)（[`spawnProcess`](file:///Users/luckye/Documents/Code/a2a-review/T-212-r1/candidate/workbench/src/panes.ts#L1357-L1431)）保持原 `node-pty` 路径未改动。
  - 项目终端（[`startShell`](file:///Users/luckye/Documents/Code/a2a-review/T-212-r1/candidate/workbench/src/panes.ts#L254-L323)）唯一走 `this.hc.spawn(...)` + `this.attachShell(...)`，没有保留第二条 `node-pty` 启动路径。

### 8. 四项旧回归与父版本（`4cb88bba7`）失败点比对
经逐一核对 `evidence/parent-*` 与候选回归证据原始输出，四项旧回归在父版本与候选版本上的失败点完全一致，确属既有问题而非本票引入：
1. **`T-184`（`test_t184_unwired_cli_e2e.py`）**：
   - 父版本 [`parent-t184-01.json`](file:///Users/luckye/Documents/Code/a2a-review/T-212-r1/evidence/parent-t184-01.json#L1-L26) 与候选 [`t184-regression-02/summary.json`](file:///Users/luckye/Documents/Code/a2a-review/T-212-r1/evidence/t184-regression-02/summary.json#L1-L30) 均在 [`test_t184_unwired_cli_e2e.py:130`](file:///Users/luckye/Documents/Code/a2a-review/T-212-r1/candidate/workbench/tests/test_t184_unwired_cli_e2e.py#L130) `wait_until("bare claude prompt", ...)` 超时失败（Claude Code 2.1.112 在新目录卡在交互式信任确认界面，未发出首轮 `/v1/messages` 请求）。
2. **`T-195`（`test_t195_native_link_e2e.py`）**：
   - 父版本 [`parent-t195-01.json`](file:///Users/luckye/Documents/Code/a2a-review/T-212-r1/evidence/parent-t195-01.json#L1-L25) 与候选 [`t195-regression-02/summary.json`](file:///Users/luckye/Documents/Code/a2a-review/T-212-r1/evidence/t195-regression-02/summary.json#L1-L30) 均在 [`test_t195_native_link_e2e.py:59`](file:///Users/luckye/Documents/Code/a2a-review/T-212-r1/candidate/workbench/tests/test_t195_native_link_e2e.py#L59) `wait_until("initial controller idle", ...)` 超时失败（`controller_state="running"`，`requests=0`）。
3. **`test_daemon_recovery_e2e.py`**：
   - 父版本 [`parent-recovery-01.json`](file:///Users/luckye/Documents/Code/a2a-review/T-212-r1/evidence/parent-recovery-01.json#L1-L25) 与候选 [`recovery-regression-03/stdout.log`](file:///Users/luckye/Documents/Code/a2a-review/T-212-r1/evidence/recovery-regression-03/stdout.log#L1-L31) 均在 [`test_daemon_recovery_e2e.py:165`](file:///Users/luckye/Documents/Code/a2a-review/T-212-r1/candidate/workbench/tests/test_daemon_recovery_e2e.py#L165) `assert post_kill["pane"]["failed"]["code"] == "process_lost"` 失败：实际返回 `code: "turn_aborted", detail: "signal_SIGTERM"`（[`recovery-regression-03/output/run.json:83-86`](file:///Users/luckye/Documents/Code/a2a-review/T-212-r1/evidence/recovery-regression-03/output/run.json#L83-L86)）。
4. **`test_electron_e2e.py`**：
   - 父版本 [`parent-electron-01.json`](file:///Users/luckye/Documents/Code/a2a-review/T-212-r1/evidence/parent-electron-01.json#L1-L25) 与候选 [`electron-regression-03/stdout.log`](file:///Users/luckye/Documents/Code/a2a-review/T-212-r1/evidence/electron-regression-03/stdout.log#L1-L16) 均在 [`test_electron_e2e.py:528`](file:///Users/luckye/Documents/Code/a2a-review/T-212-r1/candidate/workbench/tests/test_electron_e2e.py#L528) `assert all(verdict["checks"].values())` 失败，且唯一失败项同为 `dispatch_reached_waiting_review: false`（[`electron-regression-03/output/verdict.json:12`](file:///Users/luckye/Documents/Code/a2a-review/T-212-r1/evidence/electron-regression-03/output/verdict.json#L12)）。

### 9. 主控中途决定（[`controller/decisions.md`](file:///Users/luckye/Documents/Code/a2a-review/T-212-r1/controller/decisions.md)）是否放宽验收
- **结论：主控的 3 条中途决定均未放宽验收标准，相反收紧并维护了验收要求**：
  - **D1**（[`decisions.md:5-22`](file:///Users/luckye/Documents/Code/a2a-review/T-212-r1/controller/decisions.md#L5-L22)）：拒绝直接套用未适配的旧重连预期，要求按新规格更新 `test_t104_shell_e2e.py` 为“后台重启后接回同一 hc 终端且 PID 不变”，并在父版本跑留底。
  - **D2**（[`decisions.md:24-39`](file:///Users/luckye/Documents/Code/a2a-review/T-212-r1/controller/decisions.md#L24-L39)）：在首轮审查中准确指出 Worker 未验证终端画面完全一致、未实际运行打包后 `.app`、且把含明文 token 的 `terminals.json` 复制进了证据目录，打回重做。
  - **D3**（[`decisions.md:41-55`](file:///Users/luckye/Documents/Code/a2a-review/T-212-r1/controller/decisions.md#L41-L55)）：允许在无外接硬盘环境下把证据写到本地 `../T-212-evidence/`，属于测试产物存放位置的合理工程适配，未降低功能或安全验收标准。

---

## 三、八条验收条目逐条结论

1. **条目 1**：真实打开项目终端，核对私有 `hc core` 已在 `<runtimeRoot>/hc-state/core/core.sock` 下运行，终端进程挂在 `hc` 的 `terminal-holder` 下而非后台直接子进程。
   - 依据：[`round2-screen-04/run.json:55-97`](file:///Users/luckye/Documents/Code/a2a-review/T-212-r1/evidence/round2-screen-04/run.json#L55-L97) 实测验证 `core_socket.exists == true`、终端进程（PID `70039`）的父进程为 `hc terminal-holder`（PID `70038`，`ppid == 1`），且不等于后台 daemon PID（`70003`）。
   - 结论：**`PASS`**

2. **条目 2**：在项目终端里启动交互进程（输出多行、改 cwd、设局部变量、留半行未回车输入），杀掉并重启 Enchanted 后台，重连后同一终端 PID 不变、交互进程不中断、屏幕内容与光标位置一致。
   - 依据：[`round2-screen-04/run.json:98-181`](file:///Users/luckye/Documents/Code/a2a-review/T-212-r1/evidence/round2-screen-04/run.json#L98-L181) 在 Electron 真实窗口（800×600）中验证：启动交互式 Python 子进程、输出多行、切换 cwd 到 `subdir-check`、设置局部变量 `LOCAL_SURVIVES=kept_value`、留半行输入 `half_line_input_42`，`SIGKILL` 后台（PID `70003`）并拉起新后台（PID `70058`）后，终端 PID 仍为 `70039`，交互式子进程 PID 仍为 `70056`，通过 `hc snapshot` 与 Electron 渲染层 `readPaneScreen` 双重核对 `text_equal == true`、`cursor_equal == true`（`row: 11, col: 18`），继续补完回车后输出 `DONE:half_line_input_42_completed`。
   - 结论：**`PASS`**

3. **条目 3**：后台重启后，在原终端里执行 `a2a status`（及已生效的主控命令）继续成功，无需重开终端或重新注入环境变量；伪造或缺失 `A2A_TERMINAL_TOKEN` 的请求被后台拒绝。
   - 依据：[`round2-screen-04/run.json:118-174`](file:///Users/luckye/Documents/Code/a2a-review/T-212-r1/evidence/round2-screen-04/run.json#L118-L174) 与 [`token-negative-01/run.json:12-38`](file:///Users/luckye/Documents/Code/a2a-review/T-212-r1/evidence/token-negative-01/run.json#L12-L38) 实测验证：后台重启后原终端直接执行 `a2a status` 返回 `ok: true`，已批准主控身份仍在侧栏保持 `controller`；伪造 token（`wrong-token`）与缺失 token（`env -u A2A_TERMINAL_TOKEN`）均被拒绝（`returncode: 1`，`shell_token_mismatch` / `missing A2A_TERMINAL_TOKEN`）。
   - 结论：**`PASS`**

4. **条目 4**：用户在界面关闭终端窗格后，`hc list` 中不再残留该终端，对应 `terminal-holder` 与 shell 进程退出。
   - 依据：[`round2-screen-04/run.json:182-193`](file:///Users/luckye/Documents/Code/a2a-review/T-212-r1/evidence/round2-screen-04/run.json#L182-L193) 与 [`t104-03.json:96-119`](file:///Users/luckye/Documents/Code/a2a-review/T-212-r1/evidence/t104-03.json#L96-L119) 实测验证：点击关闭窗格后，`hc list` 不再包含该终端 ID，原 shell（PID `70039`）、交互子进程（PID `70056`）与 `terminal-holder`（PID `70038`）全部退出。
   - 结论：**`PASS`**

5. **条目 5**：在项目终端里启动 Claude Code 并经 `a2a request` 申请主控、界面批准后生效（T-119 流程不变）；侧栏状态与改前一致或更准，不出现新的“未知”。
   - 依据：见审查意见 1 与意见 2。一是 `evidence/` 中没有任何一次测试在 hc 项目终端里启动真实 Claude Code 走完 `a2a request` 并核对侧栏状态非 `"unknown"`（`test_t121` 用的是 2 行假脚本且未断言 `state`，`test_t107` 断言的是 `"unknown"`）；二是当 `hc core` 崩溃断开时，[`sidebar.ts:224-241`](file:///Users/luckye/Documents/Code/a2a-review/T-212-r1/candidate/workbench/src/sidebar.ts#L224-L241) 与 [`panes.ts:325-366, 625-636`](file:///Users/luckye/Documents/Code/a2a-review/T-212-r1/candidate/workbench/src/panes.ts#L625-L636) 未按规定标为未知/已死，反而冒充恢复。
   - 结论：**`INCOMPLETE`**

6. **条目 6**：宿主机同时运行用户自己的 `hc` 默认 core 或 Herdr 时，Enchanted 的启动、关窗格、正常退出与崩溃清理均不连接、不影响用户的 `default` core。
   - 依据：[`round2-boundaries-02/run.json:43-61`](file:///Users/luckye/Documents/Code/a2a-review/T-212-r1/evidence/round2-boundaries-02/run.json#L43-L61) 实测验证：宿主机同时运行用户 `default` core（PID `67275`）、用户终端（PID `67277`）及假 Herdr 进程（PID `67281`），经历 Enchanted 启动、关窗格、正常退出与 `SIGKILL` 崩溃清理后，用户 `default` core、用户终端与假 Herdr 全部存活且状态未变。
   - 结论：**`PASS`**

7. **条目 7**：打包后的 macOS 应用在无开发者 `PATH` 的双击环境下能直接拉起随包 `hc` 并通过上述终端验收。
   - 依据：[`round2-packaged-runtime-04/run.json:1-45`](file:///Users/luckye/Documents/Code/a2a-review/T-212-r1/evidence/round2-packaged-runtime-04/run.json#L1-L45) 实测验证：`Enchanted Workbench.app` 通过 `codesign --verify --deep --strict`，在仅含 `/usr/bin:/bin:/usr/sbin:/sbin` 的最小 `PATH` 下启动打包产物，确认拉起 `Contents/Resources/bin/hc/hc` 私有 core，完成终端输出、关闭清理，且随包附带 `LICENSE` 与 `THIRD-PARTY-NOTICES`。
   - 结论：**`PASS`**

8. **条目 8**：跑完测试后无残留 `hc` 测试 core、无孤儿 `terminal-holder`、无残留后台进程。
   - 依据：[`round2-process-cleanup-final.json:1-6`](file:///Users/luckye/Documents/Code/a2a-review/T-212-r1/evidence/round2-process-cleanup-final.json#L1-L6)、[`round2-screen-04/run.json:193`](file:///Users/luckye/Documents/Code/a2a-review/T-212-r1/evidence/round2-screen-04/run.json#L193)、[`round2-boundaries-02/run.json:70`](file:///Users/luckye/Documents/Code/a2a-review/T-212-r1/evidence/round2-boundaries-02/run.json#L70) 及 [`round2-packaged-runtime-04/run.json:42`](file:///Users/luckye/Documents/Code/a2a-review/T-212-r1/evidence/round2-packaged-runtime-04/run.json#L42) 均验证 `leaked_processes == []`。
   - 结论：**`PASS`**

---

INCOMPLETE