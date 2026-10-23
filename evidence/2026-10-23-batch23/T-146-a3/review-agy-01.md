# T-146-3 独立审查 01（agy）

- 审查员：agy 1.4.6，模型 gemini-3.8-flash-high，Herdr 可见窗格 wG:pH，交互 auto 模式（只用读文件工具），只读副本，候选 7f204cb35。
- 启动 argv：

```
agy --model gemini-3.8-flash-high --mode auto --add-dir /Users/luckye/Documents/Code/a2a-review/T-146-a3-r1 -i "$(cat /Users/luckye/Documents/Code/a2a-review/T-146-a3-r1/prompt.txt)"
# pane wG:pH started 2026-10-23T13:35:38Z
```

- 审查后核对：候选副本 git status 0 行改动。结论 PASS，无发现项。
- 执行主控注：沙箱外运行中 t145 失败为起点 bf932d499 已知问题（T-145-2 已在 main 045e8cfb1 修复），合入后回归复核。

## 窗格中的报告原文

```text

○ Thought for 4m 22s (Completed tasks ar...)
● Explored 56 files (ctrl+o to expand)

▸ Thought for 38s
   T-146 第三个 Attempt（T-146-
  3）独立审查报告

  作为 a2a
  项目的只读独立审查员，对候选版本
  7f204cb35（相对起点
  bf932d49940104ec099023aa957d06fe95116e92
  ）按用户裁定 B
  及任务卡要求完成独立审查。
  ──────
  ## 一、核对项逐项审查结论

  ### 1. 裁定 B 实现与三处同源性核对

  • 实现情况：
      • 流程页（flow.ts:41-46）：移除了
      agent.state !== 'ended'
      的两处过滤（任务泳道绑定条件与未归属
      会话过滤），使已结束的
      worker、reviewer、monitor
      以及主控保留在流程页中展示；FlowPage
      .tsx:6-16 渲染状态图标 ✓
      及文字状态“已结束”。
      •
      侧栏（sidebar.ts:173-183）：保留已确
      认生效的主控角色（含 roleRequest.
      state === 'ended'），将其以 role:
      'controller'、state: 'ended' 保留在
      agents 中；并在 renderer.tsx:696 与
      style.css:62 中，将 state ===
      'ended' 的状态标签从 sr-only
      切换为可见文字，直观展示“已结束”。
      • Reflect 页（reflect.ts:35 与
      daemon.ts:407-412）：消费
      sidebarSnapshot
      提供的状态映射，已结束主控和 worker
      均展示 ended（“已结束”）。
  • 同源性：
      • sidebar_snapshot 直接由 sidebar.ts
      计算生成。
      •
      flow_snapshot（flow.ts:51）直接调用
      sidebarSnapshot 并将 sidebar.agents
      传给 projectFlow。
      •
      reflect_tree（daemon.ts:409）在后台
      调用 sidebarSnapshot 并将 sidebar.
      agents 的状态映射传入 reflectTree。
      •
      三处完全共用侧栏投影状态，无任何独立
      推断分支。
  • 状态准确性：
      • sidebar.ts:178 在读取
      terminal_turn 之前优先判定
      roleRequest.state === 'ended' ?
      'ended'，关闭终端后不会被历史未结束
      turn 覆盖。
      • 沙箱外真实 Electron 截图（t146-
      green-02-after-cli-exit.png 与 t146-
      green-03-after-close.
      png）和数据快照证实：CLI
      退出和终端关闭后，三处页面均一致标为
      “已结束”，没有任何一处把已结束错误显
      示为运行中。

  ──────
  ### 2. 已结束主控终端的身份、层级与 T-
  139 规则核对

  • 展示身份：
      • role: 'controller'
      • preset: roleRequest.role（如
      'executor' 或 'ideation'）
      • role_label: '执行主控' /
      '构思主控'
      • terminal: true
      • state: 'ended'，state_label:
      '已结束'
  • 展示层级：
      • task:
      null，保持在项目层级（若有父主控则挂
      在父主控下，无父主控则为项目顶级），
      绝不混入具体任务内。
  • 普通终端隔离：
      • sidebar.ts:187 普通终端遍历条件为
      !agents.some(agent => agent.id ===
      record.id)。因关闭的主控终端仍留在
      agents 中，因此被严格排除在
      terminals
      之外，不再出现“主控关闭后回退为普通
      终端”的不一致问题。未确认过角色的终
      端仍正常列入 terminals。
  • T-139 规则无回退：
      •
      任务视图与普通终端视图严格分离。沙箱
      外回归测试
      test_t139_t143_views_perf_e2e.py
      全项通过（task_A_only_its_agents,
      worker_only_itself,
      controller_only_itself
      等全部通过），项目终端视图规则保持完
      好。

  ──────
  ### 3. 受保护文件改动与授权范围核对

  • 受保护测试改动范围：
      •
      test_t111_flow.mjs:36-37：严格仅在第
      36 行断言中加入 'ended'（['w1','w2',
      'ended']），第 37 行补充断言其状态为
      'ended'；其余断言、检查名、期望值完
      全未改。
      •
      test_t146_cli_exit_probe.py:56：仅将
      sidebar in ('MISSING', 'ended')
      改为契合 B 的 sidebar ==
      'ended'，Reflect 期望未变。
      •
      test_t146_session_state_e2e.py:416-4
      43：将自然退出及关闭主控后允许
      MISSING 的断言收紧为必须为 'ended'
      并断言界面文字可见及主控身份属性；新
      增支持变异测试入口。未放宽任何断言，
      未改动其他 oracle paths。
  • RESULTS.md 记录核对：
      •
      RESULTS.md:52-66“受保护测试的逐条变
      更”章节逐条记录了修改文件、候选行号
      、旧期望、新期望与修改依据，与 Git
      实际变更完全吻合。

  ──────
  ### 4. 新测试独立性与红态/变异针对性核对

  • 新测试独立性：
      •
      test_t146_ended_projection.mjs：独立
      构造 SQLite
      数据，针对业务规则直接断言关闭主控的
      身份、状态、普通终端去重、历史会话不
      授予权限（roles.approved(terminal.
      id) ===
      undefined）、只读无修改、Flow 与
      Reflect
      包含已结束节点、同一终端再次确认角色
      时替换单行等场景，未借用生产计算逻辑
      作为答案。
      •
      test_t146_red_verdict.py：判据自测验
      证红态检验逻辑拒绝超时
      sentinel，确保反例判定必须达到目标阶
      段并出现具体业务违约字段。
  • 红态与变异落地核对：
      • 起点红态（t146-red.json）：在起点
      bf932d499 上运行，流程页遗漏 ended
      worker，侧栏 ended 标签不可见，被
      red_verdict.py 准确捕获。
      • T-111 互拒证明：新 test_t111_flow.
      mjs 在基线上运行失败（t111-red.
      json，缺少 ended）；旧
      test_t111_flow.mjs
      在候选上运行失败（t111-old-on-
      candidate.json，多出
      ended），证明改动精确对应且仅对应规
      则 B。
      • 变异 1 flow-hide-ended（t146-
      mutant-flow.
      json）：恢复流程隐藏已结束会话后，fl
      ow_natural_cli_exit
      阶段准确拦截流程丢失 ended worker。
      • 变异 2 controller-becomes-
      shell（t146-mutant-controller.
      json）：恢复关闭主控仅按 approved
      过滤后，主控从 agents
      丢失且被降为普通 shell
      终端，准确被判定拦截。

  ──────
  ### 5. 架构整洁度与正确性核对

  • 无吞异常：未增加任何空的 catch
  块或静默异常处理。
  • 无 Fallback / 平行路径：
      • 侧栏投影统一处理终端生效历史，未为
      Reflect 或 Flow
      编写专有状态计算通道。
      •
      角色显示与权限解耦：历史已结束主控仅
      用于界面展示，底层 roleRequests.
      approved()
      在终端存活或角色结束后均返回
      undefined，杜绝任何历史越权隐患。
  • 同终端多次确认角色：
      • 侧栏按 launch
      过滤仅保留最新确认生效的角色（sideba
      r.ts:174），保证 DOM key
      唯一；Reflect
      页按角色申请历次保留（reflect.ts:32
      ），符合设计规范。

  ──────
  ## 二、沙箱外运行结果与证据核对

  沙箱外执行记录（evidence/outside-
  20261023T132912Z-1738/）核对如下：

  • t146-green.json：PASS（45
  项检查全部通过，包含 DOM
  轮询、截图、主控及 worker
  状态与标签可见性核对）。
  • t146-red.
  json：符合预期红态，red_verdict.py
  验证通过。
  • t146-mutant-flow.json / t146-mutant-
  controller.
  json：变异均被拒绝，red_verdict.py
  验证通过。
  • projection.json / red-verdict-checks.
  json / session-end.json：PASS。
  • t111-green.json：PASS；t111-red.json
  与 t111-old-on-candidate.
  json：新旧合同互拒成功。
  • t091-candidate.json：与 t091-baseline.
  json
  保持完全一致的错误和状态，证明不更差。
  • 回归套件：
      • t139-t143.json：PASS。
      • t140.json：PASS。
      • t137.json：PASS。
      • t107.json：PASS。
      • t145.
      json：失败项（“超时：鼠标模式输出已
      显示”）为起点 bf932d499
      既有基线问题（已在 main 045e8cfb1
      修复），不影响本候选评估。

  ──────
  ## 三、审查发现列表（Findings）

  无 P0、P1、P2、P3
  级别代码缺陷或回归问题。

  • 备注信息（Context Note）：
      •
      test_t146_red_verdict.py:258：判据自
      测脚本引用了 evidence/2026-10-23-
      batch23/T-146-a3/red_verdict.
      py。该自测仅在沙箱外随 RUN-OUTSIDE-
      01.sh 一同运行，在代码库的常规
      sparse-checkout 中该 evidence
      目录若未检出则仅跳过判据自测，不属于
      生产产品代码或标准 e2e。

  ──────
  T-146-3 REVIEW PASS
```
