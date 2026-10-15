# Intent：a2a 多 Agent 编排与工作台（第三阶段）

状态：accepted（2026-10-10）  
负责人：用户  
阶段：Plan / intent（第三阶段，2026-10-10 修订）  
规范地图：[`.project-map/MAP.md`](.project-map/MAP.md)  
决策记录：[`.grilling/native-cli-orchestration.md`](.grilling/native-cli-orchestration.md)（本次修订，决定 ticket T-069～T-072）；上一版见 [`.grilling/synara-fork.md`](.grilling/synara-fork.md)、[`.grilling/controller-split-user-input.md`](.grilling/controller-split-user-input.md)  
执行规格：[native-cli-orchestration](.project-map/specs/native-cli-orchestration-2026-10-10.md)  
初始研究记录：[herdr-a2a-research-and-plan-2026-10-06.md](herdr-a2a-research-and-plan-2026-10-06.md)

## 用户目标

> 让协作不依赖模型持续记住操作手册。

首轮为这个目标建成了门禁层；第二阶段基于 Synara 的 fork 做工作台。2026-10-10 用户改了方向：

> "我觉得不用 Synara的统一网关，只用 synara 这种前端样式框架就行，里面具体的 cli 还是看每家自己的能力，我们只做编排，像 herdr 这样。"
>
> "5.文章里好的思路我们借鉴，我没细看，但里面也有权限管理这些吧，和我们现在做的结合一下。"

借鉴的文章是立行的《将军赶路不追小兔：多 Agent 调度体系的架构与实践》，用户点名要的是任务卡与提交追溯、"提示词加脚本"、并行 worktree、质量保障、写审分开、复盘与指标。

界面的层级要求不变：

> "反正就是要项目 任务 agent 这样的层级展开，一个项目里可以有多个任务窗口，一个任务窗口里可以有多个agent"

对外观的要求仍然有效：现代界面，参照 Codex 与 Synara，不要浏览器式的旧界面。

## 要解决的问题

- 接 Synara 的统一层，几乎每张票都要改它的上游（provider 适配器、网关、投影），见 T-055、T-058、T-061、T-064、T-066、T-068。
- 合并在门禁之外：worker 交付后由执行主控手工合进工作分支，冲突也由它手工解决。
- 提交看不出是谁、用什么模型和配置干的。
- 没有验收打分、复盘与指标，"什么活派给谁"只能凭印象，系统自进化和以后的 Enchanted 没有数据可用。
- 很多规程只写在提示词里，长对话里容易丢。

## 方案

- **原生 CLI，a2a 只做编排**：各家 CLI 以交互终端运行，不用无头模式；终端由 a2a 自己托管（xterm.js、node-pty，窗格里跑用户的 zsh）。第一版只支持 Claude Code 与 Codex。
- **a2a 自己的工作台**：本仓库里的轻量 Electron 应用，借用 Synara 的前端组件与样式（MIT）；fork 只作组件来源，不再跟进上游。编排后台常驻，界面只是连上去看。
- **门禁**：从 fork 抽进编排后台，仍是唯一门禁入口；每次交付走同一串检查（身份与版本、路径边界、完成条件、红态、规则式检查、独立审查、提交尾注），全过才集成到项目的工作分支。
- **提示词管判断，脚本管事实**：能机械核对的由脚本和门禁保证，角色卡只写"用哪个命令"；要判断的交给提示词和人；不做策略引擎。
- **任务卡**：受管任务的结构化合同，写明目标、非目标、修改边界、完成条件、任务类型与复杂度，由命令生成和校验。
- **写审分开**：审查是为每次交付新开的只读会话，与写代码的会话分开。
- **并行 worktree**：统一命名，干净的自动清理，冲突回给 worker 处理，程序不替用户取舍。
- **权限四层**：角色卡；任务卡路径加门禁检查；每会话的 CLI 启动参数；收件箱命令行限定谁写哪种条目。都在工作台内，不改各家 CLI 的全局配置。
- **追溯与自进化的数据**：提交带尾注；每个 attempt 结束打一次分；原始事件全记、指标现算；复盘手动或定期跑，可选 CLI、模型、思考强度。
- **已定的三项功能换载体**：用户输入记录、两层主控（构思主控与执行主控）、问题面板搬进新工作台；面板也收构思主控的提问。

设计见 [spec](.project-map/specs/native-cli-orchestration-2026-10-10.md)，决定见 T-069～T-072。

## 期望结果：切换

用户 2026-10-09 定的切换标准："肯定要把我提的功能至少都做的能用了，我才能到 Synara 里用啊"。第三阶段的切换条件（T-069）：

1. 用户输入记录、两层主控、问题面板在新工作台里能用；
2. 任务卡、门禁检查串与独立审查、worktree 命名清理与冲突流程、提交尾注、面板收主控提问、验收打分、复盘、原始事件采集与四个指标视图都能用；
3. 用户试用时至少走一遍：一张真实任务卡从派发跑到集成（含独立审查和打分）、在面板上答一次主控的提问、手动跑一次复盘、看一次模型使用分类；
4. 用户说"可用"。

之后日常派发从 Herdr 挪到新工作台，Herdr 期的收件箱文件与脚本退役，不双写。在此之前，日常派发仍经 Herdr；Herdr 期先用任务卡模板、提交尾注与验收打分，从现在起攒数据。

## 范围

不在本阶段：

- 额度感知调度与额度水位监控；token、成本、缓存命中率监控（用户已用 TokenTracker）；
- 无头模式、改动量上限、前端录屏、风险分档；
- 多审查者交叉、顾问与影子审查、规则式审查工具（OCR）、定期架构扫描与安全扫描；
- Claude Code、Codex 以外的 CLI（以后按需加）；Windows 与 Linux；
- Enchanted 的功能（门禁进入工作台之后再并入）。

不在本 intent 内：

- 从零自建 GPUI 界面，以及基于 Zed 二次开发；
- 通用 A2A 平台、分布式调度、多机部署；
- 自动解决复杂语义冲突、自动批准权限，或把未知副作用标成成功；
- a2a 系统修改用户的 Herdr server 与 `~/.claude`、`~/.codex` 的全局配置；
- 生产发布、push 和其他不可逆外部操作；
- 改写 dated 初始研究记录。

## 约束

- **门禁契约核心不变**：[受管交付](.project-map/specs/managed-delivery-2026-10-06.md)、[恢复](.project-map/specs/recovery-2026-10-06.md)、[自动运行](.project-map/specs/supervised-run-2026-10-06.md) 中的锁、fence、CAS、attempt 绑定与中断恢复语义不变。经用户同意的改动见 T-070：路径检查；验收扩成检查串；清理干净的 worktree；核对提交尾注；缺打分拒收；集成目标改为项目工作分支。
- **唯一门禁入口**：认领、交付、验收、集成和回收只经它，保持操作锁语义；界面不另做一套门禁。抽出完成后，fork 里的门禁不再作入口，不保留两套路径。在受管 worker 会话中直接输入，记为人工介入。
- **重新证明**：旧实现的通过结论不替新实现背书；门禁换位置后，移植场景须重新取得红态、绿态与反例。
- **构建**：依赖缓存、Electron 下载等放外置盘 `/Volumes/WD-Elements`，外置盘未挂载时构建直接报错，不回退到内置盘；源码 checkout 与工作台数据目录放内置盘。
- **许可**：永不闭源；自用并开源。搬用 Synara 的代码保留其 MIT 版权声明；允许直接复用 GPL 代码，并入 GPL 代码后整体以 GPL-3.0 开源。
- **平台**：只面向 macOS。
- **不改用户的环境**：不修改或重启用户正在用的 Herdr server；a2a 系统不写各家 CLI 的全局配置，权限与钩子只经每会话的启动参数传入。

## 角色、模型与权限

| 角色 | 当前配置 | 权限边界 |
| --- | --- | --- |
| 构思主控 ideation controller | Claude Code（用户 2026-10-09 定为上层主控） | 接收想法、澄清、写决定/spec/ticket、标就绪、向执行主控分发任务、转述完成报告；不直接派发、验收、集成、回收 worker |
| 执行主控 executor controller | Claude Code（用户 2026-10-06 指定，原称主控） | 在已批准范围内监督就绪 ticket 的执行：派发和回收 worker、验收时打分、汇总证据；不得越过门禁，也不得替未知结果判成功 |
| 执行 worker | Codex，`gpt-6.1-sol`，xhigh reasoning，普通速度（`service_tier="default"`，不用 Fast；用户 2026-10-13 决定） | 只在分配的任务卡与 attempt 范围内实现或分析 |
| 审查 reviewer | Codex，默认与 worker 同一个模型，每次交付新开的干净会话 | 只读审查，结论绑定候选提交号；不 submit、不集成 |
| 监控 monitor | Codex，`gpt-6.1-sol`，high reasoning | 只读记录和报警；不得 claim、submit、集成或宣布成功 |
| 复盘 | 默认 Claude Code、Opus 5.5、medium，每次可选 | 只读代码和数据，只写自己的报告；改进建议经用户批准才落地 |
| 用户 | 人工负责人 | 决定目标与范围、验收与权限变化、不可逆外部效果、方向性取舍和发布 |

执行主控可以自主完成日常分派、状态检查、策略内重试和回收，并在已批准范围内自建缺陷级 ticket。遇到下列任一情况必须停下并问用户（执行主控经构思主控向用户说明）：

- 目标或范围发生变化；
- 验收条件、权限或允许的外部操作需要变化；
- 将产生不可逆的外部副作用；
- 外部状态无法核对或彼此冲突；
- 设计取舍会改变本 intent 的目的地；
- 预算或风险越界。

## 可观察成功条件

切换时至少留下：

- 新工作台的构建与运行记录：提交、依赖与缓存位置、内置盘占用；
- 门禁在新位置的移植场景（交付 8 项、恢复 9 项、编排 18 项）的通过记录、红态与反例；
- 一次真实闭环的追加式记录：任务卡、启动记录（CLI、模型、强度）、带尾注的提交、门禁逐项结果、独立审查结论、打分、工作分支的引用读回；
- 面板上主控提问与问题上报的收发记录；
- 一份复盘报告，以及模型使用分类视图的截图；外观由用户判断；
- 用户试用后说"可用"的原话。

首轮的原则继续适用：模型自报或会话"完成"不能单独使交付成功；任何收益主张都需要独立对照实验。

## 前两阶段的成果

- T-006～T-008 在已安装的 Herdr 上通过：[受管交付](evidence/2026-10-06-managed-01/RESULTS.md)、[中断恢复](evidence/2026-10-06-recovery-01/RESULTS.md)、[自动运行](evidence/2026-10-06-run-01/RESULTS.md)。
- 第二阶段在 fork 中原生实现了门禁（T-031、T-036～T-040），2026-10-09 第一次经工作台门禁的真实派发跑通（T-046）；三项功能在本仓库有 Herdr 期脚本（T-053、T-054），在 fork 中有部分实现（T-055～T-065）。
- 这些证据只对各自的运行时和代码版本成立；门禁换位置后须重新证明。

## 事实、未知与最小验证

| 项目 | 状态 | 依据或最小验证 | 负责人 |
| --- | --- | --- | --- |
| Synara 的许可与前端栈 | observed | MIT；React 19、Vite、Tailwind 4、xterm.js；Electron；服务端有 node-pty 终端 | — |
| 门禁抽出要替换的依赖 | observed | `@synara/contracts`、`@synara/shared/processRuntime` 两处 | 第一个切片 |
| 每会话注入 git 钩子、追加尾注 | measured | 环境变量设 `core.hooksPath`，不写配置文件；`--no-verify` 照样追加 | — |
| 两家 CLI 的启动参数 | observed | Claude `--session-id`、`--model`、`--effort`、`--settings`；Codex `-m`、`-c`、沙箱与审批参数 | — |
| Codex 的"等确认"结构化信号 | unknown | 第一个切片第 0 步实测；拿不到就显示"未知"，核心流程离不开时停下报告 | 执行主控 |
| 往两家窗格注入文字的稳定性 | unknown | 第一个切片第 0 步实测；不稳定就停下报告 | 执行主控 |
| 主控直接提交 `main` 引起的重新验收频率 | unknown | 集成紧跟验收；连续重新验收设上限，超限上报 | spec、执行主控 |

## 治理与规范

项目地图是流程索引，`CONTEXT.md` 是术语表，本文件是本阶段的 canonical artifact，dated 研究稿和评估记录是证据记录，`.grilling/` 只保存决策会话 ledger。每次 session 先运行 `project_map.py status`，读取地图、相关 ticket 和本文；一次只做一个 build ticket。

按阶段使用本机规范 skill：`project-map`、`reality-first-engineering`、`evidence-first-testing`、`design-integrity-review`、`behavioral-acceptance-review`、`document-writing`、`frontend-less-ai-tone` 与 `same-visual-family`；`grilling` 只用于决策和交接，不在会话内实现。

## 风险等级与交接

这是影响代码、Git 工作区、进程和 agent 权限的 consequential 项目，采用人工门控。本 intent 允许在批准范围内切片和实现，不授权把未知状态写成成功。

下一步：构思主控按 [spec 第 12 节](.project-map/specs/native-cli-orchestration-2026-10-10.md#12-切片建议) 切第一批票（建议 S0 Herdr 期三样、S1 tracer bullet），标就绪后交执行主控派发。用户 2026-10-10 的话："确认，写完文档后，你这边就不用了，全权交给构思主控去安排执行主控安排子 agent 去做。"
