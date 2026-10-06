# T-024：同一引擎的多项目客户端实测（2026-10-06）

结论：**支持两个活跃客户端分别查看不同项目，项目焦点、PTY 尺寸和输入可独立。并非所有焦点和尺寸操作都按客户端隔离。** 界面导航必须通过各自的 endpoint 连接。普通 CLI 焦点命令会同步所有客户端；同一任务的 pane 焦点和 PTY 尺寸共享；只剩一个活跃客户端时，缩放会改变无人查看的项目。

本记录只完成 T-024 的研究，不是 Muster.app、M1 或模型驱动 Agent 产品的发布验收。冻结的主要证据是 [run-08](run-08/)，独立审查结果见 [acceptance-review.md](acceptance-review.md)。

**交接状态：INCOMPLETE。** 最终真实探针为 PASS；独立审查保留 INCOMPLETE，原因是并行 T-026 的工作区治理差分触发审查员的冻结限制。审查员随后确认没有观察到指定候选或源码变化，其余证据已经审完；原结论没有提升为 PASS。T-024 的事实问题已明确，ticket 因此关闭。结束时地图检查另报 1 个问题：closed ticket 缺少 Decisions 索引行；stale living docs 为 0。任务书限定本 worker 只写 ticket 和自身证据，索引行需主控补入，不能把地图检查写成 PASS。

## 范围与身份

- 任务书：[brief-T-024.md](../brief-T-024.md)。规格：[workbench-m1-2026-10-06.md](../../../.project-map/specs/workbench-m1-2026-10-06.md)，承接第二阶段 `intent.md`。
- 主控：Claude Code，默认会话 `wF:pM`；worker：Codex，`wF:pP`。本次没有启动其他实现 worker，没有在受管 pane 中输入。
- 安装的 CLI 和探针 server：Herdr **0.9.3**；只读源码：`.upstream/herdr`，完整版本 **`c4653a4f10502601ac110b12b2c45a5f7134082b`**。
- 用户默认 server 实际为 **0.9.1**。探针不复用它，不升级、不重启；默认会话仅接受状态和进程身份查询。
- 探针会话：`a2a-T-024-focus-probe`。每次运行使用新的短 `/tmp/a2a-T024-*/` 目录及独立的 XDG 配置、状态和缓存。移除继承的全部 `HERDR_*`，随后仅为探针设置关闭声音的变量；每条 Herdr 命令显式指定会话。
- 两个独立 Unix socket 连接协商 endpoint generation 1，连接同一 server boot。终端内容、控制请求和语义输入都经过已安装引擎；不是模拟 server 或 mock PTY。
- `version_check=false`、`manifest_check=false` 禁用探针的线上检测。最终探针设置 `ui.pane_scrollbars=false`；0.9.3 配置文档明确说明此选项回收滚动条列，因此单 pane 的期望尺寸直接来自外部给定的 viewport 尺寸。
- 版本、启动 argv、模型配置、skill 版本及时间见 [metadata.json](metadata.json)。启动参数请求 `gpt-6.1-sol`、`xhigh`、`service_tier="fast"`；这些不是供应商实际服务档位的证明。无人工介入；首次运行到本记录截止点的原始失败均保留。

## Observed：真实引擎实测

最终运行：[result.json](run-08/result.json)、[events.ndjson](run-08/events.ndjson)、[probe-used.py](run-08/probe-used.py)。29 项检查全部成立，其中包括版本、行为边界及清理检查，不能把 29 项解释为 29 个独立可靠性样本。业务输入是两个不同项目、两个不同 viewport、一次项目内新任务导航、两次相反方向的缩放、带运行 nonce 的终端输入，以及负面对照。

尺寸表统一使用 **行 × 列**：

| 步骤 | 项目 A / 客户端 A | 项目 B / 客户端 B |
| --- | --- | --- |
| 分别聚焦 | `w1`，31 × 101 | `w2`，19 × 73 |
| 仅 A 缩放 | 37 × 119 | 19 × 73，保持原样 |
| 仅 B 缩放 | 37 × 119，保持原样 | 23 × 67 |

尺寸由 pane 内真实 `stty size` 观察。查询经显式 pane ID 的公开 CLI `pane run` 发出，该操作不认领几何控制权，避免用客户端输入先修正尺寸再测量。viewport 大小是探针输入，不从引擎输出生成期望值。

- A、B 的最新快照分别聚焦 `w1`、`w2`，boot ID 相同。A 新建并聚焦任务 A2 时，B 仍停在项目 B。
- A、B 各自的 nonce 标记只出现在对应 pane；等待条件要求标记成为独立输出行，不能只靠命令回显证明执行。A 试图向 B 的 pane 注入另一标记被拒绝；同连接导航请求完成后，再由 B 写入屏障标记，确认目标终端可用。
- **已知坏客户端路径的负面对照**：用公开 CLI `workspace focus w1` 代替客户端内导航，两个客户端实际都变成 `w1`；同一个独立焦点 oracle `[w1,w2]` 拒绝此路径。该对照没有修改或编译引擎源码。
- **同任务共享尺寸**：两个客户端查看 A2 时，B 的导航使共享 PTY 为 23 × 67；A 再发送实际输入后，变为 37 × 119。不能宣称同一个任务有两套独立 PTY 尺寸。
- **单活跃客户端边界**：B 断开后，A 保持项目 A 焦点并可继续运行。A 缩放至 29 × 113，无人查看的项目 B 也变为 29 × 113。关闭项目窗口后的后台 PTY 尺寸并不会保持冻结。
- 最终证据包含三块 pane 的 [读取文本](run-08/) 和 [B 断开后的后台文本](run-08/background-after-detach-read.txt)。endpoint 的快照、viewport 尺寸和单元格文本记录在事件文件中；任务书允许协议实测，因此本次没有创建 OS 图形窗口或截图。

## Observed：只读源码

完整定位摘录见 [source-review.txt](source-review.txt)，每段带原文件行号。

| 代码位置 | 事实 |
| --- | --- |
| `src/server/clients.rs:64`、`:131` | 每个连接有 `ClientShellLocation`、`terminal_size`、`shell_surface_active`；项目及每项目的活动任务按连接记录。 |
| `src/server/headless/client_views.rs:63`、`:328`、`:916` | 客户端内项目/任务导航按 `client_id` 改动该连接；调用全局 App 操作前后投影该客户端的位置。 |
| `src/server/client_shell.rs:38` | 快照使用连接的位置生成聚焦项目和任务；聚焦 pane 来自对应任务的共享 layout。 |
| `src/server/headless/client_views.rs:566`、`:693`、`:736` | 尺寸取自客户端，控制权按任务保存。多活跃客户端时，只调整所选任务；`app_client_count()==1` 时遍历全部项目和任务。 |
| `src/server/headless.rs:2187`、`:2318` | resize 按连接更新尺寸并核对任务控制者；语义输入检查客户端是否活跃及是否查看目标 pane。合法交互可以取得该任务的尺寸控制权。 |
| `src/server/headless/client_views.rs:806`、`:894` | 公开 API 成功的显式焦点请求会调用 `focus_all_shell_clients_on_default_target`，所以 CLI focus 具有会话级影响。 |
| `src/server/headless/surface_interest.rs:9` | surface lease 按客户端启停，重置其投影代次；停用时释放该连接的输入、图形与尺寸控制权，再重算剩余客户端。它不是另一个项目状态存储。 |

## Inferred：对 Muster 的含义与最小改动方向

**Ubiquitous language**：本研究的 `workspace` 对应项目，`tab` 对应任务，`ClientShell` 对应一个窗口的引擎客户端；没有修改现有术语表。

同一引擎加“每项目一个窗口”的方向可以沿用现有 endpoint generation 1：每个窗口持有自己的连接，经该连接选择项目与任务、提交 viewport 和语义输入。两个项目同时打开所需的核心状态已经存在，无需另造引擎或平行 API。后续客户端库应按 **Deep modules** 保持小接口，将协商、快照与帧协议隐藏在库中；这只是下一切片的接口约束，本 ticket 不实现库。

如果“互不干扰”进一步要求关闭窗口后其他窗口也不能改变该项目后台 PTY 尺寸，当前引擎**不支持这个严格版本**。最小根因改动位于 `resize_shell_tab_geometry_to_target`：删除单活跃客户端时缩放所有项目/任务的特殊分支，只调整所选任务，并保留现有按任务的控制权。若公开 CLI focus 也必须只影响某个窗口，应另行定义客户端目标的控制契约；不能让窗口导航调用现有会话级焦点入口并假装它已经隔离。本 ticket 只报告事实和方向，不修改引擎或扩展 M1 的验收条件。

OS 窗口、GPUI、IME、复制、同 pane 双写冲突、通知/弹窗隔离、重连后的项目绑定和性能可靠性没有在本研究中验收；本次结果不能替代 T-025、T-027、T-028 或运行时切换门禁。

## 失败、修正与保留

| 运行 | 原始结果 | 原因与处理 |
| --- | --- | --- |
| `run-01` | INCOMPLETE | macOS 默认临时目录使 Unix socket 路径超长；改为显式短 `/tmp`。原退出记录、配置和补核记录保留。 |
| `run-02` | INCOMPLETE | 记录函数的 `kind` 参数与协议控制字段冲突，且读线程错误中断了清理；修正记录器及清理次序。补核发现原探针已退出，停止请求返回 Connection refused；保留原结果、归档和补核。 |
| `run-03` | INCOMPLETE | 探针误把 `pane read` 的纯文本当作 JSON；修正读取器。 |
| `run-04` | INCOMPLETE | 默认滚动条占一列，实际宽度为 100/72，否定了直接等于 viewport 的原断言；依据发布配置文档关闭滚动条，保留此次反例。 |
| `run-05` | INCOMPLETE | `workspace.list` 不在 endpoint welcome 的方法清单；屏障改用已协商支持的 `workspace.focus`。 |
| `run-06` | PASS（探索运行原结果） | 完成全部场景；随后发现尺寸查询自身发送客户端输入、可能认领控制权，因此此运行不作为最终验收。其原 PASS 文件保留，不能替最终候选背书。 |
| `run-07` | INCOMPLETE | 换成不认领控制权的尺寸观察后，同任务场景缺少 A 的实际交互刺激；原断言失败。补充显式输入刺激。 |
| `run-08` | PASS（最终研究证据） | 使用独立尺寸观察和独立输出行条件，完成所有场景及清理；代码冻结在 `probe-used.py`。 |

最终运行主动停止自己的两个协议客户端及命名会话，探针 server 正常退出、两种 socket 消失，session 查询为 stopped；没有创建用户会话的临时 pane。各次运行的配置、server 日志和保存状态归档在对应 `runtime/`，原 `/tmp` 现场保留，未删除来掩盖失败。

最终 [default-before.json](run-08/default-before.json) 与 [default-after.json](run-08/default-after.json) 确认：默认 server PID **3949**、启动时间、0.9.1 状态、socket 路径未变；主控 `wF:pM` 的 shell PID **90461** 和 Claude 前台进程 PID **95638** 未变。只读观察只能证明这些身份和可达性，不宣称核对了默认会话所有业务状态。

## 复现与交接

在仓库根目录、Herdr 受管 pane 中运行，选择一个不存在的输出目录，避免覆盖证据：

```sh
python3 evidence/2026-10-06-m1-batch1/T-024/probe.py --output evidence/2026-10-06-m1-batch1/T-024/run-09
```

程序保存完整命令、协议事件、终端读取、检查结果和前后身份；实际 server argv 为 `/Users/luckye/.local/bin/herdr --session a2a-T-024-focus-probe server`，所有 API/生命周期命令继承该运行独立的 `XDG_CONFIG_HOME`。

本 worker 只写 T-024 ticket 与本目录。任务书原文：“你只改 T-024 ticket 和你自己的证据目录”；地图的 Decisions 索引由主控在交接后维护。结束状态见 [project-map-status.txt](project-map-status.txt)：`Problems (1)`、`Stale living docs (0)`，退出码 1。最小收尾是在 `MAP.md` 的 Decisions so far 增加 T-024 链接及“不同项目客户端可独立；CLI focus 与单活跃客户端 resize 有全局边界”的一行摘要，然后再运行 status。

[`project-map` 技能](/Users/luckye/.agents/skills/project-map/SKILL.md) 的 Tickets 步骤要求：“for every non-`build` ticket add one line to *Decisions so far*”。本次没有越过任务书的写入所有权，也没有据此扩大修改范围；因此治理收尾仍为 INCOMPLETE。提交只包含本 ticket 与本目录，本地提交、不 push。
