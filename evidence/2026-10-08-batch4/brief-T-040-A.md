# Worker 任务书：T-040 A 部分——删除 Muster 与 coop.py 运行路径（build）

你是 a2a 的 worker（Codex）。主控是 Claude Code（Herdr pane wF:pM）。只做 T-040 的 A 部分（`.project-map/tickets/T-040-switchover.md`，含用户决定）。用户已确认切换并要求删除旧路径；已推送备份（a2a `be59634`）。

## 先读
`AGENTS.md`、`CONTEXT.md`、`intent.md`、T-040；`evidence/2026-10-07-synara-batch2/T-037/RESULTS.md`（原生 18 项副本 `test_run_native_e2e.py`、`native-entry.py`、复现命令）；`evidence/2026-10-07-synara-batch1/T-036/RESULTS.md`（恢复副本的入口身份两行 diff，`native-acceptance/`）。

## 要做的
1. 先写删除清单（文件、理由、谁引用它）存入证据，再动手。预期包括：`coop.py`、`muster/`（含 `engine/`）、根 `Cargo.toml`/`Cargo.lock`、只服务于 Muster 的 `scripts/build`、`acceptance/live_muster.py`、`acceptance/live_run.py`、依赖 Muster 的 `probes/t025-gpui/`。清单之外若还有运行时引用，或某项你判断不该删，停下问主控。`evidence/`、`findings/`、`reports/`、`.project-map/`、`.grilling/` 中的历史记录一律不改。
2. 验收脚本改为原生入口：把 T-037 证据中的原生 18 项（`test_run_native_e2e.py` 与它的线程边界替身）提升为 `acceptance/test_run_e2e.py`；`test_recovery_e2e.py` 采用 T-036 批准的入口身份两行改动；`test_coop_e2e.py` 的默认入口改为 `acceptance/entry/a2a_gates.py`（原生门禁）。业务断言、预期答案、场景数不变；与原文件的完整 diff 存入证据并逐项说明。
3. 先在删除前用原生入口跑一遍 8/9/18 作为基线，删除后在同一 fork 版本（`~/Documents/Code/synara` 分支 `a2a`，`d3b5bcc`）上再跑 8/9/18；两次结果都保存。再做一次反例：把入口临时指回已删除的 `coop.py`，确认验收明确失败（入口不存在），证明已没有旧路径可走。
4. 更新 README 中的运行说明（删去 coop.py/Muster/`scripts/build` 用法，改为原生门禁入口的用法）。AGENTS.md、CONTEXT.md、地图由主控更新，你不改。

## 禁止
不改 fork 代码；不碰 Synara 数据、`~/.codex`、Herdr；不 push。严禁移动、替换或链接构建输出与依赖目录。Bun/Node 只经 fork 的 `a2a/scripts/bun`。

## 交付
证据 `evidence/2026-10-08-batch4/T-040-A/`，中文 `RESULTS.md`；只提交你的改动与证据（ticket 只在 Resolution 下追加 A 部分说明，保持 open）。fresh-context 只读独立审查一次。最后终端回复一行：`T-040A DONE <PASS|INCOMPLETE|BLOCKED> <a2a commit>`。需要决定的事停下说明。
