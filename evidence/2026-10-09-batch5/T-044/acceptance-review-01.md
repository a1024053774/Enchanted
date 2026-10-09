STATUS: FAIL
RELEASE: NO_GO
TARGET: `/Users/luckye/Documents/Code/synara`，`c4c1aff2bb6d81fb60d281191f36b39f4ffa99f0`；parent `28e2f1b4ca6634d4faba9bd921a55a51640407e4`。证据截止：2026-10-09 04:57:01 UTC。

EVIDENCE:

- 冻结提交前后相同，受控文件无漂移；既存未跟踪 `.grok/` 未检查或修改。审查全程只读，未调用模型、正式工作台或外部系统。
- 合同来源：[T-044](/Users/luckye/Documents/Code/a2a/.project-map/tickets/T-044-agent-driven-task-window.md)、[任务书](/Users/luckye/Documents/Code/a2a/evidence/2026-10-09-batch5/brief-T-044.md)。
- **PASS，L3 HTTP**：独立随机 task、project、title 输入经 create 建立 membership，dispatch 与 attach reviewer 返回对应绑定；monitor／sentinel 模型变体保留在 attachment 回执中。
- **PASS，L1 权限逻辑**：[submit-counterexample](/Users/luckye/Documents/Code/a2a/evidence/2026-10-09-batch5/T-044/submit-counterexample-frozen.log) 使用有效 worker 凭据、reviewer caller identity 调用真实 `a2a_submit` handler，得到 `stale_thread`，任务状态未变；其他变更命令同样拒绝。
- **PASS**：冻结候选交付／恢复 17/17；T-038 membership HTTP 场景、跨项目拒绝、CAS 和操作锁检查通过。保存的六份源码与冻结候选相同。fmt、lint、typecheck 均 exit 0。
- **INCOMPLETE**：编排 18 项中 17 PASS，1 项在 submit 准备阶段遇到 `operation_busy`；不能称为 35/35。
- **INCOMPLETE**：冻结 UI 两次失败，首次项目仍在 Loading、两个 pane 显示“会话不可用”，第二次页面加载超时；旧 `ui-active-02` 截图不能替当前候选背书。
- **INCOMPLETE**：[reclaim-frozen](/Users/luckye/Documents/Code/a2a/evidence/2026-10-09-batch5/T-044/reclaim-frozen.jsonl) 的 reviewer 原生会话因关闭 provider 而处于 error，回收正确拒绝 `run_external_unknown`；尚无成功回收、结束标记及淡化截图。
- **未解决失败**：冻结 `service.test.ts` 单例期望 `accepted`，实际停在 `verifying`，随后出现 `database is not open`。未取得父修订对照，无法归因为此次变更。

FINDINGS:

- **[P1] [core.ts:848](/Users/luckye/Documents/Code/synara/packages/a2a-gates/src/core.ts:848)** — attachment 的 `ended` 状态独立提交，下一行才写 `attachment_reclaimed` 事件。若进程在两次写入之间中断，重试在 [core.ts:819](/Users/luckye/Documents/Code/synara/packages/a2a-gates/src/core.ts:819) 直接返回成功，永久缺少完成事件，违反 membership 与门禁事件读回一致的合同。简化修正：在同一状态数据库事务中提交结束记录和完成事件，并使 membership 从持久生命周期事实恢复；操作锁只能防并发，不能消除该中断窗口。
- **[P2] [core.ts:145](/Users/luckye/Documents/Code/synara/packages/a2a-gates/src/core.ts:145)** — 手动归属保存仅从当前 membership 获取 `endedAt`。经公开 membership POST 删除已结束成员，再以新 revision 加回同一合法 thread，结束标记消失；门禁 attachment 仍为 ended，界面却失去“已结束”和淡化显示。归属路由允许该输入，且原生查询不排除归档 thread。简化修正：从持久 attachment／attempt 回收事实派生生命周期，不依赖可编辑 membership 保存结束事实。

COUNTEREXAMPLE:

- 父修订缺少自动 membership 和 attach：原始 HTTP 红态已保存；可拒绝“功能完全未实现”的候选。
- reviewer 使用有效 worker 交付凭据：真实 handler 拒绝并保持状态不变；但 caller 活跃性由夹具替代。
- 在结束记录提交后、完成事件提交前中断：源码可达，当前 ended 快路径不会修复缺失事件；本次只读审查未执行故障注入。
- 删除结束成员后再加回：公开接口可达，当前代码确定丢失 `endedAt`；本次未执行数据库写入。
- 把原生创建的模型固定为常量，同时继续回显请求中的 attachment：当前 sentinel 断言仍可通过，因为它只检查回执，未核对原生 shell 的模型／参数／指令。

LIMITATIONS:

- 能力范围：编排、异步事件、身份、CLI／HTTP／UI、持久写入和恢复适用；RAG／语义记忆 N/A。模型理解、真实 provider 启动、生产运行和部署均未验收。
- submit 反例证明 handler／核心权限逻辑，不能替代完整 MCP gateway 的可信 caller 身份证据。
- 现有 35 项使用真实 CLI、Git 和 SQLite，但 native runtime 是替代边界；不覆盖新增 attached 生命周期的真实成功回收。
- `delivery-recovery-frozen` 在审查期间完成，最终已核对 17/17；不再列为缺失。
- **整体不能通过**：P1 生命周期缺陷未修复；P2 标记丢失未修复；冻结候选尚缺完整 35 项绿态、成功回收读回及当前 UI 证据。不得放宽 error 回收保护来制造绿态。

RULE:

- 在 T-044 隔离入口验收中加入两项检查：结束记录／事件写入间中断后重试，要求恰有一条完成事件且 membership 一致；结束成员删除再加回，要求结束事实保留。前者延续现有 recovery 合同对中断记账的要求，运行位置应为门禁 CLI／HTTP 验收场景。
- session 结束 `project_map.py status`：Problems 0，Stale living docs 0。
