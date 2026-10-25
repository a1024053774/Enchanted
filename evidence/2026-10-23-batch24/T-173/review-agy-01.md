# T-173 agy 独立审查报告（gemini-3.8-flash-high，Herdr wG:p2P，只读副本 3b27d494f）

独立审查报告

  审查对象：T-173 产品页更新交互动画，修整体页面割裂、不和谐
  候选提交：3b27d494f（相对起点 ebca24616 / 基线 54dd554ce）
  关联文件：T-173 任务卡、user-decision.md、RESULTS.md
  审查员身份：只读独立审查员（未运行任何 shell 命令，未写入任何文件）

  ## 重点审查项核对

  ### (1) RESULTS.md 修前问题清单与截图支撑

  RESULTS.md:9-19 列出了 9 条具体的视觉割裂与演示落后问题，每条均给出具体成因与处置结论：

  1. 全页左边线错位（116px、200px、20px、116px）：由 before-hero.jpg 与 before-step4.jpg 确凿证实；修后 after-hero.jpg 与 after-step4-grid.jpg
  证实统一对齐在 64px。
  2. 页面与演示窗口两套色系割裂（暖灰底 #f6f6f4、旧强调色 #0169cc 对比应用偏冷底色与 #0a66d8）：修后统一从 style.css:5-30 取
  token，按钮改墨色，after-hero.jpg 支撑结论。
  3. 第二屏留白不对称：修后窗口居中，留白一致。
  4. 通知浮层长期遮挡窗格与泳道：before-step4.jpg 与 before-flow-dark.jpg 支撑了修前盖住界面的现象；修后仅在第 1、3 步提示，after-step4-grid.jpg 与
  after-flow-pan.jpg 证实无遮挡。
  5. 通栏细线切割感：已去掉分割线，靠空间留白划分。
  6. 首屏标题字重与字距：已微调为 -0.035em、600。
  7. 演示缺少 0.1.3 三层视图与普通终端：修后新增第 4 步任务格（T-12/T-11/T-14/T-09）至 T-11 分屏（worker + 独立审查 + 普通终端 + 门禁条），有
  after-step4-grid.jpg 与 after-step4-dark.jpg 支撑。
  8. 手机端演示尺寸为缩略图：不改动缩放策略，保留平实文案“完整操作请用电脑打开”，列为已知限制。
  9. 流程页泳道右侧截断：真实应用泳道总宽 1150px 超过窗口宽度需横向滚动，演示采用平移动画先向右展示“独立审查”与“集成”再归位，after-flow-pan.jpg
  支撑该展示。

  ### (2) 演示与 0.1.3 真实界面及规格一致性

  1. 项目任务分屏与普通终端：
      • 对照 renderer.tsx:979-986，真实应用在选中项目且无任务选中时显示 .project-task-grid 与 .project-task-tile，任务格包含状态、标题、ID 与 agent
      计数。演示在 demo.js:422-426 还原了完全一致的 DOM 结构和类名。
      • 对照 README.md:100-106, 273-277，任务内分屏允许在 worker 旁开普通终端；普通终端不记为人工介入，页脚标为“普通终端 · zsh”。演示在
      demo.js:189-190, 363-372 忠实还原了 layouts['inkwell/T-11'] 下包含 shellPane，且页脚为 普通终端 · zsh。
  2. 流程页泳道宽度：
      • 对照 flow.css:6, 12，.flow-lane 最小宽度为 1150px（5 列 × 230px）。演示在 demo.css:216, 220 保持完全一致的 1150px，并在 demo.js:937-939
      用平移动画引导用户看到右侧的“独立审查”与“集成”。
  3. 任务格“N 个 agent”计数差异核实：
      • 真实应用 renderer.tsx:984 使用 {agents.filter(agent => agent.task === item.task_id).length} 个 agent。在真实应用后端 sidebar.ts:184-186，主控终端的
      task 字段恒为 null（主控归属项目级而非单任务），因此该统计自然仅计算挂在该任务上的 worker、reviewer 与 monitor。
      • 在演示虚拟数据 demo.js:69-70 中，构思主控与执行主控因场景说明需要被预设了 task: 'T-12'。为避免任务格将项目主控误计入 T-12 的 agent
      计数，demo.js:425 补充了 agent.role !== 'controller' 过滤，使 T-12 显示“2 个 agent”（即 worker 与 monitor），呈现效果与 0.1.3 真实应用完全一致。


  ### (3) 色彩与对比度计算（WCAG AA/AAA 核算）

  针对 site.css:3-20 中引入的 workbench/app/style.css token 计算相对亮度 L 与对比度：

  1. 浅色模式：
      • 页面底色 --bg: #f2f3f6（L ≈ 0.8987）
      • 墨色 --ink: #1d1d1f（L ≈ 0.0136）
          • --ink 在 --bg 上的对比度为 14.92 : 1（远超 WCAG AAA 7 : 1）。
          • 主按钮 .button.primary（墨色底、--bg 浅色字）对比度同样为 14.92 : 1。
      • 次要文字 --muted: #6b6b72（L ≈ 0.1460）
          • --muted 在 --bg 上的对比度为 4.84 : 1，满足 WCAG AA 正常正文要求（≥ 4.5 : 1）。

  2. 深色模式：
      • 页面底色 --bg: #141417（L ≈ 0.0077）
      • 墨色反白 --ink: #ececf0（L ≈ 0.8379）
          • --ink 在 --bg 上的对比度为 15.39 : 1（远超 WCAG AAA 7 : 1）。
          • 主按钮（#ececf0 底、#141417 字）对比度为 15.39 : 1。
      • 次要文字 --muted: #a1a1aa（L ≈ 0.3566）
          • --muted 在 --bg 上的对比度为 7.05 : 1，达到 WCAG AAA 级别（≥ 7 : 1）。



  文字与主按钮对比度在明暗双主题下均达到或超过标准。

  ### (4) 动效工程质量

  1. 动效属性限制：
      • site.css:75, 86 与 demo.css:351-353 中的 @keyframes cue, @keyframes step-in, @keyframes wb-fade, @keyframes wb-rise, @keyframes wb-toast
      严格限定仅使用 opacity 与 transform。
      • 引导高亮 @keyframes wb-spot 仅对 outline-color 进行透明度过渡，不触发页面重排（reflow）。
  2. 可被打断性：
      • demo.js:954 在 go(name) 进入时，首句执行 timers.forEach(clearTimeout); timers = [];，在任何快速切步或用户打断时立即清除所有挂起动画定时器。
  3. prefers-reduced-motion 静态替代：
      • demo.js:949 enter() 在 calm.matches 时直接返回，不添加动画类名。
      • demo.js:968 在减弱动效下，直接把第 4 步目标态 then（T-11 分屏）合并进当前视图状态，跳过中间过渡；且不调度 scene.play（平移动画）。
      • CSS 媒体查询在 no-preference 下才挂载关键帧动画。
  4. 换步定时器与重置清理：
      • reset()（demo.js:178）与 go() 均全量清理 timers。
  5. wb-enter 动画不重播：
      • demo.js:952 在入场动画播完后（900ms）自动移除 .wb-enter。演示窗口内部的点按交互（如切换标签、点击申请）仅触发 render()，不调用
      enter()，因此不会触发全局淡入重播。


  ### (5) 测试套件检验与变异拒绝

  1. check.mjs 与 T-172 对照：
      • 对照 T-172 check.mjs 与 T-173 check.mjs，原有 44 项检查完整保留且断言阈值未作任何放宽。
      • 原第 4 步右键菜单测试调整为 await page.waitForSelector('.wb .pane .terminal-scroll')，适配第 4 步先出现任务格再展示窗格的预期时序。
      • 新增 7 项 T-173 专项断言（总检查项由 44 项增至 51 项）。
  2. 红态运行结果验证：
      • 查阅 report.json，线上修前版本 54dd554ce 运行结果为 INCOMPLETE 45/51。原有 44 项全过，精准在 T-173 的 6 项新检查上变红（左边线 [116, 200, 20, 116]
      错位、通知遮挡流程页、未展示任务格、未展示普通终端、减弱动效下未直接呈现终态）。
  3. 变异体拒绝验证：
      • mutant-calm-01：查阅 report.json，删除减弱动效静态替代后，精准被 t173 reduced motion shows the settled views state at once 拦截拒绝。
      • mutant-notice-01：查阅 report.json，删除切步清理通知后，精准被两项 notification does not cover the flow step 拦截拒绝。


  ### (6) 响应式、文案与 lcu 状态

  1. 390px 视口：
      • check.mjs:123-126 自动化测试 w390 no horizontal page scroll 结果溢出为 0，且 after-phone.jpg 证实无横向溢出。
  2. 文案平实：
      • index.html:34-45, 88-106 均如实阐述机制原理（原生
      CLI、门禁验证、写审分开），在已知限制中诚实声明“未做过性能与成本承诺”、“启动失败可回收仅在模拟上验证过”，不含任何营销夸大语句。
  3. lcu 复看状态：
      • 执行主控在 RESULTS.md:40 如实记录由于 Chrome
      用户个人资料授权及系统权限边界，未擅自代批越界操作，已按规则停止并记录待补。按本次审查指令，这不作为本票缺陷。


  ## 审查规程五项核对

  1. 根因与改动层级：
      • 割裂与动画缺失的根因找准（边距计算容器不同、样式表未同步应用 token、演示仍停留在 0.1.2 视图模型）。
      • 改动限定在最小根因层（仅文档与演示页面），无吞异常、无 fallback、无重试、无兼容分支或平行 API。
  2. 验收证据与期望值：
      • 每条验收标准均有独立可复现的 Playwright 端到端检查与截图佐证。
      • 期望值（左边线最大差值 ≤ 2px、减弱动效下无运行中动画、通知数为 0、窗格角色严格匹配）来源于规格与用户要求，而非抄录产品自身输出。
  3. 红态与变异：
      • 红态在真实修前代码上精准落在缺陷断言上；两个变异体均代表真实坏实现并被成功拒绝。
  4. 修改边界与文案：
      • full.diff 为空，完全未改动产品代码；文案克制平实。
  5. 其他正确性与回归风险：
      • 页面代码遵循了标准 DOM 与 CSS 规范，无样式污染或全局作用域泄露风险。


  ## 审查发现（Findings）

  ### [P3] 任务格 agent 计数过滤逻辑与应用端数据结构差异说明

  • 文件与行号：demo.js:425 对比 renderer.tsx:984
  • 场景描述：真实应用的 renderer.tsx 为 {agents.filter(agent => agent.task === item.task_id).length} 个 agent，依靠后端 sidebar.ts 主控角色 task: null
  的特性天然排除主控；而在演示虚拟数据中，主控被指定了 task: 'T-12'，因此 demo.js 在行 425 增加了 agent.role !== 'controller' 显式排除。
  • 影响评估：最终界面展示效果与 0.1.3 完全一致（正确展示该任务下的 2 个 worker/monitor），无业务或演示偏差，属于为了配合 mock
  数据结构保持展现一致的有意设计，建议保留当前实现并在代码注释中记明即可。

  ### [P3] wb-spot 动画属性补充说明

  • 文件与行号：candidate/docs/assets/demo.css:349, 354
  • 场景描述：导览聚焦引导动画 @keyframes wb-spot 改变了 outline-color。虽然主体入场动画均严格限制在 opacity 和 transform，且 outline-color 不引发 layout
  重排，在 prefers-reduced-motion: reduce 下该动画亦被禁用，但属于微小属性特例，不影响性能与规范一致性。

  T-173 REVIEW PASS
