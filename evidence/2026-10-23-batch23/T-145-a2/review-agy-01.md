# T-145-2 独立审查 01（agy）

- 审查员：agy 1.4.6，模型 gemini-3.8-flash-high，Herdr 可见窗格 wG:pG，交互 auto 模式（只用读文件工具），只读副本，候选 df88753ae。
- 启动 argv：

```
agy --model gemini-3.8-flash-high --mode auto --add-dir /Users/luckye/Documents/Code/a2a-review/T-145-a2-r1 -i "$(cat /Users/luckye/Documents/Code/a2a-review/T-145-a2-r1/prompt.txt)"
# pane wG:pG started 2026-10-23T13:12:04Z
```

- 审查后核对：候选副本 git status 0 行改动。结论 PASS，无发现项。

## 窗格中的报告原文

```text

○ Thought for 2m 30s (The input-enabled...)
● Explored 18 files (ctrl+o to expand)

▸ Thought for 23s, 3.4k tokens

   T-145-2（attempt 2）独立审查报告

  本审查基于
  /Users/luckye/Documents/Code/a2a-
  review/T-145-a2-r1/ 下的候选提交
  df88753ae、任务卡 card.md、改动差异
  full.diff
  以及合并失败与沙箱外运行证据完成。
  ──────
  ## 一、审查要点逐项核对结论

  ### 1. 根因是否属实

  • 核对结果：属实。
  • 详细证据：
      1. 在 renderer.tsx:482
      中，状态明确声明为 const
      [screenReader, setScreenReader] =
      useState(false);，并在 L198-L201
      中传入 new Terminal({ ...,
      screenReaderMode: screenReader, ...
      })，即屏幕阅读器支持默认关闭（属于
      T-143
      的终端性能改动，并在设置对话框
      L460-L462
      提供了显式开关；test_t139_t143_view
      s_perf_e2e.py:221-222
      中亦有专门断言
      check('screen_reader_default_off',
      ...screenReaderMode===false)）。
      2. 测试修改前在
      test_t145_mouse_reports_e2e.py:127
      原先等待的条件是：
      [...document.
      querySelectorAll(pane_selector + "
      .xterm-accessibility-tree
      [role=listitem]")].some(r=>r.
      textContent.
      includes("T145_MOUSE_READY"))。
      3. @xterm/xterm 的
      AccessibilityManager 仅在
      screenReaderMode: true
      时才会创建和更新 .xterm-
      accessibility-tree DOM
      树。读屏模式默认关闭后，该树始终为
      空，导致测试在 electron.
      until('鼠标模式输出已显示') 超时。
      4. 现场证据 t145-green.json:67-68
      显示两次失败均明确挂在
      test_t145_mouse_reports_e2e.
      py:125（即该等待行），而接收端夹具
      中 mouse-ready 标记与 pty.raw
      均包含完整的就绪序列，证明产品未吞
      掉输出，纯属测试观察目标失效。

  ──────
  ### 2. 改动边界、等待条件与验收强度核对

  •
  核对结果：符合边界要求，未放宽验收，无
  提前伪通过风险。
  • 详细证据：
      1. 改动范围：仅改动
      test_t145_mouse_reports_e2e.py:125-
      127 的两处 electron.until
      等待逻辑及文件头注释，未碰任何产品
      代码、门禁代码或 .project-
      map，完全符合 card.md:11
      的修改边界。
      2. 断言与期望值：所有 16
      项断言检查名（如
      receiver_native_identity_bound、mot
      ion_bytes_match_coordinates_exactly
      、cli_receives_only_complete_report
      s、mouse_focus_do_not_create_record
      s
      等）、坐标期望字节、设备回复序列、
      真实打字断言与默认等待超时完全未变
      。
      3. 第一处等待（终端可输入）：
          • 修改后：const p=document.
          querySelector(pane_selector +
          "[data-input-enabled=true]");
          return !!p?.getClientRects().
          length && !!p.
          querySelector("[data-
          restoring=false]") && !!p.
          querySelector(".xterm-helper-
          textarea");
          • 作用：适应 T-139
          引入的窗格保持机制，要求窗格可
          见（getClientRects().length >
          0）且恢复完毕（data-
          restoring="false"），防止误匹配
          到后台隐藏窗格，条件比此前更严
          格。
      4.
      第二处等待（鼠标模式输出已显示）：
          • 修改后：[...document.
          querySelectorAll(pane_selector +
          " .xterm-rows > div")].
          some(r=>r.getClientRects().
          length && getComputedStyle(r).
          visibility === "visible" && r.
          textContent.
          includes("T145_MOUSE_READY"))
          • 伪通过与放宽评估：
              • T145_MOUSE_READY
              仅在测试显式写入 (home /
              'enable-mouse').touch()
              之后由受管接收端 CLI
              触发输出，不存在旧行残留。
              •
              检查要求每行具有非零布局尺
              寸（r.getClientRects().
              length）且 visibility ===
              "visible"，防止隐藏行或未排
              版节点冒充。
              • 观察 .xterm-rows > div
              是读屏关闭时终端内容真实渲
              染到画面的标准路径，在此处
              同步后，后续仍有严格的坐标
              字节、PTY
              吞吐、数据库记录和事件校验
              ，未放宽任何验收。



  ──────
  ### 3. 键入方式与红态/变异有效性核对

  •
  核对结果：键入仍走真实原生路径，红态与
  变异准确落在所声称的缺陷上。
  • 详细证据：
      1. 真实键入路径：测试使用
      cdp('Input.dispatchKeyEvent',
      type='char', ...
      )。在读屏关闭时，CDP char 向聚焦的
      .xterm-helper-textarea 发送受信任的
      keypress、beforeinput 和 input
      事件（见 t145-green.json:84-109
      中记录的 keyboard_events），由
      xterm 原生键盘监听分发至
      onData，并经过主进程 panes.ts、PTY
      转发至真实受管进程，路径真实完整。
      2. 红态校验（--revision
      f8aa84625）：
          • 在 t145-red.json:13-19
          中，测试越过了窗格定位、等待与
          坐标匹配，精准失败于 L162
          check('mouse_focus_do_not_creat
          e_records')，复现了修前将鼠标序
          列记录为 user_inputs 的缺陷。
      3. 变异 1（record-reports）：
          • 在 t145-mutant-record.json:74
          中，精准失败于
          check('mouse_focus_do_not_creat
          e_records')，证实对误记录逻辑的
          拦截有效。
      4. 变异 2（drop-reports）：
          • 在
          t145-mutant-drop.json:69-70
          中，精准失败于 fixture.
          wait('三次移动均到
          PTY')，证实对 PTY
          转发被吞的拦截有效。
      5. 门禁与回归：
          •
          t139-t143-candidate.json（视图
          与性能）与
          t133-t134-regression.json（记录
          与指标）均绿态通过。


  ──────
  ## 二、发现项列表（Defect Log）

  经过对候选代码、diff
  及全部沙箱外执行记录的审查，未发现
  P0–P3 级别的缺陷或违规行为：

   … │ 文件与行号 │ 严重度 │ 发现描述与…
  ───┼────────────┼────────┼─────────────
   1 │ test_t145_ │ 无异常 │ 等待终端可
     │ mouse_repo │        │ 输入条件强
     │ rts_e2e.py │        │ 化了对可见
     │ :125       │        │ 性及恢复状
     │            │        │ 态的判断，
     │            │        │ 防止在多窗
     │            │        │ 格切换中命
     │            │        │ 中隐藏或脏
     │            │        │ DOM。
   2 │ test_t145_ │ 无异常 │ 替代原读屏
     │ mouse_repo │        │ DOM
     │ rts_e2e.py │        │ 的行渲染等
     │ :127       │        │ 待具备可见
     │            │        │ 性约束与文
     │            │        │ 本匹配，在
     │            │        │ 读屏开关两
     │            │        │ 种状态下均
     │            │        │ 真实反映渲
     │            │        │ 染状态。
  ──────
  T-145-2 REVIEW PASS
```
