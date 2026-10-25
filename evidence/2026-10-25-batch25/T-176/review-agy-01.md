  ## 一、审查概述

  审查对象：T-176（来源：findings/2026-10-25-lcu-real-use.md L03；ticket：T-176-session-state-consistency.md；commit：2e1f33266）。
  对比基线：8f36d6495。

  本次审查核对了 5 项核心要求，并重点核对了真实运行中钩子未送达的处理、真实 Electron 端到端验收证据、修前红态落点、改动边界与正确性回归风险。
  ──────
  ## 二、核心核对点审查

  ### 1. 根因是否找对，改动是否在最小根因层；有无吞异常、fallback、重试、兼容分支或平行 API

  • 界面状态来源不一致的根因找对并完成最小改动：
      • 窗格头状态此前直接读取进程生命周期（pane?.lifecycle），导致主控回合结束后终端 zsh 存活时仍显示“运行中”。改动直接收敛为从侧栏同一数据源读取
      agentState，删除了原有的 lifecycleNames 和 activityNames 两个平行映射表（renderer.tsx:27-28），消除了平行状态体系。
      • worker 窗格底栏的多余状态（“执行：运行中”）被直接删除，不再显示与窗格头冲突的进程级生命周期。
      • 结束时长此前基于启动时间计算（agent.created_at），现增加 SQLite 查询 MAX(time) 提取退出事件时间（ended_at），在聚合根因层解决。
  • 无吞异常、无重试、无兼容补丁：
      • 全量 diff 未添加任何新的 try/catch 吞异常逻辑，未添加轮询或重试。


  ### 2. ticket 的每条验收是否有真实入口的证据；期望值是否来自 ticket/规格/用户原话

  • 主控回合结束显示空闲：有真实 Electron + CDP + Claude Code 2.1.310 脚本化运行证据（green-02.json:30-35），ideation_pane 的 row 与 header 同为 idle /
  空闲，伴有对照截图 green-04-tree.jpg。
  • worker 窗格头与底栏一致：有证据（green-02.json:102-107），底栏无“执行：”字样，头部与侧栏同为“等主控回答”。
  • 主控等用户时项目行聚合：在测试中检查了 data-project-state === 'waiting_user_answer'。但在视觉呈现上存在与验收条目不符的缺口（见发现 2）。

  ### 3. 红态是否在修前版本上落在缺陷断言上；变异是否代表真实坏实现并被拒绝

  • 修前红态落点：在 --revision 8f36d6495 上，测试运行到 Check 8（test_t133_t107_terminal_controller_e2e.py:187）即断言失败（侧栏为 idle，窗格头仍为
  running/运行中），保存了红态截图 red-controller-header.jpg。Check 8 确实准确落在了修前缺陷断言上。
  • 红态覆盖不完整：因为四个新检查项串行在一个 E2E 测试中，Check 8 断言失败直接终止了进程，导致 Check 9、10、11
  在修前基线上从未执行过，且测试脚本未为这三项提供 --mutant（见发现 3）。

  ### 4. 是否越出任务卡的修改边界；界面文案是否清楚、不含营销腔

  • 修改完全限定在 workbench/app/renderer.tsx、workbench/src/sidebar.ts 以及对应的两个测试文件内，无越界修改。
  • 文案采用“结束 刚刚”、“结束 N 分”、“结束于 ...”，无营销浮夸词汇。
  ──────
  ## 三、关于 RESULTS 中“钩子未送达原因未查清”的处置判断

  ### 诚实性判断

  该处理完全符合个人代理规范的诚实与实事求是原则：

  1. 开发者在排查中没有把“界面多来源不一致”与“真实 Claude Code 偶发未加载插件/未发钩子”混为一谈；
  2. 开发者穷尽测试了开发树与安装包、预先信任与弹窗信任、Herdr 环境变量、settings.json 等配置，均无法稳定复现该丢失现场；
  3. 开发者没有加任何猜测性的 fallback 超时、兜底定时器或重试来掩盖未知；
  4. 开发者在 RESULTS.md:3 中明确将本卡状态定为 INCOMPLETE，没有将未完全解决的实测现象粉饰为 PASS。

  ### 需要的后续处置

  虽然开发者态度诚实，但该未知现象是导致 L03
  在真实使用中出现“主控回合结束仍转圈”的关键诱因之一（若钩子未送到，即使界面同一来源，侧栏和窗格头也会一同停留在批准时的 running）。
  后续处置：

  • 不能将该问题仅作为 RESULTS 里的文本备注就此放过；
  • 构思主控/用户需在 .project-map/tickets/ 单独切出专门的调查/缺陷 Ticket（例如 T-xxx: 调查 Claude Code 启动时 Enchanted 插件偶发未加载及 terminal_turn
  丢失根因），记录已排查的环境变量与复现边界，独立建卡解决。
  ──────
  ## 四、具体缺陷与发现列表

  ### 发现 1 [P1 回归缺陷] 独立终端（家目录普通终端）窗格头状态永久显示为“未知”

  • 位置：sidebar.ts:196 与 renderer.tsx:995
  • 代码分析：
  在 sidebar.ts:196：
    for (const record of store.launches().filter(record => record.role === 'shell' && record.project !== null &&
      !agents.some(agent => agent.id === record.id))) {
  在 renderer.tsx:995：
    agentState={[...agents, ...ordinaryTerminals].find(agent => agent.id === launches[key])?.state}

  • 失败场景：
  当用户在家目录下打开“独立终端”（free-terminals，其 record.project === null）时，sidebarSnapshot 的 launches（过滤了 role !==
  'shell'）不含它，terminals（过滤了 record.project !== null）同样将其排除。
  因此在前端 [...agents, ...ordinaryTerminals].find(...) 永远为 undefined，传给 SessionPane 的 agentState 恒为 undefined。
  根据 renderer.tsx:448：
    <span className="pane-state" data-state={error ? 'unknown' : agentState ?? 'unknown'}>
      {error ? '未知' : stateNames[agentState ?? 'unknown'] ?? '未知'}
    </span>
  独立终端只要打开，窗格头状态永久显示为“未知”，即便 shell 正常运行并交互。而在修改前，普通终端读取 lifecycleNames[pane?.lifecycle] 能正常显示“运行中”。
  ──────
  ### 发现 2 [P2 验收缺陷] 当 worker 上报等主控但主控空闲时，项目行视觉上并未显示“等你回答”

  • 位置：renderer.tsx:852、#L868-L871
  • 代码分析：
  在 renderer.tsx:852：
    const scope = agents.filter(agent => agent.project === item.project_id);
    const waiting = scope.filter(agent => agent.state === 'waiting_user_answer').length;
  在 renderer.tsx:868-871：
    {waiting > 0 && <span className="project-needs">{waiting} 个等你</span>}
    {item.issues_waiting === null ? <span className="project-needs" ...>问题数未知</span>
      : item.issues_waiting > 0 && <span className="project-needs" ...>{item.issues_waiting} 个问题</span>}
    <span className="sr-only project-state">{item.state_label}</span>

  • 失败场景：
  当 worker 提出 issue（worker 本身状态为 waiting_controller_answer），且项目内所有主控均处于空闲时：
      1. 后台 sidebar.ts:233 确实把 project.state 聚合为了 waiting_user_answer，state_label 为 '等待用户回答'；
      2. 但前端界面上，scope 内没有任何单个 agent 的 state === 'waiting_user_answer'（worker 是 waiting_controller_answer，主控是 idle），因此 waiting ===
      0；
      3. item.issues_waiting 未在 sidebarSnapshot 的 project 对象中填充（为 undefined）；
      4. 而包含了 '等待用户回答' 的 <span className="sr-only project-state"> 具有 sr-only 样式（绝对定位宽高 1px 且隐藏，仅供读屏软件读取）。
      结果：对于视觉用户，此时项目行仅显示项目名和数字，没有任何“等你”、“等你回答”文案。Ticket 验收要求“主控等用户时项目行写等你回答”，测试仅断言了 DOM
      属性 data-project-state，掩盖了视觉文案缺失。

  ──────
  ### 发现 3 [P2 验证缺陷] 缺少 Checks 9、10、11 在修前版本的独立红态与变异体证据

  • 位置：test_t133_t107_terminal_controller_e2e.py:65、#L187-L216
  • 分析：
  新加入的 4 个断言：
      • Check 8: controller_pane_header_matches_row
      • Check 9: worker_pane_header_matches_row_without_second_state
      • Check 10: project_waits_on_user_when_no_controller_in_turn
      • Check 11: ended_row_time_says_ended
      在 --revision 8f36d6495 运行时，由于单脚本顺序执行，在 Check 8 即抛出 AssertionError 终止，导致 Check 9、10、11 从未在修前代码上运行过。同时脚本 --
      ￺mutant 参数仅保留了旧票的 4 种变异体，未为 9/10/11 提供任何变异验证。

  ──────
  ## 五、审查结论

  开发者诚实记录了未解的真实运行诱因并主动将状态定为 INCOMPLETE。本次审查确认：

  1. 核心状态一致性收敛方向正确，删除了平行 API；
  2. 但引入了独立终端状态恒为“未知”的回归缺陷（P1）；
  3. 且存在项目行可见文案未达验收（P2）以及部分验收项红态证据链缺失（P2）；
  4. 真实运行中的钩子丢失问题需要开专门 ticket 跟踪。

  T-176 REVIEW INCOMPLETE

