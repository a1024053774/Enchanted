---
id: T-074
title: 先核实两个事实：Codex 的"等确认"信号，往窗格注入文字是否稳定
type: build
status: open
blocked_by: []
claimed_by:
supersedes:
ready: yes
ready_by: ideation
ready_rev: 3
---

## What to build

[spec](../specs/native-cli-orchestration-2026-10-10.md) 第 12 节切片 S1 的第 0 步，单独成票。第 13 节的风险 R6、R7 由执行主控负责，结论可能让方向停下，所以先于 tracer bullet（[T-075](T-075-tracer-bullet-daemon-gate-pane.md)）核实。只出事实报告与探针，不写产品代码。

- **R6**：Codex CLI（固定版本）在等用户确认（命令批准、补丁批准等）时，有没有能被外部程序拿到的结构化信号，例如 `notify`、hooks、OSC 序列、rollout 记录里的事件。Claude Code 对应的 hooks 与 OSC 7501 一并核实一次。
- **R7**：在 node-pty 托管的 zsh 窗格里运行交互式 Claude Code 与 Codex，从外部往 PTY 写一行带 `⟦主控 #序号⟧` 标记的文字再回车，CLI 能否稳定把它当作一条新的用户消息，包括 CLI 正在运行回合时、空闲时、正在等确认时。

## Acceptance

- [ ] 每个结论标 observed / measured / inferred / unknown，附原始输出、CLI 版本、启动 argv 和重放命令。
- [ ] R6：至少触发一次真实的等确认状态（Codex 一次，Claude 一次），记下外部程序收到了什么、在什么时刻收到；没有信号就写"未找到"并列出查过的途径，不改用读屏或正则。
- [ ] R7：两家各至少 10 次注入，覆盖空闲、回合进行中、等确认三种状态；记成功次数、失败的样子（丢字、拼进上一条、被当作确认的回答等）。设计成功率门槛之前先把原始次数报上来，门槛由构思主控与用户定。
- [ ] 注入的文字在写入前登记（spec 第 6 节），探针能把登记与 CLI 实际收到的对上。
- [ ] 结论写成 `findings/` 下的中文报告，报告里写明对 T-075 的影响：可以按 spec 做、要改设计、或要停下。
- [ ] 任一项不通过：停下写 `needs-decision` 交构思主控，不硬做、不加兜底重试，不开始 T-075。

## 说明

- 失败方式清单（处理方式写进 RESULTS）：CLI 启动时的更新提示或信任目录提示挡住输入；注入时 CLI 正在渲染导致字符交错；中文与标记字符的编码；多行文字被拆成几条消息；粘贴模式（bracketed paste）开关不同；等确认时注入的文字被当作确认的回答（这是危险情况，必须单独记）。
- 真实模型调用：Codex 按 AGENTS.md 用隔离 `CODEX_HOME`，turn 数尽量少；Claude Code 用不写 `~/.claude` 的方式启动（例如独立的配置目录与 `--settings`），认证方式拿不准时先停下问，不动用户的全局配置。启动参数里固定 `check_for_update_on_startup=false`。
- 探针代码放证据目录，不进产品目录；node-pty 可以在证据目录里临时装，依赖缓存放外置盘（AGENTS.md 构建规则）。
- 与 [T-073](T-073-herdr-period-task-card-trailers-scoring.md) 改的文件不重叠，可以并行。
- 授权来源：用户 2026-10-10 在会话"a2a-构思主控"确认切法（逐字："确认"），在此之前在会话"新思路构思"说："确认，写完文档后，你这边就不用了，全权交给构思主控去安排执行主控安排子 agent 去做。"`ready_by: ideation`，`ready_rev: 1`。

## 修订 rev 2（2026-10-10，用户决定）

依据首轮实测（Codex 等批准时，M3 注入的文字被当作 Accept）和用户的三项答复，本票追加与改动如下；与上文冲突处以本节为准。

- **Claude 认证**：用用户平常的 Claude 登录（用户选"直接用你平常的登录"）。这是用户对本票的明确例外：CLI 自己往 `~/.claude` 写会话历史、首次信任目录写 `~/.claude.json` 都可以接受；a2a 的代码与 worker 仍不写 Claude 的设置或权限配置，hooks 与设置只经 `--settings` 传入；不读取、不复制凭据。上文"不写 `~/.claude` 的方式启动"一句作废。
- **Claude 模型与上限**：Haiku 5.5，最多 15 个原生回合（用户选"Haiku 5.5，最多 15 回合"）；达到上限就停下报告，不自动追加。
- **受管 worker 不弹批准**（用户选"worker 不弹批准"）：worker 启动时给定沙箱与允许的命令，审批设为不问（Codex `approval_policy=never`，Claude `--permission-mode dontAsk`，均只经每会话启动参数）。追加验证：在这种启动方式下，越界操作被拒而不弹批准；随后 M3 注入照常作为新消息送达，不会被当作批准。两家各至少 3 次。
- **主控窗格等批准时暂停注入，先验证**（用户选"等批准时暂停，先验证"）：用每会话启动参数装的权限请求 hook（Claude 的 PermissionRequest，Codex 对应的 hook）作为结构化的"等批准"信号，核实它在批准窗口出现时、结束时各有事件，能拿到请求标识。再验证竞态：注入写到一半时进入等批准，记录实际发生了什么。hook 不可靠或竞态无法避免时停下报告，不加兜底重试，不改用读屏。
- 结论报告要写明对 T-075 的影响，以及 spec 第 6 节的派发规则是否需要再改。

## 修订 rev 3（2026-10-11，用户决定）

依据 rev 2 交付（needs-decision `20261011T012207Z-executor-needs-decision-001`）：两家的权限请求 hook 只有开始事件，没有结束事件与请求标识，"等批准时暂停、批完再送"没有恢复依据。与 rev 2 冲突处以本节为准。

- **主控窗格只在空闲时注入**（用户选"只在空闲时注入"）：不依赖"批准结束"信号。只有当该窗格最近一条结构化事件是"回合结束"、且其后没有"回合开始"时才写入，其余时间排队；空闲时不会出现批准窗口。rev 2 的"权限请求 hook 作恢复依据"一项撤回，不再要求它的结束事件。
- 追加验证，两家各做：
  1. 找到并记下"回合开始"与"回合结束"的结构化事件（例如 Claude 的 UserPromptSubmit 与 Stop hook，Codex 的对应 hook 或 `notify`），只经每会话启动参数装；
  2. 按上面的规则做至少 5 次空闲注入，全部作为新消息送达；
  3. 竞态：在"回合结束"之后、注入写入之前，人为让新回合开始（例如脚本先提交一条消息），记录排队规则是否挡住、实际发生了什么。挡不住或会被当作批准时，停下报告。
- **补全 Claude R7**（用户选"补全并加额度"）：补到至少 10 次，覆盖运行中状态。
- **额度上限**：Claude 25 个原生回合，Codex 40 个主 turn（均含已用的）；达到就停下报告，不自动追加。Codex 新会话按 2026-10-11 的临时规定用 `gpt-6-astra` xhigh Fast，结论标明测出它的模型。
- 不读屏、不用 OSC 文字或回合结束猜测之外的推断；不加自动回车或重试。

## Resolution

2026-10-10，T-074-1 首轮交付 **BLOCKED，待主控关闭**；保持 open，Acceptance 未完成项不勾选。Codex 0.162.1 在 node-pty 1.1.0 托管的 zsh 中初始化完成后，登记并一次写入单行标记文字与回车；42.396156 秒内原生 user.text 没有对应消息，结果 `codex idle other 1`。按卡停止，没有补发或重投。R7 尚缺至少 10 次及 running/awaiting_approval 覆盖，R6 未实际触发批准，Claude 未真实启动；不能支持 T-075 直接开工。

证据与完整启动参数：[RESULTS](../../evidence/2026-10-10-batch12/T-074/RESULTS.md)、[原始注入](../../evidence/2026-10-10-batch12/T-074/r7-injections.jsonl)、[中文报告](../../findings/native-cli-signals-injection-2026-10-10.zh-CN.md)。待决定的实验协议、Claude 隔离认证与调用估算见 [needs-decision](../../evidence/2026-10-10-batch12/T-074/needs-decision-01.md)。两个自建后台与临时 home 已清理，首次设置异常现场保留，auth.json 未入证据。

计数命令退出 0，但覆盖不达标；status 为 Problems (0)、Stale living docs (1)，退出 1，输出保留在 checks.json。新增报告触发 findings/README.md 索引维护，现有 README 超出 worker 修改边界，交执行主控处理。交付 commit 以最终终端回执和 Git 文件历史为准，主控核对后补关闭结论。

2026-10-10，按执行主控决定 01 和当前对话主控 #5 继续后，**Codex 部分事实采集完成，整票仍 BLOCKED、待主控关闭；只差 Claude 的隔离认证与真实实验**。方法 M1/M2/M3 各 2 次 idle pilot，选 M3 后另外 10 次覆盖三状态。总计 16 次：M1 idle other 2；M2 idle ok 2；M3 idle ok 7、running ok 4、awaiting_approval taken_as_approval 1。R6 真实批准发出 OSC 9；该次 M3 注入没有成为用户消息，而引发 Accept 响应及夹具文件写入。累计 14 个主 turn（上限 30），4 个辅助标题完成通知另列。所有自己启动的进程与完整临时 home 已清理，Claude 未启动。

现行交付见 [RESULTS](../../evidence/2026-10-10-batch12/T-074/RESULTS.md)、[逐次数据](../../evidence/2026-10-10-batch12/T-074/r7-injections.jsonl)、[归档核对](../../evidence/2026-10-10-batch12/T-074/analysis-round2.json)。首轮报告与失败现场仍保留。findings 索引按决定 01 授权补一行。T-075 的统一窗格派发需要改设计，已另上报 blocking issue `20261010T200708Z-worker:s12-t074-issue-001`，详见 [needs-decision-02](../../evidence/2026-10-10-batch12/T-074/needs-decision-02.md)；完整采集只差 Claude，不意味着设计获批或整票 PASS。

2026-10-11 UTC，ready_rev 2 / 执行主控决定 02 本轮交付 **BLOCKED，待主控关闭**。两家不问模式各三次真实越界拒绝、随后 M3 新消息送达均有原生记录，样本项通过。PermissionRequest 各收到一个开始事件；关闭后观察 30 秒仍只有原开始事件，没有审批请求标识。Codex Esc 实际为 Cancel/turn_aborted，独立 Decline 路径未测；Claude 有明确工具拒绝，prompt_id 对应用户输入而非审批请求。按决定 02 的停止条件，未继续竞态和 Claude R7 基本项；Claude 当前 7 条注入，不足原票至少 10 条及 running 覆盖，不能关闭整票。

本轮新增 14 条 R7，累计原始文件 30 条。Codex 累计 23/30 主 turn；Claude 原生输入回合 10，首次无记录启动保守多计 1，共 11/15。实际成功模型为 claude-haiku-5-5，认证已解决；所有探针已停，隔离 CODEX_HOME 已删除，Claude 夹具按要求保留。新会话模型切换发生在本轮模型探针停止之后，收尾未再调用模型。

本轮证据：[RESULTS 新增 rev 2 节](../../evidence/2026-10-10-batch12/T-074/RESULTS.md)、[原生归档核对](../../evidence/2026-10-10-batch12/T-074/analysis-rev2.json)、[needs-decision-03](../../evidence/2026-10-10-batch12/T-074/needs-decision-03.md)。blocking issue `20261011T011326Z-worker:s12-t074-issue-001` 已交 triage。spec 第 6 节的 worker 不问方式有样本证据，主控恢复派发条件仍需设计决定；T-075 不由本 worker 开始。保持 open，整票 Acceptance 不提前勾选。
