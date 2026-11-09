# T-265 原生验证第二轮：诊断和清理修正

INCOMPLETE：等待主控核对最终脚本后外部运行。native-01 没有业务红态或绿态；其原始结果、启动记录和脚本快照保持原样。第二轮使用当前脚本，不将第一轮结论套用到第二轮。

从工作目录 `/Users/luckye/Library/Application Support/a2a-orchestrator/worktrees/a2a/T-265-1-a1` 执行：

```sh
/usr/bin/python3 -B workbench/tests/test_t265_review_cli_e2e.py --codex /Users/luckye/.local/bin/codex --node /opt/homebrew/Cellar/node/26.5.0/bin/node --summary /Users/luckye/Documents/Code/a2a/evidence/2026-11-09-batch35/T-265/controller/native-cli-02.json
```

运行前核对 `native-plan-02.json` 及当前 `workbench/tests/test_t265_review_cli_e2e.py`。argv 与 native-01 核准版本相同：无 hooks、无 MCP，`-a never`，workspace-write，`writable_roots=[]`，排除 `/tmp` 和 TMPDIR 自动写根，gpt-6-astra / xhigh / default。每轮的候选副本不含 `.git`。不新增权限，不请求弹窗批准，不回退其他运行方式，不启动额外 agent、Claude、后台、hc 或 Electron。

产品 `panes.ts` 与 native-01 快照逐字节一致；原生 argv 与材料读取业务断言的 AST 均一致，见 `driver-scope-02.json`。父版仍要求原生输入上限拒绝且没有 task_started；候选仍要求完整 UTF-8 字节、55000 条 diff、50000 条 verification、头中尾随机标记、材料只读及原生回合开始/结束。

本轮只修驱动：

- 沿用仓库 `t141_probe_codex_start.py` 的 `openpty + Popen + setsid/TIOCSCTTY` 创建方式。Popen 持有自身 waitpid 句柄，启动失败不会让 fork 后的第二个 Python 解释器继续跑清理。
- 保存创建阶段、创建结果、正整数 PID、观察到的 PGID 和退出码。用 Popen.poll/wait 先回收已退出子进程；仍活着时，只有创建记录与当前 PGID 都等于本次子进程 PID、且不是本进程组，才发送 SIGTERM。只有等待超时才在再次核对身份后发送 SIGKILL。EPERM 直接记录失败，不改用另一路信号或权限。
- 终端字节随读取追加并 flush 到证据目录；清理前 fsync，并保存原生关键事件。异常阶段及原异常与清理异常分开保存；cases 在开始时登记，失败也不会丢失该 case。
- 全部业务成功并确认自身子进程已回收，才删除完整夹具。业务或清理不完整时保留失败夹具；已确认退出的子进程可以删除其隔离 CODEX_HOME，未确认退出的子进程目录保持原样并明确上报。删除自身夹具失败也不能保留 PASS。

结果为 `native-cli-02.json` 与 `native-cli-02-artifacts/`。每个 case 保存 `*-launch.json`、逐段落盘的 `*-terminal.txt`、追加式 `*-process.jsonl`、清理前的 `*-before-cleanup-native-events.json`、清理后的 `*-native-events.json` 和 `*-process.json`；目录清理前另存 `before-fixture-cleanup.json`。文件名已存在即拒绝覆盖，不自动重试。

若结果 INCOMPLETE，请回传 summary 和 process/terminal 证据路径，保留未确认退出的夹具。主控按其中的本次 PID、PGID、阶段核对，不按名字或目录通配杀进程。worker 不在沙箱中重试这一步。README stale 已由主控接管，不再为此阻塞或发新状态问题。

离线驱动检查命令：`python3 -B evidence/2026-11-09-batch35/T-265/worker/test_driver_diagnostics.py`（使用本 attempt 的 A2A_REQUEST_DIR）。全部 PTY、Popen、进程查询和信号均为 mock；8/8 通过，见 `driver-green-03.txt`。同一检查指定 `T265_DRIVER_SOURCE=/Users/luckye/Documents/Code/a2a/evidence/2026-11-09-batch35/T-265/controller/native-01-test_t265_review_cli_e2e.py` 时 8/8 失败，见 `driver-native01-counterfactual-02.txt`。这证明驱动诊断和清理修复，不替代真实 CLI 业务结果。
