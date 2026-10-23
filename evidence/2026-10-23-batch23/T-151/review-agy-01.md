# T-151 独立审查 01（agy）

- 审查员：agy 1.4.6，gemini-3.8-flash-high，Herdr 可见窗格，auto 模式只用读文件工具，只读副本。
- 启动 argv：

```
agy --model gemini-3.8-flash-high --mode auto --add-dir /Users/luckye/Documents/Code/a2a-review/T-151-r1 -i "$(cat /Users/luckye/Documents/Code/a2a-review/T-151-r1/prompt.txt)"
# pane wG:p15 started 2026-10-23T19:07:39Z candidate b5b520a9e350ffe8779281d3d1921b1a4e5410c9
```

- 审查后候选副本 git status 0 行改动。结论 PASS，无 P0–P3 发现。报告首次结束时缺结论行，执行主控在同一会话追问一行结论，得到 PASS（未要求重写报告）。

## 窗格中的报告原文

```text
○ Thought for 3m 15s (The cod...)
● Explored 41 fil... (ctrl+o to
expand)

▸ Thought for 31s
   T-151 独立审查报告

  审查对象：T-151 候选提交
  b5b520a9e（任务卡 T-151-1 /
  a1）
  审查范围：workbench/tests/tes
  t_t078_claude_signals.ts、相
  关证据目录 evidence/2026-10-
  23-batch23/T-151/、用户授权
  user-decision.md 及项目契约
  审查结论：全部 5
  项核对点均符合契约与规范，未
  发现 P0–P3 严重度缺陷。
  ──────
  ## 1. 逐项核对分析

  ### 1.1
  断言过时性与新期望来源

  • 过时原因确认：原测试中
  record 未指定
  role，运行时走非 controller
  分支；在匹配 Stop
  时触发现行契约 panes.ts:1518
  对 this.claudeTurnFacts
  的调用。原夹具未在磁盘提供
  native-session.jsonl，导致
  readFileSync 报
  ENOENT。这属于夹具缺少模型事
  实/transcript
  前提，而非业务断言契约被废弃
  。
  •
  改动性质：未删除、反转或弱化
  原测试中的任何断言。原有的 7
  处有效断言（startController
  入口存在性、UserPromptSubmit
  后的 busy 状态、首次 Stop
  后的 idle 状态与 active
  清空、首次 Stop 后 pane_idle
  计数为 1、重复 Stop 后
  pane_idle 计数仍为 1、外来
  session_id
  拒收）全部百分之百原样保留。
  • 新期望来源独立性：
      •
      test_t078_claude_signals.
      ts:16-19：合成写入的用户
      promptId
      与助手回复模型（claude-
      haiku-5-
      5），作为测试夹具的合成输
      入，并非抄自产品代码当前
      输出。
      •
      test_t078_claude_signals.
      ts:41：新增 assert.
      equal(pane.claudePromptId,
      promptId)，明确校验提交绑
      定。
      •
      test_t078_claude_signals.
      ts:44：新增 assert.
      equal(store.read().find(e
      => e.type ===
      "pane_idle")!.data.
      submission,
      "submission")，明确核验
      pane_idle
      关联当前活跃提交 ID。
      • 期望值均严格来自 T-151
      与 T-078
      规定的领域状态契约。


  ### 1.2 ticket
  列出有效检查的完整保留

  T-151
  ticket（T-151-migrate-t078-cl
  aude-signals.md:18）列出的有
  效检查全部保留：

  1. 已登记 active submission
  的 UserPromptSubmit/Stop
  关联：
      • UserPromptSubmit
      后状态保持 busy 且绑定
      claudePromptId（保留并加
      强）；
      • 匹配 Stop 后状态转为
      idle，pane.active
      置空，pane_idle 指向该
      submission（保留并加强）
      。
  2. 重复 Stop 不重复产生
  pane_idle：
      •
      test_t078_claude_signals.
      ts:45-46：原样保留对第二
      次 Stop 发送后 pane_idle
      总数仍为 1 的严格断言。
  3. 异会话拒收：
      •
      test_t078_claude_signals.
      ts:48-50：原样保留对外来
      session_id 抛出
      hook_native_session_misma
      tch 拒绝的断言。
  4. 主控运行时入口存在性：
      •
      test_t078_claude_signals.
      ts:38：原样保留对 (panes
      as any).startController
      的类型校验。


  ### 1.3 红态落点与变异真实性

  • 变异设计：RUN-CHECKS-01.py
  注入变异 duplicate-stop-
  idle（RUN-CHECKS-01.py:35-39
  ）。在 panes.ts 的 Claude
  Stop
  分支中，当未匹配到活跃提交时
  （如重复
  Stop），错误地追加记录
  pane_idle 事件。
  •
  代表真实缺陷：在调度与生命周
  期契约中，重复发射 pane_idle
  会引发主控重复派发或过早唤醒
  等状态损坏，是 Stop
  去重保护的核心防护场景。
  • 红态落点：
      • 变异执行时进程退出码
      1，精准触发保留的原有断言
      test_t078_claude_signals.
      ts:46
      失败（AssertionError:
      Expected values to be
      strictly equal: 2 !==
      1）。
      •
      红态落在保留的未修改有效
      检查上，其余两个检查（入
      口存在性与异会话拒收）保
      持
      PASS，没有因夹具错误、导
      入异常或被改断言误伤。


  ### 1.4
  修改边界与产品代码完整性

  • 产品代码未修改：根据 full.
  diff
  以及仓库状态，workbench/src/*
  * 与 workbench/app/**
  零修改。
  •
  测试与索引边界：未修改任何其
  他测试，未修改
  workbench/tests/HISTORICAL.
  md，未修改 .project-map/**。
  •
  修改限制：代码修改仅局限于获
  授权文件
  test_t078_claude_signals.ts；
  其余新增文件全部位于凭证目录
  evidence/2026-10-23-
  batch23/T-151/。

  ### 1.5 正确性与实现细节

  • 测试环境与隔离：测试使用
  mkdtempSync 独立临时目录与
  SQLite 内存/临时
  store，测试末尾通过 store.
  close()
  妥善关闭连接，无外部依赖或网
  络/PTY 泄漏。
  •
  状态退出码：当且仅当所有检查
  通过时设置 process.exitCode =
  0，否则置
  1，符合测试运行框架与脚本要求
  。
  • 变异脚本设计：RUN-CHECKS-
  01.py
  使用独立的只读临时副本执行变
  异测试，检查锚点唯一性，拒绝
  覆盖已有
  summary，不污染当前仓库工作树
  。
  ──────
  ## 2. 审查发现列表

   序… │ 文件与行… │ 严… │ 失…
  ─────┼───────────┼─────┼─────
   1   │ test_t078 │ 无  │ 角
       │ _claude_s │ 缺  │ 色
       │ ignals.ts │ 陷  │ 明
       │ :21-23    │ (PA │ 确
       │           │ SS) │ 设
       │           │     │ 置
       │           │     │ 为
       │           │     │ wor
       │           │     │ ker
       │           │     │ ，
       │           │     │ 保
       │           │     │ 持
       │           │     │ 走
       │           │     │ 非
       │           │     │ con
       │           │     │ tro
       │           │     │ lle
       │           │     │ r
      │            │     │ 的
      │            │     │ 真
      │            │     │ 实
      │            │     │ 产
      │            │     │ 品
      │            │     │ 分
      │            │     │ 支
      │            │     │ ，
      │            │     │ 未
      │            │     │ 通
      │            │     │ 过
      │            │     │ 伪
      │            │     │ 造
      │            │     │ con
      │            │     │ tro
      │            │     │ lle
     │            │        │ ，
     │            │        │ 未
     │            │        │ 通
     │            │        │ 过
     │            │        │ 伪
     │            │        │ 造
       │           │     │ t
       │           │     │ 读
       │           │     │ 取
       │           │     │ 。
   2   │ test_t078 │ 无  │ 正
       │ _claude_s │ 缺  │ 确
       │ ignals.ts │ 陷  │ 构
       │ :16-19    │ (PA │ 建
       │           │ SS) │ 符
      │            │     │ 合
      │            │     │ cla
      │            │     │ ude
      │            │     │ Tur
      │            │     │ nFa
      │            │     │ cts
      │            │     │ 解
      │            │     │ 析
      │            │     │ 格
      │            │     │ 式
      │            │     │ 的
      │            │     │ JSO
      │            │     │ NL
      │            │     │ tra
      │            │     │ nsc
     │ claude_sig │ (PASS) │ 正
     │ nals.ts:16 │        │ 确
     │ -19        │        │ 构
     │            │        │ 建
     │            │        │ 符
     │            │        │ 合
     │            │        │ l
     │            │        │ a
     │            │        │ u
     │            │        │ d
     │            │        │ e
     │            │        │ T
     │            │        │ u
     │            │        │ r
     │            │        │ n
     │            │        │ F
     │            │        │ a
     │            │        │ c
     │            │        │ t
     │            │        │ s
     │            │        │ 解
     │            │        │ 析
     │            │        │ 格
     │            │        │ 式
     │            │        │ 的
     │            │        │ S
     │            │        │ O
     │            │        │ N
     │            │        │ L
      │            │     │ 定
      │            │     │ 的
      │            │     │ 检
      │            │     │ 查
      │            │     │ ，
      │            │     │ 来
      │            │     │ 源
      │            │     │ 明
      │            │     │ 确
      │            │     │ ，
     │            │        │ ，
     │            │        │ 修
     │            │        │ 复
     │            │        │ N
     │            │        │ O
     │            │        │ E
     │            │        │ N
     │            │        │ T
     │            │        │ 夹
     │            │        │ 具
     │            │        │ 缺
     │            │        │ 陷
     │            │        │ 。
   3 │ test_t078_ │ 无缺陷 │
     │ claude_sig │ (PASS) │ 新
     │ nals.ts:41 │        │ 增
     │ , L44      │        │ 断
     │            │        │ 言
     │            │        │ 加
     │            │        │ 强
     │            │        │ 对
     │            │        │ u
     │            │        │ b
     │            │        │ m
     │            │        │ i
     │            │        │ s
     │            │        │ s
     │            │        │ i
     │            │        │ o
     │            │        │ n
     │            │        │ 与
     │            │        │ l
     │            │        │ a
     │            │        │ u
     │            │        │ d
     │            │        │ e
     │            │        │ P
     │            │        │ r
     │            │        │ o
     │            │        │ m
     │            │        │ p
     │            │        │ t
     │            │        │ I
     │            │        │ d
     │            │        │ 绑
     │            │        │ 定
     │            │        │ 的
     │            │        │ 检
     │            │        │ 查
     │            │        │ ，
     │            │        │ 来
     │            │        │ 源
     │            │        │ 明
     │            │        │ 确
     │            │        │ ，
     │            │        │ 未
     │            │        │ 放
     │            │        │ 松
     │            │        │ 任
     │            │        │ 何
     │            │        │ 原
     │            │        │ 有
     │            │        │ 检
     │            │        │ 查
     │            │        │ 。
   4 │ test_t078_ │ 无缺陷 │
     │ claude_sig │ (PASS) │ 重
     │ nals.ts:45 │        │ 复
     │ -46        │        │ t
     │            │        │ o
     │            │        │ p
     │            │        │ 检
     │            │        │ 查
     │            │        │ 原
     │            │        │ 样
     │            │        │ 保
     │            │        │ 留
     │            │        │ ；
     │            │        │ 在
     │            │        │ u
     │            │        │ p
     │            │        │ l
     │            │        │ i
     │            │        │ c
     │            │        │ a
     │            │        │ t
     │            │        │ e
     │            │        │
     │            │        │
     │            │        │
     │            │        │
     │            │        │

───────────────────────────────
> 你的报告没有按约定以结论行结尾
  。请不要重写报告，只回复一行：T
  -151
  REVIEW PASS、T-151 REVIEW
  INCOMPLETE 或 T-151 REVIEW
  NO_GO 之一。

  T-151 REVIEW PASS

──────────────────────────────────
>
──────────────────────────────────
? for shortcuts
```
