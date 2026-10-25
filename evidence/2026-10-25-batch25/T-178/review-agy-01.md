   T-178（L05：流程页项目范围与标题去重）独立审查报告

  作为 Enchanted（a2a）项目的独立审查员，我对候选提交 8bd6de2a1（工作区：/Users/luckye/Documents/Code/a2a-review/T-178-r1/candidate/，相对 main 改动见
  full.diff）进行了只读独立审查。
  ──────
  ## 一、审查结论与裁定

  • 综合裁定：INCOMPLETE
  • 核心判定依据：
      1. 代码修复与逻辑设计：完全达标（PASS）。根因定位准确，改动严格位于最小根因展示层；无吞异常、无 fallback、无重试、无兼容分支或平行
      API；其他项目的泳道与会话完整保留在折叠区域未丢失；未选项目时行为完全向后兼容；标题去重条件严谨，不会误吞真实标题。
      2. 测试与变异杀灭：完全达标（PASS）。真实 Electron 端到端验收脚本在基线 main 上准确触发 4 项缺陷断言红态；no-scope 与 title-repeated
      两个坏实现变异分别被对应的作用域与标题断言准确拒绝；T-144 回归全部 11 项通过，全程 0 次模型调用。
      3. 交付证据归档完整性：未完全落地（INCOMPLETE）。虽然测试在本地运行通过，但 RESULTS.md 承诺归档的 3 张截图（声明位于 shots/）以及 T-144
      首次回归失败的现场（声明保留在 setup-error-01/），在候选交付目录中均为空目录，实际文件遗留在执行机 /private/tmp/
      临时目录下未提交入库。依照项目规范“不将不完整结果四舍五入为 PASS”，本次审查结论判定为 INCOMPLETE，待证据补全后即可放行。

  ──────
  ## 二、逐项核对详情

  ### 1. 根因分析与最小改动层

  • 根因确认：准确。
      1. FlowPage 原实现未接收当前项目上下文，从后台取得的全量任务按任务号字典序平铺，导致 a2a+T-138 在未集成状态下排在 demo 项目前面并默认展开；
      2. 门禁在创建任务时若未传标题，按契约默认记为 title: args.title ?? taskName，而 Lane 无条件拼接 {lane.name} · {lane.
      title}，导致未起标题的任务显示为“T-1 · T-1”。
  • 最小根因层：改动完全收敛在前端表现层，仅修改了 3 个生产文件（共 37 行增改）：
      • FlowPage.tsx:10-95：按当前项目将泳道与未归属会话分为“当前项目”与“其他项目”，后者收进独立折叠区；标题在全等时省略拼接；
      • renderer.tsx:960：将 selectedProject 传入 FlowPage，并以 key={selectedProject ?? ''} 实现换项目时安全卸载重挂；
      • flow.css:71-75：折叠按钮样式。
  • 结构完整性：经全文审查，无任何 try/catch 吞异常、无 fallback 兜底备用分支、无静默重试、无历史兼容分支，亦未添加平行 API。

  ### 2. 其它项目泳道/会话保留与未选项目行为

  • 其它项目泳道与会话：
      • snapshot.lanes 中非当前项目的任务通过 others 过滤，渲染在 <div id="flow-others-lanes" hidden={!othersOpen}> 的 .flow-scroll 内；
      • snapshot.unassigned 中非当前项目的会话通过 othersUnassigned 过滤，渲染在折叠区域内的 <section className="flow-unassigned" aria-
      label="其他项目未归属"> 中；
      • 折叠按钮初始 aria-expanded={false}，点击切换展开。其它项目的泳道和未归属会话完整可见，绝无丢失。
  • 未选项目时的行为：
      • 当处于独立终端区（project === null）时，const mine = (item) => project === null || item.project === project 恒返回 true；
      • 此时 lanes 包含全部泳道，others 为空；unassigned 包含全部未归属会话，othersUnassigned 为空；
      • (others.length > 0 || othersUnassigned.length > 0) 恒为 false，不展示折叠区；空状态展示原通用提示
      '还没有任务票。注册任务后，流程会显示在这里。'。行为与修前完全一致，平铺展示全部内容。


  ### 3. 标题去重条件与真实标题安全性

  • 去重逻辑：FlowPage.tsx:28
  {lane.name}{lane.title && lane.title !== lane.name &&  · ${lane.title}}
  • 场景覆盖：
      • 任务未设标题（门禁填充为任务名）：title === name，条件不成立，只显示 T-1，成功消除“T-1 · T-1”；
      • 任务设有真实标题：title !== name，条件成立，显示 T-2 · 导出 CSV，真实标题完整保留；
      • 真实标题包含任务名子串（如 T-1 导出 CSV）：全等比较依然为 true，显示 T-1 · T-1 导出 CSV，绝不会被误吞；
      • 仅在用户显式将标题命名为与任务号完全一致的字面量时才省略后缀，符合去重语义。


  ### 4. 验收真实入口、期望值独立性与模型消耗

  • 真实入口：test_t178_flow_project_scope_e2e.py 真实拉起 Electron 实例、后台守护进程、真实 Git 仓库与两个项目主控（a2a 任务 T-138、demo 任务 T-1 与 T-
  2），严格重现了 L05 的多项目现场。
  • 期望值来源：直接源自 Ticket T-178-flow-page-project-scope.md 的验收条件（“在 demo
  项目下打开流程页，置顶是本项目任务；标题不重复”），断言核验项目顶置、折叠状态、标题不重复、展开可见与切项目响应，无任何自证哈希或抄产品输出。
  • 模型额度保护：测试不派发 worker，fixture.api.main === 0，全过程零模型调用，符合用户 Claude 额度受限时的原则。

  ### 5. 红态验证与变异杀灭

  • 修前红态（red-main-01）：在基线 main 上运行，准确挂在 4 项缺陷断言：
      1. demo_lanes_first_and_only_in_view（a2a+T-138 错误排在第一）；
      2. other_project_folded（缺少折叠分组）；
      3. title_not_repeated（出现 T-138 · T-138 和 T-1 · T-1）；
      4. a2a_lanes_first_after_switch（切换项目后无法正确顶置）。
  • 变异 1（no-scope）：将 mine 条件常设为 true，模拟全量平铺的坏实现，在 mutant-no-scope-01 与 02 中均准确被 3 项作用域断言拒绝。
  • 变异 2（title-repeated）：恢复原拼接逻辑，在 mutant-title-repeated-01 中准确被 title_not_repeated 断言拒绝。

  ### 6. T-144 回归与失败记录合理性

  • 事故与归因：T-178 首版实现过滤 unassigned 时直接丢弃了非本项目的未归属会话，导致包含 unrelated 项目独立主控的旧验收用例 test_t144
  因页面缺失会话而超时失败。
  • 处理方式：开发人员没有修改测试降低标准，而是在生产代码中补全了 othersUnassigned 分组折叠机制，随后再次回归 regression-t144-02 取得 11/11 全项 PASS。
  • 记录如实度：RESULTS.md:30 如实记录了该失败原因及整改过程，处理完全合理。
  ──────
  ## 三、审查发现明细（Findings）

  ### 发现 1（P2 - 交付证据缺陷：RESULTS 声明的截图目录实际为空）

  • 文件与行号：RESULTS.md:34 与 test_t178_flow_project_scope_e2e.py:220, 234, 240
  • 严重度：P2
  • 失败场景：
  RESULTS.md 声称“截图：shots/（修前与修后：demo 下的流程页、展开其他项目、a2a 下的流程页）”。但在候选交付目录中，evidence/2026-10-25-batch25/T-178/shots/
  实际为一个空目录。
  根因是测试脚本将截图保存到了 fixture.out（临时目录 /private/tmp/t178-6rfy97pe/out/），测试结束后未复制归档到仓库 evidence/.../T-178/shots/
  中。临时目录随时可能被系统清理，导致验收截图证据丢失。

  ### 发现 2（P2 - 交付证据缺陷：RESULTS 声明的首次失败现场未提交）

  • 文件与行号：RESULTS.md:30
  • 严重度：P2
  • 失败场景：
  RESULTS.md 记录“第一次 INCOMPLETE：其他项目未归属的会话被直接过滤掉，页面少了 2 个会话（保留在 setup-error-01/）”。但核查发现候选目录中的 evidence/2026-
  10-25-batch25/T-178/setup-error-01/ 是一个空目录，未存入任何 summary.json、run
  日志或异常调用栈。这使得声称保留的失败证据现场处于缺失状态，违背了项目保留失败现场的治理要求。

  ### 发现 3（P3 - 测试验证盲区：展开其他项目截图未滚动到可视区域）

  • 文件与行号：test_t178_flow_project_scope_e2e.py:231-234
  • 严重度：P3
  • 失败场景：
  在 test_t178 中点击展开折叠按钮后，未将 #flow-others-lanes 滚动进入视口即调用 electron.screenshot()。由于 demo
  项目本身包含两条泳道及未归属会话，页面内容高度已超出 Electron 窗口视口（右侧出现滚动条），展开的“其他项目的任务”被挤在视口下方。这导致截获的 02-demo-
  flow-others-open.png 图像内容与 01-demo-flow.png 在视觉上完全一样，未能直观体现展开后的 UI 变化（依赖 DOM evaluate 断言通过）。建议在截图前执行
  scrollIntoView()。

  ### 发现 4（P3 - 边界文案瑕疵：仅有外项目未归属会话时的按钮文案歧义）

  • 文件与行号：FlowPage.tsx:87
  • 严重度：P3
  • 失败场景：
  若其它项目无任何泳道（others.length === 0）但存在未归属会话（othersUnassigned.length > 0）时，外层 section 会渲染折叠按钮，文案为固定格式“›
  其他项目的任务 0 张”。虽然展开后能正常看到“其他项目未归属”列表，但“0 张”的描述对用户有歧义。此点已在 RESULTS.md
  的“未验证事项”中主动交代，后续可将文案优化为考虑未归属会话的表述。
  ──────
  ## 四、整改放行建议

  1. 补齐证据文件：
      • 将当前临时目录（或从重跑产物）中的修前与修后截图（01-demo-flow.png、02-demo-flow-others-open.png、03-a2a-flow.png 及修前对应截图）复制放入
      evidence/2026-10-25-batch25/T-178/shots/；
      • 在 evidence/2026-10-25-batch25/T-178/setup-error-01/ 中补充首次回归失败时的 summary/日志，或若确实未保存文件，在 RESULTS.md
      中修正表述（说明当时仅保留了目录骨架、未保存 JSON，避免空头引用）；
  2. 测试微调（可选）：在 test_t178 截取 02 截图前增加 document.querySelector('#flow-others-lanes')?.scrollIntoView()，使视觉证据更直观。

  完成上述证据补归档后，可直接放行合并。
  ──────
  T-178 REVIEW INCOMPLETE
