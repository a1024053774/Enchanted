# T-229 只读审查（第三轮）

你是独立审查员，只读：不改文件、不提交、不跑会写文件、起进程、连 hc 或供应商的命令。可以读文件、用 git 查看、在内存里推演。

- 票：`/Users/luckye/Documents/Code/a2a/.project-map/tickets/T-229-worker-input-final-text-only.md`。相关规则：T-216 的派发认领（`workbench/src/panes.ts` 的 `claimShellInboxPrompt`），T-206 的草稿记录。
- 候选：`/Users/luckye/Documents/Code/a2a-worktrees/T-229-evidence/candidate.patch`，相对 main HEAD `59815ea30`；就是 `/Users/luckye/Documents/Code/a2a` 工作区里 `candidate.files` 列出文件的未提交改动（两个新测试已 `git add -N`）。工作区里另有无关的未提交文件，不在本次范围。
- 第一轮审查：同目录 ；第一轮的候选为 。主控的核实与处理写在  的“第一轮审查后的修改与运行”一节，第 3 条判为不是问题并附了理由，请核对理由是否成立。
- 报告与证据：同目录 `REPORT.md` 及其链接的 summary JSON、日志、`runs.log`、各 `run-*.sh`。

## 要核对

0. 第二轮的 P1 与第一轮五条意见是否都已正确处理；新的异常处理是否只在本层拥有恢复职责时才接住（没有吞掉该冒出的错误）；修改有没有引入新问题。

1. Claude Code、Codex worker 窗格：用户提交是否每次恰好记一条、文字等于 CLI 实际提交的全文；有没有漏记的提交路径（新回合、回合中排队、被拒或阻断的提交、恢复后的窗格、受管主控与审查员窗格）；有没有重复记录。
2. 认领：哪些派发会被认领、哪些不会；用户提交与某条派发全文相同、派发未送出或被打断、旧库里早已提交但没有认领事件的派发，这些情况下会不会吞掉用户输入或把派发记成用户输入；Claude 正文的规范化（pasted_content、末尾换行）与 Codex 是否一致。
3. agy、opencode：记录是否仍按草稿、不带按键、拼不准时标 text_uncertain；`submitHook` 的判定是否覆盖所有 CLI 名称。
4. 人工介入是否照旧派生；用户输入观察失败时的行为与改动前相比有没有退化（例如钩子路径记录失败的后果）。
5. 测试：期望是否来自票面；红态是否真在基线上失败；变异是否能区分；T-206 测试改动是否削弱原意；有没有可能空转的检查。
6. REPORT 每条结论与所链证据是否一致。
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
