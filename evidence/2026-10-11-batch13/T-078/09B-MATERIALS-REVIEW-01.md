# 09B 计划性材料审阅与 green-3 收尾

green-3 真实单角色闭环 **PASS**；09B 本包只供计划审阅，**launch NO_GO、业务验收 INCOMPLETE**。按主控 #185 的“先交计划性的材料审阅，不启动”，本轮不实现双角色新 profile／协议驱动，不调用真实 CLI／API／Electron／目标，不冒称已生成当前产品可接受的启动记录。

## green-3 实际读回与清理

[本轮读回](slice1-green-3-closeout/readback.json) 对 source `8e99d62e7892ef0468fe2b2b8dabe22387684557`、材料 `b5b8b165d06c5cc5ab341c965679d7932d74c8a3` 原件核对：主 Messages3，实际ACK/FINAL_ACK、relay_processed1、intent2、turn_end2、idle2、permission_control_written1，没有user intent。真实第一 Stop 中执行 inbox_list 一次，角色参数executor未覆盖 ideation 凭据；完整登记反馈作为第二根到达并结算。供应商模型0，独立reviewer及整票仍未完成。

#184 的 API3 字符串表示缺陷经原样red→green修复，登记原文／预算／tool／角色核对保留；旧 scene仍INCOMPLETE／4/3 NO_GO。旧 [cleanup-184](p1-materials-slice1-green/cleanup-184/result.json) PASS，错误根保持。此次green-3是全新ID与批准后的真实复验，不覆盖旧失败。

本次 [cleanup-slice1-green-185.py](cleanup-slice1-green-185.py) 交主控运行：固定 root `/private/tmp/t078-2-p1-slice1-green-3-jzfi4ju5`、launch `c4a5dc22-7d3f-430d-8e82-1b8723fac40f`、session `b733f220-534f-4411-b960-5caabd1ed73e`，API49173／daemon49190／CLI49211／shell49210。先核对原PASS、恰三Messages与无api-error；认证daemon_stop并确认原CLI/shell/daemon退出，API完整命令/root及双读lifetime后最多一次SIGTERM，确认退出。归档到外置 `p1-materials-slice1-green-3/cleanup-185/fixture.tar.gz`，逐成员读回、四PID仍不存在、库存未变后才删此根。未知／PID复用／缺盘即BLOCKED，不强杀、不删。

slot单列：`/Volumes/WD-Elements/a2a-workbench/t078-slice1-c4a5dc22-7d3f-430d-8e82-1b8723fac40f` 本轮保持；所有旧slot也不动。后续主控如批准，另冻精确路径清单、所有权／应用退出／引用核对与删除脚本。cleanup代码不包含slot处置。当前实际cleanup INCOMPLETE。

## 拟冻结的 09B 结构

同一新 broker/state/repo/project/task，两个实际Claude角色、一个受管确定性C接收目标；目标不是实际Codex，其日志仅为Codex形状，模型0。角色各自 `roles/<preset>/home,claude,tmp,shell,requests,hooks,user-data,debug`，独立session/thread/launch/API；不读用户认证、不共享HOME或请求目录。拟argv固定2.1.296、Haiku5.5/low、manual、Bash/Read、空MCP、既有三hook；能力值仅实际daemon签发，材料不造worker attempt/fence。

目标必须通过任务卡→实际受管dispatch/claim取得attempt/session/fence/worktree/launch及活进程身份；字段未取得时是未绑定，不能用null／假字串代替。任务卡模板显式oracle_paths=`oracle/contract-09b.json`，在初始夹具Git基线保存。卡禁止目标误提交候选；真实stop/ack验证依据独立oracle.json的运行观察，不能用卡的失败保护当验收。

**Tracer bullet**：单角色已真实通过，再扩实际ideation发送、executor执行及ack。**Deep modules**：沿原writer/relay/caller/gates与队列，不添operator业务代理或并行门禁。**Ubiquitous language**：queued／执行收据／实际投递／ack分开；阶段I1/E1是场景标签，不等于共库的dispatch.seq。

## 因果序列与独立反例

拟预算：ideation **4根／6主Messages**，executor **6根／11主Messages**，合计17；各不超过 #163 审定6/12、合计24，供应商模型0。共有7个预声明Bash调用；每个实际许可屏分别审批，一次Yes，不永久allow或auto。每个有工具根产生tool_use/真实queued tool_result两次Messages，再由真实Stop执行并登记后续反馈根；确认根一次Messages。没有无限重试或补根额度。

| 阶段 | 真实根的输入与动作 | 必须看到的实际结果 |
| --- | --- | --- |
| I1 | 一条批准的test-simulated-user窗口stop请求；库send，故意`--from executor` | from仍ideation；唯一真实stop，投递executor |
| I2 | 真实send执行反馈；只确认 | 原发送根与反馈根结算，不新增业务 |
| E1 | 真stop唤醒；对ideation线程尝试stop | worker_target_required，无目标Esc |
| E2 | 真实E1拒绝反馈；对实际受管目标stop，故意actor=user | actor仍executor；一次真实Esc，目标进程及attempt保留 |
| E3 | 真实E2成功执行反馈之后才ack，故意role=ideation | ack实际from=executor、reply_to同stop，真唤醒ideation |
| E4 | 真ack结果反馈；新库调用／新request_id重复ack | 原ack ID相同，无新ack／wake／Esc |
| I3 | 真executor ack投递；ideation尝试ack原stop | recipient_required，无越权ack |
| I4 | 真实I3拒绝反馈；只确认 | ideation最终Stop／idle |
| E5 | 真实E4反馈；对已ack stop再调用stop | stop_already_acknowledged，无第二Esc |
| E6 | 真实E5拒绝反馈；只确认 | executor最终Stop／idle |

I/E事件可交错，不要求表格行对应墙钟全局顺序；关键依赖是E2真实成功在E3 ack之前。server／driver只接受实际登记完整文本与实际stop/request/inbox ID；不能按单角色写死#1/#2或从API自己生成expected。假服务只发精确批准工具和中性确认，不能编造预期业务错误、seed stop/ack或替角色执行。

独立oracle还要求目标最终received.bin等于“初始派发完成后的baseline＋单Esc”，不把bracketed-paste字节当中断；同PID/start/leader及attempt/fence不变，没有kill/reclaim/archive/submit。两角色实际hook/session/prompt、tool ID/command、真实relay/inbox与三个绑定窗格观察齐全。wrong-session／revoked-token另走实际认证入口反例；未运行不称权限规则已证明。

## 当前前置和审阅边界

[静态源码探针](09b-profile-preconditions/results.json) PASS的是现状事实：两个preset共享六路径，第三根被`invalid_controller_turn_limit`拒绝；09B合同INCOMPLETE。claudeLaunch与Panes.signal仍仅1/2，不能用计划argv绕开。非blocking [问题上报](ISSUE-09B-PROFILE-PRECONDITIONS.md) 先提最小路径预算11；本包加入实际wrong-target／foreign-ack／acked-stop反例后，最终拟预算17，以本包为准。

审阅后应先统一角色目录并同步P1夹具、把批准的4/6根贯穿同一profile与signal核对；再实现共库双角色fake API／逐次阶段驱动及oracle执行器，真实入口红绿和边界反例后另冻**可执行launch包**。不得删除根校验、共享目录fallback、使用静态prepared记录冒充live登记或让operator发stop/ack。当前包明确没有启动driver，argv/env是proposal，不是通过当前生产构造器的配置。

## 提交与生成步骤

先运行成功场景cleanup（`--approval-ref "主控 #185"`），PASS后按原身份运行 [commit-closeout-and-09b-materials.sh](commit-closeout-and-09b-materials.sh)。第一提交保存真实green-3读回、cleanup、#184结论、前置事实与本轮材料脚本；随后 [prepare-09b-plan.py](prepare-09b-plan.py) 生成新 `09b-materials-01` 提案IDs／目录／角色卡、protocol/oracle/card/空approval模板与source tar，逐文件与Git读回，再作材料提交。没有Git初始化／编译目标／服务／CLI／UI启动。

审阅文件为plan.json、protocol.json、oracle.json、task-card-template.json、两role.md、actions/launch-approval-template.json、static-check.json。生成静态PASS只说明计划冻结／预算／源码字节正确，launch仍NO_GO。09C仍等09B实际通过后单独新冻结，保持真实>120000ms且总观察≤150秒；本轮不生成C实例，不快进时间，不关闭T-078或集成/push。
