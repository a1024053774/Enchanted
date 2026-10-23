# T-144 独立审查 01（agy）

- 审查员：agy 1.4.6，模型 gemini-3.8-flash-high，Herdr 可见窗格 wG:pM，交互 auto 模式（只用读文件工具），只读副本，候选 9eb9a4c5f。
- 启动 argv：

```
agy --model gemini-3.8-flash-high --mode auto --add-dir /Users/luckye/Documents/Code/a2a-review/T-144-r1 -i "$(cat /Users/luckye/Documents/Code/a2a-review/T-144-r1/prompt.txt)"
# pane wG:pM started 2026-10-23T14:27:03Z
```

- 审查后核对：候选副本 git status 0 行改动。结论 PASS，一条 P3（审查副本继承稀疏检出，读不到候选内 batch23 证据；执行主控此后在审查副本里展开本批目录）。

## 窗格中的报告原文

```text

○ Thought for 6m 32s (The agent's configuration uses a s...)
● Explored 79 files (card.md, T-144-f...) (ctrl+o to expand)

▸ Thought for 32s, 4.2k tokens

   T-144 独立审查报告

  作为 a2a 项目的只读独立审查员，我对任务 T-144
  候选提交（9eb9a4c5f，相对起点
  6af6e3028）进行了完整审查与核对。材料包括代码变更
  full.diff、任务卡
  card.md、用户裁定与授权文件、沙箱外两轮执行证据
  outside-20261023T141754Z-U3kdek 与
  outside-02-20261023T142626Z-bmaYji，以及 worker 提交说明
  RESULTS.md。
  ──────
  ## 1. Ticket 四项需求实现与归属逻辑核对

  根据 ticket T-144-flow-page-fixes.md
  的用户原话与验收要求逐项核对：

  ### 1.1 卡片标题改为角色与任务名，UUID 仅在悬停提示

  • 在 FlowPage.tsx:11-18 的 Agents
  组件中，卡片标题由原来的 <strong>{agent.id}</strong>
  改为：
    <strong>{agent.role_label ?? agent.role}{agent.
  task_name && ` · ${agent.task_name}`}</strong>
  泳道内的 worker 与主控会附加任务名（如 worker · T-left-.
  ..、执行主控 · T-left-...），未归属主控显示为 执行主控。
  • UUID（agent.id）移至容器标签的 title 悬停提示中：
    title={`${agent.id}${agent.attempt ? ` · attempt
  ${agent.attempt}` : ''}`}

  • 真实 Electron 测试 test_t144_flow_page_e2e.py:308-310
  通过正则表达式 uuid_pattern 检查了全部 DOM
  节点的可见文本，确认 UUID 绝不出现在正文中，且存在于
  title 提示内。

  ### 1.2 执行主控按派发关系归属泳道与“确实无关联”判定依据

  • 判定依据：在 flow.ts:44-48 的 projectFlow 中：
    const controllers = agents.filter(agent => agent.
  project === task.project_id && agent.role ===
  'controller' &&
      agent.preset === 'executor' && bound.some(child =>
  child.role === 'worker' && child.parent === agent.id));
  归属依据是当前 attempt 中当前任务 worker 的认证父
  launch（child.parent === agent.
  id，由门禁派发记录确立并由 sidebarSnapshot
  核实），绝非读取终端窗格文字、主控终端启动时的 task
  字段或任何名称启发式。
  • 确实无关联判定与原因文字：
  未关联到任何任务当前 attempt 派发 worker 的主控进入
  unassigned，并在 flow.ts:58-62 中生成明确原因：
    unassigned_reason: agent.role === 'controller'
      ? agent.preset === 'executor' ? '没有关联到当前任务
  attempt 的派发 worker' :
  '构思主控属于项目，不归属任务阶段'
      : !tasks.some(task => task.task_id === agent.task &&
  task.project_id === agent.project) ?
  '项目或任务无法对应'
      : !agent.parent ? '缺少已核实的父会话关系' :
  '无法对应任务的当前 attempt 或阶段角色'
  在 FlowPage.tsx:16 中通过 <small className="flow-
  unassigned-reason">{agent.unassigned_reason}</small>
  在卡片下方渲染。真实 Electron 的 DOM
  数据（green.json:533-541）确认文字正常显示。

  ### 1.3 不同任务泳道互相独立

  • 各任务在 projectFlow
  的映射中独立计算本泳道成员，只有派发了本任务 worker
  的主控才进入本泳道，另一任务的主控绝不进入本泳道，已归属
  的主控统一进入 assigned 集合，不再掉入未归属。
  • 测试 test_t144_flow_page_e2e.py:301-302
  严格断言了两个任务泳道的成员隔离：{a['id'] for a in
  lane['agents']} == {controller['launch'],
  worker}，并通过了验证。

  ### 1.4 一个任务多路径（额外目录）展示

  • 在 flow.ts:50-52 中：
    const project = projects.find(project => project.
  project_id === task.project_id);
    const paths = [...new Set<string>([project?.repo ??
  task.repo, ...(project?.extra_directories ?? [])]
      .filter((path): path is string => typeof path ===
  'string' && path.length > 0))];
  泳道结构中包含主目录和 T-140 的所有 extra_directories。
  • 在 FlowPage.tsx:31 中通过 <ul className="flow-paths"
  aria-label="任务路径"> 逐行显示，未合为一个；在样式
  flow.css:10-11 中设有独立排版支持。
  ──────
  ## 2. 受保护文件改动与授权范围核对

  根据用户裁定
  A（20261023T142024Z-ideation-answer-001.md）与任务卡规定
  进行比对：

  1. 改动文件与行号精准受控：
      • test_t111_flow.mjs:36：将泳道成员期望 ['w1','w2',
      'ended'] 调整为 ['controller','w1','w2','ended']。
      • test_t111_flow.mjs:41：将未归属期望 ['controller',
      'old','orphan'] 调整为 ['old','orphan']。
      • test_t146_ended_projection.mjs:65：将查找已结束
      terminal 的位置由 flow.unassigned 改为 flow.
      lanes[0].agents，期望状态仍严格为 'ended'。
  2. 其余检查点零改动：
      •
      上述两文件的其余断言、检查名称、上下文冻结核对均未发
      生任何改动。
      •
      任务卡中的验收文件（oracle_paths：workbench/tests/te
      st_t146_session_state_e2e.
      py、workbench/tests/test_t137_reflect_e2e.
      py）未被触碰。
  3. RESULTS.md:36-44 逐条陈述：
      • 表格形式逐一列出 3 行改动、旧期望、新期望与裁定 A
      依据。

  ──────
  ## 3. 状态来源与裁定 B 一致性核对

  1. 单一状态来源：
      • flowSnapshot 先读取 sidebarSnapshot 获取 sidebar.
      agents，然后直接输入给 projectFlow。
      • 流程页不自行计算或推断 agent
      状态，完全透传侧栏给出的状态及状态文字（state、state
      _label）。
  2. 已结束会话按裁定 B 列出：
      • 即使 worker
      或主控已结束，仍按派发关系在泳道中展示，并标有“已结
      束”与图标 ✓。
      • 回归测试 t146（真实 Electron e2e 47 项检查，见
      t146.json:2）与 t137（Reflect e2e，见
      t137.json:2）保持全绿，确认与侧栏、Reflect
      页面行为统一。

  ──────
  ## 4. 新测试独立性、红态与变异有效性核对

  1. 测试独立性：
      • 新测试 test_t144_flow_page_e2e.py
      构造跨项目真实夹具与真实 Claude CLI
      交付流程，采用黑盒形式通过 Electron CDP 操作真实 DOM
      界面取证，断言直接来自需求定义，未预设或回读实现内部
      变量。
      • 聚焦投影测试 test_t144_flow_projection.mjs
      独立构造输入，验证了纯函数只读性与边界场景（过期
      attempt、跨项目混淆、缺少父会话等）。
  2. 红态验证：
      • 在起点提交 6af6e3028 上运行
      test_t144_flow_page_e2e.py，在 red.json:12-57
      中精准失败在标题
      UUID、主控未归属、未归属无原因、缺少路径 4
      项业务断言上。
      • 改后受保护断言在起点源码上分别精准拒绝在第 36
      行与第 65
      行（t111-base.json:5-7、t146-ended-base.json:130-133
      ）。
  3. 变异拒绝：
      • 变异 uuid-title（恢复标题为 UUID）：在
      uuid-title.json:22-28 中精准被
      worker_title、controller_title 和
      uuid_only_in_tooltip
      断言拦截，成员隔离断言依然通过。
      • 变异 terminal-task（退回使用 agent.task 判定）：在
      terminal-task.json:14-32 中精准被
      isolated_members、controller_title 和
      only_unrelated_controller_unassigned 拦截。
  4. 断言与超时：
      •
      断言均为严格等值判定，未放宽任何期望值；超时保持夹具
      标准（Claude 交付 180s、DOM 渲染
      30s），未增加不合理延迟。

  ──────
  ## 5. 修改边界、代码健康与正确性审查

  1. 修改边界检查：
      • workbench/src/gates/** 与 daemon.ts 零修改。
      • .project-map/**、AGENTS.md、CONTEXT.md 零修改。
  2. 代码健康：
      • 核心改动仅 8 处文件，无任何吞异常的空 catch 块。
      • 无推测性抽象、fallback 垫片或平行双写路径。
      • projectFlow 保持纯函数且入参只读，FlowPage
      无状态泄露或内存泄漏隐患。

  ──────
  ## 6. 审查发现与观察事项清单（Findings）

  ### 发现 1：审阅副本 candidate/ 受 Git sparse-checkout
  规则限制未展开 batch23 证据目录

  • 文件与行号：sparse-checkout:1-4
  • 严重度：P3（审阅环境配置细节 / 无功能损害）
  • 场景描述：在审查工作区 candidate/
  目录下，candidate/evidence/2026-10-23-batch23/T-
  144/RESULTS.md 读取报文件不存在。经核查 worktree
  配置发现，评审底座 candidate7 配置了 sparse-
  checkout，仅放行了历史 batch16 与 batch17，未包含
  batch23。
  • 核实事实：Worker 分支 exec/t144 上的提交 9eb9a4c5f
  已经完整提交了 RESULTS.md 与两轮运行脚本；且审阅根目录
  evidence/ 下已提供沙箱外运行的完整结果证据。代码库集成时
  git merge 会正常合并，不影响功能与主线代码。
  ──────
  ## 7. 综合审查结论

  T-144 候选提交 9eb9a4c5f 完整、准确地实现了 ticket
  的全部四项要求，判定主控归属严格基于派发事实而非启发式，
  受保护文件的修改完全在用户裁定 A
  的授权边界之内，未改动任何未授权断言或 oracle
  验收文件；状态流沿用 T-146 结构化状态与裁定
  B；新增测试独立完整，红态与两个变异精准命中缺陷，第二轮
  真实 Electron 与合同复验全数通过。

  T-144 REVIEW PASS
```
