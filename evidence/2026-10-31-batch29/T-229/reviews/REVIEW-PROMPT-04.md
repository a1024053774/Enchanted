# T-229 只读审查（第四轮）

你是独立审查员，只读：不改文件、不提交、不跑会写文件、起进程、连 hc 或供应商的命令。可以读文件、用 git 查看、在内存里推演。

- 票：`/Users/luckye/Documents/Code/a2a/.project-map/tickets/T-229-worker-input-final-text-only.md`。相关规则：T-216 的派发认领（`workbench/src/panes.ts` 的 `claimShellInboxPrompt`），T-206 的草稿记录与 fail-closed。
- 候选：`/Users/luckye/Documents/Code/a2a-worktrees/T-229-evidence/candidate.patch`，相对 main HEAD `59815ea30`；就是 `/Users/luckye/Documents/Code/a2a` 工作区里 `candidate.files` 列出文件的未提交改动（两个新测试已 `git add -N`）。本轮比上一轮多了 `workbench/src/gates/cli.ts` 与五个单元测试夹具。工作区里另有无关的未提交文件，不在本次范围。
- 前几轮：同目录 `REVIEW-01.md`、`REVIEW-02.md`、`REVIEW-03.md`，对应候选 `candidate-01.patch`、`candidate-02.patch`、`candidate-03.patch`。主控的核实与处理写在 `REPORT.md` 的“第一轮／第二轮／第三轮审查后的修改与运行”三节。第一轮第 3 条判为不是问题，前两轮审查已认可理由。
- 报告与证据：同目录 `REPORT.md` 及其链接的 summary JSON、日志、`runs.log`、各 `run-*.sh`，单元测试比较在 `r5-unit/`。

## 要核对

0. 第三轮两条意见是否都已正确处理：阻断是否覆盖整个 UserPromptSubmit 钩子请求路径（后台各步写入失败、连不上后台）；查询或认领失败时是否标了观察失败。第二轮加的那层诊断写入删掉后，失败是否仍有记录。修改有没有引入新问题，例如钩子命令对 UserPromptSubmit 的其他拒绝（会话不符、提示号重复、注入正文不一致等）现在一律阻断，这个行为变化是否合理、会不会误伤正常提交或受管主控、审查员窗格。
1. Claude Code、Codex worker 窗格：用户提交是否每次恰好记一条、文字等于 CLI 实际提交的全文；有没有漏记的提交路径（新回合、回合中排队、被拒或阻断的提交、恢复后的窗格、受管主控与审查员窗格）；有没有重复记录。
2. 认领：哪些派发会被认领、哪些不会；用户提交与某条派发全文相同、派发未送出或被打断、旧库里早已提交但没有认领事件的派发，这些情况下会不会吞掉用户输入或把派发记成用户输入。
3. agy、opencode：记录是否仍按草稿、不带按键、拼不准时标 text_uncertain；`submitHook` 的判定是否覆盖所有 CLI 名称。
4. 人工介入是否照旧派生；用户输入观察失败时的行为与改动前相比有没有退化。
5. 测试：期望是否来自票面；红态是否真在基线上失败；变异是否能区分、是否失败在业务断言上；单元夹具的改动是否削弱原测试的意图（特别是给 T-108 夹具接一个什么也不记的 `recordUserSubmission`）；有没有可能空转的检查。
6. REPORT 每条结论与所链证据是否一致。
7. 有没有吞异常、fallback、兼容分支、平行路径；新的 catch 是否只在本层拥有恢复职责时才接住。

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
