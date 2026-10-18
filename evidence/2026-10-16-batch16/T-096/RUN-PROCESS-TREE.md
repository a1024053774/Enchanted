# T-096：真实进程树演练与 red-b-04 归档

本阶段 **PASS**：主控 #99／#13 已运行以下对照，旧候选按预期失败，当前修复四场 PASS，全部独立收尾完成；red-b-04 归档 PASS。摘要已保存，以下命令保留为复现记录，不重跑相同输出路径。T-096 原生重启验收仍为 INCOMPLETE，下一步 red-b-05／tracer-b-05 见 [RUN-RESTART.md](RUN-RESTART.md)。

预算：每场依次创建四棵私有 Python 父子树，每棵两个 Python 进程；不启动供应商 CLI、a2a daemon 或 Electron，不调用模型，不发终端键。Python 父进程只提供私有 Unix socket 的 status／stop 测试回执，每场景最多两次 operator 请求、各限 30 秒。每场景最多 240 次仅限登记 PID 的 ps；同启动时间但 command 变化只等待最多 3 秒，不发信号，持续存活则拒绝。父进程均在独立进程组；独立收尾只通过私有管道关闭、等待并回收子进程，不重试信号或杀进程组。源夹具在 `/private/tmp`，原始记录与已停夹具副本在外置盘；原件保留。

上一次沙箱尝试 `process-tree-red-01.json` 在首次 ps 处被拒绝，未形成真实红态。独立收尾已发送 private shutdown 并等父进程返回，但其后 ps 仍被沙箱阻止；原摘要为 cleanup false。请先只读核对这两个登记 PID，不发信号：

```sh
/bin/ps -ww -p 56541,56543 -o pid=,lstart=,command=
```

rc 1 且输出为空表示两者已退出；其他结果请保留读回、停止后续演练并交回。被拒绝的升级申请没有运行记录，本 worker 不再申请升级。

红态：旧候选 `da6a095fce268e2c8c6707e08ce432851bbfddbb`。下列输出名均未使用；不覆盖已有文件。原始 JSON 在外置盘，仓库只保存小摘要。

```sh
python3 workbench/tests/test_t096_process_tree.py --candidate da6a095fce268e2c8c6707e08ce432851bbfddbb --output /Volumes/WD-Elements/a2a-evidence/2026-10-16-batch16/T-096/process-tree-red-02/run.json --summary evidence/2026-10-16-batch16/T-096/process-tree-red-02.run.json
```

红态预期 rc 1、INCOMPLETE。必须在 `zombie` 场景实际读到 Z 状态，`injection_error` 为身份变化拒绝；旧 finally 在已停死端点场景也应失败。四场的独立 `cleanup` 应全为 true，表明旧候选失败后，测试自身也没有遗留进程。若是 ps 权限、夹具或协议错误，则不算所需红态。任一场出现 handoff／cleanup false 时先停，按摘要交回，不继续绿态。

绿态：当前已提交修复。脚本在启动资源之前核对自身与被调用 helper 没有未提交改动，保存 harness 的完整提交号；`worktree` 表示该提交上的 runner 源码。

```sh
python3 workbench/tests/test_t096_process_tree.py --candidate worktree --output /Volumes/WD-Elements/a2a-evidence/2026-10-16-batch16/T-096/process-tree-green-01/run.json --summary evidence/2026-10-16-batch16/T-096/process-tree-green-01.run.json
```

绿态预期 rc 0、PASS，四场均 PASS／cleanup true：

1. `parent-death`：杀父后子进程因私有管道 EOF 自行退出，轮到子进程时不再发信号。
2. `zombie`：子进程退出但父进程暂不回收，实际 ps 读到 Z；kill 不发信号，只等父进程回收后确认 PID 不存在。
3. `already-exited`：子进程在 kill 之前已自行退出并被回收；不发信号，继续收尾。
4. `live-replacement`：同 PID／同启动时间的进程 exec 成另一命令并持续存活；必须拒绝发信号，替代进程仍存活，再由测试私有协议正常关闭。

每场都执行候选 runner 的实际 `identify/alive/kill` 与完整 finally；进程和信号边界不用替身。需要候选确认所有登记 PID 不存在、确认死端点、复制并比较已停夹具。测试故意从 INCOMPLETE 开始，收尾成功不得把候选失败改记 PASS；演练自身的 PASS 单独记录。原始 JSON 中 `runner_result` 是候选收尾证据，摘要 `cleanup` 是独立测试收尾证据，两者不能混淆。

red-b-04 的固定只读归档：仅接受 `/private/tmp/t078-2-t096-mhufgnng`、主控列出的七个 PID、epoch 1 与原 ownership journal。无启动、信号、stop 请求或源目录写入。活动／未知 PID 或端点均拒绝；排除死 socket 与 operator 私密文件后，复制并比较数量、字节、路径；所有原件保留。

```sh
python3 evidence/2026-10-16-batch16/T-096/archive_failed_02.py --case red-b-04 --label archive-red-b-04 --approval-ref '执行主控 T-096 #11／#12：只读核对并归档 red-b-04'
```

归档摘要：`evidence/2026-10-16-batch16/T-096/archive-red-b-04.run.json`；清单：`red-b-04-archive-red-b-04.archive.json`；副本：`/Volumes/WD-Elements/a2a-evidence/2026-10-16-batch16/T-096/red-b-04/fixture`。旧 red-b-04.run.json 的 INCOMPLETE 不变。
