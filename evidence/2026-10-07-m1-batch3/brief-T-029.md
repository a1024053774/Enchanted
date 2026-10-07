# Worker 任务书：T-029 coop.py 改接 Muster 控制接口（build）

你是 a2a 的 worker（Codex）。主控是 Claude Code（Herdr pane wF:pM）。只做 T-029。
先读：AGENTS.md、README（含 Muster 引擎与 Rust 构建两节）、.project-map/tickets/T-029-coop-on-muster.md（验收以它为准）、
.project-map/specs/workbench-m1-2026-10-06.md（"控制接口与名词"）、T-018、
.project-map/specs/managed-delivery-2026-10-06.md、recovery-2026-10-06.md、supervised-run-2026-10-06.md、
evidence/2026-10-06-m1-batch2/T-027/RESULTS.md（引擎能力、隔离会话做法、限制）、CONTEXT.md。

## 要求
- `coop.py` 只调用 `muster`，不再调用 `herdr`，不留 Herdr/Muster 双路径或回退；门禁语义（claim、submit、verify、integrate、reclaim、run）不变。
  `muster` 可执行文件的位置要显式给定（例如命令行参数或明确的环境变量），找不到就报错，不回退到 `herdr`。启动 argv、版本输出写入运行记录。
- 先拿红态：在改代码前，用现有三套验收（交付 8、恢复 9、编排 18）和 live 入口对 Muster 跑一次，保存失败证据；再改实现与夹具。
  编排负例里的替身改成模拟 muster 边界，并在报告中标明是隔离证据。不得为让测试通过而改写 oracle 的预期答案。
- 构建 muster 只经 `MUSTER_BUILD_SLOT=worker-t029 ./scripts/build ...`；可复用 T-027 的冻结二进制做早期检查，但最终证据必须用本 ticket 冻结候选构建的二进制。
- 真实 `run`：在独立命名的 muster 会话（名字含 t029）中开 pane，从 muster pane 内调用 `coop.py run`，Codex worker 在 muster pane 中完成分页夹具、显式 submit、独立 oracle 验收、CAS 集成并回收 pane。
  Codex 仍用用户正常的 ~/.codex（不改它）；如出现目录信任、hooks review 或任何权限对话，停下并把现场与请求写入证据，等主控批准，不要自行回答。
- 反事实：去掉 attempt 绑定或 fence 校验的错误实现，在 Muster 运行时上必须被验收抓住，保存 mutant 结果。
- 安全：不修改或重启用户正在使用的 Herdr server（默认会话）；只停止你自己创建的 muster 会话；运行前剥离继承的 HERDR_* / MUSTER_* 变量。
- 不改 MAP.md、AGENTS.md、README.md、CONTEXT.md；需要改时写进结论交给主控。只 add 你自己的文件。
- 证据目录：evidence/2026-10-07-m1-batch3/T-029/。

## 验收与审查
逐条对照 T-029 的 4 个复选框，附命令、输出摘要、证据路径；只在有证据时勾选，全部勾选才 closed。
冻结候选后做一次 fresh-context 只读独立审查（记录审查模型与冻结提交）；审查期间不要修改已跟踪文件。

## 完成
运行 project_map.py status；本地 git commit（英文信息，末尾 `Co-Authored-By: Codex <noreply@openai.com>`），不 push。
最后终端回复一行：`T-029 DONE <PASS|INCOMPLETE|BLOCKED> <commit>`。
遇到权限请求、需要写用户级配置或需要用户决定的事，停下说明，不要猜。
