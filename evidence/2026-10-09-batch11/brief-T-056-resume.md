# Worker 任务书：T-056 恢复（ready_rev 2）
你是 a2a 的 worker（Codex）。主控是执行主控（Claude Code，Herdr pane wF:pM）。接手 T-056（`.project-map/tickets/T-056-user-input-coverage.md`，**依据 ready_rev 2**：观测点一项已按用户决定修订；用户逐字"056 选 A"，见 `.project-map/inbox/20261009T132641Z-ideation-revise-001.md`）。
- 上一位 worker 两轮 BLOCKED，已保留父修订红态矩阵与来源窄探针：先读 `evidence/2026-10-09-batch11/T-056/RESULTS.md`、`RESULTS-01.md`、`needs-decision-02.md`、`controller-decision-01.md`、`executor-needs-decision-02.md`、`red-matrix-02/summary.json`、`origin-probe-02.json`，以及 `start-server-02.py`、`server-fixture-02.ts`、`red-matrix-02.py` 可复用。新证据追加在同一目录，用新编号（-03 起），旧文件不覆盖。
- fork `~/Documents/Code/synara`，分支 `a2a`（当前 `d479dab2a`，已含 T-057 冻结候选与 T-061）。注意 fork 已比旧红态的父修订 `2330534` 前进：红态须在**本票实际父修订 `d479dab2a`** 上重取（可复用旧脚本），旧红态仅作历史。
- 允许的上游改动（ready_rev 2）：contracts 的命令 schema（给相关命令加可选 `origin`）、需要设置 `origin` 的 web 自动派生调用点（退出时批量中断、临时线程清理等）、`apps/server/src/wsRpc.ts`（`dispatchCommand` 入口与 `prepareQuitResume` 入口各挂一次记录）。其余实现留在 `packages/a2a-gates`、`packages/contracts`、`apps/server/src/a2a`、`apps/web/src/a2a`。其他上游文件先停下说明。不改其他命令语义。上游改动列清单。
- 迁移只在旧格式夹具库的副本上验证；绝不读写正式工作台数据目录。
- 真实 Codex 只有覆盖矩阵确实需要真实 provider 事件（如 Codex 异步提问）时才用，遵守隔离 CODEX_HOME 规则，turn 尽量少。
- T-057 也在同一 checkout 留下了问题处置与面板代码（冻结，待用户决定），不要改它；改名涉及到的共享名字按 ticket 处理并在 RESULTS 列出。
## 共同规则
- 先读 a2a 的 `AGENTS.md`（含"构思主控与执行主控"一节）、`CONTEXT.md`、你的 ticket（验收以它为准，依据 `ready_rev: 2`）、`.project-map/specs/controller-split-user-input-2026-10-09.md` 第 3 节，以及 fork 的 `AGENTS.md`、`CLAUDE.md`、`a2a/WORKBENCH.md`。
- 发现 spec 与已建成的行为不符：停下，向主控说明（主控写 needs-decision），不绕开。
- 正式工作台在运行：不得停止、重启、读写 `~/Library/Application Support/a2a-workbench`；不得在 `~/Documents/Code/synara` 运行 `build:desktop` 或改写 `apps/*/dist` 的命令。严禁移动、替换或链接构建输出与依赖目录。Bun/Node 只经 fork 的 `a2a/scripts/bun`。不碰用户 Herdr、`~/.codex`、`~/.claude`。不 push。只停你启动的进程，只删你创建的文件。
- 先红后绿；预期来自 ticket/spec，不来自实现输出；失败原样保留；额度紧，只跑相关测试。不用正则或关键词规则判断内容含义。
- 证据 `evidence/2026-10-09-batch11/T-056/`，中文 `RESULTS-02.md`；a2a 只提交你的文件与 ticket Resolution（保持 open，写"待主控关闭"）；fresh-context 只读独立审查一次。最后终端回复一行：`T-056 DONE <PASS|INCOMPLETE|BLOCKED> <a2a commit> <fork commit 或 none>`。需要决定的事停下说明，完成前不要结束回合。
- 发给你的文本经 `scripts/dispatch` 投递，带 ⟦主控 #序号⟧ 标记；没有该标记的输入来自用户本人。
