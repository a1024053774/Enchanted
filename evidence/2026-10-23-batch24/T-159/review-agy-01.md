# T-159 独立审查 01（agy）

- 候选：16fca3526；起点 e83a8a04e
- argv：`agy --model gemini-3.8-flash-high --mode auto --add-dir /Users/luckye/Documents/Code/a2a-review/T-159-r1 -i "$(cat /Users/luckye/Documents/Code/a2a-review/T-159-r1/prompt.txt)"`
- # pane wG:p1J started 2026-10-24T00:45:01Z candidate 16fca3526707fec7712b672ba0c4e351d6d5ae02
- 结论：INCOMPLETE（P1：验收第 1 条写“并排”，候选走“禁用并说明”分支）。执行主控转构思主控 needs-decision 20261024T005359Z；用户 2026-10-24 选并排普通终端（answer 20261024T024128Z-001），本候选方向作废，需重做。
- 审查中另提的“菜单按 role==='shell' 判断导致已批准主控禁分屏”经执行主控核实不成立（已批准主控快照 role 仍为 shell，outside-03 实测可分屏），已在 20261024T022208Z 更正。

## 窗格原文

```text
  审查结论与总体判
  定

  •
  审查结论：INCOMPL
  ETE（因验收合同语
  义出入阻断，需交
  构思主控裁定）
  •
  代码实现与工程质
  量：通过（PASS）
  。根因分析准确，
  改动集中在最小根
  因层（main.ts:593
  与
  renderer.tsx:403-
  408）；未吞异常、
  无
  fallback、无重试
  、无平行
  API；无真实模型调
  用；修前真实
  Electron
  红态在缺陷断言上
  稳定复现；两个变
  异（旧实现变异与
  缺少入口拦截变异
  ）均被预期业务断
  言杀死；T-139
  的三项已有回归均
  通过；未越出任务
  卡修改边界。
  •
  阻断放行的关键原
  因：候选实现选择
  了“不能同屏、操作
  前说明”分支，彻底
  禁用了任务视图内
  的向右/向下分屏；
  然而
  T-159-split-keeps
  -original-pane.md
  :25 的 ##
  Acceptance 第 1
  条明确写着：“任务
  视图点向右分屏后
  ，原 worker
  与新窗格并排，窗
  格数、类型、目录
  与菜单所述一致”。
  候选并未做到并排
  ，画面保持单
  worker
  窗格。此项属于验
  收合同与实现分支
  的直接字面语义冲
  突。根据项目规则
  与授权边界，只读
  审查员无权擅自豁
  免或重写 ticket
  的验收条款，必须
  作为验收语义问题
  提交构思主控裁定
  并修订
  ticket，不能自己
  放行。
  ──────
  ##
  核心专项判断：T-
  139 依据与 Ticket
  验收出入分析

  ### 1.
  这一选择是否真有
  T-139 依据？

  答：有充分、真实
  且严格的代码与规
  格依据。

  1. T-139
  视图模型的核心铁
  律是普通终端只在
  项目层，不进任务
  视图：
      •
      README.md:266
      -267
      明确写明：“左
      侧点项目进入
      任务总览；点
      任务显示其
      Agent
      会话，点单个
      agent
      或项目普通终
      端只显示它自
      己。普通终端
      不混入任务视
      图；‘独立终端
      ’显示不属于项
      目的终端。”
      • 在
      test_t139_sel
      ection.mjs:1-
      4
      中，文件头第
      一条列出的失
      败模式就是：F
      ailure modes:
      task includes
      a project
      shell; ...
      ，其核心断言
      task_only_its
      _agents
      严防项目终端
      混进任务视图
      。
      •
      后台门禁入口
      cli.ts:21 的
      shell_start
      命令仅接受 --
      cwd 与可选的
      --project，根
      本不接受 --
      task
      参数；后台数
      据库中 shell
      记录的 task
      字段永远为
      null。
  2.
  工作台分屏机制的
  固有属性：
      •
      工作台中的“向
      右分屏 /
      向下分屏”（cr
      eateTerminal
      ）创建的是普
      通 shell
      终端（shell_s
      tart），并非
      派发新的
      Agent
      会话（Agent
      必须经由
      claim/dispatc
      h/role
      门禁链路启动
      ）。
      •
      如果在任务视
      图里允许分屏
      创建新终端，
      要么必须把项
      目级普通终端
      塞进任务视图
      （破坏 T-139
      的隔离模型）
      ，要么像修前
      一样把视图隐
      式切到项目层
      （导致原
      worker
      窗格被刷掉、
      上下文丢失的
      F03 缺陷）。
  3. 结论：在现有
  T-139
  模型下，“任务
  Agent
  与普通终端不能同
  屏”是客观成立的技
  术事实，worker
  识别该约束是有据
  可依的。

  ### 2. 是否符合
  Ticket 正文？

  答：符合 Ticket
  的【目标/What to
  build】说明，但与
  【Acceptance】第
  1 条直接冲突。

  • 符合目标部分：
  在 Ticket T-159
  的 ## What to
  build 中写道：
  │ “目标：分屏保留
  │
  当前窗格并增加右
  │ 侧窗格；任务
  │ agent
  │
  与普通终端若不能
  │
  同屏，操作前说明
  │ 。与 T-139
  │
  的视图模型一致，
  │ 不另做一套。”
  │ 在
  │ 任务卡 T-159-1
  │ 中也写道：
  │ “若任务 agent
  │ 与普通终端按 T-
  │ 139
  │
  视图模型不能同屏
  │ ，按 ticket
  │
  做‘操作前说明’，
  │ 并在 RESULTS
  │ 写明依据。”
  │ Worker
  │
  选择这一分支完全
  │ 是在 Ticket
  │
  目标与任务卡提示
  │
  的授权范围内行事
  │ 。

  • 与 Acceptance
  验收项冲突：
  在 Ticket T-159
  的 ## Acceptance
  中，起草的验收条
  款逐字为：
  │
  │     [ ] 真实
  │
  Electron：任
  │
  务视图点向右
  │     分屏后，原
  │     worker
  │
  与新窗格并排
  │
  ，窗格数、类
  │
  型、目录与菜
  │
  单所述一致。
  │     [ ]
  │
  红态：修前只
  │
  有一个新终端
  │     。
  出入所在：Ticket
  的 Acceptance
  并没有为“操作前说
  明”备选分支设计对
  应的验收清单（例
  如“任务视图禁用分
  屏按钮并给出事前
  说明、直接 IPC
  被拒绝、原 worker
  与布局保持不变”）
  ，而是仍然要求“原
  worker
  与新窗格并排”。候
  选实现的测试
  test_t159_split_e
  2e.py:185-195
  验证的是禁用菜单
  、给出说明、拒绝
  IPC、保留原单
  worker
  窗格，并未执行、
  也无法达成“原
  worker
  与新窗格并排”。

  ### 3.
  判断：应交构思主
  控，不可自己放行

  •
  根据项目治理原则
  （AGENTS.md:58-61
  、user-decision.m
  d 以及
  COMMON-FIX.md:23-
  30）：
  │ “目标、验收、设
  │
  计级的取舍不要自
  │ 己定：上报并在
  │ RESULTS.md
  │
  写明，停在那一项
  │ 。”
  │ “T-157/T-160
  │
  里涉及验收语义的
  │ 选择仍经 needs-
  │ decision。”
  │ “状态逐字报告
  │
  PASS、INCOMPLETE
  │
  、BLOCKED、NO_GO
  │
  ；构思主控转述时
  │ 不上调。”

  •
  验收合同（Accepta
  nce
  criteria）是冻结
  的门禁依据。当实
  现走通了 What-to-
  build
  允许的二选一分支
  ，但导致验收第 1
  条字面不成立时，
  这是典型的验收语
  义未决（Acceptanc
  e Semantic
  Divergence）。
  •
  独立审查员（revie
  wer）不能擅自脑补
  修改验收合同并宣
  布通过，必须把该
  出入指出，评定为
  INCOMPLETE，交由
  构思主控审议并修
  订 Ticket
  的验收条款，待构
  思主控正式确认该
  验收语义后才能做
  集成闭环。
  ──────
  ##
  五项核对清单详细
  评估

  ### 1.
  根因是否找对，改
  动是否在最小根因
  层；有无吞异常、f
  allback、重试、兼
  容分支或平行 API

  • 根因准确：
      •
      修前在任务视
      图中对 worker
      窗格分屏时，
      前端
      renderer.tsx:
      405-408
      未针对非
      shell
      窗格禁用分屏
      操作；
      • 后端主进程
      main.ts:591-6
      07 的
      createTermina
      l 在接收到
      relative
      为任务 worker
      窗格时，未在
      shell_start
      前拦截，随后
      由于检测到
      context.task
      存在，调用
      changeView
      强行切换回项
      目根视图，把
      原任务视图及
      其 worker
      窗格卸载，主
      区只剩一个新
      普通终端。
  •
  改动最小且在根因
  层：
      •
      main.ts:593：
      在
      createTermina
      l
      入口第一步判
      断 if
      (relative &&
      relative.
      project ===
      undefined)
      throw new
      Error('任务视
      图只展示
      Agent
      会话。请在普
      通终端中分屏
      。');
      ，在启动任何
      shell 之前
      Fail-Closed。
      •
      renderer.tsx:
      403-408：在菜
      单渲染中将分
      屏按钮绑定
      disabled={!sh
      ell}，并在下
      方附带 <p
      role="note">
      提示文字；键
      盘导航改为
      button:not(:d
      isabled)
      自动跳过禁用
      按钮。
  •
  无不良工程模式：
      •
      未吞噬任何异
      常（主进程直
      接抛出明确中
      文错误，前端
      显示该错误）
      ；
      •
      无任何自动重
      试、无
      fallback
      分支、无平行
      API
      或中间兼容垫
      片。


  ### 2. Ticket
  的每条验收是否有
  真实入口的证据；
  期望值是否来自
  ticket/规格/用户
  原话

  • 真实入口：
      • 测试
      test_t159_spl
      it_e2e.py
      启动了真实后
      台常驻守护进
      程、门禁系统
      、本地编译的
      受控 PTY
      驱动（control
      led-
      claude）、真
      实 Electron
      窗口，并通过
      Chrome
      DevTools
      Protocol
      (CDP)
      驱动真实 DOM
      点击与 IPC
      调用。全程模
      型请求数为
      0（zero_model
      _requests）。
  • 期望值来源：
      •
      预期断言（原
      窗格保持、普
      通终端分屏的
      几何位置与目
      录继承、任务
      视图禁止混入
      普通终端）均
      直接来自
      T-159 ticket
      、T-139 视图
      规
      和用户真实使
      用报告
      2026-10-23-re
      al-user-dogfo
      od.md:36-43
      的 F03
      条目，不是从
      代码输出反向
      推导抄写的。
  • 验收项比对：
      • 验收项
      1（并排）：候
      选未实现并排
      ，而是实现并
      验证了“禁用并
      事前说明”，见
      上文专项分析
      。
      • 验收项
      2（红态）：修
      前真实
      Electron
      成功重现“只有
      一个新终端，
      原 worker
      消失”，红态证
      据确凿。


  ### 3.
  红态是否落在缺陷
  断言上；变异是否
  代表真实坏实现并
  被拒绝

  • 修前红态：
      • 在基线提交
      c017428049612
      14ed025b6c9fb
      9924a1ea49ee2
      d
      上运行，结果
      见
      red.json:10-7
      8。
      •
      测试在点击向
      右分屏后，精
      确捕获到缺陷
      现场：panes
      只剩 1 个，且
      role 为
      shell，原
      worker
      ddd67143-
      d12e-423a-
      bcab-
      4c326f1b5d28
      消失。测试准
      确落在断言
      AssertionErro
      r:
      task_right_ex
      plains_before
      _action
      上，退出码为
      1。运行脚本
      RUN-OUTSIDE-0
      1.sh:21-28
      机械比对了该
      缺陷现场结构
      。
  • 变异 1（old-
  task-split）：
      • 恢复修前
      main.ts 与
      renderer.
      tsx，运行结果
      见
      mutant-old.js
      on。
      •
      结果：再次重
      现单个普通终
      端替换原
      worker，精确
      触发
      AssertionErro
      r:
      task_right_ex
      plains_before
      _action，被测
      试拒绝（exit
      1）。
  • 变异
  2（missing-split-
  guard）：
      •
      保留前端菜单
      说明和
      disabled
      状态，但移除
      main.ts
      里的入口
      guard 检查。
      •
      结果：前端点
      击被禁用，但
      直接 IPC
      调用绕过了前
      端，成功创建
      了普通终端并
      切走视图，精
      确触发断言
      AssertionErro
      r:
      task_right_ip
      c_refused_wit
      h_explanation
      ，被测试拒绝
      （exit
      1）。证明了仅
      靠前端禁用不
      足以保证后端
      视图契约。


  ### 4.
  是否越出任务卡的
  修改边界；界面文
  案是否清楚、不含
  营销腔

  • 修改边界：
      • 任务卡
      card.md:10
      允许改动
      workbench/app
      /renderer.
      tsx、workbenc
      h/app/*.ts(x)
      视图相关文件
      、新增测试
      workbench/tes
      ts/test_t159_
      *.
      py、证据目录
      、必要的
      workbench/REA
      DME.md。
      • git diff
      显示修改仅包
      含
      README.md:266
      -274、main.ts
      :593、rendere
      r.tsx:403-408
      以及测试文件
      test_t159_spl
      it_e2e.py。没
      有任何越界改
      动。
  • 界面文案：
      •
      文案为：“任务
      视图只展示
      Agent
      会话。请在普
      通终端中分屏
      。”
      • 术语符合
      CONTEXT.md
      标准术语，语
      言简明直接、
      就事论事，无
      任何 AI
      腔调、无营销
      吹嘘词汇。


  ### 5.
  其他正确性与回归
  风险

  •
  普通终端分屏功能
  完好：测试覆盖了
  在子目录（child/
  ）中对普通终端向
  右分屏与向下分屏
  ，验证了分屏后的
  窗格数量（2 格、3
  格）、几何并排排
  布（X 轴/Y
  轴坐标增大）、工
  作目录继承与实际
  pwd
  输出，证明普通终
  端的分屏逻辑未受
  负面影响。
  • T-139
  现有回归全过：tes
  t_t139_selection.
  mjs（25
  项）、test_t139_l
  ayout_store.mjs（
  10
  项）、test_t139_t
  erminal_catalog.m
  js（2
  项）均在修前与修
  后独立跑通，无回
  归。
  ──────
  ##
  审查发现清单（Fin
  dings）

  ### 发现 1（P1 -
  验收合同脱节 /
  语义未决）

  •
  文件与行号：T-159
  -split-keeps-orig
  inal-pane.md:25
  • 严重度：P1
  • 失败场景：
      •
      现象：Ticket
      验收条款第 1
      条要求“真实
      Electron：任
      务视图点向右
      分屏后，原
      worker
      与新窗格并排
      ，窗格数、类
      型、目录与菜
      单所述一致”。
      •
      冲突：候选代
      码实现了
      Ticket
      的备选分支——
      完全禁用了任
      务视图分屏（d
      isabled={!she
      ll}），点击分
      屏不创建任何
      新窗格，界面
      维持单一
      worker
      窗格，无法满
      足验收项“原
      worker
      与新窗格并排”
      。
      •
      处置要求：属
      于 Acceptance
      编写时的遗漏
      （未同步
      What-to-build
      的备选分支条
      件），需移交
      构思主控修订
      ticket
      验收条件，审
      查员不得擅自
      放行。


  ### 2. 发现 2（P3 -
  次要界面文案语境
  瑕疵）

  •
  文件与行号：rende
  rer.tsx:408
  • 严重度：P3
  • 失败场景：
      •
      现象：rendere
      r.tsx:347 中
      shell
      判断逻辑为
      snapshot?.
      launch?.role
      === 'shell'。
      •
      瑕疵：当用户
      在项目终端中
      申请并获批成
      为执行主控（r
      ole ===
      'controller'
      ）时，该终端
      位于项目层（
      非任务视图）
      ，但由于其
      role !==
      role !==
      'shell'，打开
      其窗格菜单时
      也会显示说明
      文字：“任务视
      图只展示
      Agent
      会话。请在普
      通终端中分屏
      。”
      •
      影响：该提示
      在项目级主控
      终端下不够精
      确（此时并非
      处于任务视图
      ），但不影响
      主控正常运行
      ，且
      main.ts:600
      的
      requireShellP
      ane
      本身就限制了
      只有 role ===
      'shell'
      的普通终端才
      能分屏。建议
      后续小修时判
      断如果处于非
      任务视图且非
      shell，文案可
      调整为通用说
      明。

  ──────
  ##
  构思主控移交建议

  请执行主控向构思
  主控（ideation
  controller）呈报
  以下决策项：

  1.
  确认选择分支：确
  认 T-159
  采用“任务视图内禁
  止向右/向下分屏并
  给出事前说明”分支
  ，保持与 T-
  139“普通终端不混
  入任务视图”的视图
  模型一致。
  2. 修订 Ticket
  验收准则：将
  T-159-split-keeps
  -original-pane.md
  :25 的 Acceptance
  第 1 条由：
  │ - [ ] 真实
  │
  Electron：任务视
  │
  图点向右分屏后，
  │ 原 worker
  │
  与新窗格并排，窗
  │
  格数、类型、目录
  │
  与菜单所述一致。
  正式更新为已通过
  测试验证的验收语
  义：
  │ - [ ] 真实
  │
  Electron：任务视
  │ 图 worker
  │ 菜单禁用向右/向
  │
  下分屏并事先说明
  │
  （键盘可跳过），
  │ 直接 IPC
  │ 分屏被拒绝，原
  │ worker
  │
  与任务布局保持不
  │
  变；普通终端向右
  │ /向下分屏正常保
  │ 留原窗格并排。

  3. 构思主控完成
  Ticket
  验收语义确认并更
  新 ready_rev
  后，执行主控即可
  无阻碍集成候选代
  码。

  T-159 REVIEW
  INCOMPLETE

──────────────────────
>
──────────────────────
? for shortcuts```
