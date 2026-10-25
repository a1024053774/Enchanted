  ## 一、第一轮审查三项缺陷复核

  ### 1. 第一轮 发现 1 [P1 回归缺陷] 家目录终端窗格头恒为“未知”

  • 修复核对：
      • 在 sidebar.ts:127-135，普通终端遍历删除了 record.project !== null 过滤条件，家目录终端（record.project === null）重新被纳入 sidebarSnapshot 返回的
      terminals 集合中。
      • 侧栏项目树渲染时通过 ordinaryTerminals.filter(row => row.project === item.project_id)
      过滤，家目录终端不会被错误渲染在具体项目下方，保持侧栏视图干净。
      • 前端 renderer.tsx:996 处的 [...agents, ...ordinaryTerminals].find(...) 能够命中家目录终端的启动记录，获得正确的 state（进程存活时为 'running'）。
  • 证据核对：
      • 在测试 test_t133_t107_terminal_controller_e2e.py:252-260 中新增了 home_terminal_header_known
      检查项（点击“独立终端”，新建终端，检查窗格头状态文本）。
      • 一轮候选红态复现：在 regression-review01-candidate-01.json:125 中，基准代码 2e1f33266 运行该检查时观察值为 "未知"，断言失败。
      • 本轮绿态：在 green-03.json:24 与 #L121，观察值为 "运行中"，测试通过。
  • 判定：已彻底修复，证据确凿成立。
  ──────
  ### 2. 第一轮 发现 2 [P2 验收缺陷] 当 worker 上报等主控但主控空闲时，项目行视觉上无可见“等你”

  • 修复核对：
      • 在 renderer.tsx:868-869，项目行渲染处增加了显式判断：
        {waiting > 0 ? <span className="project-needs">{waiting} 个等你</span>
          : item.state === 'waiting_user_answer' && <span className="project-needs" data-project-needs-you
          title="有上报在等主控答复，但没有主控在回合中">等你处理</span>}

      • 当 worker 状态为 waiting_controller_answer 且没有主控在回合中时，后台 sidebar.ts:147 将项目聚合状态标为 waiting_user_answer。前端由于单会话 waiting
      === 0，走入分支渲染出可见的 <span className="project-needs">等你处理</span> 徽标。
  • 证据核对：
      • 在测试 test_t133_t107_terminal_controller_e2e.py:228-232 中，断言要求 any('等你' in text for text in project_row['visible'])。
      • 一轮候选红态复现：在 regression-review01-candidate-01.json:89-92 中，state 为 waiting_user_answer 但 visible 为 []，测试失败。
      • 本轮绿态：在 green-03.json:90-94 中，visible 成功捕获到 ["等你处理"]，断言通过。
  • 判定：已彻底修复，证据确凿成立。
  ──────
  ### 3. 第一轮 发现 3 [P2 验证缺陷] 缺少 Checks 9、10、11 在修前版本的独立红态与变异体证据

  • 修复核对：
      • 测试脚本 test_t133_t107_terminal_controller_e2e.py:174-182 引入了 soft=True 收集机制：在测试运行中将 T-176
      的新增检查设为软失败并记录现场，待整个完整用例流程执行完毕后在末尾 #L269 统一 assert not soft_failed。
  • 证据核对：
      • 在修前基线 8f36d6495 运行结果 red-main-02.json:35-67 及日志 runs-03.log 中，四个检查项在修前版本上全部跑完并精确捕获了修前坏实现的观察值：
          1. controller_pane_header_matches_row: 窗格头文本为 "运行中"（侧栏为 "idle"）；
          2. project_waits_on_user_when_no_controller_in_turn: 项目状态为 "waiting_controller_answer"，可见文案为空；
          3. worker_pane_header_matches_row_without_second_state: 窗格头为 "空闲"，底栏含 "执行：运行中"；
          4. ended_row_time_says_ended: 结束时间列为 "刚刚"（未加 "结束" 前缀）。
      • 报错明确为：AssertionError: T-176 checks failed: ['controller_pane_header_matches_row', 'project_waits_on_user_when_no_controller_in_turn',
      'worker_pane_header_matches_row_without_second_state', 'ended_row_time_says_ended']。
      • 根据规则，测试必须在坏实现上失败（父版本修前代码、revert 代码或变异体之一）。开发者不仅完整提供了修前父版本的 4 项全红证据，还对一轮候选代码
      2e1f33266 提供了两项复现红态。
  • 判定：已彻底修复，证据链完整闭合。
  ──────
  ## 二、全面核对点审查

  ### 1. 根因是否找对，改动是否在最小根因层；有无吞异常、fallback、重试、兼容分支或平行 API

  • 根因定位与最小改动：
      • 界面多处状态脱节的根因在于各组件各自为政读取底层数据：窗格头此前通过平行字典 lifecycleNames 和 activityNames 读取进程级生命周期（pane?.
      lifecycle），而侧栏读取的是回合事件（agentState）。
      • 改动在 renderer.tsx:27-28 彻底删除了原有的 lifecycleNames 和 activityNames
      平行映射表，窗格头直接统一使用侧栏同一数据源（agentState），消除了系统内的平行状态体系。
      • worker 窗格底栏删除了冲突的二次状态（执行：运行中），消除了双重状态展示。
      • 已结束会话时长从基于启动时间计算（agent.created_at）改为在聚合根因层（sidebar.ts:98-101）通过 SQLite 查询退出事件的最新时间（ended_at）。
  • 纯净性核对：
      • 全量 diff 中无任何新增的 try/catch 吞异常逻辑；
      • 无兜底定时器、无 fallback 超时；
      • 无轮询重试；
      • 无兼容分支或平行 API。

  ──────
  ### 2. ticket 的每条验收是否有真实入口的证据；期望值是否来自 ticket/规格/用户原话

  • 真实 Electron 运行：
      • 验收基于真实隔离 Electron 实例、本地 CDP 驱动、真实的 node-pty 终端与真实 Claude Code 2.1.310 运行环境（本地脚本化接口，零额度消耗）。
  • 各验收条目核对：
      1. 主控回合结束后各处同时显示空闲：
          • 证据：green-03.json:30-36，侧栏行状态为 "idle"，窗格头状态同为 "idle"、显示文本 "空闲"；
          • 视觉截图：green-04-tree.jpg 清晰显示侧栏打勾（空闲）与窗格头“空闲”一致。
      2. worker 窗格头与底栏一致：
          • 证据：green-03.json:108-113，窗格头与行同为 "waiting_controller_answer" / "等主控回答"，底栏文本为
          "在此窗格输入会记录为人工介入"，无任何“执行：”字样。
      3. 主控等用户时项目行写等你回答：
          • 证据：green-03.json:88-94，项目行在两个主控均空闲、worker 等主控时，项目聚合状态为 waiting_user_answer，可见提示文字显示 ["等你处理"]。
      4. 时间列写清启动还是结束：
          • 证据：green-03.json:120，退出的终端显示 "结束 刚刚"；代码 renderer.tsx:66 悬停 title 显式写明 "结束于 ..." 或 "启动于 ...".
      5. 红态截图对照：
          • 证据：red-controller-header.jpg（窗格头显示“运行中”，而侧栏为打勾空闲）与 green-04-tree.jpg（窗格头与侧栏同为“空闲”）形成严格视觉对照。

  • 期望值来源：
      • 全部期望值直接来自 Ticket What to build、Acceptance 以及 findings L03 报告，没有抄写被测物自身的输出。

  ──────
  ### 3. 红态是否在修前版本上落在缺陷断言上；变异是否代表真实坏实现并被拒绝

  • 红态落点：
      • 修前 main（8f36d6495）在 E2E 流程中完整运行并通过了前 7 项基础检查，进入 T-176 的 4 项断言时，全部落在了缺陷行为上（见第一节第 3
      点详细分析），无假红或因环境 setup 失败的偶发红态。
  • 坏实现覆盖：
      • 本票共在两套真实坏实现上进行了验证：
          1. 修前基线 8f36d6495（证明 4 个原始缺陷的存在）；
          2. 第一轮候选 2e1f33266（证明一轮审查发现的 2 个回归缺陷的存在）。


  ──────
  ### 4. 是否越出任务卡的修改边界；界面文案是否清楚、不含营销腔

  • 修改边界核对：
      • 修改文件严格限于 4 个文件：
          • workbench/app/renderer.tsx（前端界面状态统一）
          • workbench/src/sidebar.ts（数据聚合层与结束时间计算）
          • workbench/tests/test_t133_t107_terminal_controller_e2e.py（端到端测试与检查项）
          • workbench/tests/test_t157_stop_input_e2e.py（已有测试的断言同步修正）
      • 无任何越出任务卡范围的不相干修改。
  • 文案风格：
      • 文案为“结束 刚刚”、“结束 N 分”、“结束于 ...”、“启动于 ...”、“等你处理”；
      • 悬停说明为“有上报在等主控答复，但没有主控在回合中”；
      • 客观平实，完全不含营销腔或夸张浮夸词汇。

  ──────
  ### 5. 关于 RESULTS 中“真实运行钩子未送达未查清、未改动”的处置判断

  • 诚实性判断：
      • 完全符合个人代理与项目规范的求真诚实原则。开发者明确界定了“前端多来源显示不一致”与“真实 Claude Code
      偶发未加载插件/未发钩子”属于不同层面的问题，穷尽了安装包与开发树、系统信任、环境变量等多种组合均无法稳定复现后，记录现场为“未知”，未通过猜测性的轮询
      、fallback 超时或重试来粉饰。
  • 后续处置判断：
      • 该底层未知问题是导致 L03 在真实使用中出现“主控回合结束仍转圈”的关键诱因之一（若钩子未送到，即便多处来源一致，也会一同卡在 running 状态）。
      • 构思主控与用户应在 .project-map/tickets/ 单独切出专门的调查与缺陷追踪票（例如 T-xxx: 调查 Claude Code 启动时 Enchanted 插件偶发未加载及
      terminal_turn 丢失根因），独立跟进定位解决，不将其与 T-176 的状态显示一致性耦合。

  ──────
  ### 6. 其他正确性与回归风险检查

  • 已有测试断言同步：
      • test_t157_stop_input_e2e.py:229 此前在 agent['state'] == 'unknown' 时的反例断言期望窗格头为 '忙'（源自旧的 activityNames
      平行映射）。在状态收敛后，agentState 为 unknown 对应的窗格头标准文案为 '未知'。该测试同步更新期望后完整跑通，回归结果见
      regression-t157-02.json，状态为 PASS。
  • 边界情况安全性：
      • 终端/会话未结束时，agent.ended_at 为 null，时间列稳定回退为启动时长 since(agent.created_at, now)，不会输出 NaN 或空白；
      • 窗格无对应 launch 或 launch 丢失时，安全回退至 'unknown' / '未知'，无未捕获异常。

  ──────
  ## 三、审查结论

  第一轮报告指出的 3
  项缺陷已全部修复，修前修后红绿对照证据确凿；改动位于最小根因层，删除了历史遗留的平行映射表，无防御性编程与兼容补丁；界面文案平实合规；钩子未送达处置诚实
  ，需另建卡跟踪。本轮审查通过。

  T-176 REVIEW PASS

