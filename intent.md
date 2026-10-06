# Intent：a2a 多 Agent 工作台

状态：accepted（2026-10-06）  
负责人：用户  
阶段：Plan / intent（第二阶段）  
规范地图：[`.project-map/MAP.md`](.project-map/MAP.md)  
决策记录：[`.grilling/a2a-gui-client.md`](.grilling/a2a-gui-client.md)  
评估记录：[图形客户端方向评估](findings/gui-client-assessment-2026-10-06.zh-CN.md)  
初始研究记录：[herdr-a2a-research-and-plan-2026-10-06.md](herdr-a2a-research-and-plan-2026-10-06.md)

## 用户目标

> 让协作不依赖模型持续记住操作手册。

首轮已为这个目标建成门禁层（见"首轮成果"）。第二阶段在它之上建设自有的图形工作台：

> "就做成本身还是依赖于各个 agent 的 cli 的，但是给他们做一个类似 herdr 的这种，但不要 herdr cli,构建一个 gpui,然后要有 herdr 这样的，每个项目是一个窗口，这个项目窗口里又可以给不同的任务再加各个窗口，然后每个任务的窗口里有各个 pane，用于不同 agent 分工。"

> "主要就是想要一个现代化的界面，像 codex、synara 这样，不要像是 enchanted 那样老气横秋的，看着还跟浏览器一样，初版也做像 synara 这样的果冻，可以选择不同色彩集作为强调色。"

## 要解决的问题

- 当前的多 agent 工作依赖另外安装的 Herdr，以及它的终端界面和 CLI；a2a 的运行时也绑定在 Herdr 的 9 个命令上（`coop.py`）。
- 用户要用一个现代的原生图形应用来组织多 agent 分工：每个项目一个窗口，按任务分页，在任务里给不同 agent 分 pane。
- Enchanted 现有的 Tauri + React 界面观感陈旧、像浏览器；它的功能以后要并入这个应用。

## 期望结果：第一个里程碑（M1）

工作台完全接替 Herdr，承担 a2a 的日常工作：

1. **引擎**：以 Herdr 0.9.3（`c4653a4`）引擎的硬分叉作为后台服务。关掉窗口后 agent 继续运行；重新打开时，项目窗口、任务页和 pane 都能恢复。
2. **结构**：每个项目一个窗口；任务是项目窗口里的标签页；一个任务里有多个 pane。working、blocked、idle、done 状态显示在 pane、任务标签和侧栏上。
3. **CLI**：Codex 与 Claude Code 端到端实测（启动、状态、恢复、中文输入）；本机已安装的其他 CLI 做冒烟检查；未安装的沿用引擎的检测清单，标为未验证。
4. **a2a**：`coop.py` 改用工作台的控制接口；交付 8 项、恢复 9 项、编排 18 项三套验收在新运行时上通过；主控通过工作台的控制接口，在任务页中真实跑一次 `run`。这些都达成后，删除 Herdr 路径。
5. **外观**：Codex、Synara 式的现代界面；窗口级玻璃质感（整窗或仅侧栏半透明，透明度可调）；强调色可从多套配色中选择；中文输入与复制正常。

## 范围

M1 之内：上述五项；agent 继续以各自的 CLI 运行在终端 pane 中；工作台为 a2a 主控和 worker 提供与现有 9 个 Herdr 命令等价的控制接口。

不在 M1：

- 对话视图（由原生会话记录生成的结构化视图），随 Enchanted 并入时再做；
- Enchanted 的其他功能（回放、Evidence、Improve、用量）；
- 远程机器（SSH）、插件、Windows 与 Linux 版本；
- 元素级背景模糊，例如悬浮输入框模糊下方内容；
- 从 Herdr 上游同步检测清单和修复，以后单独同步。

不在本 intent 内：

- 基于 Zed 二次开发（评估判为 NO_GO）；
- 通用 A2A 平台、分布式调度、多机部署；
- 自动解决复杂语义冲突、自动批准权限，或把未知副作用标成成功；
- 生产发布和不可逆外部操作；
- 改写 dated 初始研究记录。

## 约束

- **门禁优先**：界面上对受管任务的验收、集成和回收，只调用 `coop.py` 的同一入口，不另做一套门禁；在受管 worker 的 pane 里直接输入，记为人工介入。
- **不用 Herdr CLI**：用户只通过工作台操作。
- **引擎**：硬分叉，从 Herdr 0.9.3 开始自主演进；fork 中不自动拉取 Herdr 的在线检测清单，清单与上游修复以后单独同步。新引擎使用独立的命名空间（可执行文件名、环境变量、socket 目录、集成 hook），在切换完成前与已安装的 Herdr 并存。
- **构建**：a2a 与 Enchanted 的构建缓存默认放在外置硬盘 `/Volumes/WD-Elements`；外置盘未挂载时构建直接报错，不回退到内置盘。用户接受机械硬盘较慢。
- **许可**：永不闭源；自用并开源；允许直接复用 GPL 代码。并入 GPL 代码后，整体以 GPL-3.0 开源。
- **复用**：能复用就复用，但不因此改变方向；多 CLI 支持这类关键代码优先参考他人的设计（Herdr、Synara、muxel）。
- **平台**：M1 只面向 macOS。

## 术语

项目、任务、Pane、原生会话等术语以 [`CONTEXT.md`](CONTEXT.md) 为准。任务就是 a2a 的 Task：在界面上是项目窗口里的标签页，验收合同可以稍后再挂，挂上后才走 claim、submit、验收和集成门禁。

## 角色、模型与权限

| 角色 | 当前配置 | 权限边界 |
| --- | --- | --- |
| 主控 controller | `gpt-6-astra`，max reasoning | 在已批准范围内理解目标、分派和回收 worker、汇总证据；不得越过门禁，也不得替未知结果判成功 |
| 执行 worker | `gpt-6.1-sol`，xhigh reasoning，Fast service tier | 只在分配的 task/attempt 范围内实现或分析 |
| 监控 monitor | `gpt-6.1-sol`，high reasoning | 只读记录和报警；不得 claim、submit、集成或宣布成功 |
| 用户 | 人工负责人 | 决定目标与范围、验收与权限变化、不可逆外部效果、方向性取舍和发布 |

主控可以自主完成日常分派、状态检查、策略内重试和回收。遇到下列任一情况必须停下并问用户：

- 目标或范围发生变化；
- 验收条件、权限或允许的外部操作需要变化；
- 将产生不可逆的外部副作用；
- 外部状态无法核对或彼此冲突；
- 设计取舍会改变本 intent 的目的地；
- 预算或风险越界。

切换完成前，主控与 worker 仍经已安装的 Herdr 分派；切换完成后改用工作台的控制接口。

## 可观察成功条件

M1 达成时至少留下：

- 新运行时上三套验收（8、9、18 项）的通过记录，以及一次真实 `run` 的追加式运行记录：模型、CLI 与引擎版本，task、attempt、submit、验收、集成、人工介入和失败事件；
- 关闭并重开应用后，agent 进程仍在、项目窗口与任务页得到恢复的记录；
- Codex 与 Claude Code 的端到端检查记录（启动、状态、恢复、中文输入），已安装 CLI 的冒烟结果，以及未验证 CLI 清单；
- 玻璃质感、强调色切换、中文输入与复制的截图或录屏；外观是否达标由用户判断。

首轮的原则继续适用：终端 `idle`/`done` 或模型自报不能单独使交付成功；任何收益主张都需要独立对照实验。

## 首轮成果

T-006～T-008 已在已安装的 Herdr 上通过：[受管交付](evidence/2026-10-06-managed-01/RESULTS.md)、[中断恢复](evidence/2026-10-06-recovery-01/RESULTS.md)、[自动运行](evidence/2026-10-06-run-01/RESULTS.md)。这些证据只对 Herdr 运行时成立；切换到新运行时后，须重跑同样的验收。

## 事实、未知与最小验证

| 项目 | 状态 | 依据或最小验证 | 负责人 |
| --- | --- | --- | --- |
| Herdr 支持的 CLI 与检测方式 | observed | 23 个由 Herdr 支持、5 个自报状态；22 个 TOML 检测清单 | — |
| 多个窗口各看不同项目 | inferred | 服务端按客户端区分聚焦的标签页（`client_views.rs`）；spec 阶段核实 | spec session |
| 引擎编译需要 Zig | observed | 本机未安装；工具链缓存同样放外置盘 | spec session |
| GPUI 玻璃质感的边界 | observed | 有窗口级模糊；强度可调需要私有 macOS 接口；没有元素级背景模糊 | spec session |
| GPUI 上的中文输入与复制 | unknown | 在本机 macOS 27 上实测 | spec session |
| 机械硬盘上的构建耗时与多 worker 并发编译 | unknown | spec 阶段测量 | spec session |
| 9 个 Herdr 命令在新控制接口中的等价实现 | unknown | 在新运行时上重跑现有三套验收 | build session |

## 治理与规范

项目地图是流程索引，`CONTEXT.md` 是术语表，本文件是本阶段的 canonical artifact，dated 研究稿和评估记录是证据记录，`.grilling/` 只保存决策会话 ledger。每次 session 先运行 `project_map.py status`，读取地图、相关 ticket 和本文；一次只做一个 build ticket。

按阶段使用本机规范 skill：`project-map` 管理地图、ticket、spec 和 tracer-bullet slice；`reality-first-engineering` 在架构或大范围实现前处理事实与方向门；`evidence-first-testing` 为行为变化保留失败证据和反事实；`design-integrity-review` 在结构风险变更完成时检查；`behavioral-acceptance-review` 审查独立行为证据；`document-writing` 负责项目文档；`frontend-less-ai-tone` 与 `same-visual-family` 负责界面文案与视觉方向；`grilling` 只用于决策和交接，不在会话内实现。

## 风险等级与交接

这是影响代码、Git 工作区、进程和 agent 权限的 consequential 项目，采用人工门控。本 intent 允许在批准范围内开始 Design / Spec 和后续切片，不授权把未知状态写成成功。

下一步：按 [Muster 工作台 M1 spec 与初步任务书](.project-map/specs/workbench-m1-2026-10-06.md) 执行；工作台名为 Muster，代码位于本仓库。Enchanted 已于 2026-10-06 做 git 快照并冻结（T-021）。
