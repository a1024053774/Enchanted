# 审查报告：v0.1.2 发布与产品页改版

作为只读审查员，本轮审查仅通过只读文件核对代码与证据，未执行任何命令，未修改任何文件。

---

## 发现清单（按 P0～P3 排序）

### P0 阻断缺陷

#### 1. 凭据增量扫描脚本漏扫 `commit`、`tag` 和 `tree` 对象，仅扫描 `blob`
- **文件与行号**: [credential_delta_scan.py#L11-L20](file:///Users/luckye/Documents/Code/a2a/evidence/2026-10-23-batch21/release-0.1.2/credential_delta_scan.py#L11-L20)
- **证据**:
  ```python
  rows = [line.split(' ', 1) for line in git('rev-list', '--objects', 'origin/main..main').decode().splitlines()]
  blobs, names, hits = 0, [], []
  for oid, *path in rows:
      if git('cat-file', '-t', oid).strip() != b'blob': continue
      blobs += 1
  ```
  对照项目基线扫描器 [slim_history.py#L496](file:///Users/luckye/Documents/Code/a2a/evidence/2026-10-19-batch17/T-101/slim_history.py#L496)（`if header[1] in ('blob', 'commit', 'tag'):`），Git 的 commit 信息（提交日志、作者信息、尾注）、annotated tag 内容均可携带 token/key。`credential_delta_scan.py` 显式跳过了所有非 blob 对象。
- **影响**: 若任何提交信息（Commit Message）或标签包含未脱敏凭据，扫描器完全失灵无法报警，存在凭据泄漏风险。

---

### P1 严重缺陷

#### 2. `tour.js` 中第二屏置顶判定 (`< 2px`) 脆弱，轻微负偏移时上滑会触发“跳步”（直接跳到第 10 步），且从首屏滑入第二屏容易失效
- **文件与行号**: [tour.js#L36-L37](file:///Users/luckye/Documents/Code/a2a/docs/assets/tour.js#L36-L37)、[tour.js#L87-L91](file:///Users/luckye/Documents/Code/a2a/docs/assets/tour.js#L87-L91)、[site.css#L62-L70](file:///Users/luckye/Documents/Code/a2a/docs/assets/site.css#L62-L70)
- **证据**:
  1. `tour.js` 定义 `const pinned = () => Math.abs(top()) < 2;`。
  2. 当在导览中间步骤浏览发生微小负偏移（例如页面停在 `top() = -5px`），若用户向上轻微回滚（`delta < 0`），因不满足 `pinned()`，代码落入：
     ```javascript
     else if (delta < 0 && t < 0 && t > -h) { // 下载说明往上：回到最后一步。
       event.preventDefault(); locked = true; stepAt = now; enter(steps.length - 1);
     }
     ```
     这会被误判为“从底部下载区往上回退”，导致用户**直接从第 2～9 步瞬跳到第 10 步（最后一步）**。
  3. 当首屏内容因字号或视口高度稍微撑高（`top() > innerHeight + 1`）时，[tour.js#L87](file:///Users/luckye/Documents/Code/a2a/docs/assets/tour.js#L87) 的 `delta > 0 && t > 0 && t <= h + 1` 判定为假，第一下滚轮无法触发 `enter()`，页面会原生自由滚动而无法对齐第二屏。
- **影响**: 破坏用户要求的“每滚一下鼠标滚轮切换一步”，造成严重跳步和视口不同步。

#### 3. 触摸滑动监听未覆盖全页且强依赖 `pinned()`，移动端触摸切步基本失效
- **文件与行号**: [tour.js#L102-L109](file:///Users/luckye/Documents/Code/a2a/docs/assets/tour.js#L102-L109)
- **证据**:
  1. `touchstart` / `touchmove` / `touchend` 仅挂载在 `tour` DOM 节点上，首屏 `.intro` 根本无触摸监听，移动端无法通过滑动手势进入第二屏导览。
  2. 触摸切步逻辑首行均为 `if (!pinned()) return;`。在 iOS/Android 自然惯性滚动下，页面几乎不可能精确停在 `Math.abs(top()) < 2` 像素内。只要差 2 像素以上，所有触摸切换逻辑全部直接 `return` 放弃处理。
- **影响**: 移动端和触摸屏用户无法上下滑动切步，演示在触控环境下不可用。

#### 4. `check.mjs` 测试未能独立捕获真实交互缺陷，存在“按实现写测试”和路径规避
- **文件与行号**: [check.mjs#L19-L24](file:///Users/luckye/Documents/Code/a2a/evidence/2026-10-23-batch21/release-0.1.2/page-check/check.mjs#L19-L24)、[check.mjs#L48](file:///Users/luckye/Documents/Code/a2a/evidence/2026-10-23-batch21/release-0.1.2/page-check/check.mjs#L48)、[check.mjs#L59-L69](file:///Users/luckye/Documents/Code/a2a/evidence/2026-10-23-batch21/release-0.1.2/page-check/check.mjs#L59-L69)
- **证据**:
  1. 导览滚轮循环中，脚本在 [check.mjs#L20](file:///Users/luckye/Documents/Code/a2a/evidence/2026-10-23-batch21/release-0.1.2/page-check/check.mjs#L20) 显式调用 `page.mouse.move(150, 450)` 将光标强行移到左侧纯说明文本区滚动，刻意避开了右侧演示窗口内的各可滚动面板。
  2. 脚本对方向键（ArrowDown/ArrowUp/PageDown/Space）步进的测试为 0 项（唯一一次键盘操作是 [check.mjs#L48](file:///Users/luckye/Documents/Code/a2a/evidence/2026-10-23-batch21/release-0.1.2/page-check/check.mjs#L48) 按 Escape 关菜单）。
  3. 移动端尺寸检查（[check.mjs#L59-L69](file:///Users/luckye/Documents/Code/a2a/evidence/2026-10-23-batch21/release-0.1.2/page-check/check.mjs#L59-L69)）完全没有触发任何触摸手势（Touch event），而是通过 `scrollTo(...)` 强行置顶，只核对了水平无横向溢出。
- **影响**: 测试套件无法充当真实独立 Oracle，31 项通过结论未能证明用户要求的真实可用性。

#### 5. `RESULTS.md` 将多项未核对或不符合验收的事项上调为 `PASS`
- **文件与行号**: [RESULTS.md#L9-L14](file:///Users/luckye/Documents/Code/a2a/evidence/2026-10-23-batch21/release-0.1.2/RESULTS.md#L9-L14)
- **证据**:
  1. `/Applications 更新`: 明文写着 `“PASS；窗口未目视核对 ... osascript 无辅助功能权限，窗口是否出现没有核对”`。违反项目全局规则“`never round an incomplete result up to PASS. Report unknowns, skipped checks, and stale evidence plainly.`”，真实状态应为 `INCOMPLETE`。
  2. `T-115、T-116`: 明文写着 `“PASS（按用户决定不再做） ... 验收条件没有达成”`，验收未达成不能登记为 `PASS`。
  3. `推送`: 登记为 `PASS`，但其前置扫描脚本存在 Commit 漏扫（见 Finding 1），且 63 处凭据豁免未获得用户确认（见 Finding 6）。
- **影响**: 证据报告失真，违反 a2a 项目验收纪律。

#### 6. `credential-exemptions-03.json` 新增的 63 条豁免缺少用户授权引用
- **文件与行号**: [credential-exemptions-03.json#L32-L34](file:///Users/luckye/Documents/Code/a2a/evidence/2026-10-23-batch21/release-0.1.2/credential-exemptions-03.json#L32-L34)
- **证据**:
  - `credential-scan-01.json` 中的 63 处命中经核对全部落在 `evidence/` 与 `workbench/tests/` 下的测试用例中，确实都是测试夹具伪字符串。
  - 但是，历史版本 [credential-exemptions-01.json#L6](file:///Users/luckye/Documents/Code/a2a/evidence/2026-10-19-batch17/T-101/credential-exemptions-01.json) 声明了 `"不授权任何未列的新命中"`，T-114 增加 36 项时通过对话征询了用户。而本次 0.1.2 发布的 63 项仅在 L32 注记 `"63 entries added after reading each hit in credential-scan-01.json..."`，无用户原话引用和授权记录。
- **影响**: 代理人自主给 63 处凭据命中加白名单，违反授权约束。

---

### P2 中度缺陷

#### 7. 演示代码缺少真实界面的多个筛选控件与明细数据表格，且证据中未予说明
- **文件与行号**:
  - [demo.js#L543](file:///Users/luckye/Documents/Code/a2a/docs/assets/demo.js#L543) 对照 [RecordsPage.tsx#L48-L50](file:///Users/luckye/Documents/Code/a2a/workbench/app/RecordsPage.tsx#L48-L50)
  - [demo.js#L555-L575](file:///Users/luckye/Documents/Code/a2a/docs/assets/demo.js#L555-L575) 对照 [MetricsPage.tsx#L43-L46](file:///Users/luckye/Documents/Code/a2a/workbench/app/MetricsPage.tsx#L43-L46)、[MetricsPage.tsx#L59-L63](file:///Users/luckye/Documents/Code/a2a/workbench/app/MetricsPage.tsx#L59-L63)
  - [demo.js#L605-L609](file:///Users/luckye/Documents/Code/a2a/docs/assets/demo.js#L605-L609) 对照 [RetrospectiveSections.tsx#L69-L77](file:///Users/luckye/Documents/Code/a2a/workbench/app/RetrospectiveSections.tsx#L69-L77)
- **证据**:
  1. **记录页**: 真实应用拥有“任务”和“会话”两个筛选器，演示中遗漏了“会话”筛选器。
  2. **指标页**: 真实应用拥有“从……到……”的日期范围筛选器，且“模型使用”区块下展示了汇总表和会话明细表（含任务、角色、CLI、模型、强度、回合数）两个表格；演示中删除了日期筛选器，且遗漏了整张会话明细表。
  3. **复盘设置**: 真实应用“定期复盘”包含执行角色/模型/强度的表单配置与保存按钮；演示中只有纯文本展示，无法配置执行者。
  4. **Dock 角标**: 演示在窗口顶栏放了一个红色角标元素（[demo.js#L647](file:///Users/luckye/Documents/Code/a2a/docs/assets/demo.js#L647)），真实应用角标位于系统 Dock，窗口内无此组件。
  5. [RESULTS.md#L22](file:///Users/luckye/Documents/Code/a2a/evidence/2026-10-23-batch21/release-0.1.2/RESULTS.md#L22) 宣称“演示与真实应用的差别：有角色申请时通知移到窗口右下；通知悬停时保留底色”，未说明上述实质功能差异。
- **影响**: 演示与最新真实界面存在未披露的不一致。

#### 8. 焦点位于演示内部按钮时与全局导览方向键冲突
- **文件与行号**: [tour.js#L94-L100](file:///Users/luckye/Documents/Code/a2a/docs/assets/tour.js#L94-L100)
- **证据**:
  - `tour.js` 的键盘监听排除了输入框和 `.pane-menu`，但没有排除普通的 `<button>`。
  - 当键盘焦点位于演示区域内的按钮（如项目行、标签页）时，用户按上下方向键浏览列表，事件会被 [tour.js#L99](file:///Users/luckye/Documents/Code/a2a/docs/assets/tour.js#L99) 截获并调用 `preventDefault(); move(direction)`，强行切走整个演示场景。
- **影响**: 键盘导航发生冲突，破坏键盘可访问性底线。

#### 9. 设置弹窗缺乏键盘焦点陷阱 (Focus Trap)
- **文件与行号**: [demo.js#L899](file:///Users/luckye/Documents/Code/a2a/docs/assets/demo.js#L899)
- **证据**: 设置对话框虽然声明了 `aria-modal="true"`，但仅监听了 `Escape` 键关闭，未对 `Tab` 键进行循环捕获。键盘用户按 Tab 键会直接穿透背景遮罩，聚焦到底部不可见或被阻挡的元素上。
- **影响**: 违反 WAI-ARIA 模态弹窗可访问性标准。

---

### P3 轻微问题

#### 10. 问题上报关闭卡片包含源码中不存在的额外提示文字
- **文件与行号**: [demo.js#L525](file:///Users/luckye/Documents/Code/a2a/docs/assets/demo.js#L525) 对照 [IssuesPage.tsx#L70-L74](file:///Users/luckye/Documents/Code/a2a/workbench/app/IssuesPage.tsx#L70-L74)
- **证据**: `demo.js` 中多了 `<p class="record-meta">标了“阻塞”的问题只有你能关闭。</p>`，而真实应用的 `IssuesPage.tsx` 表单内无此行。
- **影响**: 文案轻微出入。

---

## 审查结论

# `NO_GO`

**判定理由**:
1. **安全门禁漏洞 (P0)**: 发布验证使用的 `credential_delta_scan.py` 过滤并跳过了 Git `commit`、`tag` 和 `tree` 对象，仅扫描 `blob`，未能覆盖提交日志与标签中的凭据风险。
2. **用户交互缺陷 (P1)**: `tour.js` 对第二屏的对齐判断存在盲区，轻微偏移即出现跳步（直接跳至第 10 步）；移动端触摸滑动切步未生效；`check.mjs` 测试缺乏证伪能力，未测试键盘与触摸边界。
3. **证据合规问题 (P1)**: `RESULTS.md` 将未目视核对的 `/Applications 更新` 和未达成验收的 `T-115/T-116` 擅自记为 `PASS`；63 处凭据豁免未见用户明确授权记录。
