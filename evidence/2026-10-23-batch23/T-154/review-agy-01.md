# T-154 独立审查 01（agy）

- 审查员：agy 1.4.6，gemini-3.8-flash-high，Herdr 可见窗格 wG:p19，auto 模式只用读文件工具，只读副本。
- 启动 argv：

```
agy --model gemini-3.8-flash-high --mode auto --add-dir /Users/luckye/Documents/Code/a2a-review/T-154-r1 -i "$(cat /Users/luckye/Documents/Code/a2a-review/T-154-r1/prompt.txt)"
# pane wG:p19 started 2026-10-23T19:38:39Z candidate bf855ff44d3c40c431be5d4a7544f7504ae17def
```

- 审查后候选副本 git status 0 行改动。结论 PASS，无 P0–P3 发现。窗格较窄，结论行被折成两行（`T-154 REVIEW` / `PASS`）。

## 窗格中的报告原文

```text
○ Thought for 3m 11s
● Explored 47 fil...
(ctrl+o to expand)

▸ Thought for 52s
   a2a
  项目独立审查报告
  ：T-154

  ## 审查概述

  • 审查对象：T-
  154（6
  个过时测试整份标
  历史，workbench/
  tests/HISTORICAL
  .md
  更新为最终处置）
  •
  候选版本：bf855f
  f44d3c40c431be5d
  4a7544f7504ae17d
  ef（相对起点
  b058e3a7585ccc85
  df190e90c01b5275
  6c9d076e）
  • 核对材料：
      •
      user-decisio
      n.md（用户授
      权选项
      C：迁移 4
      个，其余 6
      个整份标历史
      并写明“当前
      无人守护这些
      检查”，不删
      、不迁）
      •
      full.diff（w
      orkbench/
      全部改动）
      •
      DISPOSITION.
      md（T-149
      处置调查报告
      ）
      • RESULTS.md
      与任务卡
      card.md
      • 候选工作区
      6
      个受保护测试
      文件与
      HISTORICAL.m
      d

  ──────
  ## 核对要点

  ### 1.
  文件头注释
  revision
  与证据支撑核验

  按要求对 6
  个标历史测试的文
  件头 revision 与
  HISTORICAL.md
  引用的证据文件进
  行比对：

  1.
  test_t112_execut
  ion.mjs:1：
      •
      注释版本：e1
      61476d6bb17e
      6f372d4a3d98
      ed03feccf367
      55
      •
      引用证据：ev
      idence/2026-
      10-22-
      batch20/T-
      127/regress-
      t112-
      execution-
      04.json（PAS
      S）与同目录
      RESULTS.md。
      •
      核对结论：属
      实。该证据记
      录在受控版本
      库中，确为
      T-141
      放宽网络与
      MCP
      契约前，T-
      127
      最后一次对
      T-112
      execution
      回归通过的版
      本。
  2.
  test_quality_tra
  cer_e2e.py:1：
      •
      注释版本：bb
      6c0ba352ff7c
      ab1f470d2db0
      55caac36387b
      ab
      •
      引用证据：ev
      idence/2026-
      10-15-
      batch15/T-
      086/baseline
      -quality-
      tracer-
      loaded/run.
      json（PASS，
      13
      案全过）与
      RESULTS.md。
      •
      核对结论：属
      实。该测试后
      续在带改动工
      作树及 T-
      082（仅跑 4
      案）中运行，
      bb6c0ba3
      是最后一次
      13
      案全部干净通
      过的完整提交
      版本。
  3.
  run_pane_lifecyc
  le.py:1：
      •
      注释版本：历
      史快照（无通
      过证据）
      •
      引用证据：ev
      idence/2026-
      10-10-
      batch12/T-
      075/card-
      4/outside-
      live-
      04/lifecycle
      /verdict.
      json（INCOMP
      LETE）与
      RESULTS.md。
      •
      核对结论：属
      实。历史外部
      运行记录原样
      为
      INCOMPLETE，
      缺失
      turn_context
      ，未曾整份在
      绑定提交上通
      过；执行者如
      实标注“无通
      过证据”，符
      合任务卡“找
      不到就写无通
      过证据，不要
      编”的规定。
  4.
  test_t122_claude
  _worker_e2e.py:1
  ：
      •
      注释版本：01
      e0effd7c1ec9
      bdb982e593fc
      52c22fd0aceb
      77
      •
      引用证据：ev
      idence/2026-
      10-22-
      batch20/T-
      136/candidat
      e-
  1/e2e/t122-g
      reen.
      json（PASS）
      与 commands.
      sh。
      •
      核对结论：属
      实。绑定干净
      detached
      worktree
      候选，T-141
      废弃 --
      strict-mcp-
      config
      前通过。
  5.
  run_t112_native.
  py:1：
      •
      注释版本：e1
      61476d6bb17e
      6f372d4a3d98
      ed03feccf367
      55
      •
      引用证据：ev
      idence/2026-
      10-22-
      batch20/T-
      127/regress-
      t112-native-
      03.
      json（PASS，
      source_head
      为该版本）。
      •
      核对结论：属
      实。T-141
      信任继承废除
      codex_restri
      cted_opened
      之前的最后全
      绿版本。
  6.
  test_t108_questi
  ons.mjs:1：
      •
      注释版本：5f
      19062f521549
      14123e3796fd
      ff87caaa22fc
      1f
      •
      引用证据：ev
      idence/2026-
      10-20-
      batch18/T-
      112/outside-
      merge-
      questions-
      03.json（PAS
      S）与
      outside-
      merge-
      regressions-
      03.json。
      •
      核对结论：属
      实。T-124
      改变 worker
      提问等待契约
      前的最后干净
      通过版本。


  ### 2.
  “无人守护的检查”
  与 T-149
  DISPOSITION
  一致性核验

  逐文件核对注释与
  HISTORICAL.md:44
  -51
  中列出的无人守护
  检查，与
  T-149 DISPOSITIO
  N.md 第 3 节和第
  4 节完全一致：

  •
  test_t112_execut
  ion.
  mjs：五角色设置
  持久化、覆盖参数
  优先级、角色隔离
  、权限字段拒绝、
  未知 effort
  透传、原生启动失
  败记录，全部保留
  ，未漏。
  •
  test_quality_tra
  cer_e2e.
  py：评分必填与仅
  写一次、修复后重
  跑质量串、第三次
  拒绝暂停、严格审
  查
  JSON、原生审查会
  话拒复用、交付回
  合事实绑定，全部
  保留，未漏。
  •
  run_pane_lifecyc
  le.
  py：整窗关闭期间
  PTY
  继续增长、重开逐
  字节回放、后台重
  启后原 attempt
  中断事实、只读输
  入拒绝，全部保留
  ，未漏。
  •
  test_t122_claude
  _worker_e2e.
  py：Claude Git
  元数据与拼接
  git/-
  c/项目钩子攻击矩
  阵、审查
  CLI/模型/Fast/钩
  子绑定、协议失败
  与门禁拒绝留据，
  全部保留，未漏。
  •
  run_t112_native.
  py：真实设置
  DOM→SQLite→下次
  派发→原生首轮请
  求、覆盖优先级、
  未知 effort
  原样透传，保留
  closed_fixture_l
  aunches
  供离线导入，全部
  保留，未漏。
  •
  test_t108_questi
  ons.mjs：Claude
  主控原生问答关联
  、畸形/过期/外来
  hook 与
  permission
  伪造拒收、答复记
  录/写入竞争、重
  复答复拒收，全部
  保留，未漏。

  ### 3. 注释对
  shebang、模块解
  析与离线导入的影
  响核验

  • shebang：6
  个测试文件的原始
  版本均无
  shebang，在首行
  添加 # 或 //
  单行注释不破坏任
  何解释器声明。
  • 模块解析与
  AST：Python
  文件新增首行注释
  后，ast.dump
  与修改前完全一致
  ，PEP 257 模块
  docstring 与
  imports
  保持完好；两个 .
  mjs
  模块经语法解析与
  node --check
  均合法。
  • 离线导入：依赖
  run_t112_native.
  py（如
  test_t112_closed
  _fixture.
  py）及依赖
  Tracer / CASES
  的 15 个离线
  Python
  测试模块导入完全
  正常，离线依赖链
  条未受破坏。

  ### 4.
  修改边界与产品代
  码隔离核验

  •
  修改范围：full.d
  iff 严格限定在 6
  个测试文件（各仅
  增一行文件头注释
  ）与
  HISTORICAL.md；
  证据文件限定在
  candidate/eviden
  ce/2026-10-23-
  batch23/T-154/。
  •
  禁止边界：未修改
  任何产品代码（wo
  rkbench/src/**
  无任何变动）；未
  触碰用户授权由
  T-150～T-153
  迁移的 4
  个文件（test_t09
  1_pane_ipc.
  mjs、test_t078_c
  laude_signals.
  ts、test_t082_re
  view_boundary_e2
  e.
  py、run_worker_d
  elivery.py）。

  ### 5.
  其他正确性核验

  •
  断言与逻辑原样保
  留：6
  个测试文件除新增
  首行注释外，第 2
  行至末尾与起点版
  本逐字节一致，未
  删除、未迁移、未
  改断言，未添加隐
  式 skip。
  • HISTORICAL.md
  索引完整性：
      • 3
      个历史辅助文
      件（diagnose
      _t112_review
      er.
      py、t112_rev
      iewer_record
      .mjs、contro
      lled_quality
      _pty.
      ts）保留在辅
      助文件节。
      • 6
      个测试准确移
      入“整份标历
      史的 6
      个测试”节。
      • 4
      个迁移文件准
      确移入“已迁
      移到现行契约
      （T-150～T-
      153）”节，链
      153）”节，链
      接对应
      ticket，并标
      注迁移合入状
      态。
      • 30 个
      Markdown
      相对链接目标
      均存在于受控
      版本树。
  •
  过程证据留存：前
  期检查失败收据（
  local-check-01.
  json、local-
  check-02.
  json）原样保留，
  未覆写抹除。
  ──────
  ##
  审查发现（Findin
  gs）

  无任何 P0–P3
  缺陷或偏离。
  ──────
  T-154 REVIEW
  PASS

─────────────────────
>
─────────────────────
? for shortcuts
```
