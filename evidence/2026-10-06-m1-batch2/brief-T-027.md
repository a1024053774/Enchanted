# Worker 任务书：T-027 Muster 引擎以独立命名空间运行（build）

你是 a2a 的 worker（Codex）。主控是 Claude Code（pane wF:pM）。只做 T-027。
先读：AGENTS.md、README 的"Rust 构建：外置盘入口"、.project-map/tickets/T-027-muster-engine.md（验收以它为准）、
.project-map/specs/workbench-m1-2026-10-06.md（代码位置、命名空间、网络、控制接口与名词）、T-017、T-018、T-022、
CONTEXT.md、evidence/2026-10-06-m1-batch1/T-024/README.md（多客户端结论）。

## 做法要求
- 来源：`.upstream/herdr` 是 c4653a4 的只读克隆，不要修改它。把该提交的源码引入 `muster/engine/`，保留上游目录结构；
  优先用能记录上游提交的方式（如 `git subtree add --prefix muster/engine <path> c4653a4 --squash`，若不适用就复制并在 NOTICE 写明来源），
  保留 LICENSE，新增 NOTICE 说明派生自 herdrdev/herdr@c4653a4（Apache-2.0）。`muster/Cargo.toml` 为 workspace。
- 先拿红态：在改名前写好端到端检查（真实 `muster` 二进制、独立命名会话），确认它对缺失的行为失败，再实现。
- 命名空间按 spec 表格改：二进制 `muster`、`HERDR_*` → `MUSTER_*`、socket/日志/配置目录/hook/插件清单改名，界面与 CLI 输出里的产品名改为 Muster。
  引擎内部和 CLI 的 workspace/tab 名词本切片保持不变（spec 已说明）。
- 网络：去掉或关闭所有访问 herdr.dev 的功能（自更新、公告、发布说明、预览通道、在线检测清单）；用源码检索和运行时检查双重证明。
- 构建：只用 `MUSTER_BUILD_SLOT=worker-t027 ./scripts/build ...`，不直接调 cargo/zig。
- 安全：所有运行都用独立命名会话（名字含 t027）；不触碰用户正在使用的 Herdr server（默认会话，0.9.1）。
  启动前 unset 继承的 HERDR_* 与 MUSTER_* 环境变量。只关闭你自己创建的会话、pane 和进程。
- Codex 集成 hook：验证"会话 ID 经 Muster 自己的 hook 上报"时，安装位置若会写入用户的 ~/.codex/hooks.json，先停下向主控说明要写的内容，获准后再做；不得删除或改动 Herdr 已有的 hook 条目。
- 不改 MAP.md、AGENTS.md、README.md、CONTEXT.md；需要改时写进结论交给主控。并行的 T-025 worker 在写 `probes/t025-gpui/`，commit 只 add 你自己的文件。
- 工作量大时可分多次本地 commit，但每次都只含本 ticket 的文件。

## 验收
逐条对照 T-027 的 6 个复选框，每条附命令、输出摘要与证据路径（evidence/2026-10-06-m1-batch2/T-027/）。
只在有证据时勾选；全部勾选才把 status 改为 closed，否则保持 open 并写清剩余项。
再请一个只读子审查（可用你自己的子 agent，记录其模型）对照 ticket 审一遍，结果存档。

## 完成
- 运行 project_map.py status；本地 git commit（英文信息，末尾 `Co-Authored-By: Codex <noreply@openai.com>`），不 push。
- 最后终端回复一行：`T-027 DONE <PASS|INCOMPLETE|BLOCKED> <commit>`。
遇到权限请求、需要写用户级配置或需要用户决定的事，停下说明，不要猜。
