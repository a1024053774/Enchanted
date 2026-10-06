---
id: T-024
title: 一个引擎能否让多个窗口各看不同项目
type: research
status: closed
blocked_by: []
claimed_by: Codex / T-024 worker（主控 Claude Code wF:pM）
supersedes:
---

## Question

工作台要求每个项目一个窗口。Herdr 服务端在 `src/server/headless/client_views.rs` 中按客户端区分聚焦的标签页，推断多个客户端可以各自聚焦不同的 workspace，但没有核实。

最小验证：用已安装的 Herdr 0.9.3（与引擎同版本）开一个独立命名会话，例如 `herdr --session a2a-focus-probe`；连接两个客户端，各自聚焦不同的 workspace，检查焦点、尺寸和输入是否互不干扰。不得触碰用户正在使用的 server。

## Resolution

**研究实测：PASS；交接与独立审查：INCOMPLETE。** 事实问题已明确，因此关闭本 research ticket。INCOMPLETE 来自并行工作区变化触发审查员的冻结规则；审查员澄清未观察到 T-024 候选或目标源码变化，其余证据已审完，但保留原审查状态，不升级为 PASS。见[原始审查与澄清](../../evidence/2026-10-06-m1-batch1/T-024/acceptance-review.md)。

### Observed

- Herdr 0.9.3 的同一引擎支持两个活跃 endpoint generation 1 客户端各自查看不同项目。两个连接分别聚焦 `w1`、`w2`，共享同一 boot ID；A 新建和聚焦项目内任务时，B 的项目不变。
- 真实 `stty size`：A/B 初始为 31×101 / 19×73；A 缩放后为 37×119 / 19×73；B 再缩放后为 37×119 / 23×67。尺寸查询用显式 pane ID 的公开 CLI `pane run`，不通过客户端输入认领尺寸控制权。滚动条依发布配置文档关闭，期望值直接来自外部 viewport 输入。
- 带 nonce 的语义输入只在对应 pane 产生独立输出行；向未查看项目的 pane 注入被拒绝。已知坏客户端导航路径的负面对照也被拒绝：普通 CLI `workspace focus w1` 实际把两客户端同步为 `[w1,w1]`，不满足独立焦点 oracle `[w1,w2]`。
- 限制已实测：同一任务共享 pane 焦点与 PTY 尺寸，交互者可取得该任务的尺寸控制权；B 断开后，A 缩放为 29×113 时，无人查看的项目 B 也变为 29×113。因此不能宣称所有焦点、尺寸和后台状态都按窗口隔离。
- 源码 `.upstream/herdr@c4653a4f10502601ac110b12b2c45a5f7134082b`：`ClientShellLocation` 和 viewport 按连接保存，几何控制权按任务保存；公开 focus 会同步所有客户端；单活跃客户端 resize 会遍历全部项目和任务。`surface_interest` 按连接启停 surface lease，停用时释放该连接的输入、图形和几何控制权。详见[带行号的源码证据](../../evidence/2026-10-06-m1-batch1/T-024/source-review.txt)。
- 只创建独立命名会话 `a2a-T-024-focus-probe`；两个客户端与该会话均已停止，探针 server 正常退出，socket 移除。默认 0.9.1 server 的 PID 3949、启动时间、版本与 socket，以及 Claude Code `wF:pM` 的 shell PID 90461、前台 PID 95638 前后保持一致；默认会话仅只读查询。

### Inferred

- “同一引擎、每项目一个窗口”的方向可复用现有 endpoint 协议。窗口导航必须经各自的连接执行，不能用会话级 CLI focus 替代；不同项目同时活跃时，不需要另造一套项目/客户端状态或平行 API。
- 若要求关闭某项目窗口后，别的窗口也不能改变其后台 PTY 尺寸，当前引擎不支持该严格版本。最小改动方向是在 `resize_shell_tab_geometry_to_target` 删除单活跃客户端时缩放全部项目/任务的特殊分支，只调整所选任务；本 ticket 不实施改动、不改变 M1 验收条件。
- 本研究没有验收真实 OS 窗口、GPUI/IME、重连绑定、通知隔离或性能可靠性，不替代后续 app 和运行时切换门禁。

### Evidence / handoff

- [中文报告与失败记录](../../evidence/2026-10-06-m1-batch1/T-024/README.md)、[版本与启动身份](../../evidence/2026-10-06-m1-batch1/T-024/metadata.json)。`run-01`～`run-08` 的原结果全部保留；`run-06` 的探索 PASS 因尺寸查询会认领控制权而不作为最终验收。
- 最终 [run-08/result.json](../../evidence/2026-10-06-m1-batch1/T-024/run-08/result.json) 29 项检查成立；完整命令、endpoint 快照、表面文本、独立 PTY 观察及清理见该目录。复现：`python3 evidence/2026-10-06-m1-batch1/T-024/probe.py --output evidence/2026-10-06-m1-batch1/T-024/run-09`（目录必须尚不存在）。
- 只写本 ticket 和自身证据目录；地图 Decisions 索引由主控交接后维护。提交只包含这些文件，本地 commit、不 push；完整提交号由本次终端 `T-024 DONE` 收据给出。
- 结束 `project_map.py status`：Problems (1)，closed ticket 缺少 Decisions 索引行；Stale living docs (0)。任务书禁止本 worker 改地图，故保留并报告 INCOMPLETE；主控补入 T-024 索引后再核对。原输出见 [project-map-status.txt](../../evidence/2026-10-06-m1-batch1/T-024/project-map-status.txt)。
