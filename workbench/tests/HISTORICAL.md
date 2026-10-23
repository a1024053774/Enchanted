# 历史测试与迁移处置索引

2026-10-23，T-154 最终处置索引。用户选择“C 先迁守护安全边界的 4 个”：原有 3 个历史辅助文件保留，其余 10 个中 6 个整份标历史、4 个迁移到现行契约；不删除文件。授权见 [用户裁定](../../.project-map/inbox/20261023T185657Z-ideation-answer-001.md)，调查依据、现行部分覆盖和全仓引用见 [T-149 DISPOSITION.md](../../evidence/2026-10-23-batch23/T-149/DISPOSITION.md)。后者是裁定前的日期记录，其中“待决”不是当前处置状态。

## 只针对历史版本的辅助文件

这 3 个文件的统一文件头为“历史测试：只针对 <revision>，当前 main 不跑”。标记不改变代码、导出或 import，也不替依赖它们的测试给出通过结论。当前 main 的回归入口 `RUN-MERGE-REGRESSION-06.sh` 不调用这些历史 host；离线导入诊断 handler 的请求回放仍可执行。

| 文件 | 对应 revision | 用途与调用者 |
| --- | --- | --- |
| [diagnose_t112_reviewer.py](diagnose_t112_reviewer.py) | `5f19062f52154914123e3796fdff87caaa22fc1f` | T-112 固定 Codex 0.162.1 的 reviewer 原生写入边界诊断。由 `run_t112_native.py` 调用；`test_t112_request_replay.py` 只离线回放其 handler。旧关网络断言不符合 T-141。 |
| [t112_reviewer_record.mjs](t112_reviewer_record.mjs) | `5f19062f52154914123e3796fdff87caaa22fc1f` | 上述诊断使用的 daemon/reviewer host。`test_t112_reviewer_startup.mjs` 是针对旧放行流程的 VM 检查，不能当成现行原生运行证明。 |
| [controlled_quality_pty.ts](controlled_quality_pty.ts) | `5f7f9816eb9a996377c5b255695244d99c0259e7` | 旧质量串共用的受控 PTY/process 输入层；被 quality、daemon、conflict、multiturn host 导入。只发受限目录屏幕、不发 native idle 的旧输入不能代表 T-141 后的启动协议。 |

复跑须同时取得该 revision 的 **host、测试和产品源码**，并核对当时的 CLI、输入和运行约束。不能将当前文件、历史 host 和当前产品混用，不能把旧 PASS 当成当前 main 的通过证明。T-112 的 revision 来自当时完整原生验收的 `source_head`；受控 PTY 的 revision 对应 T-082 冻结候选，不表示整个 T-076 runner 都曾全绿。具体证据边界见 DISPOSITION。

## 整份标历史的 6 个测试

**当前无人守护这些检查。** 下表逐项列出缺口；已有部分覆盖见 DISPOSITION，不据此宣称整份契约已有现行全绿替代。6 个文件只加文件头注释，不删、不迁、不改断言。历史标记是运行边界说明，没有新增自动跳过机制；离线导入仍保留，导入成功不等于历史套件在当前 main 通过。

“对应 revision”是本轮查到的最后一个可与通过证据绑定的完整版本，不是当前 main 的通过版本；只有未提交快照或部分步骤通过时单列限制，不编造 revision。以下证据路径均相对仓库根目录；稀疏 checkout 未展开时用 `git show HEAD:<路径>` 读取。

| 文件 | 对应 revision 与通过证据 | 当前无人守护的检查 |
| --- | --- | --- |
| [test_t112_execution.mjs](test_t112_execution.mjs) | `e161476d6bb17e6f372d4a3d98ed03feccf36755`；[regress-t112-execution-04.json](../../evidence/2026-10-22-batch20/T-127/regress-t112-execution-04.json) 为 PASS，版本绑定见同目录 [RESULTS.md](../../evidence/2026-10-22-batch20/T-127/RESULTS.md)“回归”。 | 五角色默认与设置持久化、覆盖参数优先级、角色隔离、权限字段拒绝、未知 effort 透传、原生启动失败不被 shell 掩盖。旧 reviewer 关网络断言不符合 T-141。 |
| [test_quality_tracer_e2e.py](test_quality_tracer_e2e.py) | `bb6c0ba352ff7cab1f470d2db055caac36387bab`；[baseline-quality-tracer-loaded/run.json](../../evidence/2026-10-15-batch15/T-086/baseline-quality-tracer-loaded/run.json) 为 PASS、13 案通过；版本来源见 [RESULTS.md](../../evidence/2026-10-15-batch15/T-086/RESULTS.md)“质量套件”。同报告的 `quality-tracer/run.json` 也为 PASS，但来自带未提交修改的工作树，不能绑定为该 HEAD 的干净通过。T-082 后续只跑 4 案，不替整份背书。 | 评分必填、字段校验与仅写一次、修复后重跑质量串、第三次拒绝暂停、严格审查 JSON、拒绝复用原生审查会话、交付回合事实绑定。旧独立 reviewer home、关网络条件不符合现行契约。 |
| [run_pane_lifecycle.py](run_pane_lifecycle.py) | **无通过证据**（未找到整份通过且绑定 revision 的记录）；[outside-live-04/lifecycle/verdict.json](../../evidence/2026-10-10-batch12/T-075/card-4/outside-live-04/lifecycle/verdict.json) 原样为 INCOMPLETE；[RESULTS.md](../../evidence/2026-10-10-batch12/T-075/card-4/RESULTS.md) 记载 `turn_context` 缺失、部分生命周期证据及获批离线修复，不能合称整份原生运行通过。 | 应用关闭期间 PTY 继续增长、重开逐字节回放、后台重启后原 attempt 中断事实、只读输入不能注入。切换视图的输出保留不替代整窗关闭/重启组合。 |
| [test_t122_claude_worker_e2e.py](test_t122_claude_worker_e2e.py) | `01e0effd7c1ec9bdb982e593fc52c22fd0aceb77`；[t122-green.json](../../evidence/2026-10-22-batch20/T-136/candidate-1/e2e/t122-green.json) 为 PASS；同目录 [commands.sh](../../evidence/2026-10-22-batch20/T-136/candidate-1/e2e/commands.sh) 绑定该候选的干净 detached worktree。此记录是正常流程，不扩称所有 reviewer/protocol 反例在同版本跑过。 | Claude Git 元数据、拼接 git/-c、项目钩子攻击矩阵；审查 CLI/模型/Fast/钩子绑定；协议失败和门禁拒绝留据。旧 `--strict-mcp-config` 期望不符合 T-141。 |
| [run_t112_native.py](run_t112_native.py) | `e161476d6bb17e6f372d4a3d98ed03feccf36755`；[regress-t112-native-03.json](../../evidence/2026-10-22-batch20/T-127/regress-t112-native-03.json) 为 PASS，`source_head` 为此版本。 | 真实设置 DOM→SQLite→下次派发→原生首轮请求、覆盖优先级、未知 effort 原样透传。旧 `codex_restricted_opened` 等待不符合 T-141；保留 `closed_fixture_launches` 供离线导入。 |
| [test_t108_questions.mjs](test_t108_questions.mjs) | `5f19062f52154914123e3796fdff87caaa22fc1f`；[outside-merge-questions-03.json](../../evidence/2026-10-20-batch18/T-112/outside-merge-questions-03.json) 为 PASS；同目录 [outside-merge-regressions-03.json](../../evidence/2026-10-20-batch18/T-112/outside-merge-regressions-03.json) 记录干净源码、`source_head` 与执行命令。 | Claude 主控原生问答关联、畸形/过期/外来 hook、permission 伪造、答复记录与写入竞争、重复答复拒收。Codex worker 的旧等待状态期望已被 T-124 取代。 |

离线依赖保持原样：`test_t112_closed_fixture.py` 导入 `closed_fixture_launches` 并运行旧 Node producer，`test_t112_counterfactuals.py` 调用旧 Node producer；它们的旧断言未在本票迁移。`Tracer` 仍被质量、坏 worker、受保护验收、副本生命周期等测试导入，`run_t076_quality_green.py` 仍导入 `CASES`。文件可导入不使这些调用者自动符合现行契约。

## 已迁移到现行契约（T-150～T-153）

| 文件 | 迁移票与状态 | 保留的检查范围 |
| --- | --- | --- |
| [test_t091_pane_ipc.mjs](test_t091_pane_ipc.mjs) | [T-150](../../.project-map/tickets/T-150-migrate-t091-pane-ipc.md)，已合入。 | 跨窗 key、iframe、未知窗口拒收；错误凭据签发拒绝；关窗竞争的迟到凭据撤销；空布局持久化。 |
| [test_t078_claude_signals.ts](test_t078_claude_signals.ts) | [T-151](../../.project-map/tickets/T-151-migrate-t078-claude-signals.md)，已合入。 | 已登记 active submission 的 UserPromptSubmit/Stop 关联、重复 Stop 不重复产生 `pane_idle`、异会话拒收。 |
| [test_t082_review_boundary_e2e.py](test_t082_review_boundary_e2e.py) | [T-152](../../.project-map/tickets/T-152-migrate-t082-review-boundary.md)，已合入。 | 审查副本生命周期、共享 refs 改动作废、`review_requirements.workspace` 绑定、结束核对前拒绝集成及 held socket 竞争。 |
| [run_worker_delivery.py](run_worker_delivery.py) | [T-153](../../.project-map/tickets/T-153-migrate-worker-delivery.md)，已合入。 | 原生 Stop 批次与重复请求只处理一次、门禁回执只注入一次且收据回合无工具、实际 turn_context→delivery→尾注。 |

迁移的红态、绿态和独立验收以各票绑定候选的证据为准；本索引不代替验收。T-152、T-153 的合入状态已由执行主控在集成时核对（2026-10-23）。
