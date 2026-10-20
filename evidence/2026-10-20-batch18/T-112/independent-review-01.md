STATUS: FAIL
TARGET: /private/tmp/t112-frozen-a0v7hoiy；起点 e3102389eda8952ea92cae4b373e14eaff898314
EVIDENCE:
- 仅审冻结代码、tracked.diff、任务要求和文本证据；未修改文件、调用模型或启动原生 CLI/Electron。
- execution-04.json、mutants-03.json、ipc-final-05.json、t108-final-03.json 和 build-final-02.json 均记录 PASS。其证明范围分别限于 SQLite/Panes 合同、定向变异、模拟边界 IPC、问题合同及构建。
- 默认值及 sentinel 期望来自需求和外部测试输入，未引用生产默认常量充当 oracle。
- 对冻结 run() 函数做内存探针：输入 exit=1、JSON error=worker_executor_mismatch，确实在返回 JSON 前触发 AssertionError。
FINDINGS:
- [P1] workbench/tests/run_t112_native.py:46 — run() 强制所有命令退出码为 0；call() 经它读取 dispatch。真实门禁拒绝由 workbench/src/gates/cli.ts:237 返回 exit=1，因此预期的基线 high 红态必然在此终止，无法到达第 153 行的 EXPECTED_RED 判断，后续候选、Electron 和原生沙箱检查均不执行。应保留完整命令结果，由具体用例分别核对退出码和业务错误。
- [P2] workbench/tests/test_t112_execution.mjs:79 — 启动失败变异通过匹配 shell 源码片段判定，再人工调用退出回调；未证明 shell 实际传播失败。包含相同文本的惰性字符串仍可通过此断言。应以隔离 shell 执行失败子进程，观察退出码和启动失败事件。
COUNTEREXAMPLE:
- 基线合法业务拒绝 exit=1、worker_executor_mismatch：被冻结验收 helper 错当命令失败，已由内存探针复现。
- `native-command; : "if (( a2a_cli_status != 0 )); then exit"; exec /bin/zsh -f -i`：仍会掩盖原命令失败，但第 79 行正则接受，已用纯文本探针确认。
- 已保存的五个变异拒绝结果支持各自有限合同；不能替代真实进程、CLI 解析或沙箱证据。
LIMITATIONS:
- 产品整体仍为 INCOMPLETE；本次 FAIL 针对可达验收脚本缺陷，不代表已复现生产启动故障。
- 原生 CLI、假 API、Electron 保存后派发及原生沙箱边界尚未执行；修前红态仅到公开 Panes.createThread 和真实版本探测。
- 新增检查未经过 dispatch/run 的完整真实入口；待运行脚本也只覆盖 dispatch，没有 run 覆盖参数场景。
- reviewer 原有权限参数、CLI 身份和版本检查静态上保留；实际网络、tmp、原 review worktree 隔离未重证。
- 主控仍使用 Claude；统一 Codex 出厂模型的可用性冲突尚未处置。monitor 没有真实启动入口。
- 本变更适用编排状态、异步事件、身份权限、交互入口、文件及启动运维检查；检索/记忆 N/A。现有 L0/L1 证据不能上调为 L3 边界通过。
RULE:
- 在本地验收检查中加入“exit=1 加预期业务拒绝 JSON”的 helper 用例；启动失败检查观察实际退出和事件，避免把设置失败当红态或把源码字符串当行为证据。
