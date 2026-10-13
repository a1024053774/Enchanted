# T-076-2 独立交付审查：槽7审批

状态：**INCOMPLETE／审查未启动**。实际6/8；原真实正例的超大日志已归档并字节读回，archive-real-log-01为PASS，原run.json的INCOMPLETE/archive_required保持历史原文。本卡交付审查是独立于产品reviewer的另一件事。

按 #86“若需真实Codex先交argv”提交本实例。可用子代理接口没有显式service_tier=default参数；为满足用户的每会话覆盖要求，采用新真实交互CLI，而非无法核实档位的调用。请求槽7仅一个审查主回合，不调用槽8，不继承原生会话、不续接、不纠格式或自动重试。

冻结TARGET为delivery-review-01，基线a7f4cc30，当前HEAD为15f28e449f2c7c63af9914e399237ee08ac7ec9c；142个源/测试/治理输入文件，含批准的acceptance修改，候选、baseline及diff在[delivery-review-01/candidate](delivery-review-01/candidate/)。完整列表见[manifest.json](delivery-review-01/manifest.json)。没有实现聊天、PLAN或RESULTS。独立契约、证据边界及结构检查要求见[CLAIM.md](delivery-review-01/CLAIM.md)，提示词包含完整behavioral-acceptance-review及agent-products要求、同次结构审查要求；[PROMPT.txt](delivery-review-01/PROMPT.txt)为唯一主输入。

| 项目 | 固定值 |
| --- | --- |
| 根（运行前不存在） | `/private/tmp/a2a-t076-delivery-review-01` |
| CODEX_HOME | `/private/tmp/a2a-t076-delivery-review-01/codex-home` |
| 唯一信任的自建Git候选根 | `/private/tmp/a2a-t076-delivery-review-01/candidate` |
| Codex | `/Users/luckye/.codex/packages/standalone/releases/0.162.1-aarch64-apple-darwin/bin/codex` |
| 模型／强度／档位 | gpt-6.1-sol／xhigh／显式default |

完整argv在[argv.json](delivery-review-01/argv.json)和[argv.txt](delivery-review-01/argv.txt)，无动态ID或省略参数；最后一个参数是完整冻结PROMPT，作为原生交互CLI的初始提示词，仅一个输入。参数含--no-daemon、--no-alt-screen、-C固定候选根、-a never、--sandbox read-only、-m gpt-6.1-sol、model_reasoning_effort=xhigh、service_tier=default、关闭更新/通知/工具网络。它不是codex exec或无头模式，必须在执行主控自己创建的交互TTY/pane运行。

home仅复制auth.json（0600）及新建单候选根trust config，无rules，无Git写许可，不复制用户配置/hook/插件/历史。没有任何自定义会话hook或Git尾注hook；审查员不能submit/integrate或写报告文件。完整最终报告从原生task_complete.last_agent_message取回，不按终端done/idle或关键词猜结论。要求唯一source=cli的session、唯一匹配task_started/task_complete、模型/effort/read-only/never可读回，候选Git干净；保存全部原生日志和原始REPORT，不做自动语义裁决。

准备/启动/收集均由执行主控在沙箱外进行：

1. 审核并写`delivery-review-01/APPROVED.json`，内容为`{"approved":true,"policy":"T076-2-delivery-review-01","slot":7,"root_turn_limit":1,"decision_ref":"实际批准引用"}`。
2. `zsh evidence/2026-10-11-batch13/T-076/card-2/outside-sandbox.sh prepare-delivery-review delivery-review-01`。仅准备已批准的隔离home/候选Git根，冻结字节不符、预算已另预留或根存在即停止；append槽7 reservation，不启动模型。
3. 在自己新建的交互pane/TTY运行生成的`outside-delivery-review-01/launch.sh`。脚本要求TTY，记录其CLI PID，再exec上述完整argv；不要另发主输入、Enter或ACK。启动不就绪/权限等待即保存并停，不重发。
4. 单回合最多900秒。确认原生日志task_complete后，仅停止本次CLI；PID以launch.sh保存的cli.pid核对，不按名字杀进程，不碰Herdr server/他人的pane。超时、权限等待、第二个turn/session或未知也停止保存，计入槽7；不要启动第8槽。
5. 把home/sessions复制到本卡审查证据，取唯一完整task_complete的last_agent_message为REPORT.md；读回实际model/effort/sandbox、服务参数与native计数，append槽7 observation。Herdr可见状态只帮助确认退出，不能替代报告。
6. 核对CLI及其自建进程退出后删除整个CODEX_HOME；不能确认则保留并报BLOCKED。auth不入证据/tar/Git；只保留候选快照和原始报告。大文件按既有压缩/外置盘规则处理。

审查发现可达问题时先保存报告，执行worker按原卡“先取红态再修、修复diff交主控”处理；不得把提出意见当修复。若结果PASS，执行worker再核对冻结字节、更新RESULTS/Resolution并提交带新launch尾注；不push。当前尚未做此审查或交付提交，READY停在本实例审批点。
