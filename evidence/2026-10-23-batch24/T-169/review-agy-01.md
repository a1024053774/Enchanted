# T-169 agy 独立审查报告（gemini-3.8-flash-high，Herdr wG:p29，只读副本 6b87c2024）

独立审查报告

  审查对象：T-169（工作中输入被 CLI 并入当前回合后，后台仍等它成为单独回合，worker 停在等待、回执不送、回收被拒）
  候选提交：6b87c2024（相对基线 73b7e7873）
  写入者：执行主控（Claude Code）
  用户授权依据：构思主控转述 user-decision.md（answer 20261024T070244Z-ideation-answer-001，用户 2026-10-24 逐字“让执行主控修复，然后做完每个票让 agy 审查”；T-169 为执行主控按 T-004 在
  T-166 缺陷残余范围内自建的缺陷级票）
  审查者：agy（只读独立审查员，未执行任何 shell 命令，未修改任何文件）

  ## 1. 根因分析与改动纯洁度（Minimal Sufficient Change）

  ### 1.1 根因核对

  • 现场与根因：源于 T-164 第二轮实测（findings/2026-10-24-real-user-dogfood-rerun-2.md N03）。当 Claude Code worker 仍在执行工具调用链（尚未生成最终回复）时，用户在窗格键入消息，Claude
  Code（v2.1.310）的原生行为是将该输入并入当前正在运行的回合（在原生 JSONL 转录中记录 type: "queue-operation", operation: "remove", reason: "absorbed_mid_turn"，并将文本作为
  queued_command 附件随下一个工具结果交给模型），不再为该输入开启单独回合。
  • 缺陷层：T-166 的实现假设所有运行中输入在原回合 Stop 后都会作为单独的排队回合（promptSource: "queued"）出现。原回合 Stop 交付虽已受理，但因排队列表 pane.claudeQueuedPrompts
  未感知并入事实，后台判定 pane_waiting_native_queue，将窗格持续置为 busy；排队的门禁回执由于窗格非 idle 无法被 drain 送入；侧栏停在忙/未知，进而导致主控在 revise 后的 reclaim 报
  worker_working 拒绝。
  • 根因判定：根因定位准确，与 Claude CLI 真实转录机制完全相符。

  ### 1.2 改动层级与坏味道检查

  • 修改位置：panes.ts:1744-1776
  • 实现机制：在原回合 claudeStop 转交完成但清理窗格状态之前，调用 dropAbsorbedPrompts(pane)：
      1. 仅当 pane.claudeQueuedPrompts 非空时执行，避免无意义 I/O；
      2. 仅认原生转录真实记录：必须满足 value.type === 'queue-operation' && value.operation === 'remove' && value.reason === 'absorbed_mid_turn'；
      3. 四重严格绑定：
          • 同会话：value.sessionId === pane.native
          • 有效标识：typeof value.commandUuid === 'string' && value.commandUuid.length > 0
          • 同正文：value.content === queued.prompt
          • 时间戳不早于收到时间：Date.parse(value.timestamp) >= Date.parse(queued.received_at)
      4. 单次消费（No Double Spending）：通过查询历史已记录的 claude_prompt_absorbed 事件构建 used 集合，并在遍历匹配成功后立即加入 used，保证每条转录移除记录仅能核销一次排队输入；
      5. 记录事实：核销时发射 claude_prompt_absorbed 审计事件，移出等待列表；未匹配的输入保持不变，继续等待原生单独回合。
  • 坏味道排查：
      • 无吞异常：dropAbsorbedPrompts 内没有任何 bare try-catch 或静默降级；外层 claudeStop 的 catch 块保持 recordFailure(..., throw error)。
      • 无超时清队列：绝不凭时间推测或超时清空排队列表，完全依赖原生转录客观证据。
      • 无 Fallback / 重试 / 平行 API：未添加任何抽象层、重试分支或影子 API。


  ## 2. 验收证据与独立期望值检验

  ### 2.1 真实入口证据

  • 测试机制：test_t166_busy_input_e2e.py
      • 驱动真实的后台 daemon、真实 Electron GUI、真实 PTY、真实 Claude Code 2.1.310 CLI，模型后端使用本地脚本化 Messages 端点（厂商回合 0，无额外费用）；
      • 输入从 Electron UI 真实键入（PTY packet 序列 \x1b[200~... 和 \r），验证 CLI 真实发出的 UserPromptSubmit 与转录日志；
      • 完整覆盖了 --scenario absorbed（在工具调用未完成时输入）与 --scenario separate（在模型生成最终文本回复时输入）两个场景。


  ### 2.2 期望值来源独立性

  • 期望断言严格来自 T-169 ticket 与 CLI 原生规范定义，绝非抄录产品输出：
      • scenario_cli_absorbed_input：断言转录中真实存在 absorbed_mid_turn；
      • no_separate_turn_awaited：断言转录并入后不再期待新的 turn_start_signal；
      • gate_receipt_written_once：断言门禁回执在原回合结束后正常被 drain 且只送入一次；
      • returns_idle：断言侧栏与窗格状态均恢复为 idle 且无报错；
      • native_cli_received_original_input：断言用户输入正文原样进入了下一次模型请求的 body。


  ## 3. 红态复现与变异测试（Mutant）审查

  ### 3.1 修前红态（Red State）

  • 依据 CHECKS.json 及截图 red-1.png：
      • 修前版本（main 基线及 73b7e7873）在 --scenario absorbed 下，2/2 均判定 red_reproduced=true；
      • 精确落在缺陷断言上：失败于 no_separate_turn_awaited、gate_receipt_written_once、returns_idle；
      • 现场现象显示原交付受理但窗格停在 pane_waiting_native_queue，窗格保持“忙”，门禁回执未能写入，完全重现 T-164 N03。


  ### 3.2 变异测试（Mutant Check）

  • 变异设计（mutant-clear-queue-at-stop.diff）：
      • 模拟“在 Stop 时不核对转录直接粗暴清空 pane.claudeQueuedPrompts = []”的敷衍实现；
  • 变异拒绝：
      • 运行在 --scenario separate（T-166 原场景，CLI 排成单独回合）时，由于队列被错误提前清空，导致后续单独回合无法绑定和完成，断言 queued_native_turn_bound_and_completed 失败，运行判定
      INCOMPLETE 被拒绝；
      • 证明本票修复不是无脑清队列，而是精确识别并入与单独排队。


  ### 3.3 回归测试

  • separate-1（T-166 默认单独排队回合场景）：PASS；
  • reg-t157-stop-input、reg-t165、reg-t166-host、reg-t157-identity：全部 PASS。

  ## 4. 任务卡修改边界与文档文案核对

  ### 4.1 修改边界（Diff Scope）

  • full.diff 严格限定在 3 个文件：
      1. panes.ts：核心判定与状态更新；
      2. test_t166_busy_input_e2e.py：测试增加 --scenario absorbed 分支与断言；
      3. README.md：文档补充。
  • 无任何越界修改，无无关改动。

  ### 4.2 文案与说明

  • README.md:763-766 技术说明客观叙述了 CLI 并入行为与 claude_prompt_absorbed 判定逻辑，无任何主观营销修饰。

  ## 5. 正确性、边界情况与潜在缺陷发现

  经过详细逐行代码审查，未发现 P0/P1 阻塞级缺陷，仅记录以下一项已知限制（P3，低风险，已披露）：

  ### [P3] 混合输入序列（同一回合中先并入、后又产生单独排队）未在单次回合中专门构造测试

  • 文件与行号：panes.ts:1757-1775
  • 场景描述：若用户在同一工作回合中连续输入两次：第一次在工具调用前（被 CLI 并入），第二次在模型写最终回复时（被 CLI 排为单独回合）。
  • 分析与缓解：
      • 代码逻辑上，dropAbsorbedPrompts 仅移出在转录中有 absorbed_mid_turn 的 prompt，由于第二次输入在 CLI 中无 absorbed_mid_turn 记录，它将安全保留在 pane.claudeQueuedPrompts
      中，原回合结束后窗格保持 busy 并等待下一次单独回合 scan，逻辑是完备的；
      • 执行主控在 RESULTS.md:30 已如实披露该边界未单独构造复合时序测试，且当前机制遵循 fail-safe 原则（未匹配转录则不误判 idle），不构成阻断。


  ## 结论汇总

   审查维度                                                               判定结果                      说明
  ┼┼
   1. 根因与改动纯洁度                                                      符合                        根因完全契合 T-164 N03；改动位于最小根因层；无吞异常、无 fallback、无超时清队列
   2. 验收证据与期望值                                                      符合                        真实 daemon/PTY/Claude CLI/Electron 端到端证据完整；期望值来自原生协议契约
   3. 红态复现与变异测试                                                    符合                        修前基线落在缺陷断言；坏实现变异（清空队列）被单独场景准确拒绝
   4. 修改边界与文案质量                                                    符合                        严格限定在任务卡涉及的 3 个文件；文案为纯技术陈述
   5. 安全与回归风险                                                        符合                        四项原生转录绑定规则严密，防重复消费；回归测试全绿

  T-169 REVIEW PASS
