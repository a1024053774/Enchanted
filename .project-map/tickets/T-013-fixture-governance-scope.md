---
id: T-013
title: Make fixture governance scope explicit
type: task
status: open
blocked_by: [T-009]
claimed_by:
supersedes:
---

## Question

如何在任务分派时明确任务仓库、治理根目录、适用规则与验收入口，避免夹具 worker 误用主项目规范？
三个真实分页 worker 都对不含项目地图的 worktree 执行 project-map status，并得到缺失提示。
证据：[F03](../../findings/a2a-session-retrospective-2026-10-06.zh-CN.md)、
[E09–E11](../../evidence/2026-10-06-session-review-01/excerpts.json)。

先定义当前 Codex 任务实际需要的范围合同，不预制通用适配器，也不复制全部主项目规则。
检查需区分合法的独立夹具与确实缺失治理资料的项目，不能一律跳过 project-map。
合同应明确不适用检查的理由，并保留 task/attempt 身份和原 submit 门禁。
旧夹具记录应暴露范围缺口，明确范围的样本应能按真实入口完成交付。
不得让 worker 自行初始化第二套项目地图来消除报错。

本票记录待办，尚未修改 dispatch prompt 或业务接口。

## Resolution

未执行。
