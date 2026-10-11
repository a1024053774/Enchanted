# T-078 变基冲突处理

当前结论 **INCOMPLETE**：两个文本冲突已解决，静态检查通过，等待执行主控运行 `git rebase --continue`。最终候选验收和独立审查尚未运行。

起点为 worker 提交 `b5ed880b8ad0461786a8aee7f4e0a18ea42752a3`，目标 main 为 `532c51f4cc12352bb7cf545ce1e5f824d68bdc4a`。原冲突内容及 combined diff 保存在本目录，原 outside-rebase-01 失败输出不修改。

两个冲突的取舍如下：

- `workbench/README.md`：保留 main 的 run 传输期限、停止受理及收尾说明，同时保留本卡的管理凭据、GateActor 与 SubmitCaller 区分说明。没有删掉任一侧的段落。
- `workbench/tests/run_daemon_acceptance.py`：同时声明 BASE、IDENTITY；保留 main 的 `--output-root`、子进程输出根传递、legacy validation 限制及默认 runner 身份；保留本卡的显式 `--output`、`--identity-file`、凭据排除归档。读取身份文件时合并默认字段，避免原本整表替换把 main 输出使用的 `runner` 删除。

自动合并逐处核对：

- panes 的启动环境仍区分请求模型／强度；readThread 仍核对进程，并返回 launch、thread、shell_pid、leader_pid、native_session 的 runtime_identity。
- core 的稳定所有者校验、首次观测绑定、原生 submit 的 caller/thread/turn 与非空身份检查、回收身份检查全部保留；beginShutdown 及 run 各安全边界仍有效。
- daemon 保留停止拒收、在途请求和回执收尾、signal 后延迟 drain 的计数；本卡的 operator 凭据只传 GateActor，不伪造 SubmitCaller。worker inbox 仍经已认证 Stop caller，并核对当前 attempt。
- cli、relay、credentials 与冻结 worker 提交逐字节相同；transport 保留 main 的 run 等待余量。验收 host 同时保留 main 的受控运行时身份和本卡的 operator 凭据／真实 SubmitCaller 分离。

静态检查通过：七个共享源码文件中 main 新增的 41 个连续代码块均保留；23 个只由 main 修改的 workbench 文件逐字节保留。Python／TypeScript 语法及参数解析检查通过。参数检查将 suite/probe 执行替换为记录器，只证明参数和输出目录传递，没有启动后台、socket、PTY、Electron、Claude 或其夹具，也不替代最终 8/9/18。

复现静态检查（输出目录须为新目录）：

```sh
python3 evidence/2026-10-11-batch13/T-078/verify_rebase_resolution.py --output evidence/2026-10-11-batch13/T-078/rebase-resolution-replay-01
```

实际结果见 `../rebase-resolution-check-02/results.json`，48 项 PASS。首轮检查器对 `/tmp` 别名的误判保留在 check-01，原因及更正见本目录 PROBE-NOTE.md；没有改验收业务断言。此次只暂存两个冲突文件，证据文件留待后续证据提交。
