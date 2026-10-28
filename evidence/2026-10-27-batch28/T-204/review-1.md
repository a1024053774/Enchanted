# T-204 独立审查报告

基于对候选补丁 `/private/tmp/t204-review/change.diff`、票据 [.project-map/tickets/T-204-close-terminal-resize-error.md](file:///Users/luckye/Documents/Code/a2a/.project-map/tickets/T-204-close-terminal-resize-error.md)、说明文档 [evidence/2026-10-27-batch28/T-204/RESULTS.md](file:///Users/luckye/Documents/Code/a2a/evidence/2026-10-27-batch28/T-204/RESULTS.md)、同目录下的全部证据 JSON 文件，以及相关生产源码进行的只读代码走查与证据核验，审查结果如下：

---

### 1. 根因与修复层级核对

#### 1.1 根因一致性核对
[RESULTS.md](file:///Users/luckye/Documents/Code/a2a/evidence/2026-10-27-batch28/T-204/RESULTS.md) 描述的根因与底层代码逻辑完全一致：
- 在 [workbench/src/panes.ts](file:///Users/luckye/Documents/Code/a2a/workbench/src/panes.ts#L2200-L2241) 中，当关闭普通终端时，[`closeShell`](file:///Users/luckye/Documents/Code/a2a/workbench/src/panes.ts#L430-L437) 调用 [`terminate`](file:///Users/luckye/Documents/Code/a2a/workbench/src/panes.ts#L2200-L2219)，设置 `pane.closing = true` 并发送 `SIGHUP` 信号，随后在 [`confirmShellExit`](file:///Users/luckye/Documents/Code/a2a/workbench/src/panes.ts#L2220-L2241) 中轮询进程树（最多等待 5 秒）等待前台程序（如 Claude Code 或测试慢退出程序）退出。
- 在此等待窗口期内，daemon 中的 [`RoleRequests.all()`](file:///Users/luckye/Documents/Code/a2a/workbench/src/roleRequests.ts#L61-L65) 因 `alive(terminal.id)` 变为 `false`（`panes.terminalAlive` 检查了 `!pane.closing`），立即将该终端上的待批角色申请判定为 `terminal_gone` 并结束。
- 界面渲染进程收到 `sidebar_snapshot` 更新后，顶部的申请横幅消失，触发整个窗格工作区高度变大，从而触发 [workbench/app/renderer.tsx](file:///Users/luckye/Documents/Code/a2a/workbench/app/renderer.tsx#L276) 的 `ResizeObserver` 回调 [`resize`](file:///Users/luckye/Documents/Code/a2a/workbench/app/renderer.tsx#L260-L274)；同时正在关闭窗格的 [`read`](file:///Users/luckye/Documents/Code/a2a/workbench/app/renderer.tsx#L331-L389) 轮询循环也在此期间向主进程调用 [`a2a:snapshot`](file:///Users/luckye/Documents/Code/a2a/workbench/app/main.ts#L516-L553)。
- 主进程 [workbench/app/main.ts](file:///Users/luckye/Documents/Code/a2a/workbench/app/main.ts#L154) 的 [`sendWindowCommand`](file:///Users/luckye/Documents/Code/a2a/workbench/app/main.ts#L153-L178)（响应 `a2a:resize`）与 [`a2a:snapshot`](file:///Users/luckye/Documents/Code/a2a/workbench/app/main.ts#L522) 均检查了 `pane.closing`，分别抛出 `'Window is not available for input'` 和 `'Task view changed'` 拒绝。
- 渲染进程捕获后，分别由 `failInput` 显示为“输入尚未确认，已停止发送：Error: Error invoking remote method 'a2a:resize'...”，由外层 catch 显示为“Error invoking remote method 'a2a:snapshot'...重新连接”。

#### 1.2 修复层级与真实错误防吞核对
- **修复位置**：修复位于 [workbench/app/renderer.tsx](file:///Users/luckye/Documents/Code/a2a/workbench/app/renderer.tsx#L201) 的 [`SessionPane`](file:///Users/luckye/Documents/Code/a2a/workbench/app/renderer.tsx#L197-L450) 组件层。在用户点击关闭时，通过 `closingRef.current = true` 同步切断渲染层对处于销毁过程中窗格的无效 IPC 调用（`resize` 与 `snapshot` 轮询）。修复在根因层，没有在主进程或 daemon 做未经论证的静默兼容或吞噬。
- **真实错误与恢复逻辑**：
  - 在 [`resize`](file:///Users/luckye/Documents/Code/a2a/workbench/app/renderer.tsx#L260-L274) 中：当 `closingRef.current` 为 `true` 时，守卫阻断了 `window.a2a.resize`，同时**不会更新**内部闭包变量 `dimensions = next`。这意味着若关闭失败（catch 块被触发），执行 `closingRef.current = false; refit.current();` 时，`dimensions !== next` 依旧成立，能够正确补发当前 DOM 实际尺寸给后端 PTY。
  - 在 [`read`](file:///Users/luckye/Documents/Code/a2a/workbench/app/renderer.tsx#L331-L389) 中：`if (!visibility.current.active || closingRef.current) { await delay(); continue; }` 仅在关闭过渡期暂停发送快照与输出请求，未添加任何吞噬异常的 `try-catch`。若关闭失败，恢复轮询后若 snapshot 失败依然会抛入外层 catch 并在 UI 展现。
  - 在 [`closePane`](file:///Users/luckye/Documents/Code/a2a/workbench/app/renderer.tsx#L442-L448) 中：若主进程或 daemon 关闭失败，Promise 异常进入 `.catch`，立即复位 `closingRef.current = false`、`setClosing(false)`、执行 `refit.current()` 补发尺寸，并通过 `setCloseError('关闭窗格未确认：' + String(error))` 在界面弹出警告，没有吞噬关闭失败。

---

### 2. 生命周期与轮询循环核对

- **关闭成功时**：
  1. [`closePane`](file:///Users/luckye/Documents/Code/a2a/workbench/app/renderer.tsx#L442-L448) 调用 `window.a2a.closePane(paneKey)` 成功返回后，触发 `onClose(paneKey, value)`。
  2. 父组件更新 `connectedPaneKeys`，移除了该 `paneKey`，React 卸载该 [`SessionPane`](file:///Users/luckye/Documents/Code/a2a/workbench/app/renderer.tsx#L197-L450)。
  3. 卸载触发 `useEffect` cleanup（L392-L402）：设置 `mounted = false`，调用 `wakeRead.current()` 立即唤醒 `delay()`，使 `while (mounted)` 循环立刻退出；断开 `ResizeObserver` 并执行 `term.dispose()`。生命周期循环正常退出，无内存泄漏与挂起轮询。
- **关闭很慢时**：
  - 在等待前台进程退出的 3～5 秒内，`closingRef.current` 保持为 `true`，`SessionPane` 保持在最后画面，关闭按钮保持禁用态，期间不再对主进程发送会被拒绝的 `resize` 与 `snapshot`。这与关闭中的窗格生命周期预期一致；且后台 `confirmShellExit` 设有 5 秒超时上限，不会无限卡死。
- **关闭失败时**：
  - 若后台关闭超时或抛错，[`closePane`](file:///Users/luckye/Documents/Code/a2a/workbench/app/renderer.tsx#L442-L448) 的 `.catch` 立即将 `closingRef.current` 复位为 `false`；
  - `read()` 循环在下一 tick（最多 100ms 内）恢复执行，从保留的 `cursor` 偏移量继续调用 `a2a.output` 追补最新输出；
  - [`refit.current()`](file:///Users/luckye/Documents/Code/a2a/workbench/app/renderer.tsx#L275) 重新核对并补发因横幅变化引起的 PTY 尺寸。窗格不会永久卡死在旧画面。

---

### 3. 测试区分度与证据核对

#### 3.1 预期来源的独立性
[workbench/tests/test_t204_close_pane_e2e.py](file:///Users/luckye/Documents/Code/a2a/workbench/tests/test_t204_close_pane_e2e.py) 的预期严格来源于票据 [.project-map/tickets/T-204-close-terminal-resize-error.md](file:///Users/luckye/Documents/Code/a2a/.project-map/tickets/T-204-close-terminal-resize-error.md) 验收条件及试用复现场景，断言条件独立于具体修复代码：
- 关闭过程中整个 DOM 不出现内部错误关键词（`BAD = ('Error invoking remote method', 'Window is not available for input', '输入尚未确认', '关闭窗格未确认')`）；
- 申请随终端结束而失效；
- 关闭后再批准必须被拒绝（`approve_after_close_refused`）；
- 剩下的终端依然可写且 PTY 自适应扩展宽度（避免修复将全部 resize 一并误杀）。

#### 3.2 修前红态与变异体核对
- **旧代码红态** [red-3.json](file:///Users/luckye/Documents/Code/a2a/evidence/2026-10-27-batch28/T-204/red-3.json)：
  - 携带 `--revision a3ae46cf2`，在真实 Electron/CDP 入口运行；
  - 在 `no_internal_error_on_close` 失败，捕获到试用出现的原样错误：`a2a:snapshot: Task view changed` 与 `a2a:resize: Window is not available for input`；证明场景能真实复现缺陷。
- **变异体 1** [mutant-resize-while-closing.json](file:///Users/luckye/Documents/Code/a2a/evidence/2026-10-27-batch28/T-204/mutant-resize-while-closing.json)：
  - 变异：去掉 `resize()` 中的 `!closingRef.current`；
  - 结果：在 `no_internal_error_on_close` 失败，捕获到 `a2a:resize` 拒绝错误；证明 resize 守卫有效且敏感。
- **变异体 2** [mutant-poll-while-closing.json](file:///Users/luckye/Documents/Code/a2a/evidence/2026-10-27-batch28/T-204/mutant-poll-while-closing.json)：
  - 变异：去掉 `read()` 中的 `|| closingRef.current`；
  - 结果：在 `no_internal_error_on_close` 失败，捕获到 `a2a:snapshot` 拒绝错误；证明轮询守卫有效且敏感。
- **变异体 3** [mutant-no-resize.json](file:///Users/luckye/Documents/Code/a2a/evidence/2026-10-27-batch28/T-204/mutant-no-resize.json)：
  - 变异：粗暴停掉全部 `resize`（`if (false && ...)`）；
  - 结果：在 `remaining_terminal_pty_follows_view` 处因“剩下的终端变宽”超时失败；证明测试有效防范了误伤正常窗格 resize 的伪修复。

#### 3.3 绿态运行与 RESULTS.md 一致性核对
- [green-4.json](file:///Users/luckye/Documents/Code/a2a/evidence/2026-10-27-batch28/T-204/green-4.json) 包含全部 6 项 checks，全部通过（`status: PASS`，`alerts_seen: []`，`approve_after_close_refused: ok=false, error=request_not_pending`，`cols: 77 -> 159`）。
- **关于 `green-2-run1..4.json` 的改名保留**：
  - 走查 `green-2-run1.json` 至 `green-2-run4.json` 的 `argv` 发现，当时 shell 循环传参错误，将 `--summary "../../evidence/.../red-3 --revision a3ae46cf2.json"` 整个当成 `--summary` 参数传入，未解析出 `--revision` 与 `--mutant`，导致实际执行的均是修后代码。
  - 开发过程没有覆盖或丢弃异常现场（遵守全局规则“Preserve dirty worktrees, earlier artifacts, and failure evidence; never overwrite or discard an anomalous result to make a run look clean”），如实按执行内容改名保留，并在 [RESULTS.md](file:///Users/luckye/Documents/Code/a2a/evidence/2026-10-27-batch28/T-204/RESULTS.md#L35) 详细记录了原因；后续均已单拎参数重新跑出正规的 `red-3.json` 与各 mutant 证据，证据链诚实完整。

---

### 4. 票验收条件对照

| 票据 Acceptance 条件 | 对应检查项 / 运行证据 | 验证结论 |
| :--- | :--- | :--- |
| 1. 修前版本经真实入口：关闭带待批申请的终端后出现上述错误；修后不出现。 | 红态：[red-3.json](file:///Users/luckye/Documents/Code/a2a/evidence/2026-10-27-batch28/T-204/red-3.json)（旧版本 `a3ae46cf2` 准确失败并捕获报错）<br/>绿态：[green-4.json](file:///Users/luckye/Documents/Code/a2a/evidence/2026-10-27-batch28/T-204/green-4.json)（`alerts_seen` 为空，`no_internal_error_on_close` 判定 PASS）<br/>变异体：[mutant-resize-while-closing.json](file:///Users/luckye/Documents/Code/a2a/evidence/2026-10-27-batch28/T-204/mutant-resize-while-closing.json)、[mutant-poll-while-closing.json](file:///Users/luckye/Documents/Code/a2a/evidence/2026-10-27-batch28/T-204/mutant-poll-while-closing.json) | **PASS** |
| 2. 关闭终端后再批准该申请仍被拒绝（不变）。 | 绿态：[green-4.json](file:///Users/luckye/Documents/Code/a2a/evidence/2026-10-27-batch28/T-204/green-4.json) 的 `approve_after_close_refused` 检查明确记录返回 `request_not_pending`，判定 PASS | **PASS** |

---

### 5. 发现的问题与观察

- **问题 1（观察项）**
  - **位置**：[workbench/app/renderer.tsx:443](file:///Users/luckye/Documents/Code/a2a/workbench/app/renderer.tsx#L443)
  - **场景**：用户点击“关闭窗格”后，后台在前台进程挂起退出的 3～5 秒内处于关闭过渡期。此时若用户用鼠标主动点回终端内容区域并敲击键盘，由于 `closePane` 未显式设置 `term.options.disableStdin = true`，按键依然会尝试触发 `window.a2a.input`，被主进程的 `if (pane.closing)` 拒绝并触发 `failInput` 弹窗。
  - **严重程度**：`P3`（用户主动关闭后在几秒过渡期内重新点击打字的概率极低，且关闭完成后窗格正常卸载；不影响本次修复的正常业务逻辑）。

---

### 6. 审查结论

**结论**：`可合并`

候选改动针对 UAT-02 暴露的关闭窗格界面误报问题做了最小必要且准确的根因层修复，不吞噬真实异常，测试预期独立客观，红态、绿态与变异体反事实证据充分完整，票据验收条件均已达成。

---

## LIMITATIONS

1. **未执行真实 Shell 命令与活体应用测试**：本次审查严格遵循用户“只读、不修改文件、不运行 shell 命令”的限制，未在本地直接启动 Electron 窗口或重新运行 pytest/python 测试脚本，动态验证完全基于对测试执行脚本 [workbench/tests/test_t204_close_pane_e2e.py](file:///Users/luckye/Documents/Code/a2a/workbench/tests/test_t204_close_pane_e2e.py)、源码静态逻辑及生成的 JSON 记录的逐行核验。
2. **未直接读取外置盘原始截图文件**：根据项目归档规则，测试生成的 PNG 截图（`before-close.png`、`after-close.png`）存放在外置盘 `/Volumes/WD-Elements/a2a-evidence/2026-10-27-batch28/T-204/`，本次仅查验了本地清单 [screenshots.archive.json](file:///Users/luckye/Documents/Code/a2a/evidence/2026-10-27-batch28/T-204/screenshots.archive.json) 及 JSON 记录中的对应关系，未挂载/读取外部位图数据。