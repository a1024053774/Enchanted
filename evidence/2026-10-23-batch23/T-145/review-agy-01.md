# T-145 独立审查 01（agy）

- 审查员：agy 1.4.6，模型 gemini-3.8-flash-high，Herdr 可见窗格 wG:pD，交互 auto 模式（只用读文件工具），只读副本，候选 32d4f0f40。
- 启动 argv：

```
agy --model gemini-3.8-flash-high --mode auto --add-dir /Users/luckye/Documents/Code/a2a-review/T-145-r1 -i "$(cat /Users/luckye/Documents/Code/a2a-review/T-145-r1/prompt.txt)"
# pane wG:pD started 2026-10-23T12:43:33Z
```

- 审查后核对：候选副本 git status 0 行改动。结论 PASS，一条 P3（RESULTS.md 与 RUN-OUTSIDE 未入候选提交：worktree 继承稀疏检出，evidence 路径被跳过；执行主控在本提交补入）。

## 窗格中的报告原文

```text

○ Thought for 4m 8s (`exec/t145` and `c...)
● Explored 44 files (ctrl+o to expand)

▸ Thought for 31s
   T-145 候选交付独立审查报告

  审查对象：T-145 候选提交
  32d4f0f40baf791f38eff6a058830fe6141d8a5
  3
  基线版本：f8aa846252ddd97008a5e506469ce
  30024aaacab（main）
  审查范围：终端控制上报（SGR
  鼠标、焦点、设备状态回复等）输入过滤与
  透传、键入记录保护、测试证据与回归对照
  。
  ──────
  ## 一、逐项核对结论

  ### 1. 协议区分规则与真实用户键入保护

  • 规则纯粹基于终端控制协议格式：
  在 [panes.
  protocolReport
  的判定完全建立在终端控制协议序列标准（C
  SI / OSC / DCS
  前缀、控制参数与终结字符）的正则解析上
  ：
      • 二进制模式匹配标准 X10
      鼠标报文：/^(?:\x1b\[M[\s\S]{3})+
      (?![\s\S])/。
      • UTF-8 文本模式匹配完整 ANSI/xterm
      上报序列（SGR 鼠标 CSI <...
      M/m、urxvt 鼠标 CSI ...M、焦点 CSI
      I/O、设备状态 CSI 0n、光标报告 CPR
      CSI ...R、设备属性 DA CSI ...
      c、模式报告 DECRPM CSI ...
      $y、窗口控制 CSI ...t、调色板 OSC
      \x1b]...、DCS DECRQSS 回复）。
      •
      没有对用户文本内容做任何关键词匹配
      或意图分类，严格遵守了“不通过正则揣
      测用户意图”的架构约定。
  • 真实键入绝不被误判为上报：
      • 普通文字与中文：不以 CSI/OSC/DCS
      开头，正则完全不匹配。
      • 方向键：\x1b[A / \x1b[B / \x1b[C
      / \x1b[D，CSI 内无匹配单字母
      A/B/C/D 的规则，不匹配。
      • 独立 Esc（如 Vim 中按 Esc）：\x1b
      单字符不匹配 CSI
      格式，走既有的中断与退回逻辑（[pane
      s.
      ts#L1143](file:///Users/luckye/Docu
      SS3 序列（\x1bOP 等），F5–F12
      采用波浪号终结符（\x1b[15~
      等），均不被匹配；特别是带修饰键的
      F3（\x1b[1;2R 至 \x1b[1;
      16R），实现中特意添加了负向前瞻
      (?!1;(?:[2-9]|1[0-6])R)
      排除，避免被 CPR
      规则误伤，确保作为按键记录。
      • Alt 组合键：如 \x1ba 或 \x1b[1;
      3A，不匹配。
      • 粘贴带 ESC 文本与 Bracketed
      Paste：括号粘贴以 \x1b[200~
      开头并被单独识别为
      pasted，协议正则不含 200~
      分支；普通粘贴若含文字与 ESC
      混合，由于正则要求从开头 ^ 到结尾
      (?![\s\S])
      全串均为协议上报，混合串无法全串匹
      配，因此被安全归为真实输入记录。


  ### 2. PTY 透传与混合输入处理

  • 控制上报原样送达 PTY：
  在 panes.ts:1162，pane.pty.write(binary
  ? bytes : data)
  处于无条件执行分支中，未受
  !protocolReport 的限制。变异测试
  electron-mutant-drop 证明一旦在写入 PTY
  时吞掉序列，CLI
  会因收不到鼠标坐标而超时失败。
  • 混合输入处理：
      • 连续合法上报（如连续多次鼠标移动
      \x1b[<35;9;3M\x1b[<35;10;3M
      或鼠标混合焦点回复）：外层 +
      贪婪连续匹配，正确判为
      protocolReport，不产生误记录。
      • 上报与真实文字交织（如 \x1b[<35;
      9;3Mhello）：由于无法整串完全匹配协
      议包，protocolReport 判定为
      false，遵循防御性原则整串保留并记录
      ，绝不丢字漏记。


  ### 3. 修改边界、验收文件与代码健康度

  • 修改边界：
      • 生产代码仅修改了 [panes.
      ts](file:///Users/luckye/Documents/
      中的输入转发路径（共 13 行增删）。
      • 未修改任何禁止路径：renderer.
      tsx、main.ts、gates/** 逻辑、.
      project-map/**、AGENTS.md、CONTEXT.
      md 均未触碰。
  • 验收文件（oracle_paths）：
      •
      workbench/tests/test_t133_t134_reco
      rds_metrics_e2e.py 与
      workbench/tests/test_t091_pane_ipc.
      mjs 零修改。
  • 异常处理与设计完整性：
      • 无异常吞噬：PTY
      写入异常记录后继续向上抛出（throw
      error），assertCurrent()
      身份检查保持同步校验并抛出
      Refusal。
      • 无
      fallback、降级分支或平行兼容路径，
      修改在单点就地完成，符合 Deep
      Modules 设计准则。


  ### 4. 测试独立性与两轮运行核实

  • 期望值独立性：
  [test_t145_mouse_reports_e2e.
  内部根据窗口尺寸、CDP 鼠标坐标与终端
  SGR 协议格式独立计算期望字节串
  \x1b[<35;col;
  rowM，严格与接收端写入文件比对，期望值
  完全独立于待测实现。
  • 第 2 轮改用 keypress 的根因核查：
      • 第 1 轮超时的原因是测试端直接调用
      CDP Input.insertText，而 [renderer.
      renderer.tsx:187 中启用了
      screenReaderMode: true。xterm
      在无障碍屏幕阅读器模式下故意忽略纯
      DOM 的 input(insertText)，要求由
      helper textarea 捕获键盘 keypress /
      keydown 事件。
      • 第 2
      轮仅修改测试端输入注入方式，改用
      CDP Input.
      dispatchKeyEvent(type='char')
      模拟原生击键。生产代码在两轮之间一
      字未动，证实这纯属测试驱动适配真实
      的 Electron/xterm
      行为，绝非掩盖产品过滤吞字缺陷。
  • 红态与变异精准度：
      • 红态（electron-red）：在基线
      f8aa84625 上运行，鼠标移动在
      user_inputs 表中生成了 10
      条误记录，精准触发
      mouse_focus_do_not_create_records
      断言失败，证实了 T-145
      所声称的缺陷。
      • 变异 1（record-
      reports，恢复记录上报）：在
      mouse_focus_do_not_create_records
      处被捕获拒绝。
      • 变异 2（drop-reports，写入 PTY
      时过滤掉上报）：在接收端等待
      三次移动均到 PTY 处超时被捕获拒绝。
      • 回归对照：t133-t134
      全项通过；t091
      基线与候选产生完全一致的 IPC
      handler 报错，符合“不更差”标准。


  ### 5. 历史记录与页面展示

  •
  历史误记录在数据库中保持追加式不可变，
  没有运行任何清洗或删除脚本。
  • E2E
  测试在启动时主动插入了一条真实的历史鼠
  标上报记录（\x1b[<35;9;
  3M），并在测试流程末尾断言该记录在数据
  格 [RecordsPage.t
  中完整保留，打字后仅新增真正打字产生的
  一条记录。

  ### 6. 状态管理与正确性优化

  • 修复前，鼠标移动序列会触发
  panes.ts:1148 的 pane.userDraft = true
  与 pane.inputGeneration++，导致后台
  drain
  任务因判定用户正在编辑草稿而被无限期挂
  起（直到用户按回车或释放队列）。
  • 本次修复在识别到 protocolReport
  时不仅跳过了 record，也跳过了 userDraft
  = true 和 inputGeneration++
  ，彻底杜绝了鼠标滑动意外阻塞后台任务派
  发的隐蔽缺陷。
  ──────
  ## 二、发现项清单（Findings）

  ### [P3]
  交付工作区与候选提交证据目录分离

  • 位置：candidate/evidence/2026-10-23-
  batch23/T-145/RESULTS.md（Git 提交
  32d4f0f40 未包含该文件，保留在工作区
  /Users/luckye/Documents/Code/a2a-wt-
  t145/ 及主控 review 目录 evidence/ 中）
  • 严重度：P3（过程与文档管理）
  • 影响场景：候选提交 32d4f0f40 的 Git
  树中仅包含 workbench/
  内的生产与测试改动，RESULTS.md 及 RUN-
  OUTSIDE 脚本留存在 worker 的 worktree
  中，未通过 git add 入库。
  • 说明：执行主控已在沙箱外完整复跑并在
  evidence/run02-0InMi4/
  保留全部证据，生产代码无任何缺损。在最
  终合入 main
  时，由主控将对应的交付证据文件统一打包
  归档即可，不阻塞本次代码交付。
  ──────
  ## 三、审查结论

  T-145
  候选交付代码变更最小、边界严密、协议判
  定精准且考虑了修饰键边界情况，端到端测
  试真实覆盖了 Electron/PTY
  通道，红态与变异充分有效，回归测试表现
  一致。

  T-145 REVIEW PASS`
```
