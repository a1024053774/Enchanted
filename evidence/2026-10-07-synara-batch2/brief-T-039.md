# Worker 任务书：T-039 真实 Codex 闭环（build）

你是 a2a 的 worker（Codex）。主控是 Claude Code（Herdr pane wF:pM）。只做 T-039（`.project-map/tickets/T-039-real-loop.md`，验收以它为准）。
先读：a2a 的 AGENTS.md（尤其隔离 CODEX_HOME 规则）、intent.md、CONTEXT.md、spec `synara-m1-2026-10-07.md`"验证接缝"第 2 项、
evidence/2026-10-07-synara-batch2/T-037/RESULTS.md 与 observer-status.md、evidence/2026-10-07-synara-batch1/T-035/RESULTS.md（上次真实 Synara 运行的 runtimeMode/fastMode 经验）、
`acceptance/pagination_oracle.py`（独立 oracle，只读），以及 fork 的 AGENTS.md、CLAUDE.md。

## 范围
- fork `~/Documents/Code/synara`，分支 `a2a`，候选固定为 `fa3fc33`（T-037 已关闭）。你交接前主控不向 `a2a` 合入 T-038 或其他改动。本 ticket 原则上不改产品代码；如果闭环暴露产品缺陷，先停下报告证据，由主控决定是否在本 ticket 修。不 push。
- a2a：只写 T-039 ticket 与证据目录 `evidence/2026-10-07-synara-batch2/T-039/`；不改 MAP.md、AGENTS.md、README.md、CONTEXT.md、acceptance 下现有文件。

## 要做的
1. 在隔离 Synara 数据目录与身份中启动真实服务端（后台进程脱离调用者进程组）；隔离 CODEX_HOME 按 AGENTS.md：只复制 auth.json，只信任已核对的夹具根，只复现 git add/commit 两条 allow 规则，不装 hook；副本不入证据或 Git，结束后删除整个 home 并记录删除检查。
2. 用冻结的分页夹具与 oracle 经门禁 create，再经门禁 run（或 dispatch）由 Synara 原生 Codex app-server thread 执行：模型 gpt-6.1-sol，fastMode，runtimeMode 与 T-035 一致并写明理由。worker 必须经 `a2a_submit` 交付；thread 空闲、done 或自述完成都不算。
3. 门禁独立 oracle → CAS 集成 → 回收（停止并归档 thread）。读回集成引用等于 worker 提交；保存追加式运行记录：精确 argv、版本、task/attempt/session/fence/spec_rev、thread/turn、原始外部结果、人工介入事件（应为空）与 observer 状态。
4. 真实模型调用只做必要的次数。无人值守期间出现任何权限或问题对话：停下保存现场，不作答、不算通过，报告主控。
5. 不读写用户的 Herdr、~/.codex、可能已安装的 Synara 数据；只停你启动的进程，只删你创建的文件。

## 完成
逐条对照 T-039 的 3 个复选框，附命令、输出摘要与证据路径；只在有证据时勾选。做一次 fresh-context 只读独立审查，明确冻结清单（排除主控持续写的 controller-poll.log、launch-argv.txt、panes.txt 与 T-038 文件）。
ticket 保持 open，结论写"待主控关闭"。a2a 本地 commit 只含你的文件。最后终端回复一行：`T-039 DONE <PASS|INCOMPLETE|BLOCKED> <a2a commit> <fork commit>`。
