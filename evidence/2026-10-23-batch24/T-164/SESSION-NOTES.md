# T-164 操作记录

实例 /private/tmp/t164-dogfood-xn9_oslt，Electron 41077，daemon 41076。
首次目录选择误落旧 T-155 夹具；未启动终端，已切回本轮。当前项目 UI 名 demo-repo-2。

C1：请担任本一次性项目执行主控，按 Enchanted a2a 使用说明申请 executor，等界面批准。本回合不派发。仅当前 repo，不 push、不删除、不碰其他项目。

C1 实际发送文本：`Enchanted a2a executor repo push`（typeText 丢失中文，见图 03）。它未执行 push，只申请角色并等待。此为测试输入缺陷，不归产品。
C2 使用 paste，截图确认后提交：更正：刚才中文输入丢失。只操作当前一次性 repo，不 push，不删除，不碰其他项目。角色已确认；现在继续等待，不派发，不轮询。

F04：记录页 1 条批准，角色事件 #37。F07：窗格头包含执行主控。
阻断待澄清：README:430 及 :689 reviewer 同 worker CLI/model，与其余全部 Haiku 冲突；尚未派发。

主控 #81：外层周额度7% left，由主控监看≤3%即停，不再询问。
C3：需求：从 pantry.json 做三张受管小票，工作分支 main。A 用 claude-haiku-5-5：inventory.md 按类别列种类数、库存件数及总计；首版受控漏总计，真实门禁打回后补齐，此顺序写进卡。B 是唯一 Codex worker，用 gpt-6.1-sol/high/default：shopping.md 只列零库存食材；必须先 issue 问是否按类别分组，等界面答复再实现。C 后续用 Haiku 更新 README 使用说明。先建 A/B 独立 worktree 并行派发，启动后结束回合让我观察，不轮询、不先验收。验收脚本由你按原始数据建立并用正确、错数字、反向语义样本自检；不让 worker 改验收文件。Haiku 票 reviewer 也用 Haiku；B 的 Codex reviewer 尚待外层确认，先不启动。全程只本 repo、不 push、不删除；Claude 总预算60回合，失败原样报告不长轮询。

主控 #82 原文：允许。用户原话限制的是 worker（“应用内只用 1 个 Codex worker”），同时要求走到集成；产品规定 reviewer 与 worker 同 CLI 同模型，所以那个 Codex worker 的独立审查用产品自动给的 Codex reviewer，其余 worker 与 reviewer 都用 claude-haiku-5-5。这是执行主控的解释，我会在报告里列给构思主控；你在 RESULTS 里引用本条。继续推进到集成。
图05：主控自检发现 runner 状态码读取错误并修复；语义改述“以上数字都靠不住”仍被接受，主控将其记录为独审要查的已知缺口。此时仍在编卡，无 worker。

图06：指标明确“不是全局总回合”，主控回合显示未覆盖，汇总未知（已记录0/未覆盖1），打回分母说明为已打分结束attempt。F06的误导性零已消失，完整计量尚未验证。

人工介入：A 运行中（图08）输入仅在说明确认消息、不改验收/不额外提交。随后A未知（图11），candidate仍尚未交付，CLI已答复完成。A只跑本地脚本失败即补总计，未形成门禁打回。B上报并等答复，图10面板答平铺显示已送达；B也随后未知。
C4：外层执行主控已确认：允许 B 对应的产品自动 Codex reviewer，其余 worker/reviewer 仍 Haiku。B 问题我已在界面答复平铺，显示已送达。A 忙时人工介入已收到回复，但侧栏未知、门禁仍已认领/尚未交付；B 侧栏也未知。请按公开 a2a 流程做一次有界核对，显示原始拒绝原因；不重放未知写入、不长轮询、不新建 Codex worker。能继续的票做真实 verify/独审/打分/集成。若 A 只是本地自检红态，不冒称真实门禁打回。继续建 C（Haiku README 小票）并推进。

图12：T-B任务右分屏保留左侧worker与右侧普通终端，未向新终端发命令。图14：T-C无人工介入，交付已被门禁接受，8749aa0d113fdb5f3f672d8c5c8abd26fcdd2ed4。
C5：C 界面已明确 submitted，候选 8749aa0d113fdb5f3f672d8c5c8abd26fcdd2ed4。请继续真实 verify→独立审查→打分→集成，不靠自报。A/B 已知not_submitted不再重复verify；仅用公开帮助核对一次原attempt的事件/请求队列拒绝原因及文档化恢复入口，不读凭据、不改产品、不重放未知写入。

图15：Codex 的门禁#3 ACK完整停留在输入区（无Working），已送达用户答复尚未出现。仅按一次Return提交屏幕上已完整核对的“只确认收到/不调用工具”收据，图16出现Working与新空输入框；没有重发业务写入或重新issue。此为明确人工介入，须计入预算和报告。Codex状态栏显示GPT-6-Luna medium，与请求6.1high不符，待事后原生日志核对，不据此推断实际模型。

C6：新事实：B 界面现已交付，可按门禁读回当前候选并 verify/独审/打分/集成；我只在其完整停留的门禁ACK输入区按了一次回车，随后恢复，勿重复发送。A 的 a3452b88 是其终端明确显示的提交（有人工介入前后截图），但交付未知，保留旧attempt不重放。为复验修订恢复，授权同目标保存A卡v2、按公开README revise提升spec_rev，再正常派Haiku新attempt；原失败现场不删除、不复用旧候选。C 审查结果到达后继续集成。没有新事实时结束，勿长轮询。

C7（在C6运行中排队）：C 的真实独审打回已确认。授权仅按原 README 使用说明目标强化你生成的验收脚本，保留旧版和失败，再 card_save/revise 正常新attempt重审，不降低检查、不伪造结论。A 保留旧失败worktree，不通过reclaim删除现场；revise后按公开正常dispatch复验路径释放，拒绝即报原码。
图19：C独审需修复，有三项变异放过及正文断言文件存在问题；B候选611ca29机械过并启动独审。

C8：已核对公开 README 395～405：修订完整流程是保存旧attempt→card_save→revise→reclaim旧attempt→dispatch；未回收时path_overlap是有效拒绝。请按此完整流程优先推进C：核对旧worker已提交且pane_status idle/writing=false/active=null/queued=[]，仅经门禁归档回收，再正常派新Haiku attempt；失败现场由门禁归档保留，不手工删文件。A未知/worker_working保持，不强制。B先保留需修复，不新派第二个Codex worker。C修复后完整独审打分集成。
更正：前面为保留现场而让主控跳过reclaim，未覆盖公开README修订完整流程。该部分path_overlap不能判F05回归；现要求按完整流程复验C。旧A未知导致worker_working另记F01恢复限制。
