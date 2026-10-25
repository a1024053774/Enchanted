   Enchanted (a2a) T-177 独立审查报告

  审查对象：T-177 候选交付（commit afa2e830b）
  关联工单：T-177-sidebar-cleanup.md（来源 findings/2026-10-25-lcu-real-use.md L04）
  审查基准：相对起点 main 的 full.diff、运行证据 RESULTS.md 与测试摘要。
  ──────
  ### 一、重点核对项结论

  #### 1. “历史”判定逻辑与父子会话处理

  • 判定依据：只依据会话状态（state === 'ended'）与门禁当前 attempt（current !== undefined && current.attempt !== record.attempt），见 sidebar.ts:175-187。
  • 当前会话与在任主控：当前 attempt 的非结束会话 superseded 为 false 且 state !== 'ended'，不会被折入历史；在任主控（task: null, attempt:
  null）生命周期处于运行/空闲态时，history 严格为 false，不会被折入历史（在 test_t177_sidebar_history_e2e.py:510-511 中由 controller_not_history
  断言证明）。
  • 子会话活跃时父会话的处理：在 sidebar.ts:241-248 构建树形视图时，计算 history: agent.history && children.every(child => child.
  history)。只要有任何一个子会话尚未进入历史（仍在运行/使用），即使父会话自身已结束，其 history 也会保持为 false
  停留在主视图中，确保当前活跃的子会话不会随父会话被折叠隐藏。

  #### 2. sidebar_hide 语义与权限

  • 状态限制：在 daemon.ts:206-214 中，强制核验 rows.every(row => row?.state === 'ended')。若包含仍在运行的会话或不存在的会话，立即抛出
  Refusal('session_not_ended')。变异测试 hide-live 证明去掉此项检查会被端到端断言拦截。
  • 纯追加事件，不删记录：通过 store.event('sidebar_hidden', { launches: input.launches }) 追加事件，未触发任何 SQLite 删除/更新操作，不修改 launch_records
  表，不修改门禁事件（test_t177_sidebar_history_e2e.py:544-551 验证清理前后 launch_records 数量与门禁事件数保持不变，launch_show 仍可正常读取）。
  • 权限边界：严格检查 if (authority.kind !== 'operator') throw new
  Refusal('operator_required')，只有操作员凭据（桌面主进程）可调用，项目终端与未授权来源无权调用。

  #### 3. 回收入口与门禁一致性

  • 真实经门禁 reclaim：前端点击“回收”经 IPC 调起 main.ts:10-15，向后台发送 { command: 'reclaim', task, attempt }；后台透传给门禁 gates.
  call，在门禁事件流水中真实触发 reclaimed 事件（test_t177_sidebar_history_e2e.py:525-529 验证捕获到了门禁事件）。
  • 对象范围限制：sidebar.ts:177 判定 reclaimable = record.role === 'worker' && state === 'idle' && Boolean(current?.integrated) && current!.attempt ===
  record.attempt。仅针对已集成任务的当前 attempt 且仍处于 idle 的 worker 开放；集成完成后不会自动关闭 worker，必须由用户/主控显式回收。

  #### 4. 启动默认选择（startupView）

  • 绝不选中已结束终端：main.ts:40-45 过滤 !row.history && !['ended', 'unrestored'].includes(row.state)，并在按 active_at
  降序排序后选取首个活跃项。若无任何活跃会话，则回退到首个项目概览页（空窗格）或空选择。
  • 读取失败行为：if (!catalog.ok) throw new Error(catalog.error)，直接抛出异常中断窗口创建，不吞异常，不做降级猜想。
  • 显式启动入参无影响：main.ts:779 显式判断 if (options.task === undefined && options.project === undefined && options.launch ===
  undefined)，当外部传入任务/项目/会话时完全跳过 startupView，原有指定启动链路完全不变。
  ──────
  ### 二、五项原则逐项核对

  #### 1. 根因与最小改动层

  • 根因确认：准确。原侧栏平铺所有历史 launch 且缺乏隐藏入口；门禁集成时不自动关 worker
  且界面缺乏触发回收的途径；无显式启动参数时误恢复了保存布局中已退出的普通终端。
  • 改动层级：完全落在根因层：
      • 数据模型层（sidebar.ts）计算 history、reclaimable、active_at，过滤 hidden。
      • 编排控制层（daemon.ts）新增 sidebar_hide 命令。
      • 主进程启动调度（main.ts）新增 startupView 及 IPC 管道。
      • 视图层（renderer.tsx、style.css）展示历史折叠区、清理与回收入口。
  • 无吞异常 / fallback / 重试 / 兼容分支 / 平行 API：
      • 各 IPC handler 及内部查询在 !result.ok 时均直接 throw。
      • sidebar_hide 校验严格抛 Refusal。
      • 未引入双写或中间包装层。


  #### 2. 真实入口证据与期望值独立性

  • 真实入口证据：测试脚本 test_t177_sidebar_history_e2e.py 真实拉起 Electron 实例（DevTools 协议控制）、a2a 守护进程、SQLite 状态库、门禁系统及脚本化模型
  worker/reviewer，全链路验证侧栏折叠、展开、回收、清理及应用重启流程。
  • 期望值独立性：期望值依据工单场景手动推演（T-1 经历 a1、a2 作废回收与 a3 交付集成，预期历史 3 个；T-2 经历 a1 作废与 a2 空闲，预期历史 1 个；回收后 T-1
  历史变为 4 个；启动默认选中未结束的最新活跃 worker），断言全部按场景预先定义，而非取自实现产物的输出。

  #### 3. 红态落在缺陷断言与变异拒绝

  • 修前红态落点：summary.json 在基线 main 上运行，准确失败在 13 项核心缺陷断言（7
  个会话平铺未折叠、无回收入口、无清理入口、重启后选中已结束家目录终端等）。
  • 变异拒绝：
      • history-too-wide（将当前 attempt 会话也误折入历史）：被 summary.json 的 6 项断言准确拦截。
      • hide-live（允许清理仍处于运行/空闲态的活跃会话）：被 summary.json 的 live_session_cannot_be_hidden 断言准确拦截。


  #### 4. 修改边界与文案质量

  • 修改边界：变更仅涉及 workbench/ 目录下的 7 个相关文件，无越界修改。
  • 文案质量：
      • 折叠按钮：历史 {past.length} 个
      • 清理按钮：清理，hover 说明为 把已结束的会话从列表里拿掉；记录和门禁事件都保留
      • 回收按钮：回收，hover 说明为 任务已集成，这个 worker 还空着。经门禁回收：停止并归档这个会话。
      • 项目计数说明：不含折进“历史”的会话
      文案朴实直白，操作含义与边界说明清晰，无任何 AI 或营销腔调。


  #### 5. 正确性与回归风险

  • 回归测试覆盖：
      • test_t133_t107_terminal_controller_e2e.py（含 T-176 侧栏状态检查）PASS。
      • test_t171_superseded_issue_e2e.py PASS。
      • test_t174_silent_cli_hint_e2e.py PASS。
  • 无新增回归风险：会话折叠及清理只影响侧栏投影展示（sidebarSnapshot），未变动底层 launch_records、编排事件和门禁状态机。
  ──────
  ### 三、审查发现明细（Findings）

  本次审查未发现 P0、P1、P2 级缺陷。

  • 发现 1（P3 - 观察项）
      • 文件与行号：main.ts:40-41、sidebar.ts:136-137
      • 严重度：P3
      • 场景描述：active_at 取自 orchestration_events 中该会话的最大事件时间戳（如 turn、input、dispatch 等）。对于无额外编排事件交互的纯项目 PTY
      终端，其活跃时间为启动时间 created_at，终端内部单纯的终端打字和输出未触发编排事件时不更新 active_at。该限制已在 RESULTS.md
      中如实记录，符合当前仅利用既有编排事实的架构设计，无阻断影响。

  ──────
  T-177 REVIEW PASS

