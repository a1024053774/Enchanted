# T-229 只读审查（第十二轮）

你是独立审查员，只读：不改文件、不提交、不跑会写文件、起进程、连 hc 或供应商的命令。可以读文件、用 git 查看、在内存里推演。

- 票：`/Users/luckye/Documents/Code/a2a/.project-map/tickets/T-229-worker-input-final-text-only.md`。已并入本票：`/Users/luckye/Documents/Code/a2a/.project-map/tickets/T-234-blocked-claude-submit-leaves-pane-busy.md`。
- 候选：`/Users/luckye/Documents/Code/a2a-worktrees/T-229-evidence/candidate.patch`，相对 main HEAD `59815ea30`；就是 `/Users/luckye/Documents/Code/a2a` 工作区里 `candidate.files` 列出文件的未提交改动（两个新测试已 `git add -N`）。工作区里另有无关的未提交文件，不在本次范围。
- 本轮相对上一轮（`candidate-11.patch` 是第十一轮审查时的候选）：Codex UPS 判断同一回合追加输入时，要求 `active` 不早于最近一次打断（`panes.ts` Codex UPS 处的 `steered`）；新场景 `esc-then-submit`（Codex）与变异 `esc-reuses-turn`；T-207 测试的变异定位串跟随第九轮的缩进变化（`test_t207_user_turn_delivery_e2e.py` 已加入 `candidate.files`）。T-235 扩到同一 harness 的三个场景（基线上同样失败）。
- 前几轮：同目录 `REVIEW-01.md`～`REVIEW-11.md`，对应候选 `candidate-01.patch`～`candidate-11.patch`。主控的核实与处理写在 `REPORT.md` 各“第 N 轮审查后的修改与运行”一节。
- 证据：同目录 `REPORT.md`、`runs.log`、`run-round14.sh`、`r14-*.json`/`.log`、`r14-unit/`、`r14-base-*`、`r13-base-*`（之前几轮的也在）。本轮夹具跑完即删，只留摘要（`fixtures-r14.tsv` 记了每次尝试的夹具路径）；HEAD 对照副本在 `/private/tmp/t229-head`。

## 要核对

0. 第十一轮意见（REPORT“第十一轮审查后”一节）：
   - Codex `steered` 的判断是否正确区分新回合与同回合追加；有没有把真正的同回合追加（含打断后同一新回合里的第二次追加）误判为新回合，或反过来；Claude 一侧是否需要同样处理。
   - `esc-then-submit` 的检查是否测到审查描述的业务后果；T-207 变异定位修正是否正确。
   - T-235 扩到 T-157 stop-input、T-165 ordered，证据（`r14-reg-*`、`r14-base-*`）是否支持“基线既有”。
   - 前几轮已处理的各项（草稿按输入代数释放、记录即提交点、期限、阻断后不改窗格、认领、观察失败）是否仍成立。
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
