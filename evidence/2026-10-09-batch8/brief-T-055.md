# Worker 任务书：T-055 问题上报最薄一刀（build）
你是 a2a 的 worker（Codex）。主控是执行主控（Claude Code，Herdr pane wF:pM）。只做 T-055（`.project-map/tickets/T-055-issue-report-tracer-bullet.md`）。
- fork `~/Documents/Code/synara`，分支 `a2a`（当前 `6efac84`）。改动在 `packages/a2a-gates`、`packages/contracts`、`apps/server/src/a2a`、`apps/web/src/a2a`；其他上游文件先停下问主控。
- 参考：T-037（human_intervention 记录器、observer）、T-044（attach、membership、任务窗口）、T-047（CLI run）的 RESULTS；T-039/T-042 intervention 的真实 Codex 隔离做法。
- 真实 Codex 验收：按 AGENTS.md 隔离 CODEX_HOME 规则（只复制 auth.json、只信任夹具根、两条 git 规则、无 hook、结束删除整个 home、前后核对用户配置元数据与 herdr status），只用最少 turn。provider 只在你的隔离实例中启用。
- 界面截图：可用 fork 现有 Playwright，或 Codex CLI 的 Computer Use（只操作你自己启动的隔离窗口；权限请求由主控代批；遇到系统设置、登录、密码、付款界面停下）。
## 共同规则
- 先读 a2a 的 `AGENTS.md`（含"构思主控与执行主控"一节）、`CONTEXT.md`、你的 ticket（验收以它为准，依据 `ready_rev: 1`）、`.project-map/specs/controller-split-user-input-2026-10-09.md` 中 ticket 指向的章节，以及 fork 的 `AGENTS.md`、`CLAUDE.md`、`a2a/WORKBENCH.md`。
- 发现 spec 与已建成的行为不符：停下，向主控说明（主控写 needs-decision），不绕开。
- 正式工作台在运行：不得停止、重启、读写 `~/Library/Application Support/a2a-workbench`；不得在 `~/Documents/Code/synara` 运行 `build:desktop` 或改写 `apps/*/dist` 的命令。严禁移动、替换或链接构建输出与依赖目录。Bun/Node 只经 fork 的 `a2a/scripts/bun`。不碰用户 Herdr、`~/.codex`、`~/.claude`。不 push。只停你启动的进程，只删你创建的文件。
- 先红后绿；预期来自 ticket/spec，不来自实现输出；失败原样保留；额度紧，只跑相关测试。不用正则或关键词规则判断内容含义。
- 证据 `evidence/2026-10-09-batch8/T-05x/`，中文 `RESULTS.md`；a2a 只提交你的文件与 ticket Resolution（保持 open，写"待主控关闭"）；fresh-context 只读独立审查一次。最后终端回复一行：`T-05x DONE <PASS|INCOMPLETE|BLOCKED> <a2a commit> <fork commit 或 none>`。需要决定的事停下说明，完成前不要结束回合。
- 发给你的文本暂未经 `scripts/dispatch`（T-054 尚未完成），由主控经 Herdr 直接投递。
