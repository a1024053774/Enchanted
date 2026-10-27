# a2a 开发发现

这里集中保存开发过程的发现、复盘与相关报告。任务状态仍由 [project-map](../.project-map/MAP.md) 管理，原始证据保留在 `evidence/` 和对应 session 中。

按用户要求，报告只保留中文版本。采用明确主体、统一术语和保留条件的写法，不将英文 STE 检查结果当作中文合规证明。

## 分类口径

2026-10-06 按用户更正：**有已授权工作可继续却结束回合，属于主控 GPT 的模型行为问题，不属于分工协调问题。**

| 类别 | 本次内容 | 文档 |
| --- | --- | --- |
| GPT 模型行为 | F01 提前结束回合，以及具体状态解读和中断判断。责任归主控模型，不转成协调层整改目标。 | [模型行为记录](gpt-behavior-2026-10-06.zh-CN.md) |
| 分工协调 | F02–F05：研究交付合同、夹具规范范围、子 agent 清单、监控任务及发现处置。 | [过程复盘](a2a-session-retrospective-2026-10-06.zh-CN.md) |
| 工程与证据处理 | F06–F07：采集脚本、失败分类、大段输出与归档。 | 同上报告的“工程与证据处理发现”部分。 |

T-012 已缩小为[研究阶段产物与移交证据](../.project-map/tickets/T-012-research-handoff.md)。它不再包含模型续执行或回合结束检查。其他协调、工程待办的状态以项目地图为准。

## 相关资料

- [Enchanted 0.1.5 两次真实使用的问题记录](2026-10-27-two-real-uses.md)：用户两次使用均未按宣称走通（NO_GO）；记 U01～U11（项目移不掉、已删仓库拖垮全局认领、agy 显示“未知”、任务页为空、跨路径受限等）及用户提出的方向；U05 经后来的截图更正为非缺陷；U11 路径限制改由主控判断（T-196）。
- [Enchanted 0.1.3 lcu 真实使用实测](2026-10-25-lcu-real-use.md)：构思主控用 lcu 走完申请主控、两票并行、审查打回、修订重派与门禁集成；记 L01～L09（系统授权弹窗致空白、中文字宽、状态不一致等），对应 T-174～T-181。
- [Enchanted 多 agent 真实使用第三轮重跑](2026-10-24-real-user-dogfood-rerun-3.md)：T-164-3应用内Codex改用GLM/max；A有效独审后门禁集成，B启动前失败及回收缺陷N05/T-170保留，原混合流程INCOMPLETE。
- [Enchanted 多 agent 真实使用第四轮重跑](2026-10-24-real-user-dogfood-rerun-4.md)：T-164-4应用内Codex worker与审查员用gpt-6.1-sol high；一次verify拒绝后revise、reclaim、重派，独审通过并门禁集成，PASS。
- [Enchanted 多 agent 真实使用第二轮重跑](2026-10-24-real-user-dogfood-rerun-2.md)：T-164-2额度停线INCOMPLETE；T-167共17次回执/答复/打回自动唤醒，B五次独审未通过，含回收重派、REOPEN、Reflect及采集错误恢复记录。
- [Enchanted 多 agent 真实使用重跑](2026-10-24-real-user-dogfood-rerun.md)：T-164 的隔离 Computer Use 重跑；额度停点 INCOMPLETE，已覆盖混合CLI并行与真实独审打回，尚未集成，含F/M逐条复验及现场交接。
- [Enchanted 多 agent 真实使用记录](2026-10-23-real-user-dogfood.md)：T-155 的隔离 Computer Use 实测、同后台 UI 重开、37 回合终核与 Herdr 对照；证据已归档，完整流程 INCOMPLETE（审查协议暂停与交付未知）。
- [框架、实现与操作说明](herdr-a2a-2026-10-06.zh-CN.md)：包含实际架构、使用步骤和第 10 节的 monitor 观察与利用记录。
- [证据入口](evidence-index.md)：连接三份原始 monitor 报告、20 份 session 的扫描索引、关键选录和产品验收结果。
- [复盘研究 ticket T-009](../.project-map/tickets/T-009-session-retrospective.md)：保存扫描范围、截止点及本次分类修订。
- [Claude 主控与 Codex 的 SiteCraft 实际经验](claude-sitecraft-experience-2026-10-06.zh-CN.md)：指定对话的消息来源、独立验收、版本与材料绑定、资源归属和主控交接记录。
- [图形客户端方向评估](gui-client-assessment-2026-10-06.zh-CN.md)：2026-10-06 的日期记录，比较基于 Zed 二次开发、独立 GPUI、Electron 等路线。其推荐的"Herdr 客户端"路线未被采用；同日 grilling 决定自建工作台（Herdr 引擎硬分叉加 GPUI），见 [intent.md](../intent.md) 与 T-016～T-021。
- [原生 CLI 状态信号与 PTY 注入](native-cli-signals-injection-2026-10-10.zh-CN.md)：T-074 rev 4 的本地提交记忙、Stop 放行、模拟人工 release 验证，以及旧反例与适用范围。
- [ticket 生命周期与门禁检查串的显式图](ticket-gates-graph-2026-10-16.zh-CN.md)：T-087 的日期记录，含可重跑生成脚本、逐点逐边来源、持久化边界与隐式边清单；来源语义抽查另由非作图会话完成（抽查 01 指出的未知结果暂停、审查协议暂停与 model unknown 例外已补；抽查 02 指出的 R2 各分支持久记录已逐支写明）。

`reports/` 中的旧文件只保留跳转入口，正文以本目录为准。分类调整不改写历史消息，不把已经登记的待办写成已经完成的改进。
