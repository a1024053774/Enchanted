# T-265 第四轮外部验证：退出竞态修正

INCOMPLETE，候选真实验证尚未完成。native-03 已保留真实父版红态：原生 ready 后实际投递 1665447 字符，Codex 明确拒绝超过 1048576 字符的输入，原生事件为空。该轮因为 TERM 超时后 getpgid 报 ESRCH 而整体 INCOMPLETE，候选未启动。native-01/02 仍是启动/驱动 INCOMPLETE，不算业务红态。原始结果和脚本快照不修改。

工作目录：`/Users/luckye/Library/Application Support/a2a-orchestrator/worktrees/a2a/T-265-1-a1`。

```sh
/usr/bin/python3 -B workbench/tests/test_t265_review_cli_e2e.py --codex /Users/luckye/.local/bin/codex --node /opt/homebrew/Cellar/node/26.5.0/bin/node --summary /Users/luckye/Documents/Code/a2a/evidence/2026-11-09-batch35/T-265/controller/native-cli-04.json
```

本轮只改 `stop_owned`：每轮信号前重新用同一 Popen.poll 核对退出。getpgid/killpg 若发生 ProcessLookupError，只能在同一 Popen.wait 成功取得退出码后标为 complete；wait 超时或其他错误继续传播为 INCOMPLETE，不再向未知状态的进程发信号。EPERM、无效 PID 和身份不一致继续拒绝，不改权限。TERM/KILL 的原有等待仍为 3 秒，原生每 case 期限仍为 240 秒。

产品代码、argv、业务断言、onboarding、权限及所有其他驱动函数与 native-03 快照一致，见 `driver-scope-04.json`。onboarding 已在 native-03 实际观察到 restricted-key-written、native-ready-observed、entry-paste-written、sent=true，本轮未改这条路径。

时序不变式在 `EXIT-RACE-04.md`。现有 mock 检查增加一个含 9 种退出位置的表，覆盖 native-03 的 TERM-timeout→ESRCH→wait、未退出/已退出/检查后退出/TERM 后退出/身份改变/EPERM，以及 ESRCH 后 wait 无证据。`driver-green-exit-race-04.txt`：10 个检查方法全部通过，包含先前诊断、清理与 onboarding 检查；`exit-race-native03-counterfactual-04.txt`：同一退出表在 native-03 快照上 6 个场景被业务断言拒绝。所有进程操作都是 mock，不代替本轮真实候选证明。

本轮产物：`native-cli-04.json` 与 `native-cli-04-artifacts/`，保留原有 launch、terminal、process.jsonl、清理前/后的原生事件和清理摘要。只有成功 wait 的自有子进程可确认已回收；未知状态保留诊断和相应夹具。native-03 的 `/private/tmp/t265-cli-53i8pydy` 已由主控核对并清理，worker 不操作。

按本轮输入要求，不再创建 issue 或重复排队；主控从最终答复读取命令与此交接文档。README stale 由主控处理。真实候选验证通过后，worker 再补最终报告、Git 提交和显式 submit。
