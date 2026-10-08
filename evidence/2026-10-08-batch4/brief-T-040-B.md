# Worker 任务书：T-040 B 部分——工作台启动器与专用数据目录（build）

你是 a2a 的 worker（Codex）。主控是 Claude Code（Herdr pane wF:pM）。只做 T-040 的 B 部分（`.project-map/tickets/T-040-switchover.md`，含用户决定 Q1=A、Q2=A）。

## 目标
用户日常使用的工作台 = fork 构建的 Synara 桌面版 + 专用数据目录 `~/Library/Application Support/a2a-workbench`，与可能已安装的官方 Synara 完全分开；Codex 用用户自己的登录（Synara 的正常 CODEX_HOME overlay 做法，不复制、不改写用户 `~/.codex`）。主控（终端 Claude Code）通过门禁 CLI/MCP 派发，所以门禁的 HTTP 入口地址与鉴权要能被主控稳定找到。

## 先读
fork 的 `AGENTS.md`、`CLAUDE.md`、`a2a/scripts/bun`；a2a 的 `AGENTS.md`；`evidence/2026-10-07-synara-batch2/T-042/desktop/RESULTS.md` 与 `T-042/intervention/RESULTS.md`（Electron 启动方式、desktop-home/SYNARA_HOME、入口 `/#/a2a`、gate CLI 经 HTTP 调用与 token）。

## 要做的
1. 在 fork 新增 `a2a/scripts/workbench`（只在 `a2a/` 目录和必要的少量接入点内改动）：检查外置盘（与 `a2a/scripts/bun` 相同规则）、用标准 `build:desktop` 产物（不存在或过期就用标准命令构建；严禁移动、替换或链接构建输出与依赖目录）启动 Electron，数据目录固定为上述专用目录，后台进程脱离调用者进程组，重复启动时提示已在运行而不是再起一份。
2. 主控接入：工作台运行时，把门禁 HTTP 地址与鉴权所需信息写到一个固定位置（例如专用数据目录下的 `a2a-gates/endpoint.json`，权限 0600），并提供 `a2a/scripts/gate`：读取该文件后调用 `packages/a2a-gates/src/cli.ts`。记录这个 token 的来源、生命周期和泄露影响；不把 token 写进证据或 Git。
3. 验证（不做真实模型调用、不登录）：用一个临时测试数据目录（外置盘）代替专用目录跑一遍启动器——启动、重复启动提示、`a2a/scripts/gate status` 能连上、停止后端口无监听。再确认专用目录默认值正确、未被创建或写入（真正首次启动由用户/主控进行）。
4. 写一页中文使用说明（fork 的 `a2a/WORKBENCH.md`）：如何启动、停止、更新（拉取 fork 后重建）、数据目录位置、主控如何调用 `a2a/scripts/gate`。

## 禁止
不读写官方 Synara 数据、用户浏览器 profile、Herdr；不复制或修改 `~/.codex`；不 push。只停你启动的进程，只删你创建的文件。

## 交付
fork 在 `a2a` 分支提交；a2a 仓库证据 `evidence/2026-10-08-batch4/T-040-B/`、中文 `RESULTS.md`，只提交你的文件（ticket 只在 Resolution 下追加 B 部分说明，保持 open）。最后终端回复一行：`T-040B DONE <PASS|INCOMPLETE|BLOCKED> <a2a commit> <fork commit>`。需要决定的事停下说明。
