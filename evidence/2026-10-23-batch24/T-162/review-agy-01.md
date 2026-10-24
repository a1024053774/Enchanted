# T-162 独立审查 01（agy）

- 审查员：agy，gemini-3.8-flash-high，Herdr 可见窗格 wG:p1K，auto 模式只用读文件工具，只读副本，候选 304ed8eda。
- 启动 argv：

```
agy --model gemini-3.8-flash-high --mode auto --add-dir /Users/luckye/Documents/Code/a2a-review/T-162-r1 -i "$(cat /Users/luckye/Documents/Code/a2a-review/T-162-r1/prompt.txt)"
# pane wG:p1K started 2026-10-24T00:57:44Z candidate 304ed8eda168e3025e7905f4e2cd7777cab3fdba
```

- 结论 PASS，无 P0～P3 发现。

## 窗格中的报告原文

```text
  ~/Documents/Code/a2a-review/T-162-r1
───────────────────────────────────────────────────
> 你是 a2a 项目的只读独立审查员（reviewer），审查
  T-162：真实使用测试发现（F04）角色批准/拒绝不进“用
  户输入记录”，（F06）指标把查不到的主控回合显示为
  0。ticket
  目标：批准/拒绝进统一输入记录并关联角色申请事件（角
  色批准属于用户输入，见
  CONTEXT.md）；指标区分已核对的零与未知/未覆盖、写明
  口径、给出逐会话计数来源；不把看板数报成全局总回合
  。
  执行主控批准的边界修订：允许改 daemon.ts 的
  role_request_decide 与 roleRequests.ts 的
  decide（只记操作员亲自的批准/拒绝；同角色其他申请的
  自动拒绝、过期不算）。
  执行主控沙箱外跑
  RUN-OUTSIDE-01（修前红态两条缺陷断言 FAIL）与
  RUN-OUTSIDE-02（14 项 PASS：绿态、4 指标变异、3
  Electron 变异含
  non-atomic-decision、T-121、T-133/T-134、原生主控回
  归与审计）。
  请特别核对：决定与输入记录是否原子写入；自动拒绝/过
  期是否被排除；“未知”与“已核对的
  0”在界面与数据层是否都区分；指标口径说明是否准确，
  不夸大覆盖。
  材料在
  /Users/luckye/Documents/Code/a2a-review/T-162-r1/
  下：candidate/ 为候选 304ed8eda 只读副本（ticket 在
  candidate/.project-map/tickets/，任务卡、RESULTS
  与运行证据在
  candidate/evidence/2026-10-23-batch24/T-162/）；ful
  l.diff
  为相对起点 c01742804 的 workbench/
  全部改动；user-decision.md
  为本批用户授权的转述（构思主控 assign）。
  请核对：
  1.
  根因是否找对，改动是否在最小根因层；有无吞异常、fal
  lback、重试、兼容分支或平行
  API。
  2. ticket
  的每条验收是否有真实入口的证据；期望值是否来自
  ticket/规格/用户原话而不是抄产品输出。
  3.
  红态是否在修前版本上落在缺陷断言上；变异是否代表真
  实坏实现并被拒绝。
  4.
  是否越出任务卡的修改边界；界面文案是否清楚、不含营
  销腔。
  5. 其他正确性、回归风险。
  这是交互会话。只用你自带的读文件/搜索工具，不要运行
  任何
  shell
  命令，不要写任何文件。可以打开截图。输出中文报告：
  每条发现写文件与行号、严重度（P0–P3）、失败场景。审
  查完把完整报告作为你最后一条回复直接输出，最后一行
  只写
  `T-162 REVIEW PASS`、`T-162 REVIEW INCOMPLETE` 或
  `T-162 REVIEW NO_GO` 之一。
○ Thought for 6m 18s (`day('2026-10-23', true)` i...)
● Explored 42 files (user-deci...) (ctrl+o to expand)
▸ Thought for 37s
   a2a T-162 独立审查报告
  审查对象：T-162
  真实使用测试发现（F04）角色批准/拒绝不进“用户输入
  记录”，（F06）指标把查不到的主控回合显示为 0
  审查候选提交：304ed8eda（基于基线 c01742804）
  关联资料：
  •
  Ticket：T-162-role-approval-record-and-metrics-tu
  rns.md
  • 任务卡：card.md 与 NEEDS-DECISION.md
  • 交付与运行证据：RESULTS.md 与
  verify-20261024T005052Z-7ae5a172-SUMMARY.json
  • 代码变动：full.diff
  ──────
  ## 1. 根因分析与改动层次
  ### 1.1 F04（角色批准/拒绝记录）根因与改动层
  • 根因：修前 roleRequests.ts 的 decide 方法仅向
  orchestration_events 写入 role_request_decided
  事件，未向 user_inputs
  表写入对应的统一用户输入；前端记录读取层
  userInputRecords.ts 与 RecordsPage.tsx
  亦未关联角色申请 ID 与事件序号。
  • 改动位置：在 roleRequests.ts:101-124
  中，直接在操作员做出决定的根因层写入 A2AUserInput
  记录；在 userInputRecords.ts:23-30 提取
  role_request 与 role_event；在
  RecordsPage.tsx:62-64 呈现关联信息。
  • 原子性与异常处理：写入采用 SQLite BEGIN
  IMMEDIATE ... COMMIT /
  ROLLBACK（roleRequests.ts:101-118），未用 catch
  吞没异常，存储失败时自动回滚，角色申请保持未决定
  状态，异常正常抛出。
  • 排除系统级拒绝与过期：roleRequests.ts:140-142
  中竞争申请的自动拒绝仅写入
  role_request_decided（携带 reason:
  "role_given_to_other"），不经过
  decide，不产生用户输入；roleRequests.ts:121-125
  超时未确认过期触发的是
  role_request_ended，不新增用户输入记录，已发生的
  用户批准依然保留。
  ### 1.2 F06（指标查不到的主控回合显示为
  0）根因与改动层
  • 根因：修前 metrics.ts
  在处理未采集到回合事实的会话时，使用了 facts?.
  turns ??
  0，将“未接入计数来源/未覆盖”与“已核对的零”混淆为
  0；在 byModel 汇总中也直接将 0
  累加，导致看板将查不到主控回合显示为 0。
  • 改动位置：在 metrics.ts:19-28,62-83
  中，记录会话的全部计数来源
  turnSources。若会话无计数来源，turns 明确返回
  null（对应界面“未覆盖”）；若会话有来源但所选区间
  内无事件，返回 0（对应“已核对的
  0”）。汇总在存在未覆盖会话时保持 turns:
  null（界面显示“未知”），并独立输出 recorded_turns
  与 uncovered_sessions。
  • 设计纯度：未引入任何
  fallback、自动重试、兼容过渡分支或平行
  API。daemon.ts:451 的 metrics RPC 接口透传
  metricsSnapshot 结果，无包裹层。
  ──────
  ## 2. 验收条件与真实入口证据
  Ticket
  规定的两项验收条件均通过真实入口进行了端到端验证
  ，期望值来自于需求规格与真实日志事实，而非抄录产
  品输出：
   验收项 │ 验证入口与断言 │ 期望值来源 │ 证据状态
  ────────┼────────────────┼────────────┼──────────
   真实实 │ test_t162_role │ CONTEXT.md │ PASS，详
   例：批 │ _records_metri │ 术语与用户 │ 见截图
   准后记 │ cs_e2e.py：真  │ 原话：亲自 │ [01-
   录页出 │ 实 Electron    │ 点击产生两 │ role-rec
   现该条 │ 界面点击批准执 │ 条输入（批 │ ords.png
   并关联 │ 行主控与拒绝构 │ 准/拒绝各  │ ](file:/
   角色事 │ 思主控，断言   │ 一），关联 │ //Users/
             │ 批准执行  │ 申请 ID    │
             │ 主控与拒  │ 与事件序号 │
            │ ser_inputs、de │ 关联申请 │
            │ cision_event_i │ ID       │
            │ s_linked、reco │ 与事件序 │
            │ rd_page_shows_ │ 号；竞争 │
            │ decisions_and_ │ 者自动拒 │
            │ event_sources  │ 绝不进输 │
            │                │ 入       │
   指标：主 │ 1.             │          │
   控回合与 │ test_t162_role │          │
   原生日志 │ _records_metri │          │
   核对一致 │ cs_e2e.py：Ele │          │
   ，或明确 │ ctron          │          │
   显示“未  │ 界面主控行显示 │          │
   覆盖/未  │ “未覆盖”，汇总 │          │
   知”      │ 显示“未知（已  │          │
            │ 记录 0；未覆盖 │          │
            │ 2              │          │
            │ 个会话）”，断  │          │
          │ controller_wit │            │
          │ hout_native_co │            │
          │ unt_is_unknown │            │
          │ 、unknown_is_n │            │
          │ ot_summed_as_z │            │
          │ ero；2.        │            │
          │ test_t162_nati │            │
          │ ve_controller_ │            │
          │ audit.mjs：读  │            │
          │ 取 T-133       │            │
          │ 既有真实       │            │
          │ Claude CLI     │            │
          │ 运行留存的原生 │            │
          │ .jsonl（构思主 │            │
          │ 控 4           │            │
          │ 个根回合，执行 │            │
          │ 主控 1         │            │
          │ 个），断言指标 │            │
          │ 快照对两个主控 │            │
          │ 均返回 turns:  │            │
          │ null 与空来源  │            │
  ──────
  ## 3. 红态复现与变异测试有效性
  ### 3.1 修前红态（RUN-OUTSIDE-01）
  在修前基线提交 c01742804 上运行
  RUN-OUTSIDE-01.sh，准确命中了真实缺陷断言，无夹具
  或环境初始化错误（red-20261024T003707Z-17506.json
  ）：
  •
  two_explicit_decisions_are_user_inputs：FAIL（修
  前未写入用户输入表，实际为 []）
  •
  controller_without_native_count_is_unknown：FAIL
  （修前主控会话 turns 为 0）
  •
  unknown_is_not_summed_as_zero：FAIL（修前汇总模型
  turns 为 0）
  • native-controller-
  parent：FAIL（修前对拥有真实原生提示的主控会话误
  报为 turns: 0）
  ### 3.2 变异测试（RUN-OUTSIDE-02 中 7 项变异）
  7
  项变异均代表真实的坏实现或回归风险，且全部被针对
  性断言拒绝：
  1. metrics-mutant-unknown-as-zero：变异为 facts?.
  turns ?? 0，被 no_source_is_unknown 拒绝。
  2. metrics-mutant-zero-as-unknown：变异忽略
  turnSources 存在性，被
  verified_recorded_zero_is_distinct 拒绝。
  3. metrics-mutant-source-dropped：变异丢弃
  turn_sources，被 claude_replay_sources 拒绝。
  4. metrics-mutant-range-
  ignored：变异移除时间区间判断，被
  old_session_with_in_range_turns_is_included
  拒绝。
  5. electron-mutant-unknown-as-
  zero：变异端到端指标默认 0，被
  controller_without_native_count_is_unknown 拒绝。
  6. electron-mutant-decision-
  unrecorded：变异不写入统一输入，被
  two_explicit_decisions_are_user_inputs 拒绝。
  7. electron-mutant-non-atomic-decision：移除
  BEGIN IMMEDIATE 与 COMMIT，注入存储故障时断言
  decision_and_input_roll_back_together
  失败（事件未回滚，产生孤立决定事件），被成功拦截
  。
  ──────
  ## 4. 修改边界与界面文案审查
  ### 4.1 修改边界核对
  • 任务卡与主控批准修订范围：
      •
      允许改动：userInputRecords.ts、metrics.ts、Re
      cordsPage.tsx、MetricsPage.tsx、必要的
      README.md 行、本票测试及 evidence。
      • 经主控 #30 批准修订卡：允许改动
      roleRequests.ts 的 decide 方法。
      • 禁止改动：.project-map/**、AGENTS.
      md、CONTEXT.md、他人测试。
  • 审查核验结果：检查
  full.diff，改动文件完全落在上述授权范围内，未修改
  daemon.
  ts，未触碰任何受保护文件，工作区无越界污染。
  ### 4.2 界面文案与口径表达
  • MetricsPage.tsx:48-50 文案准确阐明：
  │ “回合数只统计所选时间内后台采集的 Claude
  │ 回合事实和 Codex
  │
  回合上下文，按事件时间筛选。项目终端主控未接入这
  │ 些计数来源时显示‘未覆盖’；人工输入后的回复、CLI
  │ 回执只有被这些来源采集时才计入。Reflect
  │ 复盘不在此表中，这不是全局总回合。”
  │ “0
  │ 表示该会话有计数来源，但区间内没有对应记录；‘未
  │ 知’表示汇总中还有未覆盖的会话。展开来源可核对会
  │ 话、事件序号与原生日志位置。”
  •
  文案克制平实，无营销腔与浮夸词汇，明确警示用户“这
  不是全局总回合”，准确履行了口径披露要求。
  • README.md:1020-1035
  同步更新了记录页与指标页说明，内容与代码行为完全
  一致。
  ──────
  ## 5. 其他正确性与回归风险
  1. 事务完整性：
  roleRequests.ts:101-118 在同一个 SQLite
  连接上开启 BEGIN IMMEDIATE，先后执行
  orchestration_events 写入与 user_inputs
  写入并提交。若任一步骤异常，finally 中的
  isTransaction
  回滚保障了数据库绝对不会产生半提交孤立记录。
  2. 已有功能回归验证：
      • T-121 角色申请与生命周期：49 项检查
      PASS（regression-t121.json）。
      • T-133/T-134 用户输入与四个指标：14 项检查
      PASS（regression-t133-t134.json）。
      • T-133/T-107 原生终端主控回归：13 项检查
      PASS（regression-native-controller.json）。
  3. 模型开销与外部副作用：
  全部 14 项外部测试均使用隔离夹具与脚本化本地
  Messages 接口，供应商真实模型回合消耗为
  0，符合安全基线。
  4. 范围外发现处理：
  README 中既有旧 Codex
  描述不一致问题已正确通过非阻塞上报记录于
  OUT-OF-SCOPE.md，未违规随手扩改。
  ──────
  ## 6. 缺陷发现清单（P0–P3）
  经全面审查，未发现 P0、P1、P2 或 P3 缺陷。
  ──────
  T-162 REVIEW PASS
──────────────────────────────────────────────────────
>
──────────────────────────────────────────────────────
? for shortcuts                Gemini 3.8 Flash · high
```
