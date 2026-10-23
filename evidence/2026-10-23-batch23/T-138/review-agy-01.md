# T-138 独立审查 01（agy）

- 审查员：agy 1.4.6，模型 gemini-3.8-flash-high，Herdr 可见窗格 wG:pY，交互 auto 模式（只用读文件工具），只读副本，候选 102db97ea。
- 启动 argv：

```
agy --model gemini-3.8-flash-high --mode auto --add-dir /Users/luckye/Documents/Code/a2a-review/T-138-r1 -i "$(cat /Users/luckye/Documents/Code/a2a-review/T-138-r1/prompt.txt)"
# pane wG:pY started 2026-10-23T17:48:17Z
```

- 审查后核对：候选副本 git status 0 行改动。结论 PASS，三条 P3：读屏模式下用方向键在未回车的行内移动时，原生输入框没有可朗读的字符；个别输入法用 Esc 取消时若留下字符，要等下一次输入才清空；README 过期由执行主控在集成时处理。

## 窗格中的报告原文

```text

○ Thought for 4m 56s (The code snippet represents the `paste` function, which handles text insert...)
● Explored 51 files (full.diff, T-138-ime-composition-position.md, RESULTS.md,...) (ctrl+o to expand)

▸ Thought for 1m 42s
   T-138 独立审查报告：终端输入法在行中间插入时文字错位修复

  审查对象：候选提交 102db97ea（相对起点 b99f4869b）
  关联工单：T-138-ime-composition-position.md / 任务卡 T-138-1
  审查依据文件：

  • 生产修改：renderer.tsx:241-264
  • 验收套件：workbench/tests/test_t138_ime_e2e.py
  • 依赖机制核对：CompositionHelper.ts 及 CoreBrowserTerminal.ts
  • 运行证据：evidence/outside-01-.../red.json 与沙箱外第 3 轮证据
  ──────
  ## 1. 修复是否落在根因与竞态分析

  ### 1.1 根因核对

  缺陷的根本原因由 xterm.js 内部机制与浏览器原生输入框行为共同构成：

  1. CompositionHelper.ts` 第 63 行：在 compositionstart 时，记录 this._compositionPosition.start =
  this._textarea.value.length；而在 compositionend 提交时（第 170 行），截取 this._textarea.value.
  substring(currentCompositionPosition.start)。xterm 假定 composition 必定发生在 textarea.value
  的末尾。
  2. CoreBrowserTerminal.ts` 第 1098 行：在非读屏模式下，xterm 对常规按键（包括方向键）调用 this.
  cancel(event, true) 阻止浏览器默认行为，因此光标在隐藏 textarea
  中始终停留在末尾（长度与选区始终一致）；但在读屏模式（screenReaderMode:
  true）下，为了允许屏幕阅读器感知光标，xterm 不对方向键调用
  preventDefault()。用户在终端按左方向键移到行中时，浏览器将隐藏 textarea
  的光标同步移到了字符中间（如选区变为 2..2）。
  3. 当下一次 IME 组合在行中输入“打出”时，浏览器将文字插入在光标位置（索引 2），使 textarea.value
  变成 "前面打出怪了"（长度 6）；但 CompositionHelper 记录的 start 为组合开始前的旧末尾（索引
  4），导致 substring(4) 截取到的是末尾残留的旧文字 "怪了"，刚输入的 "打出" 被丢弃。

  候选在每次提交（onData）后清空 term.textarea.value，切断了旧文字跨组合累积的链条，使得每一次
  compositionstart 时的起点与光标永远对齐在 0，完全消除了光标与 value.length
  脱节的几何错位。修复准确落在根因机制上。

  ### 1.2 竞态与边界场景核对

  在 workbench/app/renderer.tsx` 第 241–264 行 的 setTimeout(..., 0) 清空逻辑中：

  • xterm 读取与清空的先后次序：CompositionHelper._finalizeComposition 在 compositionend
  时通过宏任务 setTimeout(..., 0) 读取 textarea.value 并同步触发 coreService.
  triggerDataEvent，进而同步调用 term.onData。renderer.tsx 的 term.onData 在此时才调度新的
  setTimeout(..., 0) 清空输入框。清空操作位于 xterm 完成读取的下一轮事件循环，绝对不会在 xterm
  读取之前提前清空输入框。
  • 快速连续输入（Fast Consecutive Input）：
      • ASCII 快速输入：_keyDown 同步触发 triggerDataEvent 发往 PTY，不依赖 textarea.value；onData
      内的 clearTimeout(clearInputTimer) 保证连续按键期间平滑防抖，松开时清空。
      • IME 快速输入：新组合触发 compositionstart 时，beginComposition 同步将 composing 设为 true
      并调用 clearTimeout(clearInputTimer) 取消任何未决清空，确保组合过程中输入框内容不受干扰。
  • 粘贴（Paste）：xterm 自身的 Clipboard.ts` 第 55 行 在分发粘贴数据后已主动执行 textarea.value =
  ''，renderer.tsx 的清空定时器与之无冲突、无丢字、无重复。
  • 组合中途失焦（Blur during composition）：浏览器在失焦时自动派发 compositionend，endComposition
  同步复位 composing = false；若失焦前产生了已提交文字，正常进入 onData 清空流程；若无提交则不触发
  onData。
  • IME 取消（IME Cancellation，如按 Esc）：取消组合时浏览器还原 textarea，xterm 的 input.length
  === 0 不触发 triggerDataEvent，故不触发 onData；输入框仍维持组合前的空状态，下次组合起点仍为 0。
  • 同一 tick 多次 onData：clearTimeout(clearInputTimer) 确保同一 tick
  或微任务队列中多次触发时，前序定时器全部被取消，最终只保留一个清空回调，安全防抖。
  • 读屏模式下 xterm 自身同步：通过核查 xterm 源码，_syncTextArea() 仅更新 textarea 的 CSS
  几何位置（style.left/top/width/height），xterm 自身从不把终端终端屏幕的文字写回 textarea.
  value。因此清空 textarea.value 不会破坏或冲突 xterm 的屏幕同步逻辑。
  • 非 IME 普通键入：普通 ASCII 键入由 _keyDown 直接发出 VT 序列，不经过 CompositionHelper
  的截取逻辑，不受清空影响。
  ──────
  ## 2. 读屏模式影响分析（屏幕阅读器依赖）

  ### 2.1 依赖关系与影响机制

  • 终端阅读（Screen Reading）主通道不受影响：xterm.js 的无障碍核心实现完全位于
  AccessibilityManager.ts。它在终端 DOM 顶层动态维护 role="list" 的无障碍行元素树（.xterm-
  accessibility-tree）以及 aria-live="assertive" 的 live-region。屏幕阅读器（如 macOS
  VoiceOver、Windows NVDA）遍历终端内容和接收终端输出公告，均走这套辅助 DOM 树，完全不依赖
  textarea.value 的内容。
  • 打字按键回声（Typing Echo）不受影响：用户敲击单个字符时，浏览器原生事件在当前 tick
  立即触发屏幕阅读器的按键回声播报，随后宏任务中的清空不会追溯取消已发出的系统语音。
  • 局限与轻微影响（P3）：当用户在读屏模式下，试图用左右方向键在未回车的一行中回退光标并依赖原生
  textarea 朗读光标越过的历史字符时，由于 textarea.value
  在每次输入后被重置为空，原生编辑框内无可朗读的字符上下文。但正如 xterm
  源码注释所述，终端历史命令的行内回显主要依赖 PTY 回传及无障碍树，textarea.value 本就因缺少 shell
  提示符及命令输出而无法提供完整上下文。该影响为低严重度（P3），绝不破坏屏幕阅读器的主体功能。
  ──────
  ## 3. 测试套件审查（独立性、双模式覆盖、真实性、反例有效性）

  ### 3.1 测试独立性

  test_t138_ime_e2e.py 严格遵循端到端原则：

  1. 真实链路：拉起完整 Electron 进程、受管 daemon、真实 node-pty 以及原生的 receiver.py
  字节捕获夹具。
  2. 零实现侵入：测试未直接调用 window.a2a.input，未侵入 xterm 私有成员，未通过 DOM 手工修改
  textarea.value。
  3. 断言来源独立：断言直接校验 PTY 最终接收到的 UTF-8 原始字节流（received.
  read_bytes()），期望值来自工单需求（打出 即 e68993e587ba），而非被测代码自身的输出。

  ### 3.2 模式覆盖与 ASCII 驱动修正

  • 双模式覆盖：测试通过点击真实的“设置”对话框切换“读屏软件支持”，在 screen_reader=False 与
  screen_reader=True 两种配置下完整执行相同的种子、行中间多次插入、回车后再插入及 ASCII 混杂测试。
  • CDP 驱动保真度：
      • IME 组合使用 CDP Input.imeSetComposition（触发可信 compositionstart/compositionupdate）与
      Input.insertText（触发 compositionend/input）。针对 Chromium CDP 中 compositionend.
      isTrusted=false
      的固有协议表现，测试如实记录并断言可信的开始/更新/输入事件及实际发生的结束事件，不造假不补发
      。
      • 第 3 轮对 type_ascii 的修正：由旧版的单纯 type='char' 改为发送带有 text/unmodifiedText
      的完整 keyDown 与 keyUp 序列。这契合了 Chromium
      处理键盘输入的真实行为，避免了读屏模式下前一个 Enter 残留的 _keyDownHandled 标志阻断后续
      ASCII 输入的问题。


  ### 3.3 红态与变异反例有效性

  • 起点红态（red.json）：在起点版本 b99f4869b 上运行，读屏开启时 4
  次行中间插入全部精准复现缺陷——期望收到“打出”，PTY 实际均收到旧末尾“怪了”，defect_reproduced
  标志明确置为 true。
  • 坏实现变异（mutant.json）：通过 --mutant retain-input 移除 renderer.tsx
  中的清空语句，读屏开启时的 4
  次行中间插入同样全部被拦截失败（收到“怪了”），有效证明测试具备拒绝坏实现的能力。
  ──────
  ## 4. 修改边界与代码规范核查

  1. 受控文件范围：
      • workbench/app/renderer.tsx：仅改动终端输入监听与 composition 状态管理（净增 18 行）。
      • workbench/tests/test_t138_ime_e2e.py：新增独立 e2e 驱动与断言。
      • evidence/2026-10-23-batch23/T-138/**：新增测试记录与证据。
      • 未改动 workbench/src/**、AGENTS.md、CONTEXT.md、既有回归夹具或 .project-map
      文件，严格限定在授权边界内。
  2. 防御性设计：
      • 组件卸载钩子中严格执行了 clearTimeout(clearInputTimer)
      以及所有新增事件监听的清理（removeEventListener），无内存泄漏或卸载后孤立定时器触发风险。
      • 无全局捕获吞异常，无向下兼容 shim，无硬编码补发，实现紧凑克制。

  ──────
  ## 5. 发现清单（Findings）

  ### [F-01] 读屏模式下清空输入框降低了原生 textarea 光标越字回显能力

  • 文件与行号：renderer.tsx:250
  • 严重度：P3（非阻塞轻微局限）
  •
  失败场景：在读屏模式开启时，用户如果在当前终端行内输入了一段文字后，使用左/右方向键在尚未按回车的
  输入中来回移动光标，屏幕阅读器无法从该隐藏 textarea 中逐字读取光标越过的字符（因为 textarea.value
  已被重置为空）。
  • 处置说明：终端的核心读屏依托 AccessibilityManager 的屏幕行元素列表与 live-region，该局限属于
  ticket 显式要求“不改 xterm
  源码且清空输入框”下的已知且最小代价权衡，不影响终端命令的实际读屏阅读与执行。

  ### [F-02] IME 异常取消（如按 Esc 中止）时若遗留字符需待下一次输入才被清空

  • 文件与行号：renderer.tsx:243-251
  • 严重度：P3（极低概率边界）
  • 失败场景：如果某种非标准输入法在用户按 Esc 取消组合时未将 textarea.value
  恢复为空，由于取消时不触发 onData，输入框可能未能由定时器立刻清空。
  • 处置说明：现代 Chromium 原生 IME 在 Esc
  取消时会自动撤销未提交的未完成文本，且下一次有效键入触发 onData
  时会立即执行清空，在标准运行时中不可见。

  ### [F-03] 候选代码修改引发 README stale 问题已合规上报

  • 文件与行号：project-map-status-04.txt:3
  • 严重度：P3（集成跟踪项）
  • 说明：worker 修改 renderer.tsx 导致 workbench/README.md living doc 判定过期。worker
  受限于任务卡写入边界，未越权修改文档，而是正确通过 scripts/inbox 上报了 worker:b23-t138-issue-
  001，应在执行主控集成阶段统一处理。
  ──────
  ## 6. 审查结论

  候选提交 102db97ea 精准定位了 xterm CompositionHelper
  的几何假定与读屏模式光标移动产生的冲突根因；修复方案遵循最小充分变更原则，无竞态隐患；新增 e2e
  测试完备且严格独立，双模式验证充分，红态与变异反例真实有效，回归验证通过，未越界修改。

  T-138 REVIEW PASS
```
