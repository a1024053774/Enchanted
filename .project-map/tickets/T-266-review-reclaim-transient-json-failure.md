---
id: T-266
title: 审查正常 Stop 后自动回收遇到 JSON 读取失败并停在未知状态
type: build
status: open
blocked_by: []
claimed_by:
supersedes:
ready: no
ready_by: executor
ready_rev: 1
---

## 已观察事实

2026-11-09，T-249-2 的独立审查 d20988dc-95ec-4424-8f62-07d1ef2d052f 正常提交“需修复”，门禁接受结果并向原 worker 派发修复回执。原生 Stop 已记录 pane_idle。随后 reclaim 阶段抛 `SyntaxError: Unexpected end of JSON input`，task 变 paused、review 变 unknown；同一 reviewer 的 pane 被标 `queue_stopped`，active 为空但仍运行，failed 标记保留。

稍后正式 pane_process_info 成功，返回原 shell 96754、leader 96757、native session 01a1c043-77e7-7581-b738-863f336d7934，但不会清除 failed。原始结果和身份查询在 evidence/2026-11-09-batch35/T-249/controller-package/terra-a5-review-status-04.json 与 terra-a5-review-reclaim-process-info.json。此故障不同于 T-264 的额度错误，也不同于应用更新后旧 node_repl 的路径读取失败；目前没有足够证据确定是进程观察输出还是原生日志解析抛错。

用户授权来自当前对话“修复现在 enchanted故障并继续”“主线是完成主要的两个面板的任务以及 bug 修复”。本票只恢复已经完成审查的生命周期，不放宽身份、回收或审查结论校验，不手改正式数据库，不用合成 Stop，不把“需修复”变成通过。

## Acceptance

- [ ] 经真实入口保留可定位到具体解析源的失败证据，并确认根因；一过性读取错误与身份冲突分开。
- [ ] 已接受审查结果与 worker 修复回执保持一次性；回收仍核对原 task、attempt、review、session 和实际空闲身份，失败后可经正常入口恢复。
- [ ] 已知坏实现命中业务反例；外部状态未知、原进程仍工作、身份替换、重复回收均不得误放行。
- [ ] 独立审查、回归与自有夹具清理完成；真实正式数据未手改。

## 当前状态

INCOMPLETE：尚未定位解析来源或修改产品。原 worker 已完成修复检查点 c16489e2d435513a00bfa3b61ec2ae346549bfb0；重交因 task paused 被拒绝。主控在实际输入框清空、原生回合停止及 Git 干净后正常重启后台，旧进程已结束；T-249-2 的旧 attempt 经 abandon（升级）及 reclaim 成功，检查点由 Git 保留，card/spec 6 仅接回该证据进行一次限定复审。重启及门禁原始输出位于本票 controller 和 T-249/controller-package。恢复不证明本缺陷已修复；正式数据库未手改，原审查需修复结论及故障证据保留。
