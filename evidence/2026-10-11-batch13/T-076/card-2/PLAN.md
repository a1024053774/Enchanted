# T-076-2 实施计划（2026-10-11，待执行主控批准）

计划交付：**PASS**。实施与验收：**INCOMPLETE**。本轮只读核对和写计划；未改产品或测试、未启动后台/PTY/真实 Codex、未提交。主控 #30 要求“先交计划，停下等我”，交付本文后停止。

## 0. 范围、基线与批准点

- Task：T-076-2；ticket T-076，`ready_rev: 1`；worker：`s13-t076-2`。
- 开工分支：主 checkout `main`；HEAD：`a7f4cc3033c16d5888de50d8352da516c941f8e9`。T-076-1 的 `42e2b8ed`、`d95f4171` 已在此基线上。
- 起始脏文件：`evidence/2026-10-09-batch11/controller-poll.log`、`evidence/2026-10-10-batch12/controller-poll.log`；保留，不纳入本卡提交。
- 目标：完成质量检查串、同 attempt 修复重交、fresh reviewer、最终打分；证明真实的“第一次打回 → 自动回写 → 修好重交 → 审查可合并 → 带分集成”。
- 非目标：T-077 的命名/清理/冲突/R8 实现，T-078 的主控与收件箱，存储迁移，Electron 改动，正式工作台切换。
- 验收：本票六类反例均通过后台 CLI 到门禁被拒并留事件；正例用真实交互 Codex；保持身份、fence、CAS、操作锁、中断恢复与 T-076-1 证据约束。
- 允许修改：卡片所列 `workbench/src/`、`hooks/`、`tests/`、`workbench/README.md`、本证据目录、T-076 Resolution。计划阶段不改 ticket、地图、spec、全局配置或 `scripts/`。

**本次批准需要明确覆盖以下选择。** 这些是拟议接口，不是已经实现或已获批准的契约：

| 编号 | 待批准事项 | 选择与原因 |
| --- | --- | --- |
| P1 | 红态测试文件声明、规则配置来源 | `red_commands` 非空项增加显式 `test_paths`；项目规则从注册时的工作分支提交读取 `.a2a/quality.json`，按正文第 2 节快照。不能根据文件名/命令字符串猜哪些是测试 |
| P2 | 只读 reviewer 的结论通道 | reviewer 不写请求文件；显式输出第 4 节的 JSON 请求，由本回合 Stop hook 落文件并走既有 B relay。此项是 B 的 reviewer 扩展，需要批准，不能当成原有 worker 文件通道已经证明 |
| P3 | `run` 的最终验收 | `run` 负责等待交付、修复与审查，在审查通过后等待执行主控显式 `integrate --score-file` 或 `abandon --score-file`；不在派发前预填最终评分，不自动编造分数。期限继续显式给出，全部操作绑定原 attempt |
| P4 | 断言与夹具迁移 | 批准第 7 节 W01–W06 的准确位置/范围，以及 F01–F04 的夹具适配；没有列入的业务断言不改 |
| P5 | 真实回合和 hook | 批准第 9 节预算与第 10 节的会话 hook 范围。每个实际启动仍给出准确 argv、隔离目录和授权引用，经沙箱外脚本交接；不能把本文当成 hook 已获批准 |

## 1. 已核对的事实与未决边界

**REALITY GATE：INCOMPLETE。** 方向受 ticket 约束；只读 reviewer 结论通道尚未实测，P1–P5 等待主控批准。

| 状态 | 事实/边界 | 来源与影响 |
| --- | --- | --- |
| observed | `verify` 现有顺序为合并、路径、完成条件、尾注；不执行 `red_commands`，没有项目规则或 reviewer | `workbench/src/gates/core.ts:2401`、`taskCards.ts`；补在唯一生产路径，不增第二门禁 |
| observed | 已有 `red_commands` 仅接受 `{argv}`，没有测试文件清单；库中保存任务卡快照 | `taskCards.ts:14,117`；需要 P1，不能臆测测试文件 |
| observed | 现有 submit 在 candidate 不同时报 `candidate_conflict`，运行时交付回合也绑定旧 turn | `core.ts:2359`；仅凭明确打回记录允许下一次交付换 C/交付 turn，保留 T-076-1 的原生身份检查 |
| observed | 现有 `run` 顺序 verify/integrate，oracle 失败后尝试 reclaim | `core.ts:1486–1555`；它会和修复回写争用同一 worker，必须接上新协议 |
| observed | `store.register` 已给 source=gate 生成 `⟦门禁 #序号⟧`；`Panes.dispatch/drain` 先登记、空闲才 bracketed paste 加 CR | `store.ts:43`、`panes.ts:292`；复用，不另造发送队列 |
| observed | 当前 Panes 只允许一个 worker；角色、caller address、沙箱和请求白名单硬编码为 worker | `panes.ts:112`、`relayFiles.ts:7`、`relay.ts`、`daemon.ts:81`；按实际第二种角色扩展边界 |
| observed | B 通道经显式文件和匹配本回合的 Stop 转交，重复 request_id 不重复处理；Stop 本身不 submit | T-075 rev 4；`relay.ts`、`daemon.ts`；reviewer 也不能凭 idle/done 被判可合并 |
| observed | Codex 0.162.1 的旧实测 Stop 原始数据有 `last_assistant_message`、`session_id`、`turn_id` | `T-075/card-3/outside-verify-03/probe/orchestration-events.json` 的 hook_received；这是旧通道事实，不是本卡只读 reviewer 通过证据 |
| observed | 官方 hook 文档也列出 Stop 的 `turn_id` 与可空 `last_assistant_message` | [OpenAI Hooks 文档](https://learn.chatgpt.com/docs/hooks)，2026-10-11 查阅；只支持字段设计，固定 CLI 的端到端行为仍须实测 |
| observed | `scripts/score` 的 schema=1 已完整规定 executor/user、放弃例外及七类打回计数 | 只读 `scripts/score:19–94`；后台与它对齐，不改该脚本或真实 scores 文件 |
| observed | T-077 计划的 R8 只沿用同 C、同合同/身份的有效 review；它不接受裸 passed 布尔值 | 只读 `a2a-wt-t077/.../T-077/PLAN.md` 第 6 节；该 worktree 是未提交现场，不以它的 PASS 为证据，不写入它 |
| unknown | 固定 CLI 下，read-only + never 是否仍把显式 JSON 完整送到本会话 Stop，且工具无法改候选 | P-review 探针，见第 9 节；失败即停，不转 workspace-write、不加 writable root、不改用读屏 |
| unknown | 旧手工 claim 测试没有真实 worker launch，如何提供新增评分来源而不伪称真实模型 | F01 明确使用受控运行时证据；不让生产门禁凭 card.executor 冒充实际 launch。若该适配不能保持原断言含义，另交白名单 |

已发现规范记录差异：spec 第 5 节仍写 socket 方案 A；T-075 rev 4 及当前代码已用 B。本卡按主控 #30 明确要求参照 B 提案，已上报 `20261011T161950Z-worker:s13-t076-2-issue-001`（正文 `ISSUE-spec-channel.md`），不修改 dated spec，也不重新验证/恢复方案 A。执行前请主控确认按已有 rev 4 衔接，并把规范处理交构思主控。

**Ubiquitous language**：沿用任务卡、attempt、受管 session、原生会话、交付回合、启动记录、审查结论、验收打分；review_id 只是一次审查的记录号，不是新 attempt。

**Deep modules**：检查与状态跃迁由门禁持有；Panes 只负责真实 CLI/PTY/身份事实；relay 只做明确请求的转交。新增文件仅放有独立职责的规则/红态执行或评分格式校验，不新增策略引擎、通用工作流层、通过布尔开关或平行 API。

## 2. 检查串、接口与规则配置

### 2.1 固定顺序

1. `submit`：核对 task/attempt/session/fence/spec、运行身份、交付回合授权、完整 C、worktree HEAD、干净状态；提交事实先入库。
2. `verify --task T --attempt A`：持原任务操作锁，固定本次 G、C、卡快照；沿现有路径建合并结果 M。合并冲突返回 T-077 的接口，不吞成完成条件失败。
3. **路径**：继续检查允许/禁止路径、重命名和删除两端、G→M 净改动；不放松原有路径与尾注保护。
4. **完成条件**：在 M 的 detached 验收 worktree，按任务卡快照顺序执行 argv；一项失败就终止后续机械项。
5. **红态**：卡没有命令时记录 `not_applicable`，不假记 passed；有命令时，对认领起点 B 加候选测试得到的目录运行失败，并在独立 C 目录运行通过。不能把 G 当 B，不能把整个候选实现搬到 B。
6. **规则式检查**：在 M 执行注册时冻结的项目规则 argv，如 lint、类型检查；逐项保存 cwd、argv、开始/结束、退出码、原始输出、通过/失败/未知。
7. **尾注**：沿用 T-075/T-076-1。外任务/旧身份尾注拒绝；缺尾注仍记推断人工介入，不擅自改成拒绝；真实模型与强度继续按原生事实核对。
8. **独立审查**：机械项都过后落 `review_requested`，再新开 reviewer；review 结论到达前不能集成。
9. **验收打分与集成**：只由执行主控显式命令发起；有效 review、分数、当前身份与候选都核对后才建立 integration intent/CAS。

每项结果绑定 task、attempt/session/fence、spec/card、verification_id、B/G/C/M。机械 `verification.state=passed` 只表示机械串通过；task 在等待审查时拟为 `reviewing`，有效“可合并”后为 `verified`。`verify` 返回机械记录与 review_id/待审状态，不将待审包成验收成功。命令启动失败、未知退出与中断进入 paused/unknown，不能算红态或可自动修复的质量打回。

检查实现只维护一条内部执行路径，供显式 verify 和 T-077 的 R8 调用；在同一操作锁内调用内部段，不递归走 CLI 争用自己的锁。锁不跨 reviewer 的整个模型回合：机械结果及 review intent 持久化后释放，review_submit 再取原任务锁并重新核对全部绑定。等待、重启与迟到结果都不能绕过核对。

### 2.2 红态的最小声明（P1）

拟保留任务卡的 13 个顶层字段；非空 `red_commands` 每项为：

```json
{"argv":["python3","tests/test_value.py"],"test_paths":["tests/test_value.py"]}
```

`test_paths` 由执行主控在派发前明确填写，写入卡版本/快照；非空、精确仓库相对路径，不是 glob，不准 `..`、绝对路径、Git 元数据、symlink 或目录。每个路径必须是 C 中的普通文件，且相对 B 新增或修改；只把这些 Git blob 放进 B 的红态目录，不复制生产文件、依赖目录或工作区的未提交内容。测试辅助文件若必需，也要显式声明并由 reviewer 检查没有夹带实现。红态 C、B 目录与 M 验收目录分开，防止测试执行的副作用污染后续检查。

现有空数组不变；已有非空 `{argv}` 卡不能静默猜文件，需执行主控保存新版本。不保留两套红态定义。测试数据内容和“是不是有效业务测试”仍由任务卡作者/reviewer 判断；脚本不靠名字或关键词判含义。

门禁机械事实为“B+测试的命令正常退出且非零，C 的同一命令退出 0”，保存两边完整结果。不能仅凭非零宣称独立业务红态；启动失败、signal/timeout 不满足，语法/导入错误等须在独立审查中判为无效证据。本卡自己的红态进一步要求保存具体业务断言失败，环境错误不计。若主控要求机器区分任意测试框架的业务失败与导入失败，需另定显式报告协议，不能加 stderr 关键词推断。

### 2.3 项目规则配置（P1）

拟从 `create` 读到的工作分支提交 B0 中读取 `<repo>/.a2a/quality.json`：

```json
{"schema":1,"rule_checks":[{"id":"lint","argv":["npm","run","lint"]},{"id":"types","argv":["npm","run","typecheck"]}]}
```

记录 repo、配置路径、完整来源提交、原始内容与解析结果到既有 created/card 快照事件及 task JSON；不读候选 C 的配置来决定检查项。缺文件表示未配置，事件明确记录；文件存在但内容损坏、重复 id、空命令、非法字段则拒绝注册，不回退。非空命令在 M 执行，环境与绝对可执行文件解析沿已有完成条件机制，不加依赖。候选若改配置不能影响本次任务已冻结的规则；下一次注册才读取新配置。P1 批准后在夹具里提供该文件，本卡不修改主仓库根配置。

## 3. 打回回写与重交

### 3.1 一次打回的原子事实

机械质量失败或有效 reviewer“需修复”产生一条 `delivery_rejected`，含 submission/verification/review 标识、检查项、C、明确失败结果、序号与计数。持锁保存原失败记录和修复授权，然后才交 Panes 投递；投递前再核对原 attempt/session/fence/launch，没有当前活 worker 时写 issue，不接管新 attempt。

正文由事实构造，不用模型总结或关键词判定：

```text
⟦门禁 #<dispatch_records.seq>⟧
任务 <task> / attempt <attempt> / 候选 <C> / 第 <n> 次打回
失败项：completion | red_state | rule_checks | independent_review | …
证据：<verification/review id、命令、退出码、原始输出位置>
修复清单：<审查的 location / failure_scenario / suggestion 原文>
在本 attempt 内修复、运行完成条件、提交并用给定 CLI 显式重交。
```

已有 register 写原文/source/id/序号，再入队；只在匹配 Stop 后的 idle 注入，CR 先记忙。不混作用户输入/人工介入。控制字符在协议数据中用 JSON 转义，原始证据保留；不把原始终端控制字节注入 PTY。

### 3.2 重交、去重和三次上限

- 只有针对当前 C 的明确打回，才开放一次新交付轮次。该授权允许本原生会话的新 turn 提交新的 C；同时仍核对 launch/thread/shell/leader/native_session、fence、spec、HEAD、干净状态。普通 submitted/verified 未被打回时继续拒绝换 C。
- 重交成功后记新 submission，旧 C、verification、review 原样保留，当前审查失效；从 G/M 构造起重跑整串，不只重跑失败项。计数不因换 C、完成一个机械项或回执回合清零。
- 一轮最多记一次打回；同一请求/同一失败结果重放不递增、不重复注入；无新交付重复 verify 不再次制造同一打回。统计从事件推导，不加独立计数表。
- 第 1、2 次失败自动登记并回写；**第 3 次失败保存摘要及 issue，但不向 worker 登记第三条修复消息，不再自动注入**。旧队列里同修复链的未发送项也不能在停止后送出；保留取消/抑制事实。任务暂停交执行主控；本卡不提供偷偷重置计数的命令。
- “连续”指同 attempt 内尚未完成完整门禁的交付链；中间机械通过但 reviewer 需修复不清零。最终通过/放弃/升级结束链，新 attempt 才从零开始。
- 身份伪造、数据损坏、未知外部效果、review 协议非法不是提示 worker 改代码能解决的问题：拒绝并记录/上报，不自动修复或重试。
- 停止时 issue 复用后台已有追加式 issue 能力，包含接收者 executor、绑定身份、三次失败证据与最后 C；面板属于后续切片，本卡不新建 UI。三次停止不把 attempt 记 accepted，也不擅自放弃/打分。

`run` 必须保留原 attempt 等待新 submission，不能在首个 oracle_failed 就 reclaim。显式 submit 等待期限不因每次回写无限延长；到期记录 deadline/暂停与现场，不能因此给出评分。审查通过后按 P3 等执行主控最终命令，再核对原 attempt 的 accepted/结束与 idle 回收。T-076-1 的“回执不是新运行身份”和 leader/native_session 反例继续成立。

成功 submit 的 B 回执继续是仅确认通知；质量打回另有修复指令，不能套用当前 daemon 的“仅确认、不调用工具”文案。两者有独立类型和序号，按登记次序排队，不能让同一失败既发 ACK 又发第二份修复。

## 4. 产品独立审查会话

### 4.1 新建和启动参数

门禁为本次机械通过的 C 生成 review_id，持久化 review intent 后由后台创建独立 thread、受管 session、launch、capability、PTY 和 detached 审查 worktree。沿用一次交付一个 reviewer；修复重交新 C 时重新开，不能 resume/fork/续接旧 reviewer 或 worker。上一轮问题清单作为显式材料传入，不带之前的对话历史。

审查包包含任务卡快照、角色卡版本、B/C、完整候选 diff、完成条件/红态/规则/尾注结果及上一轮问题清单。reviewer 在 C 的目录读代码，合并后的 M 机械结果作为证据；绑定 C 使纯 G/M 变化能按 T-077 沿用结论。

真实验收拟固定 Codex CLI 0.162.1；worker/reviewer 都请求 `gpt-6.1-sol`、xhigh、Fast。reviewer argv 的关键部分：

```text
codex --no-daemon --no-alt-screen -C <detached-review-worktree>
  -a never --sandbox read-only -m gpt-6.1-sol
  -c model_reasoning_effort="xhigh" -c service_tier="fast"
  -c check_for_update_on_startup=false -c tui.notifications=false
  -c features.network_proxy=false
  -c hooks.UserPromptSubmit=<本 launch 的 signal 命令>
  -c hooks.Stop=<本 launch 的 signal 命令>
  -c hooks.PermissionRequest=<本 launch 的 signal 命令>
  --dangerously-bypass-hook-trust
```

此处是参数清单，实际 argv 由数组生成、完整保存。不开网络、socket 放行或额外可写目录；不改只读沙箱。hook 仍只经每会话 `-c` 配置并须主控批准。reviewer 不安装 worker 的 Git 尾注 hook，不提供 Git 写入授权；worker 隔离 home 仅两条 git add/commit allow，reviewer 单独 home 不含 Git 写规则（权限取更小集合，请随 P5 批准）。两个 home 都只复制 auth.json、仅信任核实后的夹具根，不继承用户 hooks/全局配置。

Panes 解除的是“一整个后台仅一个窗格”的 S1 限制；仍检查每个 task 的写入会话唯一。caller/relay 按保存的角色路由，不能用请求里的 `role` 自称 reviewer。首次 release 沿已有执行主控核对前台领导进程后显式放行的机制，计 executor action；不为 reviewer 新造读屏判 idle。

### 4.2 显式 JSON 与 B 通道扩展（P2）

严格 read-only 下不能要求模型写 `/tmp` 请求文件。因此 reviewer 在最终消息中只输出完整 JSON 对象，明确请求 `review_submit`；这不是从“我觉得能合并”推断动作。Stop hook 只针对已绑定 reviewer、匹配本 review 的主 turn，解析整个 `last_assistant_message`；不剥 Markdown fence、不提取部分 JSON、不扫描终端或 transcript 中任意历史文本。字段缺失/多余、null/非法 JSON、无显式 command 都不形成结论，保存原始数据、上报并停止，不自动追加纠格式回合。

hook 把这份显式请求以固定 review_id/request_id 写到该 launch 的专用请求目录，再经同一 `signal`/RequestRelay/门禁处理；只有 hook 写文件，模型没有可写例外。不让模型传任意文件路径、任意后台命令或 shell。沿用 relay 的 request intent/outcome、身份绑定、请求重放和未知结果不重试。worker 仍只走原有显式文件 B 通道。

```json
{
  "schema":1,
  "request_id":"review-<review_id>",
  "command":"review_submit",
  "task":"T-XXX-1",
  "attempt":"<worker-attempt>",
  "session":"<reviewer-managed-session>",
  "fence":1,
  "spec_rev":1,
  "review_id":"<review_id>",
  "candidate_commit":"<完整 C>",
  "verdict":"可合并",
  "findings":[]
}
```

`verdict` 仅为“可合并”/“需修复”；可合并必须 findings 为空；需修复必须至少一条 `{location:{path,line}, failure_scenario, suggestion}`，文本非空、路径/行号类型合法。语义由 reviewer 判断，程序只核对协议，不用正则/关键词决定工程结论。

后台持久化的 review result 还加入 **自己观测** 的 review generation、card_snapshot_id、verification_id、worker session/launch、reviewer thread/session/launch/native_session/leader、turn、请求和接收时间；这些不能由结论 JSON 自报覆盖。成功写库即可结束 reviewer；不注入纯 ACK 另花一轮。回执保存在 relay 与 CLI/状态查询中，清理前确认匹配 Stop 已 idle。

### 4.3 门禁核对与需修复回写

1. review_id 由门禁为本次机械通过创建，尚未被消费/中断/替换；本 task/attempt/session/fence/spec/card/C 与当前仍一致。
2. launch 必须来自该 review intent 之后创建的后台 launch 记录，role=reviewer、运行模式只读、无 resume/fork 参数；不能提交任意已有 launch。
3. reviewer thread、受管 session、launch、原生会话均不能是本 attempt 的 writer；同一原生会话也不能已服务之前的 review 或任何 writer。核对唯一的本次启动关联、原生 session 元数据与本次首个派发前没有历史用户回合；独立 home 只复制 auth，不复制旧 rollout。不只比较创建时间或一个自报 `fresh=true`。
4. capability、shell/leader、原生会话、匹配 Stop/turn 全部来自 Panes 的当前观察；T-076-1 的辅助进程不误当新 leader。没有可核对 native identity 就拒绝/暂停。
5. verdict 的完整 candidate_commit 必须逐字等于当前 C；迟到旧 C、旧 spec/attempt 结论只留拒绝事件，不影响新候选。管理员 CLI 不能用裸 JSON 无 reviewer caller 注入“可合并”。
6. “可合并”入库后 task 才可 verified；“需修复”问题清单原文交第 3 节打回流程，计一次 independent_review 打回。新 C 必须新 reviewer。

重启时 review intent 没有结果或真实窗格身份丢失，进入 unknown/paused，不把原生结束或队列送达当结果。结果提交、审查清理分别留事实，禁止回收还 working 的 reviewer。

## 5. 打分接口、拒收及格式对齐

### 5.1 命令

```text
.../cli.ts --state <隔离目录> integrate --task T --attempt A --score-file <executor-score.json>
.../cli.ts --state <隔离目录> abandon --task T --attempt A --score-file <executor-score.json>
.../cli.ts --state <隔离目录> scores_validate --file <scores.jsonl>
```

`score-file` 只装执行主控主观字段，即 `scripts/score` 的 data；事实由后台计算。integrate 只接受 result=通过；abandon 结束本 attempt，接受 result=放弃或升级；升级必须有两项分数/理由/notes，不替主控自动启动更强模型。放弃仅 `{result:"放弃",reason:"非空理由"}`，禁止混入分数、notes、facts。放弃不是 reclaim；reclaim 是窗格清理，不提供另一条无评分的最终验收入口。revoke/revise 仍是原合同的取消所有权/改版，不冒充已完成评分。

通过/升级精确字段：`result,boundary_discipline,boundary_reason,engineering_taste,engineering_reason,notes`。分数必须整数 0–3（拒 boolean/字符串/小数/越界），理由非空；notes 必须字符串，允许空。缺文件、缺项、未知字段、结果与命令不匹配、假事实、非执行主控调用均拒绝，保存拒收事件，不能推进引用或结束 attempt。CLI 的语法层允许请求到达后台，由门禁判定缺评分；不能仅以本地 usage 错误替代“缺分被拒且有事件”的反例。

在生成 integration intent 前校验评分；把原评分及上下文绑定到该 intent，最后 integration 成功和 score 事实在一次已有数据库事务中落库。Git 变更前/后中断恢复沿原 intent，不能改分/重计；CAS 未成功时只有意图，不产生最终通过评分。重放同一个最终命令无新分、无新 Git 写；不同评分不得覆盖旧记录。abandon 在同一原 attempt 锁下保存终结与最终分，未知 integration intent 先 reconciliation，不能以放弃掩盖。

不改库结构：审查、打回、评分使用现有追加 events/orchestration_events 的类型及 JSON 内容；需要的当前状态放在已有 task/verification JSON，并经原 save() 与事件同事务。既有一致性缺口另票处理；若实现发现必须迁移表，停下报告。

### 5.2 `records/scores.jsonl` schema=1 映射

| 输出字段 | 后台来源/规则 |
| --- | --- |
| schema / score_id / created_at / source | `1`、唯一最终评分号、结束时间 UTC、`executor`；每 project/task/attempt 最多一条最终分 |
| launch_id / project / task / attempt | 本 attempt 的 **worker** 启动记录与门禁身份；不得误用 reviewer launch；缺实际来源不凭空补造 |
| cli / model / effort | worker launch 的 CLI 版本与最近交付回合实际模型/强度；请求值与实际值分开保存，不能拿请求值冒充实际 |
| data | 主控精确提供的上述主观字段；放弃只有 result/reason |
| facts.task_type / complexity | attempt 绑定的任务卡快照 |
| facts.delivery_rounds | 同 attempt 已接受的独立 submission 轮数；重放同请求/重复同一交付不加一，ACK 不算交付 |
| facts.elapsed_seconds | attempt 认领到最终结束的整秒，非负；含等待/审查，时间源和端点事件号留在事件关联中 |
| facts.human_interventions | 同 attempt 的 human_intervention 事件去重后的数量；主控派发、门禁消息与 reviewer 输入不计 |
| facts.rejections | 必含 `identity_version,path_boundary,completion,red_state,rule_checks,independent_review,commit_trailers` 七键，值为非负整数；从逐项打回/拒绝事件推导，重放不重复计 |
| 用户行 source=user / score_of | 校验时原样保留，score_of 指先前 executor 分，身份一致；绝不覆盖原分。此卡不新增用户打分 UI |

放弃行不带 facts，按现有 `scripts/score.validate_scores` 的明确规则对齐；客观事件仍保留在库里。新后台不向真实 `records/scores.jsonl` 双写。此卡提供只读 `scores_validate`，读取文件逐行严格校验，并用隔离样例做双方验证：旧脚本读后台导出的 schema=1 payload，后台读旧脚本产生的样例；不调用旧脚本给真实任务打分，也不实施切换导入。未知/损坏/重号/同 attempt 重复分逐行报告，不猜补零。

## 6. T-077 衔接与文件冲突

### 6.1 R8 可沿用条件

沿用已有“可合并”仅适用于 **纯 G/M 改变** 的 CAS 重验：candidate C、task/attempt、worker session/fence、spec/card 快照、有效 review 身份均未变。mechanical checks 在新 M 全跑，新 verification 保存 `reused_review_id` 及旧/新 G/M；不调用假 reviewer，不只传布尔值。

C 变化、文本冲突后重交、attempt/spec/card 变化、审查未完成/被拒/身份未知均不能沿用；需 fresh review。上一轮“需修复”不能作为可沿用结论。T-077 第 4 次 CAS 失配停止的计数与本卡第 3 次质量打回是两条不同链，不能互相重置或混算。R8 保留同一个待最终成功的评分意图，失败时不重复打分。

本卡暴露的是内部 `verification + review reference` 绑定检查和统一 gate 回写调用点；T-077 负责什么时候重验、生命周期和冲突上报。不另实现 retry 循环或 worktree 管理层。

### 6.2 worktree 用途

对齐 T-077 已提出的根 `<state>/worktrees/<project_id>/`，以它最终批准实现为准：

- worker：`<card>-a<N>`，分支 `a2a/<card>-a<N>`。
- M 验收：`<card>-a<N>-verify-<V>`，detached。
- 红态 B/C：`<card>-a<N>-red-base-<V>`、`<card>-a<N>-red-candidate-<V>`，detached，属于验收用途。
- 审查 C：`<card>-a<N>-review-<R>`，detached。

V/R 由持久记录分配，不使用目录数量推算，不复用历史目录。此卡在未合流前沿已有唯一分配边界加用途输入，不自做 worker 重命名/自动删除。结果先落库再通知生命周期边界，T-077 负责删除；运行中、结果未知和仍待修复的 worker 不能因“打回”被提前删。T-077 接入前须把缺少的用途清理如实记 INCOMPLETE，不复制一个临时清理实现。

### 6.3 预计冲突位置与写入者

| 文件/位置 | 本卡负责 | 与 T-077/T-078 的衔接 |
| --- | --- | --- |
| `gates/core.ts` submit/verify/integrate/run/reclaim 周围 | 质量串、修复授权、review 绑定、评分意图 | T-077 改同段 R8/命名/清理/冲突；主控合流逐 hunk 保留原 attempt 与锁语义 |
| `contracts/a2aGates.ts`、`gates/cli.ts` | review/score/abandon 输入，结果字段 | T-077 放弃/并行理由参数，T-078 管理调用身份；不并存两个 abandon 命令 |
| `panes.ts`、`daemon.ts`、`relay*.ts` | reviewer 角色、Stop 回传、质量消息与预算 | T-077 归档窗格释放，T-078 主控窗格/授权；只按角色扩展同一机制 |
| `stateConsistency.ts` | 仅在需要时识别新增 JSON 状态字段 | 不修既知存储缺口，不新增当前表 |
| `workbench/tests/daemon_acceptance_*`、任务卡/真实回合 runner | 新契约夹具与反例 | T-077 已有 W01–W16 白名单，本卡编号/授权独立，不能互借授权 |
| `workbench/README.md` | 当前可用命令、权限、限制 | 合流后由主控安排统一核对，不写尚未实现的功能已通过 |

本 worker 只写主 checkout 自己范围；不修改或 cherry-pick `exec/t077` 现场。上述路径若他人变更进入 main，重新读直接调用与断言再继续；不覆盖、不回退。合流的 R8+真实审查联合验收由主控安排，当前任务卡不授权本 worker自行做分支集成。

## 7. 断言白名单申请

行号对应开工 HEAD；以文件+方法定位，行号漂移不扩大授权。此处是**待批准白名单**，不是已修改记录。8/9/18 与 T-075/T-076-1 的旧报告保留，不改原始证据。

依据 Q1=spec §3.4 打回/重交/三次；Q2=§3.5 fresh review；Q3=§3.6 与 §8 结束评分；Q4=§3.8 idle 回收及原 T-076-1 身份约束。

| 编号 | 文件、方法、位置 | 旧断言/前提 | 拟变更与独立预期 | 红态 |
| --- | --- | --- | --- | --- |
| W01 | `acceptance/test_run_e2e.py:432–451`，`test_oracle_failure_is_not_success_and_reclaims_only_owned_thread` | 第一次 oracle 拒绝即结束失败并 close 原 worker | 改为首拒保留原 worker/attempt，自动 gate 消息已登记；等待修复或受限暂停，不能 accepted/ref 不动；保留独立 oracle 非零断言与其他会话未被关闭检查。可改方法名使其准确表达新行为。目录清理断言交 T-077，不借此改 | R-feedback：起点首拒后没有修复消息并 reclaim；Q1/Q4 |
| W02 | `acceptance/test_run_e2e.py:207–245`、`:293–311`，两个正常闭环方法；`:570–583` 重放方法的正常闭环前置 | run/手工 integrate 没有 reviewer 与主控评分也可完成 | 增加显式受控 reviewer/执行主控动作与事件断言后再完成；保留 accepted、原 candidate/ref、唯一 Git 写、分页 oracle、只关闭本人、重放无副作用。正常 worker 派发仍只一次；reviewer 的输入另按角色计，不把质量消息伪成初始任务 | R-review、R-score；Q2/Q3 |
| W03 | `acceptance/test_coop_e2e.py:405–455`，`test_good_candidate_uses_oracle_snapshot_and_integrates_once`；`:340–341`、`:461–462`、`:506–510` 的 verify 后阶段前置 | 机械完成即 verified，可无评分 integrate | 精确插入等本次独立 review 完成的前置与主控 score 参数；新增“待审不能集成、缺分不能集成”业务检查。保留旧通过后 verified、候选/卡快照、原 oracle、撤销/改版和冻结候选所有断言，不允许 verify 包装直接造 review | R-review、R-score；Q2/Q3 |
| W04 | `workbench/tests/test_task_cards_e2e.py:138–167`、`:193–213`、`:327–360`、`:386–400`、`:402–423`，对应正常集成前置与事件列表；由 `test_daemon_gates_e2e.py` 继承 | 只查旧四项，机械后直接集成 | 增加 reviewer/评分前置与 red/rules/review/score 事件；原路径、完成条件失败、尾注人工介入、dirty 内容保护/非 fast-forward 断言不改。T-077 已申请的 R8/目录断言不由本卡改 | R-chain、R-review、R-score；Q2/Q3 |
| W05 | `workbench/tests/test_multiturn_identity_e2e.py:120–159`，receipt 后 reclaim/run 两正例；`run_t076_real.py:284–299` 正例收尾前置 | 仅 worker 交付+ACK 即自动集成，真实 runner 固定累计 2 turn | 受控测试显式加本候选 reviewer 与主控打分，再验证 run completed/reclaimed；新真实 runner 分角色计数，不改 card-1 的历史证据。原 turn_id=delivery-A、runtime_identity、原生/leader 伪造反例与 ACK 不干活断言保留；本卡优先新建 real runner，旧脚本变更限使新增前置明确，不扩真实预算 | R-run-finalize；Q2/Q3/Q4 |
| W06 | `workbench/tests/run_worker_delivery.py:195–250` 正常收尾、`test_task_cards_e2e.py` 卡校验用例中 `red_commands` 非空项（当前正例均为空） | 没有 review/score、总通知/turn 只按单 worker 计；非空红态只需 argv | 新真实路径以新 runner 为主，旧 harness 如复用则显式新增前置、按 launch 分组计数；不删除同请求仅一次、精确原生消息与 ACK 不执行工具检查。卡校验新增 test_paths 的独立无效/有效样例，空数组和13顶层字段不变 | R-red-declaration、R-review；P1/Q2/Q3 |

**Recovery 9 项不申请改业务断言。** `test_recovery_e2e.py:477–478,565–566` 的 verified 观察通过夹具先完成受控 reviewer 后继续；`:583–607` 恢复/重放仍验证同 intent、精确 CAS 次数和原事实不变；新增评分恢复检查放本卡新测试。`:560–562` 中断 worktree 保留、未知引用 reconciliation、原 live operation lock 一律不动。若实际无法只改夹具实现，停下另交白名单，不删原断言。

**不得误改的冻结候选反例**：`test_coop_e2e.py:476–511` 是“未获打回就换 C”，在新契约下仍必须拒绝；只在另写的“已获打回后重交”正例允许 C2。`test_run_e2e.py:254–264` 的 leader-changed 仍是原生身份替换，不能借新 turn 支持放行。

### 7.1 夹具适配范围（不是产品免检开关）

- F01：`daemon_acceptance_adapter.py`、`daemon_acceptance_host.ts` 以及 `multiturn_identity_host.ts` 增加明确的受控 reviewer 运行时边界、独立外部结论与调用身份。通过真实 CLI/relay/门禁校验，不改 `checkVerification`、不写 passed 到数据库。手工 claim 用例中真实 claim/竞争/fence 检查仍保留；需要评分来源的场景由测试 fixture 显式提供受控 worker launch 事实，不伪称真实 CLI。若生产接口无法容纳这一边界，停止提交详细设计，不能增“test mode”。
- F02：受控执行主控 driver 在收到本候选审查结果后才通过 CLI 给测试固定评分；`integrate` 参数由夹具显式提供并保存 argv。缺分反例明确不调用该 helper，避免适配器给每个调用偷偷补分。run 的 driver 不接管替换 attempt。
- F03：verify 后的 fixture 显式等待 review_result，再让原观察继续；超时失败，不伪造 verified、不屏蔽拒绝。旧 runtime 的 worker prompts/closes 与 reviewer 专用事件分开，但原 worker 数量/归属断言仍保留，新增检查确保 reviewer 确实存在。
- F04：测试结果按真实边界标注：受控 reviewer 的 8/9/18 是“真实后台+真实 Git+受控外部会话”回归，不能继续全称 default-production-runtime 或真实模型证明。真实 reviewer 由本卡端到端正例单独证明。

每个批准的 hunk 在 `assertion-hunks.md` 对应 W/F 编号、规格原句、起点业务红态与候选绿态；起点上不能因缺新 CLI 参数/字段报 usage 就算新行为红态。红态先用旧入口可表达的信号观察缺失行为，再对新增接口用明确已知坏变异体证明拒绝。若主控要求每个全新入口本身在起点跑通后业务失败，需要先批准纯入口支架阶段，不能虚称起点存在该入口。

## 8. 红态、六类反例与实施顺序

实施前按 `evidence-first-testing` 保存真实入口红态；原输出只追加，新标签不覆盖。缺 socket、导入错误、程序不识别参数、缺外置盘均为环境/夹具失败，不作为产品红态。

**Tracer bullet**：先在保留的生产路径连起“显式 submit → 完成条件拒绝 → 已登记的 gate 回写 → 同原生会话重交 C2 → 机械通过 → fresh reviewer → 明确结论 → 主控带分集成”，再加宽红态、规则、三次停止、非法结论、打分格式与恢复。真实模型只在受控测试与最高风险通道探针满足后调用，不先堆完一层才接下一层。

| 编号 | 起点缺口/红态信号 | 候选正例、反例与独立读回 |
| --- | --- | --- |
| R-chain | 现有 verify 不执行红态/规则且机械即 verified | 事件顺序严格为 path→completion→red→rules→trailers→review；先失败项后的项未执行；M、C、B 按 Git 独立读回 |
| R-red | argv 在 B 不失败仍可通过旧 verify；候选测试未移植 | 真新增业务测试：B+测试失败、C 通过；反例1：B也通过必拒；C失败、漏测试、symlink/越界声明拒绝；证明 B 生产文件仍是 B 的内容 |
| R-rules | 独立配置明确失败命令，旧 verify 仍通过 | 反例2：lint/type 命令非零即拒且无 reviewer；配置先冻结、候选删除/改配置不能取消检查；未配置明确不适用 |
| R-feedback | 首次完成条件失败无修复登记；C2 被 candidate_conflict/旧交付turn 拒 | 首拒消息与原生输入一致、不是人工介入；同 attempt/原生会话修好重交；未获打回的换 C、伪 session/fence/leader 仍拒 |
| R-limit | 重复有效交付失败没有 attempt 级停止语义 | 反例6：三个独立 submission 失败后只送前两条修复消息，第三次生成 issue/暂停；重放与重启不重计、不再发，Git不变；忙时队列不穿透停止点 |
| R-review | 起点无 reviewer 也可 integrate | 真新 reviewer 按卡审候选；反例3：writer/旧 reviewer/续接原生会话各被拒；反例4：结论 C 不符被拒；非法结论/重复请求/过期合同/未匹配 Stop 均不推进 |
| R-review-fix | 起点无“需修复”反馈 | 新会话给 location/场景/建议，原文回写 worker；C2 全检查、新 review；受控证据不冒称模型审查能力 |
| R-score | 起点无 score 的正常 integrate 成功 | 反例5：缺分/缺字段/非法分数/来源混淆拒绝且不改 ref；合法通过集成、合法放弃/升级终结、每 attempt 一分；CAS前后中断恢复不重复或篡改分 |
| R-run-finalize | 起点机械通过自行 integrate；首拒 reclaim | 明确等 reviewer/主控；预算/期限到达不接新 attempt；ACK后身份仍能核对，原 leader/native 反例保留 |
| R-score-format | 起点没有后台 schema 对齐验证能力 | 双方校验器接受固定独立样例；重复attempt、错误user引用、缺七键、放弃带分/事实均拒绝；只读真实文件，不写回 |
| R-regression | 本卡新入口/协议可能影响 8/9/18、T-075与T-076-1 | 当前候选上完整重跑 8/9/18（0 fail/error/skip），任务卡/daemon正反例、多回合与五类变异体；旧 PASS不迁移 |

六类反例主要用脚本控制输入、真实 CLI/后台/Git 留事件，零模型回合；“独立性”反例还在真实 reviewer 正例产生的身份上做外部错误请求，不能靠 fake record 证明真实新会话。每个新测试须在起点/撤销相关变更/定向变异体上被业务断言击中，记录准确原因；没有证明的标 INCOMPLETE。

同一失败出现为待实现的新契约红态可按批准计划推进；发现既有产品真实协议异常、额外缺陷或无法判定结果，则依任务卡立即交主控，不擅自修。探针/测试自身错误可修，保留原失败与修正记录。

## 9. 真实 Codex 回合预算：总计最多 8

下表涵盖被测 worker 与产品 reviewer；都用 `gpt-6.1-sol`、xhigh、Fast 请求。预算按主输入/原生主 turn 核对，未知已发输入保守占一名额；不把 ACK、纠错、意外 continuation 算成免费。辅助通知另记但不拿它当新主 turn。所有后台共用本卡外部预算账，不因换 state/home 或重新启动归零。

| 槽位 | 会话/用途 | 产物及约束 |
| --- | --- | --- |
| 1 | P-review：新 read-only reviewer 的通道探针 | 读取固定候选、执行一次向自建 disposable sentinel 的写入负例（必须被拒且字节不变），显式 JSON 经匹配 Stop→B落库；无 Git写授权、无直接socket。也是旧实现 reviewer能力缺失的对照，入口缺失本身不冒充业务红态 |
| 2 | worker 主回合1 | 按预写任务制造一个明确会被独立完成条件拒绝的 C1，提交并显式 submit；不改 oracle；中等难度夹具含边界输入及独立 G 提交 |
| 3 | worker 回执1 | 仅确认 B submit 回执，不调用工具；之后执行主控触发 verify，首拒进入自动 gate 回写 |
| 4 | worker 修复回合2 | 因 `⟦门禁 #n⟧` 修复 C1、测试、提交 C2、显式重交；原 attempt和原生会话不变 |
| 5 | worker 回执2 | 仅确认第二次 B 回执；核对交付turn仍绑定修复回合，不被ACK改写 |
| 6 | 新产品 reviewer 正例 | 在 C2 新建只读会话，实际审阅任务卡/候选/机械证据，交付结论；不在提示里强制“可合并”。可合并才由主控带分集成；需修复/无法核实时停交主控，不强制改结论 |
| 7 | 预留：经主控另行分配 | 仅处理第6槽真实需修复后的 worker 修复，或已查明夹具问题后的单回合复验；不是自动重试许可 |
| 8 | 预留：经主控另行分配 | 第7槽所必需的后续；若需要 ACK+新 reviewer 超过剩余预算，则不启动半条闭环，报告 INCOMPLETE。不得花第9个主turn |

正常目标消耗6个主turn，预留2个不自动使用。P-review 成功后该 reviewer 不可复用于第6槽，正好提供“旧 reviewer 不能续用”的真实身份。机械红/绿、六类错误调用、变异体、格式校验与8/9/18使用受控边界，不花模型回合。

本卡自身交付的一次 fresh-context 只读独立审查是另一件事：冻结候选后按任务卡显式授权新开独立审查 agent，使用 `behavioral-acceptance-review`，结构风险在同一次审查覆盖；不继承实现聊天、不写候选、不 submit、不集成，不开被测 Codex CLI。单独登记其模型/实际可见配置，不冒称已核实 Fast。若改用真实 CLI，必须计入这8槽并先让主控批准重分配，不能额外隐瞒模型预算。

## 10. 沙箱外交接、验证与交付

获批后准备本目录 `outside-sandbox.sh`；它按显式阶段和全新 label 运行，不一次性把后续全部跑完，不自动重试。需要沙箱外的项统一在此脚本中：

1. 固定版本/外置盘检查；冻结起点/候选源码与 harness；保存完整版本、输入、argv/cwd、stdout/stderr、退出码和差异。缺挂载直接报错，不安装到内置盘。
2. Unix socket、node-pty/zsh、ps/进程组、后台启停和信号；所有服务脱离调用者进程组，显式隔离 `/tmp` state，先核实身份，只停本阶段自建进程。
3. 冻结起点的契约红态，以及受控 reviewer/worker 的新反例；新接口无基线实现时报告缺失并以业务变异体补证，不把 usage 错算红态。
4. P-review 真实探针；配置/argv/hook 授权未核实不启动。probe失败或出现批准窗口即停；不注入 Enter 代批准，不修改权限。
5. 实现后 focused green 与已知坏变异体；运行结果逐项回交主控。每一步前有 corresponding red，新增失败保留。
6. 六回合真实正例；独立读回数据库事件/launch/native turn、G/C/M父提交与工作分支、评分payload、dispatch原文及人工介入。真实完成条件的答案预写在候选外，不从实现生成。
7. 候选8/9/18与T-075/T-076-1相关回归；检查器如实报告已知无法重建表与attachment缺口，不借此修存储。
8. 保存必要原生记录及证据，再清理本阶段自建隔离CODEX_HOME（含auth副本），不把凭据入证据/归档/Git；其他失败现场按规则保留。压缩或把>5 MB文件归档到外置盘，提交摘要/路径/重放命令。

本卡不需 Electron，除非主控另改验收；不运行/修改用户正式服务，不读写默认工作台目录。worker不申请提权；脚本可审阅后回复 `T-076 OUTSIDE-SANDBOX READY` 并停下，由执行主控运行。本文交付时该脚本尚未编写或声称可运行。

拟交付文件/顺序：批准计划 → 新测试与红态交接 → 按阶段实现 → 绿态/反例/回归 → 冻结候选 → 一次fresh-context只读审查。审查发现问题先红态，修复diff交主控；不自行追加追审或改断言。最后更新中文RESULTS和T-076 Resolution（逐条证据、保持open、待主控关闭），只提交本卡文件，提交带尾注，不push。

所有报告附可重新生成的确切命令；未来阶段命令在脚本存在后冻结，当前不编造“已经跑过”的命令。提交前 `find evidence/2026-10-11-batch13/T-076/card-2 -size +5M`、`git diff --check`、文件编码回读和project-map status；stale文档限授权范围内处理，地图Verified交主控。

## 11. 本轮计划检查与停止

已读取 AGENTS、CONTEXT、intent第三阶段、MAP、T-076/T-077、native spec、T-075 rev4/B决定、相关core/CLI/Panes/relay/score及旧断言。开始与结束时project-map status均为Problems=0、Stale=0；结束命令与原始输出见 `plan-status.json`。新文档已按UTF-8无BOM回读，未见替换字符或CRLF扰动。

本轮真实Codex用量 **0/8**；产品测试未运行，未取得红/绿态或产品通过结论。正文P1–P5、白名单及P-review探针待执行主控批准。按主控 #30 交付后停止，不进入实现。
