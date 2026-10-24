# T-160 独立审查 01（agy）

- 候选：e281b1b55；起点 3aea74368
- argv：`agy --model gemini-3.8-flash-high --mode auto --add-dir /Users/luckye/Documents/Code/a2a-review/T-160-r1 -i "$(cat /Users/luckye/Documents/Code/a2a-review/T-160-r1/prompt.txt)"`
- # pane wG:p1S started 2026-10-24T02:33:51Z candidate e281b1b55794cccbc7ec7432b86904db742dff6a
- 结论：PASS。两条 P3 观察：OBS-01 回收中断后 review_recovery_unknown 为 fail-closed，须主控介入；OBS-02 问题页按 system 问题正文 JSON 判定协议错误。均不阻塞。

## 窗格原文

```text

      ▄▀▀▄        Antigravity CLI 1.4.6
     ▀▀▀▀▀▀       littledave950@gmail.com (Google AI Pro)
    ▀▀▀▀▀▀▀▀      Gemini 3.8 Flash (High)
   ▄▀▀    ▀▀▄     ~/Documents/Code/a2a-review/T-160-r1
  ▄▀▀      ▀▀▄

──────────────────────────────────────────────────────────
> 你是 a2a 项目的只读独立审查员（reviewer），审查
  T-160：真实使用测试发现（M03）haiku reviewer 把审查 JSON
  包进 ```json 代码块，门禁按 review_json
  协议错误暂停，且无明确恢复路径。ticket 目标：（1）reviewer
  启动指令与角色卡写清输出裸
  JSON、输出前自检；（2）协议错误时保留原文并拒绝，不剥围栏
  追认通过；界面写明原因并给出恢复路径（为同一次交付新开审查
  ）；不加自动重试。
  执行主控批准的边界扩展：允许改
  workbench/src/panes.ts，仅在“该 reviewer
  的审查提交协议解析失败，且该次提交对应的 Stop
  已匹配完成”时补 idle/可回收事实；其他 unknown
  一律拒绝回收。
  执行主控沙箱外运行：RUN-OUTSIDE-01
  修前红态；RUN-OUTSIDE-02 idle 红/绿与两个状态变异（任意
  unknown 可回收、忽略提交匹配）、真实 Electron
  绿态、accept-fenced/unbound-review/reuse-failed
  三个变异、问题页与审查集成回归均 PASS；RUN-OUTSIDE-03 真实
  haiku reviewer 3 次（9/9 回合）：2 次裸 JSON 被接受，1
  次仍带围栏被拒、原文保留、恢复入口可用。
  请特别核对：门禁是否仍拒绝带围栏输出且不剥围栏；恢复是否绑
  定原交付（同一
  task/attempt/候选），不复用旧审查结论、不自动重试；panes.t
  s
  改动是否只在上述条件成立、反例是否覆盖；界面文案是否说清原
  因与下一步；RESULTS
  是否如实写 2/3 比例而非“均符合协议”。

  材料在 /Users/luckye/Documents/Code/a2a-review/T-160-r1/
  下：candidate/ 为候选 e281b1b55 只读副本（ticket 在
  candidate/.project-map/tickets/，任务卡、RESULTS
  与运行证据在
  candidate/evidence/2026-10-23-batch24/T-160/）；full.diff
  为相对起点 3aea74368 的 workbench/
  全部改动；user-decision.md 为本批用户授权的转述（构思主控
  assign）。

  请核对：
  1.
  根因是否找对，改动是否在最小根因层；有无吞异常、fallback、
  重试、兼容分支或平行
  API。
  2. ticket 的每条验收是否有真实入口的证据；期望值是否来自
  ticket/规格/用户原话而不是抄产品输出。
  3.
  红态是否在修前版本上落在缺陷断言上；变异是否代表真实坏实现
  并被拒绝。
  4.
  是否越出任务卡的修改边界；界面文案是否清楚、不含营销腔。
  5. 其他正确性、回归风险。

  这是交互会话。只用你自带的读文件/搜索工具，不要运行任何
  shell
  命令，不要写任何文件。可以打开截图。输出中文报告：每条发现
  写文件与行号、严重度（P0–P3）、失败场景。审查完把完整报告
  作为你最后一条回复直接输出，最后一行只写
  `T-160 REVIEW PASS`、`T-160 REVIEW INCOMPLETE` 或 `T-160
  REVIEW NO_GO` 之一。

○ Thought for 4m 30s (The code directly parses the input...)
● Explored 88 files (user-decision.md...) (ctrl+o to expand)

▸ Thought for 1m 31s
   a2a 独立审查报告：T-160 reviewer 围栏 JSON
  协议错误与同一次交付恢复

  ## 1. 审查概述与结论

  本审查员受命对任务 T-160（候选提交 e281b1b55，相对起点
  3aea74368）进行只读独立审查。

  审查结论：PASS。
  候选实现根因定位准确，修改位于最小根因层；严格遵循“不剥
  围栏、不追认、不自动重试”的核心原则；执行主控批准的
  workbench/src/panes.ts 边界扩展严格约束在 reviewer
  提交协议解析失败且 Stop
  匹配完成的分支；红态、绿态、变异体与真实 haiku
  模型测试（9/9 回合）证据完整且具有独立性；RESULTS
  真实记录了 2/3 的协议符合比例，无虚假粉饰。
  ──────
  ## 2. 特别核对项专项核实

   核对项               │ 审查结论 │ 关键代码与证据核验
  ──────────────────────┼──────────┼──────────────────────
   门禁是否仍拒绝带围栏 │ 符合要求 │ workbench/src/gates/
   输出且不剥围栏       │          │ qualityProtocol.ts
                        │          │ 保持原样未动，review
                        │          │ Request 仍直接调用裸
                        │          │ JSON.parse(raw)，任
                        │          │ 何带
                        │          │ ````json围栏或文本前
                        │          │ 缀的输出均抛出Qualit
                        │          │ yProtocolError("revi
                        │          │ ew_json")。<br>变异
                        │          │ 体 mutant-accept-
                        │          │ fenced（模拟剥除围栏
                        │          │ 坏实现）被测试在
                        │          │ fenced_output_reject
                        │          │ ed`
                        │          │ 断言明确捕获拒绝。
   恢复是否绑定原交付， │ 符合要求 │ workbench/src/gates/
   不复用旧结论、不自动 │          │ core.ts:2532–2570（r
                         │        │ 在同一任务操作锁下严
                        │          │ ）在同一任务操作锁下
                        │          │ 严格校验
                        │          │ args.attempt ===
                        │          │ attempt.attempt_id、
                        │          │ args.review_id ===
                        │          │ review.review_id、re
                        │          │ view.candidate_commi
                        │          │ t ===
                        │          │ task.candidate_commi
                        │          │ t、task.verification
                        │          │ .verification_id
                        │          │ 等一致性；重新派发
                        │          │ requestReview
                        │          │ 生成全新
                        │          │ review_id、新独立目
                        │          │ 录与新工作副本，绝不
                        │          │ 复用旧审查结论。变异
                        │          │ 体 mutant-reuse-
                        │          │ failed（模拟直接将任
                        │          │ 务标为 verified
                        │          │ 追认旧审查）与
                        │          │ mutant-unbound-
                        │          │ review（模拟放宽
                        │          │ review_id
                        │          │ 绑定）分别被
                        │          │ same_delivery_new_re
                        │          │ view 和
                        │          │ unbound_recovery_rej
                        │          │ ected
                         │        │ 用户在界面显式点击，
                        │          │ 用户在界面显式点击，
                        │          │ 绝无自动重试。
   panes.ts             │ 符合要求 │ workbench/src/panes.
   改动条件与反例覆盖   │          │ ts:1549–1556 仅在
                        │          │ pane.record.role ===
                        │          │ "reviewer" &&
                        │          │ pane.failed ===
                        │          │ "invalid_review_resu
                        │          │ lt" 且对应提交的
                        │          │ active、nativeTurn、
                        │          │ pane.turn 与
                        │          │ session_id
                        │          │ 四重一致时，才在保留
                        │          │ pane.failed
                        │          │ 标记的同时补齐 turn
                        │          │ 完成的 idle
                        │          │ 事实；任何不匹配均保
                        │          │ 持 unknown
                        │          │ 并退出。workbench/te
                         │        │ _idle.ts 覆盖 7
                        │          │ ol_idle.ts 覆盖 7
                        │          │ 种场景（包含未匹配
                        │          │ Stop、替换新提交、其
                        │          │ 他 unknown、其他
                        │          │ review 错误、worker
                        │          │ 角色、抛出异常
                        │          │ transfer 等 6
                        │          │ 个反例），且有两个变
                        │          │ 异体（any-
                        │          │ unknown、ignore-
                        │          │ submission）验证全部
                        │          │ 反例均有效拒绝。
   界面文案是否清楚、不 │ 符合要求 │ workbench/app/Issues
   含营销腔             │          │ Page.tsx:69–79
                        │          │ 文案准确说明：“审查
                        │          │ 输出不是可直接解析的
                        │          │ JSON
                        │          │ 对象。代码围栏、前后
                        │          │ 说明或 JSON
                        │          │ 语法错误都会被拒绝。
                        │          │ 这次输出被拒绝，当时
                        │          │ 任务因此暂停。原文保
                        │          │ 留如下。”并提供“为同
                        │          │ 一次交付新开审查”操
                        │          │ 作入口及“将停止并归
                        │          │ 档旧审查，为这一次交
                        │          │ 付新开一个干净的审查
                        │          │ 会话，仍审查同一个候
                        │          │ 选提交”的操作提示。
                        │          │ 文案克制、使用统一定
                        │          │ 义术语，无任何 AI
                        │          │ 腔或营销修饰。
   RESULTS 是否如实写   │ 符合要求 │ evidence/2026-10-23-
   2/3 比例             │          │ batch24/T-
                        │          │ 160/RESULTS.md 第 3
                        │          │ 行与第 59
                        │          │ 行明确如实记载：真实
                        │          │ haiku reviewer 3
                        │          │ 次测试中，2 次输出裸
                        │          │ JSON 被协议接受，1
                        │          │ 次仍带围栏被拒并展示
                        │          │ 恢复入口，明确指出“
                        │          │ 比例为
                        │          │ 2/3……不能写成‘输出均
                        │          │ 符合协议’”。
  ──────
  ## 3. 五个审查维度详细评估

  ### 维度
  1：根因是否找对，改动是否在最小根因层；有无吞异常、fallb
  ack、重试、兼容分支或平行 API

  1. 根因定位精准：
      • 诱因层：haiku reviewer
      缺乏对首尾字符及禁止代码块的自检约束；
      • 运行时层：Codex Stop 在 reviewer
      交付结果校验失败（pane.failed）后，将窗格置为
      unknown，导致 readThread 误报 running:
      true，进而使门禁在回收时遭遇 reviewer_not_idle
      阻断；
      •
      产品层：协议解析失败后，界面未格式化解析协议错误结构
      体，未提供绑定原交付的新开审查入口，且门禁 verify
      缺乏在 paused 状态下重开审查的分支。
  2. 改动处于最小根因层：
      • 提示词层仅在 workbench/roles/reviewer.md:11 与
      workbench/src/gates/core.ts:2492 补充输出前 JSON
      自检规则；
      • 核心门禁协议解析层 qualityProtocol.ts
      保持严格不变；
      • 门禁恢复复用现有 verify
      命令入口与任务锁，未开辟平行 API；
      • panes.ts
      仅对匹配完成的审查协议错误补充回合结束事实，不放宽对
      其他未知态的阻断。
  3. 无吞异常、fallback、自动重试或兼容分支：
      • 解析错误明确抛出
      QualityProtocolError("review_json") 并入库；
      • 界面 JSON.parse(issue.body) 的 try-catch
      仅用于区分结构化系统问题与普通自由文本问题，无降级容
      错；
      • 恢复操作需显式发起，绝无静默重试。


  ### 维度 2：ticket
  的每条验收是否有真实入口的证据；期望值是否来自
  ticket/规格/用户原话

  1. 真实 haiku 3 次运行证据（RUN-OUTSIDE-03）：
      • 证据文件：evidence/2026-10-23-batch24/T-160/real-
      haiku-3-20261024T022454Z-t160-real-outside-cu5MpE.
      json；
      • 审计文件：outside-03-audit.json，核验 6 份原生
      transcript（3 worker × 2 回合 + 3 reviewer × 1 回合
      = 9 回合），真实预算 9/9 回合完全契合；
      • 截图 real-haiku-3-20261024T022454Z-t160-real-
      outside-cu5MpE-03-real-rejected.png
      证实第三次带围栏输出被拒后，界面展示了可展开原文及“
      为同一次交付新开审查”按钮。
  2. 反例与带围栏拒绝证据：
      • 修前 Electron 红态（red-20261024T013902Z-t160-red-
      outside-cp6P1m.json）与修后 Electron 绿态（green-
      20261024T020931Z-t160-verify-outside-U5psYJ.
      json）均验证带围栏输出导致 paused
      且原文字串完整留存；
      • 期望值直接来源于 ticket
      原话“反例：带围栏输出仍被拒绝，原文保留”，并非由实现
      代码推导。


  ### 维度
  3：红态是否落在缺陷断言上；变异是否代表真实坏实现并被拒
  绝

  1. 修前红态落点：
      • RUN-OUTSIDE-01.sh 在起点提交 3aea74368
      上运行，前面的业务断言均通过，精准断言失败于
      AssertionError:
      recovery_guidance_visible（界面仅堆砌未格式化的原始
      JSON 且无恢复操作入口）；
      • Codex 状态级红态 idle-red-parent-01.json 在
      3aea74368 上准确失败于
      matched_parser_failure_reclaimable（协议错误无法
      stop）与 different_submission_not_reclaimable（旧
      Stop 误清除了新提交）。
  2. 变异体代表真实坏实现且被全数拒绝：
      • mutant-accept-fenced（剥围栏追认通过）：失败于
      AssertionError: fenced_output_rejected: verified；
      • mutant-unbound-review（解绑 review_id
      校验）：失败于 AssertionError:
      unbound_recovery_rejected；
      • mutant-reuse-failed（直接复用旧审查结果）：失败于
      AssertionError: same_delivery_new_review；
      • idle-mutant-any-unknown（盲目允许任意 unknown
      回收）：6 个反例全部触发 Missing expected
      rejection；
      • idle-mutant-ignore-
      submission（忽略提交替换核对）：失败于
      different_submission_not_reclaimable。


  ### 维度
  4：是否越出任务卡修改边界；界面文案是否清楚、不含营销腔

  1. 修改边界检查：
      • 修改仅涉及 workbench/roles/reviewer.
      md、workbench/src/gates/core.
      ts、workbench/src/panes.ts（经主控批准扩展）、workbe
      nch/app/（IssuesPage.tsx、main.ts、preload.
      ts、records.css、renderer.tsx）、workbench/README.md
      及本票测试与证据；
      • 禁止修改的 .project-map/**、AGENTS.md、CONTEXT.md
      及他人测试文件在 diff 中零改动；
      • 本地生成的两个 inbox 文件留在 worktree
      未提交入库。
  2. 文案质量：
      •
      全流程文案使用产品标准用语（“代码围栏”、“为同一次交
      付新开审查”、“查看审查原文”），无多余口语与 AI
      腔调。


  ### 维度 5：其他正确性、回归与并发风险分析

  1. 恢复意图事件幂等与防重：
      • workbench/src/gates/core.ts:2550 在开始回收前检查
      review_protocol_recovery_intent，若上次回收中途中断
      导致状态未知，再次恢复会直接报错
      review_recovery_unknown
      并交由主控核对，绝不盲目重做外部副作用。
  2. 回收顺序与安全确认：
      • 顺序为：校验意图 -> 停止进程 -> 归档线程 ->
      校验已停止且已归档 -> 清理候选工作副本 -> 清理独立
      worktree -> 释放成员资格 ->
      发起新审查，每一步均有前置与后置门禁校验。
  3. 隔离凭据安全治理：
      • 真实模型测试测试脚本在独立临时 HOME
      复制凭据时剔除了 refreshToken，设置模式为
      0600，测试完成后立即递归销毁临时
      HOME，凭据未泄露至日志或版本控制。
  4. 现行回归完全通过：
      • test_t132_issues_panel_e2e.py（6 项）与
      test_t137_reflect_e2e.py（10 项）全数通过。

  ──────
  ## 4. 发现与观察清单

   编号   │ 位置               │ …  │ 场景与说明
  ────────┼────────────────────┼────┼─────────────────────
   OBS-01 │ workbench/src/gate │ P3 │ 回收中断后的重入保
          │ s/core.ts:2550     │    │ 护为 Fail-
          │                    │    │ Closed：当
          │                    │    │ stopThread 或
          │                    │    │ cleanupReviewCandid
          │                    │    │ ate
          │                    │    │ 中途崩溃或断电后，r
          │                    │    │ eview_protocol_reco
          │                    │    │ very_intent
          │                    │    │ 已经落库，后续对该
          │                    │    │ review_id
          │                    │    │ 的重试将被门禁拒绝
          │                    │    │ 为
          │                    │    │ review_recovery_unk
          │                    │    │ nown。这是系统特意
          │                    │    │ 设计的保护机制（防
          │                    │    │ 止未知现场下的双重
          │                    │    │ 清理或进程错杀），
          │                    │    │ 此时必须由执行主控
          │                    │    │ 介入排查，无自动重
          │                    │    │ 试或自愈通路。
   OBS-02 │ workbench/app/Issu │ P3 │ 系统问题体结构依赖
          │ esPage.tsx:49–55   │    │ JSON
          │                    │    │ 字符串反序列化：当
          │                    │    │ 前问题上报体系通过
          │                    │    │ issue.from ===
          │                    │    │ 'system'
          │                    │    │ 且正文可解析为含有
          │                    │    │ error 与 raw 字段的
          │                    │    │ JSON
          │                    │    │ 判定为协议错误。虽
          │                    │    │ 然外层通过
          │                    │    │ canRestart 对
          │                    │    │ attempt_id 与
          │                    │    │ thread_id
          │                    │    │ 做了双重绑定防错，
          │                    │    │ 但属于带内数据复用
          │                    │    │ 。未来若问题系统演
          │                    │    │ 进，建议为系统问题
          │                    │    │ 引入独立结构化元数
          │                    │    │ 据字段。
  ──────
  T-160 REVIEW PASS


─────────────────────────────────────────────────────────────
>
─────────────────────────────────────────────────────────────
? for shortcuts                       Gemini 3.8 Flash · high```
