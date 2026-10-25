   T-181 候选交付（468cde5b2）独立审查报告

  本审查为只读独立审查，核对范围涵盖
  full.diff、user-decision.md、RESULTS.md、测试脚本、运行日志与截图
  证据。
  ──────
  ## 核心核对结论汇总

   核对项                  │ 结论 │ 证据依据
  ───────────────────────────┼──────┼──────────────────────────────
   L09 根因推理与最小修复    │  成立  │ PTY 有亮白 ANSI
                             │        │ 转义（38;5;231），xterm
                             │        │ 缓冲区有文字，浅色底色（纯
                             │        │ 白）下对比度接近 1:1
                             │        │ 导致空白；minimumContrastR
                             │        │ atio: 4.5
                             │        │ 属于渲染层标准最小修复，不
                             │         │ 不入侵全局配置，深浅自适
                             │         │ 应。
   开局说明与 SKILL 准确性   │  合格   │ 事实无误（后台不主动向
                             │         │ PTY 推送交付通知；run
                             │         │ 后台运行由 Claude Code
                             │         │ 异步唤起；相对路径保障
                             │         │ worker
                             │         │ 独立隔离区工作）。无诱导
                             │         │ 越权措辞，明确限制只有用
                             │         │ 户要求时才申请且由用户界
                             │         │ 面批准。
   真实 Haiku 复跑与共用约定 │ 基本合  │ cards.json 中 T-1 与 T-2
                             │   格    │ 目标均明确写清 restock.md
                             │         │ 格式；最终回复如实报告了
                             │         │ 状态、反例漏洞、并发冲突
                             │         │ 与分支回执；但 T-2
                             │         │ 验收脚本对格式断言存在漏
                             │         │ 检（见发现 3）。
   测试期望与红态有效性      │  合格   │ 期望来自实测原话与
                             │         │ ticket；修前 red-main-01
                             │         │ 明确落在 3
                             │         │ 项缺陷断言上；测试超时与
                             │         │ T-180 缺陷均在 RESULTS
                             │         │ 中如实记录。
   修改边界与分支基线        │  阻断   │ 候选分支基于旧基线，diff
                             │         │ 包含对已合并 T-178
                             │         │ 的完全回退与测试文件删除
                             │         │ （见发现 1）。
  ──────
  ## 审查发现清单

  ### 1. [P1] 候选分支基线漂移，误回退已集成的 T-178 改动并删除测试

  • 文件与行号：
      • workbench/README.md
      • workbench/app/FlowPage.tsx
      • workbench/app/flow.css
      • workbench/app/renderer.tsx#L107
      • workbench/tests/test_t178_flow_project_scope_e2e.py
  • 严重度：P1
  • 失败场景：
  在 full.diff 中，候选 468cde5b2 相对 main 删除了
  test_t178_flow_project_scope_e2e.py（deleted file mode
  100644），并将 FlowPage.tsx 中的项目范围过滤、折叠分组逻辑以及
  renderer.tsx 中的 <FlowPage project={selectedProject} />
  全部回退为未分项目的初始版本。若将此候选直接集成到 main，将导致
  T-178 成果被静默抹除，产生严重功能回退。
  • 整改建议：
  执行主控必须将 T-181 分支 rebase 到最新的 main，仅保留 T-181
  自身所需的改动（终端渲染对比度、SessionStart 钩子、CLI
  开局说明、SKILL.md 及 T-181 新增测试）。
  ──────
  ### 2. [P2]
  真实主控端到端测试的回合结束检测逻辑存在缺陷，导致无谓等待 900
  秒超时

  • 文件与行号：
      • test_t181_real_controller_e2e.py:629-636
  • 严重度：P2
  • 失败场景：
  测试脚本中使用 last = next((r for r in reversed(rows) if r.
  get('type') == 'assistant'), None) 匹配助手末尾回合。然而在
  Claude Code 2.1.310
  的原生会话记录中，助手回答后追加的一条记录类型为 type:
  "assistant" 但仅含 API 请求元数据（无 message
  属性）；真实的回复内容保存在前一条记录中。这导致 last.
  get('message', {}).get('stop_reason') 恒为 None，脚本无法识别已于
  80 秒结束的真实回合，死等至 900 秒 deadline（outcome:
  timeout_900s）。
  • 整改建议：
  修改查找条件为匹配含 message 字段的记录，例如 last = next((r for
  r in reversed(rows) if r.get('type') == 'assistant' and 'message'
  in r), None)，使测试在回合真实结束时能及时退出并断言 outcome ==
  'turn_ended'。
  ──────
  ### 3. [P3] T-2 验收脚本未对共享格式约定进行机械断言

  • 文件与行号：
      • acceptance-scripts.json:3（/tmp/a2a-cards/check_readme.py）
      • cards.json:157
  • 严重度：P3
  • 失败场景：
  虽然 Haiku 主控在 T-2 的卡片目标中明确要求
  说明中的示例格式须与输出约定一致：- 物品名：库存 X，最低 Y，需补
  Z。，但生成的验收脚本 check_readme.py 仅做了关键字核对：
    for key in ["stock.csv", "restock.md", "min"]:
        if key not in text:
            sys.exit(f"用法说明缺少 {key}")
  脚本未断言 README 中是否包含约定格式的示例。如果 worker 在 README
  中写了相反排版或错误格式，机械门禁依然会误放行，必须依赖人工或独
  立审查兜底。
  ──────
  ### 4. [P3] 规范工件缺失独立 ticket 文件与任务卡归档

  • 文件与行号：
      • tickets/
      • T-181/
  • 严重度：P3
  • 失败场景：
  仓库中未创建 tickets/T-181-*.md 独立文件，亦未在 evidence/2026-
  10-25-batch25/T-181/ 归档形式化的 task-card.md，仅以 inbox 派工单
  20261025T035611Z-ideation-assign-001.md 与 RESULTS.md
  代替。虽在紧急修复批次中说明清晰，但与项目规范要求存在格式偏差。
  ──────
  ## 详细审查证据与核对

  ### 1. L09（问答框正文空白）复现与修复验证

  • 证据文件：
      • 修前截图：red-main-01-long.jpg（正文行完全空白，暗色像素仅
      32，为左侧边框）
      • 修后截图：green-01-long.jpg（正文清晰可见，暗色像素提升至
      12,004）
      • 短问题对照：red-main-01-short.jpg vs
      green-01-short.jpg（像素由 0 提升至
      866，“先做哪一个？”清晰显示）
  • 根因确认：
  Claude Code 假设终端为暗色背景，输出 38;5;
  231（纯白粗体）。在工作台默认浅色背景上呈现白字白底。xterm.js 的
  minimumContrastRatio: 4.5
  通过自动将与背景对比不足的前景色调深，以最简方式解决了问题，未触
  碰用户全局配置。

  ### 2. 开局说明与文本核对

  • 源码位置：terminalCli.ts:49-52
  • 内容审查：
  文案仅提示 a2a 位于 PATH、a2a help 查命令、做主控时直接 a2a
  request executor 等待界面批准、派工前阅读
  skill。措辞严谨、不含营销腔，且在无 terminal identity
  环境下不输出，未产生意外副作用。

  ### 3. 真实 Haiku 复跑过程及回复核对

  • 会话记录：native-transcript.json:9807-9812
  • 工具调用与执行流：
      1. 调用 Skill 工具加载 enchanted-a2a:a2a；
      2. 调用 a2a request executor（timeout
      600000），由测试在界面批准；
      3. 未在文件系统中搜寻 a2a，未出现 AskUserQuestion 阻断；
      4. 验收脚本均使用相对路径 Path("restock.md")、Path("README.
      md")；
      5. 并发派发时遇到
      operation_busy，查状态后成功重试一次，未进入死循环；
      6. 派发完成后查一次状态即结束回合，无 sleep 轮询。
  • 回复如实性：
  Haiku
  回复中如实告知工作分支“沿用已有分支”，因前序失败请求在后台已建好
  分支，后台回执返回 existing，模型忠实转述了回执事实，并对
  neg_reversed 样本未拦截情况如实向用户声明交由人工审查。
  ──────
  ## 结论

  T-181 的核心缺陷修复（L09 渲染对比度与 L08
  终端开局引导）根因准确、方案精简、无异常吞噬或兼容分支，在真实
  Haiku 与真实 Electron 上均取得了坚实的验证证据。但由于候选提交
  468cde5b2 携带了对已集成功能 T-178
  的完全回退与测试文件删除，构成不可接受的破坏性集成风险。必须在完
  成 rebase 并修复测试脚本的回合检测 Bug 后重新评估。

  T-181 REVIEW NO_GO
