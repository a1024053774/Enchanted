# T-230 只读审查

你是独立审查员，只读：不改文件、不提交、不跑会写文件、起进程、连 hc 或供应商的命令。可以读文件、用 git 查看、在内存里推演。

- 票：`/Users/luckye/Documents/Code/a2a/.project-map/tickets/T-230-enchanted-terminals-a2a-only.md`。背景决定见 T-220。
- 候选：`/Users/luckye/Documents/Code/a2a-worktrees/T-230-evidence/candidate.patch`，相对 main HEAD `121c43f21`；就是 `/Users/luckye/Documents/Code/a2a` 工作区里 `candidate.files` 列出的五个文件的未提交改动（新测试已 `git add -N`）。工作区里另有无关的未提交文件，不在本次范围。
- 报告与证据：同目录 `REPORT.md` 及其链接的 run 目录（run.json、日志、截图）、`regression-runs.log`、`run-regression.sh`。

## 要核对

1. 四个 `HC_*` 变量是否在所有项目终端（含 worker、主控、普通终端）启动时都去掉；有没有别的启动路径把它们带进去；a2a 自己的终端身份是否保留。
2. 去掉变量后，终端里的 hc 调用在 core 崩溃时是否确实碰不到私有 core；测试的“外来 core”判据（父进程、私有锁、夹具 HOME 下的会话目录）能否空转。
3. 验收第 4 条（经 a2a 命令跨终端发字有记录、目标提交不记为用户输入）用 T-216 既有 e2e 覆盖，这个论证是否成立。
4. 界面“历史不完整”：数据从哪来，exact/未知时会不会误显示或漏显示；复位与接回是否未改。
5. 测试：期望是否来自票面；红态是否真在基线上失败；变异是否能区分；边界测试的缓存路径改动是否影响原意。
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
