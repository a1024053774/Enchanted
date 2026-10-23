# T-139 / T-143 独立审查 01（agy）

- 审查员：agy 1.4.6，模型 gemini-3.8-flash-high，Herdr 可见窗格 wG:p8，交互 auto 模式（只用读文件工具），审查对象为只读副本（候选 7c60d0d67）。
- 启动 argv：

```
agy --model gemini-3.8-flash-high --mode auto --add-dir /Users/luckye/Documents/Code/a2a-review/T-139-T-143-r1 -i "$(cat /Users/luckye/Documents/Code/a2a-review/T-139-T-143-r1/prompt.txt)"
```

- 审查后核对：候选副本 git status 0 行改动。结论 PASS，三条 P3 观察项。

## 窗格中的报告原文

```text

○ Thought for 4m 52s (The code handles failures by disabling standard input and updating...)
● Explored 40 files (card.md, COMMON.md, T-139-view-model-split-screen...) (ctrl+o to expand)

▸ Thought for 57s
   T-139 与 T-143 联合候选交付独立审查报告

  审查对象：候选提交 7c60d0d67043a660315ab1f8bfc97a2a6d57b3d5（基线起点
  ebbae7bd09cee3a8220b948029f9033dc2906c90）
  关联卡号：T-139（视图模型分屏与隔离）、T-143（终端性能与窗格切换）
  验证材料：沙箱外联合验收 RUN-OUTSIDE-05（COMPARISON.json、各项 json/log 与真实 Electron
  截图）、full.diff、card.md、RESULTS.md。
  ──────
  ## 一、核对详情

  ### 1. T-139：视图模型与窗格行为

  • 项目视图分屏展示任务列表：
  在 candidate-01-project.png 中，项目 demo 视图在同屏以网格形式分屏列出 demo+T-A 和 demo+
  T-B 两个任务卡片（每任务一格，展示门禁状态、标题、ID、agent 数量及跳转箭头）。测试检查
  project_two_task_tiles 通过。
  • 进任务只显示该任务 agent，不含项目普通终端：
  点击任务 T-A 后（candidate-02-task-A.png），主屏仅展示该任务下的受管
  worker，彻底移除了修前在 prepareSelection 中强行追加项目终端的代码。检查
  task_A_only_its_agents 通过。
  • 点单个 agent 只见它自己：
  侧栏点击 worker 时（candidate-03-worker.png），屏幕仅展示该 worker
  自身，不带项目主控或任务其它 agent。检查 worker_only_itself 通过。
  • 项目普通终端有独立入口且只在它自己的视图出现：
  侧栏通过 sidebarSnapshot 将普通终端分离至 terminals
  集合，并在界面独立终端区渲染（candidate-05-ordinary-terminal.png）；经申请成为主控的终端
  点击后亦仅展示其自身（candidate-04-controller.png）。检查
  controller_only_itself、ordinary_terminal_only_itself 及 project_does_not_mix_terminals
  均通过。
  • 窗格布局持久化：
  在单 agent 视图中进行重命名或关闭时，serializedArrangement
  重新读取已保存的完整窗格集合并仅替换对应叶子节点，不清除同级兄弟会话及其名称。test_t139_l
  ayout_store.mjs 在真实 SQLite store 和守护进程校验下通过 10 项断言，e2e
  中重命名后切出再切回验证了 layout_name_persisted。
  • 凭据复用与只读/隐藏隔离：
  同 agent 再次点击复用相同窗格凭据（same_agent_does_not_reissue_credential）；隐藏/parked
  窗格的 snapshot 明确返回 input_enabled: false 且不带
  window_id（inactive_snapshot_cannot_enable_input）；向隐藏窗格发送输入会被拒绝抛出
  Unknown pane key（inactive_input_rejected）；已结束（ended）的 worker
  无法获取输入凭据并拒绝输入（ended_has_no_input_credential_and_rejects_input）。

  ### 2. T-143：性能改动与前后数字

  • 同一夹具同一命令的前后测量：
  测试均在相同夹具（两个真实 Claude CLI worker + 一个真实项目终端主控）上，使用统一的 5000
  行编号命令 python3 -c 'for i in range(5000): print("BENCH_%05d" % i)' 测量。
  • 改动项保留与撤除：
      1. 屏幕阅读器模式默认关闭（renderer.tsx:193）：切换耗时中位数从 99.45 ms 缩短至 89.30
      ms（提升 ~10.2%），并提供设置面板手动开启入口。有改善，保留。
      2. 切换窗格保留已连接 xterm（最多保留 4 个未显示终端，超出 LRU
      淘汰）：切换耗时中位数从 83.90 ms 缩短至 75.00 ms（提升 ~10.6%）。在最终 RUN-OUTSIDE-
      05 中，切换耗时中位数由基线 108.75 ms 降低至候选 78.35 ms（整体缩短 ~28.
      0%）。有改善，保留。
      3. WebGL 渲染插件：前期实验由于 context lost 及未能有效激活
      WebGL2，整体未证明改善。生产候选已彻底撤除，package.json 与 package-lock.json
      无任何残留依赖。
      4. 缩短轮询（100ms → 16ms）：切换耗时未见改善（78.05 ms → 81.70
      ms）。已撤回，生产保持 100ms 轮询，未残留推送分支。
  • 未将封顶 FPS 计为收益：
  由于受 macOS/Electron 屏幕垂直同步 60Hz 封顶限制，基线（60.004 FPS）与候选（60.002
  FPS）无统计差异。Worker 在交付说明与主控在 COMPARISON.json 中均明确记录 scroll_claim:
  "未证明改善；平均帧率受刷新率封顶"，并引入端到端可见耗时（output_to_visible_ms：167.30 ms
  → 148.90 ms，缩短 ~11.0%）作为独立指标，未将刷新率封顶的 FPS 谎称为收益。
  • 输出完整性、焦点与输入正确性：
      • 切换前后 5000 行输出完整无缺失无重复（numbered_output_once_before_switch 与
      numbered_output_once_after_switch 均 PASS）。
      • 隐藏期间在后台产生的输出，重新切回时准确补齐且仅出现一次（hidden_output_once
      PASS）。
      • 切换回窗格后，焦点在恢复与绘制完成后准确回到
      textarea（controller_focus_after_switch
      PASS），输入能够准确路由到对应终端（focused_input_routes_correctly PASS）。


  ### 3. 架构与规范核对

  • 无吞异常：main.ts 各 IPC 处理器和内部逻辑均正常向调用方抛错；renderer.tsx:308-311
  的读取循环捕获错误后设置状态以在界面展示告警条并禁用输入，未吞掉底层错误。
  • 无 fallback、兼容分支或平行路径：未引入 WebGL 失败回退 DOM
  的分支；未引入轮询与推送并存的平行链路；未针对普通终端做双写或兼容 shim。
  • 严格遵守修改边界：
  所有改动均在卡片允许范围之内（main.ts、renderer.tsx、style.css、sidebar.ts、README.md
  及测试）。renderer.tsx 中由 T-140 worker 维护的项目行菜单未被触碰；未修改 .project-
  map/**、AGENTS.md、CONTEXT.md 或任何受保护验收文件。

  ### 4. 测试独立性、红态与变异体核对

  • 测试独立性：期望断言（如 5000 行 BENCH_%05d 编号集合、DOM
  视图元素筛选、落盘文件标记）均独立于实现代码定义。
  • 红态准确落地：在基线提交 ebbae7bd0 上运行新 e2e 测试，准确失败于 5 个声称的检查项：
      1. task_A_only_its_agents（失败：任务视图混入了项目终端）
      2. worker_only_itself（失败：worker 视图混入了项目终端）
      3. project_two_task_tiles（失败：修前无每任务一格的任务网格）
      4. project_does_not_mix_terminals（失败：项目视图直接渲染终端）
      5. ordinary_terminal_reachable（失败：普通终端无独立侧栏导航）
  • 变异体准确击中：
      1. mutant-task-includes-project-terminal：命中
      task_A_only_its_agents、worker_only_itself、inactive_snapshot_cannot_enable_input、in
      active_input_rejected。
      2. mutant-duplicate-replay：命中
      numbered_output_once_before_switch、numbered_output_once_after_switch、hidden_output_
      once。
      3. mutant-inactive-input：命中 inactive_input_rejected。


  ### 5. 回归与正确性核对

  • 历史回归测试：
      • test_t107_live_sidebar_e2e.py：PASS。
      • test_t133_t107_terminal_controller_e2e.py：PASS。
      • test_t091_pane_ipc.mjs：在起点即因既有 IPC
      接口白名单断言失败，候选版本表现与起点完全一致，未引入退化，满足主控裁定。

  ──────
  ## 二、发现与说明清单

   编号   │ 位置                              │ …  │ 场景与说明
  ────────┼─────────────────────────────────────┼────┼─────────────────────────────────────
   OBS-01 │ renderer.tsx:399                    │ P3 │ 渲染期递增 ref
          │                                     │    │ 状态版本：组件在渲染体中直接执行 if
          │                                     │    │ (visibility.current.active !==
          │                           │        │ visibility.current = { active, version:
          │                           │        │ visibility.current.version + 1 };。在当前
          │                           │        │ Electron
          │                           │        │ 运行模式下，其目的是确保激活瞬间与后续读
          │                           │        │ 取/聚焦的视次对齐，防止旧视次的
          │                           │        │ restoring=false 提前窃取焦点，单元测试
          │                           │        │ test_t143_retained_focus.mjs 及真实 e2e
          │                           │        │ 验证均正常无副作用。
   OBS-02 │ test_t139_t143_views_perf │   P3   │ 滚动帧率受系统刷新率封顶：在 60Hz
          │ _e2e.py:1155-1165         │        │ 屏幕下，滚动平均帧率被严格封顶在 ~60
          │                           │        │ FPS（基线 60.004 vs 候选 60.002）。Worker
          │                           │        │ 与主控均如实记录“未证明改善”，未将其包装
          │                           │        │ 为优化，符合证据诚实原则。
   OBS-03 │ test_t091_pane_ipc.mjs    │   P3   │ 既有 IPC 白名单差异：该 oracle 在修前起点
          │                           │        │ ebbae7bd0
          │                           │        │ 即失败，本次候选版本生成的报错与起点完全
          │                           │        │ 一致，执行主控已定按“与起点同样、不更差”
          │                           │        │ 验收。

  注：本交付无 P0（致命故障）、P1（严重缺陷）或 P2（普通功能阻碍）问题。
  ──────
  ## 三、审查结论

  T-139
  实现了项目任务分屏与三层导航隔离，窗格布局持久化健全，输入凭据严格限制于当前可见且可写的
  会话；T-143
  准确落实了先量后改，保留了有效改善切换耗时的改动（读屏默认关与窗格连接保留），彻底清除了
  无效的 WebGL 及其依赖，未把封顶 FPS
  当作收益，回放与焦点行为严密可靠；测试具备充分的独立性，红态与变异体全部精确落于声称点，
  受保护验收测试无回归。

  T-139-T-143 REVIEW PASS
```
