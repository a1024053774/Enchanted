# Worker 任务书：T-024 一个引擎能否让多个窗口各看不同项目（research，只读）

你是 a2a 项目的 worker（Codex）。主控是 Claude Code（pane wF:pM）。只做本 ticket。

先读：AGENTS.md、.project-map/MAP.md、.project-map/tickets/T-024-per-window-project-focus.md、
.project-map/specs/workbench-m1-2026-10-06.md、CONTEXT.md。源码在 .upstream/herdr（c4653a4，只读，不要修改）。

## 问题
Muster 要求每个项目一个 OS 窗口，每个窗口是同一个引擎的一个客户端。需要确认：多个客户端能否各自聚焦
不同的 workspace（对应项目），焦点、尺寸、输入互不干扰。

## 方法
1. 源码：读 src/server/headless/client_views.rs、surface_interest、client 相关模块，说明焦点/尺寸是按客户端还是全局。
2. 实测：用已安装的 herdr 0.9.3 开独立命名会话，例如 `herdr --session a2a-focus-probe`（名字带本 ticket 标识）。
   - 绝不能触碰用户正在用的默认会话：所有命令都带 `--session a2a-focus-probe` 或 HERDR_SESSION，
     不要在继承了 HERDR_SOCKET_PATH 的情况下误操作当前 server（先 unset HERDR_SOCKET_PATH HERDR_PANE_ID 等）。
   - 客户端需要真实终端：可以在本 tab 内 split 出两个临时 pane 各运行一个 TUI 客户端，或用 endpoint 协议的测试方式；
     自己创建的 pane 和会话用完要关掉（只关你自己建的）。
   - 两个客户端分别聚焦不同 workspace，检查：焦点是否独立、各自尺寸是否互相改写、输入是否只到达对应 pane。
3. 结束时停止你创建的探针会话（只停 a2a-focus-probe），确认用户的默认会话不受影响。

## 输出
- 证据写到 evidence/2026-10-06-m1-batch1/T-024/（命令、输出、截图或 pane read 文本）。
- 在 T-024 ticket 的 Resolution 写结论：observed/inferred 分开；若结论是"不支持"，给出最小的引擎改动方向。
- 结论明确后把 ticket 设为 closed；运行 project_map.py status；本地 git commit（英文信息，末尾 `Co-Authored-By: Codex <noreply@openai.com>`），不要 push。
- 最后在终端回复一行：`T-024 DONE <PASS|INCOMPLETE|BLOCKED> <commit>`。
注意：与 T-026 的 worker 并行工作，你只改 T-024 ticket 和你自己的证据目录；git commit 时只 add 你自己的文件。
