STATUS: FAIL

FINDINGS:

- [P1] [panes.ts:2194](/Users/luckye/Documents/Code/a2a/workbench/src/panes.ts:2194) — **Codex 在 Esc 后提交的新回合可能沿用被打断的旧 `active`。** Esc 只退休 Claude 的提交（[1876 行](/Users/luckye/Documents/Code/a2a/workbench/src/panes.ts:1876)）；Codex 新回合的 `task_started` 被扫描后，会先把旧对象的 `nativeTurn` 改成新值（[1522 行](/Users/luckye/Documents/Code/a2a/workbench/src/panes.ts:1522)）。随后 UPS 的相等比较跳过创建新提交，旧 `interruption` 未更新。新回合的工具钩子因此被 [questions.ts:69](/Users/luckye/Documents/Code/a2a/workbench/src/questions.ts:69) 拒绝，留下不可信标记，Stop 无法受理交付。应区分真正的新回合与同回合追加输入，不能仅比较已被扫描改写的 `nativeTurn`；补 Codex「Esc → 用户新提交 → 交付」真实入口回归。

EVIDENCE:

- 开始、结束均逐字比较：`candidate.files` 范围内工作区 diff 等于 `candidate.patch`；HEAD 为 `59815ea30e3811d2e449bf5c67b7c70b050081ec`。
- `submitGeneration` 路径已读：[panes.ts:1613](/Users/luckye/Documents/Code/a2a/workbench/src/panes.ts:1613)、1640、560。准入时捕获代数、回车写入前保存，支持保留之后才开始的组合输入；协议回报不增加代数，组合开始和门禁中断会增加。
- 证据目录中的 `r13-composition-after-enter-{claude,codex}-1.json`：三项检查通过，等待派发时 `details.dispatch_waits_for_later_draft.pane.user_draft=true`；对应 `draft-released-on-submit-c` 变异失败于该业务断言。
- `r13-{claude-1,codex-2}.json`：各五项通过，`observed.claims=2`、`human_interventions=3`；`red-{claude,codex}.json` 保留带 keys、历史重发漏记的基线红态。失败注入及变异摘要支持记录提交点、期限拒绝和观察失败处理。
- 三个 T-108 夹具补 `submitGeneration:0` 与其模拟的“回车后无新输入”一致；429 项名称与状态同第十一轮，仍为 **254 PASS、175 INCOMPLETE**。答题生命周期仍为 **12 PASS、2 INCOMPLETE**；`unknown_pty_queued` 保留排队写入失败断言（[测试:46](/Users/luckye/Documents/Code/a2a/workbench/tests/t108_answer_lifecycle_contracts.mjs:46)）。
- T-165 候选三次为失败、通过、失败；基线三次均失败于 `checks[name=positive_returns_idle_without_regular_recovery]`，后台 idle、DOM 标题“未知”，支持登记 T-235。REPORT:85 的四次启动超时均为零项业务检查，补跑单独保留，未混算业务结果。
- agy、opencode 摘要保留 `text_uncertain` 且无 keys；人工介入仍由原记录事务派生。新增异常处理明确标记窗格失败，未确认新增静默吞异常、fallback 或平行记录路径。
- 当前 T-207 真实入口回归仅使用 Claude（[测试:2](/Users/luckye/Documents/Code/a2a/workbench/tests/test_t207_user_turn_delivery_e2e.py:2)），不能排除上述 Codex 回归。

LIMITATIONS:

- 未运行测试、status、服务或供应商命令，未连接 hc；新增 P1 来自静态可达路径，尚无本轮运行复现。
- 已删除夹具只能核对保留摘要；未实测旧库恢复、Tab 补全。agy、opencode 使用替身。
- 固定期限余量不能证明任意同步写入、调度及回包延迟下“有记录就必然执行”。