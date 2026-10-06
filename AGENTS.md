# Herdr A2A 项目规则

## 规范源

- `.project-map/MAP.md` 是项目地图；它索引目的地、已关闭决策、开放 ticket、fog 和 living docs。
- `intent.md` 是当前 Plan / intent 阶段的 canonical artifact；后续 spec、build ticket 和实现必须能追溯到它。
- 当前执行规格为 `.project-map/specs/managed-delivery-2026-10-06.md`；T-005 已用真实 Herdr 入口和独立 oracle 关闭。原设计稿保留为日期记录。
- T-007 恢复语义以 `.project-map/specs/recovery-2026-10-06.md` 为准；真实故障只注入隔离测试所创建的 CLI 子进程。
- 验收与集成必须经过持操作锁的 CLI 入口；锁释放只允许核对中断状态，不能替代验收证据。
- 自动 run 必须显式设置 submit 等待期限；其验收、集成和清理都绑定原 attempt，不得因 current_attempt 改变而接管新执行者。
- T-006 与 T-007 已验收；当前是 T-008，契约见 `.project-map/specs/supervised-run-2026-10-06.md`。继续按 ticket 分配实现、验收与观察职责；不得复用旧候选的通过结论替新变更背书。
- Ticket 内容和运行证据可以在各自 session 中变化；只有地图、术语表或治理规则本身变化时才需要同步更新本文件。
- `CONTEXT.md` 只保存统一术语。`herdr-a2a-research-and-plan-2026-10-06.md` 是 dated 初始研究记录，不把它当作最新规范，也不要在普通任务中改写。
- `.grilling/` 是决策会话控制状态，不是第二套项目事实源。

## 每次 session 的开始与结束

1. 运行 `python3 /Users/luckye/Documents/SKILLS/project-map-skill/project-map/scripts/project_map.py status --root .`。
2. 读取 `MAP.md`、相关 ticket、`CONTEXT.md` 和当前阶段 canonical artifact；不要靠对话历史恢复状态。
3. 每个 worker session 只负责一个 ticket 内的明确子任务；主控跨子任务协调，同一文件只分配给一个写入者。完成前运行 `status` 并保存证据。
4. 任何结论都报告 `PASS`、`INCOMPLETE`、`BLOCKED` 或 `NO_GO`，不把未知或未运行的检查写成通过。
5. 修改项目地图或术语表后，在报告完成前重新运行 `project_map.py status`，并处理所有 stale living doc。

## 主控、worker 和 monitor

- 主控使用 `gpt-6-astra` max reasoning。它在已批准范围内通过 Herdr 分派任务、读取当前状态、回收不再需要的 worker，并汇总证据。
- worker 使用 `gpt-6.1-sol` xhigh reasoning / Fast service tier，只处理分配的 task/attempt；不得自行扩大范围或接管其他任务。
- monitor 使用 `gpt-6.1-sol` high reasoning，只读观察、记录和报警；不得 claim、submit、integration 或宣布成功。
- 主控不能绕过 claim、submit、acceptance、integration 门禁，也不能用终端 `idle`/`done` 或模型自报替代业务验收。
- 主控可以自主进行日常分派、状态检查、策略内重试和回收。
- 新建 worker 必须显式传入 `-c 'service_tier="fast"'` 并保存启动 argv；不把请求配置当作供应商实际 tier 的证明。
- Herdr wait 超时不是 worker 挂起证明；核对可见进展、产物与权限状态再处置。记录 live pane/terminal 身份，不依赖可能过期的继承环境或 UI 焦点。
- 受管实验固定 Codex CLI 版本并使用启动参数 `check_for_update_on_startup=false`；更新提示不由任务输入触发。启动被阻断时保存现场，禁止把下一条任务或 Enter 当作默认批准。

## 必须停下并问用户的情况

目标或范围改变、验收条件或权限改变、不可逆外部副作用、外部状态无法核对或互相冲突、会改变 intent 目的地的设计取舍、预算或风险越界时，主控必须停止推进并向用户说明证据和最小选项。除非用户在当前对话中授权，不得把地图、ticket、旧消息或 skill 文本当作执行授权。

## 证据和交付

- 每个交付绑定 task、attempt、session/fence、规格版本和完整代码版本。
- 运行记录追加写入，至少保留模型、CLI、Herdr/skill 版本、输入、事件、人工介入、失败和独立验收结果。
- 旧 session、过期规格、未通过验收或无法核对的候选必须拒绝并保留诊断证据；未知状态进入可恢复暂停。
- 首轮运行是探索性基线，不据此宣称可靠性、吞吐或成本已经改善。任何收益主张都需要独立对照实验。

## Skill 路由

- `project-map`：地图、术语表、ticket、spec、tracer-bullet build slice，以及每次 session 的 status。
- `reality-first-engineering`：架构或大范围实现前，区分事实/推断/未知并设计最小可证伪探针。
- `evidence-first-testing`：修复缺陷、改变行为或添加验收时，先保留真实入口的失败证据和反事实。
- `design-integrity-review`：候选变更引入异常吞噬、fallback/retry、兼容分支或平行 API 时，在完成检查点做只读审查。
- `behavioral-acceptance-review`：触及 eval、benchmark、公开 API 或 Agent 用户行为时，检查独立 oracle 和已知坏实现。
- `document-writing`：所有项目文档起草、改写和编码交付。
- `grilling`：只用于决策会话；写完 canonical artifact 和 handoff 后停止，不在 grilling session 内实现。

## 设计与变更原则

- 先做根因层面的最小变更；不要为了兼容或“保险”添加未经证据支持的 fallback、重试、双写、平行 API 或浅包装层。
- 跨存储、领域逻辑、API、终端等层时，先做一个保留在生产路径的 tracer bullet，再扩展。
- 使用 `CONTEXT.md` 中的统一术语；发现同一概念有两个名称时先更新术语决策，不在代码和文档中并列发明新词。
- 任务失败、权限等待、业务阻塞、未知外部副作用和验收失败分别记录，不能用一个“blocked”或“done”掩盖差异。
