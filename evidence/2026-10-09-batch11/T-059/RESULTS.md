# T-059 首次模型调用前交接

**BLOCKED：Claude 认证、模型及额度尚待用户决定。ticket 保持 open，待主控关闭。** 本轮只完成非模型探针和一个聚焦合同红态，没有产品实现、完整端到端绿态或整票验收。依据主控 #25、[brief](../brief-T-059.md)、T-059 ready_rev 1、spec 第 1、4、5、6、7 节（brief 将 S5 写成第 8 节，实际在第 7 节，按 ticket 引用的内容核对）。

fork 基线 `49cae984f22924de006e0f8358cb447eb881aaf6`，没有 fork 候选提交；本票产品验收新增真实 Claude/Codex 模型 turn 均为 0。认证来源和预算请求见 [needs-decision-04](needs-decision-04.md)，blocking issue 为 [20261010T145554Z-worker:s11-t059-issue-001](../../../.project-map/inbox/20261010T145554Z-worker:s11-t059-issue-001.md)，发给 triage，由执行主控转构思主控请用户决定。本轮 Herdr 交付用 a2a 证据提交及 DONE 行，不走业务门禁 submit；未 claim/submit/verify/integrate 真实 worker，未触及其它 attempt。

## 已完成与边界

| 检查 | 实际结果 |
| --- | --- |
| 项目地图开工 | PASS：Problems 0、Stale living docs 0；结尾另存 status 输出 |
| 前置票 | 已读 T-055/RESULTS-03、T-056/RESULTS-05、T-057/RESULTS-03、T-058/RESULTS-02、T-064/RESULTS、隔离修正及各 ticket 的最后关闭决定。旧审查失败和版本边界未上调。当前默认能力、用户自定义与仅两家 provider 免确认沿用已定方向 |
| 认证环境 | PASS（无模型构造探针）：[environment.json](auth-preflight-01/environment.json)直接运行现有构造函数，假值继承凭据被清除、显式假值保留、所有凭据文件查找均在 owned /tmp；不是登录/API/Keychain 验收 |
| CLI 与 SDK | PASS（版本/help）：原生 CLI 2.1.296、SDK 0.3.259；只在独立空 home 运行 version/help，未生成文件，未调用模型。完整 argv、cwd、环境白名单及输出在 native-cli-03 |
| 父修订合同红态 | 已取得聚焦红态（脚本退出 1）：真实禁用 provider 的隔离服务，两个 Claude controller 预设不传 instructions 均返回 invalid_path；手工提供中性 instructions 的正对照成功。期望来自“预设注入首条角色卡”，不是从实现复制答案。见 [观察](setup-parent-red-02/contract-observation.json)、[对照](setup-parent-red-02/existing-presets-positive-control.json)。还未取得完整闭环端到端脚本的红态，不勾 ticket 第 1 项 |
| 进程与现场 | PASS：仅本票创建的 detached 隔离服务以自有 Popen 终止、wait 读回 exit 0；原目录留外置盘，SQL/Git/oracle/instructions 已归档，不登记 gitlink。没有认证副本或凭据令牌签发，临时无秘密探针目录保留 |

Tracer bullet 下一步是控制任务、两种角色预设、首条卡与实际任务窗口，再扩展真实模型闭环。Deep modules 保持门禁业务、操作锁、身份与 inbox 在原核心，不另实现一套派发/验收。Ubiquitous language 沿用 ideation/executor、task/attempt/thread、问题、处置、答复与 report。

## 五种失败方式的处理设计

这些是待实现/待验证的设计，不能写成已经通过。

| 失败方式 | 处理方式与下一轮证据 |
| --- | --- |
| 构思主控压缩后丢角色卡 | 预设持久绑定；首条消息注入卡，inbox_list 再返回该角色的卡。卡中要求每个工作周期重新读取；不依赖压缩摘要记住权限。测试直接清除驱动历史后核对当前持久角色返回，不为了压缩另耗真实模型 turn |
| 唤醒到达时长工具调用未结束 | 沿用现有原生 queue 与追加式 inbox；已排队/已投递消息不冒称对方已处理。对方恢复时先查未确认条目；未知送达不重送。真实停止场景保留 busy 期间条目、队列、后续 ack 的独立时间线 |
| 两个主控同时改同一文件 | 角色卡明确写入归属：构思主控写 ticket 正文/ready，执行主控只写认领/验收/Resolution；已认领正文修订走 revise。测试夹具分别写不同文件段/记录，保留 CAS 与追加记录；提示词写入范围不冒称路径级强制保护，真正冲突停下上报 |
| report 写一半会话结束 | 完整 report 正文先在自建夹具文件成形，随后一次 a2a_inbox_send；没有完整追加 report 时不宣称完成。原 inbox SQL 的追加式记录是交接事实；接收方核对 ticket、状态、版本与待决定项。故障探针在发送前中断，确认无半条 report，恢复后显式发送，不自动重试 |
| stop 重复确认 | 复用核心 inbox_ack：同一收件角色/原 stop 返回同一 ack id，不重复追加或唤醒；stop 中断与 ack 是两件事，不用 ack 代替已停止证据。核对原始中断命令数量、原生状态和两个 ack 回执；过 2 分钟且无 ack 才允许窄 stop，不能回收/验收/集成 |

问题场景按 spec 保持“一条用户答复 + 一次关闭告知”送回同一 worker，不为“两题打包”的文字放开已关闭问题；歧义与源码依据一并列入待决说明。面板关闭理由、等你决定、发送后的确切消息与输入记录，都需要下一轮真实验证。

## 未运行与复现

未实现控制任务预设/UI/角色卡恢复，也未运行完整分发→执行→验收→汇报、问题面板截图、三种真实停止、用户试用、绿态、反事实后绿态、产品 fmt/lint/typecheck/相关 Vitest 或独立审查。不用 T-064 的假 API 代替真实主控；没有冻结产品候选，因此唯一一次独立审查尚未使用。用户试用一项及所有 Acceptance 均不勾选；日常派发不改。

无模型重放必须使用全新标签，避免覆盖现场：

```sh
python3 evidence/2026-10-09-batch11/T-059/preflight-01.py NEW_AUTH
python3 evidence/2026-10-09-batch11/T-059/native-cli-probe-03.py NEW_CLI
python3 evidence/2026-10-09-batch11/T-059/setup-contract-02.py NEW_RED
```

第三条在当前父修订预计退出 1，且在 finally 停止自己的服务并归档；完整原始 stdout/stderr、argv、source revision 与各调用分别保留。初轮代码读取有几次 cwd/路径不匹配导致 cat/rg/sed 退出非零，随后在正确仓库重读；它们是调查命令错误，不是产品红态。没有依赖安装、构建、dist 变更、用户 Herdr 操作、用户配置改动或 push；他人的 controller-poll.log 和 fork .grok/ 保留。

本轮交接是等待必需决定的研究/红态证据提交，不是已完成候选或整票 PASS。
