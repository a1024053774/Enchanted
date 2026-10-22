# T-132 候选 2 独立审查报告

**审查对象**：
- 候选提交：`7dd585c92`（面板显示问题上报：列表、状态、答复与处置；候选 2 修复）
- 父提交：`ea68df9d9`（候选 1 基线）
- 改动汇总：`/private/tmp/claude-501/-Users-luckye-Documents-Code-a2a/193bb4d9-d8a5-4f5f-9e0a-4a1f8bbc5df3/scratchpad/agy-t132c2-euy1/full.diff`
- 需求来源：[.project-map/tickets/T-132-issue-reports-in-panel.md](file:///Users/luckye/Documents/Code/a2a/.project-map/tickets/T-132-issue-reports-in-panel.md)
- 上轮审查：[evidence/2026-10-22-batch20/T-132/candidate-1/review-01.md](file:///Users/luckye/Documents/Code/a2a/evidence/2026-10-22-batch20/T-132/candidate-1/review-01.md)
- 本轮证据：[evidence/2026-10-22-batch20/T-132/candidate-2/RESULTS.md](file:///Users/luckye/Documents/Code/a2a/evidence/2026-10-22-batch20/T-132/candidate-2/RESULTS.md) 与 [evidence/2026-10-22-batch20/T-132/candidate-2/e2e/](file:///Users/luckye/Documents/Code/a2a/evidence/2026-10-22-batch20/T-132/candidate-2/e2e/)

---

## 一、审查 01 五项处理核实

| 发现项 | 严重度 | 修复位置 | 处理方式与核查结论 |
| --- | --- | --- | --- |
| **P2-1**：侧栏逐任务读问题，单个任务读取失败导致全局侧栏拒绝 | P2 | [`workbench/src/daemon.ts:318-324`](file:///Users/luckye/Documents/Code/a2a/workbench/src/daemon.ts#L318-L324) | **已妥善处理**。当某任务 `!result.ok` 时，立即置 `waiting = null` 并 `break` 退出该项目循环，不再向外 `throw new Refusal`，保证其他项目与侧栏全局快照（Agent 树、窗格等）正常工作；前端将其呈现为“问题数未知”。 |
| **P2-2**：轮询瞬时出错导致卡片卸载、未发送草稿丢失 | P2 | [`workbench/app/IssuesPage.tsx:37`](file:///Users/luckye/Documents/Code/a2a/workbench/app/IssuesPage.tsx#L37) | **已妥善处理**。卡片列表去除了 `!error` 条件，出错时保留已有卡片，仅顶部展示错误条；同时将操作后的 `setVersion` 刷新与切换项目的重置解耦，操作后刷新不再卸载卡片。端到端测试与变异已证实草稿保留。 |
| **P2-3**：空项目读取失败时同时展现报错与“还没有问题上报”矛盾文案 | P2 | [`workbench/app/IssuesPage.tsx:36`](file:///Users/luckye/Documents/Code/a2a/workbench/app/IssuesPage.tsx#L36) | **已妥善处理**。在第 36 行增加了 `!error` 守卫条件，当发生读取失败时互斥隐藏空列表文案。端到端测试 `--empty-failure` 及变异体已证明。 |
| **P3-4**：切换项目时残留上一个项目的问题列表 | P3 | [`workbench/app/IssuesPage.tsx:16`](file:///Users/luckye/Documents/Code/a2a/workbench/app/IssuesPage.tsx#L16) | **已基本处理**。新增独立 `useEffect(..., [project])`，在 `project` 变更时调用 `setTasks(null); setError(null);`。经核验不存在异步串台竞态；细节观察见下文。 |
| **P3-5**：IPC 关闭入口缺少 `reason` 与 `basis` 的前置非空校验 | P3 | [`workbench/app/main.ts:260-262`](file:///Users/luckye/Documents/Code/a2a/workbench/app/main.ts#L260-L262) | **已妥善处理**。在主进程 IPC 入口严格增加了 `(action === 'close' && ![reason, basis].every(value => typeof value === 'string' && value.trim()))` 校验，空白或缺省参数直接在窗口侧拒收。 |

---

## 二、问题数未知（null）全链路核查

重点核查了侧栏、页签、通知、Dock 徽标等链路中，是否都妥善处理了 `issues_waiting === null`，以及有无误当成 `0` 或抛出运行时异常：

1. **后台协议**（[`workbench/src/daemon.ts:318-324`](file:///Users/luckye/Documents/Code/a2a/workbench/src/daemon.ts#L318-L324)）：
   - 累加器类型显式声明为 `let waiting: number | null = 0;`。
   - 单个任务失败后，`waiting = null; break;` 立即生效并截断后续无效查询，返回 `{ ...project, issues_waiting: null }`。
   - 所有任务均正常时，返回累加计数值（`number >= 0`）。
2. **侧栏项目行**（[`workbench/app/renderer.tsx:63, 720-721`](file:///Users/luckye/Documents/Code/a2a/workbench/app/renderer.tsx#L63)）：
   - 类型契约扩充为 `issues_waiting: number | null;`。
   - 渲染逻辑：
     ```tsx
     {item.issues_waiting === null ? <span className="project-needs" data-project-issues="unknown" title="这个项目的问题列表读取失败">问题数未知</span>
       : item.issues_waiting > 0 && <span className="project-needs" data-project-issues={item.issues_waiting}>{item.issues_waiting} 个问题</span>}
     ```
   - 优先通过严格等值检查 `=== null`，正确渲染带有琥珀色警告样式的“问题数未知”徽标与 `data-project-issues="unknown"` 属性，并附带悬浮提示；未将 `null` 隐式转为 `0`，也没有把未知当成“没有问题”。
3. **工作区“问题”页签**（[`workbench/app/renderer.tsx:685, 749-750`](file:///Users/luckye/Documents/Code/a2a/workbench/app/renderer.tsx#L685)）：
   - `const issuesWaiting = project ? project.issues_waiting : 0;`：当未选中项目时兜底为 0（不显徽标）；当选中项目的问题数为 `null` 时，`issuesWaiting` 正确透传为 `null`。
   - 页签按钮渲染：
     ```tsx
     问题{issuesWaiting === null ? <span className="tab-needs" aria-label="问题数读取失败">?</span>
       : issuesWaiting > 0 && <span className="tab-needs" aria-label={`${issuesWaiting} 个等你决定`}>{issuesWaiting}</span>}
     ```
   - 严格在 `issuesWaiting === null` 时显示 `?`，并提供无障碍标签 `aria-label="问题数读取失败"`。
4. **应用通知与 Dock 徽标**（[`workbench/app/notificationCenter.ts`](file:///Users/luckye/Documents/Code/a2a/workbench/app/notificationCenter.ts#L29-L51)、[`workbench/app/main.ts:38-45`](file:///Users/luckye/Documents/Code/a2a/workbench/app/main.ts#L38-L45)）：
   - 核对票据要求：`T-132` 明确规定“新上报出现时在面板与项目行提示（应用内，不调用系统通知，沿用 T-110）……不做系统通知”。
   - 系统 `NotificationCenter` 与 Dock 徽标仅监听 Agent 的等待用户提问（`waiting_user_answer`）及主控配额报警（`quota`），未接入亦不需要接入 `issues_waiting`，因此不存在将其误读为 `0` 或导致通知组件抛错的情况。

---

## 三、草稿保留与切换项目 Effect 及竞态深度分析

在 [`workbench/app/IssuesPage.tsx:16-27`](file:///Users/luckye/Documents/Code/a2a/workbench/app/IssuesPage.tsx#L16-L27) 中，组件采用了两个拆分的 Effect：
```tsx
// A project switch starts from "reading"; a refresh after an action keeps the cards and their drafts.
useEffect(() => { setTasks(null); setError(null); }, [project]);
useEffect(() => {
  if (!project) return;
  let mounted = true;
  const load = () => window.a2a.issues(project).then((value: TaskIssues[]) => {
    if (!mounted) return;
    setTasks(value); setError(null);
  }, (reason: unknown) => { if (mounted) setError('问题列表读取失败：' + String(reason)); });
  void load();
  const timer = setInterval(load, 3000);
  return () => { mounted = false; clearInterval(timer); };
}, [project, version]);
```

### 1. 竞态防护分析
- **项目快速切换时无旧数据串台**：
  当用户从项目 A 切换到项目 B 时，Effect 2 针对项目 A 的 cleanup 立即执行（`mounted = false; clearInterval(timer);`）。此时项目 A 的异步 IPC 无论何时返回，均会被 `if (!mounted) return;` 拦截丢弃；项目 B 的闭包拥有独立的 `mounted = true`，确保最终渲染仅反映项目 B 的事实。
- **操作后刷新无旧轮询倒流覆盖**：
  当用户在某张卡片上点击提交（答复或关闭）后，触发 `changed() => setVersion(v => v + 1)`。此时 `version` 递增使 Effect 2 重新挂载，清理旧的定时器并将前一次周期的 `mounted` 置为 `false`，从而取消了先前在途中、尚未落地的旧轮询结果；新挂载的 Effect 2 立即发起一次最新的数据拉取，杜绝了操作前的旧数据覆盖操作后新状态的竞态问题。
- **草稿保留机理**：
  由于 `setTasks(null)` 仅依赖 `[project]`，在同一项目内执行操作（仅改变 `version`）或后台 3 秒定时轮询时，`tasks` 保持连续更新，外层 `<Issue key={view.issue.id} ... />` 依靠不变的 `key` 保持组件实例不被卸载，其内部各输入框的状态（`answer`、`reason`、`basis`）得以完整保留。

---

## 四、测试与变异证据核查

候选 2 的端到端测试机制全面，且均在 `7dd585c92` 的隔离干净 worktree 内通过 DevTools 协议（CDP）对真实 Electron 应用完成全流程验收：

1. **正向与回归测试**：
   - `green`（[`green.json`](file:///Users/luckye/Documents/Code/a2a/evidence/2026-10-22-batch20/T-132/candidate-2/e2e/green.json)）：通过全部 6 项核心断言（徽标展示、门禁状态一致、答复送达 worker 窗格并记为 user 答复、关闭记录保留且含依据、读取失败展示错误非空列表、草稿在断开后台后幸存）。
   - `empty-failure`（[`empty-failure.json`](file:///Users/luckye/Documents/Code/a2a/evidence/2026-10-22-batch20/T-132/candidate-2/e2e/empty-failure.json)）：覆盖无问题的空项目断开后台场景，核实只显示错误提示。
   - `t122-green`：23 项端到端流程全量通过，证明门禁与操作员身份改动未破坏既有主控/worker 调度。
2. **反事实（已知坏实现对比）**：
   - `red-candidate-1`（`--revision ea68df9d9`）：在候选 1 源码上复现，确在 `draft_survives_failed_read` 断言处失败（断网轮询后卡片被卸载，草稿丢失）。
   - `red-candidate-1-empty-failure`：在候选 1 源码上复现，确在 `empty_project_failure_is_not_no_reports` 断言处失败（错误信息与“还没有问题上报”同时显示）。
3. **变异体全量击杀验证**：
   - `mutant-cards-dropped-on-error`：突变还原为错误时卸载卡片，测试失败于 `draft_survives_failed_read`。
   - `mutant-empty-shown-with-error`：突变还原为缺少 `!error` 检查，测试失败于 `empty_project_failure_is_not_no_reports`。
   - `mutant-error-shown-as-empty`：突变还原为读取失败伪装为空列表，测试失败于 `read_failure_is_not_an_empty_list`。
   - `mutant-disposition-as-executor`：突变还原为处置记为 executor，测试失败于关闭阻塞问题超时。
4. **未覆盖点客观评估**：
   - `RESULTS.md` 真实反映了未覆盖项：单任务在真实后台崩溃产生 `null` 未跑端到端（因需要人为破坏门禁 SQLite 底层），由代码静态核查覆盖；“稍后再看”由主进程/门禁协议单元逻辑覆盖。

---

## 五、审查发现明细

### 发现 1：切换项目时通过 useEffect 异步置空存在 1 帧旧卡片残影（P3）
- **位置**：[`workbench/app/IssuesPage.tsx:16`](file:///Users/luckye/Documents/Code/a2a/workbench/app/IssuesPage.tsx#L16)
- **场景**：
  在 React 渲染流程中，当从项目 A 切换到项目 B 时，传给 `IssuesPage` 的 prop `project` 发生变化。在 React 执行渲染函数时，`tasks` 状态仍保留着项目 A 的数组，因此在这一轮 commit 到 DOM 时，页面短暂渲染出项目 A 的卡片；随后 commit 阶段后运行的 `useEffect(..., [project])` 触发 `setTasks(null)`，再调度第二次渲染显示“正在读取…”。
  虽然这不会导致数据污染或功能失效（异步 IPC 响应被 `mounted` 机制有效阻断），但在视觉上会产生轻微的旧列表闪烁。
- **改进建议**：
  在父组件调用处传 `key`（例如在 [`renderer.tsx:758`](file:///Users/luckye/Documents/Code/a2a/workbench/app/renderer.tsx#L758) 写为 `<IssuesPage key={selectedProject} project={selectedProject} />`），由 React 树节点生命周期在切换项目时自然重置内部所有状态，既消除了闪烁，也可以省去第 16 行的特殊 `useEffect`。

---

## 六、总体审查结论

**结论**：**PASS**

**判定依据**：
1. 上一轮审查提出的 3 项 P2 缺陷及 2 项 P3 缺陷均已得到彻底且合理的修复；
2. 全链路核查确认 `issues_waiting === null` 在后台收集、项目行徽标展示、页签提示以及无障碍语义上均得到严谨处理，无误作 0、无报错；
3. 草稿保护与防竞态设计逻辑完备，并经变异体和已知坏实现（候选 1 父提交）的双向端到端反例严格验证；
4. 遗留的 1 项 P3 建议属于次要渲染优化，不影响功能交付与系统稳定性。具备集成条件。
