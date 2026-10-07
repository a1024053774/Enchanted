# Worker 任务书：T-035 门禁 tracer bullet（build）

你是 a2a 的 worker（Codex）。主控是 Claude Code（Herdr pane wF:pM）。只做 T-035。
先读：a2a 的 AGENTS.md、intent.md、CONTEXT.md、.project-map/specs/synara-m1-2026-10-07.md（全文，尤其"层级模型""门禁""界面""隔离运行""验证接缝"）、
.project-map/tickets/T-035-gate-tracer-bullet.md（验收以它为准）、三份冻结规格 managed-delivery / recovery / supervised-run（契约来源）、
`coop.py`（参考实现，只读）、evidence/2026-10-07-synara-batch1/T-034/RESULTS.md（构建入口与隔离数据目录的做法），
以及 fork `~/Documents/Code/synara` 的 AGENTS.md、CLAUDE.md、CONTRIBUTING.md。

## 两个仓库
- fork：`~/Documents/Code/synara`，在分支 `a2a` 上开发，所有 Bun/Node 命令只经 `a2a/scripts/bun`。不 push。
- a2a：只写 T-035 ticket 与证据目录 `evidence/2026-10-07-synara-batch1/T-035/`；不改 MAP.md、AGENTS.md、README.md、CONTEXT.md（需要时写进结论交主控）。

## 第一步：核实接入点（写成证据，再动手）
读 Synara 源码，回答并附文件与行号：
1. thread 之间是否已有持久的归属关系（例如创建者与被创建 thread、split 分组）；没有的话，任务与 thread 的归属放在我们的 package 里。
2. 服务端内部如何创建 thread（agentGateway 背后的服务），能否指定 worktree 环境、baseRef、模型与参数。
3. Codex app-server 会话的 turn 开始、结束与空闲信号在哪里；如何停止并归档一个 thread。
4. 如何新增一个 MCP 工具给 agent 调用（参照现有 gateway 工具的注册方式）。
5. 隔离：如何让 Synara 使用隔离的数据目录，以及如何让它启动的 Codex 使用隔离的 CODEX_HOME。

## 实现（只走正常路径）
- 新建 workspace package `packages/a2a-gates`：门禁核心，持有自己的 SQLite 文件（位于隔离数据目录下）与追加式事件；实现 create（冻结输入与 oracle）、dispatch（经 Synara 内部服务创建 worker thread，worktree 环境，起点为集成头）、submit（核对 attempt/session/fence/spec_rev 与完整提交号、worktree 干净、为集成头后代）、verify（新 detached worktree 中跑冻结的 oracle）、integrate（`git update-ref` CAS 并读回）、reclaim（停止并归档 worker thread）。语义以冻结规格为准，本切片可不实现恢复与竞争，但不能写出违背规格的行为。
- 新增 MCP 工具 `a2a_submit` 供 worker 调用；thread 结束或空闲本身不推进状态。
- 服务端只做注册与挂载；web 在独立目录中加一个最小的门禁状态显示（任务窗口里显示 claimed → submitted → verified → accepted）。对上游文件的每处改动列清单。
- 先拿红态：在实现前用真实入口证明缺失行为失败，再实现转绿。

## 真实闭环
- 夹具：用 a2a 仓库 `fixtures/pagination` 的同一夹具内容（新建隔离 Git 仓库），oracle 用 `acceptance/pagination_oracle.py`，不得修改其预期答案。
- worker 会话用 Codex（gpt-6.1-sol、xhigh、fast），隔离 CODEX_HOME 严格按 AGENTS.md：只复制 auth.json、只信任已核对的夹具根目录、只复现用户规则中的 `git add`、`git commit` 两条 allow 规则；不装 hook；副本不入证据或 Git；结束后删除整个 home。遇到任何其他权限或信任对话，停下报告主控。
- 反例：不调用 `a2a_submit`、或提交身份不符时，任务不会进入验收或集成。
- 截图或录屏：任务窗口显示门禁状态变化。

## 安全
本机 Codex 默认 danger-full-access，没有沙箱兜底：不改用户级配置，不碰用户正在用的 Herdr 与可能已安装的 Synara 数据，只关闭你启动的进程，只删除你创建的文件。

## 完成
逐条对照 T-035 的 5 个复选框，附命令、输出摘要与证据路径；只在有证据时勾选。冻结候选后做一次 fresh-context 只读独立审查（记录审查模型与冻结提交），审查期间不改已跟踪文件。
ticket 若全部满足，Resolution 写清结论；地图索引由主控补，你保持 status 为 open 并在结论中说明"待主控关闭"。
a2a 仓库本地 commit 只含你的文件；fork 在 `a2a` 分支提交，不 push。最后终端回复一行：`T-035 DONE <PASS|INCOMPLETE|BLOCKED> <a2a commit> <fork commit>`。
遇到权限请求、需要用户级改动或需要用户决定的事，停下说明，不要猜。
