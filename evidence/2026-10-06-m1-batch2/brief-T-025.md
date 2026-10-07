# Worker 任务书：T-025 本机 GPUI 的中文输入、复制与玻璃质感（research）

你是 a2a 的 worker（Codex）。主控是 Claude Code（pane wF:pM）。只做 T-025，不扩大范围。
先读：AGENTS.md、README 的"Rust 构建：外置盘入口"、.project-map/tickets/T-025-gpui-cjk-glass-probe.md、
.project-map/specs/workbench-m1-2026-10-06.md 的"界面""构建与工具链"、CONTEXT.md、
findings/gui-client-assessment-2026-10-06.zh-CN.md 中 P2 的描述。

## 边界
- 代码只放在 `probes/t025-gpui/`（独立 Cargo 包，不加入 `muster/` workspace）。证据放 `evidence/2026-10-06-m1-batch2/T-025/`。
- 所有构建都用 `MUSTER_BUILD_SLOT=worker-t025 ./scripts/build ...`；不得直接调 cargo。
- 依赖锁定 gpui-kit 0.7.1（它固定 gpui-pre =0.3.8）并提交 Cargo.lock。依赖说明以 crates.io / 该版本源码和 docs.rs 为准，不凭记忆写 API。
- 不改 MAP.md、AGENTS.md、README.md、CONTEXT.md；需要改时写进结论交给主控。并行的 T-027 worker 在写 `muster/`，git commit 只 add 你自己的文件。

## 要做的
1. 最小应用：一个窗口，左侧半透明侧栏，右侧一个多行 Input 和一个 Markdown TextView（含中文、代码块、emoji 的样例正文）。
   窗口背景用 Blurred；提供切换"整窗半透明 / 仅侧栏半透明"与透明度的控件或启动参数。
2. 能自动验证的自动验证：编译、启动、窗口出现（`screencapture` 截图存档）、通过 GPUI 无头测试检查状态到视图的逻辑（若可行）。
3. 中文输入法和跨段复制需要真人操作：写一份 `MANUAL-CHECK.md`，给出启动命令、逐步操作、每一步的预期文本
   （拼音输入"会话复盘：证据引用"、连续组词、取消候选、删除、撤销、切换输入框；从正文跨中文、代码、emoji 选中复制粘贴到"文本编辑"），
   以及用户填写实际结果的位置。你自己不能宣称 IME 通过。
4. 记录：构建耗时、target 占用、运行时窗口截图、遇到的 API 版本问题与修正次数（编译修错轮数）。

## 完成
- T-025 ticket 的 Resolution 写清已自动核实的部分与待用户手测的部分；在用户手测前保持 status: open，结论为 INCOMPLETE。
- 运行 project_map.py status；本地 git commit（英文信息，末尾 `Co-Authored-By: Codex <noreply@openai.com>`），不 push。
- 最后终端回复一行：`T-025 DONE <PASS|INCOMPLETE|BLOCKED> <commit>`。
遇到权限请求或需要用户决定的事，停下说明，不要猜。
