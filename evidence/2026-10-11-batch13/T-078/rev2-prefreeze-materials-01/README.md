# T-078 rev 2：A-16／09C 前冻结材料

2026-10-16，执行主控 #338。**材料待审；运行 INCOMPLETE，launch NO_GO，源码与运行身份均未绑定。** 本目录是计划、字段模板与脚本契约，不是可执行launch包。未生成sources.tar.gz、静态fixture root、session/launch UUID、PID、实际target claim或任何已签批准；不能传给旧run-09b.py冒充冻结包。

授权原文见 [main票rev 2副本](authority-ticket-rev2.md) 和 [revise原件副本](authority-revise.md)。本worktree尚未合入main的新票内容，旧ready_rev 1是历史视图；本轮按主控明确转述及main原文使用 **ready_rev 2**，不自行改地图/ticket。三窗格移T-091；正常登录/真实模型复核移T-092；系统IME本轮不做，保持未验证/INCOMPLETE。旧计划、真登录材料和A15结论原样保留，不运行真登录、不读取认证。

## 两场共同的前置与边界

1. T-090在main修审查开始时绑定worker实际HEAD/分支/clean、结束核对未变；合入后由主控安排exec/t078合并main。本轮不改core，不做Git合并。
2. 合并后核对双方语义，更新真实源码绑定，完整重跑 `review-followup-regressions-02`：8/9/18、CAS、T075门禁正反例及三变异；T082相关边界仍需成立。失败即停，不拿旧绿态替代。
3. 实现并排练本目录的逐记录捕获、外置归档/sidecar、独立重数及回收契约；实现09C专用阶段/保持屏障/条件式单Enter。**现有A15 redactor只存汇总，不可直接复用来收A16；现有09B phase-plan不能把C-I2/C-I3映射成普通确认回合。** 本轮只写契约，未称这些新脚本已实现或已通过测试。
4. 先用真实daemon/relay/HTTP及隔离Electron/确定性替身做无模型排练，覆盖Bash command schema、异步queued→Stop结算、完整读屏和一次写入回执、重试/坏body/错身份/截断/错模板/超时。排练不代替真实Claude场景；如需额外原生CLI探针，另列预算，不从本场偷挪。
5. 上述准备完成后，才用标准prepare/相应C生成器冻结**合并后**的真实源码闭包、两场独立新实例并重新绑定。F6的八个Python reader依赖必须继续在标准包内，新捕获/归档/C模块的所有本地依赖也逐文件入包核对，不能靠host checkout补齐。每个fake API在阶段A起就加载最终完整协议；不热替换运行中的API，不复用旧PID/lstart/ready。
6. 启动、首启、业务、工具、回收各阶段批准仍需按真实收据填齐后由执行主控签；[批准字段模板](APPROVAL-FIELDS.json)仍空签。用户已经授权09B补跑和09C代签，**不重复请用户选择路线**。若执行主控的权限分类器拒绝某次代签，不绕过或伪造签字，停止该动作、保留INCOMPLETE并回needs-decision，由用户在该会话确认。

两个场景同批准备、**串行运行**：先A16完成/归档/回收，再启动独立09C。两场各一broker/state/repo、两名交互Claude Code 2.1.296（Haiku5.5/low，假API）、一个真实门禁dispatch/claim的确定性worker接收器；角色HOME/config/tmp/shell/requests/hooks/user-data按preset隔离。真实供应商模型和真实Codex会话均0，不复制用户认证，不接管用户会话；同一时刻最多两Claude、两fake API、一个daemon/target、一个隔离Electron观察/许可窗口。无额外Codex或子代理，不并开两套场景。

## A-16：09B同protocol补原件

[A16-STAGES](A16-STAGES.json)的十个业务阶段逐项沿用 [冻结protocol](../09b-materials-01/protocol.json)，不改阶段含义、tool、argv语义或预算。I1是批准的test-simulated-user停止请求；Bash input必须command字符串；工具只返回真实queued回执，门禁结果到真实Stop/relay后才结算。source文本/真实dispatch/request/inbox/prompt/tool ID及**全局**seq由实际记录取得，不写死#1/#2；E_WRONG_TARGET保留protocol的负例目标，不当本次真实target。实际body文件/target refs按现有规则绑定本场root/真实claim，不能将旧实例身份带入。

操作顺序：

| 步骤 | 动作及停点 |
|---|---|
| A0 | 真实入口card校验在任何spawn前；阶段A detached daemon/fake API启动，实际dispatch/claim并记录target完整身份；无角色CLI，写readiness后停 |
| A1 | ideation单独B1/首启：主题ArrowUp→Auto、ArrowDown→Dark、Enter；Security notes原文一致才Enter（B1计划security-notice/screen_text，实际键purpose=onboarding-notice）；信任屏ArrowDown选Yes再Enter。每次一键、当前原屏批准；禁Digit1/默认Enter。只读屏过早可新-02重读，不发键、不覆盖旧证据 |
| A2 | ideation readiness核对空提示符/manual/0 Messages；I1经正常输入路径到许可屏即停，签一次性Yes后单Enter；Stop生成实际stop，pending对发送方可见、feedback=0 |
| A3 | executor单独B1/同样六键。每键后走真实收据刷新：原stop仍queued、无delivered历史/原I2、unknown/active=null、零业务输入/POST；六次通过再readiness |
| A4 | 先arm原I2（不发输入），再初始release原stop队列；只有turn_submitted才delivered；原request/entry的I2恰一次，只确认。E1到许可屏停；不能用operator另send或另派I2 |
| A5 | E1真实错目标拒绝 → 原反馈E2实际一次Esc → 原反馈E3 ack。各工具读完整原屏、另签一次性Yes、awaited单Enter、Stop/relay读回后才过阶段 |
| A6 | E3因果分叉：ack唤醒I3、执行反馈触发E4；按真实全局seq关联，允许交错。分别预arm各自阶段批准，原生请求不得在180秒批准门外自动重试；I3越权ack拒绝→I4只确认，E4重复ack幂等→E5已ack stop拒绝→E6只确认。每阶段命令独立、工具许可逐次，不捆绑多键 |
| A7 | 最终独立重数17 Messages/10根/七工具许可、单ack/单Esc、角色实际来源与pending→delivered→原I2；**逐POST/hook原件**外置归档及sidecar通过，再单独批准owner-bound回收 |

自动根只来自实际inbox wake/gate feedback；阶段批准arm不是派发，不新增根。空闲/忙、UPS/Stop/permission必须真实发生。工具许可Enter为control action，不新增turn_submit_intent；源码尾CR/LF规范化与逐字匹配原规则保留，不裁剪/容忍拼接。

## 09C：真实时钟、无ack、只中断

见 [09C-STAGES](09C-STAGES.json) 与 [C-I3完整核对契约](CONDITIONAL-ENTER-09C-I3.md)。两个角色先串行完成B1/onboarding/readiness，executor已能实际接收；此时尚未创建stop，不消耗120秒窗口。使用全新独立root/角色/API/stop/target，不复用A16实例；初始模拟用户请求明确持续要求在本次观察期停止该唯一目标，撤销即停。

| 阶段 | 因果输入与行为 | 原生回合/POST/许可 |
|---|---|---|
| C-I1 | 批准的模拟窗口stop请求→真实inbox send→queued→真实Stop生成stop并delivered；保留实际created_at | I 1根/2 POST/1许可 |
| C-E1 | 原stop实际inbox wake；executor UPS/API确实收到，单个SSE请求保持，**不给工具、不执行、不ack** | E 1根/1 POST/0许可 |
| C-I2 | 原send执行反馈触发ideation；实际命令stop同一target/stop，在年龄<120000ms时经真实Stop得到stop_too_early；target新增0 | I 1根/2 POST/1许可 |
| C-I3 | 原too-early反馈触发ideation；假API下发真实late-stop工具，**先停在真实PermissionRequest**。在阈值前尽早完整捕获实际原屏，由执行主控签实值预批准模板；不按键等待。>120秒后按契约再次完整读屏、全部相同才一次Enter；真实Stop/relay执行ideation中断 | I 1根/2 POST/1许可 |
| C-I4 | 原成功中断执行反馈，只确认，实际Stop/idle；随后让C-E1的原单次SSE中性结束，无工具/ack/新根 | I 1根/1 POST/0许可；E仍原1 POST |

这里将“等到阈值”放在C-I3的**真实许可屏之前已准备、尚未按Enter**的状态；不要求主控到120秒才临时审未知屏，不增POST/根。它取代旧计划“到120秒才发tool_use”的操作安排；用户授权的条件和真实门禁执行>120秒不变。若等待时PTY有任何新增字节而不再等于已签完整原屏，结果就是INCOMPLETE、零Enter，不能只比尾窗或自动改签。

时钟起点是真实stop.created_at；同步记录首次观察条目的UTC/monotonic，不能回写created_at或快进/冻结系统时钟。每≤20秒只读记录age/no-ack/持续停止要求/原target身份/received.bin；“等了120秒”不是门禁执行证据。晚到single Enter的准备点采用monotonic观察已≥120100ms且真实wall age>120000ms，并在130000ms前开始，给结算留余量；这是驱动安全截止，不把产品的>120000门槛改成130秒。全场真实时钟观察/结论≤150000ms；不足以完整结算也INCOMPLETE，不延长。

独立oracle必须看到：早期真实stop_too_early和0新字节；晚到实际emergency_interrupt_intent/requested.actor=ideation，年龄严格>120000ms、同stop/target且仍无ack；received相对基线恰1b，进程/attempt/fence/workspace保留，无kill/reclaim/archive；所有HTTP/hook/原事件行可重新核对。C-E1必须实际已收到而非pending未送达；保持期间无工具/ack，最后中性结束不重送。缺少finished/EOF、C阶段被旧09B API当确认、90秒旧超时/409诱发重试，都不算成功。

## 当前交付状态

本目录有六份核心未绑定JSON、两份archive sidecar模板、授权副本及脚本/捕获/停止契约，另留只读文件检查回执。归档的字段清单与 `*.archive.json` 在 [RAW-RETENTION](RAW-RETENTION-AND-ARCHIVE.md)；回收流程在 [CLEANUP契约](CLEANUP-SCRIPT-CONTRACT.md)；两场预算/统一停止条件见 [BUDGET](BUDGET-AND-STOPS.md)。这些是合并后实现/排练/冻结的输入，**不是把未实现脚本伪装成READY或给出假PASS收据**。新脚本运行结果、实际审批/归档路径/成员字节、源码版本和launch都待后续真实绑定。当前无可执行launch命令，无任何场景运行。
