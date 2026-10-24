# T-170 agy 独立审查报告（gemini-3.8-flash-high，Herdr wG:p2E，只读副本 aa2d7104a）

独立审查报告：原生 CLI 启动失败（launch_failed）导致 attempt 无法回收

  ## 1. 审查总览与结论

  作为 a2a 项目的只读独立审查员，依据 user-decision.md（构思主控转述用户授权：核对 B a2 现场并裁定，处置走门禁；被打回照常重派不限次数）及 AGENTS.md
  治理规则，对候选版本 aa2d7104a（相对于起点 7a7885f7d）的改动、ticket、端到端测试及归档证据进行了全面静态核验。

  审查结论：T-170 REVIEW PASS

  所有核心门禁语义、真实入口证据、红态复现、反例验证与回归测试均完整成立，改动严格位于最小根因层，无旁路、无吞异常、无重试、无兼容分支。

  ## 2. 根因与最小改动层核对

  ### 2.1 根因分析

  在 T-164 第三轮中，worker attempt a2 使用 Codex CLI 启动（launch 51773fcf-231c-471d-9bc1-ed8b26915a39）。Codex CLI 启动约 16 秒后退出 1（终端报错输出
  Error: account/read failed during TUI bootstrap: account/read failed: workspace routing discovery timed out (code -
  32603)），未能建立原生会话（native_session: null）。
  编排后台在窗格进程退出时检测到未建立原生会话，如实记录了 launch_failed（panes.ts:822-833），并使窗格进入 pane.failed 状态（panes.ts:1920-1921）：

    blocked: Boolean(pane.failed), ...(pane.failed ? { error: { providerPresent: !pane.stopped, activeTurn: pane.turn } } : {})

  在修前版本的门禁 core.ts 的 reclaim 方法中：

  1. 入口硬性断言 attempt.runtime_identity!.leader_pid !== null && attempt.runtime_identity!.native_session !== null。由于从未建连，native_session ===
  null，直接被抛出 identity_conflict 拒绝；
  2. 即使绕过上述断言，随后的 this.checkErrorReclaim(live) 与 requireGate(!live.blocked, "run_blocked", live) 又因为失败窗格标记了 blocked: true（且
  checkErrorReclaim 也要求 live.blocked === false）而必然拒绝。

  这导致从未建立会话即退出的 attempt 无法通过任何门禁路径回收，任务永久停留在 claimed 状态，工作区与分支无法清理，无法进行重新派发。

  ### 2.2 最小改动层与放宽条件判定

  改动仅修改了 core.ts:4246-4254 7 行代码：

    const neverStarted = attempt.runtime_identity!.native_session === null && live.runtime_identity.native_session === null &&
      live.stopped && !live.running && live.turn === null &&
      live.error?.providerPresent === false && live.error.activeTurn === null;
    requireGate(attempt.runtime_identity!.leader_pid !== null && (attempt.runtime_identity!.native_session !== null || neverStarted),
      "identity_conflict", { attempt, live });
    if (!neverStarted) {
      this.checkErrorReclaim(live);
      requireGate(!live.blocked, "run_blocked", live);
    }
    requireGate(!live.running, "worker_working");

  • 放宽条件的边界约束：
  neverStarted 严格绑定了 7 个物理事实：
      1. attempt.runtime_identity!.native_session === null（登记记录无会话）
      2. live.runtime_identity.native_session === null（实时读数无会话）
      3. live.stopped（进程已退出）
      4. !live.running（窗格未在运行中）
      5. live.turn === null（无活动回合）
      6. live.error?.providerPresent === false（错误读数中 provider 确认已不在）
      7. live.error.activeTurn === null（无进行中回合）
  • 是否会误回收活进程或有会话的 attempt：
      • 若 CLI 进程存活（如卡住未退出），live.stopped 为 false、live.running 为 true，neverStarted 必为 false，且入口断言与 worker_working 断言均会拒绝；
      • 若曾建立过原生会话（native_session 不为 null），neverStarted 必为 false，照常执行完整的会话门禁检查；
      • 若有未结算的 turn，neverStarted 必为 false。
  • 确认语义保留：
  neverStarted 仅放宽了对会话存在与失败窗格 blocked 标识的检查，随后的停机确认（stopThread -> stopped.stopped）、归档确认（archiveThread -> archived.
  archived && archived.stopped）和工作区清理（cleanupAttempt -> 检查 dirty worktree、保留 commit、删除 worktree）均逐一执行，没有任何绕过。
  • 架构纯洁性：
  改动未添加任何异常吞噬（try-catch 吞错）、fallback 分支、重试机制、兼容分支或平行 API，门禁仍为唯一回收入口。

  ## 3. Ticket 验收条件与真实入口证据核对

  核对 ticket T-170-reclaim-after-failed-launch.md 与运行证据 CHECKS.json：

   Ticket 验收项                           期望来源                     测试入口与机制                          证据结果
  ┼┼┼
   红态：修前，用真实后台/PTY 与重放 B   Ticket 规格与 T-164 B a2 缺陷现场  在修前基线 6412c5e08 下通过真实       red-1, red-2 均判定 red_reproduced:
   原始终端输出的 Codex 替身，复现         缺陷现场                       Socket、PTY 启动替身并触发               true，reclaimed.error ==
   reclaim 报                                                            reclaim（test_t170_failed_launch_recla  'identity_conflict'，failed:
   identity_conflict、任务不能再派发                                     im_e2e.py）                             ["reclaim_accepted",
                                                                                                                 "attempt_reclaimed",
                                                                                                                 "workspace_removed",
                                                                                                                 "task_dispatchable_again"]
   绿态：同一序列下 reclaim               Ticket 目标与门禁回收契约      修后代码同一序列运行，断言              green-1, green-2 均 PASS，failed: []
   受理，工作区移除，任务可再派发                                        reclaim.ok、after.current_attempt.recl
                                                                         aimed 或 cleared、not
                                                                         workspace.exists()、redispatch
                                                                         dispatch.ok
   反例：原生会话为空但 CLI 仍在运行时    Ticket 反例要求与历史门禁规范  --scenario hang 替身进程持续 sleep      hang-1: PASS（live_cli_not_reclaimed,
   reclaim 仍拒绝；T-158、T-146 回归不变                                 存活，测试调用 reclaim；并运行 T-       workspace_kept）；reg-t146-native:
                                                                         158、T-146 回归集                       PASS；reg-t146: PASS；reg-t158: PASS

  期望值均来自门禁契约定义与现场客观状态，未出现对照实现输出硬编码断言的情况。

  ## 4. 现场重放真实性与红态、反例核对

  ### 4.1 替身重放真实性

  在 test_t170_failed_launch_reclaim_e2e.py:65-78 中：

  • 替身使用编译型 C 程序（fake-codex.c -> cc -o fake-codex），以匹配生产环境下进程树能正确解析出 leader 二进制路径的机制（解释型脚本会导致进程名为 Python
  解释器而无法识别 leader_pid）；
  • 数据源读取 b-a2-pty.raw，核对该文件确实完整保留了现场原始 ANSI 转义序列、版本号 v0.164.0、工作区路径以及错误输出 Error: account/read failed during TUI
  bootstrap: account/read failed: workspace routing discovery timed out (code -32603)；
  • 替身重放启动画面后延时 3 秒，输出错误并退出 1，忠实重现了现场时序，没有迎合实现做任何裁剪。

  ### 4.2 红态与反例验证

  • 修前红态精准性：在 6412c5e08 上，reclaim 在入口处由于 attempt.runtime_identity!.native_session === null 触发 identity_conflict 报错，导致重派报
  already_claimed，断言严格落在缺陷本质上。
  • 反例有效性：--scenario hang 将退出阻断，替身维持运行，门禁拒绝了 reclaim（返回 ok: false），工作区得以完整保留，证明了放宽不会引起活进程被误回收。

  ## 5. 任务卡边界、证据治理与文案核对

  1. 修改边界：
      • 生产代码仅修改 core.ts；
      • 测试代码新增端到端测试 test_t170_failed_launch_reclaim_e2e.py；
      • 未碰触任何与 T-170 无关的模块或界面代码，未越出修改边界。
  2. 证据保存与合规性：
      • 保留了早期探索失败的夹具记录 runs-python-standin.archive.json并在 RESULTS.md 中如实说明（不粉饰干净历史，符合用户全局规则）；
      • 大体积运行现场按 T-088 策略归档至外置盘（runs.archive.json），本地仓库仅保留关键摘要与原始现场证据文件（pty.raw, CHECKS.json, RESULTS.md）。
  3. 文案风格：
      • 代码注释、文档与提交信息均为客观陈述，无任何宣传口吻或营销腔。


  ## 6. 审查发现清单（Findings）

  本次审查未发现 P0、P1 或 P2 级别阻断性缺陷。记录 2 项 P3 级别观察项：

  ### 发现 1（P3 - 说明性）：未针对 neverStarted 各布尔子项构造单项语句变异

  • 位置：core.ts:4246-4248
  • 严重度：P3
  • 场景说明：test_t170_failed_launch_reclaim_e2e.py 实现了 --scenario hang 反例证明活进程不会被回收，但未提供 --mutant 参数对 neverStarted
  条件内部各个独立谓词（例如故意去掉 live.turn === null 或 live.error.activeTurn === null）进行逐项破坏测试。作者已在 RESULTS.md:27
  中主动声明该项未覆盖；鉴于底层物理逻辑中未建连 CLI 进程绝不可能产生活动 turn，且后续仍有 !live.running 门禁兜底，此项无实际业务安全风险。

  ### 发现 2（P3 - 流程性）：Ticket 文件仍保留 status: open 与未勾选状态

  • 位置：T-170-reclaim-after-failed-launch.md:5
  • 严重度：P3
  • 场景说明：候选副本中该 ticket 的 frontmatter 为 status: open，验收条件 - [ ]
  尚未打勾。符合独立审查前提交只读候选的常规流程，待执行主控根据本审查结论执行合并与闭票动作即可。

  T-170 REVIEW PASS
