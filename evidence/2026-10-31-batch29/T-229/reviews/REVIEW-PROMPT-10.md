# T-229 只读审查（第十轮）

你是独立审查员，只读：不改文件、不提交、不跑会写文件、起进程、连 hc 或供应商的命令。可以读文件、用 git 查看、在内存里推演。

- 票：`/Users/luckye/Documents/Code/a2a/.project-map/tickets/T-229-worker-input-final-text-only.md`。已并入本票：`/Users/luckye/Documents/Code/a2a/.project-map/tickets/T-234-blocked-claude-submit-leaves-pane-busy.md`。
- 候选：`/Users/luckye/Documents/Code/a2a-worktrees/T-229-evidence/candidate.patch`，相对 main HEAD `59815ea30`；就是 `/Users/luckye/Documents/Code/a2a` 工作区里 `candidate.files` 列出文件的未提交改动（两个新测试已 `git add -N`）。工作区里另有无关的未提交文件，不在本次范围。
- 本轮相对上一轮（`candidate-09.patch` 是第九轮审查时的候选）：成功的 UPS 只在回车之后没再输入时释放草稿（`inputDraft.ts` 的 `draftHeld`）；用户提交一经记录就是提交点，之后这次请求里的写入失败（`panes.ts` 的 `afterRecord`、`daemon.ts` 的 `request_result`）把窗格标为失败，钩子不再阻断。新场景 `draft-after-enter`、`after-record-fails`、`result-fails`，新变异 `draft-released-on-submit`、`record-then-block`；T-108 两个夹具的窗格补上空草稿。
- 前几轮：同目录 `REVIEW-01.md`～`REVIEW-09.md`，对应候选 `candidate-01.patch`～`candidate-09.patch`。主控的核实与处理写在 `REPORT.md` 各“第 N 轮审查后的修改与运行”一节。
- 证据：同目录 `REPORT.md`、`runs.log`、`run-round12.sh`、`r12-*.json`/`.log`、`r12-unit/`（上一轮的 `r11-*` 也在）。本轮夹具跑完即删，只留摘要（`fixtures-r12.tsv` 记了每次尝试的夹具路径）；HEAD 对照副本在 `/private/tmp/t229-head`。

## 要核对

0. 第九轮两条意见（REPORT“第九轮审查后”一节）：
   - 草稿释放：`draftHeld` 按 attach 一侧草稿判断是否还有回车后的输入，有没有误放（派发粘到未发出的字上）或永远占用的路径；Claude 排队输入、新 prompt、Codex 三处是否一致。
   - 记录即提交点：记录之后的失败改为标窗格失败、不阻断，是否让“有记录”等于“CLI 执行了”；`afterRecord` 把记录之后的 `check` 失败也算作窗格失败，是否合适；`daemon.ts` 那处 catch 对其他请求是否照旧抛出；有没有新的吞异常。
   - 前几轮已处理的各项（期限、阻断后不改窗格、认领、观察失败）是否仍成立。
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
