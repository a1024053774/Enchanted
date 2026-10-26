# T-165 独立审查 01（agy）

- 候选：c36e3eef2；起点 f2756ea20
- argv：`agy --model gemini-3.8-flash-high --mode auto --add-dir /Users/luckye/Documents/Code/a2a-review/T-165-r1 -i "$(cat /Users/luckye/Documents/Code/a2a-review/T-165-r1/prompt.txt)"`
- # pane wG:p21 started 2026-10-24T05:31:42Z candidate c36e3eef2ec6739447fff67f82d048e47002f226
- 结论：PASS。无 P0–P2。两条 P3 均为观察：(1) panes.ts:1067-1070 早到 Stop 异步完成，stopInProgress 与 drain 衔接、失败经 recordFailure 记录，审查认为闭环完整；(2) panes.ts:1039 转录坏行抛错由外层记录（沿用 T-157 裁定，不加吞异常）。执行主控不需改动。

## 窗格原文

```text

      ▄▀▀▄
     ▀▀▀▀▀▀
    ▀▀▀▀▀▀▀▀
   ▄▀▀    ▀▀▄
  ▄▀▀      ▀▀▄

  Antigravity CLI 1.4.7
  <agy 账号邮箱，已删> (Google AI Pro)
  Gemini 3.8 Flash (High)
  ~/Documents/Code/a2a-review/T-165-r1

──────────────────────────────────────────
> 你是 a2a
  项目的只读独立审查员（reviewer），审查
  T-165（执行主控自建的缺陷票，属 T-157
  已批准范围的残余）：T-157 合并后，受管
  Claude worker 在 Stop
  交付批次期间收到用户输入；CLI
  处理排队输入那一轮的 Stop
  有时早于后台凭原生转录登记该轮到达，被记
  stop_not_matched，之后再无 Stop，worker
  永远停在“运行中/未知”。
  T-157 的用户原则（经构思主控转述）：“我在
  agent 工作过程中输入内容这个他自己 cli
  会处理的吧,他会在此次工具执行完成后加入这
  句话再做思考,这个不用我们处理吧”——输入原样
  直达
  CLI，只记人工介入；门禁
  turn/attempt/版本核对不放松。
  修复（panes.ts）：Stop
  先到且满足条件（有排队输入、无
  active、同一转录、晚于排队输入、非子代理、
  stop_hook_active=false、prompt_id
  未用过）时暂存；登记该轮后按同一
  claudeStop 核对与转交完成；不符的暂存 Stop
  记 stop_not_matched；current 判定新增
  !stopped && !nativeEnded。
  执行主控沙箱外 outside-03（0
  个真实模型回合，真实 daemon/PTY/Claude
  CLI/Electron）：同一时序绿态 3/3、T-157
  stop-input 3/3 PASS；无关 Stop 反例
  PASS；修前基线与丢弃早到 Stop
  的坏实现只败在三项空闲/完成断言；T-157
  基线、坏调用方与三个变异只在预期断言失败；
  stale
  recover/expired 与 T-159/T-160/T-133 回归
  PASS。
  请特别核对：暂存条件会不会把无关或伪造的
  Stop 配给该轮；延迟执行的 claudeStop
  是否与同步路径同样核对（信任、transfer、af
  ter_transfer
  比对），失败是否被记录而非吞掉；scan 中
  stopInProgress
  早返回会不会让排队输入永远不登记；有无竞态
  导致重复
  submit；改动是否在任务卡边界内（panes.ts、
  test_t165_*、T-157
  测试夹具、evidence）。

  材料在
  /Users/luckye/Documents/Code/a2a-review/T-
  165-r1/
  下：candidate/ 为候选 c36e3eef2
  只读副本（ticket 在
  candidate/.project-map/tickets/，任务卡、R
  ESULTS
  与运行证据在
  candidate/evidence/2026-10-23-batch24/T-16
  5/）；full.diff
  为相对起点
  f2756ea2030d8ce0bddf9980d3f36d1825201d3a
  的 workbench/ 全部改动；user-decision.md
  为本批用户授权的转述（构思主控 assign）。

  请核对：
  1.
  根因是否找对，改动是否在最小根因层；有无吞
  异常、fallback、重试、兼容分支或平行
  API。
  2. ticket
  的每条验收是否有真实入口的证据；期望值是否
  来自
  ticket/规格/用户原话而不是抄产品输出。
  3.
  红态是否在修前版本上落在缺陷断言上；变异是
  否代表真实坏实现并被拒绝。
  4.
  是否越出任务卡的修改边界；界面文案是否清楚
  、不含营销腔。
  5. 其他正确性、回归风险。

  这是交互会话。只用你自带的读文件/搜索工具
  ，不要运行任何
  shell
  命令，不要写任何文件。可以打开截图。输出中
  文报告：每条发现写文件与行号、严重度（P0–P
  3）、失败场景。审查完把完整报告作为你最后
  一条回复直接输出，最后一行只写
  `T-165 REVIEW PASS`、`T-165 REVIEW
  INCOMPLETE` 或 `T-165 REVIEW NO_GO` 之一。

○ Thought for 5m 33s (The `recordFailure...)
● Explored 41 files (user-decision.md, f...)
● Explored 1 file (ctrl+o to expand)

▸ Thought for 26s
   T-165 独立审查报告

  审查对象：T-165（执行主控自建缺陷票，属
  T-157 已批准范围内的缺陷级残余）
  候选提交：c36e3eef2（被测完整产品版本
  0603f2128056108dd828941ff53307cabfc6b4bf
  ，相对起点
  f2756ea2030d8ce0bddf9980d3f36d1825201d3a
  ）
  审查范围：workbench/src/panes.ts、workbe
  nch/tests/test_t165_queued_stop.ts、work
  bench/tests/test_t165_queued_stop_e2e.py
  、任务卡与证据目录 evidence/2026-10-23-
  batch24/T-165/
  ──────
  ## 审查发现（P0–P3）

  本次审查未发现
  P0（阻断集成）、P1（严重安全/状态破坏）
  或 P2（行为不符）缺陷。记录两项
  P3（背景观察/已知设计特征）：

  1.
  **panes.ts:1067-1070**（P3，轻微时序观察
  ）：
      • 位置：workbench/src/panes.ts 第
      1067–1070 行
      • 分析：scan()
      是同步方法，在命中暂存早到
      Stop（early）时，通过 void this.
      claudeStop(...).then(() => this.
      drain(pane)).catch(error => this.
      recordFailure(pane,
      'deferred_stop_failed', error));
      异步触发完成并 break 退出循环。此时
      claudeStop 同步进入并将
      stopInProgress 置为
      true，防止任何并发 scan
      误推进新轮次；待其异步 transfer
      结束后在 finally 恢复 stopInProgress
      = false，并通过 drain
      衔接任务队列。若队列中还有后续排队输
      入，由后续观察或
      pane_waiting_native_queue
      驱动。时序闭环完整，错误通过
      recordFailure 记录，未吞异常。
  2. **panes.ts:1039**（P3，继承自 T-157
  的既有设计）：
      • 位置：workbench/src/panes.ts 第
      1039 行
      • 分析：scan() 中逐行解析原生转录
      entries = lines.filter(Boolean).
      map(line => JSON.parse(line))
      若遇损坏坏行会抛出异常，由外层调用方
      （如
      processInfo）捕获并记录失败，fail-
      closed。T-157
      独立审查已有同类裁定，本票未在此层做
      防御性吞异常包装，符合最小根因与设计
      完整性要求。

  ──────
  ## 专项核对与核验结论

  ### 1. 根因分析与改动层次

  • 根因准确性：T-157 合并后，受管 Claude
  worker 在收到用户排队输入后，CLI
  执行该排队输入回合产生的 Stop hook
  有时早于后台扫描到原生转录 native.jsonl
  中登记的该轮记录到达。旧逻辑在 !pane.
  active && !pane.claudePromptId 时将该
  Stop
  判定为未匹配并丢弃（stop_not_matched），
  随后转录登记该轮时已无后续 Stop，导致
  worker 永久停留在
  busy（“运行中/未知”）。此故障机理在基线
  回放中被完整捕获（RED-02-red-1.json seq
  116→120→121→130）。
  •
  改动层次与设计完整性：改动完全落在负责原
  生会话身份与 Hook 转交的最小根因拥有层
  panes.ts:1050-1072。将原 Stop
  匹配与完成逻辑统一定义为
  claudeStop()，消除重复逻辑，无平行
  API。未添加任何重试循环、定时轮询、启发
  式猜测或兼容分支。

  ### 2.
  暂存安全性与匹配核对（特别核对项）

  • 暂存条件防止无关/伪造
  Stop：panes.ts:1696-1706 严格要求：
      • validateHookEnvelope 通过（校验
      session、worktree、transcript
      文件名及进程归属）；
      • queued && !active && !pane.
      claudePromptId（确有排队输入且当前无
      活动 turn）；
      • !pane.failed && !pane.stopped &&
      !pane.nativeEnded && !pane.
      interrupted && !pane.
      stopInProgress；
      • !value.agent_id && value.
      stop_hook_active === false；
      • !pane.claudePromptIds?.has(value.
      prompt_id)（prompt_id
      从未被消费过）；
      • Date.parse(received_at) >= Date.
      parse(queued.received_at)；
      • realpathSync(value.
      transcript_path) ===
      realpathSync(pane.nativeFile!)。
      暂存仅存入 queued.stops Map，不执行
      transfer、不创建 turn、不推进
      active。
  • 转录身份作为唯一权威：在 scan()
  中，必须在原生转录中核对出符合正文、时间
  戳、uuid、session 的合法 entry
  后，才建立 pane.active 并设定 pane.
  claudePromptId = entry.
  promptId。随后遍历 queued.stops：任何
  prompt !== entry.promptId 的暂存 Stop
  立即记录 stop_not_matched
  并丢弃；唯有与原生 entry.promptId
  完全一致的暂存 Stop
  才被取出执行（panes.ts:1058-1061）。
  •
  延迟执行的核对与失败记录：延迟执行经由统
  一方法
  claudeStop，与同步路径核对完全相同的信封
  校验、时间戳核对、currentTurnTrust
  信任核对、transfer 异步转交以及转交后的
  after_transfer（pane.active 与 pane.
  claudePromptId
  状态比对）。若转交或核对失败，在
  claudeStop 内触发 recordFailure(pane,
  'stop_transfer_failed', error)，外层
  Promise catch 触发 recordFailure(pane,
  'deferred_stop_failed',
  error)，异常被可靠捕获并记录为窗格失败事
  件，绝无吞异常。
  • stopInProgress
  不导致排队输入丢失：panes.ts:1033 中的
  if (pane.stopInProgress) return; 仅在
  claudeStop 异步执行 transfer
  期间保护当前轮身份，防止转交过程中的调用
  方检查重新触发 scan
  误向前推进。stopInProgress 在 finally
  块中始终被重置为 false，转交完成后触发
  drain 或后续观察时排队输入即刻正常处理。
  •
  防竞态与防重复提交：排队输入被原生转录匹
  配后，pane.claudeQueuedPrompts.shift()
  即刻将该排队项连同其暂存 Map
  移出队列，且 pane.claudePromptIds.
  add(entry.promptId) 标记该 prompt_id
  已用。若同一 Stop 再次到达，无法匹配
  active 且无法通过 !pane.claudePromptIds.
  has(...) 暂存条件，直接进入
  stop_not_matched，绝不导致重复
  submit（此点在
  test_t165_queued_stop.ts:191-192
  中被宿主断言验证）。

  ### 3. 验收标准与真实入口证据

  • 红态证据：RED-02-red-1.json 与
  RED-02-red-2.json 使用真实
  Electron、daemon、PTY、Claude CLI
  和确定时序探针，在起点 main
  f2756ea2030d8ce0bddf9980d3f36d1825201d3a
  上执行，均复现 red_reproduced:
  true，且精准落在
  positive_returns_idle_without_regular_re
  covery、intervention_turn_stop_restores_
  idle、queued_native_turn_bound_and_compl
  eted 3 项空闲断言失败上，进程退出码
  1，无运行错误。
  • 绿态与回归证据：OUTSIDE-03-RESULT.json
  包含 20 场独立实例执行结果：
      • ordered-1/2/3：同一时序确定探针
      3/3 PASS；
      • stop-input-1/2/3：T-157 真实正例
      3/3 PASS；
      • stale-recover / stale-
      expired：PASS；
      • split-regression (T-159)、review-
      regression (T-160)、controller-
      regression (T-133)：3/3 PASS。
  • 反例与坏实现变异：
      • unrelated-stop：在早到 Stop
      期间注入伪造 prompt_id 的对抗
      Stop，验证其保持
      stop_not_matched、未完成该轮、未转交
      请求，且真实 Stop
      仍能完成本轮，断言全部通过；
      • ordered-baseline 与 mutant-drop-
      stop（丢弃早到 Stop
      变异）：均精准且仅在 3
      项空闲断言失败，验证了测试的判别力；
      • T-157 历史坏调用方与变异（stop-
      input-baseline、stop-input-bad-
      caller、stale-baseline、mutant-old-
      stop、mutant-no-reason、mutant-no-
      recovery）均在预期断言上失败。
  •
  期望值独立性：断言期望（回到空闲、人工介
  入绑定原 attempt、单次交付、拒绝无关
  Stop）直接来自 T-157 用户裁定原则与 T-
  165
  票证规格，非读取被测代码产物反向拼凑。

  ### 4. 任务卡边界与文案规范

  • 文件改动边界：检视
  full.diff，被测候选修改的文件仅为：
      • workbench/src/panes.ts
      •
      workbench/tests/test_t165_queued_sto
      p.ts
      •
      workbench/tests/test_t165_queued_sto
      p_e2e.py
      未触碰 AGENTS.md、CONTEXT.md、.
      project-map/** 或
      workbench/app/renderer.tsx。
  • Living doc 边界合规：实现触发
  workbench/README.md stale 报警时，worker
  恪守任务卡禁止修改范围，未越权改动
  README，而是通过 scripts/inbox
  上报非阻塞问题并保留在
  LIVING-DOC-ISSUE.md，未把文档健康误报为
  PASS。
  •
  界面文案：本票改动完全位于后台核心逻辑与
  测试，未修改任何用户界面渲染文本，无营销
  腔或多余提示。
  ──────
  ## 结论

  T-165
  根因定位精准，改动在最小拥有层，保持门禁
  与身份核对标准不放松；早到 Stop
  的暂存与转录登记绑定逻辑严密，无伪造匹配
  或重复提交风险；红态、绿态、反例及变异证
  据完整且源自真实运行时；改动严格限制在任
  务卡授权边界内。

  T-165 REVIEW PASS

─────────────────────────────────────────────
>
─────────────────────────────────────────────
? for shortcuts       Gemini 3.8 Flash · high```
