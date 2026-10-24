# T-164-3 agy 独立审查报告（gemini-3.8-flash-high，Herdr wG:p2F，只读副本 1c9426c05）

独立审查报告

  审查对象：T-164-3 真实用户 dogfood 交付产物（调研报告与文本证据，不改产品代码）
  候选提交基线：1c9426c05aab916b85e5684487a05f4da27b6d2e（相对起点 2907db9522a2a8a07b95a358f72437eb60851409）
  关联任务卡与决策：card-3.md、user-decision.md

  ## 一、审查概述

  本轮 dogfood 交付物为调研报告与测试证据，未修改任何产品代码（full.diff 为空，workbench/** 无改动）。测试者在真实隔离 Electron 实例（/private/tmp/t164-
  dogfood-0zw8tib0）中，仅经 Computer Use 进行了多 agent 流程实测。

  业务执行中，A 任务（Claude Haiku）经受控打回演练、检查器两次修订与独立审查通过，成功由唯一门禁集成到 dogfood 分支（提交 547b261a18）；但 B 任务（Codex
  GLM-5.3-Flash）在首候选因卡路径冲突被拒后，B a2 重派遭遇 Codex 启动路由超时（外部失败），随后的普通回收因产品缺陷 N05/T-170（未建原生会话的 attempt
  无法回收）失败。执行主控裁定保留 B 现场、不派 C，A 集成后收尾。测试者如实将混合流程整体结论定为 INCOMPLETE，未将 A 的局部集成上调为全流程通过。

  ## 二、重点项核对

  ### 1. 修改路径与保护文件边界核对

  • 允许修改路径：
      • 2026-10-24-real-user-dogfood-rerun-3.md：新增调研报告。
      • README.md:21：仅在第 21 行新增一行索引，无多余改动。
      • evidence/2026-10-23-batch24/T-164/rerun-3/**：包含 RESULTS.md、readback.py、对账 JSON、AX 文本及截图证据。
  • 禁止修改与保护路径：
      • workbench/**、.project-map/**、AGENTS.md、CONTEXT.md 均未被触碰。
      • 执行主控撰写的保护文件 glm-image-probe.md、quota-start.md、quota-start-2.md 及 glm-tester-attempt/ 完好无损，未被修改。


  ### 2. 报告如实性核对

  • 结论状态未被上调：
      • 任务卡要求“走到审查通过并经门禁集成，含 Codex worker”。实测中仅 Claude worker A 集成，Codex worker B 现场保留，C 未派发。
      • 报告全文、RESULTS 及索引严格标明 INCOMPLETE（原混合 CLI 全流程），报告第 88 行明确指出“A 的 accepted/completed
      是这一次小任务的门禁事实，不是完整切换或发布结论”。
  • 模型比较非目标遵守：
      • 报告开头与结语均声明：本轮应用内 Codex 改用 zcode/GLM-5.3-Flash max，与前两轮 gpt-6.1-sol worker 表现不可直接比较；未做模型优劣评比。
  • 逐条复验支撑证据完整：
      • 14 项条目（F01–F07、M01–M04、N01–N04）均有清晰的状态判定（已消失/仍在/未能复验/未单独复验）与边界限制。
      • 核心条目均附有截图与 AX 树：
          • F01 / N03（T-169）：有时序表（#405 queued → #419 submit ok → #421 absorbed → #422 idle；第二输入 #495 → #498 start → #523 Stop → #527
          idle）、截图 16-a-midtool-input.jpeg、19-a-postdelivery-input.jpeg 与 AX 文件。
          • M02（完成条件弱）：记录了初版夹带数字放行、第二版漏明细检查的需修复打回过程。
          • M03（协议失败）：记录了 completion_conditions_sufficiency 填 false 导致暂停的现场，附截图 27-a-a2-review-protocol-issue.jpeg。



  ### 3. RESULTS.md 要素核对

  • 产品版本：e3b14d27b5f0f94ee65d1e15a69d6c90c1eafc5d（第 6 行）。
  • 实例路径：/private/tmp/t164-dogfood-0zw8tib0（第 7 行）。
  • 真实回合统计：
      • Claude 与 Codex 严格分列，且排除 isMeta 与 tool_result，仅计原生根消息。
      • Claude 合计 31 回合（执行主控 12、A a1 6、A a1 独审 1、A a2 6、A a2 无效独审 1、A a2 重开独审 1、A a3 2、A a3 独审 1、Reflect 1），低于 60
      回合上限。所有 Claude 会话实际模型均为 claude-haiku-5-5（claude-native-models.json）。
      • Codex B a1 实际建立会话，实际模型确认：6 个 turn_context 均为 zcode/GLM-5.3-Flash / max，CLI 为 codex-cli 0.164.0；B a2 为 0 回合（启动退出）。
  • 用量起止读数：
      • 启动日志读数 13:20:45Z：5h 已用 2%、周 16%。
      • 收尾核对 14:23:42Z：5h 已用 51%、周 23%（未触发 70%/90% 停线）。逐次读数见 quota-observed.jsonl。
  • 集成提交：
      • 候选与集成提交：547b261a18f0fa4e021d7b176960bfaf8bf9edbb。
      • 门禁对账：G=476cfb246c1d0d0d18d5f3949e778c8c49bc449e，集成引用 refs/heads/dogfood，验证 ID d97ce072-ad6c-4f5f-8a23-8df68d4bcc28（integrate-A.json
      与截图 a3-integrated.jpeg 一致）。


  ### 4. 凭据与隐私核对

  • 证据目录中未包含 auth.json、operator.json、API token、私钥或任何用户个人敏感路径数据。
  • 受管启动参数中过滤了敏感环境变量；quota-observed.jsonl 与 quota-start*.md 仅包含用量比例与时间戳。

  ## 三、专项技术审查

  ### 1. 根因与最小改动层

  • 本次任务为纯调研与证据采集，未改动产品代码。
  • 在遭遇 B 启动失败与回收被拒时，测试者未尝试通过脚本绕过门禁，未做循环重试或伪造状态，如实将现场保留在 status-B-a2.json 与
  reclaim-B-a2.json，交由外层建票 T-170 处理。

  ### 2. 真实入口证据与独立期望值

  • 所有操作均通过 Electron 客户端 UI 和交互终端进行，无 CDP/DOM 或后端驱动绕行。
  • A 任务检查器期望值（水果 3、主食 2、乳品 1、总计 6）严格来源于 golden/pantry.json 的独立推导，而非抄录候选输出。

  ### 3. 红态落在缺陷断言与变异检查有效性

  • 红态表现真实：
      • A a1 首候选缺失总计，精准落在 oracle_failed 断言上。
      • A a2 独审以变异 M4（水果夹带数字）与 M5（总计夹带数字）证明原 check_a.py 判定过宽，真实打回需修复。
      • B a1 交付触发 path_boundary_failed，精准拦截卡内 allow 与 deny 矛盾的 shopping.md。
  • 独审 5 个变异检查（integrate-A.json 第 357–388 行、a3-review-pass.ax.txt:35-42）：
      • M1（删全局总计）-> 退出码 1，FAIL；
      • M2（水果改 4）-> 退出码 1，FAIL；
      • M3（总计改 7）-> 退出码 1，FAIL；
      • M4（加逐项明细行）-> 退出码 1，FAIL；
      • M5（水果首个数字置 0）-> 退出码 1，FAIL。
      • 5 个变异均代表真实的坏实现，且在临时副本中均被检查器拒绝。


  ### 4. 任务边界与文案规范

  • 改动完全处于授权边界内。
  • 报告与 AX 记录均遵循客观事实陈述，无营销腔与模糊夸大词汇。

  ## 四、审查发现列表

   编号       位置                                                    严重度  缺陷/失败场景说明
  ┼┼┼
   FINDING-1  T-164-real-user-dogfood-rerun.md:25                       P2    业务目标未完整闭环：Ticket 验收第 1
                                                                              条要求“走到审查通过并集成（经门禁），含 Codex worker”。本轮仅 Claude
                                                                              worker A 经门禁集成，Codex worker B 因外部启动路由超时及回收缺陷 N05/T-
                                                                              170 保留现场，C 未派发。全流程验收未闭环（报告如实标记为 INCOMPLETE）。
   FINDING-2  reclaim-B-a2.json:3findings/...-rerun-3.md:56             P2    未建会话 attempt 无法普通回收（N05/T-170）：当 worker
                                                                              在原生会话建立前即失败（launch_failed、native_session: null）时，后台
                                                                              reclaim 因校验 native_session 判定 identity_conflict
                                                                              拒绝回收，导致同票无法重派或自主恢复。现场已安全保留并由主控建票 T-170。
   FINDING-3  findings/...-rerun-3.md:74reflect-final.ax.txt:68         P3    界面重开审查在 Reflect
                                                                              树中显示“未归属”：从问题面板为同次交付新开的审查会话（e2d0d578），在
                                                                              Reflect 视图中脱离了执行主控/attempt
                                                                              层级，显示在“未归属”列表中，影响会话层级溯源直观性。
   FINDING-4  findings/...-rerun-3.md:74a3-integration-done.ax.txt:3    P3    终端持续报告 Stop hook 报错：执行主控在结束回合触发 Stop hook 时反复提示
              6                                                               Stop hook error: MCP server 'lcu' not
                                                                              connected。虽未中断主控进程与门禁集成，但在终端产生干扰日志。

  ## 五、结论与后续建议

  1. 报告与证据交付质量：材料边界清晰、无代码越界修改、无凭据泄露，各现象均有完整的 AX 差异、截图与转录数据交叉核验。
  2. 结论判定：根据规范，验收条件第 1 条（“含 Codex worker 走到审查通过并经门禁集成”）未达成，且全流程停留在局部集成收尾，按照“不将未完成结果上调为
  PASS”的准则，审查结论定为 INCOMPLETE。该结论与交付报告本身的自评完全一致，允许将本轮成果与证据合入 main 并归档，留待修复 T-170 后继续推进。

  T-164-3 REVIEW INCOMPLETE
