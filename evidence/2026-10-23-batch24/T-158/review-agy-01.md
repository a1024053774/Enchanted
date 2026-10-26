# T-158 独立审查 01（agy）

- 审查员：agy，gemini-3.8-flash-high，窗格 wG:p1P，只读副本，候选 98e61d19a。

```
agy --model gemini-3.8-flash-high --mode auto --add-dir /Users/luckye/Documents/Code/a2a-review/T-158-r1 -i "$(cat /Users/luckye/Documents/Code/a2a-review/T-158-r1/prompt.txt)"
# pane wG:p1P started 2026-10-24T01:28:28Z candidate 98e61d19a3427df61a5f58a00bab3f21cc605d4d
```

- 结论 PASS，无发现。

```text
      ▄▀▀▄        Antigravity CLI 1.4.6
     ▀▀▀▀▀▀       <agy 账号邮箱，已删> (Google AI Pro)
    ▀▀▀▀▀▀▀▀      Gemini 3.8 Flash (High)
   ▄▀▀    ▀▀▄     ~/Documents/Code/a2a-review/T-158-r1
  ▄▀▀      ▀▀▄
────────────────────────────────────────────────────────────
> 你是 a2a 项目的只读独立审查员（reviewer），审查 T-158：真实使用测试发现（F05）修订任务卡后重试仍被旧 attempt
  的 path_overlap 挡住。用户 2026-10-24 裁定“显式 reclaim 后释放”：保存 v2 → revise → 对旧 attempt reclaim →
  正常 dispatch；旧 attempt 仍活跃时继续拒绝。ticket 验收第 1 条改为“reclaim
  之后一次成功、无需交叠参数”，重点补 a2a help 与角色说明里的可发现步骤，必要时修 reclaim
  后仍拒绝的缺陷（决定见 user-decision.md）。
  执行主控沙箱外运行：RUN-OUTSIDE-01（修前 a2a help/角色说明五项可发现性检查失败；第一版夹具 reclaim
  太早，worker 已证实是夹具漏等 writing）、RUN-OUTSIDE-02（夹具选择器错误超时）、RUN-OUTSIDE-03 PASS：修前
  flow 基线与候选均通过（产品门禁修前已支持 reclaim
  后一次派发），两个变异（release-before-reclaim、retain-after-reclaim）分别落在预期断言，T-121 回归通过。
  请特别核对：帮助与角色说明写出的步骤是否完整、顺序正确、命令可运行、与门禁实际行为一致；夹具修正有没有放松业
  务断言；红态是否真落在“步骤不可发现”上；README
  与 SKILL.md 的改动是否准确。
  材料在 /Users/luckye/Documents/Code/a2a-review/T-158-r1/ 下：candidate/ 为候选 98e61d19a 只读副本（ticket 在
  candidate/.project-map/tickets/，任务卡、RESULTS 与运行证据在
  candidate/evidence/2026-10-23-batch24/T-158/）；full.diff 为相对起点 c01742804 的 workbench/
  全部改动；user-decision.md 为本批用户授权的转述（构思主控 assign）。
  请核对：
  1. 根因是否找对，改动是否在最小根因层；有无吞异常、fallback、重试、兼容分支或平行 API。
  2. ticket 的每条验收是否有真实入口的证据；期望值是否来自 ticket/规格/用户原话而不是抄产品输出。
  3. 红态是否在修前版本上落在缺陷断言上；变异是否代表真实坏实现并被拒绝。
  4. 是否越出任务卡的修改边界；界面文案是否清楚、不含营销腔。
  5. 其他正确性、回归风险。
  这是交互会话。只用你自带的读文件/搜索工具，不要运行任何 shell
  命令，不要写任何文件。可以打开截图。输出中文报告：每条发现写文件与行号、严重度（P0–P3）、失败场景。审查完把
  完整报告作为你最后一条回复直接输出，最后一行只写
  `T-158 REVIEW PASS`、`T-158 REVIEW INCOMPLETE` 或 `T-158 REVIEW NO_GO` 之一。
○ Thought for 2m 3s (Examining `test_t121_role_request_e2e.py`, it shares a consistent structure: failure...)
● Explored 29 files (user-decision.md, full.diff, T-158.md, +26) (ctrl+o to expand)
▸ Thought for 33s
   T-158 独立只读审查报告
  ## 1. 审查结论与概要
  • 结论：PASS
  • 审查对象：候选版本 98e61d19a（测试候选 1c34ad29c，产品内容 2ca1204b3），对比起点基线 c01742804。
  • 任务目标：落实用户 2026-10-24 裁定“显式 reclaim 后释放”：打回 → 保存 v2 → revise → 对旧 attempt 显式
  reclaim → 正常 dispatch 一次成功，无需交叠参数；旧 attempt 活跃（未回收）时继续保持 path_overlap
  拒绝；重点补全 a2a help 与角色说明中的可发现步骤；现场证据保留与路径占用严格分离。
  • 核心判定：根因定位准确（产品门禁修前已支持历史 attempt
  回收与路径释放，真正缺陷在于可发现性缺失）；改动位于最小根因层；红态与反例变异真实落在目标断言上；夹具两轮
  修正属于时序与 UI
  交互的精确对齐，未放松业务断言；文档步骤完整、顺序正确、命令可直接运行且与门禁实际行为严格一致；无范围外修
  改，T-121 回归通过。
  ──────
  ## 2. 根因与改动层级审查
   检查项             │ 判定 │ 事实与代码证据
  ────────────────────┼──────┼──────────────────────────────────────────────────────────────────────────────
   根因定位准确性     │ 合格 │ 在 core.ts:1250-1259 中，路径检查的活跃条件为 `!a.reclaimed &&
                      │      │ a.cleanup?.state !== "removed" && (a.state !== "revoked"
   改动层级与架构纪律 │ 合格 │ 未对 workbench/src/gates/**
                      │      │ 进行任何非必要篡改，未引入自动重试、fallback、兼容分支或平行
                      │      │ API。改动严格聚焦于补齐说明（terminalCli.ts:17-50、SKILL.md:17-68、worker.md
                      │      │ :14-32、README.md:384-396）并增加高保真端到端验收测试
                      │      │ test_t158_revise_retry_e2e.py。
  ──────
  ## 3. 验收条件与真实入口证据核对
  核对 T-158-revise-then-retry-path-release.md 及用户裁定逐项验收要求：
  ### 验收 1：打回 → 保存 v2 → revise → 对旧 attempt reclaim → 正常 dispatch 一次成功（无需交叠参数）
  • 核对结果：PASS
  • 证据来源：t158-outside-03.r3PP19-candidate.json:13-656。
  • 细节验证：
      1. initial_dispatch 派发首个
      attempt（9c5ac497…），首次交付后打回（candidate_rejected_before_revision，oracle_failed）；
      2. 测试在旧工作区写入脏哨兵文件 uncommitted-evidence.txt（测试独立输入，非产品硬编码）；
      3. card_save 保存 v2（save_v2_does_not_adopt_contract，确认 task 仍绑定 v1）；
      4. revise 显式采用 v2（revise_revokes_candidate_and_keeps_ready_task，current_attempt 为
      null，spec_rev 与 card_version 递增至 2）；
      5. 显式 reclaim 旧 attempt
      成功（explicit_historical_reclaim_succeeds），旧工作区未提交脏现场被完整保留（dirty_evidence_preserved
      _after_reclaim，内容原样保留）；
      6. 执行常规 dispatch（无 --overlap-reason 参数），返回 ok: true，生成新 attempt（f4e78b33…），fence 从
      1 递增至 2（one_dispatch_after_reclaim_without_overlap_reason）；
      7. 新 attempt 使用 v2 规格并正常交付（new_attempt_uses_v2）；事件日志完整保留旧 attempt
      回收事件（old_attempt_reclaimed_event_preserved）；
      8. Electron UI 交互层完成任务选择，并打开新 worker 窗格，核对 dataset 中的 taskId、attemptId、launchId
      完全匹配且窗格可见（electron_selected_revised_task、electron_shows_new_attempt_identity）。
  ### 验收 2：反例：旧 attempt 仍活跃时路径检查继续拒绝
  • 核对结果：PASS
  • 证据来源：candidate.json:384-406。
  • 细节验证：在 revise 完成后、reclaim 执行前，执行 dispatch，门禁严格返回 error:
  "path_overlap"，冲突列表中明确指向旧 attempt ID（unreclaimed_attempt_still_reserves_paths）。
  ### 验收 3：角色卡 / a2a help 写明步骤
  • 核对结果：PASS
  • 证据来源：instructions-green-02.json。
  • 细节验证：真实执行 node workbench/src/terminalCli.ts help（退出码 0），6 项说明检查全部通过。
  ──────
  ## 4. 红态、夹具演进与变异拒绝审查
  ### 4.1 红态真实性核验
  • 执行证据：instructions-red-02.json。
  • 分析：在修前基线 c01742804 上运行 --check instructions：
      • help_entry_exits_zero: true（命令本身可运行）；
      • help_has_ordered_revision_retry_steps: false（缺少有序重试流程）；
      • help_names_card_spec_and_old_attempt_parameters: false（缺少参数）；
      • controller_has_ordered_revision_retry_steps: false；
      • controller_has_runnable_revise_and_explicit_reclaim_examples: false；
      • worker_has_ordered_steps_and_controller_handoff: false。
      • errors: []。红态完全且精确地落在“步骤不可发现”缺陷上，无任何环境或运行期意外报错。
  ### 4.2 夹具修正核验（RUN-OUTSIDE-01 与 RUN-OUTSIDE-02）
  • RUN-OUTSIDE-01 失败与修正：
      • 原因：根据 diagnosis-01.json，原测试的 idle() 判定仅检查了 state=idle 与 active/queue
      为空，漏掉了打回消息正在通过 PTY 发送给 worker 的写入过程（writing=true），导致在输入正在发送期间发送
      reclaim，门禁正确拒绝 worker_working。
      • 修正：夹具在 test_t158_revise_retry_e2e.py:220 增加 state.get('writing') is False，确保旧 worker
      完全静默后再回收。
      • 审查判定：未放松业务断言。这修复了夹具误把未静默状态当做空闲的时序漏洞，未增加重试，未修改产品判断。
  • RUN-OUTSIDE-02 失败与修正：
      • 原因：根据 diagnosis-02.json，十项后端业务断言全部通过，但在 Electron UI 侧，旧 attempt
      被回收后清空了窗格布局（pane_layout_closed），任务选择保持空布局；原测试错误等待 SessionPane 的 data-
      task-id 选择器导致超时。
      • 修正：夹具在 test_t158_revise_retry_e2e.py:270-287 明确分步：先验证任务按钮点击并检查 aria-
      current="page" 与主进程 selection；再点击新 worker 的启动按钮 data-agent-launch，并核验新 worker
      终端的 taskId、attemptId、launchId 与可见性。
      • 审查判定：未放松业务断言。该修正补全了真实 UI 操作链路，业务断言反而更加严格。
  ### 4.3 变异反例拒绝核验（Mutants）
  根据 test_t158_revise_retry_e2e.py:112-118 与 RUN-OUTSIDE-03 运行摘要：
  1. release-before-reclaim：
      • 变异：将 (a.state !== "revoked" || Boolean(a.thread_id)) 替换为 a.state !==
      "revoked"（撤销即释放路径，不等待回收）。
      • 结果：t158-outside-03.r3PP19-release-before-reclaim.json:388-504 中，在
      unreclaimed_attempt_still_reserves_paths 断言处被精准拒绝（exit 1，errors: []）。
  2. retain-after-reclaim：
      • 变异：将 !a.reclaimed && a.cleanup?.state !== "removed" 替换为 a.cleanup?.state !==
      "removed"（只要工作区被保留，回收后仍占用路径）。
      • 结果：t158-outside-03.r3PP19-retain-after-reclaim.json:510-533 中，在
      one_dispatch_after_reclaim_without_overlap_reason 断言处被精准拒绝（exit 1，errors: []）。
  3. help-no-reclaim：
      • 变异：破坏 terminalCli.ts 中的 reclaim 关键词。
      • 结果：instructions-mutant-02.json:22-26 中，在 help_has_ordered_revision_retry_steps
      断言处被精准拒绝（exit 1，errors: []）。
  ──────
  ## 5. 修改边界、文案风格与文档准确性审查
  ### 5.1 修改边界
  • card.md 允许范围：workbench/src/gates/**、workbench/src/terminalCli.ts、角色说明文件、测试
  workbench/tests/test_t158_*.py、必要的 workbench/README.md。
  • full.diff 实际改动文件仅 5 个，完全在允许范围内，无多余文件，未触碰 .project-map/**、AGENTS.md、CONTEXT.
  md 或其他人的测试。
  ### 5.2 步骤完整性、顺序与命令可运行性
  核对以下四处文档改动：
  1. workbench/src/terminalCli.ts（L36-L50）：
      • 步骤顺序：status 保存旧 attempt ID → card_save 保存新卡 → revise 显式采用 → reclaim 回收旧 attempt →
      正常 dispatch。
      • 命令格式：均为合法且可直接复制执行的 a2a call '{"command":...}' JSON。
      • 明确指明 spec_rev 递增、card_save 只存版本不改合同、未回收仍会
      path_overlap、不使用交叠参数绕过、脏工作区保留与路径释放分离。
  2. workbench/terminal/plugin/enchanted-a2a/skills/a2a/SKILL.md（L61-L67）：
      • 为执行主控提供严格有序的 4 步指导与参数解释，明确指明输入正在发送中不能回收、worker_working
      时检查队列与回合、无法确认停止或归档时保留现场上报。
      • 经测试代码反序列化校验，文内反引号包围的 JSON 样例均为可运行的有效 JSON。
  3. workbench/roles/worker.md（L29）：
      • 规范 worker 遇到改卡需求时通过 issue 交给主控，明确 worker
      自身不改卡、不回收、不重派；收到撤销通知后停止旧 attempt 工作，不接管新 attempt。
  4. workbench/README.md（L387-L395）：
      • 给出概念说明及对应 CLI 选项，明确回收前核对
      writing=false、active=null、queued=[]，脏现场保留与路径释放分离，并明确指引项目终端里的 JSON 示例参见
      a2a help。
  ### 5.3 文案风格
  • 语言精练克制，纯客观技术说明与安全约束，无营销腔调，无助手口吻。
  ──────
  ## 6. 回归风险评估
  • 既有回归测试 workbench/tests/test_t121_role_request_e2e.py（49 项检查）在候选上全部通过（见
  t158-outside-03.r3PP19-t121.json）。
  • 门禁核心代码无变更，不引入任何状态机或鉴权回归风险。
  ──────
  T-158 REVIEW PASS
───────────────────────────────────────────────────────────────────────────────────────────────────────────────
>
───────────────────────────────────────────────────────────────────────────────────────────────────────────────
? for shortcuts                                                                         Gemini 3.8 Flash · high
```
