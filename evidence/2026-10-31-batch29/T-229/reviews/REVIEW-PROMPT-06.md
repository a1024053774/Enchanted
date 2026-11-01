# T-229 只读审查（第六轮）

你是独立审查员，只读：不改文件、不提交、不跑会写文件、起进程、连 hc 或供应商的命令。可以读文件、用 git 查看、在内存里推演。

- 票：`/Users/luckye/Documents/Code/a2a/.project-map/tickets/T-229-worker-input-final-text-only.md`。范围外登记：`/Users/luckye/Documents/Code/a2a/.project-map/tickets/T-234-blocked-claude-submit-leaves-pane-busy.md`。
- 候选：`/Users/luckye/Documents/Code/a2a-worktrees/T-229-evidence/candidate.patch`，相对 main HEAD `59815ea30`；就是 `/Users/luckye/Documents/Code/a2a` 工作区里 `candidate.files` 列出文件的未提交改动（两个新测试已 `git add -N`）。本轮相对上一轮（`candidate-05.patch`）改了 `workbench/src/gates/cli.ts`（请求带 `submit_deadline`）、`workbench/src/daemon.ts`（`signal` 入口拒绝过期请求），以及 `test_t229_worker_input_e2e.py` 的 `request-hangs` 断言和 `late-handled` 变异。工作区里另有无关的未提交文件，不在本次范围。
- 前几轮：同目录 `REVIEW-01.md`～`REVIEW-05.md`，对应候选 `candidate-01.patch`～`candidate-05.patch`。主控的核实与处理写在 `REPORT.md` 各“第 N 轮审查后的修改与运行”一节。
- 报告与证据：同目录 `REPORT.md` 及其链接的 summary JSON、日志、`runs.log`、各 `run-*.sh`。测试夹具目录按用户要求只留状态、已删除（状态表在 `/Users/luckye/Documents/Code/a2a/evidence/2026-10-31-batch29/T-229/fixtures-status.md`），只能读 summary 与日志。

## 要核对

0. 第五轮的 P1 是否已正确处理：
   - `submit_deadline` 比较的位置是否在 `signal` 处理中任何窗格状态、事件、记录改动之前；从比较到 `noteSubmission` 及回合状态改动之间，是否真的没有 await（会让过期请求在检查后仍被处理）。
   - 7 秒与 8 秒的余量是否足够让“后台已处理且回了 ok、钩子却已放弃并阻断”的窗口实际不出现；两边用同一台机器的时钟，有没有别的时钟问题。
   - 被拒的过期请求在库里留下什么（`request_rejected`、`hook_received` 等），会不会被别处当成这次提交的证据。
   - `request-hangs` 的断言与 `late-handled` 变异是否真的区分新旧行为；把 `no_turn_for_blocked_submission` 只留在 Claude 上的理由（REPORT“第五轮审查后”一节）是否成立，会不会漏掉 Codex 上后台确实开了回合的情况。
   - 拆到 T-234 的“被阻断后窗格停在 busy”是否确属范围外，还是 T-229 本身引入、必须在本票修的回归。
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
