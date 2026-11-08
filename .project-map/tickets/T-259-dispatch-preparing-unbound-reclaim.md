---
id: T-259
title: dispatch 在窗格创建后、身份绑定前失败，preparing attempt 无法经门禁回收
type: build
status: open
blocked_by: []
claimed_by: executor
supersedes:
ready: yes
ready_by: executor
ready_rev: 1
---

## What to build

### 本轮隔离修复例外（2026-11-08）

工作台连本票派发都失败、两个 preparing attempt 正常回收被拒后，用户对“由我在隔离工作区完成 T-259 修复并准备独立审查，交你看候选与测试证据后再批准安装，随后恢复原门禁继续 T-258、两个面板”的问题回答：

> 允许一次隔离修复例外（推荐）

此授权仅限本票隔离修复，不包含手改正式数据库或跳过最终审查。工作区 `/private/tmp/a2a-t259-repair-20261108`、分支 `codex/t259-preparing-reclaim`。当前修正版候选 `2083f72e4f43d6bc84be2ef57b5fef49f65e1bcb`；首候选 `fb96f5aee181035a1fc810ead1e952dba10cbef8` 独立审查发现归档后中断恢复缺口，已先复现再修复，证据保留在候选的 `evidence/2026-11-08-batch34/T-259/review-01/`。修正版 310 项边界、普通及归档中断真实后台入口通过；唯一一次针对性独立复审 PASS，见 `evidence/2026-11-08-batch34/T-259/review-02/REVIEW.md`。尚未安装或集成，不将本票标为完成。

用户另允许点击本次 Enchanted 所需权限提示，包括新构建访问文稿。新增界面问题已登记 T-260（问题状态）、T-261（最新任务在前及折叠）、T-262（记录分类排序），恢复门禁后与 T-249/T-250 主线继续。

用户本轮针对“先正常重启并修复 T-258 这类启动恢复问题，再继续两个面板”回答：

> 修启动阻塞后继续（推荐）

本票是执行主控在上述启动恢复范围内登记的阻塞缺陷，不改变 T-258 的冻结验收。先完成本票，使 T-258 能恢复独立审查，再继续 T-249/T-250。worker/reviewer 为 gpt-6-astra xhigh 普通速度；不启动 Claude，不 push，敏感变更仍需用户读证据批准后集成。

2026-11-08 16:57Z，T-258 第三次 dispatch 返回 gate_failure / SyntaxError: Unexpected end of JSON input。门禁已创建 attempt 和 worktree，窗格已启动；runtime_identity 仍为 null，task/attempt 为 preparing。没有 claimed、prompt_intent、dispatch_created、turn_submitted 或原生回合记录；现场窗格 idle、active=null、queued=[]、native_session=null。一次正式 reclaim 返回 identity_conflict。错误回执与身份见 [现场](../../evidence/2026-11-08-batch34/T-258/controller/prepare-attempt3-refused.json)。

绑定：task a2a+T-258-1；attempt 3bba04f2-9ea5-4148-960f-c699720eca78；session bcc5addd-6f15-4ed0-8d2e-9c026aba7b38；fence/spec_rev 3；thread 6e9b2c8d-9fc5-4b15-a45b-4fe198c5bda5；launch 4f3a203c-a63d-44a6-b3e6-edcf4b5fc3dd。源码基线 fa8d554c87210c15a7944542b2e9cfff3362ee8d。原始 dispatch 请求 80cebbbc-dba2-44cf-bef3-b2b45d2f65e3 结果已知失败，未重发。

REALITY GATE: INCOMPLETE。代码证实 claim 在 createThread/readThread 成功后才保存 runtime_identity；reclaim 的 checkThread 必须有已绑定身份。因此准备中断可留下无法回收的 attempt。JSON 解析异常的具体来源尚未确定，不能称为 rollout、磁盘或 CLI 的已证实缺陷。

目标：通过现有门禁入口，安全处理“确属该 attempt、从未发出任务输入”的准备失败；记录故障和身份依据，确认停止与归档后才释放路径。不得自动重发任务、把未知外部副作用当成未发生、只凭工作目录相同接管窗格，或清空正式数据库。T-253 的原生身份绑定决策 B 保持；本票处理的是初始运行身份整个尚未落库的准备失败。

## Acceptance

- [ ] 使用真实 A2AGates 的 dispatch→失败→reclaim 入口复现；先从独立契约列预期，已知父版在“可核验的未发送准备失败能回收”断言判红。错误必须发生在真实创建之后、初始身份落库之前；不能把只写数据库伪造状态当唯一证据。
- [ ] 候选中，确属原 attempt 的未发送准备失败能经门禁确认停止、归档与回收，再派同一任务；保留原错误、身份/版本/attempt 证据，输入及任务动作不重复执行。
- [ ] 不同 launch/thread/shell/attempt/session/fence/spec、工作中、已发出或不能判定是否发出的输入、缺失可信创建记录、操作锁冲突继续拒绝；拒绝不停止其他进程、不释放其他 attempt 的路径、不删除脏工作区或失败证据。
- [ ] 正常 dispatch/submit、T-253 原生身份绑定与 T-170 启动失败回收保持原有契约；覆盖后台重启前后的相关边界，或明确不可恢复情况及证据。
- [ ] 新增检查在父版及 2–5 个独立变异上命中业务断言，候选通过；写明每个检查的依据、命令、退出码、版本、清理结果与未运行项。真实正式现场只读；必要的真实 CLI 探针在隔离后台运行。
- [ ] 门禁独立审查通过；改到敏感回收/清理代码时完成两项 review skill 并取得用户阅读证据后的集成批准。

## 不做

不修改 T-258 候选、panes.ts、面板实现、角色权限、凭据、schema/migration、公开接口、全局配置或验收文件。不重试来源未知的写操作，不扩大为普遍身份重绑定。不直接修正式状态；部署后才用门禁处理原 attempt。若最小正确修复超出此边界，先上报。
