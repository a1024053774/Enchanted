# T-227 只读审查（第四轮）

你是独立审查员，只读：不改文件、不提交、不跑会写文件、起进程、连 hc 或供应商的命令。可以读文件、用 git 查看、在内存里推演。

- 票：`/Users/luckye/Documents/Code/a2a/.project-map/tickets/T-227-trace-failure-aftermath.md`。
- 候选：`/Users/luckye/Documents/Code/a2a-worktrees/T-227-evidence/candidate.patch`，相对 main `03ba1cf54`（之后 main 上提交了 T-228 的 `10e4fcbfd`、`bbf8d5f80`，不碰这三个文件，候选相对 HEAD 逐字不变）；就是 `/Users/luckye/Documents/Code/a2a` 工作区里 `workbench/src/panes.ts`、`workbench/tests/test_pane_trace_failure.ts`、`workbench/tests/test_t212_trace_failure_e2e.py` 的未提交改动。工作区里另有无关的未提交文件，不在本次范围。
- 报告与证据：同目录 `REPORT.md`（第四轮一节）及其链接的 run.json、日志；前三轮审查意见见 `REVIEW-01.md`～`REVIEW-03.md`。

## 要核对

0. REVIEW-01～03 的意见是否都已解决；`recordFailure` 的新规则（每种失败只记一次、保留首个原因）对其他调用者有没有坏影响，修改有没有带来新问题。

1. 选定的两条规则（初次打开失败当场关掉终端；trace 失败后停写、只记一次）是否在所有写 trace 的地方一致实现，有没有漏掉的写入点或第二套规则。
2. `startShell` 失败时关闭终端：会不会关错终端、悬挂、吞掉原错误；关闭失败时的行为。
3. 停写后有没有该继续做的事被一并跳过（例如 OSC 7501 状态、终端协议应答、原生会话扫描），与改动前相比是否退化。
4. 测试：期望是否来自票面；变异是否能区分；检查项是否可能空转。
5. REPORT 每条结论与所链 run.json、日志是否一致。
6. 有没有吞异常、fallback、兼容分支、平行路径。

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
