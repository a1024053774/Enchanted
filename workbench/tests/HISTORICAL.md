# 历史测试与待决测试索引

2026-10-23，T-149 处置记录。执行主控确认的方案为：删 0 个、标历史 3 个、待决 10 个。逐文件理由、现行覆盖和全仓引用见 [DISPOSITION.md](../../evidence/2026-10-23-batch23/T-149/DISPOSITION.md)，确认的 PLAN 为 `8eda61b96bb01cda338d2bd2cb6927ce4bae5386`。

## 只针对历史版本的辅助文件

这 3 个文件的统一文件头为“历史测试：只针对 <revision>，当前 main 不跑”。标记不改变代码、导出或 import，也不把依赖它们的待决测试宣布为已停用或已通过。当前 main 的回归入口 `RUN-MERGE-REGRESSION-06.sh` 不调用这些历史 host；离线导入诊断 handler 的请求回放仍可执行。

| 文件 | 对应 revision | 用途与调用者 |
| --- | --- | --- |
| [diagnose_t112_reviewer.py](diagnose_t112_reviewer.py) | `5f19062f52154914123e3796fdff87caaa22fc1f` | T-112 固定 Codex 0.162.1 的 reviewer 原生写入边界诊断。由 `run_t112_native.py` 调用；`test_t112_request_replay.py` 只离线回放其 handler。旧关网络断言不符合 T-141。 |
| [t112_reviewer_record.mjs](t112_reviewer_record.mjs) | `5f19062f52154914123e3796fdff87caaa22fc1f` | 上述诊断使用的 daemon/reviewer host。`test_t112_reviewer_startup.mjs` 是针对旧放行流程的 VM 检查，不能当成现行原生运行证明。 |
| [controlled_quality_pty.ts](controlled_quality_pty.ts) | `5f7f9816eb9a996377c5b255695244d99c0259e7` | 旧质量串共用的受控 PTY/process 输入层；被 quality、daemon、conflict、multiturn host 导入。只发受限目录屏幕、不发 native idle 的旧输入不能代表 T-141 后的启动协议。 |

复跑须同时取得该 revision 的 **host、测试和产品源码**，并核对当时的 CLI、输入和运行约束。不能将当前文件、历史 host 和当前产品混用，不能把旧 PASS 当成当前 main 的通过证明。T-112 的 revision 来自当时完整原生验收的 `source_head`；受控 PTY 的 revision 对应 T-082 冻结候选，不表示整个 T-076 runner 都曾全绿。具体证据边界见 DISPOSITION。

## 待用户决定，未停用

以下 10 个文件保持原样：没有删除、跳过、改断言或标为历史。它们含过时假设，也仍含未找到现行全绿替代的有效检查；是否迁移或接受覆盖缺口，待用户决定。

| 文件 | 仍有效的检查（完整缺口见 DISPOSITION） |
| --- | --- |
| [test_t112_execution.mjs](test_t112_execution.mjs) | 五角色设置持久化、覆盖参数优先级、角色隔离、权限字段拒绝、未知 effort 透传、原生启动失败不被 shell 掩盖。 |
| [test_quality_tracer_e2e.py](test_quality_tracer_e2e.py) | 评分必填与仅写一次、修复后重跑质量串、第三次拒绝暂停、严格审查 JSON、拒绝复用原生审查会话、交付回合事实绑定。 |
| [test_t082_review_boundary_e2e.py](test_t082_review_boundary_e2e.py) | 审查副本生命周期、共享 refs 改动作废、`review_requirements.workspace` 绑定、结束核对完成前拒绝集成及 held socket 竞争。 |
| [run_pane_lifecycle.py](run_pane_lifecycle.py) | 应用关闭期间 PTY 继续增长、重开逐字节回放、后台重启后原 attempt 中断事实、只读输入不能注入。 |
| [run_worker_delivery.py](run_worker_delivery.py) | 原生 Stop 批次与重复请求只处理一次、门禁回执只注入一次且收据回合无工具、实际 turn_context→delivery→尾注。 |
| [test_t122_claude_worker_e2e.py](test_t122_claude_worker_e2e.py) | Claude Git 元数据、拼接 git/-c、项目钩子攻击矩阵；审查 CLI/模型/Fast/钩子绑定；协议失败和门禁拒绝留据。 |
| [run_t112_native.py](run_t112_native.py) | 真实设置 DOM→SQLite→下次派发→原生首轮请求、覆盖优先级、未知 effort 原样透传；另提供离线测试导入的 `closed_fixture_launches`。 |
| [test_t091_pane_ipc.mjs](test_t091_pane_ipc.mjs) | 跨窗 key、iframe、未知窗口拒收；拒绝错误凭据签发；窗口关闭与身份请求竞争中的迟到凭据撤销；空布局持久化。 |
| [test_t078_claude_signals.ts](test_t078_claude_signals.ts) | 已登记 active submission 的 UserPromptSubmit/Stop 关联、重复 Stop 不重复产生 `pane_idle`、异会话拒收。 |
| [test_t108_questions.mjs](test_t108_questions.mjs) | Claude 主控原生问答关联、畸形/过期/外来 hook、permission 伪造、答复记录与写入竞争、重复答复拒收。Codex worker 的旧等待状态期望不代表现行契约。 |

本次只记录处置与添加注释，不修复历史测试。测试失败须区分过时契约、夹具缺口和产品缺陷，不能静默删除仍有效的检查来换取全绿。
