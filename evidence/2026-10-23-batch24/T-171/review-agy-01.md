# T-171 agy 独立审查报告（gemini-3.8-flash-high，Herdr wG:p2M，只读副本 6e40db3ce）

独立审查报告

  审查对象：T-171（修订重派后，旧 attempt 的 blocking 问题仍挂着“等你决定、阻塞”）
  审查基线/版本：起点 9093958a，修前版本 15a444674，候选副本 6e40db3ce
  涉及改动范围：full.diff（仅含 workbench/ 下 5 个文件，+184 / -3 行）
  审查依据：user-decision.md（构思主控 answer 选 A / 用户授权逐字选项）、candidate/.project-map/tickets/T-171-superseded-blocking-
  issue.md、candidate/evidence/2026-10-23-batch24/T-171/

  ## 发现项清单

  ### 发现 1（P3 - 轻微关注 / 边界测试覆盖）

  • 文件与行号：core.ts:680-686
  • 严重度：P3
  • 失败场景：
  在当前端到端测试 test_t171_superseded_issue_e2e.py 中，仅覆盖了 worker 上报并在 revise
  后标记为“可能已随修订失效”的主路径。对于以下两处负向分支未在端到端中构造独立断言（虽然代码逻辑显式受限且作者在 ticket Resolution 与 RESULTS.md
  中已声明“未覆盖”）：
      1. 门禁系统自动生成的阻塞问题（from: "system"，如代码质量打回停止或协议错误）在 attempt revise 后保持原有状态；
      2. 控制器发起的普通 revoke（非 revise，如超时或人工撤销，revocation_reason 不是 "spec revised"）下的未关闭问题不展示失效提示。
      影响评估：代码逻辑非常直接（issue.from !== "system" 与 attempt.revocation_reason === "spec revised"），且静态分析与 schema
      约束均能保证其正确性；未覆盖声明据实记录，无隐瞒，风险可控。


  ## 核心核查结论

  ### 1. 根因分析与改动层级

  • 根因准确：根因在于 revise 重派时，作废 attempt 下未关闭的问题依然停留在 待判断 / 等你决定 链条中，未考虑上报所在的 attempt 已因任务卡修订而失效。
  • 改动处于最小根因层：改动集中在问题状态解析的唯一真源 A2AGates.readIssues（core.ts:676-694），将状态解析为 "可能已随修订失效" 并附带
  superseded_by_revision 上下文；闭环处于 disposeIssue（core.ts:845-853），沿用既有用户关闭处置流程。
  • 无不良模式：全量 diff 中无吞异常、无 fallback 机制、无重试、无兼容性双写分支、无平行 API。

  ### 2. 重点要求核查

  #### (1) 判定条件范围与防误伤

  • 仅覆盖 revise 作废的 attempt 下仍未关闭的问题：
  判定逻辑为：issue.from !== "system" && issue.attempt_id && ["等你决定", "待判断", "稍后", "已转交"].includes(state)，并查询 attempts 表校验 attempt.state
  === "revoked" && attempt.revocation_reason === "spec revised"。
  • 防误伤核实：
      • 当前 attempt：state 为 preparing / claimed / submitted 等，未被 revoked，不会被标记（变异测试 any-attempt 专门验证了此点并被拒绝）。
      • 普通 revoke：revocation_reason 为自定义原因而非 "spec revised"，不会被标记。
      • 系统问题：门禁生成的协议/质量问题其 from 严格为 "system"，直接被 issue.from !== "system" 排除。
      • 已答复/已关闭问题：已答复（已答复、已送达）或已关闭（已关闭）不在开放状态集合中，不会被覆盖重写。


  #### (2) 状态一致性与全链路消费者

  • 侧栏 issues_waiting 计数：daemon.ts:469 统计 view.state === '等你决定'，可能已随修订失效 不再计入。
  • 工作区页签角标：renderer.tsx:834 由 project.issues_waiting 驱动，同步显示为实际有效等待数（1 而非 2）。
  • 收件箱等待判定：core.ts:3174-3176 inboxIssueWaiting 严格对比 state === "等你决定"，失效问题不进入用户收件箱等待队列。
  • Retrospective 复盘包：retrospective.ts:171-196 直接读取底层 issue_records 的基础记录，关闭动作记录为标准
  disposition，数据无缝接入，不产生状态未决或未知错误。
  • 界面与排序：IssuesPage.tsx:9 将 '可能已随修订失效' 加入 open 集合，保持未决问题顶部排列；状态徽标取中性色，不渲染急迫的 'needs' 高亮。

  #### (3) 用户输入记录与主控权限

  • 用户输入契约（A2AUserInput）：
  在 core.ts:846-853 中，通过 saveUserInput 写入标准字段：
      • form: "action", channel: "issue-panel", certainty: "observed"
      • text: "确认关闭：" + args.reason
      • target: { task, attempt, thread, turn: null, message: null }（经 saveUserInput 自动补充 project）
      • source_ref: { event_id: record.id, source_sequence: sequence }
      • question: { number, title, body }
      完全契合既有契约；在“记录”页（RecordsPage.tsx）形态列显示为“操作”，来源列显示为“问题面板”。
  • 主控权限保持受限：
  门禁规则 core.ts:793（requireGate(!view.issue.blocking || actor === "user", "blocking_requires_user")）照旧生效。主控试图调用 disposition close
  时被硬性拦截并报错 blocking_requires_user，测试已真实断言。

  #### (4) 测试有效性：独立来源、红态与变异

  • 期望值独立性：测试期望直接取自用户原话、决策选择 A 及 ticket 规格，非事后对照输出编写。
  • 修前红态（red-2）：在修前版本 15a444674 上，测试失败且精准落在缺陷断言上（旧问题未标记为失效、角标为 2 未减去、卡片缺少确认按钮），见 red-2-01.png
  截图。
  • 变异拒绝：
      • auto-close（跳过用户确认直接自动关闭）：被拒绝，断言 old_issue_marked_superseded 与 confirm_shows_full_issue 失败；
      • any-attempt（不限定 attempt 来源）：被拒绝，断言 new_issue_still_waiting 失败。
  • 回归：T-132 问题面板既有端到端测试 PASS（reg-t132）。

  #### (5) 界面文案与边界控制

  • 文案客观平实：
  卡片提示文案为：“上报它的 attempt
  已在修订任务卡时作废，任务已按新卡重新派发，这个问题可能已经不成立。它不再计入等你决定。请看上面的原文，确认不再需要处理就关闭；仍需处理的照常答复。”，按
  钮文案为：“确认已失效，关闭”。无夸大形容与营销修饰。
  • 边界严守：修改完全局限在任务卡授权的 workbench 问题展示与关闭流内，未越出组件或引入额外功能。

  T-171 REVIEW PASS
