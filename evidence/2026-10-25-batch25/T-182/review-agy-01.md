  ## 1. 16 项移植检查与 35 项退役清单核对

  ### 1.1 16 项移植检查忠实性分析

  对照 t173-check.mjs 与候选测试 check.mjs:33-109 Part 1：

  1. approve puts executor under ideation (level 1)：原检查在旧第二屏点击审批后断言 tree.join() === '1'；移植后定向到 #show-approve 分展示并在 #wb-approve
  窗口内执行审批，断言条件完全相同（tree.join() === '1'），且额外增加了鼠标按下时页面不抖动的位移检查。未放宽。
  2. context menu opens at the pointer under scaling：原检查在缩放窗口点击右键检验菜单坐标（误差 < 6px）；移植后在首屏 #wb-views 的第 3
  步窗格执行，右键菜单坐标容差保持 < 6px。未放宽。
  3. records page has task and session filters (RecordsPage.tsx)：原检查断言 select 元素数为 2；移植后在 #wb-records 窗口内断言数量为 2。完全一致。
  4. wheel over overflowing metrics page scrolls it, not the step：原检查在指标页内滚轮滚动时断言步骤停留在原步且 scrollTop > 0；移植后在 records 展示的第
  2 步（指标页）执行，断言 recordsStep === '2' 且 scrollTop > 0。语义忠实。
  5. metrics model use has summary and per-session tables (MetricsPage.tsx)：原断言 heads.length === 2 && heads[1].
  includes('角色')；移植后断言完全一致。未放宽。
  6. metrics page has a date range (MetricsPage.tsx)：原断言 input[type=date] 数量为 2；移植后完全一致。未放宽。
  7. Tab stays inside the settings dialog：原检查在设置弹窗连续按 Tab 40 次并断言焦点不跑出弹窗；移植后在 #wb-reflect 的第 2 步打开设置弹窗执行相同 40 次
  Tab，断言焦点在弹窗内。未放宽。
  8. w390 no horizontal page scroll：原检查仅在页面顶部和导览偏移处核对横向溢出；移植后通过 for (let y = 0; y < H; y += h)
  遍历页面从顶至底的全高度，断言整页最大溢出 worst <= 0。比原断言更严格。
  9. w820 no horizontal page scroll：同样在 820px 平板宽度下遍历全页高度断言 worst <= 0。比原断言更严格。
  10. t173 views: project step shows the task grid（原 views step opens on the project task grid）：原导览第 4
  步初始自动展示任务格；新结构将分步拆为步进模式，第 2 步断言 grid.grid === 'T-12,T-11,T-14,T-09' && grid.panes === ''。语义忠实。
  11. t173 views: task step shows T-11 worker, review and an ordinary terminal with the gate：原导览在 1.6 秒后自动进入 T-11 窗格分屏；新结构在第 3
  步断言窗格角色与门禁状态为 已交付。语义忠实。
  12. t173 no-preference notification does not cover the flow demo：原断言在流程步 notification 数量为 0；移植后断言 #wb-flow 内无通知遮挡。完全一致。
  13. t173 reduced motion shows the settled task view at once：原断言减弱动效下直接显示终态窗格；移植后在 views 第 3 步断言立即显示终态。未放宽。
  14. t173 reduced motion leaves nothing animating：断言运行中的动画列表（排除 spin）长度为 0；移植后还补充检查了 transitionProperty。未放宽。
  15. t173 reduce notification does not cover the flow demo：在减弱动效下断言 flow 展示无通知遮挡。完全一致。
  16. t173 header, hero, a left-side feature heading and download share one left edge：原导览计算 .wordmark、.intro h1、.tour-caption、#download h2
  的左边距极差 <= 2px；旧 .tour-caption 移除后，换用同处左栏的偶数展示标题 #show-flow .station-head h2，断言四者左对齐极差仍 <= 2px。布局基准忠实。

  ### 1.2 35 项退役清单完整性

  在 ticket-rev3.md:35 与 user-decision.md 中，用户明确授权选择“A 退役这 35 项”。
  经核对 t173-report.json 原报告全部 51 项检查，排除上述保留的 16 项后，剩余退役的 35 项在 RESULTS.md:54-88 中被逐字、逐项完整列出，包含：

  • 浅色滚轮步进与连滚、穿底与回弹：13 项（light first wheel enters tour at step 1 至 light wheel up from download returns to last step）
  • 深色滚轮步进与连滚、穿底与回弹：13 项（dark first wheel enters tour at step 1 至 dark wheel up from download returns to last step）
  • 边界漂移与按键：6 项（edge: at step 5 before drift、edge: 5px drift...、edge: ArrowDown...、edge: ArrowUp...、edge: arrow keys with focus...、edge:
  wheel over...）
  • 触屏手势切步：3 项（touch: one swipe up...、touch: swipe up...、touch: swipe down...）

  退役清单无遗漏、无多占，且注明了退役原因为随 rev 2 拆分为分功能展示不再劫持页面滚轮。
  ──────
  ## 2. 新增检查与测试独立性审查

  ### 2.1 期望值来源核查

  check.mjs:112-190 Part 2 涵盖的全部新检查期望均直接来源于用户原话与 Ticket 验收条款，未发现“照着实现输出写断言”的反模式：

  • 首屏同屏展示（t182 ${w} ${scheme}: demo, title and download are on the first screen）：要求 wbTop < vh - 80、h1 < vh、download <
  vh，来自用户原话“还是不把交互放第二屏幕了,就放在第一屏幕,不然太空”。
  • 背景层次（background is layered, not one flat color）：断言径向渐变层数 >= 2，来自用户原话“现在背景纯色太单调”。
  • 紫色抽象连线（connecting line is purple）：断言 SVG 轨道描边 RGB 中蓝、红主导且显著高于绿色（rgb[2] > rgb[0] && rgb[0] > rgb[1] && rgb[2] - rgb[1] >
  60），来自用户原话“加一些抽象线条……用紫色的最好”。
  • 切换引导与起步提示（t182 guide: first visit shows step 1 of 3, previous disabled, a start
  hint）：断言初始步数、上一步禁用、显示“从这里开始”提示，来自用户原话“切换要有引导”。
  • 引导按键与窗口隔离（t182 guide: arrow keys inside the demo window stay in the window）：断言焦点在窗口内按方向键不会触发外部步骤切换，来自 ticket
  键盘操作及焦点隔离要求。
  • 6 个分功能独立展示（t182 six separate feature demos, each with its own window 及 demos are independent...）：断言存在 6
  个展示且相互操作无交叉污染，来自用户原话“不要把所有交互都加在一个展示里,应该分功能来展示”。
  • 连线半屏与减弱动效（t182 thread ...）：断言线头高度不超过视口 50%（olavlj 文章规范），且 prefers-reduced-motion: reduce 下静态整线画全。

  ### 2.2 红态与变异有效性

  1. 修前 main 运行（red-main-01）：
      • 结果：通过 2/23（仅 390px/820px 无横滚通过）。
      • 失败位置：首屏未找到演示窗口、背景单一无渐变、缺少紫色连线 SVG、未拆分分功能展示、缺少步骤引导。红态精准落在所有本次改造的验收项上。
  2. 变异 1（mutant-hint-shift-01）：
      • 变异实现：收起首次提示时改变占位尺寸，且在任何展示内按下均触发收起。
      • 拒绝证据：精准命中 t182 a press in a feature demo does not move the page under the pointer（按下瞬间页面发生 33.39px 位移）以及 approve puts
      executor under ideation (level 1)（因位移导致审批按钮脱落点击失败）。
  3. 变异 2（mutant-calm-ignored-01）：
      • 变异实现：在减弱动效下仍依赖滚动画线。
      • 拒绝证据：精准命中 t182 reduced motion: the line is drawn whole and every station lit without scrolling（drawn: 330 未画全，仅首站亮）。

  ──────
  ## 3. 视觉、交互与多设备表现核查

  1. 首屏布局：
      • 桌面端（1440×900）采用双列网格（.intro-grid，左栏标题/说明/原则/按钮，右栏为第一个展示 show-hero），首屏下边缘前完整展示演示窗口（wbTop: 140，vh:
      900）。
      • 窄屏（390×844）垂直流式排版，标题、下载按钮与首屏演示窗口均处于第一屏内（wbTop: 476.28，download: 326.89，vh: 844）。
  2. 底色与背景层次：
      • body 采用双径向渐变（淡紫光晕与淡蓝光晕叠加，site.css:2160-2163）。
      • 首屏叠加渐变衰减的微点阵（radial-gradient(...) 22px 22px 加 linear-gradient 遮罩，site.css:2165-2167），层次丰富且不干扰文字阅读。
      • 深色模式采用一致的 OKLCH token 派生，无反差失衡。
  3. 连线图形与设计调性：
      • 图形完全避开花与藤蔓，提取自 Enchanted 标志内部的环形轨道与四角星（showcase.js:2-3）。
      • 轨道主色使用紫色 --spell: oklch(52% 0.2 293)（深色 --spell: oklch(74% 0.15 293)），沿途小珠（.thread-bead）与四角星（.station-
      star）随滚动平滑点亮。
  4. 响应式与无横滚：
      • 390px 与 820px 下全页遍历滚动检测，横向溢出值恒为 0，无横向摇摆。

  ──────
  ## 4. 代码实现质量与设计规范核查

  ### 4.1 showcase.js / demo.js 正确性

  1. 多实例隔离：
      • demo.js:16-985 将原有单例重构为工厂模式 mount(root)。每个分功能展示持有独立的 data、ui、panes、layouts 和 timers。
      • DOM 事件监听器绑定在各演示容器 root 上，DOM id 均带有 root.id 隔离前缀（如 ${root.id}-settings-title），彻底避免全局 ID 冲突。
  2. 懒加载与布局稳定性：
      • 首屏展示立即 mount，其余 5 个展示通过 IntersectionObserver 配合 rootMargin: '600px 0px' 预先异步挂载（showcase.js:88-94）。
      • 挂载前通过 CSS .show.is-live .show-frame { aspect-ratio: 1040 / 760; } 提前占位，挂载后通过动态 ResizeObserver
      计算整体缩放比例并精确写入高度，杜绝加载跳动。
  3. 键盘事件隔离：
      • 引导区的键盘监听器仅挂载在 .show-guide 说明区域（showcase.js:74-79）。
      • 演示窗口内的方向键与按键直接被内部终端/菜单捕获处理，不会向外冒泡改变导览步数。
  4. localStorage 读写健壮性：
      • enchanted-showcase-seen 的读取（showcase.js:12）与写入（showcase.js:19）均由 try...catch 包裹，在第三方 Cookie
      禁用或隐私模式抛错时安全降级，不阻断脚本。


  ### 4.2 good-css.com 规范遵循

  对照 RESULTS.md:13-21 声称做法与 site.css：

  • 现代色彩模型：主色采用 oklch()，派生微光与阴影使用 color-mix(in oklch, ...)，未硬编码碎片化色彩。
  • 指针与悬停保护：悬停动效完全置于 @media (hover: hover) and (pointer: fine) 下（site.css:2327-2344），触屏设备不会卡在 hover 状态。
  • 动效安全与精细化：位移与缩放过渡统一包裹在 @media (prefers-reduced-motion: no-preference) 中；动效指明具体属性（拒绝 transition: all），避免 ease-
  in，使用 --ease-out: cubic-bezier(0.23, 1, 0.32, 1)。
  • 逻辑属性：新编写的间距和尺寸全面使用 min-block-size、padding-inline、inset-inline-start、margin-block-start 等现代逻辑属性。
  • 标题自适应：.intro h1 使用 clamp(3rem, 2rem + 2.6vw, 4.5rem)，上下限跨度 1.5 倍，远低于 good-css 建议的 2.5 倍上限。
  • 可访问性焦点：无破坏性的 outline: none。

  ### 4.3 uiarc.dev 样式借鉴与代码原创性

  site.css:2143-2156 的 .button 为纯手写 CSS 原生实现，仅汲取了 uiarc.dev 的视觉规范（胶囊圆角 border-radius:
  999px、单一墨色主按钮、白底次按钮加淡阴影、按压时 :active 缩放至 0.97）。无 Tailwind 预设类、无外部组件依赖或代码复制痕迹，符合许可与原创要求。
  ──────
  ## 5. 修改边界、文案风格与架构整洁度

  1. 最小根因与修改边界：
      • 彻底删除旧版单例滚轮导览脚本 tour.js，以 showcase.js 替代，无向下兼容兼容层、无双写或平行 shim。
      • full.diff 仅包含 docs/ 下的 HTML、CSS、JS 文件，未越界触碰任何产品代码（workbench/、acceptance/ 等）。
  2. 文案风格（前端克制无营销腔）：
      • 文案保持客观克制的工程师语调（如“活干没干完，由门禁说了算，不由模型自己说”、“演示数据全部虚构：不连后台，不调用模型”）。
      •
      保留了开发中的初版免责声明：“没有做过可靠性、吞吐或成本的对照实验，本页不做这类承诺”、“应用内主控写的完成条件仍可能偏弱或写错；门禁会如实拒收”。无夸
      大其词或营销腔。

  ──────
  ## 6. 审查发现清单（Findings）

  经对代码、样式、运行报告及截图证据的全面排查，本次变更质量极高，未发现 P0–P2 缺陷。仅记录以下 3 项 P3 级设计与代码细节观察（无需打回修改）：

  ### Finding 1: 弱网环境动态高度计算保护

  • 文件与行号：showcase.js:35-40
  • 严重度：P3
  • 场景描述：fit() 函数中通过 wb.offsetHeight * scale 计算外框高度。当 mount() 挂载前已通过 CSS .show.is-live .show-frame { aspect-ratio: 1040 / 760; }
  进行几何约束，实际运行中极其平稳。但在极端极端极端情况下若窗口内部资源初次渲染发生异常导致 wb.offsetHeight 为 0 时，依赖 CSS aspect-ratio
  保障即可。代码中保留了对 demo 的判断保护，行为可信。

  ### Finding 2: 单步展示导航控件的省略设计

  • 文件与行号：docs/index.html:2603, 2615
  • 严重度：P3
  • 场景描述：Show 3（flow）与 Show 4（issues）各自仅有 1 步，页面中省去了 data-show-nav（上一步/下一步按钮组）。showcase.js:26-32
  采用了完善的可选链与空值判断处理，未引发任何运行时异常。符合“每个展示只讲一件事”的极简交互设计。

  ### Finding 3: 连线端点与最后展示下边界的自然衔接

  • 文件与行号：showcase.js:124-125
  • 严重度：P3
  • 场景描述：连线最底端延伸至最后一个展示容器底部 d += L${last.x} ${last.end}。在页面向下滚动进入 #download
  区块时，连线自然隐没在空白过渡区，未出现压字或穿插混乱，视觉落幅干净。
  ──────
  ## 7. RESULTS.md 状态核实与后续建议

  • RESULTS.md:3 将候选状态如实标记为：INCOMPLETE（待 agy 审查、push、线上 Pages 与 lcu 复看），如实反映了候选推送前的状态，无虚假提前提标。
  • 本地 43 项检查（16 项移植 + 27 项新增）在 local-05、local-06、local-07 连续三次全部 PASS，红态与两项变异检验具备坚实证据支撑。
  • 本独立审查（agy 独立审查）结论为通过。执行主控可推进下一阶段动作：执行无凭据泄露推送（推前扫凭据）、验证 GitHub Pages 200 返回，并在隔离环境使用 lcu
  进行 Chrome 线上真机/浏览器复看，之后将 RESULTS.md 闭环上调为 PASS。
  ──────
  T-182 REVIEW PASS

