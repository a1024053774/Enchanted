# Intent：a2a 多 Agent 工作台（基于 Synara）

状态：accepted（2026-10-07）  
负责人：用户  
阶段：Plan / intent（第二阶段，2026-10-07 修订）  
规范地图：[`.project-map/MAP.md`](.project-map/MAP.md)  
决策记录：[`.grilling/synara-fork.md`](.grilling/synara-fork.md)（本次修订）、[`.grilling/a2a-gui-client.md`](.grilling/a2a-gui-client.md)（被部分取代的上一版）  
初始研究记录：[herdr-a2a-research-and-plan-2026-10-06.md](herdr-a2a-research-and-plan-2026-10-06.md)  
角色修订：2026-10-09 主控拆为构思主控与执行主控，见 [spec](.project-map/specs/controller-split-user-input-2026-10-09.md)；本文件只改了“角色、模型与权限”一节

## 用户目标

> 让协作不依赖模型持续记住操作手册。

首轮已为这个目标建成门禁层（见"首轮成果"）。第二阶段原计划从零自建 GPUI 工作台，2026-10-07 改为复用 Synara：

> "我说白了，codex做的UI屎的不行，我真受不了。我现在想到，咱们从0做UI还是不现实，简直灾难。所以咱们复用https://github.com/Emanuele-web04/synara的仓库吧，在他的仓库上fork然后继续做我们想要的a2a以及enchanted。"

界面的层级要求：

> "反正就是要项目 任务 agent 这样的层级展开，一个项目里可以有多个任务窗口，一个任务窗口里可以有多个agent"

对外观的要求仍然有效：现代界面，参照 Codex 与 Synara，不要浏览器式的旧界面。

## 要解决的问题

- 从零自建 GPUI 界面的结果不可接受（T-025 录屏），自建成本过高。
- 当前多 agent 分工依赖另外安装的 Herdr；a2a 门禁（`coop.py`）只能经终端读屏判断 agent 状态。
- Enchanted 的界面观感陈旧，它的功能以后要并入同一个应用。

## 方案

- 在 GitHub 上 fork Synara（`a1024053774/synara`，起点 v1.0.1-beta.2），单独 clone；持续跟进上游，我们的功能做成独立模块，对核心只做少量补丁，通用修复回馈作者。
- agent 以 Synara 的原生协议会话为主（Codex app-server、Claude Agent SDK、ACP、OpenCode SDK），终端为辅；仍使用本机已安装、已登录的各家 CLI。
- a2a 门禁在 Synara 服务端用 TypeScript 原生重写，做成独立 package；`coop.py` 与 Muster 引擎冻结为参考实现。
- a2a 仓库继续保管规范、门禁契约、验收场景与证据。

## 期望结果：第一个里程碑（M1）

1. **能跑起来**：从我们的 fork 构建并运行 Synara 桌面版；按"构建"约束安装依赖与缓存，记录内置盘占用和安装、dev server 启动耗时；至少完成一次上游合并演练。
2. **层级**：界面按"项目 → 任务 → agent"展开，一个项目里有多个任务，一个任务里有多个 agent 会话分工。Synara 缺少"一个任务包含多个 agent"的分组时，在 fork 中以独立模块补上。"任务窗口"指应用内的区域，不要求独立的系统窗口。
3. **原生门禁**：门禁 package 在 Synara 服务端实现 task、attempt、claim、submit、verify、integrate、reclaim、run，提供外部可调用的门禁入口；移植后的交付 8 项、恢复 9 项、编排 18 项场景经该入口全部通过，反例被抓住。
4. **真实闭环**：主控经门禁派一个 Codex worker 会话（经 Codex app-server），worker 完成分页夹具并显式 submit，再经独立 oracle 验收、CAS 集成、收尾回收。
5. **界面可见**：受管任务的门禁状态（claimed、submitted、verified、accepted）在界面上可见；界面对受管任务的操作只走门禁入口。
6. **切换**：以上通过后，主控与 worker 的日常分派从 Herdr 改到 Synara，删除 Muster 与 `coop.py` 的运行路径。

## 范围

不在 M1：

- Enchanted 的功能，在门禁接入 Synara 之后再并入；并入方式等重叠调研后决定；
- Windows 与 Linux 版本；
- 每个项目一个独立系统窗口。

不在本 intent 内：

- 从零自建 GPUI 界面，以及基于 Zed 二次开发；
- 通用 A2A 平台、分布式调度、多机部署；
- 自动解决复杂语义冲突、自动批准权限，或把未知副作用标成成功；
- 生产发布和不可逆外部操作；
- 改写 dated 初始研究记录。

## 约束

- **门禁契约不变**：照搬 [受管交付](.project-map/specs/managed-delivery-2026-10-06.md)、[恢复](.project-map/specs/recovery-2026-10-06.md)、[自动运行](.project-map/specs/supervised-run-2026-10-06.md) 三份冻结规格中的锁、fence、CAS、attempt 绑定与中断恢复语义。
- **唯一门禁入口**：验收、集成、回收只经唯一的门禁入口，保持同样的锁语义；界面不另做一套门禁。在受管 worker 会话中直接输入，记为人工介入。
- **重新证明**：旧实现的通过结论不替新实现背书；移植场景须重新取得红态、绿态与反例。
- **跟进上游**：门禁与我们的功能是独立 package 或模块，对 Synara 核心只做少量接入。
- **旧实现**：`coop.py` 与 Muster 冻结为参考实现，不再开发；新门禁通过同样的验收后删除 Muster，不保留两套路径。
- **构建**：fork 的 checkout 放内置盘；Bun 全局缓存、Electron 下载等缓存放外置盘 `/Volumes/WD-Elements`，外置盘未挂载时构建直接报错，不回退到内置盘。a2a 仓库自身的 Rust 构建继续经 `scripts/build`。
- **许可**：永不闭源；自用并开源。Synara 为 MIT 许可，保留其版权声明；允许直接复用 GPL 代码，并入 GPL 代码后整体以 GPL-3.0 开源。
- **平台**：M1 只面向 macOS。

## 角色、模型与权限

| 角色 | 当前配置 | 权限边界 |
| --- | --- | --- |
| 构思主控 ideation controller | Claude Code（用户 2026-10-09 定为上层主控） | 接收想法、澄清、写决定/spec/ticket、标就绪、向执行主控分发任务、转述完成报告；不直接派发、验收、集成、回收 worker |
| 执行主控 executor controller | Claude Code（用户 2026-10-06 指定，原称主控） | 在已批准范围内监督就绪 ticket 的执行：分派和回收 worker、汇总证据；不得越过门禁，也不得替未知结果判成功 |
| 执行 worker | `gpt-6.1-sol`，xhigh reasoning，Fast service tier | 只在分配的 task/attempt 范围内实现或分析 |
| 监控 monitor | `gpt-6.1-sol`，high reasoning | 只读记录和报警；不得 claim、submit、集成或宣布成功 |
| 用户 | 人工负责人 | 决定目标与范围、验收与权限变化、不可逆外部效果、方向性取舍和发布 |

执行主控可以自主完成日常分派、状态检查、策略内重试和回收，并在已批准范围内自建缺陷级 ticket。遇到下列任一情况必须停下并问用户（执行主控经构思主控向用户说明）：

- 目标或范围发生变化；
- 验收条件、权限或允许的外部操作需要变化；
- 将产生不可逆的外部副作用；
- 外部状态无法核对或彼此冲突；
- 设计取舍会改变本 intent 的目的地；
- 预算或风险越界。

日常派发何时改走工作台由用户判断：切换的技术条件已于 2026-10-09 具备，用户决定工作台可用后再改，条件见 AGENTS.md 与上面的 spec。

## 可观察成功条件

M1 达成时至少留下：

- fork 的构建与运行记录：提交、上游基线、依赖与缓存位置、内置盘占用和耗时，以及一次上游合并演练的结果；
- 层级的截图或录屏：一个项目下有多个任务，一个任务下有多个 agent 会话；
- 门禁入口上移植场景（8、9、18 项）的通过记录、红态与反例记录；
- 一次真实闭环的追加式运行记录：模型、CLI 与 Synara 版本，task、attempt、submit、验收、集成、人工介入和失败事件；
- 界面显示门禁状态的截图；外观由用户判断。

首轮的原则继续适用：模型自报或会话"完成"不能单独使交付成功；任何收益主张都需要独立对照实验。

## 首轮成果与参考实现

- T-006～T-008 在已安装的 Herdr 上通过：[受管交付](evidence/2026-10-06-managed-01/RESULTS.md)、[中断恢复](evidence/2026-10-06-recovery-01/RESULTS.md)、[自动运行](evidence/2026-10-06-run-01/RESULTS.md)。
- T-027 Muster 引擎（Herdr 硬分叉）与 T-029 `coop.py` 改接 Muster 已验收：[T-027](evidence/2026-10-06-m1-batch2/T-027/RESULTS.md)、[T-029](evidence/2026-10-07-m1-batch3/T-029/RESULTS.md)。两者自 2026-10-07 起冻结为参考实现。
- 这些证据只对各自的运行时成立；新门禁须重新证明。

## 事实、未知与最小验证

| 项目 | 状态 | 依据或最小验证 | 负责人 |
| --- | --- | --- | --- |
| Synara 的许可、版本与技术栈 | observed | MIT；v1.0.1-beta.2；Bun + Turbo、Electron、React 19、xterm 6、node-pty | — |
| Synara 驱动 agent 的方式 | observed | Codex app-server、Claude Agent SDK、ACP、OpenCode SDK | — |
| Synara 已有的组织能力 | observed | split views、Local/Worktree、agent 间消息、thread goals、Automations | — |
| 一个任务包含多个 agent 的分组 | unknown | 读源码并在 fork 中实测；缺少时在 fork 中补模块 | spec session |
| 门禁接入点：会话生命周期、submit 信号、外部入口 | unknown | 读 `agentGateway`、Codex app-server 管理与事件流；设计门禁入口 | spec session |
| Bun 与 Electron 缓存放外置盘的方式、内置盘占用与耗时 | unknown | 首个任务实测 | build session |
| Enchanted 与 Synara 已有功能的重叠 | unknown | M1 之后调研 | 后续 session |

## 治理与规范

项目地图是流程索引，`CONTEXT.md` 是术语表，本文件是本阶段的 canonical artifact，dated 研究稿和评估记录是证据记录，`.grilling/` 只保存决策会话 ledger。每次 session 先运行 `project_map.py status`，读取地图、相关 ticket 和本文；一次只做一个 build ticket。

按阶段使用本机规范 skill：`project-map`、`reality-first-engineering`、`evidence-first-testing`、`design-integrity-review`、`behavioral-acceptance-review`、`document-writing`、`frontend-less-ai-tone` 与 `same-visual-family`；`grilling` 只用于决策和交接，不在会话内实现。

## 风险等级与交接

这是影响代码、Git 工作区、进程和 agent 权限的 consequential 项目，采用人工门控。本 intent 允许在批准范围内开始 Design / Spec 和后续切片，不授权把未知状态写成成功。

下一步：在 project-map 中写基于 Synara 的 M1 spec（fork 与同步流程、构建缓存、层级模型、门禁 package 的边界与入口、移植场景），再切 tracer-bullet build ticket。
