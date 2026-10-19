# T-093 裁定 A：兼容性探针与当前冻结请求 03

**INCOMPLETE。这是待外部事实的工作快照，不是裁定 A 已落地的验收候选。**
task T-093 / attempt a1 / ready_rev 1，worker s16-t093；受管 session 67f986cc-92e4-4089-9c22-802a1143b645，原生 session 01a14ae2-a3df-7731-a7b0-1b679b3bce95，launch launch-45148b6732394eccab3b21224b238513。
用户主控 #79 依据 main c06a73179 的 T-093“裁定”节与 20261018T004018Z-ideation-answer-001 改了 HOME 验收。原审查报告及其 NO_GO 原文未改。

## 本次状态

1. “清单差异不作通过条件”已落实到生产 facts、完整链检查和外层／复验报告；有差异不改 child 的成功，child 失败、扫描／计数／清理等其他条件不变。inventory-policy-red-01／green-01 是该分类的红绿态。
2. 所有父／辅助进程的 OS 禁写 **尚未实现**。现状与目标的逐进程 profile 表、最早入口、FD 与输出位置要求见 [HOME-GUARD-A-PLAN.md](HOME-GUARD-A-PLAN.md)。不拿旧 CLI profile 或只看 launch 环境变量冒称整个进程树受保护。
3. 有一个会改变实现方向的 OS 事实未定：已继承 H 的子进程能否再施加现有 CLI／只读凭据 profile。Apple 安装 SDK 的旧 API 注释不保证它可行；必须实测，不能取消原网络／Security 限制来绕过。

因此先请主控在沙箱外运行下面的小探针；它不运行供应商 CLI、ps、模型、真实上游，不读 auth：

```sh
cd /Users/luckye/Documents/Code/a2a-wt-t093
python3 -I -S -B workbench/tests/probe_t093_parent_sandbox.py --output /private/tmp/t093-parent-profile-01.json --source-revision FULL_FROZEN_SHA
```

输出必须选全新 /private/tmp 路径，文件存在即拒绝；不要把 stdout/stderr 重定向到真实 HOME 的日志。请回传退出码、status、stop_reason 与结果路径；不需要原始输出正文。

## 探针判定与安全边界

- 父进程先同 PID exec 进入 H；所有实际 probe helper 继承 H。报告列 H、请求叠加的 C-probe、合成对照 S、删合成规则的 M，以及每个 PID／角色。若某 profile 不能施加，字段明确是 requested，不冒称 active。
- 实际 HOME 拒写每次只用全新的随机文件名，以 O_CREAT|O_EXCL|O_NOFOLLOW 独占创建，绝不覆盖既有文件；要求被拒且文件未出现。
- 变异选择合成 HOME，保留实际 HOME 禁写及其余约束，仅删合成目录的禁写；要求实际创建并立即删除，created/deleted/absent_after 入证据，且预定业务断言失败。该结果不冒称已在实际 HOME 移除规则做过写入。
- 前后清单在 H 下的两个 helper 只读四个既定范围元数据，差异全部保存，pass_condition=false；采集不可用仍报告 INCOMPLETE，不能补造清单成功。
- parent-probe-safety-02 已在纯合成路径验证创建／删除、既有文件保护及业务拒绝。它没有运行 OS 沙箱，不替代此处的实际 probe。

若 nested_profile_unavailable 或 nested_profile_did_not_enforce，保持 INCOMPLETE，回主控处理如何同时满足所有进程禁写与现有 CLI 限制；不自行放宽权限或另起未批准的进程架构。
若 PASS，worker 继续实现全进程 H 启动与同一 controller_start/hook/Stop，随后再冻结真正符合 A 的产品候选供独立审查。

旧 REVIEW-REQUEST-01／02、旧运行摘要和 reviewer 原文保留历史版本边界。EVIDENCE-RECHECK-02 的完整模式已停止，不能在没有父层保护时对 A 合同给出 PASS；--check-only 只是开发检查。
本次最后一行的 FROZEN SHA 绑定这个待 probe 的工作快照，**不等于 submit、最终审查、验收、集成或可开真实模型**。当前不得集成／关闭本票。
