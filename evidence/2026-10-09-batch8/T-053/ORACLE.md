# T-053 验收输入与预期（实现前）

依据：T-053 `ready_rev: 1`、controller-split-user-input spec 第 3、4、5、8 节。
目标：一个标准库 CLI 完成追加、确认、收件箱呈现和就绪筛选。
非目标：唤醒主控、门禁操作、会话复制、fork 改动、正文含义判断。

Tracer bullet：先经真实 `scripts/inbox send → 文件 → list → ack → list` 跑通，再扩展并发、处置与 ready。Deep modules：一个入口隐藏文件发布、读取和派生状态，无传输包装。Ubiquitous language：沿用 CONTEXT 的收件箱、问题上报、就绪、角色卡。

## 手写清单

- 确认夹具：executor 收到 `a`（已由 executor 确认）、`b`（只由 ideation 确认）、`c`（两角色各确认）、`d`（未确认）；另有发给 ideation 的 `e`。executor 未确认清单逐条为 `b,d`，ideation 为 `e`。对 `b` 确认后 executor 为 `d`，`b.md` 原字节不变。
- 问题夹具：时钟 2026-10-09T12:00:00Z，11:46 无处置为待判断，11:44 无处置为等你决定，blocking 直接等你决定；close/dismiss 为已关闭，forward 为已转交并在转交 15 分钟到时为等你决定，snooze 在处置后 1 小时到时为等你决定，reopen/needs-user 为等你决定，answer 为已答复，delivered 为已送达。
- ready 夹具：正常 build、task、research，依赖 closed/superseded 的 build 可执行；缺 ready、no、缺 ready_by/ready_rev、未解决依赖、已认领、已关闭、superseded、out-of-scope、decide 均不可执行。缺字段列为不合规。
- 并发：固定同一 UTC 秒，20 个真实子进程各 send，20 个完整 md 和 20 个不同 id，正文集合等于输入集合。
- 反事实：秒级文件名 mutant 必须被并发用例拒绝；忽略 ack 发送者 mutant 必须被 `b` 清单拒绝。

## 失败方式与实现约束

并发同名、半截发布、重复确认、伪造确认、悬空 reply_to、损坏 front matter、时钟回拨、非 UTF-8 正文、极长正文均通过真实 CLI/文件系统检查。被杀只针对本测试进程；保留未发布暂存现场，收件箱不出现半截 md。坏条目跳过并逐条报告，退出非零。时钟回拨不得使已生成 id 碰撞或使过期答复覆盖较新的处置。正文不解析。

## 格式接点

角色卡只给 ideation/executor；user 是展示用途，打印“等你决定”列表而不要求不存在的 user 角色卡。`--id` 用于明确重放 id 的拒绝；disposition 使用 `--action/--reason/--basis` 显式元数据。ref 支持角色卡的 `file:路径#L行号`，现有信箱的 `ticket:T-053`，以及 issue/worker/attempt 引用。

会话副本清单接点：读取 `evidence/*/sessions/manifest.jsonl` 的 `cutoff_at`（UTC 截止时间）；没有记录不提醒。此接点供 T-054 对接，脚本不读取原生会话或副本正文。
