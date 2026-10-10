---
session_id: grilling-native-cli-orchestration-20261010
status: awaiting-user
topic: 改方向：不用 Synara 统一层，原生 CLI 交互终端 + a2a 编排 + 借用 Synara 前端的轻量应用
destination_artifact: intent.md 第三阶段修订 + .project-map/specs/ 下一份新 spec + 旧 Synara 票（T-055～T-068 中未完成者）的处置清单 + 就绪 build ticket；同步 AGENTS.md、CONTEXT.md、MAP.md
created_at: 2026-10-10
updated_at: 2026-10-10
last_round: 6
---

> 指针状态：`.grilling/ACTIVE.md` 于 2026-10-10 经用户同意（R1 Q5“都采纳”）改指向本账本；上一个会话 `controller-split-user-input` 已 confirmed，原样保留。

## Destination

定下新方向并写成文档：工作台不再基于 Synara 的统一层，改为各家原生 CLI 以交互终端运行、a2a 只做编排，前端是借用 Synara 组件与样式的新轻量应用；把已定的三项功能（用户输入记录、两层主控、问题上报）搬到新载体；吸收文章《将军赶路不追小兔》里的好思路，包括权限管理。确认后交接：新 spec、就绪 ticket、旧票标 superseded。不实现。

> "我觉得不用 Synara的统一网关，只用 synara 这种前端样式框架就行，里面具体的 cli 还是看每家自己的能力，我们只做编排，像 herdr 这样。"（2026-10-10）
>
> "5.文章里好的思路我们借鉴，我没细看，但里面也有权限管理这些吧，和我们现在做的结合一下。"（2026-10-10，R0 回答）
>
> 切换条件仍沿用用户 2026-10-09 原话："肯定要把我提的功能至少都做的能用了，我才能到 Synara 里用啊"

R4 起（新会话"新思路构思"）借鉴范围补充为：任务卡与提交追溯、质量保障与写审分开、并行 worktree、构思主控的提问进面板、复盘与指标，见 C1–C10。

## Confirmed constraints

用户在 R4 输入中直接定下（2026-10-10，新会话"新思路构思"；引号内为用户原话）：

- C1 | confirmed | source: R4 输入 | 任务卡与追溯，"提示词 + 脚本"混合。用户以"关于这两点："引出文章原文："第三，我需要完整的任务追踪和复盘能力。每个任务有标准化的任务卡模板（目标、修改边界、验收条件），每次代码提交都能追溯到是哪个执行器、什么模型干的。""能用脚本保证的事情，就不要只靠提示词。" | 落地见 Q14、Q15、Q19
- C2 | confirmed | source: R4 输入 | "然后额度水位监控这个先不做。" | 留在 fog
- C3 | confirmed | source: R4 输入 | "然后还有并行 worktree：统一的命名规范、完成后自动清理、冲突自动处理。" | 落地见 Q18；与冻结契约、intent 的冲突见 R1、R2
- C4 | confirmed | source: R4 输入 | "然后就是文章中质量保证那一节。" | 落地见 Q16
- C5 | confirmed | source: R4 输入 | "然后其实写代码和审查者也要是两个 agent，比如两个干净上下文的 codex 对话。""门禁不能省、写和审必须分开" | 落地见 Q16、Q17
- C6 | confirmed | source: R4 输入 | "还有我之前说的单独面板这个能做吗？比如构思主控需要一些我回复的问题的时候，可以把这些问题放到面板上来？我回复完再传回去，这个方式我之前应该说过，批量和逐个这些。" | 复用 controller-split 的 C6、D3、D24；落地见 Q20
- C7 | confirmed | source: R4 输入 | "我可以设置一个周期或者手动启动最近工作记录的复盘，也就是文章中的周期性复盘这一章，然后可以选择用哪个cli，哪个模型，哪个思考强度来执行。" | 落地见 Q22
- C8 | confirmed | source: R4 输入 | "检测指标可以为以后的 enchanted 做一些地基，还有复盘的轨迹数据，但是 token 监控我觉得没必要做了，重复造轮子，可以想一些其他为我的系统自进化埋一些检测指标。比如按项目看，该项目下每个任务用了哪些模型，做一个分类。"（用户已用 TokenTracker 看 token 用量） | 落地见 Q23
- C9 | confirmed | source: R4 输入 | "每一次代码提交都应该能追溯到：见文章的7." | D20 由此改为用户确认；机制见 Q19
- C10 | confirmed | source: R4 输入 | "主脑给执行层打分 这个也可以。" | 从 fog 移出；落地见 Q21

## Decisions so far

- D1（user，R0 Q1=A）：不用 Synara 包装各家 CLI 的 provider 层，也不用它给 agent 的 MCP 网关；agent 以各家原生 CLI 的终端界面运行。
- D2（user，R0 Q2=B）：前端新建轻量应用，借用 Synara 的前端组件与样式（MIT），不继续删改 fork。
- D3（user，R0 Q3=停止）：T-059、T-066、T-068 停止；已写 `20261010T153340Z-ideation-cancel-001`。T-067 一并不动，去留由本会话定。
- D4（user，R0 Q4）：执行层用交互终端，不用无头模式。
- D5（user，R0 Q5）：借鉴文章的好思路，含权限管理，与现有设计结合。
- D6（user，R0 Q6=等）：T-068 等方向定；按 D1 预计作废。
- D7（recommended，R1 Q1=b）：我们自己托管终端，复用 Synara 的终端实现（node-pty + xterm）。用户追问“用 zsh 不行吗？哪个终端方案好？”——zsh 是窗格里跑的 shell，不是终端宿主，见 R2 回答；终端方案待 R2 Q6 确认。
- D8（user，R1 Q2）：门禁抽出来用，契约不变，加路径检查（任务卡“允许/禁止”路径，越界打回）。
- D9（recommended，R1 Q3）：权限四层，都在应用内：角色卡；任务卡路径 + 门禁检查；每会话的 CLI 启动参数（只作用于该会话，不碰 ~/.claude、~/.codex）；收件箱命令行限定谁写哪种条目。设置页“角色权限”编辑启动参数与路径规则，默认按此。
- D10（recommended，R1 Q4；切换条件由 D32 扩充）：切换条件改为：三项功能在新应用里能用 + 用户试用说“可用”；面板界面、打包格式、处置规则、提醒两路、T-057 软件内通知（并入 T-067）、T-064 设置页都换载体重做，不推翻。
- D11（recommended，R1 Q5）：T-059、T-064 后端、T-066、T-067、T-068 标 superseded；已关闭的 T-055～T-065 保留为历史；fork 只作组件来源，不再跟上游，不删；`ddb765956` 保留不推送；ACTIVE 改指向本账本（已改）。
- D12（recommended，R2 Q6）：终端组成：xterm.js 渲染、node-pty 托管、窗格里用用户的 zsh（登录 shell），在 zsh 里启动各家 CLI。D7 的待确认项由此关闭。
- D13（user，R2 Q7=a）：编排后台单独常驻（像 Herdr server），界面只是连上去看；关掉或重开界面，agent 照常跑。
- D14（recommended，R2 Q8）：状态只认各家结构化信号（Claude Code hooks、OSC 7501；Codex `notify`），拿不到的显示“未知”，不用正则匹配屏幕或标题；钩子只经本会话启动参数传入（Claude `--settings`，Codex `-c`），不改全局配置。
- D15（recommended，R2 Q9）：派发文本写入 worker 窗格并带 `⟦主控 #序号⟧` 标记、记派发日志、不算用户输入；两个主控也作为窗格跑在应用里，互相唤醒改为往对方窗格写带标记的提示；收件箱条目仍是事实来源。
- D16（user，R2 Q10=a + Electron）：新应用放在本仓库的新目录；外壳用 Electron。
- D17（recommended，R3 Q11）：用户输入、问题上报、收件箱、门禁都放常驻后台的同一个 SQLite 库，只追加；`scripts/inbox` 改为后台的命令行客户端；`.project-map/inbox/` 文件在切换当天退役，不双写；切换前 Herdr 期照旧用文件。
- D18（recommended，R3 Q12）：数据模型从一开始按“项目 → 任务 → 会话”支持多项目；第一个切片只跑 a2a。
- D19（recommended，R3 Q13）：第一版只支持 Claude Code（主控）与 Codex（worker）；其他家以后按需加，每家补启动参数与状态信号。
- D20（user，R4 输入 C9 确认；原为 recommended，R0 Q5 采纳时附带）：提交可追溯到工具、模型、配置、会话（git hook + agent 自己的 hook，只经会话启动参数传入）。机制见 Q19。
- D21（recommended，R4 Q14）：原则写进 intent：提示词管判断，脚本管事实。能机械核对的（身份、版本、路径、命名、尾注、清理条件、该填的记录）由脚本或门禁保证；角色卡只写"用哪个命令"，命令执行时打印该看的规则；要判断的交给提示词和人；脚本只做能判对错的检查，不做策略引擎。basis：C1、T-049、D9。
- D22（recommended，R4 Q15）：任务卡。名称统一，取代"验收合同"（CONTEXT.md 已改）；Herdr 期 brief 的叫法随 Q24 定。执行主控填：目标、非目标（至少一条）、修改边界（允许必填，禁止可选）、完成条件（可执行命令，至少一条由执行主控在派发前写好）、红态命令（可选）、任务类型、复杂度 S/M/L、执行器（CLI、模型、强度）；脚本自动填：编号、来源 ticket 与 `ready_rev`、起点提交、唯一写入者。任务类型 8 个，改要走决定：后端逻辑、前端界面、缺陷修复、测试、重构、构建与基础设施、文档、调研。`a2a card new` 生成、`a2a card check` 校验；存后台库，修订出新版本；门禁读路径、命令、类型；一张就绪 ticket 拆成一张或几张任务卡。basis：C1、D8、F14。
- D23（user，修改推荐，R4 Q16）：统一门禁检查：身份与版本、路径边界、完成条件命令、红态（任务卡写了才查：候选里的新测试放到起点提交上必须失败，在候选上必须通过）、规则式检查、独立审查（D24）、提交尾注（D26）；先跑机械检查，全过才开审查；打回时失败摘要自动写进 worker 窗格（`⟦门禁 #n⟧`），整串重跑；同一 attempt 连续 3 次打回停止自动回写，交执行主控；风险分档、OCR、定期安全扫描先不做。rejected：改动量上限（用户："改动量上限不限制"）。deferred：前端录屏（用户："录屏先不做，这个堆积起来也很大"）。basis：C4、C5、D8。
- D24（recommended，R4 Q17）：审查独立性：机械检查过后，后台新开审查会话（不续接任何会话，角色 reviewer，只读启动参数）；门禁核对它不是本任务的写入会话、为本次新开、结论绑定候选提交号，只有"可合并"放行；默认与 worker 同为 Codex 同模型，项目设置可换模型或 CLI；v1 一个主审，多审、顾问、影子以后；"需修复"清单自动回写 worker，重交后再新开审查并附上一轮清单逐条核对。basis：C5、D9、F15。
- D25（recommended，R4 Q18）：worktree。后台认领时创建：目录 `<项目>/<任务卡号>-a<序号>`，分支 `a2a/<任务卡号>-a<序号>`。清理（改冻结契约"保留所有 worktree"一句）：集成成功且干净，删目录与分支名，提交留隐藏引用 `refs/a2a/attempts/...`，事件与历史全留；打回、撤销、放弃，留隐藏引用，干净才删目录；有未提交改动或状态未知，不删，上报面板。冲突：允许路径有交集的默认不并行，执行主控要并行须写理由；文本冲突时门禁自动回写 worker，基于最新集成头重新整理、解决、重跑后重交，整串门禁连审查重跑，会话已结束则开新 attempt；程序不做内容取舍，intent 范围外条款不变；验收后集成头变化自动重新验收。closes：R1、R2。basis：C3、F8。
- D26（recommended，R4 Q19）：提交追溯。会话环境带任务、attempt、会话、角色、CLI 版本、模型、强度、启动记录号；用环境变量为该会话的 git 指定钩子目录，提交时追加 `A2A-*` 尾注，钩子目录串联项目原有钩子；Claude 原生会话号用 `--session-id` 指定，Codex 从 notify 或 rollout 取；门禁核对：带本 attempt 尾注正常，无尾注当作用户本人提交、记为人工介入，带别的任务尾注打回；"配置"即启动记录（完整启动参数、角色卡版本、项目当时的提交号），尾注只写记录号。spec 注：无尾注提交记为 action 形态的用户输入，标明来源是"推断：缺尾注"，与用户亲手输入的记录区分。basis：C9、D9、D14、F9、F11、F12。
- D27（recommended，R5 Q20）：面板收构思主控的提问：构思主控用命令把问题放上面板（类型、选项、推荐、依据）；逐题点选、采纳推荐或写几句，草稿自动保存；逐个或打包发送（沿用 controller-split D3：已答两题以上默认打包，格式"问题 N：…… / 用户答复：……"），写进构思主控窗格，每条答复记为 `answer` 输入并指向问题；needs-decision 由构思主控改写后上面板；对话里答的，面板标"已在对话中答复"；Herdr 期照旧在对话里问。basis：C6、controller-split C6/D3/D24、D15。
- D28（recommended，R5 Q21；频率按用户追问澄清）：验收打分。只在 attempt 结束时打一次，大多数任务只有一个 attempt，即最终打一次；对话回合与门禁打回不打分，只由脚本自动计数；升级时前一个执行器那次也留一条（换执行器的证据）；放弃只记结果与理由，不打分。打分是验收命令（集成或放弃）的参数，不另起一轮提问；执行主控角色卡加一句"验收时顺手打分"；命令缺打分就拒收。脚本自动填客观字段；执行主控填边界纪律、工程品味各 0–3 并写理由，外加备注；用户可另补分，不覆盖；词表定了不轻改。用户追问："不能每轮会话都打分吧，做成最终打分比较合适吗？""这个也可以加在主控验收时加一句话，这样不用多一轮额外的提问，包含在验收提问里就行，这样不会花很多 token"。basis：C10、D21、F14。
- D29（user，修改推荐默认值，R5 Q22）：复盘与轨迹归档：手动或周期（默认每周一 9:00，可改可关）；每次可选 CLI、模型、思考强度，默认 Claude Code、Opus 5.5、medium（用户："默认 opus5.5 medium"）；在普通窗格里跑；脚本备复盘包；只读，只写报告；报告进 `findings/`（无此目录的项目进应用数据目录），建议逐条上面板由用户批；后台增量归档它启动的会话的原生记录，压缩、本机、不进 Git，设置页显示占用。basis：C7、C8、D4、D13、D21、F13。
- D30（recommended，R5 Q23）：指标：原始事件从第一个切片起全记、只追加，指标从原始事件现算。采集清单：会话启动记录、回合与权限等待、用户输入与介入、派发记录、门禁逐项结果、每次交付的改动行数与文件数、审查结论与问题清单、打分、问题上报与面板问答时间、worktree 生命周期、提交尾注、复盘记录。缺陷修复类任务卡加"修复对象"字段。v1 四个视图：模型使用分类（项目 → 任务 → 会话）、一次到位率与打回原因、注意力消耗、打分汇总（执行器 × 任务类型）。不做 token、成本、缓存。basis：C8、D17、D21、D23。
- D31（recommended，R5 Q24）：Herdr 期先用三样：任务卡模板（markdown，不写脚本；brief 从此改叫任务卡）、提交尾注（`scripts/dispatch` 带环境变量与钩子目录）、验收打分（执行主控验收时顺手写一行到追加式文件，切换时一次性导入，之后不写）；门禁检查串、自动审查、面板、复盘等新应用。basis：C1、C9、C10、D17、D21。
- D32（recommended，R6 Q25=a）：切换条件扩充为：三项功能之外，任务卡、门禁检查串与独立审查、worktree、提交尾注、面板收主控提问、打分、复盘、原始事件采集与四个指标视图都在新应用里能用；用户试用时至少走一遍：一张真实任务卡从派发跑到集成（含独立审查和打分）、在面板答一次主控提问、手动跑一次复盘、看一次模型使用分类；用户说"可用"后才切换日常派发。closes：R3。rejected：b（只加日常派发离不开的，复盘与指标视图切换后做）。basis：用户 10-09 切换标准原话、D31。assumes：晚切换可以接受，因为 Herdr 期已按 D31 攒数据。
- D33（recommended，R6 Q26=b）：门禁以项目工作分支（如 `main`）为集成目标：在分支当前头上合并候选并验收，通过后 CAS 推进，不 push；分支被某工作区检出时在该工作区快进，会覆盖未提交改动时拒绝并上报，不 stash、不 reset；改冻结契约"不更新任何用户工作分支"一句；D25 的"最新集成头"即工作分支的头。rejected：a（保持 `refs/a2a/integration` 加执行主控手工合并，合并在门禁之外，F16）。basis：D21、D23、C5、F16。assumes：主控直接提交 `main` 引起的重新验收只是偶发（见 R8）。

## Facts

- F1（observed）：Synara 统一层的接入成本——T-055、T-058、T-061、T-064、T-066、T-068 均需改上游（provider 适配器、网关、投影）。
- F2（observed）：`packages/a2a-gates` 依赖 `@synara/contracts`、`@synara/shared/processRuntime`、`effect`、`node:sqlite`；可抽出但需替换两处 Synara 包。
- F3（observed）：Synara web 栈 React 19、Vite、Tailwind 4、TanStack Router、`@xterm/xterm`；server 有终端（node-pty）实现；desktop 为 Electron 43。
- F4（observed）：Herdr 0.9.3 有 socket API（`herdr api`）、`--session <name>` 多会话、`worktree`、`integration`、`notification` 子命令。用户正在用的 Herdr server 不得修改。
- F5（observed，文章附录）：文章的权限全靠提示词（主脑不写代码、执行者只改允许范围、审查者只读），由门禁兜底（改了禁止路径的提交被打回）；任务卡有"允许/禁止"修改边界与"唯一写入者"；门禁按风险分 personal/internal/saas 三档；AI 审查分 primary/advisor/shadow 三种角色。没有沙箱配置、审批人名单或越权上报流程。
- F6（unknown，D7 后不再需要：终端改为自托管）：Herdr API 能否把 pane 输出流式给外部 GUI 渲染；Herdr 许可证。
- F7（unknown）：Codex CLI 有无"运行中/等确认/结束"的结构化信号（Claude Code 有 hooks；用户转述其 2.1.295 支持 OSC 7501，未核实）。
- F8（observed，fork `packages/a2a-gates/src/core.ts:1999-2027`、`2155-2199`；managed-delivery、supervised-run 规格）：门禁把 worktree 建在 `state/worktrees/<随机 attempt_id>`，detached，没有分支名，代码里没有删除 worktree 的路径；冻结契约要求回收时"保留 worktree/候选/证据"（supervised-run 第 4 步写作"保留所有 worktree、候选和历史"）。verify 把候选合进集成头，文本冲突返回 `merge_conflict`，任务停在 submitted，没有后续自动流程；验收后集成头变化返回 `integration_conflict`。
- F9（observed，fork `git log --since=2026-10-06 --author=LuckyE`）：52 个 a2a 提交作者都是 LuckyE；7 个带 Co-Authored-By（Claude 或 Codex），没有一个带任务、attempt、会话、模型或思考强度。
- F10（measured，同上加 `--numstat`，不计 lock、snap 文件）：单个提交的增删行数之和 p50=105、p75=394、p90=720、最大 1,748。
- F11（measured，scratchpad 探针，git 2.52.0，2026-10-10）：用环境变量 `GIT_CONFIG_COUNT`、`GIT_CONFIG_KEY_0`、`GIT_CONFIG_VALUE_0` 为一个进程设置 `core.hooksPath`，不写任何配置文件；`prepare-commit-msg` 追加了尾注，加 `--no-verify` 时同样追加；不带这组环境变量的提交没有尾注。
- F12（observed，`claude --help` 2.1.296、`codex --help` 0.162.1）：Claude 有 `--session-id <uuid>`、`--model`、`--effort <level>`、`--settings`；Codex 有 `-m`、`-c key=value`、`-p` profile、沙箱与审批参数。
- F13（measured/observed，2026-10-10）：`~/.codex/sessions` 7.1G、1,175 个 rollout，覆盖 2026 年 1 至 10 月，未见自动清理；`~/.claude/projects` 563M，本项目目录下 4 个会话记录，最早一个最后活动于 10-08；`~/.claude/settings.json` 没设 `cleanupPeriodDays`。Claude Code 文档（code.claude.com/docs/en/data-usage）："store session transcripts locally in plaintext under `~/.claude/projects/` for 30 days by default"，在 Claude Desktop 或 Cowork 里开始或最近续过的会话默认不受此限。Herdr 期 `scripts/session-copy` 的副本只含 2 个会话（执行主控 Claude 会话 `9a64ed90` 与一个 Codex 会话），已被 Git 忽略。一个 1.8M 的 rollout gzip 后 0.7M。
- F14（observed，文章附录 05、06，2026-10-10 下载到 scratchpad）：05 仓库级 AGENTS.md 是索引而非手册，200 行以内，只写稳定约定，命令须从配置核实。06 验收记分卡：时间、任务、执行器、模型、任务类型、复杂度、轮数、耗时、结果（accepted/escalated/abandoned）、边界纪律 0–3、工程品味 0–3、备注；每次都记，打分带理由，词表定了不轻改，按"执行器 × 任务类型"每月交叉分析。
- F15（observed，文章第三至五章与附录 07）：质量保障三条硬规矩（先写测试、小步提交、门禁持续找问题）；写审分开；AI 审查加规则式审查（OCR）；单个 PR 3,500 行硬上限；前端录屏；门禁全绿才合并，自己派的活也不放水；审查角色主审/顾问/影子；风险三档 personal/internal/saas；周期性复盘以本地轨迹为据；指标 1–8（token、一次到位率、最长执行时间、保留轨迹、每百万 token 成本、缓存命中率、提交追溯、主脑打分）。
- F16（observed，`.project-map/tickets/T-047-gate-run-http-timeout.md:31`；fork `git branch`、`git for-each-ref refs/a2a`）：日常派发中，worker 在 `a2a-tNNN` 分支上交付，执行主控手工合进 fork 的 `a2a` 分支，冲突也由执行主控手工解决（T-047：合并 `a2a/WORKBENCH.md` 的文档冲突时"两段说明都保留"）；`refs/a2a/integration` 停在 `09fc57f8a`（T-046 那次经门禁的真实派发）。

## Frontier

无。R6 后给出最终漂移检查，待用户确认基线。

## Blocked

无。

## Fog

无（本目的地之内）。原列的以后再说的事已移入 Out of scope。

## Risks and conflicts

- R1 | resolved by D25 | owner: user（Q18） | affects: D8、C3 | 冻结契约要求回收时保留所有 worktree（F8），与 C3"完成后自动清理"不能同时成立。
- R2 | resolved by D25 | owner: user（Q18） | affects: intent.md 范围外条款、C3 | intent 把"自动解决复杂语义冲突"列在范围外；C3"冲突自动处理"需定义为流程自动，不由程序取舍改动内容。
- R3 | resolved by D32 | owner: user（Q25） | affects: D10 | 新功能是否进入切换条件。
- R4 | resolved | owner: user | affects: C7、C8 | 终端版 Claude Code 默认只留 30 天会话记录（F13）。用户 R4 答复时要求延长到 365 天，已在 `~/.claude/settings.json` 设 `cleanupPeriodDays: 365`；这是用户当次明确要求的个人全局配置，a2a 系统本身仍不改全局配置（D9 不变）。
- R5 | open | owner: Q23（指标观察） | affects: D23、D24 | 不设改动量上限后，特别大的交付可能让审查质量下降；Q23 把每次交付的改动行数记为原始事件，配合"审查命中与漏检"观察。
- R6 | open | owner: 执行主控（第一个切片的事实验证） | affects: D14 | F7：Codex 有没有"等确认"的结构化信号未核实。stop: 第一个切片先验证；拿不到就显示"未知"；若核心流程离不开它，停下报告，不改用正则读屏。
- R7 | open | owner: 执行主控（第一个切片的事实验证） | affects: D15、D27 | 往 Claude Code、Codex 窗格注入的文字能否稳定被当作一条新消息，两家都未实测。stop: 第一个切片先验证；不稳定就停下报告，不硬做。
- R8 | open | owner: 构思主控（spec） | affects: D25、D33 | 本仓库主控常直接提交 `main`，集成时 CAS 落空会触发自动重新验收，频繁时可能反复重跑。stop: spec 规定集成紧跟验收执行，并为连续重新验收设上限，超限交执行主控并上报。

## Out of scope

- 实现与派发 | reason: 决策会话。
- a2a 系统与其会话修改用户的 Herdr server、`~/.claude`、`~/.codex` 全局配置 | reason: AGENTS.md 与用户 2026-10-09 纠正（"不是让你在Claude code和codex里改权限"）。用户当面要求的个人设置不在此列（见 R4）。
- 额度感知调度与额度水位监控 | reason: C2"先不做"。
- token、成本、缓存命中率监控 | reason: C8，用户已用 TokenTracker。
- 无头模式 | reason: D4，以后按需另开。
- 改动量上限 | reason: D23，用户"改动量上限不限制"。
- 前端录屏 | reason: D23，用户"录屏先不做，这个堆积起来也很大"。
- 风险分档（personal/internal/saas） | reason: 只有 a2a 一个项目；第二个风险不同的项目接入时另开。
- 多审查者交叉、顾问与影子审查；规则式审查工具（OCR）；定期架构扫描与安全扫描 | reason: D23、D24 的 v1 范围之外，以后另开。
- 多机/远程（文章的 herdr + mosh） | reason: intent 范围外条款"通用 A2A 平台、分布式调度、多机部署"。

## Changelog

- R0（2026-10-10）：读文章与附录 01–04、07；核实 F1–F5；用户回答 Q1–Q6（D1–D6）；写 cancel 条目；建本账本。
- R1 答复（2026-10-10）：“Q1:b, 然后用 zsh 不行吗？哪个终端方案好？ / Q2:抽出来用，契约不变，加路径检查 / 3. 采纳这四层 / 4.采纳 / 5. 都采纳”。D7–D11；ACTIVE 改指向本账本。小事：用户说“1.推送 2.删掉”——已 HTTPS 推送 a2a main 到 097268b（fork 不推）；已删 /tmp 下本项目 45 个 a2a-* 夹具目录。
- R2 答复（2026-10-10）：“Q6:采纳 / Q7:a / Q8: 采纳 / Q9: 采纳 / Q10:a + Electron / 然后要删的东西删一下，左边已经回复了”。D12–D16。删除：fork 的四个旧 worktree（synara-t038、t040bc、t040bp、t045）已 `git worktree remove --force`，分支保留；内置盘可用 19G→27G。
- R3 答复（2026-10-10）：“Q11:采纳 / Q12: 采纳 / Q13: 采纳”。D17–D19；补记 D20。frontier 清空，给出漂移检查。
- R4（2026-10-10，新会话"新思路构思"）：上一会话"a2a-构思主控"停在 R3 后的漂移检查，用户没有回"确认"，而是另开会话补充借鉴范围（C1–C10），R3 后的基线因此仍未确认。读文章正文与附录 01–07（05、06 为首次读）；核实 F8–F15（含 git 尾注注入探针）；D20 改为用户确认；执行器打分移出 fog；记 R1–R4；提出 Q14–Q19，Q20–Q24 排队到 R5，Q25 待前面定完。
- R4 答复（2026-10-10）：“Q14:采纳 / Q15: 采纳 / Q16: 改动量上限不限制，录屏先不做，这个堆积起来也很大。 其他按推荐 / Q17:采纳 / Q18: 采纳 / Q19: 采纳”。D21–D26；R1、R2 由 D25 关闭；CONTEXT.md 加“任务卡”、改 Task 条目。小事：用户“你帮我把过期时间延长到 365 天如何。”——已在 `~/.claude/settings.json` 加 `cleanupPeriodDays: 365`，JSON 校验通过；R4 关闭。提出 Q20–Q24；Q26 从 fog 升为问题，排到 R6；记 R5。
- R5 答复（2026-10-10）：“Q20:采纳 Q21:采纳,然后这个打分频率怎么样？不能每轮会话都打分吧，做成最终打分比较合适吗？ Q22:采纳，默认 opus5.5 medium Q23:采纳 Q24:采纳, 还是那个问题，打分的频率，但这个也可以加在主控验收时加一句话，这样不用多一轮额外的提问，包含在验收提问里就行，这样不会花很多 token”。D27–D31；打分频率澄清为每个 attempt 结束时一次、作为验收命令参数（D28）；复盘默认改为 Opus 5.5 medium（D29）。核实 F16（日常合并为执行主控手工完成）。提出 Q25、Q26。
- R6 答复（2026-10-10）：“Q25:a Q26:b”。D32、D33；R3 由 D32 关闭；D10 标为由 D32 扩充；F6 因 D7 不再需要；fog 清空，以后再说的事移入 Out of scope；记 R6–R8（各带 owner 与停止条件）。frontier 清空，给出最终漂移检查。
