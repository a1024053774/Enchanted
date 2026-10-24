# T-164-3 / a2 运行记录

状态：INCOMPLETE（原混合 CLI 全流程）；主控 #89 指定的“A 集成后收尾”已完成。A 门禁 accepted/completed，B 保留待 T-170，C 不派。

- 测试 worktree：`/Users/luckye/Documents/Code/a2a-wt-t164d`；分支 `exec/t164d`；起点 `2907db9522a2a8a07b95a358f72437eb60851409`。
- 产品版本：`e3b14d27b5f0f94ee65d1e15a69d6c90c1eafc5d`。
- 实例：`/private/tmp/t164-dogfood-0zw8tib0`；Electron 初始 PID 23877，REOPEN 后 46099，daemon PID 23874 不变（均由执行主控提供）。窗口 renderer URL 已对应本实例；进程表读取被沙箱拒绝，未提权。
- Computer Use 仅经 node_repl + @oai/sky，固定使用主控指定 Electron.app；业务流程没有用 CDP、DOM、外部门禁命令或数据库驱动。生命周期由执行主控管理，未读认证或 operator.json。
- 开跑额度：主控 quota-start-2.md 为 5h 100% left、周85% left；本会话日志首读 13:20:45.839Z 为5h已用2%、周16%。收尾核对 14:23:42.203Z 为5h已用51%、周23%，未触发90%停线。逐次日志读数见 quota-observed.jsonl；不是本地 /status UI。后续仅提交交付，读数不含提交后的少量外层消耗。
- 中文直接 type_text 丢字，清空未提交草稿后使用粘贴并核对；目录选择器输入一度截断，未确认旧路径或打开其他项目。截图与AX只作为其记录时点证据。

## 实际步骤

1. 打开本实例 demo-repo，启动 Claude Code 2.1.310 / Haiku 5.5，仅信任本实例repo。
2. 设置Codex worker为zcode/GLM-5.3-Flash/max，Fast关闭；开启本窗口读屏支持。
3. 申请执行主控，批准并确认；记录页有角色事件#37，指标页明确主控未覆盖、汇总未知。
4. C2提出三票，A/B并行，C随后；A打回演练，B先issue等待面板答复。完整提示见prompts.txt。
5. A首候选5510c3c43f3c87e97d9c441ddd704701fab6326b被真实oracle_failed（缺总计6）；修复工具调用期间输入A1，重交68803065ef6ffc0d6f1743d8b2b52f4972ddbf60；交付后输入A2收到回复且侧栏空闲。#405 queued→#419 submit ok→#421 absorbed→#422 idle；第二输入#495→#498 start→#523 Stop→#527 idle，随后正常回收成功。详见报告T-169节与readback a_timeline。
6. B先issue分组问题，面板答复不分组；候选e81bea0050b3b37b7c3998298f3c8124e1c8e8b0已交付。终端状态行实际GLM-5.3-Flash / ZCode max。
7. A机械通过，独审06209cdb需修复：错误分类数与总计夹带正确数字仍过；审查协议有效受理。主控按原目标修订。
8. B任务向右分屏保留B与新普通项目终端，未向新终端输入命令。
9. B verify被path_boundary_failed拒绝：主控误把shopping.md同时列allow/deny。worker报blocking issue；主控按授权修卡，不改活跃旧合同。A检查器与golden移入受保护acceptance/；A/B原attempt经普通reclaim后分别重派。
10. A a2首交f998b823再次缺总计，真实打回后重交caa797e488a459e5c8835ebb472aa7d931afeb0b。B a2启动即退出1，account/read failed / workspace routing discovery timed out (-32603)，launch_failed，无原生会话；外层裁定不停线。主控普通reclaim仅一次，identity_conflict，未绕过。
11. 依外层REOPEN回传新Electron PID46099，核对本实例URL，重启读屏支持，原daemon、任务与历史保留。B保持现场。
12. A a2独审651cb515纯JSON的review_requirements值无效被拒并暂停；在问题页为同次交付新开e2d0d578，获得有效需修复：遗漏“不写逐项明细”的检查。主控在原目标内修检查器，card v3/spec3，正常回收A a2再派A a3。
13. A a3首交547b261a18f0fa4e021d7b176960bfaf8bf9edbb已含总计，没有重复卡内缺总计演练；主控如实说明。verify通过，独审2efe38e0有效可合并，正式命令通过、5个变异被拒。
14. 主控打分（边界纪律3/3、工程品味3/3），经唯一门禁集成到dogfood，accepted/completed，G=476cfb246c1d0d0d18d5f3949e778c8c49bc449e，C=M=547b261a18f0fa4e021d7b176960bfaf8bf9edbb，verification d97ce072-ad6c-4f5f-8a23-8df68d4bcc28。权威回执见integrate-A.json，图a3-integrated显示passed/completed；事后只读show-ref核对dogfood已更新，main仍554b8b215ba2c9ad59091bb89ed7d997fa8d530f，无push。
15. 手动Reflect已完成一次，范围最早至2026-10-24T13:48:55.163Z，Haiku/medium，11条建议未批准。最终仅查看既有结果，没有新跑复盘；不包含末段集成。报告副本reflect-report.md保留模型原文，不把建议当已核事实。

## 身份、模型与回合

终核截止event #1927，观察时间2026-10-24T14:10:07.435020Z。脚本只读sqlite、选取事件和本实例原生日志，不读凭据或记录env。Claude计数排除isMeta及tool_result，只数原生user根消息；含门禁自动回执，不把工具结果算新回合。助手实际模型字段另见claude-native-models.json，全部claude-haiku-5-5。

| 会话 | launch / 原生session前缀 | 实际根回合 |
| --- | --- | --- |
| Claude执行主控 | 1db10a88 / b17ffdd6 | 12 |
| A a1 worker | 46e72ed2 / 8b68c853 | 6 |
| A a1独审 | 3576534a / 2c177420 | 1 |
| A a2 worker | 1da78f0e / 510a5c07 | 6 |
| A a2无效独审 | 1c5f12ee / 711549e1 | 1 |
| A a2重开独审 | 60af63d7 / 9b305d36 | 1 |
| A a3 worker | c7105f8e / 0ebb7155 | 2 |
| A a3独审 | d0e9a195 / 82926ea0 | 1 |
| Reflect | 非受管launch / fe2f217a | 1 |
| Claude合计 | 低于60上限 | 31 |
| Codex B a1 | 8b252677，GLM-5.3-Flash/max | 6个实际turn_context |
| Codex B a2 | 51773fcf，请求GLM/max，实际未建立会话 | 0 |

B a1的5次后续消息均自行开始：门禁#4、用户#7、门禁#11/#12/#13。本地提交至开始分别0.173、0.127、0.153、0.127、0.140秒（以readback精确值为准），只描述事件间隔，不作为模型响应速度或性能收益。首派冷启动另为8.085秒，不能混算。完整argv、task/attempt/session/fence/spec版本在readback中；Reflect启动配置以界面已完成行及原生日志为据。普通项目终端里用户手启的主控命令见证据07，不能冒称其shell启动argv就是Claude完整argv。

复现统计命令（输出新文件，不能覆盖旧观察）：

```sh
python3 evidence/2026-10-23-batch24/T-164/rerun-3/readback.py /private/tmp/t164-dogfood-0zw8tib0 evidence/2026-10-23-batch24/T-164/rerun-3/readback-new.json
```

原实例或原生日志被归档后，应由执行主控按归档位置恢复该只读统计所需路径。该命令不重放业务，不保证重新执行会取得相同模型输出。

## 截图与AX索引

截图均在screenshots/；同名AX在上层。AX多为增量树，需结合前后文。少量图片在点击后更新尚未完成时捕获，按下表限定用途，原图不替换。

| 截图 | 用途/限制 |
| --- | --- |
| 05-project-terminal.jpeg | 项目终端入口 |
| 06-glm-settings.jpeg | GLM/max、Fast关闭的请求设置 |
| 10-role-approved.jpeg | 角色批准阶段，精确最终身份以11-role-confirmed.ax.txt为准 |
| b-start.jpeg | B实际GLM/ZCode max状态行 |
| 16-a-midtool-input.jpeg | A工具调用中人工输入阶段；精确调用与时序结合AX/事件 |
| 19-a-postdelivery-input.jpeg | 第二次输入阶段；最终idle以a-second-input-state.ax.txt和事件为准 |
| 20-flow-a-b.jpeg | A/B流程状态 |
| 22-b-task-split.jpeg | 初次任务分屏阶段；左右身份以22-b-task-split.ax.txt为准 |
| 24-b-a2-unknown.jpeg | 更新滞后，实际是主控画面，不能证明B错误 |
| b-bootstrap-error.jpeg | 已核对的B启动路由错误 |
| reopen-46099.jpeg | 重开后实例；对应reopen-46099.ax.txt含URL |
| 27-a-a2-review-protocol-issue.jpeg | 审查协议暂停阶段 |
| a3-integrated.jpeg | 已核对最终任务页：候选547b261a18、passed、completed |

其他关键文本：a3-review-pass.ax.txt为有效审查及5个变异；a3-integration-done.ax.txt为主控集成回执；a3-integrated-full.ax.txt为稳定完整终态树；reflect-final.ax.txt为复盘完成和11条未批准建议。报告、提示原文及小JSON可入库；没有复制sqlite、认证文件或完整native日志。

## 裁定、异常及未完成

- 外层明确答“该超时不属停线，允许继续”；REOPEN由主控执行并回传PID；#89确认B启动外部失败与产品回收缺陷分开，T-170外层修，本轮仅A集成后交付。相关消息的原始来源是外层主控对话，不能伪造为应用内真人输入。
- N05现场源文件为/private/tmp/t164-dogfood-0zw8tib0/cards/status-B-a2.json；此处保留其小文本副本及唯一普通reclaim拒绝回执。未重试、未绕过、未重派B。
- 任务层与attempt层卡快照ID不同，主控核对verify、review、integration均绑定attempt的291799d7/spec3/card v3；完整记录保留，不凭模型一句“无误”抹去差异。
- Reflect列表重开审查“未归属”、主控lcu Stop-hook错误、中文输入及选择器截断均如实记录在发现报告；未越范围调查实现或改环境。
- 未完成：B机械通过、Codex独审和集成、C、第二新实例重复、原始运行归档和隔离认证清理。前者按裁定停止；完整实例保留，原始归档、生命周期与凭据清理由执行主控处理。外置归档未由本worker执行，不声称已完成。

未跑产品自动测试、未改产品或oracle；本次验证是指定实例中的真实UI流程与事后只读对账。最终项目状态与报告交付检查另见delivery-checks.md。
