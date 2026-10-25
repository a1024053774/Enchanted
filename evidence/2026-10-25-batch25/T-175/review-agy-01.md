  ## 一、审查核对项结论

  ### 1. 根因分析与改动层级

  • 根因判定正确：L02 表现为中文字间多空隙、表格右边框错位以及 p10k 分隔符（如 U+E0B0）显示为缺字方块。其根因为 xterm.js 默认采用 DOM
  渲染器，将整段文字组合在 HTML span 中依赖浏览器的字体度量进行连续排版；在缺少专用 CJK 等宽字体与 Nerd 字体时，macOS
  回退字体与西文字符的间距累积偏差导致表格纵向错位，且无法自绘私有区图标。同时，xterm 默认的 Unicode 6 宽度表与现代 CLI 工具计算宽字符规则不一致。
  • 改动处于最小根因层：
      1. 引入 @xterm/addon-webgl（0.19.0）替代 DOM 渲染，利用 GPU 逐格（cell grid）精准摆放字符，且其默认开启的 customGlyphs 特性直接负责制表符（Box
      Drawing）与 Powerline 三角符号（U+E0B0、U+E0B2 等）的矢量自绘，无需依赖打补丁的字体（见 renderer.tsx:59-61）。
      2. 引入 @xterm/addon-unicode11（0.9.0）并激活 Unicode 11 宽度表（allowProposedApi: true，见 renderer.tsx:49-54），消除 CLI
      与终端间的字符宽度认知差异。
      3. 提供终端字体设置输入项（renderer.tsx:108-123），默认回退链增加 "PingFang SC"，支持动态 refit 并在本地持久化。
  • 关于 WebGL 上下文丢失处理（webgl.onContextLoss(() => webgl.dispose())）的定性：
      • 这不属于违规的业务 fallback 或投机性重试，而是 @xterm/addon-webgl 官方规范强制要求的基础资源解绑生命周期（若不监听并
      dispose()，在底层图形上下文丢失时终端画布会永久冻结挂起，PTY 可读写但画面不更新）。
      • 该调用直接卸载已失效的 WebGL Addon，xterm 内部机制会自动保持终端基本响应（回退至其内置 DOM
      模式），未在业务层编写多余的猜测性重试机制或平行渲染分支。


  ### 2. 验收证据与真实入口

  • 验收项 1（真实 Electron 中文与表格对齐、p10k 提示符显示）：
      • 证据：test_t175_terminal_glyphs_e2e.py、运行日志 green-01.json 及截图对照 green-glyphs.png 与 red-glyphs.png。
      • 真实入口：真实 Electron 应用实例、真实 node-pty、本地 zsh 终端中通过 cat 打印夹具内容，使用 CDP 捕获真实渲染截图并进行像素级特征检验。
      • 期望值来源：夹具构建函数严格基于 Python 标准库 unicodedata.east_asian_width（W/F 算 2 格，独立于产品），断言各行最右侧像素 x
      坐标必须对齐在同一列（修前 7 行错位在 400~665px，修后 7 行整齐对齐在 642px）；Powerline U+E0B0 通过左缘实心（>0.7）与右缘尖角近空（<0.
      35）断言三角形几何轮廓，并非抄自产品输出。
  • 验收项 2（设置修改终端字体立即生效且重启保留）：
      • 证据：在真实 Electron 窗口通过 UI 点击设置，将字体改为比例字体 Helvetica，验证终端列数因字符宽度变化而立即重新计算缩小（159 列 -> 101
      列）；恢复为自定义 monospace 列表后销毁 Electron 并重启全新窗口，读取设置输入框验证持久化值一致。


  ### 3. 红态与坏实现变异

  • 红态落实：在修前版本（8f36d6495）上运行测试 red-main-02.json，准确命中两处缺陷断言失败：
      1. table_right_border_aligned：表格各行右边缘错位（right: [653, 400, 653, 665, 659, 665, 653]）；
      2. powerline_triangle_drawn：左右边缘采样均为 0.69，证实为矩形缺字方块（tofu 边框）。
  • 坏实现变异：本项依赖修前真实提交（parent revision 8f36d6495）作为真实坏实现验证红态，满足规范要求。

  ### 4. 修改边界与界面文案

  • 修改边界：除 package 依赖、渲染器与设置 UI 组件、样式表及对应的 e2e 测试与回归测试适配外，没有触碰任何无关业务代码。
  •
  界面文案：设置项标题为“终端字体”，字段标签“字体列表”，操作按钮“恢复默认”，说明文案“用逗号分隔，前面的字体缺字时用后面的。立即应用于本窗口的所有终端，重启
  后保留。”，文风平实客观，无任何营销腔。

  ### 5. 正确性与回归风险

  • DOM 依赖测试影响：
      • WebGL 渲染模式将字符直接绘制在 HTML5 Canvas 上，不再往 DOM 的 .xterm-rows 下插入实际字符内容。
      • 审查确认已对原有依赖 .xterm-rows 的测试用例 test_t145_mouse_reports_e2e.py:338-342 做了适应性调整（改为等待 PTY trace 记录并确认 .xterm-screen
      可见），且回归测试已通过（regression-t145-01.json）。
  • 生命周期安全：组件卸载时 term.dispose() 会级联销毁加载的插件并清理 WebGL 上下文，不会引发显存泄露。
  ──────
  ## 二、发现项列表（Findings）

  ### 发现 1：WebGL Addon 导致 DOM 终端文字消失，需警惕后续测试回归风险

  • 文件与行号：test_t145_mouse_reports_e2e.py:338-342、test_t167_codex_start_e2e.py:169-170
  • 严重度：P2
  • 失败场景：
  启用 WebGL 渲染后，终端内容不再呈现于 .xterm-rows > div。虽然本次改动修正了 test_t145 并核对了 test_t167（其 screen_tail
  字段仅作无断言观察，现实际为空列表 []），但团队其他成员或未来新增测试若按常规经验使用 document.querySelectorAll('.xterm-rows > div')
  获取终端字符进行断言，将全部遭遇超时或断言失败。
  • 建议：在项目测试指引中明确：终端文字输出断言应当优先通过 PTY trace、原生事件日志或截图像素进行，禁止依赖 DOM .xterm-rows。

  ### 发现 2：WebGL 上下文丢失时静默降级为 DOM 渲染器无视觉反馈

  • 文件与行号：renderer.tsx:61
  • 严重度：P3
  • 失败场景：
  Chromium 对每个渲染进程通常有 16 个活动 WebGL 上下文的上限，或在系统休眠唤醒、显卡驱动重置时触发 webglcontextlost。当前代码调用 webgl.dispose() 将 Addon
  卸载以防终端完全卡死，此时 xterm 会自动退回内置 DOM 渲染模式。在该模式下，L02 所述的 CJK 对齐漂移和 p10k
  字符方块现象将在该窗格中再次复现，且用户界面上没有任何指示。
  • 说明：此行为符合 xterm 官方建议，避免了更严重的 UI 假死，且多终端并发超过 16
  个为极端边缘场景，当前实现维持最小改动是合理的，无需引入复杂的重建重试逻辑。

  ### 发现 3：单行纯中文测试断言容差过大，未在修前展现红态

  • 文件与行号：test_t175_terminal_glyphs_e2e.py:636-638
  • 严重度：P3
  • 失败场景：
  在 red-main-02.json 中，单行中文测试项 cjk_two_cells_each（检查“中文字符之间不该多出空隙”行末位置）在修前版本上即为 PASS。这是因为该检查设置了高达 2
  个完整单元格（约 14px）的容差区间，12 个汉字的累积漂移未超出容差范围。真正使修前版本呈现红态的是 table_right_border_aligned（多行混排边界漂移）与
  powerline_triangle_drawn（私有区字符缺失）。
  ──────
  ## 三、审查结论

  T-175 根因定位准确，解决方案遵循“不自造、最小根因层”原则；WebGL 上下文丢失处理为官方规范的标准解绑逻辑而非违规 fallback；验收测试拥有来自真实 Electron
  与标准 Unicode 规约的真实证据；红态在修前版本落实；文案与修改边界合规。

  T-175 REVIEW PASS

