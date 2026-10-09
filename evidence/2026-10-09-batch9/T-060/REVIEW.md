# T-060 独立审查原结论

以下保留唯一一次 fresh-context、只读审查的原结论，没有上调为 PASS。

STATUS: INCOMPLETE
TARGET: 冻结候选 `c4ce31d73914fd5afa9eae59b5cb76a1fa5c1331`

EVIDENCE:
- 依据 T-060 ticket 第 16–26 行及 inbox 合同，使用真实 `scripts/inbox` CLI、外部临时夹具和陌生 nonce 输入。
- 候选行为通过：三种角色 `list` 均排除 `kind: ack`；`ack` 与 `send --kind ack` 均退出码 1，输出“ack 是终结”，文件快照不变。
- 父行为被反事实探针拒绝：`list` 列出 ack；两个入口退出码 0，并新增 ack 文件。
- 九种非 ack kind 在候选与父版本上的列表、确认写入和清空行为一致。
- 损坏条目下候选的 `send` 与 `ack` 均退出码 1，报告 `broken.md`，文件未变化。
- 候选新增测试及一个未修改 T-053 用例：4/4 通过；同测试指向父版本时 T-060 新测试失败、旧行为用例通过。
- 真实仓库 `.project-map/inbox/` 只读 `list --role executor`：退出码 0，6 个条目前后完全一致。
- 完整证据、探针源码、候选/父源码、命令和输出保存在 `/tmp/t060-independent.aDmVvS/`，主要文件为 `probe.py`、`commands.json`、`judgments.json`、`real-readonly.json`、`candidate-scripts-inbox`。
- `HEAD` 始终为候选，目标文件无工作树改动；但审查期间其他任务的工作树 diff 增加了 `scripts/dispatch-permissions*`、`evidence/.../round4/` 等文件，违反冻结快照条件。

FINDINGS:
- [P2] `scripts/inbox:371-395` — `scripts/inbox --help` 未写明 T-060 要求的两种 front matter 列表格式及损坏条目拒绝写入原因；按指令未读取 RESULTS，无法判断允许的另一文档渠道是否满足，因此该子条件未核验。

COUNTEREXAMPLE:
- 父版本 `8e260461f32e49c3b1bce50bedeceb4fad38aa8a` 在相同夹具上列出 `terminal-executor-ack`/`terminal-ideation-ack`，并允许两个入口写出新的 ack；候选正确拒绝。

LIMITATIONS:
- 审查期间工作树存在并发生了与 T-060 无关的并发 diff，故不能对严格意义上的单一冻结快照给出 PASS。
- RESULTS 按任务指令未读取；文档条件无法独立闭合。
- 未执行门禁集成、Herdr、Synara、UI 或发布验证；这些不属于 T-060 CLI/文件系统验收。

RULE:
- 无；本次未发现可归纳的重复失败类别。

## 证据保存与实现者补充

原始目录完整归档为 [independent-review-raw.tar.gz](independent-review-raw.tar.gz)，原目录未删改。独立套件首次两条命令缺少 `InboxCLI.` 前缀，分别产生 4 个测试装载错误；这些现场原样保存，不充当缺陷红态。改正命令后，候选 4/4 通过，父行为两个新用例产生 9 个业务断言失败，另外两个用例通过。

以下是实现者补充，不是新的独立审查或对原结论的修改：

- `freeze-check.json` 保存的 HEAD 为 `c4ce31d73914fd5afa9eae59b5cb76a1fa5c1331`，`target_worktree_diff` 为空。归档内候选、父版本入口分别与对应 Git 修订逐字节一致；相关两个源文件在审查结束时也与候选一致。审查者提出的变化位于其他任务的文件。
- T-060 允许在 `--help` **或** RESULTS 写行为说明；本交付采用 [RESULTS 的行为说明](RESULTS.md#行为说明)。审查者未读取该节，文档条件的独立核验仍未完成。
- 任务书只要求一次 fresh-context 审查，本次没有追加第二次审查。需执行主控判定当前独立行为证据及补充材料是否足够关闭票据，或另行授权补审；整体交付保持 INCOMPLETE。

审查规则来自 [behavioral-acceptance-review 的 SKILL.md](/Users/luckye/.agents/skills/behavioral-acceptance-review/SKILL.md)：`If the branch, candidate, or diff changes, return INCOMPLETE; do not chase a moving target.` 规则明确要求对象冻结；将同一工作树内其他任务的变化纳入冻结对象，是本次审查者的解释，并非该规则显式要求无关文件也不变。原结论与这一范围分歧均交主控判定，未由实现者改判。
