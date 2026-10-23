作为只读审查员，已对 [`test_t107_open_directory_dialog.py`](file:///Users/luckye/Documents/Code/a2a/workbench/tests/test_t107_open_directory_dialog.py)、相关证据文件、被测源码及共用夹具进行了只读审查。以下为审查判断与发现清单。

---

### 一、四个核心问题的审查判断

1. **测试期望来源与判定独立性**：
   - **期望来源独立**：测试中的期望（`expected`）完全来自独立来源——仓库由测试脚本通过系统 `git init` 独立搭建，分支名、ahead/behind 差值直接执行 `git rev-list --left-right --count HEAD...@{u}` 与 `git rev-parse` 获取，符合 [`T-107`](file:///Users/luckye/Documents/Code/a2a/.project-map/tickets/T-107-workbench-sidebar-projects-agent-tree.md#L152) 验收第 4 条。
   - **判定不依赖 Codex 自述**：测试的断言直接读取后台守护进程的 Socket 请求（`sidebar_snapshot`）及 Electron DOM 状态（DevTools CDP 抓取）。Codex 的回复（`codex-last.txt`）仅记录至摘要文本，不作为判定依据。

2. **变异有效性与坏实现穿透风险**：
   - **变异有效性**：变异 `pick-ignored`（将打开目录强行替换为 `homedir()`）在 [`mutant-pick-ignored-02.json`](file:///Users/luckye/Documents/Code/a2a/evidence/2026-10-22-batch20/T-107-dialog/mutant-pick-ignored-02.json#L67) 中被脚本本身的断言 [`registers_the_picked_directory`](file:///Users/luckye/Documents/Code/a2a/workbench/tests/test_t107_open_directory_dialog.py#L125) 真实抓住（抓取到后台登记的是 `.../home` 而非 `pick-me`）。
   - **坏实现穿透风险**：
     - **取消步骤空跑**：初始状态项目列表即为空，若 Codex 在步骤 1 未实际点击对话框“取消”而直接创建 `cancelled`，当前的 `projects() == {}` 仍会通过。
     - **工作区未联动**：测试仅检查了侧栏项目行的 `aria-current="page"`，未验证主工作区 Header（`<h1>`）和终端初始路径是否联动切入新项目。
     - **项目 ID 生成校验缺失**：测试通过 `project = registered[...]['project_id']` 动态读取 ID 去匹配 DOM，如果后台生成了错误的 ID（如随机 UUID），测试仍会通过。

3. **测试本身的设计缺陷**：
   - 存在 `time.sleep(2)` 的硬编码等待；
   - 当 Codex 异常早退时，`wait('后台登记', 20)` 会掩盖原本捕获的退出原因并产生 20 秒超时挂起；
   - 进程清理时未向 Codex 进程组（PGID）发送信号；
   - 运行于用户真实 `~/.codex` 下（系经授权的 Computer Use 依赖妥协，已在结果中声明）。

4. **RESULTS 是否超出证据**：
   - 基本忠实于运行事实。仅有一处微小表述偏差：[`RESULTS.md`](file:///Users/luckye/Documents/Code/a2a/evidence/2026-10-22-batch20/T-107-dialog/RESULTS.md#L32) 宣称“核对了：...项目 id 是 pick-me”，但测试代码仅将其作为动态查询参数，未包含对 ID 命名的显式断言。

---

### 二、发现清单（P0～P3）

#### 无 P0 发现（无阻塞性产品缺陷或伪造证据）

---

#### P1 发现

- **F-01：步骤 1 取消验证缺乏“对话框曾被触发”的正向证据（空态假阴性风险）**
  - **位置**：[`test_t107_open_directory_dialog.py#L99-L115`](file:///Users/luckye/Documents/Code/a2a/workbench/tests/test_t107_open_directory_dialog.py#L99-L115)
  - **证据**：
    测试在开始时断言 `check('starts_without_projects', projects() == {}, projects())`（项目库本就为空）。Codex 被要求点“+”、点“取消”并 `touch cancelled`。测试随后检查 `check('cancel_registers_nothing', projects() == {}, projects())`。
  - **影响**：
    由于前后基线都是 0 个项目，如果 Codex 在第一步因任何偶发原因（如按键未命中、聚焦丢失）完全没有点开对话框而直接执行了指令中的 `touch cancelled`，该断言依然会通过。测试脚本缺乏主进程是否曾真正收到 `a2a:open-project` 并返回 `null` 的探针或变异反例。

---

#### P2 发现

- **F-02：未校验主工作区视图联动，仅校验了侧栏当前项**
  - **位置**：[`test_t107_open_directory_dialog.py#L127-L132`](file:///Users/luckye/Documents/Code/a2a/workbench/tests/test_t107_open_directory_dialog.py#L127-L132) 对比 [`renderer.tsx#L767-L772`](file:///Users/luckye/Documents/Code/a2a/workbench/app/renderer.tsx#L767-L772)
  - **证据**：
    测试只核对了侧栏上的 `[data-project-id={project}]` 具备 `aria-current="page"`。而在 [`renderer.tsx`](file:///Users/luckye/Documents/Code/a2a/workbench/app/renderer.tsx) 中，项目选中会驱动右侧主区域的 `header.task-header h1` 以及后续终端启动的 cwd。
  - **影响**：
    若出现“侧栏切换了高亮，但主工作区仍停留在‘独立终端’或 `viewProject` 状态脱节”的坏实现，测试无法感知。

- **F-03：缺乏针对“取消对话框”分支的变异反例**
  - **位置**：[`test_t107_open_directory_dialog.py#L50-L53`](file:///Users/luckye/Documents/Code/a2a/workbench/tests/test_t107_open_directory_dialog.py#L50-L53)
  - **证据**：
    `patches` 字典中仅有针对打开路径的 `pick-ignored` 变异。没有针对取消分支的变异（例如将 [`main.ts#L343`](file:///Users/luckye/Documents/Code/a2a/workbench/app/main.ts#L343) 的 `if (picked.canceled) return null;` 变异为不返回或返回默认目录）。
  - **影响**：
    取消分支的测试有效性未经历变异破坏验证（Mutation Testing）。

- **F-04：Codex 异常退出时，后续等待会掩盖真实原因并白白挂起 20 秒**
  - **位置**：[`test_t107_open_directory_dialog.py#L119-L123`](file:///Users/luckye/Documents/Code/a2a/workbench/tests/test_t107_open_directory_dialog.py#L119-L123)
  - **证据**：
    在捕获 `marker('opened')` 的异常后，代码无条件执行 `registered = fixture.wait('后台登记', projects, 20)`。
  - **影响**：
    如果 Codex 在打开对话框前发生非正常早退，后台由于未触发任何打开请求，`projects()` 将恒为空。测试会死等 20 秒后报出 `AssertionError: 超时：后台登记`，导致真正的退出根因（`codex_stopped`）在日志中被超时异常掩盖。

- **F-05：取消后使用 `time.sleep(2)` 硬编码固定等待**
  - **位置**：[`test_t107_open_directory_dialog.py#L109`](file:///Users/luckye/Documents/Code/a2a/workbench/tests/test_t107_open_directory_dialog.py#L109)
  - **证据**：
    `marker('cancelled', 600)` 之后直接执行 `time.sleep(2)`，随后立刻抓取 `alerts`。
  - **影响**：
    异步 IPC 与渲染流水线在高负载或低性能宿主机上可能存在竞态条件。

---

#### P3 发现

- **F-06：RESULTS.md 关于 `project_id` 核对的声明超出测试断言范围**
  - **位置**：[`RESULTS.md#L32`](file:///Users/luckye/Documents/Code/a2a/evidence/2026-10-22-batch20/T-107-dialog/RESULTS.md#L32) 对比 [`test_t107_open_directory_dialog.py#L125-L126`](file:///Users/luckye/Documents/Code/a2a/workbench/tests/test_t107_open_directory_dialog.py#L125-L126)
  - **证据**：
    RESULTS 记录“后台登记的正是 pick-me 的 realpath，项目 id 是 pick-me”；但代码中是 `project = registered[expected['repo']]['project_id']`，并未断言 `project == 'pick-me'`。
  - **影响**：
    文本摘要略微超出了代码显式断言边界（尽管运行现场 JSON 中的 `project_id` 确实为 `pick-me`）。

- **F-07：Codex 异常中止清理未杀掉进程组（PGID）**
  - **位置**：[`test_t107_open_directory_dialog.py#L106`](file:///Users/luckye/Documents/Code/a2a/workbench/tests/test_t107_open_directory_dialog.py#L106) 与 [`L141-L143`](file:///Users/luckye/Documents/Code/a2a/workbench/tests/test_t107_open_directory_dialog.py#L141-L143)
  - **证据**：
    `codex` 启动使用了 `start_new_session=True`，但清理时仅调用 `codex.terminate()`，未调用 `os.killpg`。
  - **影响**：
    若 Codex 在执行 `seq 1 120` 等 shell 命令期间被杀，子进程可能残留至自然退出。

---

### 三、审查结论

**结论：`PASS`**

**判定理由**：
1. **被测功能真实通过**：[`main.ts`](file:///Users/luckye/Documents/Code/a2a/workbench/app/main.ts#L337-L348)、[`daemon.ts`](file:///Users/luckye/Documents/Code/a2a/workbench/src/daemon.ts#L467-L484) 与 [`renderer.tsx`](file:///Users/luckye/Documents/Code/a2a/workbench/app/renderer.tsx#L573-L579) 的逻辑完备正确，`dialog.showOpenDialog` 与后台 `project_open`、前端侧栏渲染链路经受住了真实 Electron + 真实 macOS 对话框的端到端检验。
2. **变异与证据链闭环**：变异 `pick-ignored-02` 真实触发了测试脚本自身独立检查器的红态，期望值严格来自 Git 计算，且所有日志、退出码与截图归档均完整保留。
3. **无 P0 缺陷**：所列 P1～P3 发现均属于测试工具本身的断言严密性与健壮性提升点，不影响 [`T-107`](file:///Users/luckye/Documents/Code/a2a/.project-map/tickets/T-107-workbench-sidebar-projects-agent-tree.md) 本身功能的验收结论。
