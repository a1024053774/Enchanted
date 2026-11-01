# T-229 只读审查（第七轮）

你是独立审查员，只读：不改文件、不提交、不跑会写文件、起进程、连 hc 或供应商的命令。可以读文件、用 git 查看、在内存里推演。

- 票：`/Users/luckye/Documents/Code/a2a/.project-map/tickets/T-229-worker-input-final-text-only.md`。范围外登记：`/Users/luckye/Documents/Code/a2a/.project-map/tickets/T-234-blocked-claude-submit-leaves-pane-busy.md`。
- 候选：`/Users/luckye/Documents/Code/a2a-worktrees/T-229-evidence/candidate.patch`，相对 main HEAD `59815ea30`；就是 `/Users/luckye/Documents/Code/a2a` 工作区里 `candidate.files` 列出文件的未提交改动（两个新测试已 `git add -N`）。本轮相对上一轮（`candidate-06.patch`）：`panes.ts` 新增 `beforeSubmit` 与 `submissionBlocked`；`daemon.ts` 在 UPS 请求失败时恢复窗格并照常 drain，UPS 回包不再等反馈处理；测试新增阻断后状态与派发的检查和 `no-restore` 变异。T-234 已并入本票（用户选定在本票修）。工作区里另有无关的未提交文件，不在本次范围。
- 前几轮：同目录 `REVIEW-01.md`～`REVIEW-06.md`，对应候选 `candidate-01.patch`～`candidate-06.patch`。主控的核实与处理写在 `REPORT.md` 各“第 N 轮审查后的修改与运行”一节。
- 报告与证据：同目录 `REPORT.md` 及其链接的 summary JSON、日志、`runs.log`、各 `run-*.sh`。第八、九轮的测试夹具目录还在 `/private/tmp/t229-*`（只读，可查库；例如 `r8-request-fails-claude-2` 是 `/private/tmp/t229-dqaclhal`）；更早的已按用户要求只留状态、已删除（状态表在 `/Users/luckye/Documents/Code/a2a/evidence/2026-10-31-batch29/T-229/fixtures-status.md`）。

## 要核对

0. 第六轮两条 P1 是否已正确处理（REPORT“第六轮审查后”一节）：
   - 从期限检查到 UPS 回包之间，产品路径上还有没有可能拖过 1 秒余量的 await。
   - `beforeSubmit` 的生命周期：在哪里记下、在哪里丢掉、在哪里恢复。有没有用过期快照恢复的路径，例如回车之后没有 UPS、Claude 回合中排队的提交、恢复后的窗格、Esc 中断、问答确认的回车。
   - 恢复只在“后台对这个窗格的 UPS 没回 ok”时发生，这和钩子命令阻断的条件是否完全一致，会不会在 CLI 其实执行了的情况下把窗格改回空闲。
   - Claude 保留用户草稿、Codex 不保留，依据是两次运行观察（`r8-request-fails-claude-2` 库里第 158 条事件的提交全文、`r8-request-fails-codex-1`）。这够不够，是否会误伤。
   - 阻断后的 drain 会不会在库坏时出新问题。
   - 写明不覆盖的情况（后台连不上、回包晚于余量）是否合理。
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
