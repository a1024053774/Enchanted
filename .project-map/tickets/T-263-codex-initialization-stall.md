---
id: T-263
title: 新 Codex 会话停在线程初始化，任务留在待执行队列
type: research
status: open
blocked_by: []
claimed_by: desktop-executor
supersedes:
ready: yes
ready_by: executor
ready_rev: 1
---

## 要查明的事实

2026-11-08 本地晚间安装 T-258 后，T-262 新 attempt 与 T-249 Terra 新 attempt 均已成功创建原生 CLI，但超过八分钟没有 rollout 或 UserPromptSubmit。任务文字在 CLI 的 Queued follow-up inputs 中；应用显示“未知／回合未开始”。这与 T-258 已覆盖的“可信原回合迟到后恢复”边界不同：目前还没有迟到的可信回合可恢复。

授权来自本轮用户“修复现在 enchanted 故障并继续”及后续持续执行授权。先区分系统隐私等待、文件系统阻塞与原生 CLI 初始化问题，不能凭慢启动就清空失败标记、延长期限、重复提交任务或修改全局配置。

## 已有证据

- T-262 attempt `64d48cf7-0cfc-4078-8a13-6f0067297990`，CLI PID 42488；T-249 Terra attempt `acbdf9b4-39ee-4438-a9d9-d23fd21a6031`，CLI PID 43323。正式后台 PID 38234，包 revision `66e88ffe2251ea045a398c9003fef1795c8a2af8`。
- T-262 日志显示已经分配 native thread `01a1be03-da62-79a2-960d-c8e8ce871021` 并生成 shell snapshot；门禁尚未观察到该 worktree 的原生 rollout。只读进程采样的一条阻塞栈停在 `read_dir → __opendir2 → open`，不能据此确定目录。
- TCC 日志有针对新 Enchanted 的 SystemPolicyAllFiles 策略拒绝，但没有捕获到本次 DocumentsFolder 请求或用户答复；这不证明阻塞根因，也不构成扩大到完全磁盘访问的理由。
- 该工具此前拒绝访问 `com.apple.UserNotificationCenter`。已询问用户当前屏幕是否再次出现文稿弹窗；如果出现，需要用户手动点已授权的“允许”，不能换系统自动化绕过工具限制。
- 原始结果在 `evidence/2026-11-08-batch34/T-262/controller/startup-runtime-observation-01.json`、`startup-tcc-01.log`、`startup-pane-cutoff-01.json`，以及 `T-249/controller/terra-v3-startup-cutoff-01.json`。原终端输出和采样保留在这些记录所指的 `/private/tmp` 文件中。

## 完成条件

明确能区分上述原因的直接证据；如果只是等待系统弹窗，记录点击前后同一 attempt、原输入与原生启动的对应关系。如果是可复现产品缺陷，写出真实入口最短复现、独立预期和最小修复范围，再建立受管修复任务。不以重复重启和重新派发替代根因核对。

## 当前状态

INCOMPLETE。两条输入均只送过一次，没有补 Enter 或改正式数据库。T-262 旧工作和检查点仍完整保留；T-249 产品候选已通过原独立审查，但最终 Terra 窗口验收还没开始。两主面板及 T-260／T-261／T-262 的目标继续保留。
