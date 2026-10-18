# T-096-1 当前交付记录

**BLOCKED**：当前为单窗格 Tracer bullet 候选，尚未完成任务卡验收。

身份：s16-t096；T-096 / a1；执行器 gpt-6.1-sol / xhigh；派发来源 launch-14dcc6be543a483ab0b03021f573d028；起点 main 3c9016d02；合同 ready_rev 1。CLI 实际供应 tier 未核对。

Ubiquitous language 沿用 CONTEXT.md 的启动记录、原生会话、attempt 与窗格。Deep modules：恢复的 argv 与原生会话核对由 `paneRecovery.ts` 承担，启动配置仍只读原启动记录；窗格集是同库现有事件流的投影，没有第二套 profile。

已有证据（均为局部合同，不是后台或 GUI 验收）：

- `contract-red-01.json`：修复前 recover 重启数为 0，命中应为 1 的业务断言。真实 SQLite，替代进程边界；模型回合 0。
- `contract-tracer-green-02.json`：同一合同转绿，核对前台身份确认、原启动记录不变，以及非 session 选择器的 argv 字段保留。
- `t091-ipc-regression-01.json`：新 layout 命令未被旧 VM 边界识别，属于测试适配失败，保留。
- `t091-ipc-regression-02.json`：只增加 operator layout 命令边界后，原 pane-key、窗口隔离、序列号、输出路由、历史 attempt、错误绑定等断言通过；两个已知坏版本仍被原业务断言拒绝。
- `t091-version-regression-01.json`：原 Claude 启动版本合同及版本校验变异检查通过。

未完成：main 上真实重启红态、单窗格后台/PTY/Electron Tracer bullet、三窗格绿态、四个真实入口反例、Claude 原生 CLI 零回合续接探针、完整回归、独立审查和门禁 submit。

阻塞根因及最小选项见 `ISSUE-worker-runtime-rebinding.md`。任务卡禁止 gates/；没有伪装旧 PID 或直接改门禁库。

`run_restart.py` 为主控执行的单窗格红态/绿态脚本，开头列明 CLI、按键、模型与故障注入预算。当前未运行。命令示例（先核对 source 冻结版本、独占 Electron 和外置盘）：

```sh
python3 evidence/2026-10-16-batch16/T-096/run_restart.py --source /Users/luckye/Documents/Code/a2a --output /Volumes/WD-Elements/a2a-evidence/2026-10-16-batch16/T-096/red-01 --label red-01 --approval-ref T-096-controller-red --expect-red
python3 evidence/2026-10-16-batch16/T-096/run_restart.py --source /Users/luckye/Documents/Code/a2a-wt-t096 --output /Volumes/WD-Elements/a2a-evidence/2026-10-16-batch16/T-096/tracer-01 --label tracer-01 --approval-ref T-096-controller-tracer
```

脚本仅使用受控 receiver 替代 Codex，不能证明真实 Codex resume。它不读取登录凭据；归档在外置盘，失败原件保留。没有运行 daemon、PTY、ps、Electron、截图或真实模型；这些仍交主控执行。
