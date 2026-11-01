STATUS: FAIL

FINDINGS:

- [P1] [hc.ts:206](/Users/luckye/Documents/Code/a2a/workbench/src/hc.ts:206)、[hc.ts:210](/Users/luckye/Documents/Code/a2a/workbench/src/hc.ts:210) — 身份检查没有绑定随后建立的连接。可达时序是：`lsof` 已观察到私有 core 打开锁文件；该 core 随后崩溃，终端客户端抢先在同一 socket 拉起默认 XDG 的外来 core；第 210 行连接新 core，第 211 行只检查 framed hello，随后允许 `terminal.run`。这样仍可能接受外来 core，并继承错误环境。应核对实际连接对应的 core 身份，并补充检查期间换 core 的反例。

EVIDENCE:

- 已读第二轮 `candidate.patch`、五个候选文件及直接调用路径；相对 `03ba1cf54` 在内存中应用补丁后逐字匹配工作区，审查结束时仍未变化。
- 上轮 P1 已解决：[hc.ts:204](/Users/luckye/Documents/Code/a2a/workbench/src/hc.ts:204) 将路径交给 `lsof` 筛选，只解析 PID。`r2-green-holder-non-ascii/run.json.checks` 全为 true；对应 foreign 记录确认拒绝。
- 上轮 P2 已解决：[daemon.ts:60](/Users/luckye/Documents/Code/a2a/workbench/src/daemon.ts:60) 只捕获 `hc.start()`；记录成功后重抛原错误，记录失败则用 `AggregateError` 保存两个错误。未发现吞异常或掩盖后续启动失败。
- [hc.ts:195](/Users/luckye/Documents/Code/a2a/workbench/src/hc.ts:195) 仍拒绝相同 PGID，保留 T-212 的进程组 detach 要求。`lsof` 非零退出、超时或缺少目标 PID 时均拒绝；锁仅被其他 PID 打开也不能通过。
- [新测试:138](/Users/luckye/Documents/Code/a2a/workbench/tests/test_t228_core_identity_e2e.py:138) 与第 159 行的 holder/foreign 期望来自 T-228。两轮变异记录均因错误接受 foreign、缺少拒绝事件而失败，具有区分力。
- [T-212 测试:231](/Users/luckye/Documents/Code/a2a/workbench/tests/test_t212_shell_hc_e2e.py:231) 接受 `initial-daemon` 符合 holder 继承原受控环境的事实，仍要求私有 XDG；第二轮 `core_restart.observed_environment` 支持该修改。
- REPORT 的主要绿态、变异及回归结论与所链 JSON 一致；第二轮 Electron `screen_comparison` 为 692 行对 692 行，`missing`、`extra` 均为空。未发现新增 fallback、兼容分支或平行运行路径。

LIMITATIONS:

- 未运行测试、status、hc 或供应商命令；上述连接竞态为静态推演，未现场复现。
- 证据未覆盖检查期间换 core、`lsof` 故障/超时、同 PGID、伪造 PID及事件写入失败。
- REPORT 第 49、59 行所述失败现场已删除；现存 JSON/日志只能确认启动失败或断言位置，不能独立恢复所述 stderr 原文及旧环境探针值。
- “打开私有锁文件”本身不证明持有排他锁，也不直接证明完整环境经过清理。