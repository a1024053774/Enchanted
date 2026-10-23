# T-152 断言迁移清单（编辑前）

目标：迁移审查副本边界测试；不改产品、共享测试、历史索引或项目地图。验收：当前代码全绿，保留检查能拒绝已知坏实现。未知：沙箱外运行结果尚未取得。

依据：T-152 与用户答复 `20261023T185657Z-ideation-answer-001`；T-082 的完成条件、副本、绑定与结束核对契约；T-141 的网络放开裁定和 Resolution 中仅 reviewer 副本仍 untrusted 的裁定。原生编排规格第 3 节要求新审查会话且结论绑定候选。产品代码仅用来定位，不作为预期来源：`panes.ts:711–738`、`gates/core.ts:2383–2416,2603–2611,3929–3931`。

| 原检查 | 判定与迁移 |
| --- | --- |
| T082-REVIEW-START | 有效，保留：机械检查后建立审查。 |
| T082-REVIEW-ARGV | 部分过时：`network_access=false` 改成 `true`；`features.network_proxy=false` 改为不强制关闭代理。保留 workspace-write、cwd/worktree 绑定副本、排除共享 tmp。按 T-141 保留 `-a never` 并核对 reviewer 副本 untrusted。 |
| reviewer 放行后 busy / fixture-turn-1 | 有效夹具前提，保留；旧 PTY 只展示 Open restricted 而不发 native ready，增加专用 host 发出打开后的原生 ready 信号。它不替代门禁结果。 |
| T082-REQUEST-COMPLETION | 有效，保留完成条件及 oracle_paths 请求。 |
| T082-REQUEST-MUTATIONS | 有效，保留 2～5 与报告节名。 |
| T082-COPY-CREATED | 有效，保留非 Git 副本及创建事件。 |
| T082-REVIEW-VERDICT | 有效，保留 verified。 |
| T082-COPY-REMOVED | 有效，保留物理删除与事件。 |
| T082-LAUNCH-REFUSED / PAUSED / ISSUE | 有效，保留真实门禁拒收、暂停与上报；仅在非法启动变异下运行，不能作为普通绿态案例。网络开启已不属于非法变异；改测网络关闭。保留 readonly、错误 cwd、tmp 可写。代理继承由 ARGV 检查观察，不宣称门禁另有代理拒收规则。 |
| T082-END-CHECK-INVALID | 有效，保留副本外脏变更使结论作废、保留现场。 |
| REVIEW-REFS-INVALIDATE | 有效，保留共享 refs 变化导致暂停、unknown、保留副本、主分支不动、上报和禁止回收。 |
| REVIEW-REQUIREMENTS-WORKSPACE | 有效，保留错误副本绑定须拒绝且不落 review_result。 |
| held socket 回执完整、completedReview、尚无 reclaimed | 有效夹具前提，原样保留，避免靠时间延迟构造窗口。 |
| REVIEW-END-BEFORE-INTEGRATE | 有效，保留脏/干净两个对照：结束核对前集成拒绝且 main 不动；补核对明确拒绝码。 |
| T082-DIRTY-END-INVALIDATE | 有效，保留脏结束暂停、unknown、不集成、不回收且上报。 |
| T082-INTEGRATE-AFTER-END | 有效，保留干净结束后同一候选可集成。 |
| response template 存在且可解析 | 有效夹具前提，保留。 |
| T082-TEMPLATE-FIELDS / TEMPLATE-REPORT | 有效，保留真实历史报告输入的字段集合与 object 类型。稀疏 checkout 不含该小输入，另存原 Git blob 为专用夹具，内容不改。 |
| T082-REPORT-PERSISTED / REPORT-COPY-REMOVED | 有效，保留完整 report 与 requirements 落库、verdict 绑定和副本清理。 |

**Tracer bullet**：沿用真实 CLI → 后台 → 门禁 → Git/SQLite 的端到端路径，PTY/process/native 输入受控，不声称证明真实沙箱。**Deep modules**：复用现有 Tracer，不新建门禁 API；专用 host 仅补现行原生启动信号。**Ubiquitous language**：沿用“审查副本”“结束核对”“共享 refs”。

保留检查的变异：移除结束核对前置条件、把 workspace 等值改成非空、跳过共享 refs 比较、假报副本已删除。变异只落在临时产品副本，不改 checkout 产品文件。
