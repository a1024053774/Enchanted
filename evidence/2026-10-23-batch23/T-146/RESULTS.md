# T-146-1 / a1

状态：INCOMPLETE，等待主控在沙箱外验收。Reflect 同源、Claude SessionEnd 结束事实和 T-137 夹具输入已按主控 #5 补齐；本地针对性检查通过，尚无新候选的完整 Electron 绿态与变异结果。

已读取任务卡、公共约定、ticket、项目地图、术语和 intent，以及 Reflect、侧栏、流程、角色申请与后台入口的相关代码。项目地图初检 Problems 0、Stale living docs 0。

## 已完成

- `daemon.ts` 仅改获准的 Reflect 入口：取得一次 `sidebarSnapshot`，将其完整 AgentState 按 launch 传给 Reflect。`reflect.ts` 不再把非 ended 主控或 lifecycle 为 running 的空闲会话推定为运行中；历史已结束角色按角色申请的结束事实保留 ended。`ReflectPage.tsx` 使用后台同一标签表给出的 `state_label`。未改 renderer.tsx、main.ts、流程展示、验收断言或其它 daemon.ts 区域。
- e2e 经真实后台与角色申请主控派两个真实 Claude Code worker（`claude-haiku-5-5`、本地脚本化 Messages 接口）：一个提交后空闲，另一个保持运行；先验证未知/空闲/运行中，再经真实 `/exit` 关闭前者的 CLI，以 ps/pgrep 独立核对 zsh 仍存活，最后门禁回收与关闭主控终端。每阶段保存三处 DOM 与后台快照；读取前等页面轮询追上 API，解决第一轮结束后侧栏 DOM 尚未刷新的测试竞态。
- 展示断言采用主控 #4 的暂行规则：Reflect 必须保留 ended；侧栏/流程可以 MISSING 或 ended，不能再显示 running/idle。未把缺失值改写成 ended。
- 定向变异 `reflect-lifecycle` 恢复旧的“非 ended 主控为 running、未归档会话为 running”算法，保留新接口，避免接口不匹配造成无关失败。期望红态与变异都在 `reflect_idle` 断言失败。
- 新增自然退出最小探针 `test_t146_cli_exit_probe.py`：真实 Claude 只返回一句话，不调用 Bash；完成真实回合后输入 `/exit`，用于隔离观察层与嵌套 Bash 沙箱失败。此探针不替代 Electron e2e。
- `panes.ts`：Claude 已有钩子列表只新增 SessionEnd 一项；在回合级校验之前按会话级字段核对它，保存既有 `native_session_ended` 事件并设置已有 `nativeEnded`；`status()` 消费该事实返回 ended。没有修改其它启动参数、恢复或权限逻辑。Codex 已有 `native_session_ended/nativeEnded` 事实沿用同一 status 判断；本次真实 CLI 验收范围为 Claude，未新增 Codex 真实退出证据。
- `test_t137_reflect_e2e.py` 仅改 `ask()` 的夹具输入：第 123 行产生本轮脚本化原生会话号，第 126～127 行经角色申请上报 `cli='claude'`、native_session、native_home；第 139～145 行经现有 terminal_hook 通道提交关联的 UserPromptSubmit 并保存输入证据。原夹具只有存活 shell，没有 CLI 回合证据；现在 E2 的 running 预期有同一原生会话关联的脚本化输入支撑。没有直接写数据库/状态，没有改 `:243`（原 `:234`）的 E2 running 断言、检查名或期望值。共享 `scripted_claude.py` 未修改。

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

主控 #5 之后新增的本地证据：

- `node workbench/tests/test_t146_session_end.mjs .../session-end-contract-red-03.json .`：退出 1，前五项通过后准确失败于 `claude_prompt_id_required`。这是会话级钩子契约红态，不冒称真实 CLI 退出红态。更早 red-01 缺 attempt、red-02 缺 turn_limit 是测试夹具错误，均保留但不算产品红态。
- 同一测试修后 `session-end-contract-green-02.json`：PASS，八项检查覆盖外来 session/cwd/transcript、子 agent、畸形 agent、缺 reason 的拒绝，以及 Stop 仍为空闲、无 prompt_id 的 SessionEnd 使状态 ended 而终端未关闭。
- `session-end-contract-counterfactual-01.json`：对保留的 ebbae7bd0 运行时代码再次执行，退出 1，同样因 `claude_prompt_id_required` 拒绝正确 SessionEnd。
- `python3 evidence/2026-10-23-batch23/T-146/CHECK-T137-FIXTURE.py evidence/2026-10-23-batch23/T-146/t137-fixture-channel-01.json`：PASS。直接从修改后的测试提取并执行同一个 ask()，经过真实后台角色申请/确认/钩子入口，侧栏与 Reflect 同为 running。控制角色输入是脚本化的，不宣称该局部检查启动了真实主控 CLI 或经过 Electron。
- `t137-oracle-preservation-01.json`：原有 10 个 check() 调用（含检查名、断言表达式与期望值）与 ebbae7bd0 完全一致；只新增夹具通道成功校验。
- `t111-session-end-01.json`：既有 T-111 PASS。
- 额外已有检查未全部通过：T-078 夹具缺 transcript 文件；T-108 的 Codex 矩阵有 171/429 项失败。对 ebbae7bd0 运行时代码的基线复跑重现同样问题，T-108 全部 429 项名称/状态逐项一致。不是本变更的通过证据，也未顺手改旧测试或 Codex 行为。已上报 `20261023T102949Z-worker:b23-t146-issue-001`，详见 `existing-regression-issue.md` 和相应 JSON。

请运行新的 `RUN-OUTSIDE-03.sh`：除 02 的真实 Electron 红绿态、reflect-lifecycle 变异、真实 Claude 退出红绿态与 T-111/T-137 外，增加会话级 SessionEnd 校验。每次输出写入全新 outside03-时间-PID 目录；只有两种具体缺陷红态被拒、其余五项均 PASS 才输出 PASS。02 保留作日期记录，不覆盖其脚本或既有运行结果。

提交诊断候选后执行既有流程基线：`node workbench/tests/test_t111_flow.mjs /private/tmp/t146-t111-baseline-c49e7749a.json .`，退出 0，摘要 `{"status":"PASS","task":"T-111","model_calls":0}`。该结果只证明未改产品时的既有流程契约成立，也实证当前 oracle 排除 ended；不替代 T-146 修复后的回归。fixture 清理后 `control.sock`、`daemon.pid` 均不存在。收尾 project-map status 仍为 Problems 0、Stale living docs 0。

## 主控已裁定与后续待裁定

主控 #4 已授权 daemon.ts Reflect 入口最小改动，并采用当前隐藏规则；初次问题 `20261023T100141Z-worker:b23-t146-issue-001` 的这两项已落实。

后续问题 `20261023T101234Z-worker:b23-t146-issue-001`（正文 `followup-issue.md`）已收到主控 #5 的明确处置：

1. 主控原话：“允许改 workbench/src/panes.ts 中“CLI 结束事实”这一处——Claude 的 SessionEnd 钩子注册、signal() 接收它、status() 据此返回 ended”。已在这一范围实施；恢复、权限与其它启动参数未动。
2. 主控原话：“不改 test_t137_reflect_e2e.py:234 的断言”，“允许改 T-137 测试的夹具部分”。已按上述行号补脚本化 CLI 与关联钩子输入，原验收断言未改；该例外由主控修订任务卡，worker 未自行更改任务卡或 oracle_paths。
3. 改源代码后 project-map status 为 Problems 0、Stale living docs 1（workbench/README.md）。README 和地图不在允许范围；交由主控在收口/集成时核验与同步，当前不标完成。

更新版 e2e 的修前失败断言、真实 Electron 绿态、变异失败、真实 CLI 退出红绿态、完整 T-137 回归与新候选独立行为验收仍待外部执行。不会将局部 signal/夹具检查或旧 T-137 的通过升级为整票通过。官方 SessionEnd 字段依据为 [Claude 官方钩子文档](https://code.claude.com/docs/en/hooks#sessionend)；会话级事件没有必填 prompt_id。原始 fixture 保留供主控按 T-088 归档，未将数据库/trace 加入 Git。

旧诊断候选 `c49e7749a88356f55e4368aca7e85de10d0d660b` 的只读审查为 INCOMPLETE；该结论不为本次代码变更背书。

本次冻结代码候选 `f5582927bde61a05ed838de20fb156f1fe2ba3f2` 已由新只读会话独立检查，结论 INCOMPLETE：确认上述观察层缺口与 T-137 期望冲突两项 P1，未发现虚报通过。中文转录见 `behavioral-review-02.md`。

补齐后的冻结候选 `5792d5ae6fbfa1edf67e22f8d721d6461d1d8426` 另经新只读会话审查，结论仍为 INCOMPLETE：本地状态合约通过，真实 Claude SessionEnd→后台→三页与 zsh 存活的证据仍待 RUN-OUTSIDE-03。审查保留这一 P1 证据缺口，未宣称产品已通过；转录与被测路径/期望值的区分见 `behavioral-review-03.md`。
