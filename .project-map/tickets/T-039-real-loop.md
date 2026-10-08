---
id: T-039
title: 真实 Codex 闭环
type: build
status: open
blocked_by: [T-037]
claimed_by: s2-t039
supersedes:
---

## What to build

真实 Codex（经 app-server）在 Synara thread 中完成分页夹具：门禁派发 → worker 提交并调用 `a2a_submit` → 独立 oracle → CAS 集成 → 回收。使用隔离 Synara 数据目录与隔离 CODEX_HOME（AGENTS.md 规则）。见 [spec](../specs/synara-m1-2026-10-07.md)"验证接缝"第 2 项。

## Acceptance

- [ ] 一次真实 run 经完整入口 accepted，集成引用读回为 worker 提交；追加式运行记录含精确 argv、版本、task/attempt/thread、原始外部结果。
- [x] 隔离 home 在结束后删除；用户 Herdr、Codex 配置与 Synara 数据不变。
- [x] 无人值守期间若出现权限对话，停下保存现场，不作为通过。

## Resolution

**决定02执行中：BLOCKED，待主控授权注册点修改。** [机制对照](../../evidence/2026-10-07-synara-batch2/T-039/repair-03/projection-settlement-comparison.md)已核对runtime ingestion ACK、domain high-water、snapshot最小已处理序号和provider intent ACK。`service.ts`接入已有机制与期限，受控测试10/10；最终测试在父版service上3失败/7通过。两个授权文件的工作区改动保留，尚未提交fork。

真实服务图typecheck失败：`serverLayers.test.ts:26`暴露 `ProviderCommandReactor | ProviderRuntimeIngestionService` 未提供。最小修复是在 `apps/server/src/serverLayers.ts` 的 A2AGateServiceLive 注册点提供现有的两个layer，具体 [补丁](../../evidence/2026-10-07-synara-batch2/T-039/repair-03/proposed-server-layer-wiring.patch)已用git apply --check核对、未应用。该文件超出主控决定02的授权范围，已请求确认。未启动新模型调用，35项与新根真实闭环及独立审查仍待完整候选；不复用旧轮通过结论。详情见 [repair-03/RESULTS](../../evidence/2026-10-07-synara-batch2/T-039/repair-03/RESULTS.md)。

### 决定01记录（原结论保留）

**本轮 BLOCKED，待主控决定；ticket 保持 open，待主控关闭。** 按 [主控决定01](../../evidence/2026-10-07-synara-batch2/T-039/controller-decision-01.md) 修复后，fork 候选为 `fc9e36c75af3bbcf701551abbb911883b94217c2`。只修改原生观察转换与新增服务测试；最终测试在旧候选上有3项业务红态，新候选6/6，移植场景35/35，typecheck/lint通过。

全新真实根的 worker 已显式 submit；独立 oracle 12/12通过，CAS引用与 worker提交均为 `b1f5f5178585377150ae046b5ee3fc27f4b10970`。但原 run 在回收时因 provider 已退出、投影仍 running 被 `run_external_unknown` 拒绝，收据为 `integrated_reclaim_failed`。在主控决定要求未知仍拒绝的边界内，没有添加第三类状态的容错或再次调用模型。后续同 attempt 的清理请求先遇到 `stop_unconfirmed`，核对实际 stopped 后再经原门禁成功停止、归档、读回；不改判原 run 成功，因此第一项未勾选。

隔离源 home、overlay和本次进程已清理。按主控指定的只读前后核对，用户 config/rules 的大小与mtime、Synara顶层目录元数据及 herdr status 均相同；这只是指定范围的元数据证据。人工输入事件为空，无权限或问题回答。全仓fmt仅原有 `.grok/settings.json`失败；全仓test在新状态差异的决策点未继续运行。报告和完整证据见 [repair-02/RESULTS](../../evidence/2026-10-07-synara-batch2/T-039/repair-02/RESULTS.md)，新的独立审查见 [repair-02/acceptance-review](../../evidence/2026-10-07-synara-batch2/T-039/repair-02/acceptance-review.md)。

### 首轮记录（原结论保留）

**BLOCKED，待主控决定；ticket 保持 open，待主控关闭。** 固定 fork 候选 `fa3fc3352805d00e41c454fa6f810807528de3a9`，仅一次真实 Codex 模型 turn。完整闭环未通过，未修改产品代码或 push。

- 门禁 `create` 成功；`run`（`full-access`、600 秒 submit deadline）在 `waiting_submit` 返回 `identity_conflict` / `paused`。同一 thread 的 provider 已有 active turn，而投影仍为 ready / null；后续真实 thread 读回出现相同 turn。尚无 submit、候选、oracle 验证或 CAS 集成；引用保持夹具基线。
- 原生中断仅用于清理；随后绑定原 attempt 的门禁 `reclaim` 返回 `run_external_unknown`，没有绕过门禁归档。业务回收未完成。本次 server 和 app-server 已停止；源 CODEX_HOME、Synara overlay 与私有 bootstrap token 已删除，原夹具和诊断现场保留并归档。
- 人工输入事件为空，observer 在失败及清理请求时均为 healthy。截止原生读回无 pending approval / user-input；本次没有批准或回答权限、问题对话。原生中断为资源清理事件，不能作为通过证据。
- 第二项为 INCOMPLETE：隔离配置、六个 overlay 链接、固定 CLI argv 与清理检查证明 home 删除及本次隔离边界；未操作用户 Herdr，不连接用户 Synara 实例，用户 auth.json 仅按授权复制。但没有用户数据的独立前后快照/审计，不能勾选整个条件。独立审查判 FAIL，审查时原稿保存在 review-frozen-docs；此后仅更正文档结论，产品与原始证据未变。

命令、版本、身份、原始输出与最小修复选项见 [交付报告](../../evidence/2026-10-07-synara-batch2/T-039/RESULTS.md)。入口结果：[run-01](../../evidence/2026-10-07-synara-batch2/T-039/run-01.json)、[回收拒绝](../../evidence/2026-10-07-synara-batch2/T-039/reclaim-01.json)、[清理](../../evidence/2026-10-07-synara-batch2/T-039/cleanup.json)。冻结范围见 [frozen-manifest](../../evidence/2026-10-07-synara-batch2/T-039/frozen-manifest.json)，fresh-context 只读独立审查见 [acceptance-review](../../evidence/2026-10-07-synara-batch2/T-039/acceptance-review.md)。a2a 本地提交号以最终 `T-039 DONE` 回执为准。
