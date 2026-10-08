---
id: T-037
title: 原生 run 编排与人工介入记录
type: build
status: closed
blocked_by: [T-036]
claimed_by: s2-t037
supersedes:
---

## What to build

把 [自动运行](../specs/supervised-run-2026-10-06.md) 的 run 编排移到门禁核心：dispatch 经 Synara 内部服务创建 worker thread（worktree 环境、baseRef 为集成头、明确模型与参数），只有当前 attempt 经 `a2a_submit` 交付才推进，verify/integrate 绑定原 attempt，回收停止并归档本 run 创建的 thread。运行时身份核对 thread、turn 与 worktree。受管 worker thread 中由人直接输入的消息记为人工介入事件。设计见 [spec](../specs/synara-m1-2026-10-07.md) 的"门禁""验证接缝"第 1 项。

## Acceptance

- [x] `acceptance/test_run_e2e.py` 的 18 项按新运行时改写边界替身后通过，替身明确标为隔离编排证据；先在缺失实现时取得红态。
- [x] 反例："thread 空闲或 done 而无 submit 即接受"、"忽略 expected attempt"两种错误实现在业务断言上失败。
- [x] 交付 8 项、恢复 9 项在新候选上仍通过。
- [x] 在受管 worker thread 中由人直接输入，产生绑定 task/attempt/thread 的人工介入事件；非受管 thread 的输入不产生。
- [x] 改写替身与原 18 项的差异逐条记录，不改原预期答案。

## Resolution

PASS（仅限上述 T-037 契约及主控补充的记录故障处理），待主控关闭；status 保持 open。候选 `fa3fc3352805d00e41c454fa6f810807528de3a9`，本地提交 `df9686144`、`a49342189`、`fa3fc3352`，未 push。

- 最终同版本：编排 18/18；交付 8/8、恢复 9/9。无 submit 与忽略 expected attempt 两个 mutant 取得业务红态。
- 人工介入经真实本地 engine/服务订阅证明，来源过滤、原 attempt 绑定、去重均通过。真实 SQLite 写锁故障后只读 status/events/GET 可见失败，全部变更命令（含 reclaim）拒绝；重启记录器回放遗漏消息；在途 oracle 结果记录失败返回结构化拒绝并保留旧验证阶段。
- 原验收未改，18 项边界差异与主控批准的时间输入变化逐项记录。fresh-context 独立只读审查 PASS，限制见报告。
- 证据：[交付记录](../../evidence/2026-10-07-synara-batch2/T-037/RESULTS.md)、[冻结候选](../../evidence/2026-10-07-synara-batch2/T-037/frozen-candidate-03.json)、[同版本摘要](../../evidence/2026-10-07-synara-batch2/T-037/acceptance-summary-03.json)、[独立审查](../../evidence/2026-10-07-synara-batch2/T-037/acceptance-review-03.md)。全仓检查 NO_GO：服务端 4 项失败，其他 workspace 被中止；两个单例复核通过，CodexTextGeneration 的两项隔离进程失败仍存在。源码与基线无差异，范围外未修复。最终检查、归档与 a2a 提交见交付记录。
- 没有真实 provider/model 调用、UI 证明、M1 闭环或切换声明；这些结论仍为 INCOMPLETE，归 T-039/T-040。

**主控关闭（2026-10-08，Claude Code）：PASS，限本 ticket 五项及 observer 故障处理。** 候选 fork `fa3fc33`，证据 `e17e6c4`，见 [RESULTS](../../evidence/2026-10-07-synara-batch2/T-037/RESULTS.md) 与 [独立审查](../../evidence/2026-10-07-synara-batch2/T-037/acceptance-review-03.md)。主控抽查：18 项副本 diff 主要替换 Herdr 边界替身，2 秒 deadline 与 3 秒 run_busy 断言未放宽；两个 mutant 在业务断言（accepted、Git 引用、oracle）上失败；observer 失败处理经 [主控审阅](../../evidence/2026-10-07-synara-batch2/T-037/controller-note-01.md) 提出并以红绿修复。遗留：全仓 test NO_GO（CodexTextGeneration 两项假 CLI 失败，文件与基线无差异，尚未在基线上复跑），fmt 仅 `.grok/` 失败；均记入地图 fog。
