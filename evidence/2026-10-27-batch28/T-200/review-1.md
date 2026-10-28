# T-200 独立审查报告

基于 [BRIEF.md](file:///private/tmp/t-200-review/BRIEF.md) 的要求，本次审查为**完全只读**（未执行任何 shell 命令，未修改任何文件，未启动后台或应用）。针对候选改动 [change.diff](file:///private/tmp/t-200-review/change.diff)、票据 [.project-map/tickets/T-200-non-ascii-project-name.md](file:///Users/luckye/Documents/Code/a2a/.project-map/tickets/T-200-non-ascii-project-name.md)、文档 [workbench/README.md](file:///Users/luckye/Documents/Code/a2a/workbench/README.md) 以及 [evidence/2026-10-27-batch28/T-200/RESULTS.md](file:///Users/luckye/Documents/Code/a2a/evidence/2026-10-27-batch28/T-200/RESULTS.md) 进行了逐项比对与核验。

---

## 1. 根因与设计原则核对

- **根因层定位**：
  - 问题的根因在于前端视图层（[renderer.tsx](file:///Users/luckye/Documents/Code/a2a/workbench/app/renderer.tsx)）直接将用于门禁标识的 ASCII 项目号（`project_id`）渲染为项目显示文本，导致非 ASCII / 中文目录名生成兜底的 `project` / `project-2` 被直接暴露给用户。
  - 修复通过在 UI 层引入 `projectName(id)`，从项目登记目录路径中截取末级目录名（`name = base(item)`），并在同名项目共存时带上项目号（`${name} · ${id}`）进行区分。
- **“不做”项核验**：
  - 票据明确要求“不做：改项目号的生成规则；已有项目的迁移”。
  - 审查确认：改动仅涉及前端展示组件（[renderer.tsx](file:///Users/luckye/Documents/Code/a2a/workbench/app/renderer.tsx)、[FlowPage.tsx](file:///Users/luckye/Documents/Code/a2a/workbench/app/FlowPage.tsx)、[AppNotifications.tsx](file:///Users/luckye/Documents/Code/a2a/workbench/app/AppNotifications.tsx)、[ProjectSettings.tsx](file:///Users/luckye/Documents/Code/a2a/workbench/app/ProjectSettings.tsx)）与测试夹具，完全未触碰 `daemon.ts`、`project_open`、数据库迁移逻辑或底层门禁契约。
- **错误吞噬与平行路径**：
  - `projectName` 无任何 try-catch 吞错逻辑。在项目列表尚未加载完成或找不到项目对象时，安全降级回显 `id`，属于确定性兜底，未引入兼容分支、重试逻辑或平行 API。

---

## 2. 文案与代码事实一致性

- **[RESULTS.md](file:///Users/luckye/Documents/Code/a2a/evidence/2026-10-27-batch28/T-200/RESULTS.md) 描述核对**：
  - *“按项目登记的目录取最后一段作为名字；另有已打开项目同名时，在名字后带上项目号（`我的 项目 · project`）”*：与 [renderer.tsx](file:///Users/luckye/Documents/Code/a2a/workbench/app/renderer.tsx#L58-L63) 的 `base`、`twin` 判定逻辑完全一致。
  - *“用在侧栏、窗口标题、任务眉标、角色申请横幅三处文案、“在 X 里开一个终端”、移除项目对话框、通知卡片、流程页。侧栏标题的 `title` 属性仍是项目号”*：
    1. 侧栏标题：[renderer.tsx:72](file:///private/tmp/t-200-review/change.diff#L72) 属性 `title={item.project_id}` 保留项目号，内容为 `projectName(item.project_id)`。
    2. 窗口标题：[renderer.tsx:99](file:///private/tmp/t-200-review/change.diff#L99) `viewProject ? projectName(viewProject.project_id) : ...`。
    3. 任务眉标：[renderer.tsx:100](file:///private/tmp/t-200-review/change.diff#L100) `${projectName(task.project_id)} / ${task.name}`。
    4. 角色申请横幅三处文案：[renderer.tsx:118, 122, 131](file:///private/tmp/t-200-review/change.diff#L118-L131) 分别替换为 `projectName(roleRequest.project)`，共计 3 处。
    5. “在 X 里开一个终端”：[renderer.tsx:140](file:///private/tmp/t-200-review/change.diff#L140) `在 ${projectName(viewProject.project_id)} 里开一个终端`。
    6. 移除项目对话框：[renderer.tsx:81](file:///private/tmp/t-200-review/change.diff#L81) 与 [ProjectSettings.tsx:230, 238](file:///private/tmp/t-200-review/change.diff#L230-L238) 的 `RemoveProjectDialog` 标题展示 `移除 {name}`。
    7. 通知卡片：[renderer.tsx:90](file:///private/tmp/t-200-review/change.diff#L90) 与 [AppNotifications.tsx:202, 210, 215](file:///private/tmp/t-200-review/change.diff#L202-L215) 两种通知类型均使用 `nameOf(notice.project)`。
    8. 流程页：[renderer.tsx:109](file:///private/tmp/t-200-review/change.diff#L109) 与 [FlowPage.tsx:153, 160](file:///private/tmp/t-200-review/change.diff#L153-L160) 的泳道头使用 `nameOf(lane.project)`。
  - *“没做：主进程发出的系统通知、`a2a` 回执里的项目仍是项目号（命令与门禁的标识）”*：说明属实，未修改主进程和门禁命令的回执结构。
- **[workbench/README.md](file:///Users/luckye/Documents/Code/a2a/workbench/README.md#L395-L396) 描述核对**：
  - 第 395-396 行：“*界面上项目名用目录名（中文目录的项目号是 `project`），两个同名目录在名字后带上项目号（T-200）；门禁与命令仍用项目号。*” 与代码事实完全吻合。

---

## 3. 测试与证据有效性

测试文件为 [test_t200_project_names_e2e.py](file:///Users/luckye/Documents/Code/a2a/workbench/tests/test_t200_project_names_e2e.py)，采用真实后台、socket、Electron 窗口（通过 CDP 驱动），模型调用为 0。

1. **预期独立性**：
   - 预期源自真实试用缺陷报告 UAT-01 发现 2 与 T-200 需求，断言项目号与门禁记录保持原样（`ids == ['project', 'project-2', 'project-3']`），界面显示目录名，且两处同名目录能区分（带项目号），ASCII 项目（`demo`）显示不变。预期完全独立于实现的局部细节。
2. **红绿与变异对照**：
   - **`red-1-weak-banner-check.json`**：在修前版本 `a3ae46cf2` 运行，因横幅断言写弱导致误判通过，保留为真实历史记录，未作掩盖。
   - **`red-2.json`**：修正断言后在修前版本 `a3ae46cf2` 运行，精确在预期的 4 项检查失败（`sidebar_shows_directory_names`、`twin_directories_distinguishable`、`banner_shows_directory_name`、`heading_shows_directory_name`），其余 3 项底层契约保持通过。
   - **`green-1.json`**：在修后版本运行，7 项检查全过（`PASS`）。真实输出展示 `project: "我的 项目 · project"`、`project-2: "另一个项目"`、`project-3: "我的 项目 · project-3"`。
   - **`mutant-no-twin-suffix.json`**：变异体抹去同名区分逻辑（强制 `return name;`），精准在且仅在 `twin_directories_distinguishable` 失败，变异体被有效击杀。
3. **表格与 JSON 对账**：
   - [RESULTS.md](file:///Users/luckye/Documents/Code/a2a/evidence/2026-10-27-batch28/T-200/RESULTS.md) 表格数据与对应的 4 个 JSON 文件中的 `argv`、`checks`、`failed`、`details` 逐项对应一致。
   - 截图归档记录 [screenshots.archive.json](file:///Users/luckye/Documents/Code/a2a/evidence/2026-10-27-batch28/T-200/screenshots.archive.json) 已完整记录原始文件路径、外置盘归档路径和复现命令。

---

## 4. 验收条件达成情况

- [x] **修前版本经真实入口：打开名为中文的 Git 目录，界面显示 `project`；修后显示目录名。**
  - 证据：`red-2.json`（修前显示 `project` 并失败）与 `green-1.json`（修后显示 `我的 项目 · project` 与 `另一个项目` 并通过）。
- [x] **两个中文名目录同时打开时，界面能区分；项目号与门禁记录不变。**
  - 证据：`green-1.json` 中同名项目分别展示 `我的 项目 · project` 与 `我的 项目 · project-3`；`gate_records_keep_ids` 确保证实数据项目号保持原样；`mutant-no-twin-suffix.json` 反向证明若无法区分则被拒。
- [x] **通用门禁要求（红态优先、不写全局配置、独立审查）。**
  - 证据：真实入口端到端红态（`red-2.json`）；无全局配置改动；本审查作为独立审查。

---

## 5. 发现的问题

- **问题 1（提示性注意）**
  - **位置**：[change.diff:9-10, 19, 28, 37-41, 48](file:///private/tmp/t-200-review/change.diff#L9-L48)
  - **场景**：diff 中混入了 T-204（`closingRef` 窗格关闭防抖）与 T-202（`silent_foreground` 静默文案）的改动。
  - **严重程度**：P3
  - **说明**：BRIEF 已提前说明此情况，审查确认这些改动不影响 T-200 的 projectName 逻辑，但在最终单票提交或 cherry-pick 合并时需注意提交范围的整洁性。

---

## 结论

**`可合并`**

---

## LIMITATIONS

1. **审查手段限制**：本次审查严格遵循只读约束，未使用 shell 工具重新运行自动化测试脚本，未重新启动 Electron 进程复现 CDP 过程；全部结论基于对已有代码 diff、E2E 测试用例逻辑、JSON 原始报告与归档清单的静态核验与交叉对账。
2. **多层混入提交**：[change.diff](file:///private/tmp/t-200-review/change.diff) 中的 `renderer.tsx` 包含了非 T-200 的其它票据修改（T-202 与 T-204），本审查仅覆盖与 `projectName` / T-200 相关的改动部分，不对 T-202 / T-204 的功能完整性背书。
3. **主进程/门禁回执范围**：主进程系统通知以及 `a2a` 命令行直接回执中仍使用规范项目号（ASCII），此项属于票据“不做”范围，未在 UI 替换范围内。