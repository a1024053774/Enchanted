# T-229 只读审查（第九轮）

你是独立审查员，只读：不改文件、不提交、不跑会写文件、起进程、连 hc 或供应商的命令。可以读文件、用 git 查看、在内存里推演。

- 票：`/Users/luckye/Documents/Code/a2a/.project-map/tickets/T-229-worker-input-final-text-only.md`。已并入本票：`/Users/luckye/Documents/Code/a2a/.project-map/tickets/T-234-blocked-claude-submit-leaves-pane-busy.md`。
- 候选：`/Users/luckye/Documents/Code/a2a-worktrees/T-229-evidence/candidate.patch`，相对 main HEAD `59815ea30`；就是 `/Users/luckye/Documents/Code/a2a` 工作区里 `candidate.files` 列出文件的未提交改动（两个新测试已 `git add -N`）。工作区里另有无关的未提交文件，不在本次范围。
- 本轮相对上一轮（`candidate-08.patch` 是第八轮审查时的候选）：用户选定方案 1（用户 2026-11-01：“还是在 T-229 里直接做方案 1吧,相关回归也做”）。Claude Code、Codex 窗格的窗口回车只是输入证据，不开回合、不标忙，草稿仍算占用；回合在后台处理 UPS、确认不是派发之后才开始。`beforeSubmit` 快照及 `submissionBlocked`、`submissionConfirmed` 全部删除，被阻断的提交什么都不改。测试删掉 `snapshot-overwritten`、`no-restore` 变异，新增 `enter-starts-turn`；单元夹具 `test_t157_turn_identity`、`test_t166_queued_input` 接上 `recordUserSubmission`。
- 前几轮：同目录 `REVIEW-01.md`～`REVIEW-08.md`，对应候选 `candidate-01.patch`～`candidate-08.patch`。主控的核实与处理写在 `REPORT.md` 各“第 N 轮审查后的修改与运行”一节。
- 证据：同目录 `REPORT.md`、`runs.log`、`run-round11.sh`、`r11-*.json`/`.log`、`r11-unit/`。本轮夹具跑完即删，只留摘要（`fixtures-r11.tsv` 记了每次尝试的夹具路径）；HEAD 对照副本在 `/private/tmp/t229-head`。

## 要核对

0. 第八轮五条意见（REPORT“第八轮审查后”一节）：
   - 三条快照问题是否随快照删除而不再成立；方案 1 有没有新的错配：窗口回车不改状态后，派发、Stop、Esc、门禁中断、排队输入与 UPS 交错时，窗格状态和 `userDraft` 是否正确。
   - “记录提交后又失败”遗留：主控说明门禁与编排库是两条独立的 DatabaseSync 连接，无法在本票内放进同一事务。说明是否属实、写法是否诚实、有没有本层能做的更小改法。
   - Codex `late-handled` 变异这一轮是否失败在业务断言上。
1. Claude Code、Codex worker 窗格：用户提交是否每次恰好记一条、文字等于 CLI 实际提交的全文；有没有漏记或重复记录的路径。
2. 认领：派发会不会被记成用户输入，用户输入会不会被吞掉；派发会不会粘到用户未发出的草稿上。
3. agy、opencode：记录按草稿、不带按键、拼不准时标 text_uncertain；它们的回车仍照旧开回合。
4. 人工介入照旧派生（T-133/T-134 回归）；观察失败时的行为没有退化。
5. 测试：期望来自票面；红态在基线上失败；变异失败在业务断言上；有没有空转的检查；单元夹具的改动是否合理。
6. REPORT 每条结论与所链证据是否一致（特别是启动期限的重试：没有把启动失败算作业务通过或失败）。
7. 有没有吞异常、fallback、兼容分支、平行路径。

## 输出

```
STATUS: PASS | FAIL
FINDINGS:
- [P0|P1|P2] 文件:行 — 问题；会怎样出错
EVIDENCE:
- 实际读过什么，引用文件和行号或 JSON 字段
LIMITATIONS:
- 没核对到的
```

每条意见给出文件和行号或 JSON 字段，主控会逐条核对。没有阻塞问题写 PASS。
