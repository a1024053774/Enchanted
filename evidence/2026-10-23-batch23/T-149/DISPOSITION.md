# T-149-1 / a1：13 个历史测试的处置调查

2026-10-23；worker `b23-t149`；分支 `exec/t149`；调查起点 `a981ba5643abc4bca5f6df57a62dc1f7d3344d13`。

状态：**INCOMPLETE**（调查完成，处置方案待执行主控确认；尚未删除、标记或迁移测试）。本文件是日期记录，不是 living doc。按任务卡，本轮提交只包含本文件。

建议：**删除 0 个，标历史 3 个，待决 10 个**。没有发现一份能以现有证据确认“整份已无价值”、同时可安全解除调用依赖的文件。过时断言与有效检查混在同一文件，不能因前者失败而删除后者。待决表示未找到覆盖全部有效检查的现行全绿替代，不宣称已证明全仓绝无其他覆盖。

## 范围与判据

- 目标：用同一判据调查任务卡列出的 13 个文件，给出契约、现行覆盖、引用方和可复核的处置理由。
- 非目标：不改产品，不改测试断言，不迁移测试，不运行真实 CLI、Electron、模型或历史复跑脚本，不改历史证据。
- 完成条件：13 项均有建议；覆盖标到检查名；部分覆盖明确写出缺口；引用包含稀疏工作树外的受控文件；提交后停在确认点。
- 主要未知：有些有效检查仅存在于这些已不能在当前契约下完整运行的套件中。是否迁移、另立回归或接受缺口，应交用户；本 worker 不把选项 C 扩为选项 A。

**Ubiquitous language**：本文“现行覆盖”指仍符合现行契约、且有 main 通过记录的具体检查；“历史”不等于“现行通过”；“待决 / needs-decision”均指保留文件并交用户。**Tracer bullet**：本轮只调查既有全链路，不新建实现切片。**Deep modules**：保留已有依赖关系，不为处置新增包装器、平行测试或兼容路径。

依据：本票、任务卡、`COMMON.md`、用户选 C 的转达 `20261023T181318Z-ideation-answer-001.md`、T-148 上报 `20261023T172046Z-worker:b23-t148-issue-001.md`；现行契约交叉核对 T-112、T-118、T-119、T-124、T-127、T-130、T-139、T-141、T-146，以及 `intent.md`、`CONTEXT.md` 和实际调用代码。

## 现行通过证据与边界

以下 E1～E7 均取自已有 main 回归，**不是本 worker 新跑的结果**：

`evidence/2026-10-23-batch23/merge-1/run-20261023T180034Z/NOTE.md` 记录：执行 `zsh RUN-MERGE-REGRESSION-06.sh 7436f6014`，32 项 exit=0。其绑定版本为 `7436f60148a44bac9f3557deb75ce8a28987b92a`；`t141-green.json` 自报相同 `source_revision`。调查时对该版本→起点及起点→本地 main 的 `workbench/` 做 Git 内容差异核对，均无差异（命令见下文），故可用于识别目前已有覆盖；不能替未来处置候选的回归背书。

| 编号 | 现行测试与确切检查名 | main 通过摘要（相对上述 run 目录） | 能证明什么 / 不能证明什么 |
| --- | --- | --- | --- |
| E1 | `test_t141_launch_contract.mjs`：`claude_network_mcp_write_boundary`、`codex_inherits_user_configuration`；`test_t141_reviewer_contract.mjs`：`Claude Code_production_launch_accepted`、`Codex_production_launch_accepted`、`Codex_worker_and_monitor_inherit_user_trust`、`Codex_broader_writes_rejected`、`Claude Code_broader_writes_rejected` 等 | `t141-launch-contract.json`、`t141-reviewer-contract.json`，PASS | 新 argv 构造与门禁拒收边界；无真实原生沙箱证明，也不覆盖设置持久化与优先级。 |
| E2 | `test_t141_startup_signal.mjs`：`split_native_packet_releases_trusted_startup`、`later_idle_does_not_replace_stop`、`captured_untrusted_screen_only_selects_open_restricted` | `t141-startup-contract.json`，PASS | 已信任 worker 用 native ready 放行；受限打开只能完成屏幕选择；不验证 T-112 表单改变下一次原生请求。 |
| E3 | `test_t127_codex_home_e2e.py`：`worker_runs_in_user_home`、`trusted_worker_starts_directly`、`foreign_session_in_home_ignored`、`reviewer_same_home_untrusted_copy`、`reviewer_mutations_ran_in_copy`、`reviewer_cannot_write_outside_copy`、`review_passed`、`integrated_into_working_branch` | `t127.json`，PASS | 真实 Codex、用户式隔离 home、交付/审查/集成及副本外拒写；不覆盖所有历史质量负例或 Claude Git 元数据攻击矩阵。 |
| E4 | `test_t131_parallel_workers_e2e.py`：`T-1_delivery_is_its_own`、`T-2_delivery_is_its_own`、`both_reviews_passed_on_their_own_task`、`second_integration_reverified_on_new_head` | `t131.json`，PASS | 真实 Claude 并行交付、尾注归属、审查和新 HEAD 上重新验证；默认绿态没有执行 `--foreign-ref` 分支，不算共享 refs 反例通过。 |
| E5 | `test_t139_selection.mjs`：`same_credential_on_reselection`、`inactive_input_rejected`、`ended_read_only_no_credential`、`foreign_window_cannot_read_parked_key`、`window_close_revokes_active_and_parked_credentials`；`test_t139_t143_views_perf_e2e.py`：`switch_retains_xterm_and_input_credential`、`numbered_output_once_after_switch`、`focused_input_routes_correctly` | `t139-selection.json`、`t139-t143-candidate.json`，PASS | 现行项目/任务/agent 选择、凭据隔离和保留视图；不等于每个 IPC channel 的 iframe/未知窗口拒收或应用关窗期间的逐字节回放证明。 |
| E6 | `test_t146_session_end.mjs`：`foreign_session_rejected`、`foreign_cwd_rejected`、`stop_is_idle_not_exit`、`session_end_without_prompt_is_ended_with_live_terminal`；`test_t146_reviewer_hooks.mjs`：`approved_session_end_hook_accepted`、`missing_session_end_rejected`、`shell_write_expansion_rejected` | `t146-session-end.json`、`t146-reviewer-hooks.json`，PASS | SessionEnd/Stop 区分及审查启动钩子；没有“匹配 active submission 后重复 Stop 只产生一次 pane_idle”的等价检查。 |
| E7 | `test_t141_loosened_limits_e2e.py`：`codex_inherits_trust_tools_proxy`、`claude_mcp_discovered`、`claude_user_mcp_executed`、`T-C_write_boundary_and_shell_temp`、`T-D_write_boundary_and_shell_temp`、`T-C_gate_accepts_new_reviewer_argv`、`T-D_gate_accepts_new_reviewer_argv`、两种 CLI 的 `reviewer_rejects_two_independent_bad_results`；`test_t121_role_request_e2e.py`：`controller_command_refused_without_role`、`approved_controller_command_reaches_gate` | `t141-green.json`、`t121.json`，PASS | 现行网络/MCP/写入边界、角色申请入口与双 CLI 审查；不能代替质量串的评分必填、三次拒绝、协议损坏、结束核对竞争等专项。 |

## 逐文件处置表

所有文件均在 `workbench/tests/`。引用列给出直接可执行依赖；完整文本命中与历史复跑脚本见附录 R1～R13。没有把过时套件的旧 PASS 当成现行覆盖。

| 文件 | 建议处置 | 守护契约、有效性与理由 | 覆盖它的现行测试 / 尚缺的检查 | 引用方 |
| --- | --- | --- | --- | --- |
| `test_t112_execution.mjs` | **待决 / needs-decision** | 五角色默认、SQLite 重开持久化、覆盖 > 设置 > 默认、角色隔离、拒绝权限字段、未知 effort 透传、启动失败不被 shell 掩盖均仍有效。75 行的 reviewer 关网络要求被 T-141 废弃；reviewer 仍应受写入边界限制。不能删整份。 | E1 只替代启动权限部分；E3 覆盖普通 Codex 交付。未找到现行全绿替代 `restart_persists_role_settings`、`field_override_precedence`、`permission_fields_rejected`、`unsupported_effort_not_coerced`、`native_startup_failure_recorded`，也不能用其旧变异结果补称当前通过。 | `test_t112_closed_fixture.py:22`、`test_t112_counterfactuals.py:38`；R1。 |
| `diagnose_t112_reviewer.py` | **标历史，保留依赖** | 固定 Codex 0.162.1 的真实 reviewer 写入 good/bad 对照及 Responses 回执诊断。143～145、178～181 行要求关网络，当前不成立；但真实副本外拒写仍有价值。该文件还提供 `run_reviewer_case` 给原生 runner 与离线回放，不能作为独立重复脚本直接删。 | E3 的 `reviewer_mutations_ran_in_copy`、`reviewer_cannot_write_outside_copy` 和 E7 覆盖现行副本/临时文件边界；E1 覆盖新 argv。改 effort 后的原生请求证明仍归 R8 的待决缺口，不声称已被替代。离线 handler 回放本身不因历史标记而删除或跳过。 | `run_t112_native.py:19`、`test_t112_request_replay.py:11`，在本文件 116 行启动 `t112_reviewer_record.mjs`；R2。 |
| `test_quality_tracer_e2e.py` | **待决 / needs-decision** | 47～52 行的关网络、独立 reviewer home 已废弃；显式独立审查、评分必填与一次写入、修复后重跑全串、第三次拒绝暂停、拒绝复用原生审查会话仍有效。Tracer 还是多个其他测试的基类。 | E3/E4/E7 仅有正常交付、独立审查与集成。未找到现行全绿替代 `TRACER-SCORE-REQUIRED`、`TRACER-SCORE-FIELDS`、`TRACER-SCORE-ONCE`、`TRACER-REVIEW-STRICT-JSON`、`TRACER-THIRD-STOP`、`TRACER-REVIEW-REUSE`、`TRACER-DELIVERY-CONTEXT`。 | `test_bad_worker_e2e.py`、`test_protected_acceptance_e2e.py`、`test_quality_legacy_e2e.py`、`test_quality_widen_e2e.py`、`test_review_worktree_lifecycle_e2e.py`、`test_s3_quality_joint_e2e.py`、`test_t082_parent_launch_e2e.py`、`test_t082_review_boundary_e2e.py`；4 个 runner，详 R3。 |
| `test_t082_review_boundary_e2e.py` | **待决 / needs-decision** | 32～35 行旧关网络参数无效；审查副本建立/清理、共享 refs 变化作废、review_requirements.workspace 绑定、必须先完成结束核对再允许集成仍有效。 | E1 覆盖新启动参数拒收，E3/E7 覆盖正常副本与审查。缺少当前全绿的 `REVIEW-REFS-INVALIDATE`、`REVIEW-REQUIREMENTS-WORKSPACE`、`REVIEW-END-BEFORE-INTEGRATE`（含 held socket 正/负对照）和 `T082-DIRTY-END-INVALIDATE`。E4 默认绿态不执行 foreign-ref 负例。 | `run_t082_boundary.py:44`、`test_t090_review_worker_boundary_e2e.py:11`；继承 R3；历史 `T-090/run-host.py` 等见 R4。 |
| `run_pane_lifecycle.py` | **待决 / needs-decision** | 真实 CLI 的 PTY 字节随应用关窗继续增长、重开后无丢失回放、关后台后原 attempt 保持中断事实、只读输入不能注入，仍是现行能力。359 行关网络断言、必须外置盘和旧 UI/ready_rev 假设已过时。 | E5 的切视图保留 xterm/输出只覆盖应用内切换；E6 的结束态不覆盖窗口重开、后台重启和精确 PTY 回放。未找到当前 main 全绿的同等“关闭整个应用期间仍增长 + 重开逐字节一致 + 原 attempt 中断”组合。不能把切换视图通过当作替代。 | 当前 `workbench/` 无调用者；历史外部运行入口和源码快照脚本见 R5。 |
| `run_worker_delivery.py` | **待决 / needs-decision** | 249 行的关网络、固定旧 CLI，以及 verify 后不经独立审查/评分直接 integrate 的早期流程已废弃；然而真实 Stop 批次只处理一遍、重复交付回放、门禁回执只注入一次且仅产生无工具收据回合、实际 turn_context→delivery→尾注仍有效。 | E3/E4 覆盖交付身份、尾注和现行集成；`test_relay_core.ts` 源码包含重复/不完整/错误身份拒绝，但本轮未核对到其现行 main 全绿证据，且它只测 relay 边界。未找到当前全绿替代原生“一个 Stop 批次→一条通知→无工具收据回合”的专项，因此不删。 | 当前 `workbench/` 无调用者；历史 `T-075/card-3/outside-sandbox.sh:39`、`T-080/run_final01_outside.py:27` 等见 R6。 |
| `test_t122_claude_worker_e2e.py` | **待决 / needs-decision** | 379 行要求 `--strict-mcp-config`、103 行同名 mutant 定位已不符合 T-141；但 Claude worker 的 Git 元数据/拼接 git/-c/项目钩子攻击矩阵、审查 CLI/模型/Fast/钩子绑定与协议失败留据仍有效。 | E4/E7 覆盖 Claude 正常交付、尾注和一般越界写；E1/E6 覆盖部分 reviewer argv/钩子拒收。未找到当前全绿替代 `git_metadata_closed_to_shell`、`shell_cannot_move_working_branch`、`project_hook_not_run`、`only_the_trailered_commit`、`skipped_project_hooks_recorded` 及 `--review-result malformed/rejected` / reviewer-case 矩阵。不能把普通路径拒写扩成这些攻击已覆盖。 | `workbench/README.md:223`；历史 T-123～T-136 的 e2e/commands.sh 见 R7。 |
| `run_t112_native.py` | **待决 / needs-decision** | 213 行仍等 worker 的 `codex_restricted_opened`，T-141 后已信任 worker 无此事件；但真实设置 DOM→SQLite→下一次派发 argv→原生首轮请求、覆盖优先级与未知 effort 原样透传仍有效。 | E2 替代启动信号；E3/E7 证明当前 Codex 能启动和交付。没有替代 `real_dom_save_changes_next_native_dispatch`、`override_beats_saved_medium`、`unknown_effort_unchanged_in_launch_argv_record_and_first_request` 的现行全绿证明。`closed_fixture_launches` 另被测试导入，删除会破坏离线检查。 | `test_t112_closed_fixture.py:15`；导入 R2、间接用 R9；原生回归入口见 R8。 |
| `t112_reviewer_record.mjs` | **标历史，保留依赖** | 这是 R2 的真实 daemon/reviewer 启动 host，不是独立验收。62 行的等待名本身不是断言旧屏幕必出现；实际是等 `pane.started`。但其配置、固定老 CLI 与 R2 的关网络 oracle 共同构成历史 T-112 探针，不能把改检查名当成迁移完成。 | E2 覆盖 native-ready 与受限屏幕的分工；E3 覆盖现行 reviewer 原生身份、副本与放行。`test_t112_reviewer_startup.mjs` 针对此旧 driver 的 VM 仿真仍假定显式 `release()`，不作为当前产品通过证明。 | `diagnose_t112_reviewer.py:116`、`test_t112_reviewer_startup.mjs:7`；R9。 |
| `controlled_quality_pty.ts` | **标历史，保留依赖** | 通用受控 PTY/process 边界：51 行总发 Open restricted 屏，第一条 Enter 只开目录，之后不发 native idle；与 T-141 信任继承和 native-ready 放行冲突。它没有自己的门禁 verdict/oracle，不能把其各 host 的业务检查一起废弃。 | E2 直接覆盖现行 startup 协议；E3/E4/E7 为真实 CLI 正常链路。R3/R4 等业务负例没有因此获得替代，保留原 fixture 与 imports，禁止把标记解释为这些套件已通过或已迁移。 | `quality_chain_host.ts:6`、`daemon_acceptance_host.ts:10`、`conflict_acceptance_host.ts:5`、`multiturn_identity_host.ts:6`；`run_daemon_acceptance.py:102` 复制它，`legacy_review_runtime.ts:2` 注释引用；R10。 |
| `test_t091_pane_ipc.mjs` | **待决 / needs-decision** | 旧“默认显示当前 worker”、全局 handler/bridge 名单、project/task/pane 选择模型已被 T-139 等改变；跨窗 key/iframe/未知窗口拒收、不能错误发凭据、关闭与身份请求竞争、空布局与持久化仍是有效边界。 | E5 只覆盖现行选择、parked key 和凭据撤销；不能替代 `iframe_and_unknown_window_rejected_for_all_handlers`、关闭时未完成 `window_open` 的迟到凭据撤销，以及全 IPC 面的负例。旧 handler 数量名单应历史化，但不能连这些检查一并静默停用。 | `run_t104_shell_ui.py:59`；历史回归/审查脚本很多，完整见 R11。 |
| `test_t078_claude_signals.ts` | **待决 / needs-decision** | 入口存在性、同一登记提交绑定 UserPromptSubmit/Stop、重复 Stop 不重复 idle、异会话拒收。`startController` 在当前源码仍存在，不能称其 API 已删除。旧 fixture 缺少现在非 controller 角色要读取的 transcript/模型事实，不能用 ENOENT 证明契约废弃。 | E6 覆盖异会话和 Stop≠SessionEnd；E4 覆盖真实 Claude 正常完成。尚未找到 main 全绿替代 `real_hook_shape_matches_one_registered_submission` 内“有 active 的匹配 Stop 清空后，重复 Stop 的 pane_idle 总数仍为 1”。单纯 `stop_is_idle_not_exit` 无 active，不等价。 | `regenerate_t078_p1.py:98` 的源码归档清单；旧 T-108 复跑脚本见 R12。 |
| `test_t108_questions.mjs` | **待决 / needs-decision** | Codex worker 等 `waiting_controller_answer` 的旧期望已被 T-124“worker 经 issue 提问，原生提问不登记等待”取代；但 Claude 主控的问答关联、畸形/过期/外来 hook、permission 伪造、答复记录/写入竞争和重复答复拒收仍有效。 | E6 只覆盖 SessionEnd 身份；E7 的 controller answer 是 issue，不是原生 AskUserQuestion。未找到现行全绿替代 `hookFailureContracts()` 的 Claude 部分、`answerLifecycleContracts()` 或此入口的原生提问断言；两 helper 只有这个入口调用，不能因入口先在 Codex 矩阵失败，就断言后续有效场景已获得守护。 | `workbench/README.md:1088`；自身导入两个 `t108_*_contracts.mjs`；历史调用见 R13。 |

## 历史标记方案（待确认后才实施）

仅对表中 3 个辅助文件新增统一文件头：“历史测试：只针对 <revision>，当前 main 不跑”；新增 `workbench/tests/HISTORICAL.md`，列出角色、调用者、历史 revision 和现行替代。保留导出、函数体、断言与导入，不把依赖它们的待决测试移到新契约。

| 文件 | 历史 revision | 选择依据与复跑边界 |
| --- | --- | --- |
| `diagnose_t112_reviewer.py`、`t112_reviewer_record.mjs` | `5f19062f52154914123e3796fdff87caaa22fc1f` | `evidence/2026-10-20-batch18/T-112/outside-merge-t112-native-03.json`：status PASS、source_head 为此版本；只对应 T-112 当时的完整源码与 CLI/夹具，不证明当前文件与旧源码任意混用可跑。较早 `outside-reviewer-diag-04.json` 的 PASS 另绑定 `8a6d3f6fed955f2ec1e196a1c3afae55e7e420fd`，不能混称一个候选。 |
| `controlled_quality_pty.ts` | `5f7f9816eb9a996377c5b255695244d99c0259e7` | T-082 `RESULTS.md` 明确绑定该冻结候选的结束核对/启动拒收独审；该 helper 对应当时受控输入层，不声称全部 T-076 runner 在该版本全绿。历史复跑必须同时取该 revision 的 host、测试及产品，不能只把 helper 接到当前 main。 |

`RUN-MERGE-REGRESSION-06.sh` 没有直接调用这 13 个文件；已查看 E1～E7 的相关 imports，现行回归路径使用 `scripted_claude.py`、`t112_native_api.py` 等，不导入上述 3 个历史 helper。`workbench/package.json` 也没有 glob 自动收集 tests 的脚本。新增索引须明确：当前 main 回归不调历史 host；需要离线导入 R2 的 handler 回放，不属于运行历史原生 host，不能一刀切阻止 import。

以下问题保留给主控转用户，不自行实施：

1. 对表中 10 项，确认是否另票迁移其未替代的有效检查；本票不改其断言或默默按历史全部停用。
2. R3、R4、R10 是成组依赖。若用户决定退休整个旧质量测试树，需要另行明确其外围调用者的处置范围；本卡只有“删除必须修的引用”权限，不能借清引用删除更多有效测试。
3. R7 与 R8 含真实原生端到端的独特证明。已有一般交付绿态不能替代其 Git 攻击矩阵或设置→请求透传验证。

## 已有失败记录

- `evidence/2026-10-23-batch23/T-148/ISSUE-stale-oracles.md` 与上述 worker 上报保存旧网络/home/MCP/startup 条件；本轮核对实际源码，不修它们。
- `evidence/2026-10-23-batch23/T-146/t078-session-end-01.json`：`controller_runtime_entry_exists`、`wrong_native_session_is_rejected` 为 PASS；中间检查因缺 `native-session.jsonl` 为 INCOMPLETE。它是 fixture/契约演进问题，不是当前产品不处理 Stop 的红态。
- `evidence/2026-10-23-batch23/T-146/existing-regression-issue.md` 与 `t108-baseline-comparison-01.json`：T-108 在基线与候选均有相同旧 Codex 等待状态期望，不能把它解释为 T-146 引入的回归，也不能据此忽略 Claude 的有效断言。
- T-091 的旧布局失败见 `T-139-T-143/t091-issue.md` 和 `T-138/t091-baseline-03.json` 等；保留原记录，不为当前 handler 名单改断言。

## 调查与后续验证

已执行：

```sh
python3 /Users/luckye/Documents/SKILLS/project-map-skill/project-map/scripts/project_map.py status --root .
git diff --quiet 7436f6014 a981ba564 -- workbench
git diff --quiet a981ba564 main -- workbench
```

三项退出均为 0；status 为 Problems 0 / Stale living docs 0。以上内容差异比较用于判断已有 main 覆盖是否仍对应同一源码，没有计算指纹。

引用调查先对工作树执行 `rg --json -F --hidden --no-ignore -g '!.git' -g '!node_modules' -g '!__pycache__' -g '!DISPOSITION.md' <文件名去扩展名> .`，随后对整个 Git index 执行 `git grep --cached -n -I -z -F <文件名去扩展名> -- .`，补齐 sparse checkout 外的文件。Python 汇总路径与行号，保留全部文本命中；去扩展名能同时找到 Python import，不能只查带 `.py` 的文件名。附录为两次结果的并集，不包含本文件自身；区分引用与实际调用，未执行任何匹配到的命令。

本轮**没有运行测试、构建、红态或变异**，也没有为退休而弱化任何 oracle。调查只是文档提交，不能报告 T-149 整体验收 PASS。确认后的候选仍须按任务卡：检查引用、跑可在沙箱运行的现行 node/py 项，提交新的 `RUN-OUTSIDE-01.sh` 请求主控在沙箱外完整执行回归 06 的项目，并保留新摘要。当前历史 PASS 不替该候选背书。

本轮停点：提交此文件后回报 `PLAN <提交号>`，等待执行主控确认；不继续修改测试、索引或调用者。

## 全仓引用附录

下列列表包括源码调用、文档提及、旧源码快照和日志/摘要中的路径字符串。后两类不是当前 main 的可执行依赖。历史 `evidence/` 中的复跑/审查脚本只列出，不修改；稀疏 checkout 外的条目从 Git index 读取。按文件去扩展名检索可能包括注释或变异定位，不冒称都发生运行时调用。

### R1 `test_t112_execution.mjs`

<details>
<summary>工作台 / 其他当前文件：2 个文件</summary>

```text
workbench/tests/test_t112_closed_fixture.py:22
workbench/tests/test_t112_counterfactuals.py:38
```

</details>

<details>
<summary>历史 evidence 可执行文件（含复跑脚本与冻结源码）：4 个文件</summary>

```text
evidence/2026-10-20-batch18/T-112/REVIEW-OUTSIDE-01.sh:143
evidence/2026-10-20-batch18/T-112/RUN-MERGE-REGRESSIONS-13.py:52
evidence/2026-10-20-batch18/T-112/RUN-OUTSIDE-COMMIT-01.sh:18
evidence/2026-10-20-batch18/T-112/RUN-OUTSIDE-COMMIT-02.sh:18
```

</details>

<details>
<summary>其余文本命中（治理记录、报告、摘要、日志等）：80 个文件</summary>

```text
.project-map/inbox/20261023T172046Z-worker:b23-t148-issue-001.md:6,20
.project-map/inbox/20261023T181004Z-executor-report-001.md:30
.project-map/inbox/20261023T181318Z-ideation-answer-001.md:17
.project-map/tickets/T-112-launch-model-effort-configurable.md:61
.project-map/tickets/T-118-cli-versions-shell-markers-restore.md:28
.project-map/tickets/T-148-stale-fixtures-after-t141.md:42
.project-map/tickets/T-149-retire-stale-historical-tests.md:18
evidence/2026-10-20-batch18/T-112/RESULTS.md:155
evidence/2026-10-20-batch18/T-112/closed-fixture-green-01.json:19,23
evidence/2026-10-20-batch18/T-112/closed-fixture-red-01.json:15,19
evidence/2026-10-20-batch18/T-112/controller-defaults-red-01.json:5,15
evidence/2026-10-20-batch18/T-112/execution-01.json:5,23
evidence/2026-10-20-batch18/T-112/execution-02.json:5
evidence/2026-10-20-batch18/T-112/execution-03.json:5
evidence/2026-10-20-batch18/T-112/execution-04.json:5
evidence/2026-10-20-batch18/T-112/execution-final-05.json:5
evidence/2026-10-20-batch18/T-112/execution-rev2-06.json:5
evidence/2026-10-20-batch18/T-112/execution-rev2-final-07.json:5
evidence/2026-10-20-batch18/T-112/independent-review-01.md:10,96
evidence/2026-10-20-batch18/T-112/merge-execution-01.json:5
evidence/2026-10-20-batch18/T-112/merge-local-regressions-01.json:62
evidence/2026-10-20-batch18/T-112/mutants-02.json:9,22,35,48
evidence/2026-10-20-batch18/T-112/mutants-03.json:9,22,35,48,61
evidence/2026-10-20-batch18/T-112/mutants-final-04.json:9,22,35,48,61
evidence/2026-10-20-batch18/T-112/mutants-rev2-05.json:9,22,35,48,61
evidence/2026-10-20-batch18/T-112/outside-merge-execution-01.json:5
evidence/2026-10-20-batch18/T-112/outside-merge-execution-02.json:5
evidence/2026-10-20-batch18/T-112/outside-merge-execution-03.json:5
evidence/2026-10-20-batch18/T-112/outside-merge-regressions-01.json:73,77
evidence/2026-10-20-batch18/T-112/outside-merge-regressions-02.json:85,89
evidence/2026-10-20-batch18/T-112/outside-merge-regressions-03.json:85,89
evidence/2026-10-20-batch18/T-112/outside-merge-t112-native-03.json:5421
evidence/2026-10-20-batch18/T-112/outside-native-02.json:183,187
evidence/2026-10-20-batch18/T-112/outside-native-03.json:183,187
evidence/2026-10-20-batch18/T-112/outside-native-05.json:4503
evidence/2026-10-20-batch18/T-112/outside-native-06.json:4762
evidence/2026-10-20-batch18/T-112/outside-native-07.json:5391
evidence/2026-10-20-batch18/T-112/search-rev8-01.json:24
evidence/2026-10-20-batch18/T-112/search-rev9-01.json:22
evidence/2026-10-21-batch19/T-118/RESULTS.md:8
evidence/2026-10-21-batch19/T-118/codex-version-green-02.json:5
evidence/2026-10-21-batch19/T-118/codex-version-green-03.json:5
evidence/2026-10-21-batch19/T-118/codex-version-green.json:5
evidence/2026-10-21-batch19/T-118/codex-version-red-HEAD.json:5,24
evidence/2026-10-21-batch19/T-122/regress-t112-execution-01.json:5
evidence/2026-10-21-batch19/T-122/regress-t112-execution-01.log:1
evidence/2026-10-21-batch19/T-122/regress-t112-execution-02.json:5
evidence/2026-10-21-batch19/T-122/regress-t112-execution-02.log:1
evidence/2026-10-21-batch19/T-122/regress-t112-execution-03.json:5
evidence/2026-10-21-batch19/T-122/regress-t112-execution-03.log:1
evidence/2026-10-21-batch19/T-122/regress-t112-execution-04.json:5
evidence/2026-10-21-batch19/T-122/regress-t112-execution-04.log:1
evidence/2026-10-21-batch19/T-122/regress-t112-execution-05.json:5
evidence/2026-10-21-batch19/T-122/regress-t112-execution-05.log:1
evidence/2026-10-21-batch19/T-122/regress-t112-execution-06.json:5
evidence/2026-10-21-batch19/T-122/regress-t112-execution-06.log:1
evidence/2026-10-21-batch19/T-122/regress-t112-native-03.json:91
evidence/2026-10-21-batch19/T-122/regress-t112-native-04.json:5429
evidence/2026-10-21-batch19/T-122/regress-t112-native-05.json:5310
evidence/2026-10-21-batch19/T-122/regress-t112-native-06.json:5429
evidence/2026-10-21-batch19/T-122/regress-t112-native-07.json:91
evidence/2026-10-21-batch19/T-122/regress-t112-native-08.json:233
evidence/2026-10-21-batch19/T-122/regress-t112-native-09.json:5429
evidence/2026-10-21-batch19/T-122/regress-t112-native-10.json:5417
evidence/2026-10-21-batch19/T-122/regress-t112-native-11.json:5415
evidence/2026-10-22-batch20/T-127/regress-t112-execution-01.json:5
evidence/2026-10-22-batch20/T-127/regress-t112-execution-01.log:1
evidence/2026-10-22-batch20/T-127/regress-t112-execution-02.json:5
evidence/2026-10-22-batch20/T-127/regress-t112-execution-02.log:1
evidence/2026-10-22-batch20/T-127/regress-t112-execution-03.json:5
evidence/2026-10-22-batch20/T-127/regress-t112-execution-03.log:1
evidence/2026-10-22-batch20/T-127/regress-t112-execution-04.json:5
evidence/2026-10-22-batch20/T-127/regress-t112-execution-04.log:1
evidence/2026-10-22-batch20/T-127/regress-t112-native-01.json:5333
evidence/2026-10-22-batch20/T-127/regress-t112-native-02.json:5323
evidence/2026-10-22-batch20/T-127/regress-t112-native-03.json:5337
evidence/2026-10-23-batch23/T-148/ISSUE-stale-oracles.md:7
evidence/2026-10-23-batch23/T-148/RESULTS.md:55
evidence/2026-10-23-batch23/T-148/review-agy-01.md:215
evidence/2026-10-23-batch23/T-148/stale-contract-search.txt:5
```

</details>

### R2 `diagnose_t112_reviewer.py`

<details>
<summary>工作台 / 其他当前文件：2 个文件</summary>

```text
workbench/tests/run_t112_native.py:19
workbench/tests/test_t112_request_replay.py:11
```

</details>

<details>
<summary>历史 evidence 可执行文件（含复跑脚本与冻结源码）：9 个文件</summary>

```text
evidence/2026-10-20-batch18/T-112/RUN-OUTSIDE-COMMIT-04.sh:18
evidence/2026-10-20-batch18/T-112/RUN-OUTSIDE-COMMIT-05.sh:18
evidence/2026-10-20-batch18/T-112/RUN-OUTSIDE-COMMIT-06.sh:18
evidence/2026-10-20-batch18/T-112/RUN-OUTSIDE-COMMIT-07.sh:19
evidence/2026-10-20-batch18/T-112/RUN-OUTSIDE-COMMIT-08.sh:18
evidence/2026-10-20-batch18/T-112/RUN-OUTSIDE-REVIEWER-DIAG-01.sh:6
evidence/2026-10-20-batch18/T-112/RUN-OUTSIDE-REVIEWER-DIAG-02.sh:6
evidence/2026-10-20-batch18/T-112/RUN-OUTSIDE-REVIEWER-DIAG-03.sh:6
evidence/2026-10-20-batch18/T-112/RUN-OUTSIDE-REVIEWER-DIAG-04.sh:6
```

</details>

<details>
<summary>其余文本命中（治理记录、报告、摘要、日志等）：14 个文件</summary>

```text
.project-map/inbox/20261023T172046Z-worker:b23-t148-issue-001.md:20
.project-map/inbox/20261023T181004Z-executor-report-001.md:30
.project-map/inbox/20261023T181318Z-ideation-answer-001.md:17
.project-map/tickets/T-148-stale-fixtures-after-t141.md:42
.project-map/tickets/T-149-retire-stale-historical-tests.md:18
evidence/2026-10-20-batch18/T-112/native-rev8-static-01.json:6,28,32
evidence/2026-10-20-batch18/T-112/outside-reviewer-diag-01.json:996
evidence/2026-10-20-batch18/T-112/outside-reviewer-diag-02.json:58
evidence/2026-10-20-batch18/T-112/outside-reviewer-diag-03.json:657
evidence/2026-10-20-batch18/T-112/protocol-rev7-static-final-01.json:6
evidence/2026-10-20-batch18/T-112/protocol-rev7-static-final-02.json:6
evidence/2026-10-23-batch23/T-148/ISSUE-stale-oracles.md:7
evidence/2026-10-23-batch23/T-148/RESULTS.md:55
evidence/2026-10-23-batch23/T-148/stale-contract-search.txt:3
```

</details>

### R3 `test_quality_tracer_e2e.py`

<details>
<summary>工作台 / 其他当前文件：12 个文件</summary>

```text
workbench/tests/run_t076_launch_policy.py:70
workbench/tests/run_t076_quality_green.py:15,70
workbench/tests/run_t076_quality_widen.py:125
workbench/tests/run_t081_bad_worker_suite.py:293
workbench/tests/test_bad_worker_e2e.py:11
workbench/tests/test_protected_acceptance_e2e.py:9
workbench/tests/test_quality_legacy_e2e.py:7
workbench/tests/test_quality_widen_e2e.py:21
workbench/tests/test_review_worktree_lifecycle_e2e.py:14
workbench/tests/test_s3_quality_joint_e2e.py:13
workbench/tests/test_t082_parent_launch_e2e.py:18
workbench/tests/test_t082_review_boundary_e2e.py:14
```

</details>

<details>
<summary>历史 evidence 可执行文件（含复跑脚本与冻结源码）：30 个文件</summary>

```text
evidence/2026-10-11-batch13/T-076/card-2/delivery-review-01/candidate/workbench/tests/run_t076_launch_policy.py:60
evidence/2026-10-11-batch13/T-076/card-2/delivery-review-01/candidate/workbench/tests/run_t076_quality_green.py:15,70
evidence/2026-10-11-batch13/T-076/card-2/delivery-review-01/candidate/workbench/tests/run_t076_quality_widen.py:125
evidence/2026-10-11-batch13/T-076/card-2/delivery-review-01/candidate/workbench/tests/test_quality_legacy_e2e.py:7
evidence/2026-10-11-batch13/T-076/card-2/delivery-review-01/candidate/workbench/tests/test_quality_widen_e2e.py:21
evidence/2026-10-11-batch13/T-076/card-2/prepare-p-review-approval.py:97
evidence/2026-10-11-batch13/T-076/card-2/prepare-real-delivery.py:69
evidence/2026-10-11-batch13/T-077/check-rebase-final-02-preparation.py:41
evidence/2026-10-11-batch13/T-077/check-rebase-final-03-preparation.py:41
evidence/2026-10-11-batch13/T-077/check-rebase-final-04-preparation.py:41
evidence/2026-10-11-batch13/T-077/check-rebase-final-05-preparation.py:42
evidence/2026-10-11-batch13/T-077/check-rebase-final-preparation.py:41
evidence/2026-10-11-batch13/T-077/final05-boundaries-before/preflight-at-run.py:38
evidence/2026-10-11-batch13/T-077/final05-preflight-before/preflight-at-run.py:127
evidence/2026-10-11-batch13/T-077/preflight-boundaries-05.py:39
evidence/2026-10-11-batch13/T-077/preflight-final-05.py:155
evidence/2026-10-11-batch13/T-077/probe-fixture-helpers-05.py:16
evidence/2026-10-11-batch13/T-077/run-rebase-final-01.py:192
evidence/2026-10-11-batch13/T-077/run-rebase-final-02.py:231
evidence/2026-10-11-batch13/T-077/run-rebase-final-03.py:247
evidence/2026-10-11-batch13/T-077/run-rebase-final-04.py:258
evidence/2026-10-11-batch13/T-077/run-rebase-final-05.py:265
evidence/2026-10-14-batch14/T-080/run_final01_outside.py:29,322
evidence/2026-10-14-batch14/T-080/run_red_outside.py:142
evidence/2026-10-15-batch15/T-082/OUTSIDE-COMMANDS-06.sh:40,43
evidence/2026-10-15-batch15/T-082/OUTSIDE-COMMANDS-07.sh:20
evidence/2026-10-15-batch15/T-082/OUTSIDE-COMMANDS-09.sh:24
evidence/2026-10-15-batch15/T-082/OUTSIDE-COMMANDS-11.sh:147
evidence/2026-10-15-batch15/T-082/REVIEW-OUTSIDE-01.sh:33,291
evidence/2026-10-15-batch15/T-082/REVIEW-OUTSIDE-02.sh:37,166,193
```

</details>

<details>
<summary>其余文本命中（治理记录、报告、摘要、日志等）：365 个文件</summary>

```text
.project-map/inbox/20261015T131159Z-ideation-answer-001.md:19
.project-map/inbox/20261023T172046Z-worker:b23-t148-issue-001.md:21
.project-map/inbox/20261023T181004Z-executor-report-001.md:30
.project-map/inbox/20261023T181318Z-ideation-answer-001.md:17
.project-map/tickets/T-148-stale-fixtures-after-t141.md:42
.project-map/tickets/T-149-retire-stale-historical-tests.md:18
evidence/2026-10-11-batch13/T-076/card-2/RESULTS.md:64
evidence/2026-10-11-batch13/T-076/card-2/assertion-hunks.md:96
evidence/2026-10-11-batch13/T-076/card-2/default-tier-change-01/run_t076_launch_policy.py.before:60
evidence/2026-10-11-batch13/T-076/card-2/delivery-review-01/manifest.json:137
evidence/2026-10-11-batch13/T-076/card-2/evidence-staging-check-01/run.json:51,325,372
evidence/2026-10-11-batch13/T-076/card-2/focused-preparation-checks.json:14
evidence/2026-10-11-batch13/T-076/card-2/legacy-preparation-checks.json:45,370
evidence/2026-10-11-batch13/T-076/card-2/legacy-ready-checks-01.json:43,369
evidence/2026-10-11-batch13/T-076/card-2/legacy-ready-checks-02.json:43,371
evidence/2026-10-11-batch13/T-076/card-2/legacy-ready-checks-03.json:43,371
evidence/2026-10-11-batch13/T-076/card-2/legacy-ready-checks-04.json:43,371
evidence/2026-10-11-batch13/T-076/card-2/legacy-ready-checks-05.json:43,371
evidence/2026-10-11-batch13/T-076/card-2/legacy-ready-checks-06.json:43,371
evidence/2026-10-11-batch13/T-076/card-2/managed-flow-repair-01/test_quality_legacy_e2e.py.before:7
evidence/2026-10-11-batch13/T-076/card-2/outside-delivery-review-01/commands.jsonl:3
evidence/2026-10-11-batch13/T-076/card-2/outside-delivery-review-01/native-sessions/2026/10/13/rollout-2026-10-13T12-00-00-01a135fd-fd26-7693-a738-ad75036b220e.jsonl:26,29,36,39,89,90,163,164,166,171,172,174
evidence/2026-10-11-batch13/T-076/card-2/outside-delivery-review-01/setup.json:69
evidence/2026-10-11-batch13/T-076/card-2/outside-focused-tracer-01/commands.jsonl:9,10,11,12,19,20,23,24,27,28,31,32,35,36,39,40,43,44,47,48,51,52
evidence/2026-10-11-batch13/T-076/card-2/outside-focused-tracer-01/identity-refusals-not-scored.receipt.json:8,30,1158
evidence/2026-10-11-batch13/T-076/card-2/outside-focused-tracer-01/identity-refusals-not-scored/run.json:4,1132
evidence/2026-10-11-batch13/T-076/card-2/outside-focused-tracer-01/identity-refusals-not-scored/tracer_identity_score/case.json:1118
evidence/2026-10-11-batch13/T-076/card-2/outside-focused-tracer-01/markdown-extracted.receipt.json:8,30,761
evidence/2026-10-11-batch13/T-076/card-2/outside-focused-tracer-01/markdown-extracted/run.json:4,735
evidence/2026-10-11-batch13/T-076/card-2/outside-focused-tracer-01/markdown-extracted/tracer_malformed_review/case.json:721
evidence/2026-10-11-batch13/T-076/card-2/outside-focused-tracer-01/old-native-accepted.receipt.json:8,30,1506
evidence/2026-10-11-batch13/T-076/card-2/outside-focused-tracer-01/old-native-accepted/run.json:4,1480
evidence/2026-10-11-batch13/T-076/card-2/outside-focused-tracer-01/old-native-accepted/tracer_reused_native/case.json:1466
evidence/2026-10-11-batch13/T-076/card-2/outside-focused-tracer-01/prior-turn-score-facts.receipt.json:8,30,150
evidence/2026-10-11-batch13/T-076/card-2/outside-focused-tracer-01/prior-turn-score-facts/run.json:4,124
evidence/2026-10-11-batch13/T-076/card-2/outside-focused-tracer-01/prior-turn-score-facts/tracer_missing_delivery_context/case.json:110
evidence/2026-10-11-batch13/T-076/card-2/outside-focused-tracer-01/protocol-controls.receipt.json:8,48
evidence/2026-10-11-batch13/T-076/card-2/outside-focused-tracer-01/protocol-controls/run.json:4
evidence/2026-10-11-batch13/T-076/card-2/outside-focused-tracer-01/reviewer-writable.receipt.json:8,30,628
evidence/2026-10-11-batch13/T-076/card-2/outside-focused-tracer-01/reviewer-writable/run.json:4,602
evidence/2026-10-11-batch13/T-076/card-2/outside-focused-tracer-01/reviewer-writable/tracer_success/case.json:588
evidence/2026-10-11-batch13/T-076/card-2/outside-focused-tracer-01/run.json:21,43,2870,2910,26226,26248,26979,27632,27654,29130,30145,30167,30472,31548,31570,32301,32954,32976,34044,34729,34751,35831,36550,36572,37170,37963,37985,38105,38767,38789,39917
evidence/2026-10-11-batch13/T-076/card-2/outside-focused-tracer-01/score-fields-unchecked.receipt.json:8,30,1110
evidence/2026-10-11-batch13/T-076/card-2/outside-focused-tracer-01/score-fields-unchecked/run.json:4,1084
evidence/2026-10-11-batch13/T-076/card-2/outside-focused-tracer-01/score-fields-unchecked/tracer_score_required/case.json:1070
evidence/2026-10-11-batch13/T-076/card-2/outside-focused-tracer-01/score-invented.receipt.json:8,30,1098
evidence/2026-10-11-batch13/T-076/card-2/outside-focused-tracer-01/score-invented/run.json:4,1072
evidence/2026-10-11-batch13/T-076/card-2/outside-focused-tracer-01/score-invented/tracer_score_required/case.json:1058
evidence/2026-10-11-batch13/T-076/card-2/outside-focused-tracer-01/third-rejection-keeps-writing.receipt.json:8,30,335
evidence/2026-10-11-batch13/T-076/card-2/outside-focused-tracer-01/third-rejection-keeps-writing/run.json:4,309
evidence/2026-10-11-batch13/T-076/card-2/outside-focused-tracer-01/third-rejection-keeps-writing/tracer_third_rejection/case.json:295
evidence/2026-10-11-batch13/T-076/card-2/outside-focused-tracer-01/tracer.receipt.json:8,30
evidence/2026-10-11-batch13/T-076/card-2/outside-focused-tracer-01/tracer/run.json:4
evidence/2026-10-11-batch13/T-076/card-2/outside-focused-tracer-01/wrong-c-accepted.receipt.json:8,30,761
evidence/2026-10-11-batch13/T-076/card-2/outside-focused-tracer-01/wrong-c-accepted/run.json:4,735
evidence/2026-10-11-batch13/T-076/card-2/outside-focused-tracer-01/wrong-c-accepted/tracer_wrong_candidate/case.json:721
evidence/2026-10-11-batch13/T-076/card-2/outside-launch-policy-01/commands.jsonl:3,4,5,6,7,8,9,10
evidence/2026-10-11-batch13/T-076/card-2/outside-launch-policy-01/default-tier-green/run.json:4
evidence/2026-10-11-batch13/T-076/card-2/outside-launch-policy-01/readonly-argv-mutant/run.json:4,502
evidence/2026-10-11-batch13/T-076/card-2/outside-launch-policy-01/readonly-argv-mutant/tracer_launch_policy_reviewer/case.json:488
evidence/2026-10-11-batch13/T-076/card-2/outside-launch-policy-01/reviewer-fast-red/run.json:4,618
evidence/2026-10-11-batch13/T-076/card-2/outside-launch-policy-01/reviewer-fast-red/tracer_launch_policy_reviewer/case.json:604
evidence/2026-10-11-batch13/T-076/card-2/outside-launch-policy-01/worker-fast-red/run.json:4,128
evidence/2026-10-11-batch13/T-076/card-2/outside-launch-policy-01/worker-fast-red/tracer_launch_policy_worker/case.json:114
evidence/2026-10-11-batch13/T-076/card-2/outside-launch-policy-default-01/commands.jsonl:3,4,5,6,7,8,9,10,11,12
evidence/2026-10-11-batch13/T-076/card-2/outside-launch-policy-default-01/default-tier-green/run.json:4
evidence/2026-10-11-batch13/T-076/card-2/outside-launch-policy-default-01/priority-argv-mutant/run.json:4,128
evidence/2026-10-11-batch13/T-076/card-2/outside-launch-policy-default-01/priority-argv-mutant/tracer_launch_policy_worker/case.json:114
evidence/2026-10-11-batch13/T-076/card-2/outside-launch-policy-default-01/readonly-argv-mutant/run.json:4,504
evidence/2026-10-11-batch13/T-076/card-2/outside-launch-policy-default-01/readonly-argv-mutant/tracer_launch_policy_reviewer/case.json:490
evidence/2026-10-11-batch13/T-076/card-2/outside-launch-policy-default-01/reviewer-missing-override-red/run.json:4,614
evidence/2026-10-11-batch13/T-076/card-2/outside-launch-policy-default-01/reviewer-missing-override-red/tracer_launch_policy_reviewer/case.json:600
evidence/2026-10-11-batch13/T-076/card-2/outside-launch-policy-default-01/worker-missing-override-red/run.json:4,126
evidence/2026-10-11-batch13/T-076/card-2/outside-launch-policy-default-01/worker-missing-override-red/tracer_launch_policy_worker/case.json:112
evidence/2026-10-11-batch13/T-076/card-2/outside-legacy-green-01/source.json:90
evidence/2026-10-11-batch13/T-076/card-2/outside-legacy-green-02/source.json:90
evidence/2026-10-11-batch13/T-076/card-2/outside-legacy-green-03/source.json:90
evidence/2026-10-11-batch13/T-076/card-2/outside-legacy-green-04/source.json:90
evidence/2026-10-11-batch13/T-076/card-2/outside-legacy-green-05/source.json:90
evidence/2026-10-11-batch13/T-076/card-2/outside-legacy-green-06/source.json:90
evidence/2026-10-11-batch13/T-076/card-2/outside-reviewer-green-01/commands.jsonl:11,12
evidence/2026-10-11-batch13/T-076/card-2/outside-reviewer-green-01/reviewer-normal-paths.receipt.json:9,34
evidence/2026-10-11-batch13/T-076/card-2/outside-reviewer-green-01/reviewer-normal-paths/run.json:4
evidence/2026-10-11-batch13/T-076/card-2/outside-reviewer-green-01/run.json:13699,13724
evidence/2026-10-11-batch13/T-076/card-2/p-review-01/source-manifest.json:112
evidence/2026-10-11-batch13/T-076/card-2/p-review-02/source-manifest.json:113
evidence/2026-10-11-batch13/T-076/card-2/postcommit-readback-01/run.json:79
evidence/2026-10-11-batch13/T-076/card-2/real-delivery-01/source-manifest.json:114
evidence/2026-10-11-batch13/T-076/card-2/real-delivery-02/source-manifest.json:114
evidence/2026-10-11-batch13/T-076/card-2/real-delivery-preparation-01/source-manifest.json:114
evidence/2026-10-11-batch13/T-076/card-2/real-delivery-preparation-02/source-manifest.json:114
evidence/2026-10-11-batch13/T-076/card-2/real-delivery-preparation-03/source-manifest.json:114
evidence/2026-10-11-batch13/T-076/card-2/reviewer-preparation-checks.json:447
evidence/2026-10-11-batch13/T-076/card-2/source-commit.json:44
evidence/2026-10-11-batch13/T-076/card-2/source-staging-check-02/run.json:51
evidence/2026-10-11-batch13/T-076/card-2/widen-preparation-checks.json:447
evidence/2026-10-11-batch13/T-077/conflict-red-final-01-preparation-01/plan.json:223
evidence/2026-10-11-batch13/T-077/conflict-red-final-01-preparation-02/plan.json:256
evidence/2026-10-11-batch13/T-077/final05-boundaries-before/command-output/00005.stdout.bin:1
evidence/2026-10-11-batch13/T-077/final05-boundaries-before/commands.jsonl:9,10
evidence/2026-10-11-batch13/T-077/final05-boundaries-before/run.json:52,56
evidence/2026-10-11-batch13/T-077/final05-preflight-after/run.json:4019,4037,4315,4324,4333,4342,4351,4360,4369,4378,4387,4396,4450,4463,4472,4481,4490,4499,4510,4519,4528,4537,4548,4557,4566,4575,4586,4595,4604,4613,4898,4907,4916,4925,4934,4943,4952,4961,4970,4979,4991,5000,5009,5018,5027,5036,5045,5054,5063,5072,5081,5090,5099,5108,5117,5126,5135,5146,5155,5164,5173,5182,5191,5200,5209,5218,5227,5236,5248,5257,5266,5277,5286,5295,5306,5315,5324,5336,5345,5354,5363,5399,5408,5417,5428,5437,5446,5455,5464,5473,5482,5491,5500,5511,5520,5529,5540,5549,5558,5567,5576,5585,5596,5605,5614,5623,5632,5641,5650,5659,5668,5677,5686,5695,5706,5715,5724,5733,5742,5751,5760,5772,5781,5790,5801,5810,5819,5828,5837,5846,5855,5864,5873,5882,5891,5900,5909,5918,5927,5936,5945,5954,5965,5974,5983,5992,6001,6010,6019,6028,6039,6048,6057,6069,6078,6087,6176,6626,6639,6648,6657,6666,6675,6686,6695,6704,6713,6724,6733,6742,6751,6762,6771,6780,6789,7485,7496,7505,7514,7523,7532,7541,7702,7711,7720,7729,7738,7747,7756,7765,7774,7783,7792,7801,7810,7819,7828,9917,10455,10464,10473,10482,10491,10500,10509,10518,10527,10536,10545,10554,10563,10572,10581,10599,10610,10619,10628,10637,10646,10655,10664,10677,10686,10695,10704,10713,10724,10733,10742,10751,10762,10771,10780,10789,10800
evidence/2026-10-11-batch13/T-077/final05-preflight-before/run.json:4014,4032,4310,4319,4328,4337,4346,4355,4364,4373,4382,4391,4445,4458,4467,4476,4485,4494,4505,4514,4523,4532,4543,4552,4561,4570,4581,4590,4599,4608,4893,4902,4911,4920,4929,4938,4947,4956,4965,4974,4986,4995,5004,5013,5022,5031,5040,5049,5058,5067,5076,5085,5094,5103,5112,5121,5130,5141,5150,5159,5168,5177,5186,5195,5204,5213,5222,5231,5243,5252,5261,5272,5281,5290,5301,5310,5319,5331,5340,5349,5358,5394,5403,5412,5423,5432,5441,5450,5459,5468,5477,5486,5495,5506,5515,5524,5535,5544,5553,5562,5571,5580,5591,5600,5609,5618,5627,5636,5645,5654,5663,5672,5681,5690,5701,5710,5719,5728,5737,5746,5755,5767,5776,5785,5796,5805,5814,5823,5832,5841,5850,5859,5868,5877,5886,5895,5904,5913,5922,5931,5940,5949,5960,5969,5978,5987,5996,6005,6014,6023,6034,6043,6052,6064,6073,6082,6171,6621,6634,6643,6652,6661,6670,6681,6690,6699,6708,6719,6728,6737,6746,6757,6766,6775,6784,7480,7491,7500,7509,7518,7527,7536,7697,7706,7715,7724,7733,7742,7751,7760,7769,7778,7787,7796,7805,7814,7823,9912,10450,10459,10468,10477,10486,10495,10504,10513,10522,10531,10540,10549,10558,10567,10576,10594,10605,10614,10623,10632,10641,10650,10659,10672,10681,10690,10699,10708,10719,10728,10737,10746,10757,10766,10775,10784,10795
evidence/2026-10-11-batch13/T-077/final05-preflight-complete/run.json:4193,4211,4489,4498,4507,4516,4525,4534,4543,4552,4561,4570,4624,4637,4646,4655,4664,4673,4684,4693,4702,4711,4722,4731,4740,4749,4760,4769,4778,4787,5072,5081,5090,5099,5108,5117,5126,5135,5144,5153,5165,5174,5183,5192,5201,5210,5219,5228,5237,5246,5255,5264,5273,5282,5291,5300,5309,5320,5329,5338,5347,5356,5365,5374,5383,5392,5401,5410,5422,5431,5440,5451,5460,5469,5480,5489,5498,5510,5519,5528,5537,5573,5582,5591,5602,5611,5620,5629,5638,5647,5656,5665,5674,5685,5694,5703,5714,5723,5732,5741,5750,5759,5770,5779,5788,5797,5806,5815,5824,5833,5842,5851,5860,5869,5880,5889,5898,5907,5916,5925,5934,5946,5955,5964,5975,5984,5993,6002,6011,6020,6029,6038,6047,6056,6065,6074,6083,6092,6101,6110,6119,6128,6139,6148,6157,6166,6175,6184,6193,6202,6213,6222,6231,6243,6252,6261,6350,6800,6813,6822,6831,6840,6849,6860,6869,6878,6887,6898,6907,6916,6925,6936,6945,6954,6963,7659,7670,7679,7688,7697,7706,7715,7876,7885,7894,7903,7912,7921,7930,7939,7948,7957,7966,7975,7984,7993,8002,10091,10629,10638,10647,10656,10665,10674,10683,10692,10701,10710,10719,10728,10737,10746,10755,10773,10784,10793,10802,10811,10820,10829,10838,10851,10860,10869,10878,10887,10898,10907,10916,10925,10936,10945,10954,10963,10974
evidence/2026-10-11-batch13/T-077/independent-review-product-01.diff:3698,3825
evidence/2026-10-11-batch13/T-077/outside-conflict-red-final-01/red-01/source-files.json:114
evidence/2026-10-11-batch13/T-077/outside-conflict-red-final-01/red-02/source-files.json:114
evidence/2026-10-11-batch13/T-077/outside-conflict-red-final-01/red-03/source-files.json:114
evidence/2026-10-11-batch13/T-077/outside-conflict-red-final-01/red-04/source-files.json:114
evidence/2026-10-11-batch13/T-077/outside-conflict-red-final-02-preparation/plan.json:258
evidence/2026-10-11-batch13/T-077/outside-conflict-red-final-02/candidate/source-files.json:114
evidence/2026-10-11-batch13/T-077/outside-conflict-red-final-02/red-01/source-files.json:114
evidence/2026-10-11-batch13/T-077/outside-conflict-red-final-02/red-02/source-files.json:114
evidence/2026-10-11-batch13/T-077/outside-conflict-red-final-02/red-03/source-files.json:114
evidence/2026-10-11-batch13/T-077/outside-conflict-red-final-02/red-04/source-files.json:114
evidence/2026-10-11-batch13/T-077/outside-conflict-red-final-02/red-05/source-files.json:114
evidence/2026-10-11-batch13/T-077/outside-conflict-red-final-02/red-06/source-files.json:114
evidence/2026-10-11-batch13/T-077/outside-conflict-red-final-02/red-07/source-files.json:114
evidence/2026-10-11-batch13/T-077/outside-rebase-final-01/conflict-red-01/source-files.json:113
evidence/2026-10-11-batch13/T-077/outside-rebase-final-01/conflict-red-02/source-files.json:113
evidence/2026-10-11-batch13/T-077/outside-rebase-final-01/conflict-red-03/source-files.json:113
evidence/2026-10-11-batch13/T-077/outside-rebase-final-01/conflict-red-04/source-files.json:113
evidence/2026-10-11-batch13/T-077/outside-rebase-final-01/conflict-red-05/source-files.json:113
evidence/2026-10-11-batch13/T-077/outside-rebase-final-01/conflict-red-06/source-files.json:113
evidence/2026-10-11-batch13/T-077/outside-rebase-final-01/conflict-red-07/source-files.json:113
evidence/2026-10-11-batch13/T-077/outside-rebase-final-01/s3-all/source-files.json:113
evidence/2026-10-11-batch13/T-077/outside-rebase-final-03/conflict-red-01/source-files.json:114
evidence/2026-10-11-batch13/T-077/outside-rebase-final-03/conflict-red-02/source-files.json:114
evidence/2026-10-11-batch13/T-077/outside-rebase-final-03/conflict-red-03/source-files.json:114
evidence/2026-10-11-batch13/T-077/outside-rebase-final-03/conflict-red-04/source-files.json:114
evidence/2026-10-11-batch13/T-077/outside-rebase-final-03/conflict-red-05/source-files.json:114
evidence/2026-10-11-batch13/T-077/outside-rebase-final-03/conflict-red-06/source-files.json:114
evidence/2026-10-11-batch13/T-077/outside-rebase-final-03/conflict-red-07/source-files.json:114
evidence/2026-10-11-batch13/T-077/outside-rebase-final-03/s3-all/source-files.json:114
evidence/2026-10-11-batch13/T-077/outside-rebase-final-04/conflict-red-01/source-files.json:114
evidence/2026-10-11-batch13/T-077/outside-rebase-final-04/conflict-red-02/source-files.json:114
evidence/2026-10-11-batch13/T-077/outside-rebase-final-04/conflict-red-03/source-files.json:114
evidence/2026-10-11-batch13/T-077/outside-rebase-final-04/conflict-red-04/source-files.json:114
evidence/2026-10-11-batch13/T-077/outside-rebase-final-04/conflict-red-05/source-files.json:114
evidence/2026-10-11-batch13/T-077/outside-rebase-final-04/conflict-red-06/source-files.json:114
evidence/2026-10-11-batch13/T-077/outside-rebase-final-04/conflict-red-07/source-files.json:114
evidence/2026-10-11-batch13/T-077/outside-rebase-final-04/s3-all/source-files.json:114
evidence/2026-10-11-batch13/T-077/outside-rebase-final-05/commands.jsonl:69,70
evidence/2026-10-11-batch13/T-077/outside-rebase-final-05/conflict-red-01/source-files.json:114
evidence/2026-10-11-batch13/T-077/outside-rebase-final-05/conflict-red-02/source-files.json:114
evidence/2026-10-11-batch13/T-077/outside-rebase-final-05/conflict-red-03/source-files.json:114
evidence/2026-10-11-batch13/T-077/outside-rebase-final-05/conflict-red-04/source-files.json:114
evidence/2026-10-11-batch13/T-077/outside-rebase-final-05/conflict-red-05/source-files.json:114
evidence/2026-10-11-batch13/T-077/outside-rebase-final-05/conflict-red-06/source-files.json:114
evidence/2026-10-11-batch13/T-077/outside-rebase-final-05/conflict-red-07/source-files.json:114
evidence/2026-10-11-batch13/T-077/outside-rebase-final-05/run.json:506
evidence/2026-10-11-batch13/T-077/outside-rebase-final-05/s3-all/source-files.json:114
evidence/2026-10-11-batch13/T-077/outside-rebase-final-05/t076-final-tracer.receipt.json:6
evidence/2026-10-11-batch13/T-077/outside-rebase-final-05/t076-final-tracer/run.json:4
evidence/2026-10-11-batch13/T-077/rebase-final-02-preparation-01/plan.json:191
evidence/2026-10-11-batch13/T-077/rebase-final-02-preparation-01/static-checks.json:10
evidence/2026-10-11-batch13/T-077/rebase-final-03-preparation-01/plan.json:192
evidence/2026-10-11-batch13/T-077/rebase-final-03-preparation-01/static-checks.json:10
evidence/2026-10-11-batch13/T-077/rebase-final-04-preparation-01/plan.json:193
evidence/2026-10-11-batch13/T-077/rebase-final-04-preparation-01/static-checks.json:11
evidence/2026-10-11-batch13/T-077/rebase-final-05-preparation-01/plan.json:207
evidence/2026-10-11-batch13/T-077/rebase-final-05-preparation-01/static-checks.json:11
evidence/2026-10-11-batch13/T-077/rebase-final-preparation-01/plan.json:182
evidence/2026-10-11-batch13/T-077/rebase-final-preparation-01/static-checks.json:10
evidence/2026-10-11-batch13/T-077/rebase-final-preparation-02/plan.json:182
evidence/2026-10-11-batch13/T-077/rebase-final-preparation-02/static-checks.json:10
evidence/2026-10-11-batch13/T-077/rebase-final-preparation-03/plan.json:182
evidence/2026-10-11-batch13/T-077/rebase-final-preparation-03/static-checks.json:10
evidence/2026-10-11-batch13/T-078/09b-a16-b1-executor-p1-01/source-files.json:206
evidence/2026-10-11-batch13/T-078/09b-a16-b1-ideation-p1-01/source-files.json:206
evidence/2026-10-11-batch13/T-078/09b-a16-materials-01/SOURCE.json:214
evidence/2026-10-11-batch13/T-078/09b-a16-materials-01/prepare.json:15
evidence/2026-10-11-batch13/T-078/09b-executable-materials-16-02/source-files.json:206
evidence/2026-10-11-batch13/T-078/09b-executable-materials-16-02/static-check.json:208
evidence/2026-10-11-batch13/T-078/09b-executable-materials-16/source-files.json:206
evidence/2026-10-11-batch13/T-078/09b-executable-materials-16/static-check.json:208
evidence/2026-10-11-batch13/T-078/09c-attempt-2-materials-01/SOURCE.json:246
evidence/2026-10-11-batch13/T-078/09c-attempt-2-materials-01/prepare.json:15
evidence/2026-10-11-batch13/T-078/09c-attempt-2-materials-02/SOURCE.json:250
evidence/2026-10-11-batch13/T-078/09c-attempt-2-materials-02/prepare.json:15
evidence/2026-10-11-batch13/T-078/09c-attempt-3-materials-01/prepare.json:15
evidence/2026-10-11-batch13/T-078/09c-c1-b1-executor-p1-01/source-files.json:206
evidence/2026-10-11-batch13/T-078/09c-c1-b1-ideation-p1-01/source-files.json:206
evidence/2026-10-11-batch13/T-078/09c-c2-b1-executor-p1-01/source-files.json:207
evidence/2026-10-11-batch13/T-078/09c-c2-b1-ideation-p1-01/source-files.json:207
evidence/2026-10-11-batch13/T-078/09c-c3-b1-executor-p1-01/source-files.json:210
evidence/2026-10-11-batch13/T-078/09c-c3-b1-ideation-p1-01/source-files.json:210
evidence/2026-10-11-batch13/T-078/09c-caffeinate-parity-rehearsal-01/flow/executor-p1/source-files.json:203
evidence/2026-10-11-batch13/T-078/09c-caffeinate-parity-rehearsal-01/flow/ideation-p1/source-files.json:203
evidence/2026-10-11-batch13/T-078/09c-caffeinate-parity-rehearsal-01/flow/packet/static-check.json:207
evidence/2026-10-11-batch13/T-078/09c-caffeinate-parity-rehearsal-02/flow/executor-p1/source-files.json:203
evidence/2026-10-11-batch13/T-078/09c-caffeinate-parity-rehearsal-02/flow/ideation-p1/source-files.json:203
evidence/2026-10-11-batch13/T-078/09c-caffeinate-parity-rehearsal-02/flow/packet/static-check.json:207
evidence/2026-10-11-batch13/T-078/09c-coordinator-rehearsal-01/real-chain-outside-01/flow/executor-p1/source-files.json:193
evidence/2026-10-11-batch13/T-078/09c-coordinator-rehearsal-01/real-chain-outside-01/flow/ideation-p1/source-files.json:193
evidence/2026-10-11-batch13/T-078/09c-coordinator-rehearsal-01/real-chain-outside-01/flow/packet/static-check.json:197
evidence/2026-10-11-batch13/T-078/09c-executable-materials-01/source-files.json:206
evidence/2026-10-11-batch13/T-078/09c-executable-materials-01/static-check.json:208
evidence/2026-10-11-batch13/T-078/09c-executable-materials-02/source-files.json:206
evidence/2026-10-11-batch13/T-078/09c-executable-materials-02/static-check.json:208
evidence/2026-10-11-batch13/T-078/09c-executable-materials-03/source-files.json:207
evidence/2026-10-11-batch13/T-078/09c-executable-materials-03/static-check.json:209
evidence/2026-10-11-batch13/T-078/09c-executable-materials-04/source-files.json:207
evidence/2026-10-11-batch13/T-078/09c-executable-materials-04/static-check.json:209
evidence/2026-10-11-batch13/T-078/09c-executable-materials-05/source-files.json:210
evidence/2026-10-11-batch13/T-078/09c-executable-materials-05/static-check.json:212
evidence/2026-10-11-batch13/T-078/09c-fix-01/real-chain-outside-01/flow/executor-p1/source-files.json:190
evidence/2026-10-11-batch13/T-078/09c-fix-01/real-chain-outside-01/flow/ideation-p1/source-files.json:190
evidence/2026-10-11-batch13/T-078/09c-fix-01/real-chain-outside-02/flow/executor-p1/source-files.json:190
evidence/2026-10-11-batch13/T-078/09c-fix-01/real-chain-outside-02/flow/ideation-p1/source-files.json:190
evidence/2026-10-11-batch13/T-078/09c-fix-01/real-chain-outside-03/flow/executor-p1/source-files.json:190
evidence/2026-10-11-batch13/T-078/09c-fix-01/real-chain-outside-03/flow/ideation-p1/source-files.json:190
evidence/2026-10-11-batch13/T-078/09c-materials-01/SOURCE.json:214
evidence/2026-10-11-batch13/T-078/09c-materials-01/prepare.json:15
evidence/2026-10-11-batch13/T-078/09c-topology-probe-run-01/ideation-p1/source-files.json:196
evidence/2026-10-11-batch13/T-078/09c-topology-probe-run-01/packet/static-check.json:200
evidence/2026-10-11-batch13/T-078/stage-a-readback-rebind-01/09B-prepare.json:15
evidence/2026-10-11-batch13/T-078/stage-a-readback-rebind-01/09C-prepare.json:15
evidence/2026-10-14-batch14/T-080/commit-03/run.json:67
evidence/2026-10-14-batch14/T-080/final-01/diff.stdout.bin:596,598,599
evidence/2026-10-14-batch14/T-080/final-01/source-manifest.json:23
evidence/2026-10-14-batch14/T-080/final-01/status.stdout.bin:17
evidence/2026-10-14-batch14/T-080/final-02/diff.stdout.bin:596,598,599
evidence/2026-10-14-batch14/T-080/final-02/run.json:282
evidence/2026-10-14-batch14/T-080/final-02/source-manifest.json:23
evidence/2026-10-14-batch14/T-080/final-02/status.stdout.bin:17
evidence/2026-10-14-batch14/T-080/final-02/t076-tracer.command.json:6
evidence/2026-10-14-batch14/T-080/final-02/t076-tracer.start.json:6
evidence/2026-10-14-batch14/T-080/final-02/t076-tracer/run.json:4
evidence/2026-10-14-batch14/T-080/final-02/t077-lifecycle-conflicts/source-files.json:115
evidence/2026-10-14-batch14/T-080/final-03/diff.stdout.bin:655,657,658
evidence/2026-10-14-batch14/T-080/final-03/run.json:318
evidence/2026-10-14-batch14/T-080/final-03/source-manifest.json:23
evidence/2026-10-14-batch14/T-080/final-03/status.stdout.bin:18
evidence/2026-10-14-batch14/T-080/final-03/t076-tracer.command.json:6
evidence/2026-10-14-batch14/T-080/final-03/t076-tracer.start.json:6
evidence/2026-10-14-batch14/T-080/final-03/t076-tracer/run.json:4
evidence/2026-10-14-batch14/T-080/final-03/t077-lifecycle-conflicts/source-files.json:115
evidence/2026-10-14-batch14/T-080/independent-review-01.completed.json:19
evidence/2026-10-14-batch14/T-080/independent-review-01.diff:1528,1821,1999,8829,9845,9847,9848,10216
evidence/2026-10-14-batch14/T-080/independent-review-01.request.json:37
evidence/2026-10-14-batch14/T-080/limit-replay-diagnosis-01.json:8
evidence/2026-10-14-batch14/T-080/run-repair-probe-01/diff.stdout.bin:596,598,599
evidence/2026-10-14-batch14/T-080/run-repair-probe-01/status.stdout.bin:17
evidence/2026-10-14-batch14/T-080/schema-readiness-01.json:42
evidence/2026-10-14-batch14/T-080/schema-readiness-02.json:51,101
evidence/2026-10-14-batch14/T-081/6e-full-01/source-manifest.json:101
evidence/2026-10-14-batch14/T-081/6e-full-02/source-manifest.json:101
evidence/2026-10-14-batch14/T-081/6e-regress-rest-02/t077-lifecycle-conflicts/source-files.json:141
evidence/2026-10-14-batch14/T-081/6e-regress-rest-03/progress.log:6,7
evidence/2026-10-14-batch14/T-081/6e-regress-rest-03/t076-tracer/run.json:4
evidence/2026-10-14-batch14/T-081/6e-regress-rest-03/t076-wide/run.json:37735
evidence/2026-10-14-batch14/T-081/6e-regress-rest-03/t076-wide/widen_score_after_cas/case.json:5332
evidence/2026-10-14-batch14/T-081/6e-rerun-01/source-manifest.json:101
evidence/2026-10-14-batch14/T-081/6e-rerun-rest-01/progress.log:14,15
evidence/2026-10-14-batch14/T-081/6e-rerun-rest-01/t076-tracer/run.json:4
evidence/2026-10-14-batch14/T-081/6e-rerun-rest-01/t076-wide/run.json:37719
evidence/2026-10-14-batch14/T-081/6e-rerun-rest-01/t076-wide/widen_score_after_cas/case.json:5332
evidence/2026-10-14-batch14/T-081/6e-rerun-rest-01/t077-lifecycle-conflicts/source-files.json:141
evidence/2026-10-14-batch14/T-081/full-01/source-manifest.json:80
evidence/2026-10-14-batch14/T-081/full-02/source-manifest.json:82
evidence/2026-10-14-batch14/T-081/full-03/commands.jsonl:103,104
evidence/2026-10-14-batch14/T-081/full-03/source-manifest.json:83
evidence/2026-10-14-batch14/T-081/full-03/t076-tracer/run.json:4
evidence/2026-10-14-batch14/T-081/full-03/t077-lifecycle-conflicts/source-files.json:121
evidence/2026-10-14-batch14/T-081/full-04/commands.jsonl:107,108
evidence/2026-10-14-batch14/T-081/full-04/source-manifest.json:85
evidence/2026-10-14-batch14/T-081/full-04/t076-tracer/run.json:4
evidence/2026-10-14-batch14/T-081/full-04/t077-lifecycle-conflicts/source-files.json:122
evidence/2026-10-14-batch14/T-081/full02-readiness-01/test_bad_worker_e2e.py.patch:13
evidence/2026-10-14-batch14/T-081/independent-review-03.md:112
evidence/2026-10-15-batch15/T-082/T076-BOUNDARY-MIGRATION.md:9
evidence/2026-10-15-batch15/T-082/T076-D3-ASSERTION-MAP.md:9,12
evidence/2026-10-15-batch15/T-082/outside-command-03-01/t076-quality-green/command-output/00003.stdout.bin:419,421,422
evidence/2026-10-15-batch15/T-082/outside-command-03-01/t076-quality-green/commands.jsonl:6
evidence/2026-10-15-batch15/T-082/outside-command-05-01/candidate-d3.patch.stdout.txt:3
evidence/2026-10-15-batch15/T-082/outside-command-05-01/candidate-t076-launch-policy-d3/commands.jsonl:3,4
evidence/2026-10-15-batch15/T-082/outside-command-05-01/candidate-t076-launch-policy-d3/worker-missing-override-red/run.json:4,20
evidence/2026-10-15-batch15/T-082/outside-command-05-01/candidate-t076-launch-policy-d3/worker-missing-override-red/tracer_launch_policy_worker/case.json:6
evidence/2026-10-15-batch15/T-082/outside-command-05-01/candidate-t077-review-worktree/cleanup_after_persisted_result/case.json:508
evidence/2026-10-15-batch15/T-082/outside-command-05-01/candidate-t077-review-worktree/run.json:520
evidence/2026-10-15-batch15/T-082/outside-command-05-01/parent-t076-launch-policy-old/commands.jsonl:3,4
evidence/2026-10-15-batch15/T-082/outside-command-05-01/parent-t076-launch-policy-old/worker-missing-override-red/run.json:4,20
evidence/2026-10-15-batch15/T-082/outside-command-05-01/parent-t076-launch-policy-old/worker-missing-override-red/tracer_launch_policy_worker/case.json:6
evidence/2026-10-15-batch15/T-082/outside-command-06-01/fixture-launch-policy.command.json:3
evidence/2026-10-15-batch15/T-082/outside-command-06-01/fixture-launch-policy/run.json:4
evidence/2026-10-15-batch15/T-082/outside-command-06-01/fixture-tracer.command.json:3
evidence/2026-10-15-batch15/T-082/outside-command-06-01/fixture-tracer/run.json:4
evidence/2026-10-15-batch15/T-082/outside-command-06-01/t076-launch-policy-candidate/commands.jsonl:3,4
evidence/2026-10-15-batch15/T-082/outside-command-06-01/t076-launch-policy-candidate/worker-missing-override-red/run.json:4,20
evidence/2026-10-15-batch15/T-082/outside-command-06-01/t076-launch-policy-candidate/worker-missing-override-red/tracer_launch_policy_worker/case.json:6
evidence/2026-10-15-batch15/T-082/outside-command-06-01/t076-quality-source-audit/command-output/00003.stdout.bin:419,421,422
evidence/2026-10-15-batch15/T-082/outside-command-06-01/t076-quality-source-audit/commands.jsonl:6
evidence/2026-10-15-batch15/T-082/outside-command-07-01/t076-property-tracer/run.json:4
evidence/2026-10-15-batch15/T-082/outside-command-08-01/t076-launch-policy-main/commands.jsonl:3,4
evidence/2026-10-15-batch15/T-082/outside-command-08-01/t076-launch-policy-main/worker-missing-override-red/run.json:4,20
evidence/2026-10-15-batch15/T-082/outside-command-08-01/t076-launch-policy-main/worker-missing-override-red/tracer_launch_policy_worker/case.json:6
evidence/2026-10-15-batch15/T-082/outside-command-09-01/run.json:28
evidence/2026-10-15-batch15/T-082/outside-command-09-01/t076-properties/run.json:4
evidence/2026-10-15-batch15/T-082/outside-command-11-01/13-t076-properties.assessment.json:8
evidence/2026-10-15-batch15/T-082/outside-command-11-01/13-t076-properties/run.json:4
evidence/2026-10-15-batch15/T-082/outside-command-11-01/15-t076-launch-policy/commands.jsonl:3,4,5,6,7,8,9,10,11,12
evidence/2026-10-15-batch15/T-082/outside-command-11-01/15-t076-launch-policy/default-tier-green/run.json:4
evidence/2026-10-15-batch15/T-082/outside-command-11-01/15-t076-launch-policy/priority-argv-mutant/run.json:4,128
evidence/2026-10-15-batch15/T-082/outside-command-11-01/15-t076-launch-policy/priority-argv-mutant/tracer_launch_policy_worker/case.json:114
evidence/2026-10-15-batch15/T-082/outside-command-11-01/15-t076-launch-policy/review-boundary-mutant/run.json:4,155
evidence/2026-10-15-batch15/T-082/outside-command-11-01/15-t076-launch-policy/review-boundary-mutant/tracer_launch_policy_reviewer/case.json:141
evidence/2026-10-15-batch15/T-082/outside-command-11-01/15-t076-launch-policy/reviewer-missing-override-red/run.json:4,700
evidence/2026-10-15-batch15/T-082/outside-command-11-01/15-t076-launch-policy/reviewer-missing-override-red/tracer_launch_policy_reviewer/case.json:686
evidence/2026-10-15-batch15/T-082/outside-command-11-01/15-t076-launch-policy/worker-missing-override-red/run.json:4,126
evidence/2026-10-15-batch15/T-082/outside-command-11-01/15-t076-launch-policy/worker-missing-override-red/tracer_launch_policy_worker/case.json:112
evidence/2026-10-15-batch15/T-082/outside-command-11-01/run.json:334
evidence/2026-10-15-batch15/T-082/outside-command-11-01/source.json:137
evidence/2026-10-15-batch15/T-082/outside-command-12-01/t076-launch-policy/commands.jsonl:3,4,5,6,7,8,9,10,11,12
evidence/2026-10-15-batch15/T-082/outside-command-12-01/t076-launch-policy/default-tier-green/run.json:4
evidence/2026-10-15-batch15/T-082/outside-command-12-01/t076-launch-policy/priority-argv-mutant/run.json:4,128
evidence/2026-10-15-batch15/T-082/outside-command-12-01/t076-launch-policy/priority-argv-mutant/tracer_launch_policy_worker/case.json:114
evidence/2026-10-15-batch15/T-082/outside-command-12-01/t076-launch-policy/review-boundary-mutant/run.json:4,155
evidence/2026-10-15-batch15/T-082/outside-command-12-01/t076-launch-policy/review-boundary-mutant/tracer_launch_policy_reviewer/case.json:141
evidence/2026-10-15-batch15/T-082/outside-command-12-01/t076-launch-policy/reviewer-missing-override-red/run.json:4,700
evidence/2026-10-15-batch15/T-082/outside-command-12-01/t076-launch-policy/reviewer-missing-override-red/tracer_launch_policy_reviewer/case.json:686
evidence/2026-10-15-batch15/T-082/outside-command-12-01/t076-launch-policy/worker-missing-override-red/run.json:4,126
evidence/2026-10-15-batch15/T-082/outside-command-12-01/t076-launch-policy/worker-missing-override-red/tracer_launch_policy_worker/case.json:112
evidence/2026-10-15-batch15/T-082/outside-command-13-01/02-success-green/commands.jsonl:3,4,5,6,7,8,9,10,11,12
evidence/2026-10-15-batch15/T-082/outside-command-13-01/02-success-green/default-tier-green/run.json:4
evidence/2026-10-15-batch15/T-082/outside-command-13-01/02-success-green/priority-argv-mutant/run.json:4,128
evidence/2026-10-15-batch15/T-082/outside-command-13-01/02-success-green/priority-argv-mutant/tracer_launch_policy_worker/case.json:114
evidence/2026-10-15-batch15/T-082/outside-command-13-01/02-success-green/review-boundary-mutant/run.json:4,155
evidence/2026-10-15-batch15/T-082/outside-command-13-01/02-success-green/review-boundary-mutant/tracer_launch_policy_reviewer/case.json:141
evidence/2026-10-15-batch15/T-082/outside-command-13-01/02-success-green/reviewer-missing-override-red/run.json:4,700
evidence/2026-10-15-batch15/T-082/outside-command-13-01/02-success-green/reviewer-missing-override-red/tracer_launch_policy_reviewer/case.json:686
evidence/2026-10-15-batch15/T-082/outside-command-13-01/02-success-green/worker-missing-override-red/run.json:4,126
evidence/2026-10-15-batch15/T-082/outside-command-13-01/02-success-green/worker-missing-override-red/tracer_launch_policy_worker/case.json:112
evidence/2026-10-15-batch15/T-082/t076-assertion-changes.patch:65,67,68
evidence/2026-10-15-batch15/T-084/regression-03/worktree/source-files.json:115
evidence/2026-10-15-batch15/T-086/RESULTS.md:5,93,98,106
evidence/2026-10-15-batch15/T-086/baseline-quality-tracer-loaded/command.txt:3
evidence/2026-10-15-batch15/T-086/baseline-quality-tracer-loaded/run.json:4
evidence/2026-10-15-batch15/T-086/baseline-widen-wide-loaded/run.json:37735
evidence/2026-10-15-batch15/T-086/baseline-widen-wide-loaded/widen_score_after_cas/case.json:5332
evidence/2026-10-15-batch15/T-086/conflict-suite-01/source-files.json:115
evidence/2026-10-15-batch15/T-086/green-01/source-files.json:115
evidence/2026-10-15-batch15/T-086/independent-review-01.md:12,82
evidence/2026-10-15-batch15/T-086/independent-review-02.md:96,103
evidence/2026-10-15-batch15/T-086/lifecycle-managed/source-files.json:115
evidence/2026-10-15-batch15/T-086/quality-tracer/command.txt:2
evidence/2026-10-15-batch15/T-086/quality-tracer/run.json:4
evidence/2026-10-15-batch15/T-086/quality-widen-wide/run.json:37767
evidence/2026-10-15-batch15/T-086/quality-widen-wide/widen_score_after_cas/case.json:5332
evidence/2026-10-15-batch15/T-086/red-01/source-files.json:115
evidence/2026-10-15-batch15/T-086/rework-conflict-suite/source-files.json:115
evidence/2026-10-15-batch15/T-086/rework-green-01/source-files.json:115
evidence/2026-10-15-batch15/T-086/rework-m1/source-files.json:115
evidence/2026-10-15-batch15/T-086/rework-m2/source-files.json:115
evidence/2026-10-15-batch15/T-086/rework-m3/source-files.json:115
evidence/2026-10-15-batch15/T-086/rework-m4/source-files.json:115
evidence/2026-10-15-batch15/T-086/rework-m5/source-files.json:115
evidence/2026-10-15-batch15/T-086/rework-red-01/source-files.json:115
evidence/2026-10-16-batch16/T-089/s3-baseline-local-01/cas/assertion-scope.json:2017
evidence/2026-10-19-batch17/T-105/python39-check-setup-failure-01.json:15,16
evidence/2026-10-22-batch20/T-127/RESULTS.md:94
evidence/2026-10-22-batch20/T-127/regress-release-head-01.archive.json:6
evidence/2026-10-23-batch23/T-148/ISSUE-stale-oracles.md:8
evidence/2026-10-23-batch23/T-148/RESULTS.md:55
evidence/2026-10-23-batch23/T-148/stale-contract-search.txt:23,24,25
```

</details>

### R4 `test_t082_review_boundary_e2e.py`

<details>
<summary>工作台 / 其他当前文件：2 个文件</summary>

```text
workbench/tests/run_t082_boundary.py:44
workbench/tests/test_t090_review_worker_boundary_e2e.py:11
```

</details>

<details>
<summary>历史 evidence 可执行文件（含复跑脚本与冻结源码）：10 个文件</summary>

```text
evidence/2026-10-11-batch13/T-078/merge-main-3-outside-02/fixture-source/workbench/tests/run_t082_boundary.py:44
evidence/2026-10-11-batch13/T-078/merge-main-3/run-regressions.py:36
evidence/2026-10-15-batch15/T-082/OUTSIDE-COMMANDS-03.sh:37
evidence/2026-10-15-batch15/T-082/OUTSIDE-COMMANDS-04.sh:46
evidence/2026-10-15-batch15/T-082/OUTSIDE-COMMANDS-09.sh:23
evidence/2026-10-15-batch15/T-082/OUTSIDE-COMMANDS-11.sh:120
evidence/2026-10-15-batch15/T-082/REVIEW-OUTSIDE-01.sh:35,186,289,340,342,345,347,350,363
evidence/2026-10-15-batch15/T-082/REVIEW-OUTSIDE-02.sh:39,138,146,152,158,164
evidence/2026-10-16-batch16/T-089/replay_t086.py:36
evidence/2026-10-16-batch16/T-090/run-host.py:208,228
```

</details>

<details>
<summary>其余文本命中（治理记录、报告、摘要、日志等）：144 个文件</summary>

```text
.project-map/inbox/20261023T172046Z-worker:b23-t148-issue-001.md:21
.project-map/inbox/20261023T181004Z-executor-report-001.md:30
.project-map/inbox/20261023T181318Z-ideation-answer-001.md:17
.project-map/tickets/T-148-stale-fixtures-after-t141.md:42
.project-map/tickets/T-149-retire-stale-historical-tests.md:18
evidence/2026-10-11-batch13/T-078/09b-a16-b1-executor-p1-01/source-files.json:296
evidence/2026-10-11-batch13/T-078/09b-a16-b1-ideation-p1-01/source-files.json:296
evidence/2026-10-11-batch13/T-078/09b-a16-materials-01/SOURCE.json:304
evidence/2026-10-11-batch13/T-078/09b-a16-materials-01/prepare.json:15
evidence/2026-10-11-batch13/T-078/09b-executable-materials-16-02/source-files.json:296
evidence/2026-10-11-batch13/T-078/09b-executable-materials-16-02/static-check.json:298
evidence/2026-10-11-batch13/T-078/09b-executable-materials-16/source-files.json:296
evidence/2026-10-11-batch13/T-078/09b-executable-materials-16/static-check.json:298
evidence/2026-10-11-batch13/T-078/09c-attempt-2-materials-01/SOURCE.json:342
evidence/2026-10-11-batch13/T-078/09c-attempt-2-materials-01/prepare.json:15
evidence/2026-10-11-batch13/T-078/09c-attempt-2-materials-02/SOURCE.json:348
evidence/2026-10-11-batch13/T-078/09c-attempt-2-materials-02/prepare.json:15
evidence/2026-10-11-batch13/T-078/09c-attempt-3-materials-01/prepare.json:15
evidence/2026-10-11-batch13/T-078/09c-c1-b1-executor-p1-01/source-files.json:296
evidence/2026-10-11-batch13/T-078/09c-c1-b1-ideation-p1-01/source-files.json:296
evidence/2026-10-11-batch13/T-078/09c-c2-b1-executor-p1-01/source-files.json:305
evidence/2026-10-11-batch13/T-078/09c-c2-b1-ideation-p1-01/source-files.json:305
evidence/2026-10-11-batch13/T-078/09c-c3-b1-executor-p1-01/source-files.json:317
evidence/2026-10-11-batch13/T-078/09c-c3-b1-ideation-p1-01/source-files.json:317
evidence/2026-10-11-batch13/T-078/09c-caffeinate-parity-rehearsal-01/flow/executor-p1/source-files.json:316
evidence/2026-10-11-batch13/T-078/09c-caffeinate-parity-rehearsal-01/flow/ideation-p1/source-files.json:316
evidence/2026-10-11-batch13/T-078/09c-caffeinate-parity-rehearsal-01/flow/packet/static-check.json:320
evidence/2026-10-11-batch13/T-078/09c-caffeinate-parity-rehearsal-02/flow/executor-p1/source-files.json:317
evidence/2026-10-11-batch13/T-078/09c-caffeinate-parity-rehearsal-02/flow/ideation-p1/source-files.json:317
evidence/2026-10-11-batch13/T-078/09c-caffeinate-parity-rehearsal-02/flow/packet/static-check.json:321
evidence/2026-10-11-batch13/T-078/09c-coordinator-rehearsal-01/real-chain-outside-01/flow/executor-p1/source-files.json:298
evidence/2026-10-11-batch13/T-078/09c-coordinator-rehearsal-01/real-chain-outside-01/flow/ideation-p1/source-files.json:298
evidence/2026-10-11-batch13/T-078/09c-coordinator-rehearsal-01/real-chain-outside-01/flow/packet/static-check.json:302
evidence/2026-10-11-batch13/T-078/09c-executable-materials-01/source-files.json:296
evidence/2026-10-11-batch13/T-078/09c-executable-materials-01/static-check.json:298
evidence/2026-10-11-batch13/T-078/09c-executable-materials-02/source-files.json:296
evidence/2026-10-11-batch13/T-078/09c-executable-materials-02/static-check.json:298
evidence/2026-10-11-batch13/T-078/09c-executable-materials-03/source-files.json:303
evidence/2026-10-11-batch13/T-078/09c-executable-materials-03/static-check.json:305
evidence/2026-10-11-batch13/T-078/09c-executable-materials-04/source-files.json:305
evidence/2026-10-11-batch13/T-078/09c-executable-materials-04/static-check.json:307
evidence/2026-10-11-batch13/T-078/09c-executable-materials-05/source-files.json:317
evidence/2026-10-11-batch13/T-078/09c-executable-materials-05/static-check.json:319
evidence/2026-10-11-batch13/T-078/09c-fix-01/real-chain-outside-01/flow/executor-p1/source-files.json:290
evidence/2026-10-11-batch13/T-078/09c-fix-01/real-chain-outside-01/flow/ideation-p1/source-files.json:290
evidence/2026-10-11-batch13/T-078/09c-fix-01/real-chain-outside-02/flow/executor-p1/source-files.json:291
evidence/2026-10-11-batch13/T-078/09c-fix-01/real-chain-outside-02/flow/ideation-p1/source-files.json:291
evidence/2026-10-11-batch13/T-078/09c-fix-01/real-chain-outside-03/flow/executor-p1/source-files.json:292
evidence/2026-10-11-batch13/T-078/09c-fix-01/real-chain-outside-03/flow/ideation-p1/source-files.json:292
evidence/2026-10-11-batch13/T-078/09c-materials-01/SOURCE.json:304
evidence/2026-10-11-batch13/T-078/09c-materials-01/prepare.json:15
evidence/2026-10-11-batch13/T-078/09c-topology-probe-run-01/ideation-p1/source-files.json:303
evidence/2026-10-11-batch13/T-078/09c-topology-probe-run-01/packet/static-check.json:307
evidence/2026-10-11-batch13/T-078/merge-main-3-fix-01/preflight-01.stdout.txt:18,42
evidence/2026-10-11-batch13/T-078/merge-main-3-outside-01/t082-launch/launch-boundary-refused-network-enabled/run.json:4
evidence/2026-10-11-batch13/T-078/merge-main-3-outside-01/t082-launch/launch-boundary-refused-readonly-argv/run.json:4
evidence/2026-10-11-batch13/T-078/merge-main-3-outside-01/t082-launch/launch-boundary-refused-tmp-writable/run.json:4
evidence/2026-10-11-batch13/T-078/merge-main-3-outside-01/t082-launch/launch-boundary-refused-wrong-workspace/run.json:4
evidence/2026-10-11-batch13/T-078/merge-main-3-outside-01/t082-launch/run.json:13,27,127,141,241,255,355,369,469,483
evidence/2026-10-11-batch13/T-078/merge-main-3-outside-01/t082-launch/tracer_review_copy/run.json:4
evidence/2026-10-11-batch13/T-078/merge-main-3-outside-02/result.json:33
evidence/2026-10-11-batch13/T-078/merge-main-3-outside-02/t082-end/run.json:4
evidence/2026-10-11-batch13/T-078/merge-main-3-outside-02/t082-launch/launch-boundary-refused-network-enabled/run.json:4
evidence/2026-10-11-batch13/T-078/merge-main-3-outside-02/t082-launch/launch-boundary-refused-readonly-argv/run.json:4
evidence/2026-10-11-batch13/T-078/merge-main-3-outside-02/t082-launch/launch-boundary-refused-tmp-writable/run.json:4
evidence/2026-10-11-batch13/T-078/merge-main-3-outside-02/t082-launch/launch-boundary-refused-wrong-workspace/run.json:4
evidence/2026-10-11-batch13/T-078/merge-main-3-outside-02/t082-launch/run.json:13,27,6025,6039,10681,10695,15353,15367,20025,20039
evidence/2026-10-11-batch13/T-078/merge-main-3-outside-02/t082-launch/tracer_review_copy/run.json:4
evidence/2026-10-11-batch13/T-078/merge-main-3/regression-preflight-01.stdout.txt:18,91
evidence/2026-10-11-batch13/T-078/stage-a-readback-rebind-01/09B-prepare.json:15
evidence/2026-10-11-batch13/T-078/stage-a-readback-rebind-01/09C-prepare.json:15
evidence/2026-10-15-batch15/T-082/REWORK-01.md:24
evidence/2026-10-15-batch15/T-082/T076-BOUNDARY-MIGRATION.md:13
evidence/2026-10-15-batch15/T-082/independent-review-01.md:82,121,125
evidence/2026-10-15-batch15/T-082/independent-review-02.md:82,83,84,85
evidence/2026-10-15-batch15/T-082/outside-command-02-01/controlled/launch-boundary-refused-readonly-argv/run.json:4
evidence/2026-10-15-batch15/T-082/outside-command-02-01/controlled/launch-boundary-refused-wrong-workspace/launch_boundary_refused/case.json:394
evidence/2026-10-15-batch15/T-082/outside-command-02-01/controlled/launch-boundary-refused-wrong-workspace/run.json:4,408
evidence/2026-10-15-batch15/T-082/outside-command-02-01/controlled/run.json:13,27,6083,6097,10753,10767,11171
evidence/2026-10-15-batch15/T-082/outside-command-02-01/controlled/tracer_review_copy/run.json:4
evidence/2026-10-15-batch15/T-082/outside-command-02-02/controlled/launch-boundary-refused-network-enabled/run.json:4
evidence/2026-10-15-batch15/T-082/outside-command-02-02/controlled/launch-boundary-refused-readonly-argv/run.json:4
evidence/2026-10-15-batch15/T-082/outside-command-02-02/controlled/launch-boundary-refused-tmp-writable/run.json:4
evidence/2026-10-15-batch15/T-082/outside-command-02-02/controlled/launch-boundary-refused-wrong-workspace/run.json:4
evidence/2026-10-15-batch15/T-082/outside-command-02-02/controlled/run.json:13,27,6083,6097,10753,10767,15423,15437,20093,20107
evidence/2026-10-15-batch15/T-082/outside-command-02-02/controlled/tracer_review_copy/run.json:4
evidence/2026-10-15-batch15/T-082/outside-command-03-01/end-check.command.json:3
evidence/2026-10-15-batch15/T-082/outside-command-03-01/end-check/run.json:4
evidence/2026-10-15-batch15/T-082/outside-command-06-01/t082-boundary-candidate/launch-boundary-refused-network-enabled/run.json:4
evidence/2026-10-15-batch15/T-082/outside-command-06-01/t082-boundary-candidate/launch-boundary-refused-readonly-argv/run.json:4
evidence/2026-10-15-batch15/T-082/outside-command-06-01/t082-boundary-candidate/launch-boundary-refused-tmp-writable/run.json:4
evidence/2026-10-15-batch15/T-082/outside-command-06-01/t082-boundary-candidate/launch-boundary-refused-wrong-workspace/run.json:4
evidence/2026-10-15-batch15/T-082/outside-command-06-01/t082-boundary-candidate/run.json:13,27,5987,6001,10657,10671,15327,15341,19997,20011
evidence/2026-10-15-batch15/T-082/outside-command-06-01/t082-boundary-candidate/tracer_review_copy/run.json:4
evidence/2026-10-15-batch15/T-082/outside-command-09-01/report-roundtrip/run.json:4
evidence/2026-10-15-batch15/T-082/outside-command-09-01/run.json:9
evidence/2026-10-15-batch15/T-082/outside-command-11-01/01-red-integration-window.assessment.json:8
evidence/2026-10-15-batch15/T-082/outside-command-11-01/01-red-integration-window/integration_before_end_check/case.json:5903
evidence/2026-10-15-batch15/T-082/outside-command-11-01/01-red-integration-window/run.json:4,5917
evidence/2026-10-15-batch15/T-082/outside-command-11-01/02-red-request-workspace.assessment.json:8
evidence/2026-10-15-batch15/T-082/outside-command-11-01/02-red-request-workspace/requirements_workspace_changed/case.json:5262
evidence/2026-10-15-batch15/T-082/outside-command-11-01/02-red-request-workspace/run.json:4,5276
evidence/2026-10-15-batch15/T-082/outside-command-11-01/03-request-copy-report.assessment.json:8
evidence/2026-10-15-batch15/T-082/outside-command-11-01/03-request-copy-report/run.json:4
evidence/2026-10-15-batch15/T-082/outside-command-11-01/04-dirty-review.assessment.json:8
evidence/2026-10-15-batch15/T-082/outside-command-11-01/04-dirty-review/run.json:4
evidence/2026-10-15-batch15/T-082/outside-command-11-01/05-shared-refs.assessment.json:8
evidence/2026-10-15-batch15/T-082/outside-command-11-01/05-shared-refs/run.json:4
evidence/2026-10-15-batch15/T-082/outside-command-11-01/06-integration-window.assessment.json:8
evidence/2026-10-15-batch15/T-082/outside-command-11-01/06-integration-window/run.json:4
evidence/2026-10-15-batch15/T-082/outside-command-11-01/07-clean-integration-window.assessment.json:8
evidence/2026-10-15-batch15/T-082/outside-command-11-01/07-clean-integration-window/run.json:4
evidence/2026-10-15-batch15/T-082/outside-command-11-01/08-request-workspace.assessment.json:8
evidence/2026-10-15-batch15/T-082/outside-command-11-01/08-request-workspace/run.json:4
evidence/2026-10-15-batch15/T-082/outside-command-11-01/09-M1-no-end-check-precondition.assessment.json:8
evidence/2026-10-15-batch15/T-082/outside-command-11-01/09-M1-no-end-check-precondition/integration_before_end_check_clean/case.json:5903
evidence/2026-10-15-batch15/T-082/outside-command-11-01/09-M1-no-end-check-precondition/run.json:4,5917
evidence/2026-10-15-batch15/T-082/outside-command-11-01/10-M2-no-workspace-binding.assessment.json:8
evidence/2026-10-15-batch15/T-082/outside-command-11-01/10-M2-no-workspace-binding/requirements_workspace_changed/case.json:5262
evidence/2026-10-15-batch15/T-082/outside-command-11-01/10-M2-no-workspace-binding/run.json:4,5276
evidence/2026-10-15-batch15/T-082/outside-command-11-01/11-M3-no-shared-refs-check.assessment.json:8
evidence/2026-10-15-batch15/T-082/outside-command-11-01/11-M3-no-shared-refs-check/run.json:4,5252
evidence/2026-10-15-batch15/T-082/outside-command-11-01/11-M3-no-shared-refs-check/shared_refs_changed/case.json:5238
evidence/2026-10-15-batch15/T-082/outside-command-11-01/12-launch-boundary/launch-boundary-refused-network-enabled/run.json:4
evidence/2026-10-15-batch15/T-082/outside-command-11-01/12-launch-boundary/launch-boundary-refused-readonly-argv/run.json:4
evidence/2026-10-15-batch15/T-082/outside-command-11-01/12-launch-boundary/launch-boundary-refused-tmp-writable/run.json:4
evidence/2026-10-15-batch15/T-082/outside-command-11-01/12-launch-boundary/launch-boundary-refused-wrong-workspace/run.json:4
evidence/2026-10-15-batch15/T-082/outside-command-11-01/12-launch-boundary/run.json:13,27,6024,6038,10679,10693,15350,15364,20021,20035
evidence/2026-10-15-batch15/T-082/outside-command-11-01/12-launch-boundary/tracer_review_copy/run.json:4
evidence/2026-10-15-batch15/T-082/outside-command-11-01/run.json:12,39,66,100,127,154,181,208,235,262,289
evidence/2026-10-15-batch15/T-082/outside-command-11-01/source.json:166
evidence/2026-10-16-batch16/T-089/independent-review-01.md:87
evidence/2026-10-16-batch16/T-089/independent-review-02.md:166
evidence/2026-10-16-batch16/T-089/reference-audit.md:46
evidence/2026-10-16-batch16/T-089/s3-baseline-local-01/cas/assertion-scope.json:2129
evidence/2026-10-16-batch16/T-089/t086-external-01.json:707
evidence/2026-10-16-batch16/T-089/t086-external-02.json:1265
evidence/2026-10-16-batch16/T-089/t086-local-01.json:707
evidence/2026-10-16-batch16/T-089/t086-local-02.json:707
evidence/2026-10-16-batch16/T-090/green-remaining-01.json:182,212,230,248,266
evidence/2026-10-19-batch17/T-105/python39-check-setup-failure-01.json:15,16
evidence/2026-10-23-batch23/T-148/ISSUE-stale-oracles.md:8
evidence/2026-10-23-batch23/T-148/RESULTS.md:55
evidence/2026-10-23-batch23/T-148/stale-contract-search.txt:31,32
```

</details>

### R5 `run_pane_lifecycle.py`

<details>
<summary>工作台 / 其他当前文件：0 个文件</summary>

无。

</details>

<details>
<summary>历史 evidence 可执行文件（含复跑脚本与冻结源码）：6 个文件</summary>

```text
evidence/2026-10-10-batch12/T-075/card-4/outside-sandbox.sh:8
evidence/2026-10-10-batch12/T-075/card-4/run_outside.py:119
evidence/2026-10-11-batch13/T-076/card-2/prepare-p-review-approval.py:97
evidence/2026-10-11-batch13/T-077/rebase-continue-03.sh:15,41
evidence/2026-10-11-batch13/T-077/resolve-rebase-stop-03.py:13
evidence/2026-10-14-batch14/T-080/run_final01_outside.py:25
```

</details>

<details>
<summary>其余文本命中（治理记录、报告、摘要、日志等）：259 个文件</summary>

```text
.project-map/inbox/20261015T131159Z-ideation-answer-001.md:20
.project-map/inbox/20261023T172046Z-worker:b23-t148-issue-001.md:22
.project-map/inbox/20261023T181004Z-executor-report-001.md:30
.project-map/inbox/20261023T181318Z-ideation-answer-001.md:17
.project-map/tickets/T-086-test-trailer-fixtures-launch-record.md:34
.project-map/tickets/T-148-stale-fixtures-after-t141.md:42
.project-map/tickets/T-149-retire-stale-historical-tests.md:18
evidence/2026-10-10-batch12/T-075/card-4/RESULTS.md:174,289
evidence/2026-10-10-batch12/T-075/card-4/decision02-static-01.json:5
evidence/2026-10-10-batch12/T-075/card-4/delivery-code-01/command-output/00003.stdout.bin:945,1004
evidence/2026-10-10-batch12/T-075/card-4/delivery-code-01/commands.jsonl:6
evidence/2026-10-10-batch12/T-075/card-4/delivery-code-01/receipt.json:82
evidence/2026-10-10-batch12/T-075/card-4/live-static-01.json:5
evidence/2026-10-10-batch12/T-075/card-4/live03-static-01.json:23
evidence/2026-10-10-batch12/T-075/card-4/live04-static-01/results.json:18
evidence/2026-10-10-batch12/T-075/card-4/outside-live-01/checks.json:7
evidence/2026-10-10-batch12/T-075/card-4/outside-live-01/preparation.json:19
evidence/2026-10-10-batch12/T-075/card-4/outside-live-01/verdict.json:15
evidence/2026-10-10-batch12/T-075/card-4/outside-live-02/preparation.json:19
evidence/2026-10-10-batch12/T-075/card-4/outside-live-03/checks.json:27
evidence/2026-10-10-batch12/T-075/card-4/outside-live-03/command-output/00002.stdout.bin:42
evidence/2026-10-10-batch12/T-075/card-4/outside-live-03/commands.jsonl:4,9,10
evidence/2026-10-10-batch12/T-075/card-4/outside-live-03/lifecycle.stdout.txt:13
evidence/2026-10-10-batch12/T-075/card-4/outside-live-03/lifecycle/verdict.json:13
evidence/2026-10-10-batch12/T-075/card-4/outside-live-03/preparation.json:30
evidence/2026-10-10-batch12/T-075/card-4/outside-live-03/verdict.json:35
evidence/2026-10-10-batch12/T-075/card-4/outside-live-04/checks.json:27
evidence/2026-10-10-batch12/T-075/card-4/outside-live-04/command-output/00002.stdout.bin:46
evidence/2026-10-10-batch12/T-075/card-4/outside-live-04/commands.jsonl:4,9,10
evidence/2026-10-10-batch12/T-075/card-4/outside-live-04/lifecycle.stdout.txt:13
evidence/2026-10-10-batch12/T-075/card-4/outside-live-04/lifecycle/verdict.json:13
evidence/2026-10-10-batch12/T-075/card-4/outside-live-04/preparation.json:30
evidence/2026-10-10-batch12/T-075/card-4/outside-live-04/verdict.json:35
evidence/2026-10-10-batch12/T-075/card-4/review-candidate-01/USER-ACCEPTANCE.md:18
evidence/2026-10-10-batch12/T-075/card-4/review-candidate-01/target.json:42
evidence/2026-10-10-batch12/dispatch.jsonl:87,88
evidence/2026-10-11-batch13/T-076/card-1/outside-attachments-01/source-manifest.json:60
evidence/2026-10-11-batch13/T-076/card-1/outside-green-checker-counterfactuals-01/source-manifest.json:60
evidence/2026-10-11-batch13/T-076/card-1/outside-green-focused-01/source-manifest.json:60
evidence/2026-10-11-batch13/T-076/card-1/outside-green-mutants-01/source-manifest.json:60
evidence/2026-10-11-batch13/T-076/card-1/outside-green-regression-01/source-manifest.json:60
evidence/2026-10-11-batch13/T-076/card-1/outside-green-regression-02/source-manifest.json:60
evidence/2026-10-11-batch13/T-076/card-1/outside-real-01/source-manifest.json:59
evidence/2026-10-11-batch13/T-076/card-1/outside-real-02/source-manifest.json:59
evidence/2026-10-11-batch13/T-076/card-1/outside-real-03/source-manifest.json:59
evidence/2026-10-11-batch13/T-076/card-1/outside-real-04/source-manifest.json:59
evidence/2026-10-11-batch13/T-076/card-1/review-01/manifest.json:74
evidence/2026-10-11-batch13/T-076/card-2/delivery-review-01/candidate/CANDIDATE.diff:2064,2066,2067
evidence/2026-10-11-batch13/T-076/card-2/delivery-review-01/manifest.json:99
evidence/2026-10-11-batch13/T-076/card-2/evidence-staging-check-01/run.json:162,287
evidence/2026-10-11-batch13/T-076/card-2/outside-delivery-review-01/commands.jsonl:3
evidence/2026-10-11-batch13/T-076/card-2/outside-delivery-review-01/native-sessions/2026/10/13/rollout-2026-10-13T12-00-00-01a135fd-fd26-7693-a738-ad75036b220e.jsonl:25,26,29,36,39
evidence/2026-10-11-batch13/T-076/card-2/outside-delivery-review-01/setup.json:69
evidence/2026-10-11-batch13/T-076/card-2/outside-legacy-green-01/source.json:61
evidence/2026-10-11-batch13/T-076/card-2/outside-legacy-green-02/source.json:61
evidence/2026-10-11-batch13/T-076/card-2/outside-legacy-green-03/source.json:61
evidence/2026-10-11-batch13/T-076/card-2/outside-legacy-green-04/source.json:61
evidence/2026-10-11-batch13/T-076/card-2/outside-legacy-green-05/source.json:61
evidence/2026-10-11-batch13/T-076/card-2/outside-legacy-green-06/source.json:61
evidence/2026-10-11-batch13/T-076/card-2/p-review-01/source-manifest.json:76
evidence/2026-10-11-batch13/T-076/card-2/p-review-02/source-manifest.json:76
evidence/2026-10-11-batch13/T-076/card-2/postcommit-readback-01/run.json:79
evidence/2026-10-11-batch13/T-076/card-2/real-delivery-01/source-manifest.json:76
evidence/2026-10-11-batch13/T-076/card-2/real-delivery-02/source-manifest.json:76
evidence/2026-10-11-batch13/T-076/card-2/real-delivery-preparation-01/source-manifest.json:76
evidence/2026-10-11-batch13/T-076/card-2/real-delivery-preparation-02/source-manifest.json:76
evidence/2026-10-11-batch13/T-076/card-2/real-delivery-preparation-03/source-manifest.json:76
evidence/2026-10-11-batch13/T-076/card-2/source-commit.json:32
evidence/2026-10-11-batch13/T-076/card-2/source-staging-check-02/run.json:39
evidence/2026-10-11-batch13/T-077/HANDOFF-rebase-continue-03.md:10
evidence/2026-10-11-batch13/T-077/commit-review-worktree-checks.json:15
evidence/2026-10-11-batch13/T-077/commit-review-worktree-files.json:1205,1208,1213,1216
evidence/2026-10-11-batch13/T-077/conflict-implementation-01/run.json:998
evidence/2026-10-11-batch13/T-077/conflict-red-final-01-preparation-01/plan.json:180
evidence/2026-10-11-batch13/T-077/conflict-red-final-01-preparation-02/plan.json:213
evidence/2026-10-11-batch13/T-077/outside-conflict-green-01/source-files.json:57
evidence/2026-10-11-batch13/T-077/outside-conflict-red-01/source-files.json:57
evidence/2026-10-11-batch13/T-077/outside-conflict-red-final-01/red-01/source-files.json:72
evidence/2026-10-11-batch13/T-077/outside-conflict-red-final-01/red-02/source-files.json:72
evidence/2026-10-11-batch13/T-077/outside-conflict-red-final-01/red-03/source-files.json:72
evidence/2026-10-11-batch13/T-077/outside-conflict-red-final-01/red-04/source-files.json:72
evidence/2026-10-11-batch13/T-077/outside-conflict-red-final-02-preparation/plan.json:215
evidence/2026-10-11-batch13/T-077/outside-conflict-red-final-02/candidate/source-files.json:72
evidence/2026-10-11-batch13/T-077/outside-conflict-red-final-02/red-01/source-files.json:72
evidence/2026-10-11-batch13/T-077/outside-conflict-red-final-02/red-02/source-files.json:72
evidence/2026-10-11-batch13/T-077/outside-conflict-red-final-02/red-03/source-files.json:72
evidence/2026-10-11-batch13/T-077/outside-conflict-red-final-02/red-04/source-files.json:72
evidence/2026-10-11-batch13/T-077/outside-conflict-red-final-02/red-05/source-files.json:72
evidence/2026-10-11-batch13/T-077/outside-conflict-red-final-02/red-06/source-files.json:72
evidence/2026-10-11-batch13/T-077/outside-conflict-red-final-02/red-07/source-files.json:72
evidence/2026-10-11-batch13/T-077/outside-green-01/source-files.json:55
evidence/2026-10-11-batch13/T-077/outside-green-02/source-files.json:55
evidence/2026-10-11-batch13/T-077/outside-green-03/source-files.json:56
evidence/2026-10-11-batch13/T-077/outside-green-04/source-files.json:56
evidence/2026-10-11-batch13/T-077/outside-rebase-01-cards/source-files.json:62
evidence/2026-10-11-batch13/T-077/outside-rebase-01-cas/source-files.json:62
evidence/2026-10-11-batch13/T-077/outside-rebase-01-contracts/source-files.json:62
evidence/2026-10-11-batch13/T-077/outside-rebase-01-coop/source-files.json:62
evidence/2026-10-11-batch13/T-077/outside-rebase-01-recovery/source-files.json:62
evidence/2026-10-11-batch13/T-077/outside-rebase-01-run/source-files.json:62
evidence/2026-10-11-batch13/T-077/outside-rebase-final-01/conflict-red-01/source-files.json:72
evidence/2026-10-11-batch13/T-077/outside-rebase-final-01/conflict-red-02/source-files.json:72
evidence/2026-10-11-batch13/T-077/outside-rebase-final-01/conflict-red-03/source-files.json:72
evidence/2026-10-11-batch13/T-077/outside-rebase-final-01/conflict-red-04/source-files.json:72
evidence/2026-10-11-batch13/T-077/outside-rebase-final-01/conflict-red-05/source-files.json:72
evidence/2026-10-11-batch13/T-077/outside-rebase-final-01/conflict-red-06/source-files.json:72
evidence/2026-10-11-batch13/T-077/outside-rebase-final-01/conflict-red-07/source-files.json:72
evidence/2026-10-11-batch13/T-077/outside-rebase-final-01/s3-all/source-files.json:72
evidence/2026-10-11-batch13/T-077/outside-rebase-final-03/conflict-red-01/source-files.json:72
evidence/2026-10-11-batch13/T-077/outside-rebase-final-03/conflict-red-02/source-files.json:72
evidence/2026-10-11-batch13/T-077/outside-rebase-final-03/conflict-red-03/source-files.json:72
evidence/2026-10-11-batch13/T-077/outside-rebase-final-03/conflict-red-04/source-files.json:72
evidence/2026-10-11-batch13/T-077/outside-rebase-final-03/conflict-red-05/source-files.json:72
evidence/2026-10-11-batch13/T-077/outside-rebase-final-03/conflict-red-06/source-files.json:72
evidence/2026-10-11-batch13/T-077/outside-rebase-final-03/conflict-red-07/source-files.json:72
evidence/2026-10-11-batch13/T-077/outside-rebase-final-03/s3-all/source-files.json:72
evidence/2026-10-11-batch13/T-077/outside-rebase-final-04/conflict-red-01/source-files.json:72
evidence/2026-10-11-batch13/T-077/outside-rebase-final-04/conflict-red-02/source-files.json:72
evidence/2026-10-11-batch13/T-077/outside-rebase-final-04/conflict-red-03/source-files.json:72
evidence/2026-10-11-batch13/T-077/outside-rebase-final-04/conflict-red-04/source-files.json:72
evidence/2026-10-11-batch13/T-077/outside-rebase-final-04/conflict-red-05/source-files.json:72
evidence/2026-10-11-batch13/T-077/outside-rebase-final-04/conflict-red-06/source-files.json:72
evidence/2026-10-11-batch13/T-077/outside-rebase-final-04/conflict-red-07/source-files.json:72
evidence/2026-10-11-batch13/T-077/outside-rebase-final-04/s3-all/source-files.json:72
evidence/2026-10-11-batch13/T-077/outside-rebase-final-05/conflict-red-01/source-files.json:72
evidence/2026-10-11-batch13/T-077/outside-rebase-final-05/conflict-red-02/source-files.json:72
evidence/2026-10-11-batch13/T-077/outside-rebase-final-05/conflict-red-03/source-files.json:72
evidence/2026-10-11-batch13/T-077/outside-rebase-final-05/conflict-red-04/source-files.json:72
evidence/2026-10-11-batch13/T-077/outside-rebase-final-05/conflict-red-05/source-files.json:72
evidence/2026-10-11-batch13/T-077/outside-rebase-final-05/conflict-red-06/source-files.json:72
evidence/2026-10-11-batch13/T-077/outside-rebase-final-05/conflict-red-07/source-files.json:72
evidence/2026-10-11-batch13/T-077/outside-rebase-final-05/s3-all/source-files.json:72
evidence/2026-10-11-batch13/T-077/outside-red-01/source-files.json:54
evidence/2026-10-11-batch13/T-077/outside-red-02/source-files.json:55
evidence/2026-10-11-batch13/T-077/outside-red-03/source-files.json:55
evidence/2026-10-11-batch13/T-077/outside-red-04/source-files.json:56
evidence/2026-10-11-batch13/T-077/outside-regression-02-cards/source-files.json:56
evidence/2026-10-11-batch13/T-077/outside-regression-02-cas/source-files.json:56
evidence/2026-10-11-batch13/T-077/outside-regression-02-coop/source-files.json:56
evidence/2026-10-11-batch13/T-077/outside-regression-02-recovery/source-files.json:56
evidence/2026-10-11-batch13/T-077/outside-regression-02-run/source-files.json:56
evidence/2026-10-11-batch13/T-077/outside-regression-03-cards/source-files.json:56
evidence/2026-10-11-batch13/T-077/outside-relay-regression-01-cards/source-files.json:63
evidence/2026-10-11-batch13/T-077/outside-relay-regression-01-cas/source-files.json:63
evidence/2026-10-11-batch13/T-077/outside-relay-regression-01-contracts/source-files.json:63
evidence/2026-10-11-batch13/T-077/outside-relay-regression-01-coop/source-files.json:63
evidence/2026-10-11-batch13/T-077/outside-relay-regression-01-recovery/source-files.json:63
evidence/2026-10-11-batch13/T-077/outside-relay-regression-01-run/source-files.json:63
evidence/2026-10-11-batch13/T-077/rebase-continue-02-controller.out:648,649
evidence/2026-10-11-batch13/T-077/rebase-final-02-preparation-01/plan.json:148
evidence/2026-10-11-batch13/T-077/rebase-final-03-preparation-01/plan.json:149
evidence/2026-10-11-batch13/T-077/rebase-final-04-preparation-01/plan.json:150
evidence/2026-10-11-batch13/T-077/rebase-final-05-preparation-01/plan.json:164
evidence/2026-10-11-batch13/T-077/rebase-final-preparation-01/plan.json:140
evidence/2026-10-11-batch13/T-077/rebase-final-preparation-02/plan.json:140
evidence/2026-10-11-batch13/T-077/rebase-final-preparation-03/plan.json:140
evidence/2026-10-11-batch13/T-077/rebase-stop-03/preflight.json:9,25
evidence/2026-10-11-batch13/T-078/09b-a16-b1-executor-p1-01/source-files.json:128
evidence/2026-10-11-batch13/T-078/09b-a16-b1-ideation-p1-01/source-files.json:128
evidence/2026-10-11-batch13/T-078/09b-a16-materials-01/SOURCE.json:136
evidence/2026-10-11-batch13/T-078/09b-a16-materials-01/prepare.json:15
evidence/2026-10-11-batch13/T-078/09b-executable-materials-16-02/source-files.json:128
evidence/2026-10-11-batch13/T-078/09b-executable-materials-16-02/static-check.json:130
evidence/2026-10-11-batch13/T-078/09b-executable-materials-16/source-files.json:128
evidence/2026-10-11-batch13/T-078/09b-executable-materials-16/static-check.json:130
evidence/2026-10-11-batch13/T-078/09c-attempt-2-materials-01/SOURCE.json:167
evidence/2026-10-11-batch13/T-078/09c-attempt-2-materials-01/prepare.json:15
evidence/2026-10-11-batch13/T-078/09c-attempt-2-materials-02/SOURCE.json:171
evidence/2026-10-11-batch13/T-078/09c-attempt-2-materials-02/prepare.json:15
evidence/2026-10-11-batch13/T-078/09c-attempt-3-materials-01/prepare.json:15
evidence/2026-10-11-batch13/T-078/09c-c1-b1-executor-p1-01/source-files.json:128
evidence/2026-10-11-batch13/T-078/09c-c1-b1-ideation-p1-01/source-files.json:128
evidence/2026-10-11-batch13/T-078/09c-c2-b1-executor-p1-01/source-files.json:128
evidence/2026-10-11-batch13/T-078/09c-c2-b1-ideation-p1-01/source-files.json:128
evidence/2026-10-11-batch13/T-078/09c-c3-b1-executor-p1-01/source-files.json:128
evidence/2026-10-11-batch13/T-078/09c-c3-b1-ideation-p1-01/source-files.json:128
evidence/2026-10-11-batch13/T-078/09c-caffeinate-parity-rehearsal-01/flow/executor-p1/source-files.json:109
evidence/2026-10-11-batch13/T-078/09c-caffeinate-parity-rehearsal-01/flow/ideation-p1/source-files.json:109
evidence/2026-10-11-batch13/T-078/09c-caffeinate-parity-rehearsal-01/flow/packet/static-check.json:113
evidence/2026-10-11-batch13/T-078/09c-caffeinate-parity-rehearsal-02/flow/executor-p1/source-files.json:109
evidence/2026-10-11-batch13/T-078/09c-caffeinate-parity-rehearsal-02/flow/ideation-p1/source-files.json:109
evidence/2026-10-11-batch13/T-078/09c-caffeinate-parity-rehearsal-02/flow/packet/static-check.json:113
evidence/2026-10-11-batch13/T-078/09c-coordinator-rehearsal-01/real-chain-outside-01/flow/executor-p1/source-files.json:102
evidence/2026-10-11-batch13/T-078/09c-coordinator-rehearsal-01/real-chain-outside-01/flow/ideation-p1/source-files.json:102
evidence/2026-10-11-batch13/T-078/09c-coordinator-rehearsal-01/real-chain-outside-01/flow/packet/static-check.json:106
evidence/2026-10-11-batch13/T-078/09c-executable-materials-01/source-files.json:128
evidence/2026-10-11-batch13/T-078/09c-executable-materials-01/static-check.json:130
evidence/2026-10-11-batch13/T-078/09c-executable-materials-02/source-files.json:128
evidence/2026-10-11-batch13/T-078/09c-executable-materials-02/static-check.json:130
evidence/2026-10-11-batch13/T-078/09c-executable-materials-03/source-files.json:128
evidence/2026-10-11-batch13/T-078/09c-executable-materials-03/static-check.json:130
evidence/2026-10-11-batch13/T-078/09c-executable-materials-04/source-files.json:128
evidence/2026-10-11-batch13/T-078/09c-executable-materials-04/static-check.json:130
evidence/2026-10-11-batch13/T-078/09c-executable-materials-05/source-files.json:128
evidence/2026-10-11-batch13/T-078/09c-executable-materials-05/static-check.json:130
evidence/2026-10-11-batch13/T-078/09c-fix-01/real-chain-outside-01/flow/executor-p1/source-files.json:101
evidence/2026-10-11-batch13/T-078/09c-fix-01/real-chain-outside-01/flow/ideation-p1/source-files.json:101
evidence/2026-10-11-batch13/T-078/09c-fix-01/real-chain-outside-02/flow/executor-p1/source-files.json:101
evidence/2026-10-11-batch13/T-078/09c-fix-01/real-chain-outside-02/flow/ideation-p1/source-files.json:101
evidence/2026-10-11-batch13/T-078/09c-fix-01/real-chain-outside-03/flow/executor-p1/source-files.json:101
evidence/2026-10-11-batch13/T-078/09c-fix-01/real-chain-outside-03/flow/ideation-p1/source-files.json:101
evidence/2026-10-11-batch13/T-078/09c-materials-01/SOURCE.json:136
evidence/2026-10-11-batch13/T-078/09c-materials-01/prepare.json:15
evidence/2026-10-11-batch13/T-078/09c-topology-probe-run-01/ideation-p1/source-files.json:102
evidence/2026-10-11-batch13/T-078/09c-topology-probe-run-01/packet/static-check.json:106
evidence/2026-10-11-batch13/T-078/stage-a-readback-rebind-01/09B-prepare.json:15
evidence/2026-10-11-batch13/T-078/stage-a-readback-rebind-01/09C-prepare.json:15
evidence/2026-10-11-batch13/dispatch.jsonl:205,206
evidence/2026-10-14-batch14/T-080/commit-03/run.json:60
evidence/2026-10-14-batch14/T-080/final-01/diff.stdout.bin:422,424,425
evidence/2026-10-14-batch14/T-080/final-01/source-manifest.json:16
evidence/2026-10-14-batch14/T-080/final-01/status.stdout.bin:10
evidence/2026-10-14-batch14/T-080/final-02/diff.stdout.bin:422,424,425
evidence/2026-10-14-batch14/T-080/final-02/source-manifest.json:16
evidence/2026-10-14-batch14/T-080/final-02/status.stdout.bin:10
evidence/2026-10-14-batch14/T-080/final-02/t077-lifecycle-conflicts/source-files.json:72
evidence/2026-10-14-batch14/T-080/final-03/diff.stdout.bin:422,424,425
evidence/2026-10-14-batch14/T-080/final-03/source-manifest.json:16
evidence/2026-10-14-batch14/T-080/final-03/status.stdout.bin:10
evidence/2026-10-14-batch14/T-080/final-03/t077-lifecycle-conflicts/source-files.json:72
evidence/2026-10-14-batch14/T-080/independent-review-01.completed.json:19
evidence/2026-10-14-batch14/T-080/independent-review-01.diff:1524,6890,6892,6893
evidence/2026-10-14-batch14/T-080/independent-review-01.request.json:28
evidence/2026-10-14-batch14/T-080/run-repair-probe-01/diff.stdout.bin:422,424,425
evidence/2026-10-14-batch14/T-080/run-repair-probe-01/status.stdout.bin:10
evidence/2026-10-14-batch14/T-080/schema-readiness-01.json:14
evidence/2026-10-14-batch14/T-080/schema-readiness-02.json:23,94
evidence/2026-10-14-batch14/T-081/6e-full-01/source-manifest.json:47
evidence/2026-10-14-batch14/T-081/6e-full-02/source-manifest.json:47
evidence/2026-10-14-batch14/T-081/6e-regress-rest-02/t077-lifecycle-conflicts/source-files.json:87
evidence/2026-10-14-batch14/T-081/6e-rerun-01/source-manifest.json:47
evidence/2026-10-14-batch14/T-081/6e-rerun-rest-01/t077-lifecycle-conflicts/source-files.json:87
evidence/2026-10-14-batch14/T-081/full-01/source-manifest.json:41
evidence/2026-10-14-batch14/T-081/full-02/source-manifest.json:43
evidence/2026-10-14-batch14/T-081/full-03/source-manifest.json:44
evidence/2026-10-14-batch14/T-081/full-03/t077-lifecycle-conflicts/source-files.json:74
evidence/2026-10-14-batch14/T-081/full-04/source-manifest.json:44
evidence/2026-10-14-batch14/T-081/full-04/t077-lifecycle-conflicts/source-files.json:74
evidence/2026-10-15-batch15/T-082/outside-command-11-01/source.json:82
evidence/2026-10-15-batch15/T-084/regression-03/worktree/source-files.json:72
evidence/2026-10-15-batch15/T-086/RESULTS.md:122,266
evidence/2026-10-15-batch15/T-086/conflict-suite-01/source-files.json:72
evidence/2026-10-15-batch15/T-086/green-01/source-files.json:72
evidence/2026-10-15-batch15/T-086/independent-review-01.md:85
evidence/2026-10-15-batch15/T-086/independent-review-02.md:142
evidence/2026-10-15-batch15/T-086/lifecycle-managed/source-files.json:72
evidence/2026-10-15-batch15/T-086/red-01/source-files.json:72
evidence/2026-10-15-batch15/T-086/rework-conflict-suite/source-files.json:72
evidence/2026-10-15-batch15/T-086/rework-green-01/source-files.json:72
evidence/2026-10-15-batch15/T-086/rework-m1/source-files.json:72
evidence/2026-10-15-batch15/T-086/rework-m2/source-files.json:72
evidence/2026-10-15-batch15/T-086/rework-m3/source-files.json:72
evidence/2026-10-15-batch15/T-086/rework-m4/source-files.json:72
evidence/2026-10-15-batch15/T-086/rework-m5/source-files.json:72
evidence/2026-10-15-batch15/T-086/rework-red-01/source-files.json:72
evidence/2026-10-16-batch16/T-089/s3-baseline-local-01/cas/assertion-scope.json:1298,1362
evidence/2026-10-19-batch17/T-105/python39-check-setup-failure-01.json:15,16
evidence/2026-10-23-batch23/T-148/ISSUE-stale-oracles.md:9
evidence/2026-10-23-batch23/T-148/RESULTS.md:55
```

</details>

### R6 `run_worker_delivery.py`

<details>
<summary>工作台 / 其他当前文件：0 个文件</summary>

无。

</details>

<details>
<summary>历史 evidence 可执行文件（含复跑脚本与冻结源码）：2 个文件</summary>

```text
evidence/2026-10-10-batch12/T-075/card-3/outside-sandbox.sh:39
evidence/2026-10-14-batch14/T-080/run_final01_outside.py:27
```

</details>

<details>
<summary>其余文本命中（治理记录、报告、摘要、日志等）：251 个文件</summary>

```text
.project-map/inbox/20261015T131159Z-ideation-answer-001.md:15,19,20
.project-map/inbox/20261015T152406Z-executor-report-001.md:16
.project-map/inbox/20261023T172046Z-worker:b23-t148-issue-001.md:22
.project-map/inbox/20261023T181004Z-executor-report-001.md:30
.project-map/inbox/20261023T181318Z-ideation-answer-001.md:17
.project-map/tickets/T-086-test-trailer-fixtures-launch-record.md:33,34
.project-map/tickets/T-148-stale-fixtures-after-t141.md:42
.project-map/tickets/T-149-retire-stale-historical-tests.md:18
evidence/2026-10-10-batch12/T-075/card-3/execpolicy-06/results.json:181
evidence/2026-10-10-batch12/T-075/card-3/outside-handoff-05.json:105
evidence/2026-10-10-batch12/T-075/card-3/review-snapshot-check-07-failure.json:71
evidence/2026-10-10-batch12/T-075/card-3/review-target-08.json:67,142
evidence/2026-10-10-batch12/T-075/card-4/delivery-code-01/command-output/00003.stdout.bin:946
evidence/2026-10-10-batch12/T-075/card-4/delivery-code-01/commands.jsonl:6
evidence/2026-10-10-batch12/T-075/card-4/delivery-code-01/receipt.json:82
evidence/2026-10-10-batch12/T-075/card-4/review-candidate-01/target.json:49
evidence/2026-10-11-batch13/T-076/card-1/PLAN.md:23
evidence/2026-10-11-batch13/T-076/card-1/outside-attachments-01/source-manifest.json:72
evidence/2026-10-11-batch13/T-076/card-1/outside-green-checker-counterfactuals-01/source-manifest.json:74
evidence/2026-10-11-batch13/T-076/card-1/outside-green-focused-01/source-manifest.json:71
evidence/2026-10-11-batch13/T-076/card-1/outside-green-mutants-01/source-manifest.json:74
evidence/2026-10-11-batch13/T-076/card-1/outside-green-regression-01/source-manifest.json:74
evidence/2026-10-11-batch13/T-076/card-1/outside-green-regression-02/source-manifest.json:74
evidence/2026-10-11-batch13/T-076/card-1/outside-real-01/source-manifest.json:71
evidence/2026-10-11-batch13/T-076/card-1/outside-real-02/source-manifest.json:71
evidence/2026-10-11-batch13/T-076/card-1/outside-real-03/source-manifest.json:73
evidence/2026-10-11-batch13/T-076/card-1/outside-real-04/source-manifest.json:73
evidence/2026-10-11-batch13/T-076/card-1/real-id-repair-01/run_t076_real.py.before:21
evidence/2026-10-11-batch13/T-076/card-1/real-preparation-03/run_t076_real.py.before:24
evidence/2026-10-11-batch13/T-076/card-1/real-preparation-04/deadline-fixture.diff:21
evidence/2026-10-11-batch13/T-076/card-1/real-preparation-04/run_t076_real.py.before:24
evidence/2026-10-11-batch13/T-076/card-1/review-01/manifest.json:79
evidence/2026-10-11-batch13/T-076/card-1/startup-shutdown-repair-01/run_t076_real.py.before:21
evidence/2026-10-11-batch13/T-076/card-1/stopped-readback-repair-01/audit-02/readback-only.diff:116
evidence/2026-10-11-batch13/T-076/card-1/stopped-readback-repair-01/audit-03/readback-only.diff:116
evidence/2026-10-11-batch13/T-076/card-1/stopped-readback-repair-01/readback-only.diff:116
evidence/2026-10-11-batch13/T-076/card-1/stopped-readback-repair-01/run_t076_real.py.before:23
evidence/2026-10-11-batch13/T-076/card-2/F05-migration-list.md:101
evidence/2026-10-11-batch13/T-076/card-2/PLAN.md:272
evidence/2026-10-11-batch13/T-076/card-2/assertion-hunks.md:14
evidence/2026-10-11-batch13/T-076/card-2/delivery-review-01/manifest.json:110
evidence/2026-10-11-batch13/T-076/card-2/evidence-staging-check-01/run.json:167,298
evidence/2026-10-11-batch13/T-076/card-2/outside-delivery-review-01/commands.jsonl:3
evidence/2026-10-11-batch13/T-076/card-2/outside-delivery-review-01/native-sessions/2026/10/13/rollout-2026-10-13T12-00-00-01a135fd-fd26-7693-a738-ad75036b220e.jsonl:26,29,36,39
evidence/2026-10-11-batch13/T-076/card-2/outside-delivery-review-01/setup.json:69
evidence/2026-10-11-batch13/T-076/card-2/outside-legacy-green-01/source.json:78
evidence/2026-10-11-batch13/T-076/card-2/outside-legacy-green-02/source.json:78
evidence/2026-10-11-batch13/T-076/card-2/outside-legacy-green-03/source.json:78
evidence/2026-10-11-batch13/T-076/card-2/outside-legacy-green-04/source.json:78
evidence/2026-10-11-batch13/T-076/card-2/outside-legacy-green-05/source.json:78
evidence/2026-10-11-batch13/T-076/card-2/outside-legacy-green-06/source.json:78
evidence/2026-10-11-batch13/T-076/card-2/p-review-01/source-manifest.json:85
evidence/2026-10-11-batch13/T-076/card-2/p-review-02/source-manifest.json:86
evidence/2026-10-11-batch13/T-076/card-2/postcommit-readback-01/run.json:79
evidence/2026-10-11-batch13/T-076/card-2/real-delivery-01/source-manifest.json:87
evidence/2026-10-11-batch13/T-076/card-2/real-delivery-02/source-manifest.json:87
evidence/2026-10-11-batch13/T-076/card-2/real-delivery-preparation-01/source-manifest.json:87
evidence/2026-10-11-batch13/T-076/card-2/real-delivery-preparation-02/source-manifest.json:87
evidence/2026-10-11-batch13/T-076/card-2/real-delivery-preparation-03/source-manifest.json:87
evidence/2026-10-11-batch13/T-077/conflict-implementation-01/run.json:1006
evidence/2026-10-11-batch13/T-077/conflict-red-final-01-preparation-01/plan.json:193
evidence/2026-10-11-batch13/T-077/conflict-red-final-01-preparation-02/plan.json:226
evidence/2026-10-11-batch13/T-077/outside-conflict-green-01/source-files.json:59
evidence/2026-10-11-batch13/T-077/outside-conflict-red-01/source-files.json:59
evidence/2026-10-11-batch13/T-077/outside-conflict-red-final-01/red-01/source-files.json:85
evidence/2026-10-11-batch13/T-077/outside-conflict-red-final-01/red-02/source-files.json:85
evidence/2026-10-11-batch13/T-077/outside-conflict-red-final-01/red-03/source-files.json:85
evidence/2026-10-11-batch13/T-077/outside-conflict-red-final-01/red-04/source-files.json:85
evidence/2026-10-11-batch13/T-077/outside-conflict-red-final-02-preparation/plan.json:228
evidence/2026-10-11-batch13/T-077/outside-conflict-red-final-02/candidate/source-files.json:85
evidence/2026-10-11-batch13/T-077/outside-conflict-red-final-02/red-01/source-files.json:85
evidence/2026-10-11-batch13/T-077/outside-conflict-red-final-02/red-02/source-files.json:85
evidence/2026-10-11-batch13/T-077/outside-conflict-red-final-02/red-03/source-files.json:85
evidence/2026-10-11-batch13/T-077/outside-conflict-red-final-02/red-04/source-files.json:85
evidence/2026-10-11-batch13/T-077/outside-conflict-red-final-02/red-05/source-files.json:85
evidence/2026-10-11-batch13/T-077/outside-conflict-red-final-02/red-06/source-files.json:85
evidence/2026-10-11-batch13/T-077/outside-conflict-red-final-02/red-07/source-files.json:85
evidence/2026-10-11-batch13/T-077/outside-green-01/source-files.json:56
evidence/2026-10-11-batch13/T-077/outside-green-02/source-files.json:56
evidence/2026-10-11-batch13/T-077/outside-green-03/source-files.json:58
evidence/2026-10-11-batch13/T-077/outside-green-04/source-files.json:58
evidence/2026-10-11-batch13/T-077/outside-rebase-01-cards/source-files.json:68
evidence/2026-10-11-batch13/T-077/outside-rebase-01-cas/source-files.json:68
evidence/2026-10-11-batch13/T-077/outside-rebase-01-contracts/source-files.json:68
evidence/2026-10-11-batch13/T-077/outside-rebase-01-coop/source-files.json:68
evidence/2026-10-11-batch13/T-077/outside-rebase-01-recovery/source-files.json:68
evidence/2026-10-11-batch13/T-077/outside-rebase-01-run/source-files.json:68
evidence/2026-10-11-batch13/T-077/outside-rebase-final-01/conflict-red-01/source-files.json:85
evidence/2026-10-11-batch13/T-077/outside-rebase-final-01/conflict-red-02/source-files.json:85
evidence/2026-10-11-batch13/T-077/outside-rebase-final-01/conflict-red-03/source-files.json:85
evidence/2026-10-11-batch13/T-077/outside-rebase-final-01/conflict-red-04/source-files.json:85
evidence/2026-10-11-batch13/T-077/outside-rebase-final-01/conflict-red-05/source-files.json:85
evidence/2026-10-11-batch13/T-077/outside-rebase-final-01/conflict-red-06/source-files.json:85
evidence/2026-10-11-batch13/T-077/outside-rebase-final-01/conflict-red-07/source-files.json:85
evidence/2026-10-11-batch13/T-077/outside-rebase-final-01/s3-all/source-files.json:85
evidence/2026-10-11-batch13/T-077/outside-rebase-final-03/conflict-red-01/source-files.json:85
evidence/2026-10-11-batch13/T-077/outside-rebase-final-03/conflict-red-02/source-files.json:85
evidence/2026-10-11-batch13/T-077/outside-rebase-final-03/conflict-red-03/source-files.json:85
evidence/2026-10-11-batch13/T-077/outside-rebase-final-03/conflict-red-04/source-files.json:85
evidence/2026-10-11-batch13/T-077/outside-rebase-final-03/conflict-red-05/source-files.json:85
evidence/2026-10-11-batch13/T-077/outside-rebase-final-03/conflict-red-06/source-files.json:85
evidence/2026-10-11-batch13/T-077/outside-rebase-final-03/conflict-red-07/source-files.json:85
evidence/2026-10-11-batch13/T-077/outside-rebase-final-03/s3-all/source-files.json:85
evidence/2026-10-11-batch13/T-077/outside-rebase-final-04/conflict-red-01/source-files.json:85
evidence/2026-10-11-batch13/T-077/outside-rebase-final-04/conflict-red-02/source-files.json:85
evidence/2026-10-11-batch13/T-077/outside-rebase-final-04/conflict-red-03/source-files.json:85
evidence/2026-10-11-batch13/T-077/outside-rebase-final-04/conflict-red-04/source-files.json:85
evidence/2026-10-11-batch13/T-077/outside-rebase-final-04/conflict-red-05/source-files.json:85
evidence/2026-10-11-batch13/T-077/outside-rebase-final-04/conflict-red-06/source-files.json:85
evidence/2026-10-11-batch13/T-077/outside-rebase-final-04/conflict-red-07/source-files.json:85
evidence/2026-10-11-batch13/T-077/outside-rebase-final-04/s3-all/source-files.json:85
evidence/2026-10-11-batch13/T-077/outside-rebase-final-05/conflict-red-01/source-files.json:85
evidence/2026-10-11-batch13/T-077/outside-rebase-final-05/conflict-red-02/source-files.json:85
evidence/2026-10-11-batch13/T-077/outside-rebase-final-05/conflict-red-03/source-files.json:85
evidence/2026-10-11-batch13/T-077/outside-rebase-final-05/conflict-red-04/source-files.json:85
evidence/2026-10-11-batch13/T-077/outside-rebase-final-05/conflict-red-05/source-files.json:85
evidence/2026-10-11-batch13/T-077/outside-rebase-final-05/conflict-red-06/source-files.json:85
evidence/2026-10-11-batch13/T-077/outside-rebase-final-05/conflict-red-07/source-files.json:85
evidence/2026-10-11-batch13/T-077/outside-rebase-final-05/s3-all/source-files.json:85
evidence/2026-10-11-batch13/T-077/outside-red-01/source-files.json:55
evidence/2026-10-11-batch13/T-077/outside-red-02/source-files.json:56
evidence/2026-10-11-batch13/T-077/outside-red-03/source-files.json:56
evidence/2026-10-11-batch13/T-077/outside-red-04/source-files.json:58
evidence/2026-10-11-batch13/T-077/outside-regression-02-cards/source-files.json:58
evidence/2026-10-11-batch13/T-077/outside-regression-02-cas/source-files.json:58
evidence/2026-10-11-batch13/T-077/outside-regression-02-coop/source-files.json:58
evidence/2026-10-11-batch13/T-077/outside-regression-02-recovery/source-files.json:58
evidence/2026-10-11-batch13/T-077/outside-regression-02-run/source-files.json:58
evidence/2026-10-11-batch13/T-077/outside-regression-03-cards/source-files.json:58
evidence/2026-10-11-batch13/T-077/outside-relay-regression-01-cards/source-files.json:69
evidence/2026-10-11-batch13/T-077/outside-relay-regression-01-cas/source-files.json:69
evidence/2026-10-11-batch13/T-077/outside-relay-regression-01-contracts/source-files.json:69
evidence/2026-10-11-batch13/T-077/outside-relay-regression-01-coop/source-files.json:69
evidence/2026-10-11-batch13/T-077/outside-relay-regression-01-recovery/source-files.json:69
evidence/2026-10-11-batch13/T-077/outside-relay-regression-01-run/source-files.json:69
evidence/2026-10-11-batch13/T-077/rebase-final-02-preparation-01/plan.json:161
evidence/2026-10-11-batch13/T-077/rebase-final-03-preparation-01/plan.json:162
evidence/2026-10-11-batch13/T-077/rebase-final-04-preparation-01/plan.json:163
evidence/2026-10-11-batch13/T-077/rebase-final-05-preparation-01/plan.json:177
evidence/2026-10-11-batch13/T-077/rebase-final-preparation-01/plan.json:153
evidence/2026-10-11-batch13/T-077/rebase-final-preparation-02/plan.json:153
evidence/2026-10-11-batch13/T-077/rebase-final-preparation-03/plan.json:153
evidence/2026-10-11-batch13/T-078/09b-a16-b1-executor-p1-01/source-files.json:154
evidence/2026-10-11-batch13/T-078/09b-a16-b1-ideation-p1-01/source-files.json:154
evidence/2026-10-11-batch13/T-078/09b-a16-materials-01/SOURCE.json:162
evidence/2026-10-11-batch13/T-078/09b-a16-materials-01/prepare.json:15
evidence/2026-10-11-batch13/T-078/09b-executable-materials-16-02/source-files.json:154
evidence/2026-10-11-batch13/T-078/09b-executable-materials-16-02/static-check.json:156
evidence/2026-10-11-batch13/T-078/09b-executable-materials-16/source-files.json:154
evidence/2026-10-11-batch13/T-078/09b-executable-materials-16/static-check.json:156
evidence/2026-10-11-batch13/T-078/09c-attempt-2-materials-01/SOURCE.json:193
evidence/2026-10-11-batch13/T-078/09c-attempt-2-materials-01/prepare.json:15
evidence/2026-10-11-batch13/T-078/09c-attempt-2-materials-02/SOURCE.json:197
evidence/2026-10-11-batch13/T-078/09c-attempt-2-materials-02/prepare.json:15
evidence/2026-10-11-batch13/T-078/09c-attempt-3-materials-01/prepare.json:15
evidence/2026-10-11-batch13/T-078/09c-c1-b1-executor-p1-01/source-files.json:154
evidence/2026-10-11-batch13/T-078/09c-c1-b1-ideation-p1-01/source-files.json:154
evidence/2026-10-11-batch13/T-078/09c-c2-b1-executor-p1-01/source-files.json:154
evidence/2026-10-11-batch13/T-078/09c-c2-b1-ideation-p1-01/source-files.json:154
evidence/2026-10-11-batch13/T-078/09c-c3-b1-executor-p1-01/source-files.json:154
evidence/2026-10-11-batch13/T-078/09c-c3-b1-ideation-p1-01/source-files.json:154
evidence/2026-10-11-batch13/T-078/09c-caffeinate-parity-rehearsal-01/flow/executor-p1/source-files.json:136
evidence/2026-10-11-batch13/T-078/09c-caffeinate-parity-rehearsal-01/flow/ideation-p1/source-files.json:136
evidence/2026-10-11-batch13/T-078/09c-caffeinate-parity-rehearsal-01/flow/packet/static-check.json:140
evidence/2026-10-11-batch13/T-078/09c-caffeinate-parity-rehearsal-02/flow/executor-p1/source-files.json:136
evidence/2026-10-11-batch13/T-078/09c-caffeinate-parity-rehearsal-02/flow/ideation-p1/source-files.json:136
evidence/2026-10-11-batch13/T-078/09c-caffeinate-parity-rehearsal-02/flow/packet/static-check.json:140
evidence/2026-10-11-batch13/T-078/09c-coordinator-rehearsal-01/real-chain-outside-01/flow/executor-p1/source-files.json:129
evidence/2026-10-11-batch13/T-078/09c-coordinator-rehearsal-01/real-chain-outside-01/flow/ideation-p1/source-files.json:129
evidence/2026-10-11-batch13/T-078/09c-coordinator-rehearsal-01/real-chain-outside-01/flow/packet/static-check.json:133
evidence/2026-10-11-batch13/T-078/09c-executable-materials-01/source-files.json:154
evidence/2026-10-11-batch13/T-078/09c-executable-materials-01/static-check.json:156
evidence/2026-10-11-batch13/T-078/09c-executable-materials-02/source-files.json:154
evidence/2026-10-11-batch13/T-078/09c-executable-materials-02/static-check.json:156
evidence/2026-10-11-batch13/T-078/09c-executable-materials-03/source-files.json:154
evidence/2026-10-11-batch13/T-078/09c-executable-materials-03/static-check.json:156
evidence/2026-10-11-batch13/T-078/09c-executable-materials-04/source-files.json:154
evidence/2026-10-11-batch13/T-078/09c-executable-materials-04/static-check.json:156
evidence/2026-10-11-batch13/T-078/09c-executable-materials-05/source-files.json:154
evidence/2026-10-11-batch13/T-078/09c-executable-materials-05/static-check.json:156
evidence/2026-10-11-batch13/T-078/09c-fix-01/real-chain-outside-01/flow/executor-p1/source-files.json:128
evidence/2026-10-11-batch13/T-078/09c-fix-01/real-chain-outside-01/flow/ideation-p1/source-files.json:128
evidence/2026-10-11-batch13/T-078/09c-fix-01/real-chain-outside-02/flow/executor-p1/source-files.json:128
evidence/2026-10-11-batch13/T-078/09c-fix-01/real-chain-outside-02/flow/ideation-p1/source-files.json:128
evidence/2026-10-11-batch13/T-078/09c-fix-01/real-chain-outside-03/flow/executor-p1/source-files.json:128
evidence/2026-10-11-batch13/T-078/09c-fix-01/real-chain-outside-03/flow/ideation-p1/source-files.json:128
evidence/2026-10-11-batch13/T-078/09c-materials-01/SOURCE.json:162
evidence/2026-10-11-batch13/T-078/09c-materials-01/prepare.json:15
evidence/2026-10-11-batch13/T-078/09c-topology-probe-run-01/ideation-p1/source-files.json:129
evidence/2026-10-11-batch13/T-078/09c-topology-probe-run-01/packet/static-check.json:133
evidence/2026-10-11-batch13/T-078/stage-a-readback-rebind-01/09B-prepare.json:15
evidence/2026-10-11-batch13/T-078/stage-a-readback-rebind-01/09C-prepare.json:15
evidence/2026-10-14-batch14/T-080/commit-03/run.json:64
evidence/2026-10-14-batch14/T-080/final-01/diff.stdout.bin:532,534,535
evidence/2026-10-14-batch14/T-080/final-01/source-manifest.json:20
evidence/2026-10-14-batch14/T-080/final-01/status.stdout.bin:14
evidence/2026-10-14-batch14/T-080/final-02/diff.stdout.bin:532,534,535
evidence/2026-10-14-batch14/T-080/final-02/source-manifest.json:20
evidence/2026-10-14-batch14/T-080/final-02/status.stdout.bin:14
evidence/2026-10-14-batch14/T-080/final-02/t077-lifecycle-conflicts/source-files.json:85
evidence/2026-10-14-batch14/T-080/final-03/diff.stdout.bin:532,534,535
evidence/2026-10-14-batch14/T-080/final-03/source-manifest.json:20
evidence/2026-10-14-batch14/T-080/final-03/status.stdout.bin:14
evidence/2026-10-14-batch14/T-080/final-03/t077-lifecycle-conflicts/source-files.json:85
evidence/2026-10-14-batch14/T-080/independent-review-01.completed.json:19
evidence/2026-10-14-batch14/T-080/independent-review-01.diff:1526,8145,8147,8148
evidence/2026-10-14-batch14/T-080/independent-review-01.request.json:32
evidence/2026-10-14-batch14/T-080/run-repair-probe-01/diff.stdout.bin:532,534,535
evidence/2026-10-14-batch14/T-080/run-repair-probe-01/status.stdout.bin:14
evidence/2026-10-14-batch14/T-080/schema-readiness-01.json:30
evidence/2026-10-14-batch14/T-080/schema-readiness-02.json:39,98
evidence/2026-10-14-batch14/T-081/6e-full-01/source-manifest.json:78
evidence/2026-10-14-batch14/T-081/6e-full-02/source-manifest.json:78
evidence/2026-10-14-batch14/T-081/6e-regress-rest-02/t077-lifecycle-conflicts/source-files.json:107
evidence/2026-10-14-batch14/T-081/6e-rerun-01/source-manifest.json:78
evidence/2026-10-14-batch14/T-081/6e-rerun-rest-01/t077-lifecycle-conflicts/source-files.json:107
evidence/2026-10-14-batch14/T-081/full-01/source-manifest.json:65
evidence/2026-10-14-batch14/T-081/full-02/source-manifest.json:67
evidence/2026-10-14-batch14/T-081/full-03/source-manifest.json:68
evidence/2026-10-14-batch14/T-081/full-03/t077-lifecycle-conflicts/source-files.json:88
evidence/2026-10-14-batch14/T-081/full-04/source-manifest.json:69
evidence/2026-10-14-batch14/T-081/full-04/t077-lifecycle-conflicts/source-files.json:89
evidence/2026-10-15-batch15/T-082/outside-command-11-01/source.json:113
evidence/2026-10-15-batch15/T-084/regression-03/worktree/source-files.json:85
evidence/2026-10-15-batch15/T-086/RESULTS.md:5,11,100,116,269
evidence/2026-10-15-batch15/T-086/conflict-suite-01/source-files.json:85
evidence/2026-10-15-batch15/T-086/controller-decision-01.md:9,14
evidence/2026-10-15-batch15/T-086/green-01/source-files.json:85
evidence/2026-10-15-batch15/T-086/independent-review-01.md:13,93,105
evidence/2026-10-15-batch15/T-086/independent-review-02.md:17,96,116,142
evidence/2026-10-15-batch15/T-086/lifecycle-managed/source-files.json:85
evidence/2026-10-15-batch15/T-086/red-01/source-files.json:85
evidence/2026-10-15-batch15/T-086/rework-conflict-suite/source-files.json:85
evidence/2026-10-15-batch15/T-086/rework-green-01/source-files.json:85
evidence/2026-10-15-batch15/T-086/rework-m1/source-files.json:85
evidence/2026-10-15-batch15/T-086/rework-m2/source-files.json:85
evidence/2026-10-15-batch15/T-086/rework-m3/source-files.json:85
evidence/2026-10-15-batch15/T-086/rework-m4/source-files.json:85
evidence/2026-10-15-batch15/T-086/rework-m5/source-files.json:85
evidence/2026-10-15-batch15/T-086/rework-red-01/source-files.json:85
evidence/2026-10-15-batch15/executor-report-01.md:4
evidence/2026-10-16-batch16/T-089/independent-review-02.md:159
evidence/2026-10-16-batch16/T-089/reference-audit.md:40
evidence/2026-10-16-batch16/T-089/s3-baseline-local-01/cas/assertion-scope.json:1465,1529
evidence/2026-10-16-batch16/T-089/t086-external-01.json:623
evidence/2026-10-16-batch16/T-089/t086-external-02.json:743
evidence/2026-10-16-batch16/T-089/t086-local-01.json:623
evidence/2026-10-16-batch16/T-089/t086-local-02.json:623
evidence/2026-10-19-batch17/T-105/python39-check-setup-failure-01.json:15,16
evidence/2026-10-23-batch23/T-148/ISSUE-stale-oracles.md:9
evidence/2026-10-23-batch23/T-148/RESULTS.md:55
```

</details>

### R7 `test_t122_claude_worker_e2e.py`

<details>
<summary>工作台 / 其他当前文件：1 个文件</summary>

```text
workbench/README.md:223
```

</details>

<details>
<summary>历史 evidence 可执行文件（含复跑脚本与冻结源码）：14 个文件</summary>

```text
evidence/2026-10-22-batch20/T-123/candidate-1/e2e/commands.sh:20
evidence/2026-10-22-batch20/T-123/candidate-2/e2e/commands.sh:24
evidence/2026-10-22-batch20/T-126/candidate-1/e2e/commands.sh:14
evidence/2026-10-22-batch20/T-126/candidate-2/e2e/commands.sh:11
evidence/2026-10-22-batch20/T-129/candidate-1/e2e/commands.sh:6
evidence/2026-10-22-batch20/T-130/candidate-1/e2e/commands.sh:6
evidence/2026-10-22-batch20/T-131/candidate-1/e2e/commands.sh:15
evidence/2026-10-22-batch20/T-131/candidate-2/e2e/commands.sh:20
evidence/2026-10-22-batch20/T-131/candidate-3/e2e/commands.sh:20
evidence/2026-10-22-batch20/T-132/candidate-1/e2e/commands.sh:13
evidence/2026-10-22-batch20/T-132/candidate-2/e2e/commands.sh:20
evidence/2026-10-22-batch20/T-133-T-134/candidate-1/e2e/commands.sh:18
evidence/2026-10-22-batch20/T-135/candidate-1/e2e/commands.sh:16
evidence/2026-10-22-batch20/T-136/candidate-1/e2e/commands.sh:23
```

</details>

<details>
<summary>其余文本命中（治理记录、报告、摘要、日志等）：210 个文件</summary>

```text
.project-map/inbox/20261023T172046Z-worker:b23-t148-issue-001.md:23
.project-map/inbox/20261023T181004Z-executor-report-001.md:30
.project-map/inbox/20261023T181318Z-ideation-answer-001.md:17
.project-map/tickets/T-148-stale-fixtures-after-t141.md:42
.project-map/tickets/T-149-retire-stale-historical-tests.md:18
evidence/2026-10-21-batch19/T-122/e2e-green-01.json:4
evidence/2026-10-21-batch19/T-122/e2e-green-02.json:4
evidence/2026-10-21-batch19/T-122/e2e-green-03.json:4
evidence/2026-10-21-batch19/T-122/e2e-green-04.json:4
evidence/2026-10-21-batch19/T-122/e2e-green-05.json:4
evidence/2026-10-21-batch19/T-122/e2e-green-06.json:4
evidence/2026-10-21-batch19/T-122/e2e-green-06.log:2,4,6
evidence/2026-10-21-batch19/T-122/e2e-green-07.json:4
evidence/2026-10-21-batch19/T-122/e2e-green-08.json:4
evidence/2026-10-21-batch19/T-122/e2e-green-09-worktree.json:4
evidence/2026-10-21-batch19/T-122/e2e-green-09-worktree.log:2,4,6
evidence/2026-10-21-batch19/T-122/e2e-green-10-worktree.json:4
evidence/2026-10-21-batch19/T-122/e2e-green-11.json:4
evidence/2026-10-21-batch19/T-122/e2e-green-13.json:4
evidence/2026-10-21-batch19/T-122/e2e-green-14.json:4
evidence/2026-10-21-batch19/T-122/e2e-green-15.json:4
evidence/2026-10-21-batch19/T-122/e2e-mutant-card-model-ignored-05.json:4
evidence/2026-10-21-batch19/T-122/e2e-mutant-card-model-ignored-07.json:4
evidence/2026-10-21-batch19/T-122/e2e-mutant-card-model-ignored-07.log:2,4,6
evidence/2026-10-21-batch19/T-122/e2e-mutant-card-model-ignored-08.json:4
evidence/2026-10-21-batch19/T-122/e2e-mutant-card-model-ignored-08.log:2,4,6
evidence/2026-10-21-batch19/T-122/e2e-mutant-card-model-ignored-11.json:4
evidence/2026-10-21-batch19/T-122/e2e-mutant-card-model-ignored-11.log:2,4,6
evidence/2026-10-21-batch19/T-122/e2e-mutant-codex-provider-only-01.json:4
evidence/2026-10-21-batch19/T-122/e2e-mutant-codex-provider-only-03.json:4
evidence/2026-10-21-batch19/T-122/e2e-mutant-codex-provider-only-05.json:4
evidence/2026-10-21-batch19/T-122/e2e-mutant-codex-provider-only-07.json:4
evidence/2026-10-21-batch19/T-122/e2e-mutant-codex-provider-only-07.log:2,4,6
evidence/2026-10-21-batch19/T-122/e2e-mutant-codex-provider-only-08.json:4
evidence/2026-10-21-batch19/T-122/e2e-mutant-codex-provider-only-08.log:2,4,6
evidence/2026-10-21-batch19/T-122/e2e-mutant-codex-provider-only-11.json:4
evidence/2026-10-21-batch19/T-122/e2e-mutant-codex-provider-only-11.log:2,4,6
evidence/2026-10-21-batch19/T-122/e2e-mutant-dotgit-file-writable-07.json:4
evidence/2026-10-21-batch19/T-122/e2e-mutant-gate-reviewer-executable-compared-12.json:4
evidence/2026-10-21-batch19/T-122/e2e-mutant-gate-reviewer-executable-compared-12.log:2,4
evidence/2026-10-21-batch19/T-122/e2e-mutant-gate-reviewer-fast-unchecked-11.json:4
evidence/2026-10-21-batch19/T-122/e2e-mutant-gate-reviewer-fast-unchecked-11.log:2,4,6
evidence/2026-10-21-batch19/T-122/e2e-mutant-gate-reviewer-hook-includes-11.json:4
evidence/2026-10-21-batch19/T-122/e2e-mutant-gate-reviewer-hook-includes-11.log:2,4,6
evidence/2026-10-21-batch19/T-122/e2e-mutant-gate-reviewer-model-unchecked-11.json:4
evidence/2026-10-21-batch19/T-122/e2e-mutant-gate-reviewer-model-unchecked-11.log:2,4,6
evidence/2026-10-21-batch19/T-122/e2e-mutant-git-deny-missing-05.json:4
evidence/2026-10-21-batch19/T-122/e2e-mutant-git-deny-missing-07.json:4
evidence/2026-10-21-batch19/T-122/e2e-mutant-git-deny-missing-07.log:2,4,6
evidence/2026-10-21-batch19/T-122/e2e-mutant-git-deny-missing-08.json:4
evidence/2026-10-21-batch19/T-122/e2e-mutant-git-deny-missing-08.log:2,4,6
evidence/2026-10-21-batch19/T-122/e2e-mutant-git-deny-missing-11.json:4
evidence/2026-10-21-batch19/T-122/e2e-mutant-git-deny-missing-11.log:2,4,6
evidence/2026-10-21-batch19/T-122/e2e-mutant-git-excluded-broad-07.json:4
evidence/2026-10-21-batch19/T-122/e2e-mutant-git-excluded-broad-07.log:2,4,6
evidence/2026-10-21-batch19/T-122/e2e-mutant-git-excluded-broad-08.json:4
evidence/2026-10-21-batch19/T-122/e2e-mutant-git-excluded-broad-08.log:2,4,6
evidence/2026-10-21-batch19/T-122/e2e-mutant-git-excluded-broad-11.json:4
evidence/2026-10-21-batch19/T-122/e2e-mutant-git-excluded-broad-11.log:2,4,6
evidence/2026-10-21-batch19/T-122/e2e-mutant-inbox-tasks-only-01.json:4
evidence/2026-10-21-batch19/T-122/e2e-mutant-inbox-tasks-only-03.json:4
evidence/2026-10-21-batch19/T-122/e2e-mutant-inbox-tasks-only-05.json:4
evidence/2026-10-21-batch19/T-122/e2e-mutant-inbox-tasks-only-07.json:4
evidence/2026-10-21-batch19/T-122/e2e-mutant-inbox-tasks-only-07.log:2,4,6
evidence/2026-10-21-batch19/T-122/e2e-mutant-inbox-tasks-only-08.json:4
evidence/2026-10-21-batch19/T-122/e2e-mutant-inbox-tasks-only-08.log:2,4,6
evidence/2026-10-21-batch19/T-122/e2e-mutant-inbox-tasks-only-11.json:4
evidence/2026-10-21-batch19/T-122/e2e-mutant-inbox-tasks-only-11.log:2,4,6
evidence/2026-10-21-batch19/T-122/e2e-mutant-no-initial-release-01.json:4
evidence/2026-10-21-batch19/T-122/e2e-mutant-no-initial-release-02.json:4
evidence/2026-10-21-batch19/T-122/e2e-mutant-no-initial-release-03.json:4
evidence/2026-10-21-batch19/T-122/e2e-mutant-no-initial-release-05.json:4
evidence/2026-10-21-batch19/T-122/e2e-mutant-no-initial-release-07.json:4
evidence/2026-10-21-batch19/T-122/e2e-mutant-no-initial-release-07.log:2,4,6
evidence/2026-10-21-batch19/T-122/e2e-mutant-no-initial-release-08.json:4
evidence/2026-10-21-batch19/T-122/e2e-mutant-no-initial-release-08.log:2,4,6
evidence/2026-10-21-batch19/T-122/e2e-mutant-no-initial-release-11.json:4
evidence/2026-10-21-batch19/T-122/e2e-mutant-no-initial-release-11.log:2,4,6
evidence/2026-10-21-batch19/T-122/e2e-mutant-no-terminal-parent-01.json:4
evidence/2026-10-21-batch19/T-122/e2e-mutant-no-terminal-parent-03.json:4
evidence/2026-10-21-batch19/T-122/e2e-mutant-no-terminal-parent-05.json:4
evidence/2026-10-21-batch19/T-122/e2e-mutant-no-terminal-parent-07.json:4
evidence/2026-10-21-batch19/T-122/e2e-mutant-no-terminal-parent-07.log:2,4,6
evidence/2026-10-21-batch19/T-122/e2e-mutant-no-terminal-parent-08.json:4
evidence/2026-10-21-batch19/T-122/e2e-mutant-no-terminal-parent-08.log:2,4,6
evidence/2026-10-21-batch19/T-122/e2e-mutant-no-terminal-parent-11.json:4
evidence/2026-10-21-batch19/T-122/e2e-mutant-no-terminal-parent-11.log:2,4,6
evidence/2026-10-21-batch19/T-122/e2e-mutant-requested-model-as-fact-05.json:4
evidence/2026-10-21-batch19/T-122/e2e-mutant-requested-model-as-fact-07.json:4
evidence/2026-10-21-batch19/T-122/e2e-mutant-requested-model-as-fact-07.log:2,4,6
evidence/2026-10-21-batch19/T-122/e2e-mutant-requested-model-as-fact-08.json:4
evidence/2026-10-21-batch19/T-122/e2e-mutant-requested-model-as-fact-08.log:2,4,6
evidence/2026-10-21-batch19/T-122/e2e-mutant-requested-model-as-fact-11.json:4
evidence/2026-10-21-batch19/T-122/e2e-mutant-requested-model-as-fact-11.log:2,4,6
evidence/2026-10-21-batch19/T-122/e2e-mutant-reviewer-codex-only-03.json:4
evidence/2026-10-21-batch19/T-122/e2e-mutant-reviewer-codex-only-05.json:4
evidence/2026-10-21-batch19/T-122/e2e-mutant-reviewer-codex-only-07.json:4
evidence/2026-10-21-batch19/T-122/e2e-mutant-reviewer-codex-only-07.log:2,4
evidence/2026-10-21-batch19/T-122/e2e-mutant-reviewer-codex-only-08.json:4
evidence/2026-10-21-batch19/T-122/e2e-mutant-reviewer-codex-only-08.log:2,4
evidence/2026-10-21-batch19/T-122/e2e-mutant-reviewer-codex-only-11.json:4
evidence/2026-10-21-batch19/T-122/e2e-mutant-reviewer-codex-only-11.log:2,4
evidence/2026-10-21-batch19/T-122/e2e-mutant-reviewer-shell-writable-03.json:4
evidence/2026-10-21-batch19/T-122/e2e-mutant-reviewer-shell-writable-05.json:4
evidence/2026-10-21-batch19/T-122/e2e-mutant-reviewer-shell-writable-07.json:4
evidence/2026-10-21-batch19/T-122/e2e-mutant-reviewer-shell-writable-07.log:2,4
evidence/2026-10-21-batch19/T-122/e2e-mutant-reviewer-shell-writable-08.json:4
evidence/2026-10-21-batch19/T-122/e2e-mutant-reviewer-shell-writable-08.log:2,4
evidence/2026-10-21-batch19/T-122/e2e-mutant-reviewer-shell-writable-11.json:4
evidence/2026-10-21-batch19/T-122/e2e-mutant-reviewer-shell-writable-11.log:2,4
evidence/2026-10-21-batch19/T-122/e2e-mutant-submit-provider-codex-05.json:4
evidence/2026-10-21-batch19/T-122/e2e-mutant-submit-provider-codex-07.json:4
evidence/2026-10-21-batch19/T-122/e2e-mutant-submit-provider-codex-07.log:2,4,6
evidence/2026-10-21-batch19/T-122/e2e-mutant-submit-provider-codex-08.json:4
evidence/2026-10-21-batch19/T-122/e2e-mutant-submit-provider-codex-08.log:2,4,6
evidence/2026-10-21-batch19/T-122/e2e-mutant-submit-provider-codex-11.json:4
evidence/2026-10-21-batch19/T-122/e2e-mutant-submit-provider-codex-11.log:2,4,6
evidence/2026-10-21-batch19/T-122/e2e-mutant-trust-unanswered-01.json:4
evidence/2026-10-21-batch19/T-122/e2e-mutant-trust-unanswered-03.json:4
evidence/2026-10-21-batch19/T-122/e2e-mutant-trust-unanswered-05.json:4
evidence/2026-10-21-batch19/T-122/e2e-mutant-trust-unanswered-07.json:4
evidence/2026-10-21-batch19/T-122/e2e-mutant-trust-unanswered-07.log:2,4,6
evidence/2026-10-21-batch19/T-122/e2e-mutant-trust-unanswered-08.json:4
evidence/2026-10-21-batch19/T-122/e2e-mutant-trust-unanswered-08.log:2,4,6
evidence/2026-10-21-batch19/T-122/e2e-mutant-trust-unanswered-11.json:4
evidence/2026-10-21-batch19/T-122/e2e-mutant-trust-unanswered-11.log:2,4,6
evidence/2026-10-21-batch19/T-122/e2e-mutant-user-settings-loaded-01.json:4
evidence/2026-10-21-batch19/T-122/e2e-mutant-user-settings-loaded-02.json:4
evidence/2026-10-21-batch19/T-122/e2e-mutant-user-settings-loaded-03.json:4
evidence/2026-10-21-batch19/T-122/e2e-mutant-user-settings-loaded-05.json:4
evidence/2026-10-21-batch19/T-122/e2e-mutant-user-settings-loaded-07.json:4
evidence/2026-10-21-batch19/T-122/e2e-mutant-user-settings-loaded-07.log:2,4,6
evidence/2026-10-21-batch19/T-122/e2e-mutant-user-settings-loaded-08.json:4
evidence/2026-10-21-batch19/T-122/e2e-mutant-user-settings-loaded-08.log:2,4,6
evidence/2026-10-21-batch19/T-122/e2e-mutant-user-settings-loaded-11.json:4
evidence/2026-10-21-batch19/T-122/e2e-mutant-user-settings-loaded-11.log:2,4,6
evidence/2026-10-21-batch19/T-122/e2e-red-01.json:4
evidence/2026-10-21-batch19/T-122/e2e-red-02.json:4
evidence/2026-10-21-batch19/T-122/e2e-red-03.json:4
evidence/2026-10-21-batch19/T-122/e2e-red-05.json:4
evidence/2026-10-21-batch19/T-122/e2e-red-07-candidate2.json:4
evidence/2026-10-21-batch19/T-122/e2e-red-07-candidate2.log:2,4,6
evidence/2026-10-21-batch19/T-122/e2e-red-08-candidate2.json:4
evidence/2026-10-21-batch19/T-122/e2e-red-08-candidate2.log:2,4,6
evidence/2026-10-21-batch19/T-122/e2e-red-11-candidate3.json:4
evidence/2026-10-21-batch19/T-122/e2e-red-11-candidate3.log:2,4,6
evidence/2026-10-21-batch19/T-122/e2e-red-11-reviewer-other-executable-path.json:4
evidence/2026-10-21-batch19/T-122/e2e-red-11-reviewer-other-executable-path.log:2,4,6
evidence/2026-10-21-batch19/T-122/e2e-reviewer-fast-differs-11.json:4
evidence/2026-10-21-batch19/T-122/e2e-reviewer-hook-prefixed-11.json:4
evidence/2026-10-21-batch19/T-122/e2e-reviewer-model-differs-11.json:4
evidence/2026-10-21-batch19/T-122/e2e-reviewer-other-executable-path-11.json:4
evidence/2026-10-21-batch19/T-122/e2e-reviewer-other-executable-path-11.log:2,4,6
evidence/2026-10-21-batch19/T-122/e2e-reviewer-other-executable-path-12.json:4
evidence/2026-10-21-batch19/T-122/regress-t112-native-01.json:36,50
evidence/2026-10-21-batch19/T-122/regress-t112-native-03.json:91
evidence/2026-10-21-batch19/T-122/regress-t112-native-04.json:5429
evidence/2026-10-21-batch19/T-122/regress-t112-native-05.json:5310
evidence/2026-10-21-batch19/T-122/regress-t112-native-06.json:5429
evidence/2026-10-21-batch19/T-122/regress-t112-native-07.json:91
evidence/2026-10-21-batch19/T-122/regress-t112-native-08.json:233
evidence/2026-10-21-batch19/T-122/regress-t112-native-09.json:5429
evidence/2026-10-21-batch19/T-122/regress-t112-native-10.json:5417
evidence/2026-10-21-batch19/T-122/regress-t112-native-11.json:5415
evidence/2026-10-21-batch19/T-122/review-03-probe/green-c13befd85.json:4
evidence/2026-10-22-batch20/T-123/candidate-1/e2e/superseded-01-duplicate-daemon-check/t122-green.json:4
evidence/2026-10-22-batch20/T-123/candidate-1/e2e/t122-green.json:4
evidence/2026-10-22-batch20/T-123/candidate-2/e2e/t122-green.json:4
evidence/2026-10-22-batch20/T-126/candidate-1/e2e/t122-green.json:4
evidence/2026-10-22-batch20/T-126/candidate-2/e2e/t122-green.json:4
evidence/2026-10-22-batch20/T-127/regress-t112-native-01.json:5333
evidence/2026-10-22-batch20/T-127/regress-t112-native-02.json:5323
evidence/2026-10-22-batch20/T-127/regress-t112-native-03.json:5337
evidence/2026-10-22-batch20/T-127/regress-t122-e2e-01.json:4
evidence/2026-10-22-batch20/T-127/regress-t122-e2e-02.json:4
evidence/2026-10-22-batch20/T-127/regress-t122-e2e-03.json:4
evidence/2026-10-22-batch20/T-129/candidate-1/RESULTS.md:26
evidence/2026-10-22-batch20/T-129/candidate-1/e2e/green-malformed.json:4
evidence/2026-10-22-batch20/T-129/candidate-1/e2e/green-rejected.json:4
evidence/2026-10-22-batch20/T-129/candidate-1/e2e/red-parent-malformed.json:4
evidence/2026-10-22-batch20/T-129/candidate-1/e2e/red-parent-malformed.log:2,4,6,8
evidence/2026-10-22-batch20/T-129/candidate-1/e2e/red-parent-rejected.json:4
evidence/2026-10-22-batch20/T-129/candidate-1/e2e/red-parent-rejected.log:2,4,6,8
evidence/2026-10-22-batch20/T-129/candidate-1/e2e/red-protocol-failure-unbound.json:4
evidence/2026-10-22-batch20/T-129/candidate-1/e2e/red-protocol-failure-unbound.log:2,4,6,8
evidence/2026-10-22-batch20/T-129/candidate-1/e2e/red-rejection-unbound.json:4
evidence/2026-10-22-batch20/T-129/candidate-1/e2e/red-rejection-unbound.log:2,4,6,8
evidence/2026-10-22-batch20/T-129/candidate-1/e2e/t122-green.json:4
evidence/2026-10-22-batch20/T-129/candidate-1/review-01-prompt.txt:5
evidence/2026-10-22-batch20/T-129/candidate-1/review-01.md:6,45
evidence/2026-10-22-batch20/T-130/candidate-1/e2e/red-parent.json:4
evidence/2026-10-22-batch20/T-130/candidate-1/e2e/red-parent.log:2,4,6
evidence/2026-10-22-batch20/T-130/candidate-1/e2e/t122-green.json:4
evidence/2026-10-22-batch20/T-130/candidate-1/e2e/t129-malformed.json:4
evidence/2026-10-22-batch20/T-130/candidate-1/e2e/t129-rejected.json:4
evidence/2026-10-22-batch20/T-130/candidate-1/review-01-prompt.txt:6
evidence/2026-10-22-batch20/T-130/candidate-1/review-01.md:46
evidence/2026-10-22-batch20/T-131/candidate-1/e2e/t122-green.json:4
evidence/2026-10-22-batch20/T-131/candidate-2/e2e/t122-green.json:4
evidence/2026-10-22-batch20/T-131/candidate-3/e2e/t122-green.json:4
evidence/2026-10-22-batch20/T-132/candidate-1/e2e/t122-green.json:4
evidence/2026-10-22-batch20/T-132/candidate-2/e2e/t122-green.json:4
evidence/2026-10-22-batch20/T-133-T-134/candidate-1/e2e/t122-green.json:4
evidence/2026-10-22-batch20/T-135/candidate-1/e2e/t122-green.json:4
evidence/2026-10-22-batch20/T-135/candidate-1/review-01.md:67
evidence/2026-10-22-batch20/T-136/candidate-1/e2e/t122-green.json:4
evidence/2026-10-23-batch21/release-0.1.2/credential-scan-01.json:263,311,317,329,359,365,371,377,383
evidence/2026-10-23-batch23/T-148/ISSUE-stale-oracles.md:10
evidence/2026-10-23-batch23/T-148/RESULTS.md:55
evidence/2026-10-23-batch23/T-148/stale-contract-search.txt:11,12
```

</details>

### R8 `run_t112_native.py`

<details>
<summary>工作台 / 其他当前文件：1 个文件</summary>

```text
workbench/tests/test_t112_closed_fixture.py:15
```

</details>

<details>
<summary>历史 evidence 可执行文件（含复跑脚本与冻结源码）：18 个文件</summary>

```text
evidence/2026-10-20-batch18/T-112/CHECK-WORKER-STARTUP-10.py:14
evidence/2026-10-20-batch18/T-112/REVIEW-OUTSIDE-01.sh:170,172
evidence/2026-10-20-batch18/T-112/RUN-MERGE-REGRESSIONS-13.py:72
evidence/2026-10-20-batch18/T-112/RUN-OUTSIDE-COMMIT-01.sh:18
evidence/2026-10-20-batch18/T-112/RUN-OUTSIDE-COMMIT-02.sh:18
evidence/2026-10-20-batch18/T-112/RUN-OUTSIDE-COMMIT-03.sh:18
evidence/2026-10-20-batch18/T-112/RUN-OUTSIDE-COMMIT-06.sh:18
evidence/2026-10-20-batch18/T-112/RUN-OUTSIDE-COMMIT-07.sh:19
evidence/2026-10-20-batch18/T-112/RUN-OUTSIDE-COMMIT-08.sh:18
evidence/2026-10-20-batch18/T-112/RUN-OUTSIDE-COMMIT-10.sh:18
evidence/2026-10-20-batch18/T-112/RUN-OUTSIDE-COMMIT-12.sh:18
evidence/2026-10-20-batch18/T-112/RUN-OUTSIDE-NATIVE-01.sh:8
evidence/2026-10-20-batch18/T-112/RUN-OUTSIDE-NATIVE-02.sh:8
evidence/2026-10-20-batch18/T-112/RUN-OUTSIDE-NATIVE-03.sh:8
evidence/2026-10-20-batch18/T-112/RUN-OUTSIDE-NATIVE-04.sh:8
evidence/2026-10-20-batch18/T-112/RUN-OUTSIDE-NATIVE-05.sh:8
evidence/2026-10-20-batch18/T-112/RUN-OUTSIDE-NATIVE-06.sh:8
evidence/2026-10-20-batch18/T-112/RUN-OUTSIDE-NATIVE-07.sh:8
```

</details>

<details>
<summary>其余文本命中（治理记录、报告、摘要、日志等）：44 个文件</summary>

```text
.project-map/inbox/20261020T152634Z-worker:s18-t112-issue-001.md:6,20
.project-map/inbox/20261023T172046Z-worker:b23-t148-issue-001.md:24
.project-map/inbox/20261023T181004Z-executor-report-001.md:30
.project-map/inbox/20261023T181318Z-ideation-answer-001.md:17
.project-map/tickets/T-148-stale-fixtures-after-t141.md:21,37,42
.project-map/tickets/T-149-retire-stale-historical-tests.md:18
evidence/2026-10-20-batch18/T-112/ISSUE-INVALID-EFFORT-11.md:7
evidence/2026-10-20-batch18/T-112/RESULTS.md:35,94
evidence/2026-10-20-batch18/T-112/closed-fixture-red-01.json:30
evidence/2026-10-20-batch18/T-112/independent-review-01.md:9
evidence/2026-10-20-batch18/T-112/native-rev12-static-01.json:5
evidence/2026-10-20-batch18/T-112/native-rev8-static-01.json:5,17,21
evidence/2026-10-20-batch18/T-112/outside-merge-regressions-03.json:121
evidence/2026-10-20-batch18/T-112/outside-merge-t112-native-03.json:5421
evidence/2026-10-20-batch18/T-112/outside-native-01.json:52
evidence/2026-10-20-batch18/T-112/outside-native-02.json:238
evidence/2026-10-20-batch18/T-112/outside-native-03.json:274
evidence/2026-10-20-batch18/T-112/outside-native-04.json:58
evidence/2026-10-20-batch18/T-112/outside-native-05.json:4503,4592
evidence/2026-10-20-batch18/T-112/outside-native-06.json:4762,4949
evidence/2026-10-20-batch18/T-112/outside-native-07.json:5391
evidence/2026-10-20-batch18/T-112/protocol-rev7-static-final-01.json:7
evidence/2026-10-20-batch18/T-112/protocol-rev7-static-final-02.json:7
evidence/2026-10-20-batch18/T-112/search-rev8-01.json:24
evidence/2026-10-20-batch18/T-112/search-rev9-01.json:22
evidence/2026-10-21-batch19/T-122/regress-t112-native-01.json:53
evidence/2026-10-21-batch19/T-122/regress-t112-native-02.json:60
evidence/2026-10-21-batch19/T-122/regress-t112-native-03.json:91,133
evidence/2026-10-21-batch19/T-122/regress-t112-native-04.json:5429
evidence/2026-10-21-batch19/T-122/regress-t112-native-05.json:5310,5497
evidence/2026-10-21-batch19/T-122/regress-t112-native-06.json:5429
evidence/2026-10-21-batch19/T-122/regress-t112-native-07.json:91,154
evidence/2026-10-21-batch19/T-122/regress-t112-native-08.json:233,296
evidence/2026-10-21-batch19/T-122/regress-t112-native-09.json:5429
evidence/2026-10-21-batch19/T-122/regress-t112-native-10.json:5417
evidence/2026-10-21-batch19/T-122/regress-t112-native-11.json:5415
evidence/2026-10-22-batch20/T-127/regress-t112-native-01.json:5333
evidence/2026-10-22-batch20/T-127/regress-t112-native-02.json:5323
evidence/2026-10-22-batch20/T-127/regress-t112-native-03.json:5337
evidence/2026-10-23-batch23/T-148/ISSUE-stale-oracles.md:11
evidence/2026-10-23-batch23/T-148/RESULTS.md:15,54,55
evidence/2026-10-23-batch23/T-148/oracle-preservation-local-01.json:10
evidence/2026-10-23-batch23/T-148/review-agy-01.md:43,211
evidence/2026-10-23-batch23/T-148/stale-contract-search.txt:10
```

</details>

### R9 `t112_reviewer_record.mjs`

<details>
<summary>工作台 / 其他当前文件：2 个文件</summary>

```text
workbench/tests/diagnose_t112_reviewer.py:116
workbench/tests/test_t112_reviewer_startup.mjs:7
```

</details>

<details>
<summary>历史 evidence 可执行文件（含复跑脚本与冻结源码）：5 个文件</summary>

```text
evidence/2026-10-20-batch18/T-112/RUN-OUTSIDE-COMMIT-04.sh:18
evidence/2026-10-20-batch18/T-112/RUN-OUTSIDE-COMMIT-05.sh:18
evidence/2026-10-20-batch18/T-112/RUN-OUTSIDE-COMMIT-06.sh:18
evidence/2026-10-20-batch18/T-112/RUN-OUTSIDE-COMMIT-07.sh:19
evidence/2026-10-20-batch18/T-112/RUN-OUTSIDE-COMMIT-08.sh:18
```

</details>

<details>
<summary>其余文本命中（治理记录、报告、摘要、日志等）：15 个文件</summary>

```text
.project-map/inbox/20261023T172046Z-worker:b23-t148-issue-001.md:25
.project-map/inbox/20261023T181004Z-executor-report-001.md:30
.project-map/inbox/20261023T181318Z-ideation-answer-001.md:17
.project-map/tickets/T-148-stale-fixtures-after-t141.md:21,37,42
.project-map/tickets/T-149-retire-stale-historical-tests.md:18
evidence/2026-10-20-batch18/T-112/outside-reviewer-diag-01.json:74,233,392
evidence/2026-10-20-batch18/T-112/outside-reviewer-diag-02.json:57,58
evidence/2026-10-20-batch18/T-112/reviewer-metadata-01.json:74,87,100
evidence/2026-10-20-batch18/T-112/reviewer-startup-green-01.json:62,100,134
evidence/2026-10-20-batch18/T-112/reviewer-startup-red-01.json:7
evidence/2026-10-20-batch18/T-112/reviewer-startup-red-02.json:22
evidence/2026-10-23-batch23/T-148/ISSUE-stale-oracles.md:12
evidence/2026-10-23-batch23/T-148/RESULTS.md:14,54
evidence/2026-10-23-batch23/T-148/oracle-preservation-local-01.json:15
evidence/2026-10-23-batch23/T-148/review-agy-01.md:48
```

</details>

### R10 `controlled_quality_pty.ts`

<details>
<summary>工作台 / 其他当前文件：6 个文件</summary>

```text
workbench/tests/conflict_acceptance_host.ts:5
workbench/tests/daemon_acceptance_host.ts:10
workbench/tests/legacy_review_runtime.ts:2
workbench/tests/multiturn_identity_host.ts:6
workbench/tests/quality_chain_host.ts:6
workbench/tests/run_daemon_acceptance.py:102
```

</details>

<details>
<summary>历史 evidence 可执行文件（含复跑脚本与冻结源码）：23 个文件</summary>

```text
evidence/2026-10-11-batch13/T-076/card-2/check-final-delivery.py:34
evidence/2026-10-11-batch13/T-076/card-2/check-legacy-preparation.py:37
evidence/2026-10-11-batch13/T-076/card-2/delivery-review-01/candidate/workbench/tests/daemon_acceptance_host.ts:9
evidence/2026-10-11-batch13/T-076/card-2/delivery-review-01/candidate/workbench/tests/legacy_review_runtime.ts:2
evidence/2026-10-11-batch13/T-076/card-2/delivery-review-01/candidate/workbench/tests/multiturn_identity_host.ts:6
evidence/2026-10-11-batch13/T-076/card-2/delivery-review-01/candidate/workbench/tests/quality_chain_host.ts:6
evidence/2026-10-11-batch13/T-076/card-2/delivery-review-01/candidate/workbench/tests/run_daemon_acceptance.py:102
evidence/2026-10-11-batch13/T-076/card-2/fixture-path-repair-01/check_paths.py:58,123
evidence/2026-10-11-batch13/T-076/card-2/fixture-path-repair-01/offline-02/probe.mjs:8
evidence/2026-10-11-batch13/T-077/check-rebase-final-02-preparation.py:23
evidence/2026-10-11-batch13/T-077/check-rebase-final-03-preparation.py:23
evidence/2026-10-11-batch13/T-077/check-rebase-final-04-preparation.py:23
evidence/2026-10-11-batch13/T-077/check-rebase-final-05-preparation.py:24
evidence/2026-10-11-batch13/T-077/check-rebase-final-preparation.py:23
evidence/2026-10-11-batch13/T-077/final05-boundaries-before/preflight-at-run.py:43
evidence/2026-10-11-batch13/T-077/preflight-boundaries-05.py:45
evidence/2026-10-11-batch13/T-078/merge-main-3-outside-02/fixture-source/workbench/tests/quality_chain_host.ts:6
evidence/2026-10-11-batch13/T-078/rebase-continue-01/resolved/workbench/tests/daemon_acceptance_host.ts:10
evidence/2026-10-11-batch13/T-078/rebase-continue-01/unresolved/workbench/tests/daemon_acceptance_host.ts:14
evidence/2026-10-14-batch14/T-080/probe_run_repair_outside.py:199
evidence/2026-10-15-batch15/T-082/REVIEW-OUTSIDE-01.sh:34
evidence/2026-10-15-batch15/T-082/REVIEW-OUTSIDE-02.sh:38,195
evidence/2026-10-15-batch15/T-084/independent-review-01-probe/t084-review-probe.py:227
```

</details>

<details>
<summary>其余文本命中（治理记录、报告、摘要、日志等）：217 个文件</summary>

```text
.project-map/inbox/20261023T172046Z-worker:b23-t148-issue-001.md:26
.project-map/inbox/20261023T181004Z-executor-report-001.md:30
.project-map/inbox/20261023T181318Z-ideation-answer-001.md:17
.project-map/tickets/T-076-quality-chain-scoring.md:88
.project-map/tickets/T-148-stale-fixtures-after-t141.md:42
.project-map/tickets/T-149-retire-stale-historical-tests.md:18
evidence/2026-10-11-batch13/T-076/card-2/F05-migration-list.md:82
evidence/2026-10-11-batch13/T-076/card-2/RESULTS.md:309,366
evidence/2026-10-11-batch13/T-076/card-2/assertion-hunks.md:162,189,228
evidence/2026-10-11-batch13/T-076/card-2/delivery-review-01/candidate/CANDIDATE.diff:1861,1945,2040
evidence/2026-10-11-batch13/T-076/card-2/delivery-review-01/manifest.json:82
evidence/2026-10-11-batch13/T-076/card-2/evidence-staging-check-01/cached-check.stdout:126,129
evidence/2026-10-11-batch13/T-076/card-2/evidence-staging-check-01/run.json:270,344,354
evidence/2026-10-11-batch13/T-076/card-2/evidence-staging-check-02/run.json:27,29
evidence/2026-10-11-batch13/T-076/card-2/final-delivery-check-01/run.json:54,59
evidence/2026-10-11-batch13/T-076/card-2/final-delivery-check-02/run.json:54,59
evidence/2026-10-11-batch13/T-076/card-2/fixture-path-repair-01/README.md:9
evidence/2026-10-11-batch13/T-076/card-2/fixture-path-repair-01/offline-01/check_paths.py.before-fix:57,122
evidence/2026-10-11-batch13/T-076/card-2/fixture-path-repair-01/offline-02/controlled_quality_pty.ts.diff:1,2
evidence/2026-10-11-batch13/T-076/card-2/legacy-preparation-checks.json:45,162,240,354
evidence/2026-10-11-batch13/T-076/card-2/legacy-ready-checks-01.json:43,160,238,353
evidence/2026-10-11-batch13/T-076/card-2/legacy-ready-checks-02.json:43,160,238,355
evidence/2026-10-11-batch13/T-076/card-2/legacy-ready-checks-03.json:43,160,238,355
evidence/2026-10-11-batch13/T-076/card-2/legacy-ready-checks-04.json:43,160,238,355
evidence/2026-10-11-batch13/T-076/card-2/legacy-ready-checks-05.json:43,160,238,355
evidence/2026-10-11-batch13/T-076/card-2/legacy-ready-checks-06.json:43,160,238,355
evidence/2026-10-11-batch13/T-076/card-2/outside-delivery-review-01/commands.jsonl:3
evidence/2026-10-11-batch13/T-076/card-2/outside-delivery-review-01/native-sessions/2026/10/13/rollout-2026-10-13T12-00-00-01a135fd-fd26-7693-a738-ad75036b220e.jsonl:26,29,36,39,89,90,163,164,201,202
evidence/2026-10-11-batch13/T-076/card-2/outside-delivery-review-01/setup.json:69
evidence/2026-10-11-batch13/T-076/card-2/outside-legacy-green-01/source.json:114
evidence/2026-10-11-batch13/T-076/card-2/outside-legacy-green-01/w07-red/source-manifest.json:54
evidence/2026-10-11-batch13/T-076/card-2/outside-legacy-green-02/source.json:114
evidence/2026-10-11-batch13/T-076/card-2/outside-legacy-green-02/w07-red/source-manifest.json:54
evidence/2026-10-11-batch13/T-076/card-2/outside-legacy-green-03/source.json:114
evidence/2026-10-11-batch13/T-076/card-2/outside-legacy-green-03/w07-red/source-manifest.json:54
evidence/2026-10-11-batch13/T-076/card-2/outside-legacy-green-04/coop/source-manifest.json:54
evidence/2026-10-11-batch13/T-076/card-2/outside-legacy-green-04/recovery/source-manifest.json:54
evidence/2026-10-11-batch13/T-076/card-2/outside-legacy-green-04/source.json:114
evidence/2026-10-11-batch13/T-076/card-2/outside-legacy-green-04/w07-red/source-manifest.json:54
evidence/2026-10-11-batch13/T-076/card-2/outside-legacy-green-05/coop/source-manifest.json:54
evidence/2026-10-11-batch13/T-076/card-2/outside-legacy-green-05/recovery/source-manifest.json:54
evidence/2026-10-11-batch13/T-076/card-2/outside-legacy-green-05/run/source-manifest.json:54
evidence/2026-10-11-batch13/T-076/card-2/outside-legacy-green-05/source.json:114
evidence/2026-10-11-batch13/T-076/card-2/outside-legacy-green-05/w07-red/source-manifest.json:54
evidence/2026-10-11-batch13/T-076/card-2/outside-legacy-green-06/coop/source-manifest.json:54
evidence/2026-10-11-batch13/T-076/card-2/outside-legacy-green-06/recovery/source-manifest.json:54
evidence/2026-10-11-batch13/T-076/card-2/outside-legacy-green-06/run/source-manifest.json:54
evidence/2026-10-11-batch13/T-076/card-2/outside-legacy-green-06/source.json:114
evidence/2026-10-11-batch13/T-076/card-2/outside-legacy-green-06/w07-red/source-manifest.json:54
evidence/2026-10-11-batch13/T-076/card-2/p-review-01/source-manifest.json:60
evidence/2026-10-11-batch13/T-076/card-2/p-review-02/source-manifest.json:60
evidence/2026-10-11-batch13/T-076/card-2/postcommit-readback-01/run.json:79
evidence/2026-10-11-batch13/T-076/card-2/real-delivery-01/source-manifest.json:59
evidence/2026-10-11-batch13/T-076/card-2/real-delivery-02/source-manifest.json:59
evidence/2026-10-11-batch13/T-076/card-2/real-delivery-preparation-01/source-manifest.json:59
evidence/2026-10-11-batch13/T-076/card-2/real-delivery-preparation-02/source-manifest.json:59
evidence/2026-10-11-batch13/T-076/card-2/real-delivery-preparation-03/source-manifest.json:59
evidence/2026-10-11-batch13/T-076/card-2/source-commit-check-02/run.json:54,59
evidence/2026-10-11-batch13/T-076/card-2/source-commit.json:21
evidence/2026-10-11-batch13/T-076/card-2/source-staging-check-01/format-only.diff:1,3,4
evidence/2026-10-11-batch13/T-076/card-2/source-staging-check-01/run.json:10
evidence/2026-10-11-batch13/T-076/card-2/source-staging-check-02/run.json:28
evidence/2026-10-11-batch13/T-077/HANDOFF-rebase-final-01.md:40
evidence/2026-10-11-batch13/T-077/commit-review-worktree-files.json:1236
evidence/2026-10-11-batch13/T-077/conflict-red-final-01-preparation-01/plan.json:161
evidence/2026-10-11-batch13/T-077/conflict-red-final-01-preparation-02/plan.json:194
evidence/2026-10-11-batch13/T-077/final05-boundaries-before/commands.jsonl:37,38
evidence/2026-10-11-batch13/T-077/final05-boundaries-before/run.json:183,187
evidence/2026-10-11-batch13/T-077/independent-review-01.md:67
evidence/2026-10-11-batch13/T-077/independent-review-product-01.diff:2128,2211,2213,2214
evidence/2026-10-11-batch13/T-077/outside-conflict-red-final-01/red-01/source-files.json:54
evidence/2026-10-11-batch13/T-077/outside-conflict-red-final-01/red-02/source-files.json:54
evidence/2026-10-11-batch13/T-077/outside-conflict-red-final-01/red-03/source-files.json:54
evidence/2026-10-11-batch13/T-077/outside-conflict-red-final-01/red-04/source-files.json:54
evidence/2026-10-11-batch13/T-077/outside-conflict-red-final-02-preparation/plan.json:196
evidence/2026-10-11-batch13/T-077/outside-conflict-red-final-02/candidate/source-files.json:54
evidence/2026-10-11-batch13/T-077/outside-conflict-red-final-02/red-01/source-files.json:54
evidence/2026-10-11-batch13/T-077/outside-conflict-red-final-02/red-02/source-files.json:54
evidence/2026-10-11-batch13/T-077/outside-conflict-red-final-02/red-03/source-files.json:54
evidence/2026-10-11-batch13/T-077/outside-conflict-red-final-02/red-04/source-files.json:54
evidence/2026-10-11-batch13/T-077/outside-conflict-red-final-02/red-05/source-files.json:54
evidence/2026-10-11-batch13/T-077/outside-conflict-red-final-02/red-06/source-files.json:54
evidence/2026-10-11-batch13/T-077/outside-conflict-red-final-02/red-07/source-files.json:54
evidence/2026-10-11-batch13/T-077/outside-rebase-final-01/conflict-red-01/source-files.json:54
evidence/2026-10-11-batch13/T-077/outside-rebase-final-01/conflict-red-02/source-files.json:54
evidence/2026-10-11-batch13/T-077/outside-rebase-final-01/conflict-red-03/source-files.json:54
evidence/2026-10-11-batch13/T-077/outside-rebase-final-01/conflict-red-04/source-files.json:54
evidence/2026-10-11-batch13/T-077/outside-rebase-final-01/conflict-red-05/source-files.json:54
evidence/2026-10-11-batch13/T-077/outside-rebase-final-01/conflict-red-06/source-files.json:54
evidence/2026-10-11-batch13/T-077/outside-rebase-final-01/conflict-red-07/source-files.json:54
evidence/2026-10-11-batch13/T-077/outside-rebase-final-01/s3-all/source-files.json:54
evidence/2026-10-11-batch13/T-077/outside-rebase-final-03/conflict-red-01/source-files.json:54
evidence/2026-10-11-batch13/T-077/outside-rebase-final-03/conflict-red-02/source-files.json:54
evidence/2026-10-11-batch13/T-077/outside-rebase-final-03/conflict-red-03/source-files.json:54
evidence/2026-10-11-batch13/T-077/outside-rebase-final-03/conflict-red-04/source-files.json:54
evidence/2026-10-11-batch13/T-077/outside-rebase-final-03/conflict-red-05/source-files.json:54
evidence/2026-10-11-batch13/T-077/outside-rebase-final-03/conflict-red-06/source-files.json:54
evidence/2026-10-11-batch13/T-077/outside-rebase-final-03/conflict-red-07/source-files.json:54
evidence/2026-10-11-batch13/T-077/outside-rebase-final-03/s3-all/source-files.json:54
evidence/2026-10-11-batch13/T-077/outside-rebase-final-04/conflict-red-01/source-files.json:54
evidence/2026-10-11-batch13/T-077/outside-rebase-final-04/conflict-red-02/source-files.json:54
evidence/2026-10-11-batch13/T-077/outside-rebase-final-04/conflict-red-03/source-files.json:54
evidence/2026-10-11-batch13/T-077/outside-rebase-final-04/conflict-red-04/source-files.json:54
evidence/2026-10-11-batch13/T-077/outside-rebase-final-04/conflict-red-05/source-files.json:54
evidence/2026-10-11-batch13/T-077/outside-rebase-final-04/conflict-red-06/source-files.json:54
evidence/2026-10-11-batch13/T-077/outside-rebase-final-04/conflict-red-07/source-files.json:54
evidence/2026-10-11-batch13/T-077/outside-rebase-final-04/s3-all/source-files.json:54
evidence/2026-10-11-batch13/T-077/outside-rebase-final-05/conflict-red-01/source-files.json:54
evidence/2026-10-11-batch13/T-077/outside-rebase-final-05/conflict-red-02/source-files.json:54
evidence/2026-10-11-batch13/T-077/outside-rebase-final-05/conflict-red-03/source-files.json:54
evidence/2026-10-11-batch13/T-077/outside-rebase-final-05/conflict-red-04/source-files.json:54
evidence/2026-10-11-batch13/T-077/outside-rebase-final-05/conflict-red-05/source-files.json:54
evidence/2026-10-11-batch13/T-077/outside-rebase-final-05/conflict-red-06/source-files.json:54
evidence/2026-10-11-batch13/T-077/outside-rebase-final-05/conflict-red-07/source-files.json:54
evidence/2026-10-11-batch13/T-077/outside-rebase-final-05/s3-all/source-files.json:54
evidence/2026-10-11-batch13/T-077/rebase-final-02-preparation-01/plan.json:129
evidence/2026-10-11-batch13/T-077/rebase-final-02-preparation-01/static-checks.json:50
evidence/2026-10-11-batch13/T-077/rebase-final-03-preparation-01/plan.json:130
evidence/2026-10-11-batch13/T-077/rebase-final-03-preparation-01/static-checks.json:50
evidence/2026-10-11-batch13/T-077/rebase-final-04-preparation-01/plan.json:131
evidence/2026-10-11-batch13/T-077/rebase-final-04-preparation-01/static-checks.json:51
evidence/2026-10-11-batch13/T-077/rebase-final-05-preparation-01/plan.json:145
evidence/2026-10-11-batch13/T-077/rebase-final-05-preparation-01/static-checks.json:51
evidence/2026-10-11-batch13/T-077/rebase-final-preparation-01/plan.json:121,199
evidence/2026-10-11-batch13/T-077/rebase-final-preparation-01/static-checks.json:50
evidence/2026-10-11-batch13/T-077/rebase-final-preparation-02/plan.json:121,199
evidence/2026-10-11-batch13/T-077/rebase-final-preparation-02/static-checks.json:50
evidence/2026-10-11-batch13/T-077/rebase-final-preparation-03/plan.json:121,199
evidence/2026-10-11-batch13/T-077/rebase-final-preparation-03/static-checks.json:50
evidence/2026-10-11-batch13/T-078/09b-a16-b1-executor-p1-01/source-files.json:98
evidence/2026-10-11-batch13/T-078/09b-a16-b1-ideation-p1-01/source-files.json:98
evidence/2026-10-11-batch13/T-078/09b-a16-materials-01/SOURCE.json:106
evidence/2026-10-11-batch13/T-078/09b-a16-materials-01/prepare.json:15
evidence/2026-10-11-batch13/T-078/09b-executable-materials-16-02/source-files.json:98
evidence/2026-10-11-batch13/T-078/09b-executable-materials-16-02/static-check.json:100
evidence/2026-10-11-batch13/T-078/09b-executable-materials-16/source-files.json:98
evidence/2026-10-11-batch13/T-078/09b-executable-materials-16/static-check.json:100
evidence/2026-10-11-batch13/T-078/09c-attempt-2-materials-01/SOURCE.json:137
evidence/2026-10-11-batch13/T-078/09c-attempt-2-materials-01/prepare.json:15
evidence/2026-10-11-batch13/T-078/09c-attempt-2-materials-02/SOURCE.json:141
evidence/2026-10-11-batch13/T-078/09c-attempt-2-materials-02/prepare.json:15
evidence/2026-10-11-batch13/T-078/09c-attempt-3-materials-01/prepare.json:15
evidence/2026-10-11-batch13/T-078/09c-c1-b1-executor-p1-01/source-files.json:98
evidence/2026-10-11-batch13/T-078/09c-c1-b1-ideation-p1-01/source-files.json:98
evidence/2026-10-11-batch13/T-078/09c-c2-b1-executor-p1-01/source-files.json:98
evidence/2026-10-11-batch13/T-078/09c-c2-b1-ideation-p1-01/source-files.json:98
evidence/2026-10-11-batch13/T-078/09c-c3-b1-executor-p1-01/source-files.json:98
evidence/2026-10-11-batch13/T-078/09c-c3-b1-ideation-p1-01/source-files.json:98
evidence/2026-10-11-batch13/T-078/09c-caffeinate-parity-rehearsal-01/flow/executor-p1/source-files.json:71
evidence/2026-10-11-batch13/T-078/09c-caffeinate-parity-rehearsal-01/flow/ideation-p1/source-files.json:71
evidence/2026-10-11-batch13/T-078/09c-caffeinate-parity-rehearsal-01/flow/packet/static-check.json:75
evidence/2026-10-11-batch13/T-078/09c-caffeinate-parity-rehearsal-02/flow/executor-p1/source-files.json:71
evidence/2026-10-11-batch13/T-078/09c-caffeinate-parity-rehearsal-02/flow/ideation-p1/source-files.json:71
evidence/2026-10-11-batch13/T-078/09c-caffeinate-parity-rehearsal-02/flow/packet/static-check.json:75
evidence/2026-10-11-batch13/T-078/09c-coordinator-rehearsal-01/real-chain-outside-01/flow/executor-p1/source-files.json:64
evidence/2026-10-11-batch13/T-078/09c-coordinator-rehearsal-01/real-chain-outside-01/flow/ideation-p1/source-files.json:64
evidence/2026-10-11-batch13/T-078/09c-coordinator-rehearsal-01/real-chain-outside-01/flow/packet/static-check.json:68
evidence/2026-10-11-batch13/T-078/09c-executable-materials-01/source-files.json:98
evidence/2026-10-11-batch13/T-078/09c-executable-materials-01/static-check.json:100
evidence/2026-10-11-batch13/T-078/09c-executable-materials-02/source-files.json:98
evidence/2026-10-11-batch13/T-078/09c-executable-materials-02/static-check.json:100
evidence/2026-10-11-batch13/T-078/09c-executable-materials-03/source-files.json:98
evidence/2026-10-11-batch13/T-078/09c-executable-materials-03/static-check.json:100
evidence/2026-10-11-batch13/T-078/09c-executable-materials-04/source-files.json:98
evidence/2026-10-11-batch13/T-078/09c-executable-materials-04/static-check.json:100
evidence/2026-10-11-batch13/T-078/09c-executable-materials-05/source-files.json:98
evidence/2026-10-11-batch13/T-078/09c-executable-materials-05/static-check.json:100
evidence/2026-10-11-batch13/T-078/09c-fix-01/real-chain-outside-01/flow/executor-p1/source-files.json:63
evidence/2026-10-11-batch13/T-078/09c-fix-01/real-chain-outside-01/flow/ideation-p1/source-files.json:63
evidence/2026-10-11-batch13/T-078/09c-fix-01/real-chain-outside-02/flow/executor-p1/source-files.json:63
evidence/2026-10-11-batch13/T-078/09c-fix-01/real-chain-outside-02/flow/ideation-p1/source-files.json:63
evidence/2026-10-11-batch13/T-078/09c-fix-01/real-chain-outside-03/flow/executor-p1/source-files.json:63
evidence/2026-10-11-batch13/T-078/09c-fix-01/real-chain-outside-03/flow/ideation-p1/source-files.json:63
evidence/2026-10-11-batch13/T-078/09c-materials-01/SOURCE.json:106
evidence/2026-10-11-batch13/T-078/09c-materials-01/prepare.json:15
evidence/2026-10-11-batch13/T-078/09c-topology-probe-run-01/ideation-p1/source-files.json:64
evidence/2026-10-11-batch13/T-078/09c-topology-probe-run-01/packet/static-check.json:68
evidence/2026-10-11-batch13/T-078/stage-a-readback-rebind-01/09B-prepare.json:15
evidence/2026-10-11-batch13/T-078/stage-a-readback-rebind-01/09C-prepare.json:15
evidence/2026-10-14-batch14/T-080/RUN-REPAIR-PROBE-01.md:10
evidence/2026-10-14-batch14/T-080/final-02/t077-lifecycle-conflicts/source-files.json:54
evidence/2026-10-14-batch14/T-080/final-03/t077-lifecycle-conflicts/source-files.json:54
evidence/2026-10-14-batch14/T-080/independent-review-01.diff:1463
evidence/2026-10-14-batch14/T-080/run-repair-probe-01/source-manifest.json:8
evidence/2026-10-14-batch14/T-081/6e-full-01/source-manifest.json:142
evidence/2026-10-14-batch14/T-081/6e-full-02/source-manifest.json:142
evidence/2026-10-14-batch14/T-081/6e-regress-rest-02/t077-lifecycle-conflicts/source-files.json:63
evidence/2026-10-14-batch14/T-081/6e-rerun-01/source-manifest.json:142
evidence/2026-10-14-batch14/T-081/6e-rerun-rest-01/t077-lifecycle-conflicts/source-files.json:63
evidence/2026-10-14-batch14/T-081/full-01/source-manifest.json:115
evidence/2026-10-14-batch14/T-081/full-02/source-manifest.json:117
evidence/2026-10-14-batch14/T-081/full-03/source-manifest.json:118
evidence/2026-10-14-batch14/T-081/full-03/t077-lifecycle-conflicts/source-files.json:54
evidence/2026-10-14-batch14/T-081/full-04/source-manifest.json:120
evidence/2026-10-14-batch14/T-081/full-04/t077-lifecycle-conflicts/source-files.json:54
evidence/2026-10-15-batch15/T-082/outside-command-11-01/source.json:182
evidence/2026-10-15-batch15/T-084/independent-review-01-probe/probe-output/diverged/daemon/host.stderr:16
evidence/2026-10-15-batch15/T-084/regression-03/worktree/source-files.json:54
evidence/2026-10-15-batch15/T-085/independent-review-01.md:24
evidence/2026-10-15-batch15/T-086/conflict-suite-01/source-files.json:54
evidence/2026-10-15-batch15/T-086/green-01/source-files.json:54
evidence/2026-10-15-batch15/T-086/lifecycle-managed/source-files.json:54
evidence/2026-10-15-batch15/T-086/red-01/source-files.json:54
evidence/2026-10-15-batch15/T-086/rework-conflict-suite/source-files.json:54
evidence/2026-10-15-batch15/T-086/rework-green-01/source-files.json:54
evidence/2026-10-15-batch15/T-086/rework-m1/source-files.json:54
evidence/2026-10-15-batch15/T-086/rework-m2/source-files.json:54
evidence/2026-10-15-batch15/T-086/rework-m3/source-files.json:54
evidence/2026-10-15-batch15/T-086/rework-m4/source-files.json:54
evidence/2026-10-15-batch15/T-086/rework-m5/source-files.json:54
evidence/2026-10-15-batch15/T-086/rework-red-01/source-files.json:54
evidence/2026-10-16-batch16/T-089/s3-baseline-local-01/cas/assertion-scope.json:673,838,931,1152,1290
evidence/2026-10-19-batch17/T-105/python39-check-setup-failure-01.json:15,16
evidence/2026-10-23-batch23/T-148/ISSUE-stale-oracles.md:13
evidence/2026-10-23-batch23/T-148/RESULTS.md:56
evidence/2026-10-23-batch23/T-148/review-agy-01.md:216
evidence/2026-10-23-batch23/T-148/stale-contract-search.txt:16
```

</details>

### R11 `test_t091_pane_ipc.mjs`

<details>
<summary>工作台 / 其他当前文件：1 个文件</summary>

```text
workbench/tests/run_t104_shell_ui.py:59
```

</details>

<details>
<summary>历史 evidence 可执行文件（含复跑脚本与冻结源码）：47 个文件</summary>

```text
evidence/2026-10-16-batch16/T-096/REVIEW-OUTSIDE-01.sh:30,62
evidence/2026-10-16-batch16/T-096/REVIEW-OUTSIDE-02.sh:30
evidence/2026-10-19-batch17/T-103/RUN-OUTSIDE-03-COMMIT.sh:50
evidence/2026-10-19-batch17/T-103/RUN-OUTSIDE-09-CONTRACTS.sh:35,73
evidence/2026-10-19-batch17/T-104/RUN-OUTSIDE-05-MERGE-CHECKS.sh:31
evidence/2026-10-19-batch17/T-104/RUN-OUTSIDE-06-UI.sh:35
evidence/2026-10-19-batch17/T-104/RUN-OUTSIDE-07-COMMIT-UI.sh:37
evidence/2026-10-19-batch17/T-105/REVIEW-OUTSIDE-01.sh:67
evidence/2026-10-19-batch17/T-105/RUN-OUTSIDE-02-COMMIT.sh:14
evidence/2026-10-19-batch17/T-106/RUN-OUTSIDE-02-COMMIT.sh:11
evidence/2026-10-19-batch17/T-107/REVIEW-OUTSIDE-01.sh:75
evidence/2026-10-19-batch17/T-107/REVIEW-OUTSIDE-02.sh:55
evidence/2026-10-19-batch17/T-107/REVIEW-OUTSIDE-03.sh:58
evidence/2026-10-19-batch17/T-107/REVIEW-OUTSIDE-04.sh:82
evidence/2026-10-20-batch18/T-108/RUN-OUTSIDE-COMMIT-01.sh:32
evidence/2026-10-20-batch18/T-108/RUN-OUTSIDE-MERGE-MAIN-01.sh:39,44,51
evidence/2026-10-20-batch18/T-108/RUN-OUTSIDE-RECHECK-03.sh:11
evidence/2026-10-20-batch18/T-108/RUN-OUTSIDE-RECHECK-04.sh:11
evidence/2026-10-20-batch18/T-108/RUN-OUTSIDE-RECHECK-05.sh:12
evidence/2026-10-20-batch18/T-108/resolve_main_merge_01.py:48
evidence/2026-10-20-batch18/T-109/REVIEW-OUTSIDE-01.sh:76
evidence/2026-10-20-batch18/T-109/REVIEW-OUTSIDE-02.sh:131
evidence/2026-10-20-batch18/T-109/RUN-OUTSIDE-COMMIT.sh:25
evidence/2026-10-20-batch18/T-110/REVIEW-OUTSIDE-01.sh:39,61
evidence/2026-10-20-batch18/T-110/REVIEW-OUTSIDE-02.sh:48,50,56
evidence/2026-10-20-batch18/T-110/RUN-OUTSIDE-COMMIT-02.sh:23
evidence/2026-10-20-batch18/T-110/RUN-OUTSIDE-COMMIT-05.sh:23
evidence/2026-10-20-batch18/T-110/RUN-OUTSIDE-COMMIT.sh:24
evidence/2026-10-20-batch18/T-111/REVIEW-OUTSIDE-01.sh:55
evidence/2026-10-20-batch18/T-111/REVIEW-OUTSIDE-02.sh:59
evidence/2026-10-20-batch18/T-111/RUN-OUTSIDE-COMMIT-01.sh:20
evidence/2026-10-20-batch18/T-112/REVIEW-OUTSIDE-01.sh:144
evidence/2026-10-20-batch18/T-112/REVIEW-OUTSIDE-02.sh:40,52
evidence/2026-10-20-batch18/T-112/RUN-MERGE-REGRESSIONS-13.py:48
evidence/2026-10-20-batch18/T-112/RUN-OUTSIDE-COMMIT-01.sh:18
evidence/2026-10-20-batch18/T-112/RUN-OUTSIDE-COMMIT-02.sh:18
evidence/2026-10-23-batch23/T-138/RUN-OUTSIDE-02.sh:47
evidence/2026-10-23-batch23/T-138/RUN-OUTSIDE-03.sh:46
evidence/2026-10-23-batch23/T-139-T-143/RUN-OUTSIDE-01.sh:43
evidence/2026-10-23-batch23/T-139-T-143/RUN-OUTSIDE-02.sh:45,46
evidence/2026-10-23-batch23/T-139-T-143/RUN-OUTSIDE-03.sh:65,66
evidence/2026-10-23-batch23/T-139-T-143/RUN-OUTSIDE-04.sh:66,67
evidence/2026-10-23-batch23/T-139-T-143/RUN-OUTSIDE-05.sh:62,63
evidence/2026-10-23-batch23/T-142/RUN-OUTSIDE-01.sh:27
evidence/2026-10-23-batch23/T-145/RUN-OUTSIDE-01.sh:61
evidence/2026-10-23-batch23/T-145/RUN-OUTSIDE-02.sh:61
evidence/2026-10-23-batch23/T-146-a3/RUN-OUTSIDE-01.sh:41,42
```

</details>

<details>
<summary>其余文本命中（治理记录、报告、摘要、日志等）：220 个文件</summary>

```text
.project-map/inbox/20261020T124908Z-executor-report-001.md:22
.project-map/inbox/20261023T101032Z-worker:b23-t139-issue-001.md:6,14,16
.project-map/inbox/20261023T181004Z-executor-report-001.md:31
.project-map/inbox/20261023T181318Z-ideation-answer-001.md:17
.project-map/tickets/T-103-workbench-project-task-picker.md:54
.project-map/tickets/T-104-workbench-plain-shell-pane.md:58
.project-map/tickets/T-105-workbench-free-terminals-split-panes.md:63
.project-map/tickets/T-108-native-question-signals-via-hooks.md:68
.project-map/tickets/T-109-dispatch-parent-launch-and-hierarchy-tree.md:47
.project-map/tickets/T-110-in-app-notification-for-waiting-user.md:54
.project-map/tickets/T-111-workbench-flow-view-page.md:58
.project-map/tickets/T-139-view-model-split-screen.md:47
.project-map/tickets/T-149-retire-stale-historical-tests.md:18
evidence/2026-10-16-batch16/T-091/RESULTS.md:93,113
evidence/2026-10-16-batch16/T-091/TRACER-RUN.md:59
evidence/2026-10-16-batch16/T-091/pane-ipc-takeover-01.json:6
evidence/2026-10-16-batch16/T-091/pane-ipc-unit-01.json:6
evidence/2026-10-16-batch16/T-091/pane-ipc-unit-02.json:6,22
evidence/2026-10-16-batch16/T-091/pane-ipc-unit-03.json:6
evidence/2026-10-16-batch16/T-091/pane-ipc-unit-04.json:6
evidence/2026-10-16-batch16/T-091/product-parse-takeover-01.json:12
evidence/2026-10-16-batch16/T-093/MANAGED-PROMPT-REVIEW-01.md:8
evidence/2026-10-16-batch16/T-093/REVIEW-REQUEST-T093-13.md:62
evidence/2026-10-16-batch16/T-093/REVIEW-REQUEST-T093-15.md:104
evidence/2026-10-16-batch16/T-093/REVIEW-REQUEST-T093-19.md:66
evidence/2026-10-16-batch16/T-093/t091-ipc-regression-01.json:6
evidence/2026-10-16-batch16/T-093/t091-ipc-regression-02.json:6
evidence/2026-10-16-batch16/T-093/t091-ipc-regression-17.json:6
evidence/2026-10-16-batch16/T-093/t091-ipc-regression-19.json:6
evidence/2026-10-16-batch16/T-093/t091-ipc-regression-20-02.json:6
evidence/2026-10-16-batch16/T-093/t091-ipc-regression-20-03.json:6
evidence/2026-10-16-batch16/T-093/t091-ipc-regression-20.json:6
evidence/2026-10-16-batch16/T-093/t091-ipc-regression-21.json:6
evidence/2026-10-16-batch16/T-093/t091-ipc-review-green-01.json:6
evidence/2026-10-16-batch16/T-096/RESULTS.md:53
evidence/2026-10-16-batch16/T-096/empty-layout-green-01.json:6
evidence/2026-10-16-batch16/T-096/empty-layout-green-02.json:6
evidence/2026-10-16-batch16/T-096/empty-layout-red-01.json:6,26
evidence/2026-10-16-batch16/T-096/empty-layout-red-02.json:6,26
evidence/2026-10-16-batch16/T-096/independent-review-01.md:39
evidence/2026-10-16-batch16/T-096/independent-review-02.md:53,94
evidence/2026-10-16-batch16/T-096/layout-ipc-contract-01.json:6
evidence/2026-10-16-batch16/T-096/layout-ipc-contract-02.json:6
evidence/2026-10-16-batch16/T-096/t091-ipc-regression-01.json:6,22
evidence/2026-10-16-batch16/T-096/t091-ipc-regression-02.json:6
evidence/2026-10-19-batch17/T-101/credential-triage-01.json:4302,4308,4588,4594,4666,4672,4796,4802,5004,5010
evidence/2026-10-19-batch17/T-101/credential-triage-01.md:367,389,395,405,421
evidence/2026-10-19-batch17/T-101/credential-triage-02.json:48,954,980
evidence/2026-10-19-batch17/T-101/credential-triage-02.md:99,101,110
evidence/2026-10-19-batch17/T-102/ipc-regression-02.json:6
evidence/2026-10-19-batch17/T-103/RESULTS.md:315
evidence/2026-10-19-batch17/T-103/commit-repair-17-before.json:18
evidence/2026-10-19-batch17/T-103/contracts-20261019T065323Z-summary.json:14,28,44,165,181
evidence/2026-10-19-batch17/T-103/followup-14-checks.json:77
evidence/2026-10-19-batch17/T-103/followup-15-checks.json:35
evidence/2026-10-19-batch17/T-103/independent-review-01.md:44,53,117
evidence/2026-10-19-batch17/T-103/ipc-legacy-16.json:6
evidence/2026-10-19-batch17/T-103/ipc-old-contract-red-16.json:6,26
evidence/2026-10-19-batch17/T-103/ipc-picker-16a.json:6
evidence/2026-10-19-batch17/T-103/ipc-picker-16b.json:6
evidence/2026-10-19-batch17/T-104/STAGE2-RESULTS.md:17
evidence/2026-10-19-batch17/T-104/commit-preflight-22.json:22
evidence/2026-10-19-batch17/T-104/independent-review-01.md:86
evidence/2026-10-19-batch17/T-104/independent-review-02.md:70
evidence/2026-10-19-batch17/T-104/ipc-picker-baseline-01.json:6
evidence/2026-10-19-batch17/T-104/ipc-shell-01.json:6
evidence/2026-10-19-batch17/T-104/ipc-shell-02.json:6
evidence/2026-10-19-batch17/T-104/merge-01-summary.json:12
evidence/2026-10-19-batch17/T-104/review-fix-02-summary.json:12,47
evidence/2026-10-19-batch17/T-104/ui-01-backend/suite.json:105
evidence/2026-10-19-batch17/T-104/ui-01-summary.json:12,47
evidence/2026-10-19-batch17/T-105/RESULTS.md:25
evidence/2026-10-19-batch17/T-105/independent-review-01.md:15
evidence/2026-10-19-batch17/T-105/ipc-contract-03.json:6
evidence/2026-10-19-batch17/T-105/ipc-contract-final-01.json:6
evidence/2026-10-19-batch17/T-105/python39-check-setup-failure-01.json:15,16
evidence/2026-10-19-batch17/T-105/reviewer-red-01.json:6,28
evidence/2026-10-19-batch17/T-106/RESULTS-form.md:37
evidence/2026-10-19-batch17/T-106/RESULTS-postcommit.md:45
evidence/2026-10-19-batch17/T-106/RESULTS-preflight.md:22
evidence/2026-10-19-batch17/T-106/independent-review-01.md:68
evidence/2026-10-19-batch17/T-106/independent-review-02.md:52
evidence/2026-10-19-batch17/T-106/pane-ipc-final-01.json:6
evidence/2026-10-19-batch17/T-106/pane-ipc-green-01.json:6
evidence/2026-10-19-batch17/T-106/postcommit-pane-regression-01.json:6
evidence/2026-10-19-batch17/T-106/preflight-pane-regression-01.json:6
evidence/2026-10-19-batch17/T-107/RESULTS.md:35
evidence/2026-10-19-batch17/T-107/ipc-initial-red-summary.json:6,28
evidence/2026-10-19-batch17/T-107/ipc-review-fixes-summary.json:6
evidence/2026-10-19-batch17/T-107/ipc-summary.json:6
evidence/2026-10-20-batch18/T-108/F1-RESULTS.md:20
evidence/2026-10-20-batch18/T-108/MERGE-MAIN-01.md:16
evidence/2026-10-20-batch18/T-108/REVIEW02-FIX-RESULTS.md:39
evidence/2026-10-20-batch18/T-108/f1-local.summary.json:64
evidence/2026-10-20-batch18/T-108/independent-review-01.md:84
evidence/2026-10-20-batch18/T-108/independent-review-02.md:88
evidence/2026-10-20-batch18/T-108/merge-main-01.ipc-preview.summary.json:6
evidence/2026-10-20-batch18/T-108/review02-fix-local.summary.json:191
evidence/2026-10-20-batch18/T-109/local-checks.json:155
evidence/2026-10-20-batch18/T-110/cleanup-ipc-01.json:6
evidence/2026-10-20-batch18/T-110/cleanup-regressions-01.json:8
evidence/2026-10-20-batch18/T-110/contract-green-01.json:6
evidence/2026-10-20-batch18/T-110/contract-green-02.json:6
evidence/2026-10-20-batch18/T-110/contract-red-02.json:6,29
evidence/2026-10-20-batch18/T-110/contract-red.json:6,33
evidence/2026-10-20-batch18/T-110/independent-review-01.md:13,70
evidence/2026-10-20-batch18/T-110/independent-review-02.md:107
evidence/2026-10-20-batch18/T-110/receipt-final-handoff.json:33
evidence/2026-10-20-batch18/T-110/receipt-ipc-01.json:6
evidence/2026-10-20-batch18/T-110/reconnect-ipc-green.json:6
evidence/2026-10-20-batch18/T-110/review01-disconnect-green.json:6
evidence/2026-10-20-batch18/T-110/review01-disconnect-red.json:6,29
evidence/2026-10-20-batch18/T-111/RESULTS.md:57
evidence/2026-10-20-batch18/T-111/ipc-01.json:6
evidence/2026-10-20-batch18/T-111/ipc-final.json:6
evidence/2026-10-20-batch18/T-112/RESULTS.md:31,32,158
evidence/2026-10-20-batch18/T-112/independent-review-01.md:97,134
evidence/2026-10-20-batch18/T-112/independent-review-02.md:19,20,21,86
evidence/2026-10-20-batch18/T-112/ipc-02.json:6,33
evidence/2026-10-20-batch18/T-112/ipc-03.json:6
evidence/2026-10-20-batch18/T-112/ipc-04.json:6
evidence/2026-10-20-batch18/T-112/ipc-final-05.json:6
evidence/2026-10-20-batch18/T-112/ipc-initial-01.json:6,33
evidence/2026-10-20-batch18/T-112/ipc-rev2-06.json:6
evidence/2026-10-20-batch18/T-112/ipc-rev7-01.json:6
evidence/2026-10-20-batch18/T-112/merge-delivery-checks-01.json:33
evidence/2026-10-20-batch18/T-112/merge-ipc-01.json:6
evidence/2026-10-20-batch18/T-112/merge-local-regressions-01.json:13
evidence/2026-10-20-batch18/T-112/merge-main-conflicts-01.json:9,168,180
evidence/2026-10-20-batch18/T-112/merge-main-resolutions-13/manifest.json:8
evidence/2026-10-20-batch18/T-112/merge-script-rehearsal-01.json:11,147,158,169
evidence/2026-10-20-batch18/T-112/outside-merge-ipc-01.json:6
evidence/2026-10-20-batch18/T-112/outside-merge-ipc-02.json:6
evidence/2026-10-20-batch18/T-112/outside-merge-ipc-03.json:6
evidence/2026-10-20-batch18/T-112/outside-merge-main-01.json:11,147,158,169
evidence/2026-10-20-batch18/T-112/outside-merge-regressions-01-before-merge-commit.json:25
evidence/2026-10-20-batch18/T-112/outside-merge-regressions-01.json:32
evidence/2026-10-20-batch18/T-112/outside-merge-regressions-02.json:44
evidence/2026-10-20-batch18/T-112/outside-merge-regressions-03.json:44
evidence/2026-10-23-batch21/release-0.1.2/credential-scan-01.json:239
evidence/2026-10-23-batch23/T-138/card.md:12,27
evidence/2026-10-23-batch23/T-138/outside-02-20261023-132813-22749/run-summary.json:77,89
evidence/2026-10-23-batch23/T-138/outside-02-20261023-132813-22749/t091-baseline.json:6,31
evidence/2026-10-23-batch23/T-138/outside-02-20261023-132813-22749/t091-baseline.log:1
evidence/2026-10-23-batch23/T-138/outside-02-20261023-132813-22749/t091-candidate.json:6,29
evidence/2026-10-23-batch23/T-138/outside-02-20261023-132813-22749/t091-candidate.log:1
evidence/2026-10-23-batch23/T-138/outside-03-20261023-134525-51971/run-summary.json:66,78
evidence/2026-10-23-batch23/T-138/outside-03-20261023-134525-51971/t091-baseline.json:6,31
evidence/2026-10-23-batch23/T-138/outside-03-20261023-134525-51971/t091-baseline.log:1
evidence/2026-10-23-batch23/T-138/outside-03-20261023-134525-51971/t091-candidate.json:6,29
evidence/2026-10-23-batch23/T-138/outside-03-20261023-134525-51971/t091-candidate.log:1
evidence/2026-10-23-batch23/T-138/t091-baseline-02.json:6,21
evidence/2026-10-23-batch23/T-138/t091-baseline-02.log:1
evidence/2026-10-23-batch23/T-138/t091-baseline-03.json:6,31
evidence/2026-10-23-batch23/T-138/t091-baseline-03.log:1
evidence/2026-10-23-batch23/T-138/t091-candidate-02.json:6,19
evidence/2026-10-23-batch23/T-138/t091-candidate-02.log:1
evidence/2026-10-23-batch23/T-138/t091-candidate-03.json:6,29
evidence/2026-10-23-batch23/T-138/t091-candidate-03.log:1
evidence/2026-10-23-batch23/T-139-T-143/card.md:14,30
evidence/2026-10-23-batch23/T-139-T-143/outside-02-fXauAYx2/t091-baseline.json:6,31
evidence/2026-10-23-batch23/T-139-T-143/outside-02-fXauAYx2/t091-baseline.log:1
evidence/2026-10-23-batch23/T-139-T-143/outside-02-fXauAYx2/t091-candidate.json:6,29
evidence/2026-10-23-batch23/T-139-T-143/outside-02-fXauAYx2/t091-candidate.log:1
evidence/2026-10-23-batch23/T-139-T-143/outside-04-kDtDFKqW/t091-baseline.json:6,31
evidence/2026-10-23-batch23/T-139-T-143/outside-04-kDtDFKqW/t091-baseline.log:1
evidence/2026-10-23-batch23/T-139-T-143/outside-04-kDtDFKqW/t091-candidate.json:6,29
evidence/2026-10-23-batch23/T-139-T-143/outside-04-kDtDFKqW/t091-candidate.log:1
evidence/2026-10-23-batch23/T-139-T-143/outside-05-uAcv4xAj/t091-baseline.json:6,31
evidence/2026-10-23-batch23/T-139-T-143/outside-05-uAcv4xAj/t091-baseline.log:1
evidence/2026-10-23-batch23/T-139-T-143/outside-05-uAcv4xAj/t091-candidate.json:6,29
evidence/2026-10-23-batch23/T-139-T-143/outside-05-uAcv4xAj/t091-candidate.log:1
evidence/2026-10-23-batch23/T-139-T-143/outside-cZpQfO1X/t091.json:6,29
evidence/2026-10-23-batch23/T-139-T-143/outside-cZpQfO1X/t091.log:1
evidence/2026-10-23-batch23/T-139-T-143/pane-ipc-01.json:6,29
evidence/2026-10-23-batch23/T-139-T-143/pane-ipc-baseline-01.json:6,31
evidence/2026-10-23-batch23/T-139-T-143/review-agy-01-prompt.txt:9
evidence/2026-10-23-batch23/T-139-T-143/review-agy-01.md:129,153
evidence/2026-10-23-batch23/T-139-T-143/t091-issue.md:1,3
evidence/2026-10-23-batch23/T-141/card.md:31
evidence/2026-10-23-batch23/T-142/RESULTS.md:33
evidence/2026-10-23-batch23/T-142/baseline-t091-01.json:6,31
evidence/2026-10-23-batch23/T-142/card.md:26
evidence/2026-10-23-batch23/T-142/outside-20261023T153047Z-v7ZOxk/t091.command.txt:1
evidence/2026-10-23-batch23/T-142/outside-20261023T153047Z-v7ZOxk/t091.json:6,29
evidence/2026-10-23-batch23/T-142/outside-20261023T153047Z-v7ZOxk/t091.log:1
evidence/2026-10-23-batch23/T-142/regression-t091-01.json:6,19
evidence/2026-10-23-batch23/T-142/regression-t091-02.json:6,29
evidence/2026-10-23-batch23/T-145/card.md:12,28
evidence/2026-10-23-batch23/T-145/review-agy-01.md:128
evidence/2026-10-23-batch23/T-145/run-JzoEtp/MANIFEST.json:53,66
evidence/2026-10-23-batch23/T-145/run-JzoEtp/t091-baseline.json:6,31
evidence/2026-10-23-batch23/T-145/run-JzoEtp/t091-baseline.stdout.txt:1
evidence/2026-10-23-batch23/T-145/run-JzoEtp/t091-candidate.json:6,29
evidence/2026-10-23-batch23/T-145/run-JzoEtp/t091-candidate.stdout.txt:1
evidence/2026-10-23-batch23/T-145/run-e7JqMf/MANIFEST.json:52,64
evidence/2026-10-23-batch23/T-145/run-e7JqMf/t091-baseline.json:6,21
evidence/2026-10-23-batch23/T-145/run-e7JqMf/t091-baseline.stdout.txt:1
evidence/2026-10-23-batch23/T-145/run-e7JqMf/t091-candidate.json:6,19
evidence/2026-10-23-batch23/T-145/run-e7JqMf/t091-candidate.stdout.txt:1
evidence/2026-10-23-batch23/T-145/run-htufoE/MANIFEST.json:53,66
evidence/2026-10-23-batch23/T-145/run-htufoE/t091-baseline.json:6,31
evidence/2026-10-23-batch23/T-145/run-htufoE/t091-baseline.stdout.txt:1
evidence/2026-10-23-batch23/T-145/run-htufoE/t091-candidate.json:6,29
evidence/2026-10-23-batch23/T-145/run-htufoE/t091-candidate.stdout.txt:1
evidence/2026-10-23-batch23/T-145/run02-0InMi4/MANIFEST.json:54,67
evidence/2026-10-23-batch23/T-145/run02-0InMi4/t091-baseline.json:6,31
evidence/2026-10-23-batch23/T-145/run02-0InMi4/t091-baseline.stdout.txt:1
evidence/2026-10-23-batch23/T-145/run02-0InMi4/t091-candidate.json:6,29
evidence/2026-10-23-batch23/T-145/run02-0InMi4/t091-candidate.stdout.txt:1
evidence/2026-10-23-batch23/T-146-a3/RESULTS.md:46
evidence/2026-10-23-batch23/T-146-a3/card.md:30
evidence/2026-10-23-batch23/T-146-a3/outside-20261023T132912Z-1738/t091-baseline.json:6,31
evidence/2026-10-23-batch23/T-146-a3/outside-20261023T132912Z-1738/t091-baseline.log:1
evidence/2026-10-23-batch23/T-146-a3/outside-20261023T132912Z-1738/t091-candidate.json:6,29
evidence/2026-10-23-batch23/T-146-a3/outside-20261023T132912Z-1738/t091-candidate.log:1
evidence/2026-10-23-batch23/T-146-a3/t091-baseline-01.json:6,21
evidence/2026-10-23-batch23/T-146-a3/t091-baseline-02.json:6,31
evidence/2026-10-23-batch23/T-146-a3/t091-candidate-01.json:6,19
evidence/2026-10-23-batch23/T-146-a3/t091-candidate-02.json:6,29
```

</details>

### R12 `test_t078_claude_signals.ts`

<details>
<summary>工作台 / 其他当前文件：1 个文件</summary>

```text
workbench/tests/regenerate_t078_p1.py:98
```

</details>

<details>
<summary>历史 evidence 可执行文件（含复跑脚本与冻结源码）：5 个文件</summary>

```text
evidence/2026-10-11-batch13/T-078/rebased-local-09a3-02/run.py:18
evidence/2026-10-20-batch18/T-108/RUN-OUTSIDE-COMMIT-05.sh:39
evidence/2026-10-20-batch18/T-108/RUN-OUTSIDE-RECHECK-03.sh:15
evidence/2026-10-20-batch18/T-108/RUN-OUTSIDE-RECHECK-04.sh:15
evidence/2026-10-20-batch18/T-108/RUN-OUTSIDE-RECHECK-05.sh:16
```

</details>

<details>
<summary>其余文本命中（治理记录、报告、摘要、日志等）：110 个文件</summary>

```text
.project-map/inbox/20261023T102949Z-worker:b23-t146-issue-001.md:6,16
.project-map/inbox/20261023T181004Z-executor-report-001.md:31
.project-map/inbox/20261023T181318Z-ideation-answer-001.md:17
.project-map/tickets/T-149-retire-stale-historical-tests.md:18
evidence/2026-10-11-batch13/T-078/09b-a16-b1-executor-p1-01/source-files.json:231
evidence/2026-10-11-batch13/T-078/09b-a16-b1-ideation-p1-01/source-files.json:231
evidence/2026-10-11-batch13/T-078/09b-a16-materials-01/SOURCE.json:239
evidence/2026-10-11-batch13/T-078/09b-a16-materials-01/prepare.json:15
evidence/2026-10-11-batch13/T-078/09b-executable-materials-16-02/source-files.json:231
evidence/2026-10-11-batch13/T-078/09b-executable-materials-16-02/static-check.json:233
evidence/2026-10-11-batch13/T-078/09b-executable-materials-16/source-files.json:231
evidence/2026-10-11-batch13/T-078/09b-executable-materials-16/static-check.json:233
evidence/2026-10-11-batch13/T-078/09c-attempt-2-materials-01/SOURCE.json:277
evidence/2026-10-11-batch13/T-078/09c-attempt-2-materials-01/prepare.json:15
evidence/2026-10-11-batch13/T-078/09c-attempt-2-materials-02/SOURCE.json:283
evidence/2026-10-11-batch13/T-078/09c-attempt-2-materials-02/prepare.json:15
evidence/2026-10-11-batch13/T-078/09c-attempt-3-materials-01/prepare.json:15
evidence/2026-10-11-batch13/T-078/09c-c1-b1-executor-p1-01/source-files.json:231
evidence/2026-10-11-batch13/T-078/09c-c1-b1-ideation-p1-01/source-files.json:231
evidence/2026-10-11-batch13/T-078/09c-c2-b1-executor-p1-01/source-files.json:240
evidence/2026-10-11-batch13/T-078/09c-c2-b1-ideation-p1-01/source-files.json:240
evidence/2026-10-11-batch13/T-078/09c-c3-b1-executor-p1-01/source-files.json:248
evidence/2026-10-11-batch13/T-078/09c-c3-b1-ideation-p1-01/source-files.json:248
evidence/2026-10-11-batch13/T-078/09c-caffeinate-parity-rehearsal-01/flow/executor-p1/source-files.json:245
evidence/2026-10-11-batch13/T-078/09c-caffeinate-parity-rehearsal-01/flow/ideation-p1/source-files.json:245
evidence/2026-10-11-batch13/T-078/09c-caffeinate-parity-rehearsal-01/flow/packet/static-check.json:249
evidence/2026-10-11-batch13/T-078/09c-caffeinate-parity-rehearsal-02/flow/executor-p1/source-files.json:246
evidence/2026-10-11-batch13/T-078/09c-caffeinate-parity-rehearsal-02/flow/ideation-p1/source-files.json:246
evidence/2026-10-11-batch13/T-078/09c-caffeinate-parity-rehearsal-02/flow/packet/static-check.json:250
evidence/2026-10-11-batch13/T-078/09c-coordinator-rehearsal-01/real-chain-outside-01/flow/executor-p1/source-files.json:231
evidence/2026-10-11-batch13/T-078/09c-coordinator-rehearsal-01/real-chain-outside-01/flow/ideation-p1/source-files.json:231
evidence/2026-10-11-batch13/T-078/09c-coordinator-rehearsal-01/real-chain-outside-01/flow/packet/static-check.json:235
evidence/2026-10-11-batch13/T-078/09c-executable-materials-01/source-files.json:231
evidence/2026-10-11-batch13/T-078/09c-executable-materials-01/static-check.json:233
evidence/2026-10-11-batch13/T-078/09c-executable-materials-02/source-files.json:231
evidence/2026-10-11-batch13/T-078/09c-executable-materials-02/static-check.json:233
evidence/2026-10-11-batch13/T-078/09c-executable-materials-03/source-files.json:238
evidence/2026-10-11-batch13/T-078/09c-executable-materials-03/static-check.json:240
evidence/2026-10-11-batch13/T-078/09c-executable-materials-04/source-files.json:240
evidence/2026-10-11-batch13/T-078/09c-executable-materials-04/static-check.json:242
evidence/2026-10-11-batch13/T-078/09c-executable-materials-05/source-files.json:248
evidence/2026-10-11-batch13/T-078/09c-executable-materials-05/static-check.json:250
evidence/2026-10-11-batch13/T-078/09c-fix-01/real-chain-outside-01/flow/executor-p1/source-files.json:223
evidence/2026-10-11-batch13/T-078/09c-fix-01/real-chain-outside-01/flow/ideation-p1/source-files.json:223
evidence/2026-10-11-batch13/T-078/09c-fix-01/real-chain-outside-02/flow/executor-p1/source-files.json:224
evidence/2026-10-11-batch13/T-078/09c-fix-01/real-chain-outside-02/flow/ideation-p1/source-files.json:224
evidence/2026-10-11-batch13/T-078/09c-fix-01/real-chain-outside-03/flow/executor-p1/source-files.json:225
evidence/2026-10-11-batch13/T-078/09c-fix-01/real-chain-outside-03/flow/ideation-p1/source-files.json:225
evidence/2026-10-11-batch13/T-078/09c-materials-01/SOURCE.json:239
evidence/2026-10-11-batch13/T-078/09c-materials-01/prepare.json:15
evidence/2026-10-11-batch13/T-078/09c-topology-probe-run-01/ideation-p1/source-files.json:234
evidence/2026-10-11-batch13/T-078/09c-topology-probe-run-01/packet/static-check.json:238
evidence/2026-10-11-batch13/T-078/P1-APPROVAL-02.md:52
evidence/2026-10-11-batch13/T-078/P1-APPROVAL.md:55
evidence/2026-10-11-batch13/T-078/binding-fix-09a2.diff:211,212
evidence/2026-10-11-batch13/T-078/binding-fix-final-09a2.diff:220,221
evidence/2026-10-11-batch13/T-078/claude-signals-green-09/command.json:4
evidence/2026-10-11-batch13/T-078/claude-signals-green-09/results.json:20
evidence/2026-10-11-batch13/T-078/claude-signals-green-09/stdout.txt:1
evidence/2026-10-11-batch13/T-078/implementation-09.diff:168,412,414,415
evidence/2026-10-11-batch13/T-078/implementation-final-09.diff:185,186,449,451,452
evidence/2026-10-11-batch13/T-078/notice-fix-08d.diff:89,90
evidence/2026-10-11-batch13/T-078/p1-bad-session-01/results.json:21
evidence/2026-10-11-batch13/T-078/p1-bad-session-01/stdout.txt:1
evidence/2026-10-11-batch13/T-078/p1-materials-01/source-files.json:1
evidence/2026-10-11-batch13/T-078/p1-materials-02/source-files.json:1
evidence/2026-10-11-batch13/T-078/p1-materials-03/source-files.json:35
evidence/2026-10-11-batch13/T-078/p1-materials-04/source-files.json:36
evidence/2026-10-11-batch13/T-078/p1-materials-05/source-files.json:36
evidence/2026-10-11-batch13/T-078/p1-materials-06-before-archive/source-files.json:36
evidence/2026-10-11-batch13/T-078/p1-materials-06/source-files.json:38
evidence/2026-10-11-batch13/T-078/p1-materials-07/source-files.json:37
evidence/2026-10-11-batch13/T-078/p1-materials-08/source-files.json:39
evidence/2026-10-11-batch13/T-078/p1-materials-08b/source-files.json:39
evidence/2026-10-11-batch13/T-078/p1-materials-08c/source-files.json:39
evidence/2026-10-11-batch13/T-078/p1-materials-08d/source-files.json:40
evidence/2026-10-11-batch13/T-078/p1-materials-08e/source-files.json:40
evidence/2026-10-11-batch13/T-078/p1-materials-09/source-files.json:52
evidence/2026-10-11-batch13/T-078/p1-materials-09a2/source-files.json:56
evidence/2026-10-11-batch13/T-078/p1-materials-09a3-block/source-files.json:57
evidence/2026-10-11-batch13/T-078/p1-materials-09a3/source-files.json:57
evidence/2026-10-11-batch13/T-078/p1-materials-09a3r-block/source-files.json:58
evidence/2026-10-11-batch13/T-078/p1-materials-09a3r/source-files.json:58
evidence/2026-10-11-batch13/T-078/p1-materials-09a3r2-block/source-files.json:60
evidence/2026-10-11-batch13/T-078/p1-materials-09a3r2/source-files.json:60
evidence/2026-10-11-batch13/T-078/p1-materials-slice1-green-3/source-files.json:60
evidence/2026-10-11-batch13/T-078/p1-materials-slice1-green/source-files.json:60
evidence/2026-10-11-batch13/T-078/p1-materials-slice1-red/source-files.json:60
evidence/2026-10-11-batch13/T-078/p1-resume-materials-05b/source-files.json:37
evidence/2026-10-11-batch13/T-078/p1-state-green-01/results.json:20
evidence/2026-10-11-batch13/T-078/p1-state-green-02/results.json:20
evidence/2026-10-11-batch13/T-078/p1-state-green-03/results.json:20
evidence/2026-10-11-batch13/T-078/p1-state-red-01/results.json:23
evidence/2026-10-11-batch13/T-078/rebase-continue-01/execution/worktree-status.txt:12
evidence/2026-10-11-batch13/T-078/rebase-continue-02/execution/stdout.txt:10
evidence/2026-10-11-batch13/T-078/rebase-continue-02/execution/worktree-status.txt:60,366,374
evidence/2026-10-11-batch13/T-078/rebase-continue-02/logs/worktree-status.txt:12
evidence/2026-10-11-batch13/T-078/rebase-continue-03/logs/stdout.txt:10
evidence/2026-10-11-batch13/T-078/rebase-continue-03/logs/worktree-status.txt:60,366,374
evidence/2026-10-11-batch13/T-078/rebased-local-09a3-02/command-output/00008.stdout.bin:1
evidence/2026-10-11-batch13/T-078/rebased-local-09a3-02/commands.jsonl:15,16
evidence/2026-10-11-batch13/T-078/rebased-local-09a3-02/signals/results.json:20
evidence/2026-10-11-batch13/T-078/stage-a-readback-rebind-01/09B-prepare.json:15
evidence/2026-10-11-batch13/T-078/stage-a-readback-rebind-01/09C-prepare.json:15
evidence/2026-10-11-batch13/T-078/theme-confirmation-fix-08c.diff:59,60
evidence/2026-10-11-batch13/T-078/trust-selection-fix-08e.diff:84,85
evidence/2026-10-19-batch17/T-105/python39-check-setup-failure-01.json:15,16
evidence/2026-10-20-batch18/T-108/review02-fix-local.summary.json:342
evidence/2026-10-23-batch23/T-146/existing-regression-issue.md:3
evidence/2026-10-23-batch23/T-146/t078-session-end-01.json:21
```

</details>

### R13 `test_t108_questions.mjs`

<details>
<summary>工作台 / 其他当前文件：1 个文件</summary>

```text
workbench/README.md:1088
```

</details>

<details>
<summary>历史 evidence 可执行文件（含复跑脚本与冻结源码）：21 个文件</summary>

```text
evidence/2026-10-20-batch18/T-108/REVIEW-OUTSIDE-02.sh:78
evidence/2026-10-20-batch18/T-108/REVIEW-OUTSIDE-03.sh:78
evidence/2026-10-20-batch18/T-108/REVIEW-OUTSIDE-04.sh:78
evidence/2026-10-20-batch18/T-108/REVIEW-OUTSIDE-05.sh:79
evidence/2026-10-20-batch18/T-108/REVIEW-OUTSIDE-06.sh:79
evidence/2026-10-20-batch18/T-108/RUN-OUTSIDE-COMMIT-01.sh:36
evidence/2026-10-20-batch18/T-108/RUN-OUTSIDE-COMMIT-03.sh:28
evidence/2026-10-20-batch18/T-108/RUN-OUTSIDE-COMMIT-04.sh:28
evidence/2026-10-20-batch18/T-108/RUN-OUTSIDE-COMMIT-05.sh:38
evidence/2026-10-20-batch18/T-108/RUN-OUTSIDE-COMMIT-07.sh:45
evidence/2026-10-20-batch18/T-108/RUN-OUTSIDE-MERGE-MAIN-01.sh:50
evidence/2026-10-20-batch18/T-108/RUN-OUTSIDE-RECHECK-03.sh:10
evidence/2026-10-20-batch18/T-108/RUN-OUTSIDE-RECHECK-04.sh:10
evidence/2026-10-20-batch18/T-108/RUN-OUTSIDE-RECHECK-05.sh:11
evidence/2026-10-20-batch18/T-108/replay_review03_red.py:37,39
evidence/2026-10-20-batch18/T-108/replay_review04_red.py:37,39
evidence/2026-10-20-batch18/T-108/replay_review05_red.py:37,40
evidence/2026-10-20-batch18/T-110/REVIEW-OUTSIDE-01.sh:96,101
evidence/2026-10-20-batch18/T-110/REVIEW-OUTSIDE-02.sh:83,87
evidence/2026-10-20-batch18/T-112/REVIEW-OUTSIDE-01.sh:145
evidence/2026-10-20-batch18/T-112/RUN-MERGE-REGRESSIONS-13.py:49
```

</details>

<details>
<summary>其余文本命中（治理记录、报告、摘要、日志等）：36 个文件</summary>

```text
.project-map/inbox/20261020T124908Z-executor-report-001.md:22
.project-map/inbox/20261020T130602Z-worker:t112-a1-issue-001.md:14
.project-map/inbox/20261023T102949Z-worker:b23-t146-issue-001.md:6,17
.project-map/inbox/20261023T181004Z-executor-report-001.md:31
.project-map/inbox/20261023T181318Z-ideation-answer-001.md:17
.project-map/tickets/T-108-native-question-signals-via-hooks.md:68
.project-map/tickets/T-110-in-app-notification-for-waiting-user.md:54
.project-map/tickets/T-112-launch-model-effort-configurable.md:61
.project-map/tickets/T-149-retire-stale-historical-tests.md:18
evidence/2026-10-20-batch18/T-108/F1-RESULTS.md:16,18
evidence/2026-10-20-batch18/T-108/MERGE-MAIN-01.md:22
evidence/2026-10-20-batch18/T-108/RESULTS.md:11,75,106
evidence/2026-10-20-batch18/T-108/REVIEW02-FIX-RESULTS.md:20,37,50
evidence/2026-10-20-batch18/T-108/f1-local.summary.json:15
evidence/2026-10-20-batch18/T-108/independent-review-01.md:49,72,73,74,95
evidence/2026-10-20-batch18/T-108/independent-review-02.md:63,64,74,79,80,117
evidence/2026-10-20-batch18/T-108/independent-review-03.md:94,105,106,139
evidence/2026-10-20-batch18/T-108/independent-review-04.md:108,112,113,151
evidence/2026-10-20-batch18/T-108/independent-review-05.md:39,46,146
evidence/2026-10-20-batch18/T-108/independent-review-06.md:104
evidence/2026-10-20-batch18/T-108/review02-fix-local.summary.json:24,32,40,48,56,64,72,80,84
evidence/2026-10-20-batch18/T-110/cleanup-regressions-01.json:19
evidence/2026-10-20-batch18/T-110/independent-review-01.md:13
evidence/2026-10-20-batch18/T-110/independent-review-02.md:25
evidence/2026-10-20-batch18/T-112/RESULTS.md:32,159
evidence/2026-10-20-batch18/T-112/independent-review-01.md:98
evidence/2026-10-20-batch18/T-112/issue-t108-fixture.md:1
evidence/2026-10-20-batch18/T-112/merge-local-regressions-01.json:25
evidence/2026-10-20-batch18/T-112/outside-merge-regressions-01.json:42
evidence/2026-10-20-batch18/T-112/outside-merge-regressions-02.json:54
evidence/2026-10-20-batch18/T-112/outside-merge-regressions-03.json:54
evidence/2026-10-20-batch18/T-112/t108-final-02.json:2479
evidence/2026-10-23-batch23/T-146/existing-regression-issue.md:4
evidence/2026-10-23-batch23/T-146/t108-baseline-01.json:978,985,992,999,1006,1013,1020,1027,1034,1041,1048,1055,1062,1069,1076,1083,1090,1097,1104,1111,1118,1125,1132,1139,1146,1153,1160,1167,1174,1181,1188,1195,1202,1209,1216,1223,1230,1237,1244,1251,1258,1265,1272,1279,1286,1293,1300,1307,1314,1321,1328,1335,1342,1349,1356,1363,1370,1377,1384,1391,1398,1405,1412,1419,1426,1433,1440,1447,1454,1461,1468,1475,1482,1489,1496,1503,1510,1517,1524,1531,1538,1545,1552,1559,1566,1573,1580,1587,1594,1601,1608,1615,1622,1629,1636,1643,1650,1657,1664,1671,1678,1685,1692,1699,1706,1713,1720,1727,1734,1741,1748,1755,1762,1769,1776,1783,1790,1797,1804,1811,1818,1825,1832,1839,1846,1853,1860,1867,1874,1881,1888,1895,1902,1909,1916,1923,1930,1937,1944,1951,1958,1965,1972,1979,1986,1993,2000,2007,2014,2021,2028,2035,2042,2049,2056,2063,2075,2082,2089,2096,2108,2115,2122,2129,2141,2148,2155,2162,2174,2181,2188,2585
evidence/2026-10-23-batch23/T-146/t108-baseline-comparison-01.json:8
evidence/2026-10-23-batch23/T-146/t108-session-end-01.json:978,985,992,999,1006,1013,1020,1027,1034,1041,1048,1055,1062,1069,1076,1083,1090,1097,1104,1111,1118,1125,1132,1139,1146,1153,1160,1167,1174,1181,1188,1195,1202,1209,1216,1223,1230,1237,1244,1251,1258,1265,1272,1279,1286,1293,1300,1307,1314,1321,1328,1335,1342,1349,1356,1363,1370,1377,1384,1391,1398,1405,1412,1419,1426,1433,1440,1447,1454,1461,1468,1475,1482,1489,1496,1503,1510,1517,1524,1531,1538,1545,1552,1559,1566,1573,1580,1587,1594,1601,1608,1615,1622,1629,1636,1643,1650,1657,1664,1671,1678,1685,1692,1699,1706,1713,1720,1727,1734,1741,1748,1755,1762,1769,1776,1783,1790,1797,1804,1811,1818,1825,1832,1839,1846,1853,1860,1867,1874,1881,1888,1895,1902,1909,1916,1923,1930,1937,1944,1951,1958,1965,1972,1979,1986,1993,2000,2007,2014,2021,2028,2035,2042,2049,2056,2063,2075,2082,2089,2096,2108,2115,2122,2129,2141,2148,2155,2162,2174,2181,2188,2585
```

</details>
