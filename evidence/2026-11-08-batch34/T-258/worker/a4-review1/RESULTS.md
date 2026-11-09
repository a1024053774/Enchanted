# T-258 第一次审查反馈复现

**BLOCKED（测试补充的范围待明确）**。门禁 #87 的 P2 完成条件覆盖缺口已复现。当前生产守卫正确；未修改生产代码或完成条件测试，没有生成或重交新候选。

候选 `9d6883239d2757e8899d1894999837c1e0b61617`，基线 `172b2f17566f923b2e0be8f7d21fc0b189b83fa2`。当前 task/attempt/session/fence/spec_rev 沿用 a4；审查 verification 为 `617b4f51-4177-4dc0-809d-78d43c50d6b7`。执行于 2026-11-09 UTC。

| 运行 | 结果 | 含义 |
| --- | --- | --- |
| 原 117 案运行于删 leader 守卫的源码副本 | 117 PASS、exit 0 | 现有完成条件漏检该变异。 |
| worker/reviewer 诊断运行于原候选 | 2 PASS、exit 0 | 两种角色的非空 leader 绑定失配均被 `identity_conflict` 拒绝，失败标记与原 active 保留、无输入重发。 |
| 相同诊断运行于上述变异 | 2 FAIL、exit 1 | 均报 `Missing expected rejection: bound leader mismatch must refuse recovery`，实际 failed=null、state=busy。变异不是等价变异。 |

独立输入来自审查报告与原任务进程身份契约：已绑定 leader=4099，pane/live leader=4101。没有从实现输出推导预期。仅在自身源码副本把 `(bound.leader_pid === null || bound.leader_pid === pane.leader)` 替换为 `true`；诊断以原测试副本追加两个场景，未替换正式测试。首次尝试只读审查目录中的探针时文件不存在，因此用已提供的反例重新构造，没有改动该目录。

命令（cwd 为本 attempt worktree）：`python3 evidence/2026-11-08-batch34/T-258/worker/a4-review1/reproduce.py`。逐次 node argv、输入环境、每案状态、失败断言、退出码、清理状态见 [reproduction-01.json](reproduction-01.json)；探针输入见 [leader-probe.inc.ts](leader-probe.inc.ts)。再次运行须另存新证据目录，脚本拒绝覆盖原摘要。

自身 SQLite/rollout 及源码副本均先记状态后删除。未运行真实 CLI、正式后台或新独立审查；依赖只读解析。现有三个恢复文件仍与候选相同，冻结 oracle_paths、acceptance、REVIEW.md 和任务卡未改，额外目录无改动。

阻塞依据是本卡明确要求“只从 49c7b9a…读取并恢复三个文件”“逐文件核对它们与已测 4c93144df…一致”。审查建议也要求主控先处理该限制；worker 角色卡规定任务卡修订须经 issue 交执行主控处理，不能自行改卡。已准备好最小测试补充内容，待范围明确后方可纳入完成条件、运行候选/同一变异并提交新候选。不能把门禁自动返工通知当作自行修改卡中限制的授权。

**Works**：审查报告的原套件漏检及两个非等价反例均已复现。

**No regression**：本轮没有改生产文件或正式测试；未重跑无关回归，旧回归只对应原候选。

**Risk / undo**：测试缺口尚未修复，整票不能通过；等待主控明确范围及按需处理卡修订。无需产品回退，新增诊断证据保留。
