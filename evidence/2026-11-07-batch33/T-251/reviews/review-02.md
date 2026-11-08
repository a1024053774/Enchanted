# 复审 02（Codex gpt-6.1-sol high，只读，codex exec，2026-11-07）

审 `d5cb1da53`，范围 `ab912013b..HEAD`，提示词 `prompt-02.md`。原始输出未进仓库，只留结论原文如下。

STATUS: **INCOMPLETE**  
SUMMARY: 本轮未确认新的生产代码缺陷；第 2、3、4 项修复成立。符号链接的真实触发入口仍未证实，新增检查证明了收件箱接收，尚未证明执行主控实际收到。  
TARGET: `d5cb1da53de6ff97e8aee4065819521053222b8f`；范围为 `ab912013b..HEAD` 中指定的路径。

EVIDENCE:

1. **符号链接：探针结论局部成立，上一轮的真实缺陷判断仍属“未证实”。**

   [probe_symlink.py:98](/Users/luckye/Documents/Code/a2a-wt/t251/evidence/2026-11-07-batch33/T-251/review-probes/probe_symlink.py:98) 的输入是建立 `outlink → /usr/share`，执行 `cd outlink`，再执行下一条 Bash。[symlink-cd.json:10](/Users/luckye/Documents/Code/a2a-wt/t251/evidence/2026-11-07-batch33/T-251/review-probes/symlink-cd.json:10) 确实保存了目录被重置的输出，所记录的钩子 cwd 也只有工作区根目录。因此，该次探针没有触发链接路径通过门禁的场景。

   但它没有覆盖指向 `extra_directories` 的链接，也没有覆盖 Codex，不能推出“真实入口从不报告链接路径”。本轮没有取得这两类真实入口证据，均标为**未证实**。另外，链接指向已批准的 extra directory，本身并不构成越过批准目录集合；需要核对实际目标是否在整个批准集合之外。

   [questions.ts:51](/Users/luckye/Documents/Code/a2a-wt/t251/workbench/src/questions.ts:51) 仍只做词法边界判断。“cwd 是自报字段”能说明 `realpath` 无法认证发送者，不能说明核对路径实际落点毫无价值。这不足以单独驳回目录边界问题，但当前也没有真实入口反例，不能继续把它列为已确认故障。

2. **第 2 条：PASS，已消除“窗格已空闲、可以回收”的无条件断言。**

   [core.ts:819](/Users/luckye/Documents/Code/a2a-wt/t251/workbench/src/gates/core.ts:819) 现在要求查看 `status`，下一步也明确等待空闲，否则回收返回 `worker_working`。当匹配 Stop 到达、但仍有排队输入或 `interrupted` 时，这与 [panes.ts:2450](/Users/luckye/Documents/Code/a2a-wt/t251/workbench/src/panes.ts:2450) 保持 busy 的行为一致。

   [README.md:799](/Users/luckye/Documents/Code/a2a-wt/t251/workbench/README.md:799) 同样限定为“没有排队输入、没被打断时”回到空闲。本项未发现残留矛盾。

3. **第 3 条：PASS，T-251 Stop 例外与代码范围一致。**

   [README.md:1277](/Users/luckye/Documents/Code/a2a-wt/t251/workbench/README.md:1277) 明确限定为 Claude worker、本会话匹配的 Stop；[panes.ts:2438](/Users/luckye/Documents/Code/a2a-wt/t251/workbench/src/panes.ts:2438) 的拒收例外位于 `claudeStop`，并要求 `role === 'worker'`。Codex、agy、opencode 没有获得这一 Stop 例外。

4. **排队绑定：PASS；历史红态的版本归属有记录缺口，但已独立复演修前失败。**

   [panes.ts:1493](/Users/luckye/Documents/Code/a2a-wt/t251/workbench/src/panes.ts:1493) 只替换了 cwd 条件，仍要求相同 session、queued human 来源、新 prompt ID、有效时间和完全一致的输入内容。原回合尚有 active、Stop 正在转交时仍不登记下一回合，早到 Stop 的匹配流程也未改变，与 T-157、T-165、T-166 的语义一致。

   本轮从 `git show ab912013b:workbench/src/panes.ts` 和 HEAD 提取实际 Claude `scan` 代码，在内存中提供转录与 store：
   - 子目录记录：修前不绑定，当前绑定。
   - 同前缀兄弟目录、外部目录、`..` 逃出、异 session：当前均不绑定。
   - 原回合尚在运行、Stop 正在转交：当前均不提前绑定。

   [test_t251_queued_subdir.ts:21](/Users/luckye/Documents/Code/a2a-wt/t251/workbench/tests/test_t251_queued_subdir.ts:21) 的期望来自“工作区内子目录属于本会话”和既定排队语义，没有调用生产 helper 生成答案。保存的 [red/queued_subdir.json:3](/Users/luckye/Documents/Code/a2a-wt/t251/evidence/2026-11-07-batch33/T-251/red/queued_subdir.json:3) 只有源码目录，没有 revision；因此，仅凭该工件不能独立确认历史运行确在 `ab912013b`。本轮内存复演确认了该提交上的同一失败，但不补称为历史运行证明。

5. **收件箱检查：能区分“交给收件箱”与“只保存问题”，不能证明实际送达。**

   [test_t251_untrusted_turn_e2e.py:204](/Users/luckye/Documents/Code/a2a-wt/t251/workbench/tests/test_t251_untrusted_turn_e2e.py:204) 接受 `pending/role_session_missing`。保存的 `green/e2e-untrusted-r4.json` 正是这种情况：目标 `controller_launch` 正确，但[最后回执仍为 pending](/Users/luckye/Documents/Code/a2a-wt/t251/evidence/2026-11-07-batch33/T-251/green/e2e-untrusted-r4.json:123)。

   这符合无在线主控时的排队契约。[core.ts:3452](/Users/luckye/Documents/Code/a2a-wt/t251/workbench/src/gates/core.ts:3452) 在没有目标时就保存该回执并返回，尚未调用后面的 `wakeThread`。所以修正 pending 的期望有依据，但该场景没有经过实际送入终端的边界。

   `green/e2e-cd-r3.json`、`green/e2e-compact-r3.json` 均通过，生产源码与当前候选一致；它们不检查问题投递。旧的 untrusted-r3 和 no-delivery 首轮都失败于 `issue_delivered_to_executor`，当时不能形成有效区分。

FINDINGS:

- 未确认本轮新增的生产代码故障。
- **送达验收仍不完整。** 若问题已生成 pending 回执，但主控就绪后的补送失效，当前新增检查仍可通过；主控可能一直收不到问题。本轮未实际运行这一坏实现，因此不把它列为已复现的生产故障。

COUNTEREXAMPLE:

- [no-delivery 变异:47](/Users/luckye/Documents/Code/a2a-wt/t251/workbench/tests/test_t251_untrusted_turn_e2e.py:47) 删除的是 `deliverInbox(issue)` 调用。`mutants/e2e-no-delivery-r2.json` 没有回执，且仅失败于 `issue_sent_through_inbox`，有效证明新增检查能发现**遗漏收件箱交接**。
- 它没有证明“已有回执但永不实际送达”的实现会被拒绝。

LIMITATIONS:

- 全程只读，未改文件、未提交；未运行会创建夹具的真实 CLI E2E 或完整回归。候选 HEAD 未变化，工作树仍干净。
- 符号链接的 extra directories、Codex 真实入口未证实。
- 缺少本次 T-251 系统问题在在线执行主控终端实际收到，或从 pending 随主控就绪补送成功的证据。

**结论：无法判断可合并（INCOMPLETE）。** 第 2、3、4 项可接受；合并判断仍缺第 5 项的实际送达证据及能捕获实际投递被省略的反例。第 1 项保留“未证实”，不据此要求加入 `realpath` 修复。
