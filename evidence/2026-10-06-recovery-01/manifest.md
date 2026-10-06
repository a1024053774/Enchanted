# T-007 运行清单（2026-10-06）

状态：PASS，限 T-007 声明。完整结果与原始证据索引见 [RESULTS.md](RESULTS.md)。

- 源码基线 aca370a30fb1fdd938cf89c29ffe2e2f75a21583；T-006 8 项与真实模型闭环已通过。
- 范围：真实本地 CLI 进程、Git、SQLite 的验收及集成中断恢复。不是 Herdr server 崩溃，也不杀用户已有进程。
- recovery-check 独占新恢复测试；recovery-build 独占 coop.py / README.md，红态确认前只读准备。
- 请求配置均为 gpt-6.1-sol xhigh Fast；启动记录见 commands.jsonl，供应商实际 tier 未独立观测。
- 失败只影响各自生成的隔离 fixture；不会覆盖以前的运行产物。
- 父版本失败、实现后同一入口结果、known-bad 反事实和固定候选审查分别保存。
- 主控继续按 project-map 推进：T-007 完成后进入 T-008 程序自动推进，避免模型记忆每个操作步骤。
