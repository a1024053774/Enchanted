# Worker 任务书：T-036 门禁完整契约与交付、恢复验收（build）

你是 a2a 的 worker（Codex）。主控是 Claude Code（Herdr pane wF:pM）。只做 T-036。
先读：a2a 的 AGENTS.md、intent.md、CONTEXT.md、.project-map/specs/synara-m1-2026-10-07.md（"门禁""验证接缝"）、
.project-map/tickets/T-036-gate-full-contract.md（验收以它为准）、三份冻结规格 managed-delivery / recovery / supervised-run（契约原文）、
`coop.py`（参考实现，只读）、`acceptance/test_coop_e2e.py`、`acceptance/test_recovery_e2e.py`（独立 oracle，只读）、
evidence/2026-10-07-synara-batch1/T-035/RESULTS.md 与 controller-decision-01.md，以及 fork 的 AGENTS.md、CLAUDE.md。

## 两个仓库
- fork `~/Documents/Code/synara`，分支 `a2a`（当前 `7cb0ac0`），Bun/Node 只经 `a2a/scripts/bun`；只在 `packages/a2a-gates`、`apps/server/src/a2a/` 及既有接入点内改动，对上游文件的新增改动列清单。不 push。
- a2a：只写 T-036 ticket、证据目录 `evidence/2026-10-07-synara-batch1/T-036/`，以及一个新的入口转接脚本（见下）；不改 MAP.md、AGENTS.md、README.md、CONTEXT.md，不改 acceptance 下的现有文件。

## 要做的
1. 补全门禁核心，使与运行时无关的行为符合三份冻结规格：create 冻结输入与 oracle、claim 分配 attempt/session/fence/spec_rev、submit 全部校验与重交规则、verify 在新 detached worktree 中运行冻结 oracle（超时）、integrate 先记 intent 再 CAS 并读回、revoke / revise、操作锁与 `operation_busy`、中断验收与 CAS 前后恢复、`needs_reconciliation`、status / events。状态变更只在门禁核心中发生。
2. 门禁 CLI：对上述命令保持 `coop.py` 的命令行、JSON 输出（`ok`、`error` 码）与退出码（0/1/2）契约。
3. 入口转接：在 a2a 仓库新增一个很薄的 Python 转接脚本（例如 `acceptance/entry/a2a_gates.py`），用 `os.execv` 把参数原样交给门禁 CLI（保持 PID，使中断注入有效），供现有脚本经 `COOP_SCRIPT` 选用。转接脚本不做任何业务判断。
4. 先拿红态：在实现补全前，用转接入口跑两套脚本并保存失败结果；再实现转绿。
5. 若现有脚本对入口有与运行时相关的假设（例如检查进程命令行里的脚本路径）而无法原样通过：不改 acceptance 现有文件；在证据中逐条记录差异、原因与影响，给出最小的处理建议交主控决定。不得为了通过而改写任何预期答案。
6. 反例：保存 mutant（去掉 fence 校验、忽略 Git 回读）在同一套验收下失败的结果。

## 安全
本机 Codex 默认 danger-full-access：不改用户级配置，不碰用户正在用的 Herdr 与可能已安装的 Synara 数据；真实中断只注入你在测试中创建的进程；只停你启动的进程，只删你创建的文件。本 ticket 不需要真实模型调用；若需要，先停下问主控。

## 完成
逐条对照 T-036 的 4 个复选框，附命令、输出摘要与证据路径；只在有证据时勾选。冻结候选后做一次 fresh-context 只读独立审查（记录审查模型与冻结提交），审查期间不改已跟踪文件。
ticket 保持 open，在结论里写"待主控关闭"。a2a 本地 commit 只含你的文件；fork 在 `a2a` 分支提交，不 push。
最后终端回复一行：`T-036 DONE <PASS|INCOMPLETE|BLOCKED> <a2a commit> <fork commit>`。遇到权限请求或需要用户决定的事，停下说明。
