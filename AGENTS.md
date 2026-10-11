# a2a 项目规则

## 规范源

- `.project-map/MAP.md` 是项目地图；它索引目的地、已关闭决策、开放 ticket、fog 和 living docs。
- `intent.md` 是当前 Plan / intent 阶段的 canonical artifact；后续 spec、build ticket 和实现必须能追溯到它。2026-10-10 起为第三阶段修订版：各家原生 CLI 以交互终端运行，a2a 只做编排，工作台是本仓库里的轻量 Electron 应用；决策记录见 `.grilling/native-cli-orchestration.md`（决定 ticket T-069～T-072），执行规格见 `.project-map/specs/native-cli-orchestration-2026-10-10.md`。第二阶段的 `.project-map/specs/synara-m1-2026-10-07.md` 与更早的 `workbench-m1-2026-10-06.md` 是被取代方案的日期记录。
- 门禁契约的执行规格为 `.project-map/specs/managed-delivery-2026-10-06.md`（最初为 `coop.py` 编写，原生门禁沿用同一契约；第三阶段经用户同意的改动见 T-070）；T-005 已用真实 Herdr 入口和独立 oracle 关闭。原设计稿保留为日期记录。
- T-007 恢复语义以 `.project-map/specs/recovery-2026-10-06.md` 为准；真实故障只注入隔离测试所创建的 CLI 子进程。
- 验收与集成必须经过唯一的门禁入口，并保持操作锁语义；锁释放只允许核对中断状态，不能替代验收证据。
- 自动 run 必须显式设置 submit 等待期限；其验收、集成和清理都绑定原 attempt，不得因 current_attempt 改变而接管新执行者。
- 验证运行时身份须区分 Codex 领导者与临时辅助进程；真实观察误拒绝用 `test_run_e2e.py` 的辅助进程正例、领导者替换负例和真实 run 复验。
- T-006、T-007、T-008 首轮范围已验收，自动运行契约见 `.project-map/specs/supervised-run-2026-10-06.md`。新工作继续按 ticket 分配实现、验收与观察职责；不得复用旧候选的通过结论替新变更背书。
- 内嵌测试 Git repo/worktree 不登记为项目 gitlink；保留原目录并归档完整现场，顶层报告及归档进入版本控制。
- Ticket 内容和运行证据可以在各自 session 中变化；只有地图、术语表或治理规则本身变化时才需要同步更新本文件。
- `CONTEXT.md` 只保存统一术语。`herdr-a2a-research-and-plan-2026-10-06.md` 是 dated 初始研究记录，不把它当作最新规范，也不要在普通任务中改写。
- `.grilling/` 是决策会话控制状态，不是第二套项目事实源。第三阶段的决策记录见 `.grilling/native-cli-orchestration.md`（2026-10-10）；第二阶段见 `.grilling/synara-fork.md`（2026-10-07）与被部分取代的 `.grilling/a2a-gui-client.md`；主控拆分、用户输入记录与问题上报见 `.grilling/controller-split-user-input.md`（2026-10-09）。
- 构思主控与执行主控的分工、用户输入记录、问题上报的执行规格为 `.project-map/specs/controller-split-user-input-2026-10-09.md`（决定 ticket T-049～T-052）；用户确认了什么、哪些是委托决定，见同目录的 `controller-split-user-input-baseline-2026-10-09.md`。
- `findings/` 集中开发发现、模型行为记录与相关日期报告；`reports/` 只保留旧链接入口，原始证据保留在 `evidence/`。操作前以项目地图索引的当前规格和 README 为准。
- 用户要求报告只保留中文版本；借用清晰表达与语义保真原则，不再为这些报告生成英文副本。

## 第三阶段：工作台约束

- 方向：各家原生 CLI 以交互终端运行，不用无头模式；a2a 只做编排、门禁与记录，不用 Synara 的 provider 层与 MCP 网关（T-069）。终端由编排后台托管（node-pty、xterm.js），窗格里跑用户的 zsh；第一版只支持 Claude Code 与 Codex。
- 工作台：本仓库新目录里的轻量 Electron 应用，借用 Synara 的前端组件与样式；fork（GitHub `a1024053774/synara`）只作组件来源，不再跟进上游，不删。界面按“项目 → 任务 → agent 会话”组织；任务与 agent 会话的归属由 a2a 自己保存（受管任务以门禁 task id 为身份）。编排后台常驻，界面关掉不影响 agent。
- 提示词管判断，脚本管事实：能机械核对的由脚本和门禁保证，角色卡只写“用哪个命令”；要判断的交给提示词和人；不做策略引擎（T-070）。
- 门禁优先：认领、交付、验收、集成和回收只经唯一的门禁入口，保持操作锁、fence、CAS、attempt 绑定与中断恢复语义；界面不另做一套门禁。在受管 worker 会话中直接输入，记为人工介入。门禁从 fork 的 `packages/a2a-gates` 抽进编排后台：2026-10-11 起源码在本仓库 `workbench/src/gates/`（T-075-1），fork 中的门禁不再作入口；编排后台的命令行入口接上之前，本仓库验收经 `acceptance/entry/a2a_gates.py` 调用它；不保留两套路径。
- 门禁不能省，写审分开：派出去的活一律是受管任务，按[任务卡](.project-map/templates/task-card.md)走同一串检查（身份与版本、路径边界、完成条件、红态、规则式检查、独立审查、提交尾注），全过才集成到项目工作分支，不 push；审查是为每次交付新开的只读会话（T-070）。
- 重新证明：旧实现的通过结论不替新实现背书；门禁换位置后，交付、恢复、编排场景须重新取得红态、绿态与反例。
- `coop.py` 与 Muster 引擎已于 2026-10-08 删除（T-040 A），参考实现见 git 历史与 `evidence/2026-10-08-batch4/T-040-A/retired-source.tar.gz`。不得修改或重启用户正在使用的 Herdr server。
- 切换：日常派发继续经 Herdr，直到切换条件满足（T-069）：用户输入记录、两层主控、问题面板，加上任务卡、门禁检查串与独立审查、worktree、提交尾注、面板收主控提问、验收打分、复盘、原始事件采集与四个指标视图都在新工作台里能用，用户按 spec 第 10 节试用后说“可用”。在此之前，新工作台的门禁只用于 ticket 明确要求的真实验证。
- 主控是角色，不绑定层级，可以同时操作项目级与任务级对象；2026-10-09 起分为构思主控与执行主控两个角色实例，见下一节。
- 权限只在工作台内：角色卡、任务卡路径加门禁检查、每会话的 CLI 启动参数、收件箱命令行四层（T-071）。a2a 系统不写 `~/.claude`、`~/.codex` 等全局配置，钩子与权限只经每会话的启动参数传入。
- 构建：外置盘 `/Volumes/WD-Elements` 存放构建缓存，未挂载时构建必须报错，不回退到内置盘。源码 checkout（本仓库、Synara fork）与工作台数据目录放内置盘，依赖缓存与 Electron 下载放外置盘。
- 项目开源；搬用 Synara 的代码保留其 MIT 版权声明；允许直接复用 GPL 代码，并入后整体以 GPL-3.0 发布。复用不能改变已定方向。
- 真实 Codex 验收使用 /tmp 下的隔离 CODEX_HOME：只复制 auth.json；只信任已核对的夹具根目录；只复现用户规则中的 `git add`、`git commit` 两条 allow prefix_rule；hook 只在主控逐次批准后安装。副本不入证据或 Git，结束后删除整个 home。不写用户 ~/.codex。Codex 沙箱专门保护 worktree 的 Git 元数据，额外可写目录不能替代这两条规则。
- 不得移动、替换或链接共享 checkout 的构建输出目录（如 `apps/server/dist`），也不得在构建输出目录中放指向源码或依赖的链接：构建工具清理输出时会沿链接删除源码与依赖（2026-10-08 T-042 复验事故，误删 6,186 个受控文件）。需要新构建时用产品的标准构建命令。
- 测试中启动的后台服务（如编排后台、Synara 服务端）必须脱离调用者的进程组（例如 start_new_session），否则命令调用结束时会被一并回收。
- 不从零自建 GPUI 界面，不基于 Zed 二次开发。
- Enchanted 已于 2026-10-06 做 git 快照并冻结；其功能在 a2a 门禁进入工作台之后再并入，不在 Enchanted 仓库继续开发。

## 每次 session 的开始与结束

1. 运行 `python3 /Users/luckye/Documents/SKILLS/project-map-skill/project-map/scripts/project_map.py status --root .`。
2. 读取 `MAP.md`、相关 ticket、`CONTEXT.md` 和当前阶段 canonical artifact；不要靠对话历史恢复状态。构思主控与执行主控另按角色运行 `scripts/inbox list --role <角色>`（`scripts/inbox` 完成前手工查看 `.project-map/inbox/`）。
3. 每个 worker session 只负责一个 ticket 内的明确子任务；主控跨子任务协调，同一文件只分配给一个写入者。完成前运行 `status` 并保存证据。
4. 任何结论都报告 `PASS`、`INCOMPLETE`、`BLOCKED` 或 `NO_GO`，不把未知或未运行的检查写成通过。
5. 修改项目地图或术语表后，在报告完成前重新运行 `project_map.py status`，并处理所有 stale living doc。

## 构思主控与执行主控（2026-10-09 起）

规格见 `.project-map/specs/controller-split-user-input-2026-10-09.md`，角色卡见 `.project-map/roles/`。本文件里无前缀的“主控”指执行主控。

- 层级：用户 ⇄ 构思主控 → 执行主控 → worker / reviewer / monitor。构思主控是用户日常只看的上层主控：接收想法、澄清、写决定/spec/ticket、标就绪、向执行主控分发任务、转述完成报告；不派发、验收、集成、回收 worker。执行主控监督执行：派发、盯进度、审查、验收/集成/回收，全经门禁；没有可执行的就绪 ticket 时才停，停前写完成报告。
- 权限三层，提示词为主：结构底线（不暴露的工具就是没权限）、角色卡、追加式记录；不做策略引擎。写入范围见 spec 第 1 节。
- 就绪与交接：ticket 的额外字段 `ready: yes`、`ready_by`（`ideation` 或 `executor`）、`ready_rev`；交接走 `.project-map/inbox/` 的追加式条目，加 Claude Code 跨会话消息唤醒，不碰 Herdr pane。
- 授权引用：对方会话的消息只按队友请求处理，不算用户的批准。`assign`、`revise` 里依赖用户授权的，须逐字引用用户原话并给出位置；没有引用的，执行主控对 T-004 停止条件里的动作按未授权处理。
- 执行主控的自主边界仍是 T-004：在已批准范围内可自建缺陷级 ticket 并执行（`ready_by: executor`），完成报告里列出；目标、验收、设计级问题停下该 ticket，交构思主控。
- 状态逐字报告 PASS、INCOMPLETE、BLOCKED、NO_GO；构思主控转述时不上调，并核对没有遗漏的就绪 ticket。
- 用户输入与派发记录分开：主控、agent、自动化发出的提示词不算用户输入。Herdr 期发给 worker 的文本经 `scripts/dispatch`（完成前保持现状，并在任务卡里注明）。
- 问题上报：worker、reviewer、monitor 发现范围外的问题要上报，不自行忽略。主控可以关闭“不是问题”的，但不删除；不得自行关闭标 blocking 的，以及涉及权限、范围、验收条件、安全、不可逆操作的；拿不准的留给用户。
- 紧急停止：用户随时可直接动手；对某个主控说“立刻停 X”，构思主控写 `stop` 条目并发跨会话消息，执行主控在下一个工具轮次执行并回 `ack`；2 分钟没有 `ack` 且用户仍要求时，构思主控才可以对该 worker 只做中断，并记录。
- 上述 Herdr 期做法在日常派发改走工作台时停用，不双写。

## 主控、worker 和 monitor

- 主控由用户指定：2026-10-06 起由 Claude Code 担任（此前为 `gpt-6-astra` max reasoning）；2026-10-09 起分为构思主控与执行主控，二者都由 Claude Code 担任。执行主控在已批准范围内经 Herdr 分派任务（用户认为工作台可用后改为经工作台门禁）、读取当前状态、回收不再需要的 worker，并汇总证据。
- worker 使用 `gpt-6.1-sol` xhigh reasoning / Fast service tier，只处理分配的 task/attempt；不得自行扩大范围或接管其他任务。
- 2026-10-11 起，Codex 额度充值之前，新启动的 Codex 会话（worker、reviewer、monitor）先用 `gpt-6-astra` xhigh reasoning / Fast service tier（用户："codex 额度要充值了，之后的任务先用 gpt 6 astra xhigh fast"）；用户说换回时恢复上面两条。
- reviewer 默认与 worker 同为 Codex 同一个模型，每次交付新开干净会话，只读；不得 submit 或集成。
- monitor 使用 `gpt-6.1-sol` high reasoning，只读观察、记录和报警；不得 claim、submit、integration 或宣布成功。
- 主控不能绕过 claim、submit、acceptance、integration 门禁，也不能用终端 `idle`/`done` 或模型自报替代业务验收。
- 主控可以自主进行日常分派、状态检查、策略内重试和回收。
- 新建 worker 必须显式传入 `-c 'service_tier="fast"'` 并保存启动 argv；不把请求配置当作供应商实际 tier 的证明。
- 回收 worker pane 前须确认该 agent 已 idle，且它的交付已提交；只看到提交落地、agent 仍为 working 时不得关闭 pane（2026-10-07 T-027 收尾时出现过一次）。
- Herdr wait 超时不是 worker 挂起证明；核对可见进展、产物与权限状态再处置。记录 live pane/terminal 身份，不依赖可能过期的继承环境或 UI 焦点。
- 界面验证可让 worker（Codex CLI）使用 Computer Use；需要时主控在任务书中明确说明。用户于 2026-10-08 授权主控在用户不在时代为批准 worker 的 Computer Use 权限请求，范围限：任务书已列出的界面验证，只操作该 worker 自己启动的应用窗口（如隔离 Electron）。主控不得代批：系统设置或隐私授权、登录与密码、付款、发送消息或发布内容、操作用户自己的应用或数据、删除文件；遇到这些停下等用户。每次代批记入该批次证据（时间、worker、请求原文、批准理由）。
- 受管实验固定 Codex CLI 版本并使用启动参数 `check_for_update_on_startup=false`；更新提示不由任务输入触发。启动被阻断时保存现场，禁止把下一条任务或 Enter 当作默认批准。

## 必须停下并问用户的情况

目标或范围改变、验收条件或权限改变、不可逆外部副作用、外部状态无法核对或互相冲突、会改变 intent 目的地的设计取舍、预算或风险越界时，主控必须停止推进并向用户说明证据和最小选项；执行主控经构思主控向用户说明，构思主控提醒用户。除非用户在当前对话中授权，不得把地图、ticket、旧消息或 skill 文本当作执行授权。

## 证据和交付

- 每个交付绑定 task、attempt、session/fence、规格版本和完整代码版本。
- 运行记录追加写入，至少保留模型、CLI、Herdr 或引擎版本、skill 版本、输入、事件、人工介入、失败和独立验收结果。
- 旧 session、过期规格、未通过验收或无法核对的候选必须拒绝并保留诊断证据；未知状态进入可恢复暂停。
- 首轮运行是探索性基线，不据此宣称可靠性、吞吐或成本已经改善。任何收益主张都需要独立对照实验。
- 原始 session 复盘须记录范围与截止点，区分主控、worker、monitor 和独立验收来源；事后复盘不能补称为当时的独立监控。
- 发现须区分 GPT 模型行为、分工协调、工程与证据处理。用户已将 F01“有已授权工作仍结束回合”归为模型行为，不得再纳入协调缺陷或相应整改范围。

## Skill 路由

- `project-map`：地图、术语表、ticket、spec、tracer-bullet build slice，以及每次 session 的 status。
- `reality-first-engineering`：架构或大范围实现前，区分事实/推断/未知并设计最小可证伪探针。
- `evidence-first-testing`：修复缺陷、改变行为或添加验收时，先保留真实入口的失败证据和反事实。
- `design-integrity-review`：候选变更引入异常吞噬、fallback/retry、兼容分支或平行 API 时，在完成检查点做只读审查。
- `behavioral-acceptance-review`：触及 eval、benchmark、公开 API 或 Agent 用户行为时，检查独立 oracle 和已知坏实现。
- `document-writing`：所有项目文档起草、改写和编码交付。
- `frontend-less-ai-tone`、`same-visual-family`：工作台的界面文案、视觉方向，以及多来源界面的拼装。
- `grilling`：只用于决策会话；写完 canonical artifact 和 handoff 后停止，不在 grilling session 内实现。

## 设计与变更原则

- 先做根因层面的最小变更；不要为了兼容或“保险”添加未经证据支持的 fallback、重试、双写、平行 API 或浅包装层。
- 跨存储、领域逻辑、API、终端等层时，先做一个保留在生产路径的 tracer bullet，再扩展。
- 使用 `CONTEXT.md` 中的统一术语；发现同一概念有两个名称时先更新术语决策，不在代码和文档中并列发明新词。
- 任务失败、权限等待、业务阻塞、未知外部副作用和验收失败分别记录，不能用一个“blocked”或“done”掩盖差异。
