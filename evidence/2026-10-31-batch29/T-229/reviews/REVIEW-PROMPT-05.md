# T-229 只读审查（第五轮）

你是独立审查员，只读：不改文件、不提交、不跑会写文件、起进程、连 hc 或供应商的命令。可以读文件、用 git 查看、在内存里推演。

- 票：`/Users/luckye/Documents/Code/a2a/.project-map/tickets/T-229-worker-input-final-text-only.md`。相关规则：T-216 的派发认领（`workbench/src/panes.ts` 的 `claimShellInboxPrompt`），T-206 的草稿记录与 fail-closed。
- 候选：`/Users/luckye/Documents/Code/a2a-worktrees/T-229-evidence/candidate.patch`，相对 main HEAD `59815ea30`；就是 `/Users/luckye/Documents/Code/a2a` 工作区里 `candidate.files` 列出文件的未提交改动（两个新测试已 `git add -N`）。本轮相对上一轮（`candidate-04.patch`）改了 `workbench/src/gates/cli.ts` 的钩子期限、`test_t229_worker_input_e2e.py` 的 `request-hangs` 场景与 `no-deadline` 变异、`t108_answer_lifecycle_contracts.mjs` 的 `unknown_pty_queued`。工作区里另有无关的未提交文件，不在本次范围。
- 前几轮：同目录 `REVIEW-01.md`～`REVIEW-04.md`，对应候选 `candidate-01.patch`～`candidate-04.patch`。主控的核实与处理写在 `REPORT.md` 各“第 N 轮审查后的修改与运行”一节。
- 报告与证据：同目录 `REPORT.md` 及其链接的 summary JSON、日志、`runs.log`、各 `run-*.sh`；单元比较在 `r5-unit/`。第六轮的测试夹具目录按用户要求只留状态、已删除（状态表在 `/Users/luckye/Documents/Code/a2a/evidence/2026-10-31-batch29/T-229/fixtures-status.md`），所以不能再读夹具库，只能读 summary 与日志。

## 要核对

0. 第四轮两条意见是否都已正确处理：
   - 8 秒期限是否真的早于两家 CLI 的钩子限时（看 `panes.ts` 的钩子配置与 `transport.ts` 的 `requestAt`、AbortSignal 的处理），期限到时是否一定输出阻断并以 0 退出；有没有别的步骤（读凭据、建 trace、解析 stdin）在期限之外，仍可能拖过 10 秒或抛错后不阻断。
   - REPORT 与 `cli.ts` 注释写的遗留问题（后台超过 8 秒才处理时，仍可能记下被阻断的提交并标回合开始）是否说清了影响，是否有更小的根因层改法应在本票做。
   - `request-hangs` 场景与 `no-deadline` 变异是否真的测到期限：压住的是哪一步，变异是否失败在业务断言上。
   - `unknown_pty_queued` 改用 opencode 窗格后，是否仍检查原场景的意图（排队输入与未知 PTY 写入），没有空转。
1. Claude Code、Codex worker 窗格：用户提交是否每次恰好记一条、文字等于 CLI 实际提交的全文；有没有漏记或重复记录的路径。
2. 认领：派发会不会被记成用户输入，用户输入会不会被吞掉。
3. agy、opencode：记录按草稿、不带按键、拼不准时标 text_uncertain。
4. 人工介入照旧派生；观察失败时的行为没有退化。
5. 测试：期望来自票面；红态在基线上失败；变异失败在业务断言上；有没有空转的检查。
6. REPORT 每条结论与所链证据是否一致（特别是第六轮的磁盘写满与启动超时重跑）。
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
