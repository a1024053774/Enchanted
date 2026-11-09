# T-265 原生验证第三轮：受限目录启动时序

INCOMPLETE，等待主控核对最终脚本后外部运行。native-01 与 native-02 的原始证据不变，均不算产品业务红态。第二轮已证明诊断和自有进程清理正常，但父版停在 Folder access，任务尚未投递，候选未开始。

工作目录：`/Users/luckye/Library/Application Support/a2a-orchestrator/worktrees/a2a/T-265-1-a1`。

```sh
/usr/bin/python3 -B workbench/tests/test_t265_review_cli_e2e.py --codex /Users/luckye/.local/bin/codex --node /opt/homebrew/Cellar/node/26.5.0/bin/node --summary /Users/luckye/Documents/Code/a2a/evidence/2026-11-09-batch35/T-265/controller/native-cli-03.json
```

本轮只修改新驱动的 onboarding，采用产品 `openCodexRestricted` 与仓库 `t141_probe_codex_start.py` 已有的时序：去 ANSI/空白，观察最后显示选中 `›1.Openrestricted`，等待终端输出安静 800ms（从观察选择起最多 5 秒），只排入一次 CR；`Trust and continue` 不作等价动作。完整 native ready 包 `OSC 7501;state=idle:app=codex` 到达后才投递任务。没有重复 Enter、额外权限、替代 CLI 或更长等待期限。

阶段按事实区分：`restricted-choice-observed` 是看见选择；`restricted-key-queued` 只是排队；`restricted-key-written` 是 CR 已实际写入 PTY；`native-ready-observed` 是收到完整原生 ready 包；`entry-paste-written` 是粘贴字节全部写出；`task-submitted` 是末尾提交 CR 实际写出。`sent=true` 只在最后一步赋值，不意味着原生已开始回合；native_started/native_completed 仍分别取真实原生事件。旧 `opened_restricted=true` 已删除，不再把排键解释为成功打开。

创建、诊断、清理和留证沿用 native-02 修正；每 case 最长 240 秒。父版/候选业务断言、原生 argv、无 hook/无 MCP、只读材料与目录信任级别均不变。`driver-scope-03.json` 核对产品字节、argv、业务断言、stop_owned 和 main（含等待期限）均与 native-02 快照一致。

复用原诊断检查文件，只增加一个受限目录时序用例：`driver-green-onboarding-03.txt` 为 9/9 通过，包含原有 8 项诊断/清理检查；同一时序用例在 native-02 冻结脚本上失败，见 `onboarding-native02-counterfactual-03.txt`。这是模拟 PTY 的离线行为反事实，不替代真实 CLI 证明，也未创建新测试框架。

产物在 `native-cli-03.json` 和 `native-cli-03-artifacts/`：launch、增量 terminal、process.jsonl、清理前原生事件、最终 process/native-events、目录清理前摘要。发生启动或业务问题保留诊断；未确认退出不删除对应夹具，已确认退出才删除该隔离 CODEX_HOME。native-02 的 `/private/tmp/t265-cli-9i6crfet` 剩余缓存由主控按答复 #130 记录并清理，worker 不操作。

主控回传本轮 summary/artifacts 路径与结论后，worker 再补最终 RESULTS、Git 提交和 submit。README stale 继续由主控集成时处理，不作为本轮等待条件。
