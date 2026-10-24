# T-159 独立审查 02（agy）

- 候选：59a69370b；起点 c01742804
- argv：`agy --model gemini-3.8-flash-high --mode auto --add-dir /Users/luckye/Documents/Code/a2a-review/T-159-r1 -i "$(cat /Users/luckye/Documents/Code/a2a-review/T-159-r1/prompt.txt)"`
- # pane wG:p1W started 2026-10-24T03:17:15Z candidate 59a69370b86728ae34ffb12311c5cf33d5f44594
- 结论：PASS。一条 P3：已关闭的 T-139 ticket 正文仍写“普通终端不混进任务视图”，worker 已经 ISSUE-T139-DOC-SYNC-01.md 上报，由主控处理。

## 窗格原文

```text

      ▄▀▀▄        Antigravity CLI 1.4.7
     ▀▀▀▀▀▀       littledave950@gmail.com (Google AI Pro)
    ▀▀▀▀▀▀▀▀      Gemini 3.8 Flash (High)
   ▄▀▀    ▀▀▄     ~/Documents/Code/a2a-review/T-159-r1
  ▄▀▀      ▀▀▄

────────────────────────────────────────────────────────────
> 你是 a2a 项目的只读独立审查员（reviewer），审查
  T-159：真实使用测试发现（F03）任务视图里点“向右分屏”后，原 worker
  窗格被一个新普通终端替换，不并排。
  用户 2026-10-24 裁定（构思主控转述，见
  user-decision.md）：“任务视图里也可以分屏吧,比如说我想对这个任务有疑问,想开一个
  分屏侧边聊天来讨论这个任务”。即任务视图点分屏保留原
  worker，并排新增一个普通终端；它不是该任务的 agent 会话——不计入
  worker、不占任务路径、不算人工介入，侧栏/窗格头标“普通终端”；默认目录为任务仓库
  根（非
  worker worktree）；同步改
  T-139“普通终端只在项目层”的说明与测试；撤回早先“禁用分屏并说明”的分支（其审查 01
  为 INCOMPLETE，已被取代）。
  执行主控沙箱外运行：outside-01 修前红态（worker 被替换）；outside-04
  两个变异（新窗格替换 worker、普通终端输入被记为 worker
  人工介入）均在预期断言上被拒，T-139/T-143 回归通过，green
  因测试正向对照取错基线报错；outside-05 修该对照后 green 46 项全部
  PASS（含真实正向对照）。
  请特别核对：worker
  窗格与布局确实保留并排；新窗格的角色/目录/归属是否与裁定一致，未进入任务路径、wo
  rker
  计数或人工介入；“禁用并说明”的旧改动是否已完全撤掉；对 T-139
  测试的修改是否只限于此规则；项目层分屏与已批准主控分屏不受影响。

  材料在 /Users/luckye/Documents/Code/a2a-review/T-159-r1/ 下：candidate/ 为候选
  59a69370b 只读副本（ticket 在 candidate/.project-map/tickets/，任务卡、RESULTS
  与运行证据在 candidate/evidence/2026-10-23-batch24/T-159/）；full.diff
  为相对起点 c01742804961214ed025b6c9fb9924a1ea49ee2d 的 workbench/
  全部改动；user-decision.md 为本批用户授权的转述（构思主控 assign）。

  请核对：
  1.
  根因是否找对，改动是否在最小根因层；有无吞异常、fallback、重试、兼容分支或平行
  API。
  2. ticket 的每条验收是否有真实入口的证据；期望值是否来自
  ticket/规格/用户原话而不是抄产品输出。
  3. 红态是否在修前版本上落在缺陷断言上；变异是否代表真实坏实现并被拒绝。
  4. 是否越出任务卡的修改边界；界面文案是否清楚、不含营销腔。
  5. 其他正确性、回归风险。

  这是交互会话。只用你自带的读文件/搜索工具，不要运行任何 shell
  命令，不要写任何文件。可以打开截图。输出中文报告：每条发现写文件与行号、严重度（
  P0–P3）、失败场景。审查完把完整报告作为你最后一条回复直接输出，最后一行只写
  `T-159 REVIEW PASS`、`T-159 REVIEW INCOMPLETE` 或 `T-159 REVIEW NO_GO` 之一。

○ Thought for 2m 29s (Examining the specific checks within the designated file...)
● Explored 28 files (user-decision.md, full.diff, T-159.md,...) (ctrl+o to expand)

▸ Thought for 28s
   T-159 独立审查报告：任务视图内分屏普通终端（F03 修复）

  作为 a2a 项目的只读独立审查员，依据用户 2026-10-24
  裁定原话（“任务视图里也可以分屏吧,比如说我想对这个任务有疑问,想开一个分屏侧边
  聊天来讨论这个任务”）、user-decision.md、full.diff 以及 candidate
  目录下的源码、ticket、测试与沙箱外运行证据，对候选代码进行全面核对。
  ──────
  ## 一、专项要求核对

  1. worker 窗格与布局并排保留
      • 代码实现：在 main.ts:613-642 的 createTerminal 中，彻底删除了旧版在
      context.task 存在时调用 changeView 切到项目视图的逻辑（见
      full.diff:102-105），改为保留任务上下文，并使用 replaceLeaf(context.layout,
      relative.key, { direction, first: relative.key, second: pane.key })
      将新窗格插入到原窗格右侧或下方。
      • 真实运行证据：green.json:40-97 中的 task_right_keeps_worker 与
      task_right_geometry、task_down_keeps_worker 与 task_down_geometry
      均判定通过；worker
      窗格未被替换，几何坐标严格符合并排与上下布局；布局持久化与嵌套恢复通过
      task_explicit_terminals_restored 及 task_restores_down_geometry 验证。
  2. 新窗格角色、目录与归属隔离
      • 身份与标题：新窗格角色为
      shell，窗格头与快照明确标为“普通终端”（renderer.tsx:383-390），侧栏快照中
      仅出现在 terminals，未进入 agents（测试项 task_right_catalog_not_worker
      通过）。
      • 门禁与归属：新终端的 launch 记录中 task、attempt、session、fence 均为
      null（task_right_ordinary_root_terminal 通过），完全不占用任务路径边界。
      • 启动目录：main.ts:616-622 明确规定从任务 agent 分屏时使用 context.task.
      repo（任务仓库根），而非 worker 的隔离 worktree（/worktrees/demo/T-1-
      a1）；真实终端内执行 pwd
      命令输出实测证明落在仓库根（task_right_actual_pwd、task_down_actual_pwd
      通过）。
      • 人工介入隔离与正向对照：向讨论终端输入 pwd 等内容时，独立读取 SQLite
      user_inputs 与后台门禁 human_intervention 事件，计数保持为
      0（task_right_no_intervention、task_down_no_intervention）；在用例末尾向
      worker 真实输入 T159_OBSERVER_CONTROL\r 时，两处计数各严格增加
      1（intervention_observer_positive_control
      确认通过），证明观察器对人工介入具有真实拦截与测量能力，非虚假恒真断言。
  3. 旧“禁用分屏并说明”分支已完全撤回
      • full.diff 显示相较于起点 c017428049，renderer.tsx
      仅包含一行键盘导航跳过禁用项的防御性优化
      button:not(:disabled)；菜单内的“向右分屏”、“向下分屏”按钮无任何 disabled
      属性，亦无“任务视图只展示……”等旧禁用说明文案。
      • test_t159_split_e2e.py 第 467 行显式断言 '任务视图只展示' not in
      menu['explanation']，确认旧禁用逻辑已被彻底清除。
  4. 对 T-139 测试的修改范围
      • test_t139_layout_store.mjs：仅在原有 10 项通过用例后追加了 4
      项针对新裁定的断言（task_restores_only_explicit_project_shell、inspect_ren
      ame_preserves_discussion_layout、close_discussion_keeps_agents、discussion
      _not_gate_task_member），未放宽或删除原有任何隔离断言。
      • test_t139_selection.mjs 与 test_t139_t143_views_perf_e2e.
      py：仅将断言名称与注释中的旧措辞由“任务仅含自己
      agent”更新为“任务排除未选择的项目终端”（task_excludes_unselected_project_t
      erminals），断言逻辑与期望结果集合完全保持原样。
  5. 项目层分屏与已批准主控分屏不受影响
      •
      真实测试对子目录普通终端进行了向右与向下分屏测试（shell_right_keeps_origin
      al、shell_down_keeps_original），验证了子目录继承和双终端可输入；
      •
      对已批准项目主控终端进行了向右分屏测试（project_controller_right_keeps_ori
      ginal），主控的 executor 角色与 terminal
      属性保持完整，分屏窗格同样维持在项目根目录。

  ──────
  ## 二、五项审查标准核对

  ### 1. 根因分析与改动深度

  • 根因准确：F03 缺陷的根因在于 createTerminal 中遇到 context.task 时无条件调用
  changeView
  切换到项目视图，以及布局保存/恢复链路缺乏将显式引入的普通终端与任务视图关联的
  机制。
  • 改动最小且处于根因层：在主进程窗口控制层新增轻量辅助函数
  taskPaneLayout（main.ts:66-79），通过已有的 pane_layout
  接口联合查询任务与项目打开集，既满足了视图并排恢复，又未破坏门禁数据模型。
  • 结构整洁：无吞异常（IPC 均正常
  reject/throw）、无容错重试、无兼容降级分支、无平行 API。

  ### 2. 验收证据与期望值来源

  • 证据链完整：全部证据均来自受控 PTY 驱动的真实 Electron
  自动化验证（zero_model_requests 确认 0 模型请求）。
  • 期望值独立：测试期望值直接取自用户 2026-10-24 裁定要求与 T-159
  任务卡，而非录制实现输出。

  ### 3. 红态与变异检验

  • 真实红态：复用修前产品版本 c017428049 的真实 Electron
  观测证据（red.json:42-76），实际记录向右分屏后原 worker 消失、画面仅剩一个项目
  shell 终端，准确切中 F03 缺陷事实。
  • 变异拒绝：
      • 变异 1（replace-worker）：模拟修前切走任务视图的实现，被断言
      AssertionError: task_right_keeps_worker 拒绝（退出码 1）；
      • 变异 2（shell-input-to-worker）：模拟输入误路由到 worker
      产生介入记录的坏实现，被断言 AssertionError: task_right_no_intervention
      拒绝（退出码 1）。
  • 历史证据合规保存：outside-04 运行因正向对照变量覆盖抛出 KeyError: 'inputs'
  导致 INCOMPLETE，工件被如实保留未覆盖；outside-05 仅修正该对照基线后补跑通过
  46 项检查。

  ### 4. 修改边界与文案规范

  • 改动严格限制在 workbench/README.md、workbench/app/main.
  ￺ts、workbench/app/renderer.tsx
  及相关测试用例内；未越权修改任何门禁逻辑、治理文件或数据库 schema。
  • 文案使用既有界面术语（“普通终端”、“向右分屏”、“向下分屏”等），无任何营销腔。

  ### 5. 正确性与回归风险

  • T-139 / T-143 回归测试全部 PASS，未引入性能退化或视图切换凭据泄露风险。
  • 各进程资源在测试结束后正常释放，cleanup_errors 为空。
  ──────
  ## 三、审查发现与说明（Findings）

  ### 发现 1（P3 - 说明项）：T-139 ticket 描述文档尚未同步新裁定

  • 位置：ISSUE-T139-DOC-SYNC-01.md:1-9
  • 严重度：P3
  • 场景与分析：main 分支的已关闭 ticket T-139-view-model-split-screen.md
  中仍保留旧有目标陈述“项目普通终端……只在它自己的视图里出现，不再混进任务视图”。
  worker 严格遵循任务边界，未擅自修改治理文件，而是通过非阻塞上报 ISSUE-T139-
  ￺DOC-SYNC-01.md 提示主控同步。
  • 建议：后续由执行主控/构思主控在全局治理文档维护时更新 T-139
  历史描述，不影响本次 T-159 验收。
  ──────
  T-159 REVIEW PASS

───────────────────────────────────────────────────────────────────────────────────
>
───────────────────────────────────────────────────────────────────────────────────
? for shortcuts                                             Gemini 3.8 Flash · high```
