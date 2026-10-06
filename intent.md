# Intent：Herdr 多 Agent 协作确定性运行层

状态：accepted（2026-10-05）  
负责人：用户  
阶段：Plan / intent  
规范地图：[`.project-map/MAP.md`](.project-map/MAP.md)  
初始研究记录：[herdr-a2a-research-and-plan-2026-10-06.md](herdr-a2a-research-and-plan-2026-10-06.md)

## 用户目标

> 让协作不依赖模型持续记住操作手册。

项目保留 Herdr 和现有 coding CLI 的使用方式，把关键协作事实和门禁放到可持久化、可校验、可恢复的程序与项目规范中。模型可以忘记 skill、漏掉提醒或在上下文压缩后丢失细节；系统仍应拒绝不合法状态，留下证据，并在无法核对时暂停。

## 要解决的问题

当前的 Herdr 多 Agent coding 工作流仍可能把协作约定交给模型记忆。模型或会话出现遗漏时，可能接受过期或未验收结果、重复认领任务、把终端的 `idle`/`done` 当成业务完成，或让主控承担大量转述、追踪和补救工作。现有讨论稿已经整理了这些风险，但尚未形成被项目持续使用的 intent 和治理规则。

首个实验聚焦一个可观察的边界：**旧会话或未验收结果不得被接受为有效交付**。其他冲突类型可以记录为次级观察，不在首轮把所有问题混成一个成功标准。

## 期望结果

形成一个围绕 Herdr 的受管理协作闭环，具备以下行为：

- 任务、执行尝试、所有权、规格版本、代码候选和验收结果可持久记录；
- Codex worker 在任务范围内实现，主控可在批准范围内通过 Herdr 分派和及时回收 worker；
- claim、submit、acceptance 和 integration 门禁由外部状态与程序规则校验，不以模型自报或终端空闲替代；
- 模型忘记 skill 或跳过步骤时，非法状态被拒绝，原因和外部证据被保留，系统进入可恢复暂停；
- 独立 monitor 只读观察，记录事件并标记异常，不认领、提交、集成或宣布成功；
- 第一轮运行只作为探索性基线和失败证据，不据此宣称可靠性已经改善。

## 首轮范围

- 受 Herdr 管理的当前多 Agent coding 工作流；
- Codex 作为首个 CLI 实验对象；
- 先定义跨 CLI 的 capability contract，第二个 CLI 在 Codex 实验后再验证；
- 主控、worker、monitor 的角色边界和运行记录；
- 使用 project-map、CONTEXT、intent 和项目级 AGENTS.md 固化项目规范；
- 以旧会话或未验收结果被接受为首要故障夹具。

是否修改 Herdr 核心不预先固定。只有规模或可复现的公开接口缺口证明适配层不足时，才进入内核修改决策。

## 不在本 intent 内

- 通用 A2A 平台、分布式调度、多机部署或所有 CLI 的同等适配保证；
- 第二个 CLI 的首轮互操作验证；
- 自动解决复杂语义冲突、自动批准权限或把未知副作用标成成功；
- 生产发布、部署和不可逆外部操作；
- 改写 dated 初始研究记录。

## 角色、模型与权限

| 角色 | 当前配置 | 权限边界 |
| --- | --- | --- |
| 主控 controller | `gpt-6-astra`，max reasoning | 在已批准范围内理解目标、分派/回收 worker、汇总证据；不得越过门禁或替未知结果判成功 |
| 执行 worker | `gpt-6.1-sol`，xhigh reasoning，Fast service tier | 只在分配的 task/attempt 范围内实现或分析 |
| 监控 monitor | `gpt-6.1-sol`，high reasoning | 只读记录和报警；不得 claim、submit、integration 或宣布成功 |
| 用户 | 人工负责人 | 决定目标/范围、验收与权限变化、不可逆外部效果、方向性取舍和发布 |

主控可以自主完成日常分派、状态检查、策略内重试和回收。遇到下列任一条件必须停下并问用户：

- 目标或范围发生变化；
- 验收条件、权限或允许的外部操作需要变化；
- 将产生不可逆外部副作用；
- 外部状态无法核对或彼此冲突；
- 设计取舍会改变本 intent 的目的地；
- 预算或风险越界。

## 可观察成功条件

首轮实验至少留下一份追加式运行记录，包含模型、CLI、Herdr 和规范版本，以及 task、attempt、message、claim、submit、验收、integration、人工介入和失败事件。独立验收必须针对明确代码版本和输入运行。

首轮故障注入或真实复现中，旧 session、旧 fence、过期规格或未通过验收的候选必须被拒绝，并留下可诊断的暂停状态；“测试通过”的自然语言或终端 `idle`/`done` 不能单独使交付成功。

本轮结果只能回答“事实是否被记录、非法状态是否被拒绝、失败是否可恢复”。要声称相对基线降低主控负担或提高可靠性，必须另做独立对照实验。

## 事实、未知与最小验证

| 项目 | 状态 | 依据或最小验证 | 负责人 |
| --- | --- | --- | --- |
| Herdr 终端、pane、进程和生命周期能力 | observed / 部分复核 | 初始研究记录；设计前按实际版本复查入口和能力 | Design session |
| 当前用户的首个代表性 coding task 和 Herdr 入口 | unknown | 选一个能触发旧结果/未验收结果风险的中等难度任务，记录真实入口和版本 | 用户 + controller |
| 独立验收套件与 test seam | unknown | 在 Spec 阶段先确定真实入口和独立 oracle；不能只用模型自报 | Design session |
| 是否需要修改 Herdr 核心 | unknown | 先用适配层/公开接口做最小探针；只有复现接口缺口或规模瓶颈才升级 | controller，重大取舍由用户决定 |
| 第二 CLI | out of scope for first run | Codex 首轮完成后，再按 capability contract 选择验证对象 | 后续 session |
| 数值预算 | unknown | Spec 阶段补齐；触发预算/风险越界即按停止边界升级 | 用户 + Design session |

## 治理与规范

项目地图是流程索引，`CONTEXT.md` 是术语表，`intent.md` 是本阶段的 canonical artifact，dated 研究稿是初始证据记录，`.grilling/` 只保存决策会话 ledger。每次 session 先运行 `project_map.py status`，读取地图、相关 ticket 和本文；一次只工作一个 build ticket。

按阶段使用本机规范 skill：`project-map` 管理地图、ticket、spec 和 tracer-bullet slice；`reality-first-engineering` 在架构或大范围实现前处理事实和方向门；`evidence-first-testing` 为行为变化保留失败证据和反事实；`design-integrity-review` 在结构风险变更完成时检查绕过根因的补丁；`behavioral-acceptance-review` 审查独立行为证据；`document-writing` 负责项目文档的语义和编码保真；`grilling` 只用于决策和交接，不在会话内实现。

## 风险等级与交接

这是一个会影响代码、Git 工作区、进程和 Agent 权限的 consequential 项目，采用人工门控边界。当前 intent 允许在已批准范围内开始 Design / Spec 和后续切片；它不替代具体验收套件，也不授权把未知状态写成成功。

下一步由 project-map 的下一阶段生成 `specs/<slug>.md`，确定首个真实入口、验收 seam、数据边界和 tracer-bullet build tickets。Grilling 会话在本文件和项目治理文档完成后结束；worker 的启动和实现应发生在单独的 build-ticket session。
