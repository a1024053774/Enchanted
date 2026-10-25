   T-179（L06：worker 窗格门禁回执可读化）独立审查报告

  本审查以只读方式对候选交付（commit 909344c60，相对起点 main 的 full.diff）、ticket
  T-179-readable-gate-receipt.md、运行证据与 RESULTS.md 完成核验。
  ──────
  ## 一、审查结论概要

  • 根因定位与最小改动：根因找对。问题出在 daemon.ts:121-125 的 feedbackText 无差别将 relay_results 的完整 JSON
  注入 worker 终端窗格；修复在调度与渲染层，以独立轻量模块 receiptLines
  生成摘要，且在记录页新增只读展示区，未引入多余包装或平行架构。
  • 门禁语义保持：完全未改变门禁核心逻辑与存储契约。完整回执依然完整写入 SQLite 的
  relay_results；执行主控收到的回执保持原样 JSON 格式不变；重放检查依然有效；拒绝路径和非 submit 场景处理准确。
  • 项目过滤与安全边界：relay_receipts 查询按项目任务 ID 规范契约（<project>+
  <task_name>）带加号匹配前缀，不会发生跨项目串扰；该命令登记在 readOnly 集合中且仅执行只读
  SELECT，权限无越权写风险。
  • 数据独立性：记录页将“用户输入记录”（user_inputs）与“门禁回执”（relay_requests /
  relay_results）在存储表、查询 IPC、渲染组件上完全彻底分开，端到端测试亦证明互不干扰。
  • 证据与变异有效性：测试期望严格推导自
  ticket；修前版本在缺陷断言上呈真实红态；两个变异（去提交号、去全文）分别精准击中特定断言并被拒绝；setup-error
  如实记录保留。
  ──────
  ## 二、逐项核对详情

  ### 1. 门禁语义与非 submit 回执核对

  • 回执写库不变：relay.ts:105-157 中 relay_requests 和 relay_results
  的入库事务和触发器保护原样保留，存储的仍是完整未经裁剪的门禁返回 JSON。
  • 主控回执不变：daemon.ts:121-125 判断 role === 'worker' 才给摘要；当会话为 controller 时，依然下发
  "本回合的异步请求处理结果如下……\n" + JSON.stringify(receipts, null, 2)，保障主控机械化读取字段。
  • 重放处理正确：daemon.ts:833 的 !receipt.replayed
  判断不变，重放的请求不会在窗格中重复调度反馈；而在记录页查询历史回执时，通过已记录的 key 查回并完整展示。
  • 非 submit 回执与拒绝场景：receiptLines 对不同分支覆盖完整：
      • 拒绝（!result.ok）：输出 ${name}：门禁没有受理（${result?.error ?? '原因未知'}） 及
      下一步：结束本回合；要改什么由门禁或主控另行说明。（2 行）。
      • 查状态（status）：输出 查状态：门禁已受理、任务 ... · <状态> · 候选提交 ... 及 下一步：结束本回合。（3
      行）。
      • 上报问题（issue）：输出 上报问题：门禁已受理、问题编号 #${result.number} 及 下一步：结束本回合。（3
      行）。
      • 审查员结论（review_submit）：窗格不下发（非 worker/controller 角色），记录页中展示为
      提交审查结论：门禁已受理 及验收通过摘要与完整 JSON。


  ### 2. relay_receipts 项目过滤与权限核对

  • 项目过滤不会混淆：
  在 daemon.ts:429：
    return { ok: true, receipts: rows.filter(row => String(row.task).startsWith(input.project + '+')).map(row =>
    ...
  在 a2a 系统中，任务 ID 格式严格约束为 <project>+<task_name>。过滤表达式使用 input.project + '+'
  作为前缀，尾部的 + 强分隔符保证了项目名为 demo 的过滤串 demo+ 绝不会误匹配到项目名为 demo2 的任务 demo2+T-1。
  • 权限与只读性：
  在 daemon.ts:172，relay_receipts 登记在 readOnly 集合中。底层数据库操作仅为单条 SQL SELECT
  联查，无任何数据写入、无状态修改，符合只读命令要求。

  ### 3. 记录页独立性核对

  • 数据源隔离：
      • “用户输入记录”读取 userInputRecords.ts，只从 user_inputs 追加表读取用户亲手的输入、审批及介入事件。
      • “门禁回执”读取 relay_receipts，只从 relay_requests 与 relay_results 获取。
  • 前端结构隔离：
  在 RecordsPage.tsx:97，回执区域被封装为独立的 Receipts 组件，作为单独的 <section className="receipts" aria-
  label="门禁回执"> 挂载在表格下方，并带有独立的加载中、空状态和错误告警提示。
  • 测试双重隔离验证：
  端到端测试 test_t179_receipt_summary_e2e.py:378 断言 receipts_not_user_input 明确核对 user_input_records
  接口返回的数据中没有任何回执注入，证明两表与两个接口完全没有数据污染。

  ### 4. 测试期望来源、红态与变异断言核对

  • 期望值独立性：测试脚本 test_t179_receipt_summary_e2e.py 文档与断言完全对照 ticket T-179 的两项
  Acceptance（窗格几行摘要、记录页可查全文、门禁流程不受影响）以及 L06 的缺陷描述，非抄袭产品实现。
  • 修前红态落点真实：
  在 red-main-01/summary.json 中，修前代码在 10 项检查中失败 6
  项（worker_receipt_not_raw_json、worker_receipt_has_state_commit_next、worker_receipt_few_lines、pane_shows_no
  _raw_receipt、records_page_lists_submit_receipt、records_page_full_receipt_matches_store），全部落在本票修复的
  缺陷断言上，而 gate_flow_unchanged（门禁主流程）与 full_receipt_in_store 等无关项通过，证实红态真实有效。
  • 双变异检查有效：
      • no-commit（摘要隐藏提交短号）：仅 worker_receipt_has_state_commit_next 失败，其余 9
      项通过，变异被有效拒绝。
      • no-full-text（记录页折叠详情置空）：仅 records_page_full_receipt_matches_store 失败，其余 9
      项通过，变异被有效拒绝。
  • setup-error 如实记录：
  setup-error-01 中保留了 green-01-integrate-before-review-
  reclaimed（测试在审查会话未回收完成前发送集成，触发门禁 operation_busy，后优化测试等待 review_reclaimed
  事件）与 regression-ts-01-needs-driver-args（旧单元测试缺参数退出），现场日志完整保留，未被隐瞒。

  ### 5. 质量准则与代码异味检查

  • 无吞异常：daemon.ts:426、main.ts:60 等处参数非法或内部错误均直接抛出 Refusal 或
  Error，前端在错误时展示对应的错误条，无空 catch 吞没异常。
  • 无 fallback 与兼容分支：未添加任何兜底重试机制或双写逻辑，未留弃用接口垫片。
  • 文案与修改边界：
  文案朴素清晰，无营销腔调；改动全部位于 workbench/ 内部 8 个必要文件内，未越出修改范围。
  ──────
  ## 三、审查发现列表（Findings）

  经对实现代码、全量 diff 及运行证据的严格审查，未发现 P0、P1 或 P2 级别阻碍性缺陷。

  记录 1 处低优先级建议（P3 / 代码可维护性）：

  ### [P3] gateReceipts.ts:15：多指令单回合拼接摘要时的行分隔排版

  • 文件与行号：gateReceipts.ts:15 / daemon.ts:124
  • 场景描述：如果 worker 在极罕见的单回合中连续发起了多个请求（例如先 status 再 submit），daemon.ts:124 使用
  join("\n") 将两个回执摘要行直接连续拼接。此时前一回执的末行（下一步：...）与后一回执的首行（...
  ：门禁已受理）之间无空行分隔。
  • 影响评估：受管 worker 正常生命周期在一个回合内只显式调用一次
  submit，该场景极少出现且不影响语义理解，建议后续批次如有多请求场景可改为 join("\n\n")。
  ──────
  T-179 REVIEW PASS
