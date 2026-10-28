# T-202 独立审查报告

本审查为**只读审查**，依据 [/private/tmp/t-202-review/BRIEF.md](file:///private/tmp/t-202-review/BRIEF.md) 的指引进行。候选补丁 [change.diff](file:///private/tmp/t-202-review/change.diff) 中 [renderer.tsx](file:///Users/luckye/Documents/Code/a2a/workbench/app/renderer.tsx) 混有 T-200（中文项目名展示）与 T-204（窗格关闭保护）的改动，本次审查严格限定在静默提示文案（`silent_foreground`）及新增的端到端测试 [test_t202_silent_hint_e2e.py](file:///Users/luckye/Documents/Code/a2a/workbench/tests/test_t202_silent_hint_e2e.py)。

---

## 逐项核对结果

### 1. 修复是否在根因层、是否改变“不做”、是否引入坏味道
* **根因定位**：根因在于后台 [`watchSilence`](file:///Users/luckye/Documents/Code/a2a/workbench/src/panes.ts#L403-L424) 的触发条件是纯机械事实（前台首进程启动晚于最后输出且静默满 6 秒），后台代码无法预先得知前台命令是否“本该有输出”。修前文案对所有静默进程断言“它可能在等 macOS 的权限弹窗”，对 `sleep 300` 属于误报/过于肯定。修复选择保留机械事实触发条件，在 [renderer.tsx](file:///Users/luckye/Documents/Code/a2a/workbench/app/renderer.tsx#L497-L499) 补充前提条件（“如果它本该有输出……sleep 这类本来就不输出的命令不用管”），把语义判断交给用户，符合项目“脚本管事实，文案/提示词管判断”的设计原则。
* **“不做”项遵循**：票据 [T-202-silent-command-hint.md](file:///Users/luckye/Documents/Code/a2a/.project-map/tickets/T-202-silent-command-hint.md#L27-L29) 明确列出“不做：检测系统弹窗本身”。候选实现没有引入任何系统弹窗探测逻辑，完全遵守边界。
* **结构完整性**：改动仅为单行 JSX 提示文案调整，未引入任何异常吞噬、条件兼容分支或平行 API。

### 2. 文案与代码事实一致性
* **文案逐句核对**：
  1. `“{pane.silent_foreground.command} 启动后还没有任何输出。”` —— 符合 [`watchSilence`](file:///Users/luckye/Documents/Code/a2a/workbench/src/panes.ts#L403-L424) 中 `leader.started * 1000 > outputAt` 且静默满 6 秒的事实。
  2. `“如果它本该有输出（例如 claude、codex 启动后会画出界面），可能在等 macOS 的权限弹窗（例如“想访问‘文稿’文件夹”），弹窗可能被其他窗口挡住了，请移开其他窗口找一找；”` —— 符合真实使用发现（UAT-01 发现 1）中 Claude/Codex 被 macOS “文稿”访问权限弹窗遮挡导致卡死的真实场景。
  3. `“sleep 这类本来就不输出的命令不用管。”` —— 准确指引了误触该机械检查的正常静默命令。
  4. `“有输出后这条提示自动消失。”` —— 符合 [`panes.ts`](file:///Users/luckye/Documents/Code/a2a/workbench/src/panes.ts#L314) 中 `terminal.onData` 收到数据时立即执行 `pane.silentForeground = null` 的代码行为。
* **文档一致性**：[workbench/README.md](file:///Users/luckye/Documents/Code/a2a/workbench/README.md#L306-L311) 相关段落已准确说明了触发条件、文案改动的由来（T-174、L01、T-202）及有输出后撤下提示的机制，与代码事实一致。

### 3. 测试与证据有效性
* **测试场景独立性**：[test_t202_silent_hint_e2e.py](file:///Users/luckye/Documents/Code/a2a/workbench/tests/test_t202_silent_hint_e2e.py) 覆盖真实后台、真实 zsh、Electron 窗口（CDP 驱动）及零模型调用。断言预期直接来源于需求（UAT-01 发现 1、4 与票据验收），而非直接复制实现输出。
* **修前与修后对比**：
  * [red-1.json](file:///Users/luckye/Documents/Code/a2a/evidence/2026-10-27-batch28/T-202/red-1.json)：在 `--revision a3ae46cf2` 下因替身脚本显示为 `sh` 导致 CLI 提示等待超时，记录为测试演进过程中的失败现场。
  * [red-2.json](file:///Users/luckye/Documents/Code/a2a/evidence/2026-10-27-batch28/T-202/red-2.json)：在 `--revision a3ae46cf2` 下执行，使用编译的 `claude` 二进制替身。`sleep_hint_conditional`（缺少“如果它本该有输出”）与 `sleep_hint_not_asserted`（包含了旧断言“它可能在等”）如期失败；同时证明了修前 CLI 静默提示仍能正常出现并在输出后消失。
  * [green-1.json](file:///Users/luckye/Documents/Code/a2a/evidence/2026-10-27-batch28/T-202/green-1.json)：在修后版本执行，4 项检查全部通过（`sleep_hint_conditional`、`sleep_hint_not_asserted`、`silent_cli_still_hinted`、`hint_clears_on_output`）。
* **变异体说明**：[test_t202_silent_hint_e2e.py](file:///Users/luckye/Documents/Code/a2a/workbench/tests/test_t202_silent_hint_e2e.py) 仅定义了 `--revision`，未设置 `--mutant` 参数，证据目录中无 `mutant-*.json`。鉴于本次修复为纯静态文案修改，父修订版 [red-2.json](file:///Users/luckye/Documents/Code/a2a/evidence/2026-10-27-batch28/T-202/red-2.json) 已完整证明修前文案会被精准拒绝，反向反例充分。
* **表格与 JSON 一致性**：[RESULTS.md](file:///Users/luckye/Documents/Code/a2a/evidence/2026-10-27-batch28/T-202/RESULTS.md#L15-L20) 中记录的表格与各 JSON 文件的 `status`、`failed`、`checks` 及报错信息完全一致。

### 4. 验收条件覆盖与未做项说明
* 票据 [T-202-silent-command-hint.md](file:///Users/luckye/Documents/Code/a2a/.project-map/tickets/T-202-silent-command-hint.md#L20-L24) 验收条件：
  1. `修前版本经真实入口：sleep 安静数秒后出现权限弹窗提示；修后不再把它说成可能在等权限，或文案明确“如果它应当有输出”` —— **已通过**，有 [red-2.json](file:///Users/luckye/Documents/Code/a2a/evidence/2026-10-27-batch28/T-202/red-2.json) 与 [green-1.json](file:///Users/luckye/Documents/Code/a2a/evidence/2026-10-27-batch28/T-202/green-1.json) 支撑。
  2. `CLI 真被系统授权弹窗挡住时（可用新打包的 Enchanted Test 复现），提示仍出现` —— **未执行真实系统授权弹窗**。
* **如实报告**：[RESULTS.md](file:///Users/luckye/Documents/Code/a2a/evidence/2026-10-27-batch28/T-202/RESULTS.md#L25-L27) 在 `## 没做（INCOMPLETE）` 一节中明确指出：第 2 条验收使用编译的 `claude` 替身模拟无输出前台进程，未重新打包触发真实的 macOS 系统授权弹窗（因为会在用户屏幕弹出系统弹窗并需人工干预）。票据 [T-202-silent-command-hint.md](file:///Users/luckye/Documents/Code/a2a/.project-map/tickets/T-202-silent-command-hint.md#L5) 保持 `status: open`，未提前勾选该验收项或伪称通过。

---

## 审查发现问题清单

* **位置**：[workbench/tests/test_t202_silent_hint_e2e.py:204](file:///Users/luckye/Documents/Code/a2a/workbench/tests/test_t202_silent_hint_e2e.py#L204)
  * **失败场景**：测试在运行时直接调用外部编译器 `/usr/bin/clang` 编译替身 C 程序。若在未安装 Xcode 命令行工具的最小测试环境执行，测试准备阶段将直接失败抛出异常。
  * **严重程度**：**P3**（项目默认在开发机 macOS 上运行，且已通过；不影响产品运行时代码）。

---

## 结论

**`可合并`**

文案修复精准定位在展示层，未破坏任何机械检查机制；代码与文档事实严格契合；端到端测试可靠地区分了修前与修后状态；未覆盖的真实系统弹窗场景已诚实记录在案。

---

## LIMITATIONS

1. **未在真实 macOS 系统授权弹窗下做端到端验证**：本次仅使用编译的 `claude` 替身（阻断输出直至接收标准输入）验证了“CLI 静默 6 秒后提示出现并在有输出后撤下”的触发路径，未在实际触发 TCC `kTCCServiceSystemPolicyDocumentsFolder` 弹窗的打包版环境中重验。
2. **只读静态审查**：本审查未执行测试脚本重跑，未运行应用界面或后台进程，亦未修改任何文件，所有证据均基于现有工作区代码、补丁 diff 与批次归档证据 JSON 核对推导。