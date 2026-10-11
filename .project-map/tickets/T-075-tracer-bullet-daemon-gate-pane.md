---
id: T-075
title: tracer bullet：编排后台、门禁、Codex worker 窗格、最小 Electron 窗口跑通一次交付
type: build
status: open
blocked_by: [T-074]
claimed_by:
supersedes:
ready: yes
ready_by: ideation
ready_rev: 4
---

## What to build

[spec](../specs/native-cli-orchestration-2026-10-10.md) 第 12 节切片 S1（第 0 步已拆到 [T-074](T-074-pane-signal-and-injection-facts.md)）。穿过每一层跑通一条最薄的、留在生产路径上的完整路径，之后的切片在它上面加宽：

1. **编排后台**：常驻进程，脱离调用者的进程组；对外一个本地命令行入口，主控、worker 和界面都经它。
2. **门禁进后台**：从 fork 的 `packages/a2a-gates` 搬进来，替换两处 Synara 依赖；契约不变，加上 T-070 同意的改动中本切片需要的三项：路径边界检查、提交尾注核对、集成目标改为项目工作分支。搬完后 fork 的门禁不再作入口，`acceptance/entry/a2a_gates.py` 改指新位置，不保留两套路径。
3. **任务卡**：命令生成与校验（缺字段、完成条件不是命令就拒收），存进后台库，门禁在任务注册时快照。
4. **一个 Codex worker 窗格**：node-pty 托管、窗格里跑用户的 zsh，带启动记录与 spec 第 5 节的环境变量（提交带尾注）；派发文字以 `⟦主控 #序号⟧` 写进窗格并登记。
5. **一次交付**：认领、交付、机械检查（路径、完成条件、尾注）、验收、CAS 集成到夹具仓库的工作分支，不 push。
6. **原始事件入库**：spec 第 8 节清单里本切片涉及的事件全记，只追加。
7. **最小 Electron 窗口**：从 fork 搬组件与样式（保留 MIT 声明），显示一个项目、一个任务、一个窗格（xterm.js）和门禁状态。

## Acceptance

- [ ] 检查面（用户 2026-10-10 确认）：从编排后台的命令行入口发起，驱动真实窗格里的真实 Codex worker（隔离 `CODEX_HOME`，turn 数尽量少），对夹具仓库走完整个门禁。证据：命令与输出、从库里读回的事件、Git 引用读回、Electron 截图。
- [ ] 正例：上面一次交付集成成功，工作分支从 G 前进到 M，事件齐全，候选提交带本 attempt 的尾注。
- [ ] 反例，各自在真实入口上被拒且留下事件：改了任务卡禁止路径；完成条件命令失败；候选里有别的任务的尾注；没有尾注的提交记为人工介入并标"推断：缺尾注"；过期 fence 或旧 attempt 交付。
- [ ] 门禁移植重新证明：交付 8 项、恢复 9 项、编排 18 项场景在新位置重新取得红态、绿态与反例；旧实现的通过结论不替新实现背书。
- [ ] 后台常驻：关掉 Electron 窗口后 worker 窗格照常跑，重开窗口能重新接上；后台重启后按恢复语义处理进行中的 attempt。
- [ ] 窗格状态只来自结构化信号（按 T-074 的结论），拿不到的显示"未知"，不读屏。
- [ ] 外置盘未挂载时构建报错，不回退到内置盘；工作台数据目录在内置盘，路径在 RESULTS 写明。
- [ ] 不写 `~/.claude`、`~/.codex`；不改用户的 Herdr server 与正式工作台数据目录 `~/Library/Application Support/a2a-workbench`。
- [ ] 每项保留产物与重新生成的命令；`project_map.py status` 0 problems。

## 说明

- 本票不做（后续切片）：独立审查会话、红态检查与规则式检查、打回回写（S2）；worktree 命名清理与冲突回写（S3）；主控窗格、收件箱进库、唤醒（S4）；面板、通知、设置页（S5）；复盘与指标视图（S6）。路径检查与尾注核对要做，因为它们属于门禁本身。
- 新目录名、数据目录路径、Electron 与 node-pty 版本由执行主控定，记进 RESULTS；新目录建议 `workbench/`。
- 体量大：执行主控可以拆成几张任务卡串行做，同一文件只给一个写入者；不必再拆票。目标、验收或设计级的问题停下写 `needs-decision`。
- worker 窗格按 spec 第 6 节"批准与派发分开"一条启动：审批设为不问，派发用 bracketed paste 后单独回车（T-074 实测）。
- T-074 的结论要求改设计时，本票等构思主控出 `revise` 再开工。
- 风险 R8（主控常直接提交 `main` 导致 CAS 反复落空）在本切片只用夹具仓库，不处理上限，留给 S3。
- 授权来源：用户 2026-10-10 在会话"a2a-构思主控"确认切法与检查面（逐字："确认"），在此之前在会话"新思路构思"说："确认，写完文档后，你这边就不用了，全权交给构思主控去安排执行主控安排子 agent 去做。"`ready_by: ideation`，`ready_rev: 1`。

## 修订 rev 3（2026-10-11，用户决定）

依据 needs-decision `20261011T041853Z-executor-needs-decision-001` 与存储缺口上报 `20261011T040449Z-worker:s12-t075-3-issue-001`：

- **交付通道选 A**：worker 的每会话启动参数只放行编排后台那一个 Unix socket，网络保持关闭，worker 经同一个命令行入口交付（spec 第 5 节）。追加验收：同一沙箱里连别的 Unix socket、发起网络连接仍被拒；只放行一个这件事不成立就停下报告，不改用文件中转。
- **门禁状态表**：按 spec 第 9 节的例外处理，本票不改门禁存储；新加的表只追加。"由事件重建状态与状态表一致"的检查留给后续切片。

## 修订 rev 4（2026-10-11，用户决定）

依据 needs-decision `20261011T043544Z-executor-needs-decision-001`：关闭托管网络代理时 `network.allow_unix_sockets` 不生效。与 rev 3 冲突处以本节为准。

- **先试 A2**：开 Codex 托管网络代理，域名名单留空，只放行后台 socket；1 个回合验证：后台 socket 能连；另一个 socket、任意 TCP、任意外部域名仍被拒；不弹批准。
- **A2 不过就改走 B，不再回来问**（用户选"A2 开代理试一次，不过改文件中转"）：沙箱不动，worker 在自己的 worktree 里写交付请求文件（显式 submit），由回合结束的 hook 转交后台；查状态、上报问题同样走这条路。交付仍须是 worker 显式发起；hook 只转交、不替 worker 决定；转交结果写回 worker 窗格。rev 3 的"不改用文件中转"一句作废。
- 选了哪条、为什么，写进 RESULTS 与 spec 第 5 节需要的改动说明（spec 由构思主控改）。

## Resolution

T-075-1：门禁迁移、隔离验收和一次 fresh-context 独立审查均 PASS；收尾状态 INCOMPLETE，仅剩执行主控已接管的 CONTEXT.md stale。保持 open，待后续卡、待主控关闭。

- 源码候选：`4d81efcacdaa6f8d9cf2b6127130fd7f0f0ac754`，自动 `A2A-*` 尾注已核对；来源固定为 `49cae984f22924de006e0f8358cb447eb881aaf6`。
- 新门禁位于 `workbench/`，Node 26.5 原生 TypeScript；验收入口改到新位置，不依赖 fork 门禁。按主控决定删除旧 HTTP 转接，保留 GateRuntime 边界，未改 T-075-2 的三项契约。
- 三套红态已保存；最终交付 8/8、恢复 9/9、隔离编排 18/18 全过，CAS 补充正例 1/1 全过。fence、CAS 期望旧值、操作锁三个变异体均因业务断言失败；旧交付套对 CAS 变异体误过的记录保留。
- 审查原文及重现命令见 [RESULTS](../../evidence/2026-10-10-batch12/T-075/RESULTS.md)；独立审查对上述候选给出 PASS，无需修复项。此结论不证明真实窗格、模型、后台或 Electron 可用。
- 地图检查为 0 problems、1 stale，退出 1；按执行主控决定 01 由主控更新术语表及 Verified，worker 未越界修改。完成该收尾后可将本卡记为“T-075-1 完成，待后续卡”。

**T-075-1 执行主控验收（2026-10-11）：卡片通过，ticket 仍 open（4 张卡中的第 1 张）。** 交付 a2a `4d81efc`（实现）和 `5fb7009`（报告与审查），提交带 9 项尾注。
- **门禁已搬家**：门禁在 `workbench/src/gates/`，用 Node 26 运行。对 Synara 的引用已清零，旧的 HTTP 转接分支已删除；`acceptance/entry/*` 改指新位置，`acceptance/test_*.py` 的断言没有改。
- **依赖**：effect 改用 npm 官方源的 `4.0.0-beta.25`，由执行主控安装，缓存在外置盘。
- **重新证明**：沙箱外由执行主控代跑，收据在 `evidence/2026-10-10-batch12/T-075/outside-executor.K2MrEb*`。
  - 正例：交付 8/8、恢复 9/9、编排 18/18。
  - 反例：去掉 fence、CAS 期望旧值、操作锁的三个变异体都失败，而且是断言失败，不是环境错误。
  - 已知缺口：旧交付套件抓不到 CAS 变异体，已由新增的 `workbench/tests/test_cas_race.py` 补上。
- **独立审查**：PASS。
- **文档**：`CONTEXT.md` 和 `AGENTS.md` 里门禁入口的事实已由执行主控更新（`c94d388`）。
- **打分**：已记入 `records/scores.jsonl`（score-dd335ff3）。

**T-075-2 完成，待后续卡，待主控关闭（2026-10-11）：PASS。** Ticket 保持 open；本卡只完成三项门禁契约改动与任务卡命令，不代表整张 T-075 已完成。

- 实现提交：`1273b17e933cd0bb279a20e6b237dbbd2f054db3`；审查修复提交、最终代码版本：`3386c4cd3a4e44b5b58d5a46a780fb99f9aa637a`。两次提交均带九项 `A2A-*` 尾注。
- 任务卡 JSON 的生成、校验、版本入库、注册快照和认领绑定已接入唯一 CLI。交付检查路径、M worktree 内的完成条件和提交尾注；无尾注提交记为来源“推断：缺尾注”的 action 用户输入及人工介入；外任务尾注拒收。集成以 CAS 推进项目工作分支，在实际检出目录保护未提交修改，不再读写 `refs/a2a/integration`。
- 修复版本经执行主控在沙箱外复验：交付 8/8、恢复 9/9、编排 18/18、任务卡 14/14，加双命令中断、目录更新后中断、CAS 竞争各 1/1，合计 52 项正例通过。五个变异体（路径、外任务尾注、脏目录、快进、CAS）均为业务失败，0 errors。缺尾注 action/人工介入：coop 4/4、recovery 9/9、run 9/9。
- 一次 fresh-context 只读独立审查原始 FAIL，唯一 P2 为第二条完成条件中断时串用第一条结果；先取得真实 CLI 业务红态，再修复、转绿并跑完整回归。未追审；执行主控 `⟦主控 #22⟧` 明确审过并同意 `3386c4c` 修复 diff。原始 FAIL 和全部失败现场保留。
- 完整报告、重现命令及证据索引见 [T-075-2 RESULTS](../../evidence/2026-10-10-batch12/T-075/card-2/RESULTS.md)；最终回归收据为 `card-2/outside-review-green.SC1xPN`。地图检查 0 problems、0 stale；`workbench/README.md` 的地图登记由执行主控在最终提交后处理。

接下来：T-075-3，编排后台与 Codex 窗格，跑通真实交付；随后 T-075-4 最小 Electron 窗口。

**T-075-2 执行主控验收（2026-10-11）：卡片通过，ticket 仍 open（4 张卡中的第 2 张）。** 交付 a2a `1273b17`（实现）、`3386c4c`（审查修复）、`1eb748c`（证据），提交均带 9 项尾注。

门禁新增的行为：
- 任务卡：用 `card_template`、`card_validate`、`card_save`、`card_show` 生成、校验和保存。任务卡是 JSON，13 个字段，完成条件写成 argv 命令。注册任务时拍快照，起点提交和唯一写入者在认领时绑定。
- 路径边界检查。
- 提交尾注核对：外来任务的尾注一律拒收；没有尾注的提交记为人工介入，标“推断：缺尾注”，不阻止集成。
- 集成：用 Git 引用事务加双树快进，从工作分支 G 用 CAS 推进到 M。会覆盖未提交改动时拒收，不 stash，也不 reset。`refs/a2a/integration` 已停用。

验证（沙箱外由执行主控代跑，收据见 `evidence/2026-10-10-batch12/T-075/card-2/outside-*`）：
- 既有三套测试（8/9/18）全部通过。断言只改了 A1–A10 白名单里的项，我抽查过 diff。
- 新增正例共 52 项，全部通过。
- 路径、外来尾注、未提交改动保护、快进、CAS 五个变异体都在业务断言上失败，0 errors。
- 三个 Git 中断窗口探针 182/182 通过。
- 独立审查 FAIL 一项，问题是“中断时复用了上一条完成条件的结果”。先拿到红态，再用两行修复，修复 diff 我审过。

收尾：
- `workbench/README.md` 已登记为 living doc。
- 打分已记入 `records/scores.jsonl`。

下一张：T-075-3，做编排后台、Codex 窗格和一次真实交付。

**T-075-3 完成，待后续卡，待主控关闭（2026-10-11）：PASS。** Ticket 保持 open。实现与首批证据提交为 `93a707299d3f50309b52bfafacfd9d6529794130`，九项尾注齐全，A2A-Launch 为本 worker 的 `launch-dcd075b4fa8d4d1b86c3334de6ff59e0`；其后收尾提交只更新文档，完整交付号在终端 DONE 行报告。被测源码是 `outside-b-06/workbench-source.tar.gz`，base HEAD `471fa75f7f28531e035479c795b043bb6cbc15f2` 加当时未提交变更，不能只以该 base HEAD 代指候选。

- 后台常驻并脱离调用者进程组；唯一 CLI 连接后台门禁。node-pty 托管交互 zsh/Codex，派发先登记再注入，结构化信号驱动状态；新增编排、启动、派发及转交表只追加。
- 最终走 **B**：A2 没验证成，按决定 04 改走 worker 显式请求文件、Stop hook 经同一 CLI 转交、门禁回执写回窗格。网络与代理保持关闭。请求目录在 attempt 专属 `/tmp`，不进入候选提交。
- 执行主控在沙箱外跑 b-06：relay-cli、relay-core PASS，后台门禁 15/15 PASS；真实 Codex gpt-6.1-sol/xhigh、Fast 请求，用一个交付回合加一个回执回合完成 submit、verify、CAS integrate。累计 7/10，按主控 #32 不再追加。
- 独立 Git/SQLite 读回：G=`51d612b486c6935fe1616e001507eeeb47bafbe1`，C=`641e55b8d005281c672f544ebec1c8814ab87a53`，M=`287bbf8ae5eeadc901198233eeb0a0ac84f02b9e`；main=M，M 的父提交为 G、C。C 有本 attempt 九项尾注，2 个文件、增加 51 行、删除 2 行；库中集成事件一致。
- 一次 fresh-context 只读独立审查 **PASS**，没有修复项或追审；审查者另查未见输入、真实库和 Git。完整原文、反事实及历史失败见 [RESULTS](../../evidence/2026-10-10-batch12/T-075/card-3/RESULTS.md)。审查后只更新文档，产品逻辑不变。
- 已知缺口：A2A-Model/A2A-Effort 为 unknown，按 spec 允许；原生记录另有实际模型与强度。后续需将最近回合的已核对事实传给钩子，区分启动请求和实际观测；本卡不新增真实回合补这一项。旧 run/reclaim 的回合绑定、事件重建状态视图等已上报，未声称通过。
- 本卡只验收隔离 Tracer bullet，不含 Electron、后台重启恢复、旧 8/9/18 全套后台适配或 S2–S4。隔离 home 已删除，未写全局配置、正式工作台目录，也未 push。下一张为 T-075-4。

**T-075-3 执行主控验收（2026-10-11）：卡片通过，ticket 仍 open（4 张卡中的第 3 张）。** 交付 a2a `93a7072`（实现与证据）和 `7c4bf88`（收据）。实现提交带 9 项尾注，`A2A-Launch` 指向本 worker 自己的启动记录。

做出来的东西：
- **编排后台**：`workbench/src/daemon.ts`，常驻运行，脱离调用者的进程组，对外只有一个命令行入口（Unix socket）。
- **node-pty 窗格**：`panes.ts`，在 zsh 里启动交互式 Codex，用“不问”模式；用 bracketed paste 加单独回车派发，派发文字先登记再写入。状态只认 UserPromptSubmit 和 Stop 两个 hook。
- **库**：新增的启动记录、派发、编排事件等表放进 `state.sqlite3`，只追加。门禁的状态表按 spec 第 9 节例外，视为由事件推出的当前视图。
- **交付通道 B**（T-075 rev 4）：worker 在本 attempt 专用的 /tmp 目录写请求文件，Stop hook 经 CLI 转交，门禁回执先登记，再以 `⟦门禁 #n⟧` 写回窗格。改走 B 是因为 A2（托管代理加单 socket 放行）没有验证成：被测 Codex 在工具层就拒绝了外网测试命令，脚本没有跑起来。

验证（沙箱外由执行主控代跑）：
- `outside-b-06` 全部 PASS：relay-cli、relay-core、后台入口上的门禁正反例 15/15。反例包括请求身份不符、请求不完整、同一请求重复转交不重复处理。
- 真实 Codex worker 完成一次交付和集成。我在夹具里独立读回：`main`=M=`287bbf8`，父提交为 G `51d612b` 和 C `641e55b`，C 带 9 项尾注。
- 一次独立审查 PASS。

真实回合与额度：被测 Codex 共用 7/10 个真实回合。其中 1 个回执回合是用户在 worker 窗格里批准的（原话“允许额外 1 个回执回合，完成后停止”）。

已知缺口：
- **尾注模型字段**：受管被测会话的尾注里，`A2A-Model` 和 `A2A-Effort` 是 `unknown`，因为钩子在沙箱里连不上后台。可以把启动记录里的值预先写进环境来补。
- **多回合与回收的身份绑定冲突**（已转交构思主控）：门禁把 attempt 绑定到交付那一回合，回执回合出现后，旧的回收检查可能判为身份冲突。
- **git 命令要单独执行**：受管 worker 的 `git add` 和 `git commit` 必须各自单独执行，否则匹配不上前缀放行规则。这一条已写进派发提示。

收尾：
- 隔离 CODEX_HOME 有两次因为探针收尾缺陷没有自动删除，执行主控确认没有存活进程后手动删除；探针随后已修复。
- `workbench/README.md` 的覆盖范围扩到 `workbench/src/**` 和 `workbench/hooks/**`。
- 打分已记录。

下一张：T-075-4，做最小 Electron 窗口和常驻行为（关掉再开能重新接上，后台重启后的恢复）。

**T-075-4 完成（2026-10-11）：PASS，待主控关闭。** Ticket 保持 open；一次 fresh-context 独立审查原始 FAIL，唯一 P2 为 Electron 首次安装缓存回退，已先红后绿修复，主控 #45 已明确审过并批准三文件修复 diff，未追审。本结论采用主控 #44／#45 批准的证据组合，不改写 live-04 原始 INCOMPLETE。完整中文报告、限制及全部失败见 [card-4/RESULTS](../../evidence/2026-10-10-batch12/T-075/card-4/RESULTS.md)。

T-075 Acceptance 逐项证据位置与边界：

| 验收项 | 证据 |
| --- | --- |
| 从后台 CLI 驱动真实 Codex、完整门禁、事件、Git、Electron | 卡 3 [RESULTS](../../evidence/2026-10-10-batch12/T-075/card-3/RESULTS.md) 的 outside-b-06 完整真实交付；本卡 [live-04](../../evidence/2026-10-10-batch12/T-075/card-4/outside-live-04/) 补齐 capturePage 截图和真实窗格生命周期。是分卡组合证据，不声称同一次运行同时完成交付与重启 |
| G→M、事件、候选尾注正例 | 卡 3 outside-b-06：G=51d612b、C=641e55b、M=287bbf8，独立库与 Git 读回、九项尾注；见其 RESULTS 完整提交号 |
| 禁止路径、失败完成条件、外任务尾注、缺尾注人工介入、过期身份反例 | 卡 2 [RESULTS](../../evidence/2026-10-10-batch12/T-075/card-2/RESULTS.md) 与 outside-review-green.SC1xPN；卡 3 outside-b-06 的后台门禁 15/15；本卡 outside-checks-01/02 同套后台回归通过 |
| 门禁迁移 8/9/18 重新证明 | 卡 1 [迁移 RESULTS](../../evidence/2026-10-10-batch12/T-075/RESULTS.md)、卡 2 收尾三套全过及变异体；本卡增加真实后台 recovery 5/5。旧记录各自绑定当时版本，不把它们写成最终候选重新跑过全部旧场景 |
| 关窗不停止、重开补回、后台重启 | live-04/lifecycle 的 closed-output-readback、独立 ps、reopened-backfill／reopened-live 字节对照、restart-readback、SQLite 与 interrupted-original-attempt.png。停止后原生记录遗漏按主控 #44 用 native-final-red-01 → native-final-green-01 的九项离线场景修复；live-04 原 contexts 断言失败保留 |
| 状态只来自结构化信号，不读屏 | live-04/offline-trace：中文跨块、诱导文字／OSC、普通／备用屏幕切换；门禁仍 claimed、窗格 unknown。终端只读方案已获批准，用户输入链归 S4 |
| 外置盘构建／缓存，内置数据目录 | live-04 build manifest 正例；outside-checks-01/02 的缺盘、普通目录反例及 cache-readback；Electron 安装缓存反例 review-cache-red-02 → review-cache-green-01。默认数据 a2a-orchestrator，本卡全部运行目录为 /tmp 隔离夹具 |
| 不写全局配置、Herdr 或正式工作台 | 本卡运行仅自建后台／Electron；隔离 CODEX_HOME 只复制 auth，live-01/03/04 均清理；无真实回合追加、无 push。正式 Synara PID 未操作 |
| 产物、重现命令、地图健康 | card-4/RESULTS 每段有命令、原始输出和限制；完整仓库的 delivery-precommit-01、delivery-code-01 保存提交前后 0 problems、0 stale 收据。review-candidate-01 是不完整冻结包，其 49 problems 不代表实际仓库结果 |

本卡真实回合累计 3/4，按主控 #44／#45 没有追加。现有界面／后台核心证据与最后采集离线修复经独立审查核对；五类计划产品变异体未全部执行，已明确披露，不冒称完成。实现与证据提交为 `5aad35e6dfe76036f3b757dd047122788aa6d7f2`，九项尾注齐全；提交后 0 problems、0 stale，读回见 [card-4/delivery-code-01/receipt.json](../../evidence/2026-10-10-batch12/T-075/card-4/delivery-code-01/receipt.json)。最终收据提交号以 DONE 行为准。非阻塞 issue `20261011T080957Z-worker:s12-t075-4-issue-001` 的 README Covers 登记留主控处理，worker 未修改地图。

**T-075-4 执行主控验收（2026-10-11）：卡片通过，ticket 仍 open。** 交付提交为 a2a `5aad35e6`（实现与证据）和 `7bcfe7d9`（收据），实现提交带 9 项尾注。

我核对过的内容：
- **截图**（live-04）：
  - `live-before-close.png` 显示真实 Codex TUI，状态为“忙”，门禁为“已认领”；
  - `interrupted-original-attempt.png` 显示后台重启后能回放历史，窗格状态为“未知”，执行为“已中断”，门禁保持“已认领”；
  - 离线检查通过：中文跨块、不读屏。
- **独立审查**：结论 FAIL，只有一项 P2，即 Electron 首次安装时缓存回退到内置盘。worker 先做出红态再修复，修复 diff 由执行主控审过并同意。
- **中断时原生记录漏采**：这是产品缺口，已修复，用离线测试证明，结果从红态转为绿态，9/9 通过。
- **真实回合**：用了 3/4。

还不能关闭 T-075 的原因：验收第 4 条要求“8/9/18 场景在新位置重新取得红态、绿态与反例”，在最终入口上没有满足。执行主控在 `7bcfe7d9` 上用 `run-acceptance.py` 复跑三套测试（证据在 `card-4/executor-final-{coop,recovery,run}-01`）：
- coop：8/8 失败；
- recovery：9/9 失败；
- run：18/18 失败。

失败原因都是 `daemon_call_failed: Unix socket path exceeds 103 bytes`。T-075-3 之后，CLI 只能经后台访问，而旧测试既不启动后台，临时路径也太长。卡 1、卡 2 当时的通过结论只对那两个版本有效，不能替最终入口作证。

下一步：另开 T-075-5，只在 `workbench/tests` 里加生命周期适配（每个测试用很短的路径启动隔离后台），不改 `acceptance/` 的任何断言，让 8/9/18 在最终后台入口上重新取得红态、绿态与反例。

其他收尾：
- 卡 4 计划中的五类产品变异体没有全部执行，worker 已在 RESULTS 中如实写明。
- `workbench/README.md` 的覆盖范围扩到了 `workbench/app/**` 和 `workbench/package.json`。
- 打分已记录。

**T-075-5 业务完成、收尾 INCOMPLETE（2026-10-11），待主控关闭。** Ticket 保持 open；只补 Acceptance 第 4 条的当前证据，不改验收条件或勾选其他项。D1/D2/D3 经主控 #47 批准：产品只导出同一 serve 并加默认值不变的内部构造参数；后台故障只注入自建且核对过的后台；编排十三项为隔离线程服务、五项默认 Panes。

- 当前完整运行：主控 #51 已运行并核对 `card-5/outside-full-01`，交付 8/8、恢复 9/9、编排 18/18、CAS 补充 1/1，全为 0 failures/errors/skipped。旧三套 35 项在同一最终 CLI 上先取得 socket 超长入口红态；入口红态没有被当成业务红态。
- 三个本候选单点变异体都在原业务断言处失败，0 errors：错 fence=32 被错误接受；CAS 去掉旧值后覆盖外部写入；操作锁去掉事务后启动第二 oracle 且并发 integrate 成功。原始测试的 INCOMPLETE/exit 1 保留，协调器只另判反事实成立。
- 全部业务请求经最终产品 CLI→Unix socket→同一生产后台请求处理器→真实门禁。SQLite/Git 原断言、独立分页 oracle 和三份 `acceptance/test_*.py` 相对 `7bcfe7d9` 的 diff 为空；CAS 用既有后台生命周期子类，单独计数。
- 实际执行源码为 `outside-full-01/sources.tar.gz`：base HEAD `2d7d416790e59b2082c9c5bd531b8505c3b4ac6f` 加本卡变更，阶段源文件未变化；随后 `review-candidate-01` 与其 46 个源码逐字节一致。最终提交与此候选的绑定检查见 card-5 的 delivery 收据，完整交付号见其 RESULTS／DONE 行。
- 一次 fresh-context 只读独立审查原始 **STATUS: INCOMPLETE**：限定业务 claim **PASS**，没有新修复项；仅 `workbench/README.md` stale 的交付收尾未完成，主控 #51 已明确接管。没有二次审查，worker 不上调结论。
- 原 P1 读回夹具失败先保留，再把只读快照改为停后台前保存至证据目录、事后只汇总 JSON，独立夹具红绿成立，outside-probes-02 三探针实跑通过。首次合成 writer 超时及 worker 提权请求被 Esc 拒绝的记录保留；后续 ps／清理只由主控在沙箱外执行，没有真实被测 Codex 回合或 push。
- 报告和重现命令：[card-5/RESULTS](../../evidence/2026-10-10-batch12/T-075/card-5/RESULTS.md)，审查原文：[review-01](../../evidence/2026-10-10-batch12/T-075/card-5/review-01.md)。编排十三项不证明真实 PTY/Codex/B；本卡不覆盖 UI、S2～S5、生产、可靠性或成本。
- 当前地图 0 problems、1 stale、退出 1；代码与业务证据已交付，README／Verified 收尾由主控处理。状态保持 INCOMPLETE，待主控完成该项并关闭 T-075。
