# T-216 第七轮只读审查

你是独立审查员，只读：不改文件、不提交、不跑会写文件或连 hc、供应商的命令。可以读文件、用 git 查看、在内存里跑小段 node/python 推演。

## 对象

- 票：`/Users/luckye/Documents/Code/a2a/.project-map/tickets/T-216-issues-pushed-to-controller.md`（验收条目）。
- 候选：`/Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round7-candidate.patch`，相对基线 `9c0e26212`；工作树 `/Users/luckye/Documents/Code/a2a-worktrees/T-216` 就是它。
- 本轮改动与证据：`/Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/REPORT.md` 的“第七轮”一节，及其中链接的 JSON、日志。前几轮审查意见：同目录 `ROUND6-REVIEW-01.md`、`ROUND6-REVIEW-02.md`。

## 要核对

1. `workbench/src/panes.ts` 的 `claimShellInboxPrompt`：新规则（已写 `hc_send_intent`、未被认领的派发全文相同即认领为系统、只一次；最新事件 `hc_send_rejected` 时不认领）是否正确实现；能否把用户自己的输入误认领为系统（除 REPORT 写明已接受的代价外），或把系统派发漏记成用户输入。ROUND6-REVIEW-02 的 P1 是否已解决。
2. `workbench/terminal/bin/codex` 新加的 `notice.hide_rate_limit_model_nudge=true`：参数是否生效、位置是否让用户自己的 `-c` 仍能覆盖、注释是否属实。
3. 测试：`test_t216_prompt_provenance_e2e.py` 的 never-sent 新期望与 `require-hc-return` 变异、`test_t216_real_cli_delivery_e2e.py` 的 `--quota-warning`，期望值是否来自需求而非实现输出，变异是否真能区分好坏实现。
4. REPORT 第七轮的每条结论与所链 JSON 是否一致（状态、检查项名、失败项）；“没有重跑的运行不经过这两处改动”是否成立。
5. 有没有吞异常、fallback、兼容分支、平行路径。

## 输出

写到标准输出，格式：

```
STATUS: PASS | FAIL
FINDINGS:
- [P0|P1|P2] 文件:行 — 问题；会怎样出错
EVIDENCE:
- 你实际读过、跑过什么，引用文件和行号
LIMITATIONS:
- 没核对到的
```

每条意见都要给出文件和行号或 JSON 字段，主控会逐条核对引用。没有阻塞问题就写 PASS。
