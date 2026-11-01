# T-228 只读审查

你是独立审查员，只读：不改文件、不提交、不跑会写文件、起进程、连 hc 或供应商的命令。可以读文件、用 git 查看、在内存里推演。

- 票：`/Users/luckye/Documents/Code/a2a/.project-map/tickets/T-228-daemon-refuses-holder-core.md`；背景 `T-220-core-crash-autostart-env.md` 同目录。
- 候选：`/Users/luckye/Documents/Code/a2a-worktrees/T-228-evidence/candidate.patch`（第二轮），相对 main `03ba1cf54`；就是 `/Users/luckye/Documents/Code/a2a` 工作区里这五个文件的未提交改动（工作区里还有别的无关改动，忽略）。
- 报告与证据：同目录 `REPORT.md` 及其链接的 run.json、日志。这是第二轮：上一轮审查 `REVIEW-01.md` 的 P1（lsof 路径转义）与 P2（事件写入失败盖掉启动错误）已改，见 REPORT“第二轮”。请核对这两条是否真正解决，并照常审全部候选。

## 要核对

1. `workbench/src/hc.ts` 新判据：能否接受外来 core，或拒绝自己的 core（holder 重拉、后台自己拉起、路径写法差异）；`lsof` 失败、超时、输出格式时的行为；pid 与锁持有者不一致时。
2. 去掉“父进程是 1”后，“不在后台进程组里”是否仍守住 T-212 的 detach 要求。
3. `daemon.ts` 的 `hc_start_failed`：是否吞异常、是否会掩盖别的失败。
4. 测试：`test_t228_core_identity_e2e.py` 的期望是否来自票面而非实现；变异是否能区分；对 `test_t212_shell_hc_e2e.py` 断言的修改是否合理，还是放宽了不该放宽的。
5. REPORT 每条结论与所链 run.json 是否一致。
6. 有没有 fallback、兼容分支、平行路径。

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
