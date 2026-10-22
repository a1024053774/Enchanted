# T-132 候选 1 独立审查报告

**审查对象**：
- 候选提交：[`dc4d2e257`](file:///Users/luckye/Documents/Code/a2a/workbench/app/IssuesPage.tsx)（问题列表与操作）、[`07dc957c3`](file:///Users/luckye/Documents/Code/a2a/workbench/tests/scripted_claude.py#L379)（夹具复制许可证文件与失败清理）、[`ea68df9d9`](file:///Users/luckye/Documents/Code/a2a/workbench/README.md#L942)（README 说明）。
- 父提交：`85b212a60`。
- 改动汇总：`/private/tmp/claude-501/-Users-luckye-Documents-Code-a2a/193bb4d9-d8a5-4f5f-9e0a-4a1f8bbc5df3/scratchpad/agy-t132-De2E/full.diff`。
- 验收证据：[`RESULTS.md`](file:///Users/luckye/Documents/Code/a2a/evidence/2026-10-22-batch20/T-132/candidate-1/RESULTS.md)。

---

## 一、重点问题审查

### 1. 操作员凭据发出的 disposition 记为 user

- **是否安全、是否符合“阻塞问题只有用户能关”的规则**：
  - **符合且安全**。门禁核心 [`core.ts:779`](file:///Users/luckye/Documents/Code/a2a/workbench/src/gates/core.ts#L779) 规定：
    ```ts
    if (args.action === "close") {
      requireGate(!view.issue.blocking || actor === "user", "blocking_requires_user");
      requireGate(args.reason?.trim() && args.basis?.trim(), "close_requires_reason_basis");
    }
    ```
    此外 `snooze`（稍后）与 `dismiss`（不处理）在 [`core.ts:777`](file:///Users/luckye/Documents/Code/a2a/workbench/src/gates/core.ts#L777) 明确强制 `actor === "user"`。
    修前 [`daemon.ts:654`](file:///Users/luckye/Documents/Code/a2a/workbench/src/daemon.ts#L654) 将操作员发出的请求一律硬编码为 `address: "executor"`，导致桌面应用即使由用户本人操作也无法关闭阻塞问题或稍后处理。本次修改为：
    ```ts
    const actor = authority.kind === "operator" ? { address: input.command === "disposition" ? "user" : "executor", ... }
    ```
    使得界面触发的处置在门禁层正确呈现为用户本人操作。

- **操作员凭据在产品里的持有者**：
  - 经核对 [`desktop.mjs:48-71`](file:///Users/luckye/Documents/Code/a2a/workbench/app/desktop.mjs#L48-L71)、[`desktopCredentials.ts:9-36`](file:///Users/luckye/Documents/Code/a2a/workbench/src/desktopCredentials.ts#L9-L36) 及 [T-125](file:///Users/luckye/Documents/Code/a2a/.project-map/tickets/T-125-operator-credential-storage.md) / [T-126](file:///Users/luckye/Documents/Code/a2a/.project-map/tickets/T-126-operator-credential-out-of-terminal-reach.md) 决议：
    操作员凭据存放在 `~/Library/Application Support/Enchanted/`（或专用测试目录）下的 `0600` 文件中，仅 Electron 主进程启动时读取并通过 IPC 供桌面窗口调用。
    项目终端仅被分配专用 socket（`A2A_TERMINAL_SOCKET`）和终端身份令牌，其环境不包含 `A2A_STATE` 或操作员凭据，且终端 socket 对非终端身份直接拒绝（`terminal_socket_terminal_only`）；受管 worker / reviewer 子进程亦不持有该凭据。因此在产品正常运行拓扑中，**唯有桌面界面持有操作员凭据**。

- **测试里用操作员凭据扮演 executor 的旧场景是否会被误伤**：
  - **不会误伤**。
    1. 门禁在关闭非阻塞问题时，允许 `actor` 为 `"user"` 或 `"executor"`；改为 `"user"` 后，任何旧的非阻塞问题关闭请求仍能通过。
    2. 主控终端（terminal controller）如果执行处置或答复，是通过终端身份经 [`daemon.ts:192-257`](file:///Users/luckye/Documents/Code/a2a/workbench/src/daemon.ts#L192-L257) 的 `terminalCommand` 发起，其 `actor.address` 来自已批准的角色申请（`"executor"` 或 `"ideation"`），不走 `authority.kind === "operator"` 分支。
    3. 本轮回归跑了 `t122-green`（包含 23 项主控/worker 完整流程），全部正常 PASS。

---

### 2. `sidebar_snapshot` 逐任务读 issues 的开销与失败处理

- **一个任务读失败会不会让整个侧栏失败、这是否合适**：
  - **会导致整个侧栏完全失败，这不合适（见缺陷 1）**。
    在 [`daemon.ts:289-301`](file:///Users/luckye/Documents/Code/a2a/workbench/src/daemon.ts#L289-L301)：
    ```ts
    if (input.command === 'sidebar_snapshot') {
      const snapshot = await sidebarSnapshot(gates, store, panes, roleRequests, quota.current());
      const projects = await Promise.all(snapshot.projects.map(async (project: any) => {
        let waiting = 0;
        for (const task of project.tasks) {
          const result = await gates.call({ command: 'issues', task: task.task_id });
          if (!result.ok) throw new Refusal(result.error ?? 'issues_unavailable');
          waiting += (result.issues ?? []).filter((view: any) => view.state === '等你决定').length;
        }
        return { ...project, issues_waiting: waiting };
      }));
      return { ok: true, ...snapshot, projects };
    }
    ```
    一旦任何一个项目的某一个任务在读取 `issues` 时抛出异常或返回 `!ok`，整个 `Promise.all` 立即 reject，导致 `sidebar_snapshot` 整体失败。
    前端 [`renderer.tsx:516`](file:///Users/luckye/Documents/Code/a2a/workbench/app/renderer.tsx#L516) 捕获到侧栏读取异常后，会将全站所有项目、所有 Agent 的状态全量置为“未知”，并显示“侧栏状态未知”。
    项目行和页签的“问题待办数”仅仅是一个辅助提示计数，单个任务问题读取的故障不应该导致全局侧栏监控、窗格布局和主控 Agent 树完全停摆。

- **性能开销**：
  - 侧栏是由前端每 3 秒轮询一次的快照。若仓库有 $P$ 个项目，共 $T$ 个任务，每一次侧栏轮询都要对这 $T$ 个任务分别执行完整的 `gates.call('issues')`，内部涉及 `tasks` 表、`issue_records` 表、`user_inputs` 表的重复查询及链条重建（N+1 查询）。随着任务数量累积，每 3 秒产生的开销过大。

- **只读命令是否写库**：
  - **确认不写库**。
    `command: 'issues'` 在 [`core.ts:3534-3537`](file:///Users/luckye/Documents/Code/a2a/workbench/src/gates/core.ts#L3534-L3537) 仅调用 `load(taskId)` 和 `readIssues(taskId)`，均为纯 `SELECT` 操作，无 `event()` 或 `save()` 调用。
    而在 [`daemon.ts:103-105`](file:///Users/luckye/Documents/Code/a2a/workbench/src/daemon.ts#L103-L105)，`sidebar_snapshot` 属于 `catalogCommands`，在成功处理时不记录 `request_received` 或 `request_result` 到 `orchestration_events`。因此该只读链路不产生数据库写入。

---

### 3. 界面状态、错误、并发操作、输入校验与可访问性

- **输入状态丢失缺陷（见缺陷 2）**：
  在 [`IssuesPage.tsx:57`](file:///Users/luckye/Documents/Code/a2a/workbench/app/IssuesPage.tsx#L57)：
  `{!error && rows.map(({ task, view }) => <Issue ... />)}`
  当后台发生瞬时网络抖动或轮询单次报错时，`error` 变为非空字符串。此时所有已挂载的 `<Issue>` 卡片被**直接卸载（unmount）**。
  若用户当时正在输入框中撰写答复（`answer`）或正在填写关闭原因与依据（`reason`、`basis`），卡片卸载会导致用户的**未提交输入全部丢失**。待 3 秒后下次轮询恢复，卡片重新挂载，表单已被重置为空。

- **空项目错误状态矛盾呈现（见缺陷 3）**：
  在 [`IssuesPage.tsx:53-56`](file:///Users/luckye/Documents/Code/a2a/workbench/app/IssuesPage.tsx#L53-L56)：
  ```tsx
  {error && <p className="catalog-error" role="alert">{error}</p>}
  {!project ? <p className="records-empty">先在左侧选一个项目。</p>
    : tasks === null && !error ? <p className="records-empty" role="status">正在读取…</p>
    : tasks !== null && !rows.length ? <p className="records-empty">这个项目还没有问题上报。</p> : null}
  ```
  如果某个项目原本就没有问题上报（`tasks !== null && rows.length === 0`），随后后台断开或报错（`error` 存在）：第 53 行渲染了错误提示，而第 56 行由于**缺少 `!error` 守卫**，仍然会同时渲染“这个项目还没有问题上报。”，造成界面同时出现报错与空态文案的矛盾状态。

- **项目切换时的残影状态（见缺陷 4）**：
  在 [`IssuesPage.tsx:15-25`](file:///Users/luckye/Documents/Code/a2a/workbench/app/IssuesPage.tsx#L15-L25)，`useEffect` 依赖 `[project, version]`，但切换 `project` 时并未同步清空旧的 `tasks`，导致在新项目的 `a2a.issues(project)` 返回之前，页面仍会短暂停留展示上一个项目的问题列表。

- **并发与输入校验**：
  - `<Issue>` 组件内部通过 `busy` 状态禁用了提交按钮、输入框与切换按钮，防止了重复并发点击。
  - 主进程 IPC [`main.ts:128`](file:///Users/luckye/Documents/Code/a2a/workbench/app/main.ts#L128) 对 `action` 限制了 `['close', 'snooze']`，基本参数有类型校验。但在 `action === 'close'` 时，主进程未在入口校验 `reason` 和 `basis` 是否为空白字符串，虽然门禁底层会通过 `close_requires_reason_basis` 拒绝，但 IPC 层防护可更严谨（见缺陷 5）。

- **可访问性与文案**：
  - 错误提示带有 `role="alert"`，加载状态带有 `role="status"`。
  - 页签提示带有清晰的 `aria-label="${issuesWaiting} 个等你决定"`。
  - 折叠表单带有 `aria-expanded={closing}`。
  - 文案“worker、审查员和监视器发现任务范围外的问题时报到这里……标了‘阻塞’的只有你能关闭”准确反映了统一术语。

---

### 4. 测试与结果报告评估

- **测试独立性**：
  - [`test_t132_issues_panel_e2e.py`](file:///Users/luckye/Documents/Code/a2a/workbench/tests/test_t132_issues_panel_e2e.py) 采用了端到端测试机制：真实启动后台、真实的 Claude Code worker（模型走本地脚本化 Messages API，不发生供应商网络外联）、通过 [`cdp_launch.cjs`](file:///Users/luckye/Documents/Code/a2a/workbench/tests/cdp_launch.cjs) 启动源码构建的真实 Electron 窗口，并通过 [`cdp.mjs`](file:///Users/luckye/Documents/Code/a2a/workbench/tests/cdp.mjs) 走 Chrome DevTools Protocol 模拟真实用户点击、输入与截图，最后在门禁数据层断言状态。测试独立于 UI 组件的具体实现细节。

- **变异与已知坏实现对比**：
  - `red-parent`（基线父提交 `85b212a60`）：在项目行徽标超时处失败，证明修前版本无此能力。
  - `mutant-disposition-as-executor`：证明了若后台处置未记为 `user`，关闭阻塞问题必然超时失败。
  - `mutant-error-shown-as-empty`：证明了读取失败若伪装为空列表必然失败。

- **夹具与清理**：
  - `Electron.stop()` 会清理 `a2a-build-<slot>` 目录；`Fixture.stop()` 正确关闭后台与 HTTP 服务器。保留的现场证据已归档至外置盘清单 [`fixtures.archive.json`](file:///Users/luckye/Documents/Code/a2a/evidence/2026-10-22-batch20/T-132/candidate-1/fixtures.archive.json)，符合 T-088 规范。

- **RESULTS.md 真实性与夸大核查**：
  - 报告中的运行时间、截图编号、变异测试结果真实无夸大。
  - 报告主动列出了两项未覆盖点（“稍后再看”未独立跑端到端、未重装 /Applications 打包应用）。
  - 但关于“读取失败时页面显示失败，不显示为空列表”，测试用例仅覆盖了“原本已有 2 条问题记录时断开后台”，未覆盖“原本就是 0 条问题记录时断开后台”（此时界面会同时显示失败文案与空列表文案）。

---

## 二、审查发现明细

### 发现 1：单个任务问题读取失败导致整个侧栏快照崩溃（P2）
- **位置**：[`workbench/src/daemon.ts:295-298`](file:///Users/luckye/Documents/Code/a2a/workbench/src/daemon.ts#L295-L298)
- **场景**：
  在 `sidebar_snapshot` 中，后台对所有项目的全部任务串行调用 `gates.call({ command: 'issues', task: task.task_id })`。若由于偶发锁竞争、单任务数据异常或历史脏数据导致其中任意一个任务的调用返回 `!result.ok`，代码将直接 `throw new Refusal(...)`。这会导致 `sidebar_snapshot` 整体报错，前端侧栏状态全部置为 `unknown`（“侧栏状态未知”），所有项目的终端监控、Agent 树全部中断更新。此外，每次侧栏轮询做 $N$ 次独立门禁任务展开，具有 N+1 查询放大效应。
- **建议**：
  在 `sidebar_snapshot` 聚合中对单任务的读取增加容错降级（例如单任务失败仅将该任务或项目的问题计数记为 0 并记录告警，或在门禁层提供直接统计项目“等你决定”问题数的轻量聚合接口），避免非关键的辅助徽标拖垮核心侧栏。

---

### 2. 轮询瞬时出错导致用户正在输入的答复或关闭理由清空丢失（P2）
- **位置**：[`workbench/app/IssuesPage.tsx:57`](file:///Users/luckye/Documents/Code/a2a/workbench/app/IssuesPage.tsx#L57)
- **场景**：
  页面在 `!error` 为真时才渲染卡片列表：
  `{!error && rows.map(({ task, view }) => <Issue ... />)}`
  若用户正在输入长篇答复（最大 4000 字）或正在填写关闭原因/依据，此时后台若发生 1 次网络超时或读取错误，`error` 被赋值，导致全部卡片被卸载，内部 React state 全部丢弃。3 秒后轮询成功，卡片重新挂载，用户已输入的文本化为乌有。
- **建议**：
  在已加载有数据的情况下发生读取错误时，保留当前已渲染的 `rows` 卡片列表，仅在顶部显示浮动错误条，避免组件卸载导致用户表单数据丢失。

---

### 3. 空项目读取失败时界面同时显示报错与“还没有问题上报”矛盾文案（P2）
- **位置**：[`workbench/app/IssuesPage.tsx:53-56`](file:///Users/luckye/Documents/Code/a2a/workbench/app/IssuesPage.tsx#L53-L56)
- **场景**：
  当选中的项目原本没有任何问题（`tasks !== null && rows.length === 0`），后台停止或发生读取失败时，第 53 行渲染了错误告警，而第 56 行条件 `tasks !== null && !rows.length` 依然成立且未判断 `!error`，导致页面在错误提示下方赫然出现“这个项目还没有问题上报。”，呈现自相矛盾的界面状态。
- **建议**：
  在第 56 行增加 `!error` 检查：
  ```tsx
  : tasks !== null && !error && !rows.length ? <p className="records-empty">这个项目还没有问题上报。</p> : null
  ```

---

### 4. 切换项目时残留上一个项目的问题列表（P3）
- **位置**：[`workbench/app/IssuesPage.tsx:15-25`](file:///Users/luckye/Documents/Code/a2a/workbench/app/IssuesPage.tsx#L15-L25)
- **场景**：
  当从项目 A 切换到项目 B 时，`useEffect` 重新触发，但在新项目的数据返回之前，`tasks` 状态依然保留着项目 A 的数据，导致页面在加载期间仍显示项目 A 的问题。
- **建议**：
  在 `useEffect` 开始或在项目变更的 cleanup 中调用 `setTasks(null)`，使页面在新请求返回前明确呈现“正在读取…”状态。

---

### 5. 主进程 IPC `a2a:issue-dispose` 缺少关闭参数的前置非空校验（P3）
- **位置**：[`workbench/app/main.ts:128-129`](file:///Users/luckye/Documents/Code/a2a/workbench/app/main.ts#L128-L129)
- **场景**：
  IPC 处理程序仅检查了 `reason` 和 `basis` 是否为 `string`，未校验当 `action === 'close'` 时二者是否为非空白字符（`value.trim()`），完全依赖底层门禁拒收。
- **建议**：
  在 IPC 入口处对 `action === 'close'` 明确核实 `reason?.trim()` 与 `basis?.trim()`，提前拦截无效调用。

---

## 三、总体审查结论

**结论**：**INCOMPLETE**

**判定依据**：
1. 核心链路（门禁处置身份修正为 `user`、面板列出问题、发送答复并注入会话、填写依据关闭阻塞问题、徽标更新及端到端变异验证）功能已跑通且方向正确。
2. 但发现两项 P2 级别的可靠性与界面缺陷：
   - 缺陷 1：侧栏高频轮询中单个任务读取问题失败会导致全局侧栏快照拒绝，将全站所有正常运行的项目与 Agent 误判为“未知”；
   - 缺陷 2：问题页面轮询遇到偶发错误时卸载卡片，会导致用户正在编辑的草稿被立即清空；
   - 缺陷 3：空项目读取失败时同时展现报错与“无问题”矛盾文案。
3. 建议产出候选 2 修复上述发现后重新复审。
