# T-146-1 / a1

状态：INCOMPLETE。Reflect 同源修复已实现；CLI 自然退出观察层与 T-137 期望冲突仍待裁定，当前不是整票验收通过。

已读取任务卡、公共约定、ticket、项目地图、术语和 intent，以及 Reflect、侧栏、流程、角色申请与后台入口的相关代码。项目地图初检 Problems 0、Stale living docs 0。

## 已完成

- `daemon.ts` 仅改获准的 Reflect 入口：取得一次 `sidebarSnapshot`，将其完整 AgentState 按 launch 传给 Reflect。`reflect.ts` 不再把非 ended 主控或 lifecycle 为 running 的空闲会话推定为运行中；历史已结束角色按角色申请的结束事实保留 ended。`ReflectPage.tsx` 使用后台同一标签表给出的 `state_label`。未改 renderer.tsx、main.ts、流程展示、受保护 oracle 或其它 daemon.ts 区域。
- e2e 经真实后台与角色申请主控派两个真实 Claude Code worker（`claude-haiku-5-5`、本地脚本化 Messages 接口）：一个提交后空闲，另一个保持运行；先验证未知/空闲/运行中，再经真实 `/exit` 关闭前者的 CLI，以 ps/pgrep 独立核对 zsh 仍存活，最后门禁回收与关闭主控终端。每阶段保存三处 DOM 与后台快照；读取前等页面轮询追上 API，解决第一轮结束后侧栏 DOM 尚未刷新的测试竞态。
- 展示断言采用主控 #4 的暂行规则：Reflect 必须保留 ended；侧栏/流程可以 MISSING 或 ended，不能再显示 running/idle。未把缺失值改写成 ended。
- 定向变异 `reflect-lifecycle` 恢复旧的“非 ended 主控为 running、未归档会话为 running”算法，保留新接口，避免接口不匹配造成无关失败。期望红态与变异都在 `reflect_idle` 断言失败。
- 新增自然退出最小探针 `test_t146_cli_exit_probe.py`：真实 Claude 只返回一句话，不调用 Bash；完成真实回合后输入 `/exit`，用于隔离观察层与嵌套 Bash 沙箱失败。此探针不替代 Electron e2e。

## 运行证据

命令：

```sh
python3 workbench/tests/test_t146_session_state_e2e.py --revision ebbae7bd0 --summary evidence/2026-10-23-batch23/T-146/red-attempt-01.json
```

结果：INCOMPLETE，退出 130。真实 CLI 已启动，Write、git add 和 git commit 成功；Bash 等待工具和 submit 工具均失败，错误为 `Exit code 71 / sandbox-exec: sandbox_apply: Operation not permitted`。发现环境失败后中断等待；finally 停止 fixture 后台并保存摘要。此结果不是业务缺陷红态。原始 fixture 保留在 `/private/tmp/t146-92adu2eo`；未将数据库或 trace 加入 Git，后续归档由执行主控处理。

主控运行 `RUN-OUTSIDE-01.sh` 后回传 `outside-20261023T100809Z-50877/`：修前 e2e 退出 1，T-111 与 T-137 均退出 0。修前真实 `01-before-close` DOM 中，同一主控在 Reflect 为 running、侧栏/流程为 unknown；同一 T-done worker 在 Reflect 为 running、侧栏/流程为 idle。该真实差异是本次同源缺陷红态。原测试首先失败于 `sidebar_worker_ended`，其原因混有过严的旧展示断言和未等待侧栏刷新，不能把这个断言本身当成同源缺陷；原始摘要/日志保留，更新测试后须重取具体失败断言。两张原始 Electron 截图已复制为 `baseline-01-before-close.png`、`baseline-02-after-close.png`。

本地修后检查：

- 标准构建 `cd workbench && node app/build.mjs --slot t146-state-20261023-01` 退出 0；只有现有大 bundle 警告，临时构建目录已清理。
- 用 `outside-20261023T100809Z-50877/red.json` 的修前真实 sidebar 输入与 `/private/tmp/t146-3xy5b23t/state/state.sqlite3` 只读重放新 Reflect 投影，得到 unknown/未知、idle/空闲、running/运行中。该检查仅证明新投影，不代替 Electron 绿态。
- `node workbench/tests/test_t111_flow.mjs /private/tmp/t146-t111-same-source-20261023.json .` 退出 0（PASS）。
- 两个新 Python 测试语法、`RUN-OUTSIDE-02.sh` 的 zsh 语法、diff whitespace 检查通过。
- 自然退出探针第一次运行失败于测试自身 `window_open` 漏传 task（`native-exit-red-01.json`），已修正；第二次被沙箱禁止 `/bin/ps`（`native-exit-red-02.json`），不是退出缺陷红态。随后修正探针等待真实模型回合的条件，避免将 SessionStart 的初始 idle 误判为回合结束；未因已知环境限制重跑。保留两次失败记录，外部脚本会跑修正后的版本。

`RUN-OUTSIDE-02.sh` 在新目录分别跑修前、修后、变异、自然退出红绿探针、T-111、T-137；`run-results.json` 只在红态/变异确因 `reflect_idle` 被拒、自然退出修前确因真实 CLI 退出断言被拒、四项绿态均 PASS 时才输出 PASS。环境失败或当前待裁定项导致失败时输出 INCOMPLETE。

提交诊断候选后执行既有流程基线：`node workbench/tests/test_t111_flow.mjs /private/tmp/t146-t111-baseline-c49e7749a.json .`，退出 0，摘要 `{"status":"PASS","task":"T-111","model_calls":0}`。该结果只证明未改产品时的既有流程契约成立，也实证当前 oracle 排除 ended；不替代 T-146 修复后的回归。fixture 清理后 `control.sock`、`daemon.pid` 均不存在。收尾 project-map status 仍为 Problems 0、Stale living docs 0。

## 主控已裁定与后续待裁定

主控 #4 已授权 daemon.ts Reflect 入口最小改动，并采用当前隐藏规则；初次问题 `20261023T100141Z-worker:b23-t146-issue-001` 的这两项已落实。

后续问题 `20261023T101234Z-worker:b23-t146-issue-001`（正文 `followup-issue.md`）：

1. Claude worker 退出退回 zsh 时没有结束事实：`panes.ts` 未注册/处理 SessionEnd，processInfo 还明确排除 Claude 的正常退出判断，status 只看 PTY/归档。建议授权该观察层最小修复；当前未越界改 panes.ts，不能在 Reflect 或侧栏中猜测/制造退出事实。
2. 受保护 T-137 对无 cli/native_session 证据的 E2 写死 running，而侧栏真实为 unknown。需要主控调整该 oracle 的期望或补真实 hook 证据；worker 未改 oracle。
3. 改源代码后 project-map status 为 Problems 0、Stale living docs 1（workbench/README.md）。README 和地图不在允许范围；交由主控在收口/集成时核验与同步，当前不标完成。

更新版 e2e 的修前失败断言、真实 Electron 绿态、变异失败、自然退出红绿态、修后 T-137 与独立行为验收均未完成。未声明 CLI 退出已修好，也不以旧 T-137 的通过替新实现背书。原始 fixture 保留供主控按 T-088 归档，未将数据库/trace 加入 Git。

旧诊断候选 `c49e7749a88356f55e4368aca7e85de10d0d660b` 的只读审查为 INCOMPLETE；该结论不为本次代码变更背书。

本次冻结代码候选 `f5582927bde61a05ed838de20fb156f1fe2ba3f2` 已由新只读会话独立检查，结论 INCOMPLETE：确认上述观察层缺口与 T-137 期望冲突两项 P1，未发现虚报通过。中文转录见 `behavioral-review-02.md`。
