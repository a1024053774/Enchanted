# T-149 独立审查 01（agy）

- 审查员：agy 1.4.6，gemini-3.8-flash-high，Herdr 可见窗格 wG:p11，auto 模式只用读文件工具，只读副本，候选 1b017f8ef。
- 启动 argv：

```
agy --model gemini-3.8-flash-high --mode auto --add-dir /Users/luckye/Documents/Code/a2a-review/T-149-r1 -i "$(cat /Users/luckye/Documents/Code/a2a-review/T-149-r1/prompt.txt)"
# pane wG:p11 started 2026-10-23T18:36:04Z
```

- 审查后候选副本 git status 0 行改动。结论 PASS；两条 P3：DISPOSITION 引用的历史证据在稀疏检出范围外未注明、T-082 RESULTS.md 未写完整路径（应为 evidence/2026-10-15-batch15/T-082/RESULTS.md）。

## 窗格中的报告原文

```text

○ Thought for 5m 44s (The agent is focusing on the question about historical revisions a...)
● Explored 65 files (full.diff, T-149-retire-stale-historical-tests.m...) (ctrl+o to expand)

▸ Thought for 31s
   a2a T-149 独立审查报告

  审查对象：T-149（过时历史测试：删除不再有价值的，其余标为只针对历史版本）
  候选分支/提交：candidate（基准 8eda61b96bb01cda338d2bd2cb6927ce4bae5386，最终候选
  1b017f8eff83df82ff6b89fd64d18897060a809a）
  处置结论：13 个测试文件删 0、标历史 3、待决 10；新建 HISTORICAL.md 索引。
  ──────
  ## 一、审查项逐项核对

  ### 1. 判据应用一致性核对

  用户判据：测试守护的契约已被现行且通过的测试覆盖、或契约已废弃的才删；仍是现行契约唯一守
  护者的不删，也不静默放过，交用户（needs-decision）。

  #### (1) 待决文件抽查（核对 5 个待决文件，超过要求的 4 个）

  1. test_t112_execution.mjs
      • 守护契约：五角色出厂默认、SQLite
      重启后设置持久化（restart_persists_role_settings）、参数优先级（覆盖 > 设置 >
      默认，field_override_precedence）、角色隔离、权限字段拒绝（permission_fields_rejecte
      d）、未支持 effort
      透传（unsupported_effort_not_coerced）、原生启动失败记录（native_startup_failure_rec
      orded）。同时被 test_t112_closed_fixture.py:22 直接调用。
      • 现行覆盖情况：现行全绿的 test_t141_launch_contract.mjs 仅静态检查 claudeArgv 与
      createPane 参数文本，test_t127_codex_home_e2e.py 仅覆盖常规交付；均未覆盖 SQLite
      重启持久化、参数优先级、权限拒绝或未知 effort 透传。
      • 过时部分：第 75–76 行检查 reviewer 关闭网络，已被 T-141 废弃。
      •
      核对结论：存在未被替代的有效契约守护，且被其他测试直接调用，不能整份删除；列为“待决”
      符合判据。
  2. test_quality_tracer_e2e.py
      • 守护契约：评分必填与一次写入（TRACER-SCORE-REQUIRED、TRACER-SCORE-FIELDS、TRACER-
      SCORE-ONCE）、严格 JSON 审查报告且禁止去除 markdown code block（TRACER-REVIEW-
      STRICT-JSON）、第三次拒绝暂停（TRACER-THIRD-STOP）、禁止复用原生审查会话（TRACER-
      REVIEW-REUSE）。同时作为 8 个其他测试的基类。
      • 现行覆盖情况：现行 E3 (test_t127)、E4 (test_t131)、E7 (test_t141)
      仅覆盖正常交付与审查流程，均无评分缺失拒收、markdown
      报告拒绝、三次拒绝暂停等负例测试。
      • 过时部分：第 47–52 行要求独立 home 与关网络断言已过时。
      •
      核对结论：仍是关键负例与集成门禁契约的守护者，且是测试继承基类，不能删；列为“待决”符
      合判据。
  3. test_t082_review_boundary_e2e.py
      • 守护契约：审查中共享 refs 变化作废（REVIEW-REFS-INVALIDATE）、review_requirements.
      workspace 校验（REVIEW-REQUIREMENTS-WORKSPACE）、审查结束核对完成前拒绝集成及 held
      socket 竞争检查（REVIEW-END-BEFORE-INTEGRATE）。
      • 现行覆盖情况：现行 E4 (test_t131) 默认绿态不走 --foreign-ref
      分支；现行主干回归均无 held socket 竞态或变异 workspace 拒收的等价覆盖。
      • 过时部分：第 32–35 行关网络断言失效。
      • 核对结论：属于审查边界与竞态条件的唯一守护者，不能删；列为“待决”符合判据。
  4. test_t108_questions.mjs
      • 守护契约：Claude 主控的原生问答 hook 关联、缺失 tool_name 拒绝、畸形 envelope
      拒绝、重复答复拒绝、原生取消解析等。
      • 现行覆盖情况：现行 E6 仅验证 SessionEnd；E7 的问答验证走 issue 途径，非原生
      AskUserQuestion hook。其导入的 t108_hook_failure_contracts.mjs 与
      t108_answer_lifecycle_contracts.mjs 仅由此入口调用。
      • 过时部分：第 114 行 Codex worker 等待 waiting_controller_answer 已被 T-124 取代。
      • 核对结论：Claude 原生问答契约在现行测试中无替代，不能因 Codex
      端过时断言而整份删除；列为“待决”符合判据。
  5. test_t078_claude_signals.ts
      • 守护契约：已登记 active submission 时 UserPromptSubmit/Stop 的流转，以及重复 Stop
      不产生二次 pane_idle 事件。
      • 现行覆盖情况：现行 E6 (test_t146_session_end.mjs) 中 pane.active 恒为
      null，未测试存在活动提交时收到重复 Stop 的幂等去重。
      • 核对结论：该幂等契约在现行测试中无替代；列为“待决”符合判据。


  #### (2) 3 个“标历史”文件核对

  1. diagnose_t112_reviewer.py
      • 能否直接删：不能。被现行测试 test_t112_request_replay.py:11（import
      diagnose_t112_reviewer as fixture）及 run_t112_native.py:19
      直接导入。若直接删除会导致模块缺失失败。
      • 是否守护现行契约：否。其自身执行依赖 Codex 0.162.1 及已废弃的关网络断言；现行
      reviewer 沙箱边界已由 E3 (test_t127) 与 E7 (test_t141) 覆盖。
      • 结论：标历史并保留供回放测试导入，处置正确。
  2. t112_reviewer_record.mjs
      • 能否直接删：不能。由 diagnose_t112_reviewer.py:116 启动，并被
      test_t112_reviewer_startup.mjs:7 读取。
      • 是否守护现行契约：否。它仅是配合旧诊断的 host 脚本，现行 reviewer 启动已由 E1/E2
      覆盖。
      • 结论：标历史并保留依赖，处置正确。
  3. controlled_quality_pty.ts
      • 能否直接删：不能。被 quality_chain_host.ts:6、daemon_acceptance_host.
      ts:10、conflict_acceptance_host.ts:5、multiturn_identity_host.ts:6 导入，并被
      run_daemon_acceptance.py:102 复制。直接删除会破坏全套质量 host 解析。
      • 是否守护现行契约：否。其第 51 行无条件发出 Open restricted 屏幕且不发 native
      ready，与 T-141 启动契约冲突。
      • 结论：标历史并保留供依赖方解析，处置正确。

  ──────
  ### 2. 标历史 revision 证据支撑核对

  • Revision 核对：
      • diagnose_t112_reviewer.py 与 t112_reviewer_record.mjs 标注
      5f19062f52154914123e3796fdff87caaa22fc1f：
          • 经查证票据 T-112-launch-model-effort-configurable.md:44-54 第 44 行与 Git
          提交日志（merge exec/t112 前置提交 0797da8853b），确认 5f19062f5 确为 T-112
          最终交付候选版本，其 outside-merge-*-03 与 outside-native-07 原生验收全部
          PASS。版本号准确无误。
      • controlled_quality_pty.ts 标注 5f7f9816eb9a996377c5b255695244d99c0259e7：
          • 经查证 Git 提交日志（0581324260b 与 271ac55d82d），确认 5f7f9816e 确为 T-082
          审查返工冻结候选版本，当时针对审查启动边界与结束核对做了独立验证，同时明确记录该
          版本下 T-076 runner 因契约演进存在预期失败。版本号与证据边界准确对应。

  • 证据文件存在性与稀疏检出（详见下文 P3 发现）：
      • DISPOSITION 中引用的 evidence/2026-10-20-batch18/T-112/outside-merge-t112-native-
      03.json 及 T-082 RESULTS.md（位于 evidence/2026-10-15-batch15/），因本仓库 worktree
      的 sparse-checkout 仅包含
      batch16、batch17、batch23，未在工作区磁盘检出，但历史版本与验收事实已在票据和 Git
      提交记录中闭环证实。

  ──────
  ### 3. 改动纯洁性与代码完整性核对

  核对 full.diff：

  1. 改动仅包含：
      • 新建 HISTORICAL.md；
      • 在 controlled_quality_pty.ts、diagnose_t112_reviewer.py、t112_reviewer_record.mjs
      第一行各增加一行注释。
  2. 未改动任何原有代码行、断言逻辑、导出函数或 import 声明。
  3. 3 个被标记文件原始第一行均非 shebang（#!/...），添加注释未破坏 shebang。
  4. 语法与模块解析验证：
      • diagnose_t112_reviewer.py：第 1 行 # 注释后接 module docstring，符合 Python
      语法规范，在 test_t112_request_replay.py 中离线导入及请求回放 4 项测试全部
      PASS（exit 0）。
      • controlled_quality_pty.ts：第 1 行 // 注释，Node 导入及导出 installControlledPTY
      验证 PASS（exit 0）。
      • t112_reviewer_record.mjs：第 1 行 // 注释，node --check 语法解析 PASS（exit 0）。
  5. 10 个待决文件逐字节与基准一致，未发生任何非预期修改。
  ──────
  ### 4. HISTORICAL.md 准确性核对

  1. 文件标题与结构清晰区分为“只针对历史版本的辅助文件”（3 个）与“待用户决定，未停用”（10
  个）。
  2. 文档明确声明：“标记不改变代码、导出或
  import，也不把依赖它们的待决测试宣布为已停用或已通过”、“以下 10
  个文件保持原样：没有删除、跳过、改断言或标为历史。它们含过时假设，也仍含未找到现行全绿替
  代的有效检查；是否迁移或接受覆盖缺口，待用户决定”。
  3. 准确列出了 10 个待决文件的有效检查清单，未将待决测试混淆为已通过或已停用。
  4. 所有相对 markdown 链接路径均准确有效。
  ──────
  ## 二、发现问题清单（Findings）

  ### 发现 1：DISPOSITION 引用的历史证据路径位于 sparse checkout 范围外

  • 文件与行号：DISPOSITION.md:62-63
  • 严重度：P3
  • 失败场景：
  DISPOSITION.md 表中引用的 evidence/2026-10-20-batch18/T-112/outside-merge-t112-native-
  03.json 及 T-082 RESULTS.md（位于 evidence/2026-10-15-batch15/），在本仓库 worktree 的
  sparse-checkout 规则中被排除（工作树仅检出 batch16、batch17、batch23）。
  审查员或后续开发者在工作树内直接通过文件系统路径访问该文件时会提示文件不存在（需通过 git
  show 或调整 sparse-checkout 获取）。虽然票据 T-112-launch-model-effort-configurable.md
  与 Git 历史完整证实了对应 revision 的通过事实，但 DISPOSITION
  表中未注明该文件在稀疏检出范围外。

  ### 发现 2：DISPOSITION 中 T-082 RESULTS.md 引用缺少完整路径

  • 文件与行号：DISPOSITION.md:63
  • 严重度：P3
  • 失败场景：
  DISPOSITION.md 第 63 行引用仅简写为 T-082 RESULTS.md，未给出完整仓库路径（evidence/2026-
  10-15-batch15/T-082/RESULTS.md），查阅者需要检索附录才能确认其归属批次。
  ──────
  ## 三、审查结论

  T-149 候选严格遵循了用户“选项
  C（删除不再有价值的，其余标历史；仍是现行契约唯一守护者的不删，交用户）”的授权裁定：

  1. 判据应用严格一致：待决 10
  个文件均包含未被现行测试替代的有效检查，未为迎合全绿而静默删除；标历史 3
  个文件均被其他测试或 host 依赖，不能直接物理删除，且其自身假设确已过时。
  2. 标历史所选 revision 均有扎实的项目历史记录支撑。
  3. 变更范围极其干净，仅增 1 份索引文档和 3
  行注释，未修改任何逻辑代码，未破坏语法、模块导入或 shebang。
  4. HISTORICAL.md 定位准确，如实保留待决状态。
  5. 发现的 2 条 P3 属于稀疏检出说明与路径标注细节，不影响处置方案的正确性与安全性。

  T-149 REVIEW PASS
```
