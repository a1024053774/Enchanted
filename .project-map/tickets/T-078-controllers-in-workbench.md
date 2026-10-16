---
id: T-078
title: S4 两个主控进工作台：主控窗格、交互输入、收件箱进库、唤醒、用户输入记录、紧急停止
type: build
status: open
blocked_by: []
claimed_by:
supersedes:
ready: yes
ready_by: ideation
ready_rev: 2
---

## What to build

[spec](../specs/native-cli-orchestration-2026-10-10.md) 第 12 节切片 S4，即第 5、6、9 节里与主控有关的部分；原 T-059、T-066 的目标在新载体上重做：

1. **主控窗格**：构思主控与执行主控各一个 Claude Code 窗格（`--session-id`、`--model`、`--effort`、`--settings` 只经启动参数），带启动记录与角色卡。
2. **交互输入**：Electron 窗口里的窗格可以打字；所有输入经编排后台写进 node-pty（T-074 的前提）。
3. **用户输入记录**：用户在窗格里亲手打的字记为用户输入（T-050 的语义）；落进受管 worker 窗格的记为人工介入；注入的文字写入前登记，记录器跳过已登记的部分。
4. **唤醒与派发**：按 spec 第 6 节"批准与派发分开"：worker 窗格以"不问"模式直接注入；主控窗格只在空闲时注入（后台写出提交回车就记忙、收到回合结束才回空闲），Esc 中断后排队消息由用户放行，放行记为用户输入。注入用 bracketed paste 后单独回车。
5. **收件箱进库**：条目存进后台库，只追加；新的 `scripts/inbox` 后台客户端按角色限定能写的条目（权限第四层）。本仓库日常仍用文件版 `scripts/inbox`，到切换（S7）当天退役，不双写；本票只在夹具项目上用库版。
6. **紧急停止**：用户对某个主控说"立刻停 X"的流程在库里走通（stop、ack、2 分钟无 ack 时构思主控只做中断），记录写实际调用者（原 T-066 的要求，身份取自凭据而非参数）。

## Acceptance

- [ ] 检查面同 T-075。（修订 rev 2：原有的"Electron 截图或录屏：两个主控窗格、一个 worker 窗格同时在一个任务下"一项移到 [T-091](T-091-single-window-multi-pane.md)，用户 2026-10-16 选择，见下方"修订 rev 2"。）
- [ ] 用户输入：在窗格里亲手输入的一句被记为用户输入；同一窗格里后台注入的一句不被记为用户输入；worker 窗格里亲手输入的记为人工介入。
- [ ] 唤醒：执行主控写 report 后构思主控窗格在空闲时收到带标记的唤醒；它在回合中时排队，回合结束后送达；Esc 中断后不自动放出，用户放行后送达。
- [ ] 收件箱：库版 `scripts/inbox` 的 send、list、ack、ready 在夹具项目上可用；按角色越权写入被拒（例如 worker 写 assign）。
- [ ] 紧急停止：stop → ack 正例；无 ack 2 分钟后的只中断正例；停止记录的调用者为实际角色，参数里伪造的被忽略。
- [ ] Claude 会话不写 `~/.claude` 的设置与权限；如需真实 Claude 回合，先在 needs-decision 里报认证方式与额度，由用户决定（T-074 的例外只覆盖 T-074）。
- [ ] 8/9/18 三组与 T-075 的正反例不退化。

## 说明

- 失败方式清单（处理方式写进 RESULTS）：用户与注入同时输入；中文输入法的组合输入；粘贴大段文字；窗口关闭期间的输入；后台重启后忙闲状态未知（按"未知"处理，不自动注入）；同一条唤醒重复送达。
- 与 [T-076](T-076-quality-chain-scoring.md)、[T-077](T-077-worktree-lifecycle-conflicts.md) 可能改同一批文件，由执行主控安排顺序。
- 授权来源：用户 2026-10-11 在会话"a2a-构思主控"选"S2、S3、S4 三张，缺口并入 (Recommended)"，选项原文含"我写完直接标就绪派出，不再单独给你看切法"；在此之前在会话"新思路构思"说："确认，写完文档后，你这边就不用了，全权交给构思主控去安排执行主控安排子 agent 去做。"`ready_by: ideation`，`ready_rev: 1`。

## 修订 rev 2（2026-10-16，用户在会话"a2a-构思主控"以选择题作答，逐字）

1. 三窗格：用户选"拆出去：T-078 其余先收，截图项另开 UI 票 (Recommended)"，选项原文："承认单窗多窗格是产品工作，另开一张 UI 票做（spec 里本来就写“一个任务里有多个会话窗格”）。T-078 把这一项从验收里移出并在 Resolution 写明，其余项独立审查通过就可以关。这是你对验收条件的修订，要你本人确认。"→ 移到 T-091。
2. 真登录复核：用户选"另开一张票，T-078 先不等它 (Recommended)"，选项原文见 [T-092](T-092-normal-login-profile.md)。→ 移到 T-092，T-078 按假 API 证据验收，Resolution 写明这一项未覆盖。
3. 09C：用户选"授权执行主控代签 (Recommended)"，选项原文："授权执行主控代签 09C 各阶段，并允许实际命令、stop、目标、原屏与预批准模板逐项一致时自动按一次 Enter；有任何不一致就停，结果记 INCOMPLETE。模型回合 0、假 API，预算 ideation 4 roots/7 POST、executor 1/1。上次它的权限分类器拦过代签，可能还需要你在执行主控会话里亲口确认一次。"
4. 系统输入法（失败方式清单里的"中文输入法的组合输入"）：用户选"本轮不做"，选项原文："保持 INCOMPLETE。"→ RESULTS 记未验证，不算通过。
5. 09B 补证：用户选"重跑一场 09B，留最小脱敏原件 (Recommended)"，选项原文："假 API、模型 0 回合，同 protocol 与预算，回收前额外保留逐 POST/hook 原件（不含认证信息）供独立复核，由执行主控按已有的 09B 授权代签。代价是几个小时的逐阶段签字，可与 09C 同批准备。"

## Resolution

2026-10-11，T-078-1 非 Claude 范围的最终验收与一次新上下文只读独立审查均为局部 **PASS**；T-078 整票 **INCOMPLETE，待主控关闭**。已验收代码提交 `b3fb998cf48574821c39440ece3f9ff897f26cf9`，基于 main `532c51f4cc12352bb7cf545ce1e5f824d68bdc4a`，保留 T-076-1 的稳定身份及停机收尾改动。窗口输入经后台写入 PTY，区分用户输入／人工介入与注入，覆盖组合输入占用、请求去重、二进制字节、Esc 后用户放行；worker 库收件箱使用实际会话身份经已认证 Stop 转交并核对当前 attempt；Claude 启动参数及记录只作静态准备。

最终证据见 [RESULTS](../../evidence/2026-10-11-batch13/T-078/RESULTS.md) 和 [outside-final-01](../../evidence/2026-10-11-batch13/T-078/outside-final-01/checkpoint.json)：领域 11、管理客户端 8、窗格状态 11、静态骨架 2、运行时入口 12、输入失败方式 11、worker 入口 14 全部通过；原 coop/recovery/run 8/9/18 与 CAS 1 均为 0 failures/errors/skipped；四项权限及 fence/CAS/lock 三项原业务变异反例均实际触发业务违约，原失败现场保留。旧 worker_command_forbidden 仅证明入口缺失，没有冒充权限业务规则红态。六个超限原件按规则归档外置盘，仓库保留摘要与重放路径。

[独立审查](../../evidence/2026-10-11-batch13/T-078/independent-review-01.md) 未确认该局部范围内的可达违约或结构性阻断问题，核对了冻结源码、原始字节、SQLite 内存读副本和外置原件。使用会话内独立只读 agent，fork_turns=none，请求 gpt-6-astra/xhigh；实际模型配置与服务档位未独立观测，不冒称 Fast 已生效。审查未写候选、submit 或集成。

真实 Claude 启动、主控角色凭据和 hook 接线、实际主控互相唤醒、两个主控加一个 worker 的同任务窗口验收仍未完成，等待 needs-decision `20261011T101958Z`。两分钟无 ack 条件为受控时钟／逻辑角色证据，IME 为合成组合事件；不外推为实际主控链路或系统输入法验证。测试未启动 Claude 或其夹具，待真实 Claude 复核；不切换日常文件版 inbox，不 push。Ticket 保持 open、待主控关闭。

2026-10-14，以上为 T-078-1 交付时点。用户已答复认证与预算，T-078-2 经逐次批准推进假服务验证：08e 的真实 CLI 单回合、实际 UserPromptSubmit/Stop、busy→idle 与主 Messages 请求均 PASS，真实供应商模型回合为 0。结论绑定变基前代码，尚不证明双主控／紧急停止／真登录。原件与边界见 [RESULTS](../../evidence/2026-10-11-batch13/T-078/RESULTS.md)。

09A 的 Esc 实跑 INCOMPLETE，失败和外置原件保留。主控 #122 要求的只读诊断确认驱动过早发键及 nullable 主控窗口永久禁输入；修复独立提交 `7cd19b586fe757268384d99f243f5d0a583a5ad3`，域／驱动红转绿，收据及身份反例通过。[09A-2 材料](../../evidence/2026-10-11-batch13/T-078/P2-APPROVAL-09A2.md) 静态准备 PASS，实际启动未执行，待主控审批。T-077 合入后才变基、重新生成并完整重跑；09B/09C 与真登录仍未完成。整票保持 open、INCOMPLETE、待主控关闭。

主控 #124 随后实跑 09A-2：Esc 送达／退休／队列 held 正例成立，但放行把 CLI 恢复进编辑框的第一提示与第二条拼接，hook/API 原件确认，产品 INCOMPLETE。只读诊断、最小方案与用户输入语义取舍见 [DRAFT-OPTIONS](../../evidence/2026-10-11-batch13/T-078/DRAFT-OPTIONS-09A2.md)。草稿占用标记不等于 CLI 编辑框检测；本轮未实现任何修复选项，停在方案决定。失败根及 slot 的外置归档／处置脚本另交主控执行，不把清理通过算作产品通过。整票仍 open、INCOMPLETE、待主控关闭。
