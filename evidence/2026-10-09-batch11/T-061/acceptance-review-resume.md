# T-061 固定候选独立审查（2026-10-09）

来源：一次 fresh-context、只读的 `t061_acceptance` reviewer；角色为 `acceptance-auditor`。未继承实现会话，未读取实现者的计划或结果解释。reviewer 原答复为英文，下文是中文译文；仅保存中文报告。审查建议不替代执行主控验收、集成或关闭。

STATUS: PASS
TARGET: `aff04b5f05fefc1113cdad876b18917f387dc975`（`a2a-t061`，HEAD 干净）

EVIDENCE:

- `codexAppServerManager.ts:4990` 将受控原生提示的工具名字符范围放宽到 `[a-z0-9_]+`；`:4490` 起的实际 manager 判定保留 server、lease、turn、授权、目录和交互模式检查。
- `permission-red-02.log`：已知坏解析器产生 6 个业务断言失败；`permission-green-02.log`：63/63 通过。
- 外部目录输入含 116 个唯一名字，包括 `a2a_submit`、`a2a_raise`、`synara_e2e_review`。原始基线/绿态结果显示，只有这三个由 pending 转为单次 accept，其余 113 个完全相同。
- 批准响应精确为 `{action:"accept", content:null, _meta:null}`，pending 为 0。未授权、过期/非活跃、撤销/缺 lease、错误 server/kind、目录外数字哨兵保持 pending。
- 与候选绑定的相关套件：295 通过，2 个无关的真实 Codex resume 用例跳过。fmt、lint、typecheck 收据退出码均为 0。
- 审查期间候选未改变；改动仅为解析器及其测试。

FINDINGS:

- 无。

COUNTEREXAMPLE:

- 还原已知坏的 `[a-z_]+` 会被拒绝：三个目录数字名字使六个正例业务断言失败，并在目录基线中保持 pending。
- 总是批准或忽略输入的实现会被 `shell2`、`a2a_raise2`、非完整提示、错误 server 和授权边界反例拒绝，这些反例要求保持交互 pending。

LIMITATIONS:

- PASS 仅覆盖 T-061 的受控原生帧合同。按本票明确范围，未执行真实 Codex 模型、app-server 进程、正式服务或生产部署。

## 记录校正

reviewer 的 EVIDENCE 第四条原文把错误 approval kind 与 pending 反例并列；译文保留该原意。实际生产合同及 `raise-permission.test.ts:246` 起的断言对此帧返回 `cancel`（`content`/`_meta` 为 null），不是 pending；其他上述反例保持 pending。红绿日志和测试本身正确，没有因审查文字而改变验收或代码。本校正只说明审查报告的一处措辞错误，没有进行第二轮审查。
