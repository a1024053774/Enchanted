基于对 candidate.diff（`89cc73645^..df8f972a4`）、背景与测试证据（`RESULTS.md`、`e2e/commands.sh`、各运行摘要 JSON）以及工作台源码和门禁契约的只读审查，四项判断与审查结论如下：

---

### 一、四项核心问题判定

#### 1. renderer 的修复是否正确

* **回放隐藏期间发出的聚焦请求在显示后执行**：
  * **成立**。在 [renderer.tsx](file:///Users/luckye/Documents/Code/a2a/workbench/app/renderer.tsx#L137-L141) 中，当窗格挂载并开始回放 backlog 时，`restoring` 为 `true`（挂载点被 CSS [style.css](file:///Users/luckye/Documents/Code/a2a/workbench/app/style.css#L152) 设为 `visibility: hidden`）。此时 `focusRequest` 传入，因 `if (!focusRequest || !terminal || restoring || ...)` 提前 `return`，且**不消费** `servedFocus.current`。当回放完成（`cursor === total` 且等待两个动画帧）后调用 `setRestoring(false)`，组件重新渲染，`useEffect` 重新触发，此时 `restoring` 为 `false` 且 `servedFocus.current !== focusRequest`，成功执行 `terminal.focus()`。
* **每个请求只执行一次**：
  * **成立**。执行聚焦时同步记录 `servedFocus.current = focusRequest`。对于后续的组件状态变化或重新渲染，`servedFocus.current === focusRequest` 命中早退条件，不会重复触发。
* **是否存在新的抢焦点、焦点丢失或竞态**：
  * **重连（reconnect）**：重连重新触发 `read()`，导致 `restoring` 经历 `true -> false` 的变化；但此时 `servedFocus.current` 仍等于之前的 `focusRequest`，回放结束不会重新执行 `terminal.focus()`，**不会把焦点抢走**。
  * **同一窗格连续两次请求**：父组件在 `selectAgent` 中递增版本号（`previous.version + 1`），第二次请求的版本号必然与 `servedFocus.current` 不等；如果在回放期间连续点击两次，回放结束后仅执行最新的一次；如果在回放后再次点击，立即响应，**逻辑成立**。
  * **回放中途 paneKey 变化**：父组件的 `.pane-slot` 带有 `key={key}`，React 以 `paneKey` 作为 key 协调 DOM，`paneKey` 变动会触发重新挂载全新实例，不会复用已有实例导致状态漂移。
  * **隐藏页签（`terminal-page hidden`）的焦点丢失边缘竞态**（详见发现 P2-1）：若用户在回放耗时期间主动点击其它工作区页签（如“问题”或“Reflect”），外层 `.terminal-page` 变为 HTML `hidden`；回放结束时虽然触发了 `terminal.focus()`，但浏览器对 `hidden` 子元素忽略聚焦操作，同时 `servedFocus.current` 已被置为当前版本。用户随后切回终端页签时，由于依赖项无变化，终端不会自动获得焦点，需要用户再次点击终端或侧栏。
  * **异步聚焦轻微抢焦点窗口**（详见发现 P2-2）：延迟聚焦将原本同步执行的操作延后到回放结束。若回放日志量大，用户在回放间隙主动聚焦了输入框（如设置弹窗或窗格重命名），回放结束瞬间 `terminal.focus()` 会将焦点夺走。

#### 2. 测试改动是否来自独立来源及有效性

* **期望来源的独立性**：
  * `test_t133_codex_terminal_controller_e2e.py` 中新增的项目行检查直接对应 [T-107](file:///Users/luckye/Documents/Code/a2a/.project-map/tickets/T-107-workbench-sidebar-projects-agent-tree.md#L33) Acceptance 第 3 条（“有等待用户回答的项目行最醒目，回答后恢复”），等待时断言 `['1 个等你']`，回答后断言 `[]`。
  * `run_t107_sidebar.py` 针对 `project-1` 的 agent 数量期望从 `0` 改为 `7`，源于 T-107 规格要求侧栏按 Herdr grouped 方式按项目全量分组渲染树，各项目的 agent 树并存于 DOM 中（`project-0` 有 7 个，`project-1` 有 0 个），测试提取的是整个文档的 `data-agent-launch` 元素数，改动符合统一规格。
* **新检查被反例捕获能力**：
  * 反例变异 `project-needs-hidden`（在 `renderer.tsx` 中强制将提示条件置为 `false`）在 `codex-row-mutant-project-needs-hidden` 运行中被准确抓出，失败于 `project_row_needs_user: []`。
  * 修前反例变异 `t107-sidebar-mutant-focus-while-hidden-02`（将 `renderer.tsx` 退回修前版本）在真实 Electron 上运行时准确在聚焦步骤超时失败，实测现场 `active` 为 `BODY|||`、`hasFocus` 为 `True`。
* **“任务原值不变”基准改到迁移之后是否掩盖界面写库**：
  * **未掩盖**。在 [run_t107_sidebar.py](file:///Users/luckye/Documents/Code/a2a/workbench/tests/run_t107_sidebar.py#L187-L189) 中，基准快照 `before` 的取样点位于 `start(candidate)`（已执行 T-123 门禁启动期任务号前缀迁移 `migrateTaskIds`）之后，但在**界面窗口创建（`window(candidate, ...)`）以及任何侧栏/项目/窗格 IPC 与 UI 操作之前**。在整个 UI 测试运行结束前（窗口切换、侧栏点击、聚焦、通知开关、重开），测试重新比对 `SELECT id,data FROM tasks` 必须严格等于 `before`，且此前第 200 行另有 `persistence(state) == before_sidebar` 全表与 trace 零写入断言。这既隔离了后台启动时的预期架构迁移，又完全保留了对 Electron 界面与侧栏只读性的严格约束。

#### 3. 探针清理是否可能误删非预期内容

* **不会误删**。
  * 在 [test_t107_daemon_readonly.mjs](file:///Users/luckye/Documents/Code/a2a/workbench/tests/test_t107_daemon_readonly.mjs#L148) 的 `finally` 块中执行的是：
    `fs.rmSync(join(tree, 'node_modules'), { recursive: true, force: true });`
  * `tree` 被硬绑定为 `join(root, 'runtime')`，而 `root` 是脚本开始时通过 `fs.mkdtempSync('/private/tmp/t107-daemon-read-')` 生成的独立临时目录。
  * 被清理的目标仅为本次探针测试运行在 `/private/tmp` 中使用 `fs.cpSync` 拷入的 ~500 MB 临时依赖，不包含任何指向宿主源码或真实 `workbench/node_modules` 的符号链接（入参已 `dereference: true` 展平）。临时运行目录下的 SQLite 数据库、trace 文件和测试日志均被原样保留作为证据，不会触及工作区或外部文件。

#### 4. RESULTS 的陈述有没有超出证据

* **未超出证据，陈述审慎保真**：
  * RESULTS 第 79~111 节的每一条陈述均与实测生成的 JSON 摘要和 `exits.txt` 一致。
  * 针对反例证据做出了严格区分：明确说明第一次反例 `t107-sidebar-mutant-focus-while-hidden` 因磁盘写满失败，**不算反例证据**，随后在清理磁盘后以 `t107-sidebar-mutant-focus-while-hidden-02` 重新取得了有效的反例失败证据。
  * 诚实指出“只执行一次”保留了修前语义但“没有专门的测试”；诚实指出没有驱动 macOS 系统原生“打开目录”对话框；指出测试总状态按规则固定保留为 `INCOMPLETE`。无超前宣称。

---

### 二、发现清单（P0～P3）

* **P0 / P1**：无。

* **P2-1**
  * **位置**：[renderer.tsx#L137-L141](file:///Users/luckye/Documents/Code/a2a/workbench/app/renderer.tsx#L137-L141) 与 [renderer.tsx#L792](file:///Users/luckye/Documents/Code/a2a/workbench/app/renderer.tsx#L792)
  * **证据**：`useEffect` 仅依赖 `[focusRequest, terminal, restoring]`，不依赖工作区页签状态 `page`。当用户在长回放期间切换到其他页签（如 `issues`、`reflect`），外层 `.terminal-page` 变为 HTML `hidden`（`display: none`）。此时回放结束触发 `setRestoring(false)`，`servedFocus.current = focusRequest` 立即被消费，但 Chromium 忽略对隐藏元素的 `.focus()`。
  * **影响**：若用户在日志重放完成前切走了页签，之后切回终端页时，该窗格不会自动补获键盘焦点，需用户重新在终端内部或侧栏点击一次。

* **P2-2**
  * **位置**：[renderer.tsx#L137-L141](file:///Users/luckye/Documents/Code/a2a/workbench/app/renderer.tsx#L137-L141)
  * **证据**：聚焦请求由同步调用变为挂起等待 `restoring === false`。
  * **影响**：若回放耗时较长，用户在回放间隙主动点击了其它输入元素（如打开设置弹窗、输入重命名等），回放完成瞬间异步唤醒的 `terminal.focus()` 会将键盘焦点抢回终端。该时间窗口通常很短（数十毫秒），但属于潜在的异步焦点争夺。

* **P3-1**
  * **位置**：[RESULTS.md#L86](file:///Users/luckye/Documents/Code/a2a/evidence/2026-10-22-batch20/T-107-recheck/RESULTS.md#L86)
  * **证据**：`RESULTS.md` 注明：“‘只执行一次’保留了修前的语义，没有专门的测试”。
  * **影响**：虽然代码逻辑核对成立（`servedFocus.current === focusRequest`），但缺乏专门模拟 reconnect 阶段检验焦点未被抢回的自动化反例与正例测试。

---

### 三、审查结论

**PASS**

候选变更（`89cc73645^..df8f972a4`）准确查明并修复了 T-118 引入的终端回放隐藏导致的焦点丢失回归，正例与反例均在真实 Electron 入口得到重新证明；测试对数据库只读性契约的校验依然完整；探针依赖清理安全受控；证据记录翔实严谨。发现的 P2 属于极端交互时序下的轻微体验瑕疵，不阻碍本轮提交。
