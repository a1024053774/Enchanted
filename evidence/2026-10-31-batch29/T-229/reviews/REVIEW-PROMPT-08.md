# T-229 只读审查（第八轮）

你是独立审查员，只读：不改文件、不提交、不跑会写文件、起进程、连 hc 或供应商的命令。可以读文件、用 git 查看、在内存里推演。

- 票：`/Users/luckye/Documents/Code/a2a/.project-map/tickets/T-229-worker-input-final-text-only.md`。范围外登记：`/Users/luckye/Documents/Code/a2a/.project-map/tickets/T-234-blocked-claude-submit-leaves-pane-busy.md`。
- 候选：`/Users/luckye/Documents/Code/a2a-worktrees/T-229-evidence/candidate.patch`，相对 main HEAD `59815ea30`；就是 `/Users/luckye/Documents/Code/a2a` 工作区里 `candidate.files` 列出文件的未提交改动（两个新测试已 `git add -N`）。本轮相对上一轮（`candidate-07.patch`）：快照只由第一次未决回车记下（`??=`），Stop、Esc 让它失效，并按回包的最终结果确认或恢复；关连接后 drain 的失败改用 `recordFailure`；测试在 `request-hangs` 里加了第二次空回车，新增 `snapshot-overwritten` 变异，修好 `no-claim` 的定位。T-234 已并入本票。工作区里另有无关的未提交文件，不在本次范围。
- 前几轮：同目录 `REVIEW-01.md`～`REVIEW-07.md`，对应候选 `candidate-01.patch`～`candidate-07.patch`。主控的核实与处理写在 `REPORT.md` 各“第 N 轮审查后的修改与运行”一节。
- 报告与证据：同目录 `REPORT.md` 及其链接的 summary JSON、日志、`runs.log`、各 `run-*.sh`。第八到十轮的测试夹具目录还在 `/private/tmp/t229-*`（只读，可查库；例如 `r8-request-fails-claude-2` 是 `/private/tmp/t229-dqaclhal`）；更早的已按用户要求只留状态、已删除（状态表在 `/Users/luckye/Documents/Code/a2a/evidence/2026-10-31-batch29/T-229/fixtures-status.md`）。

## 要核对

0. 第七轮四条意见是否已正确处理（REPORT“第七轮审查后”一节）：
   - 快照的记下、失效、确认、恢复四处，是否还有用过期或错配快照恢复的路径；没有核对 prompt id 这一点，影响是否可接受。
   - 确认放在 `request_result` 写入之后、回包之前，是否和钩子收到的结果完全一致。
   - 记录提交后又失败、撤不回记录这一遗留，写法是否诚实，有没有本层能做的更小改法。
   - `recordFailure` 的复用在 drain 路径上是否会改变原有的 ok 路径行为。
   - 第六轮的各项（期限、恢复、Claude 保留草稿、drain）是否仍然成立。
1. Claude Code、Codex worker 窗格：用户提交是否每次恰好记一条、文字等于 CLI 实际提交的全文；有没有漏记或重复记录的路径。
2. 认领：派发会不会被记成用户输入，用户输入会不会被吞掉。
3. agy、opencode：记录按草稿、不带按键、拼不准时标 text_uncertain。
4. 人工介入照旧派生；观察失败时的行为没有退化。
5. 测试：期望来自票面；红态在基线上失败；变异失败在业务断言上；有没有空转的检查。
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
