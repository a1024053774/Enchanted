# T-197 独立只读审查

STATUS: INCOMPLETE

日期：2026-10-27。审查目标为 `/Users/luckye/Documents/Code/a2a` 的未提交 T-197 候选，基线 HEAD 为 `bb447be5010a825ffa36dfe56b714682037a520c`，候选补丁为本目录 `change.diff`。本轮不批准合并；原因是审查期间候选变化，另有完整入口复跑被当前沙箱环境阻断。尚未确认 T-197 的业务实现缺陷。

## FINDINGS

### F01 [P2，审查证据阻断] 同一 HEAD 下的候选在审查期间改变

- 位置：`workbench/src/gates/core.ts:3996`（后续观察快照中新出现的 `out_of_card` 分支）；同次观察还发现 `taskHistory.ts`、`terminalCli.ts`、README、SKILL.md 的候选内容变化。
- 失败场景：开始时，六个目标文件的工作区 diff 与 `change.diff` 逐字节相同。07:22:41 保存的 `candidate-start.diff` 与 07:26:08 保存的 `candidate-observed.diff` 已不相同，HEAD 却未变化。后者加入了 T-198 的卡外文件判断、集成门禁及说明。这意味着继续从工作区读取代码、运行测试，可能把不同候选的代码和证据拼在一起，不能形成冻结候选的独立验收结论。
- 证据：`candidate-start.diff`、`candidate-observed.diff`、`candidate-drift.diff`。比较使用原始字节，没有计算摘要或指纹。
- 建议：交付与补丁一致且在审查期间不再修改的完整源码快照，并让测试记录明确绑定该快照，然后重新发起独立审查。可以继续开发其他候选，但不要改动供审查使用的源码目录。本条要求修复的是候选与证据的绑定，不要求撤销 T-198，也不是对 T-198 实现的审查结论。
- 停止依据：[behavioral-acceptance-review/SKILL.md](/Users/luckye/.agents/skills/behavioral-acceptance-review/SKILL.md) 明确要求：“If the branch, candidate, or diff changes, return `INCOMPLETE`; do not chase a moving target.” 本轮已观察到 diff 改变，故停止追审活动工作区，只整理已有事实与报告。

## 已完成的核对

以下是停止前取得的局部事实，不能作为变化后候选的 PASS。

1. **路径占用逻辑**：起始补丁的 `core.ts:1286` 先校验理由，`core.ts:1304` 只将 `accepted` 的重叠 attempt 放进 `not_counted`，其他未释放的重叠仍进入 `conflicts`，并在拒绝结果中返回任务、attempt、路径及操作提示。事件同时保存理由和 `passed`。空字符串、普通空白与全角空白会被 `text()` 拒绝为 `invalid_text`。
2. **状态语义**：已读集成、交付、返工和撤销的直接路径。`accepted` 只在工作分支推进成功且内容核对通过，或恢复时确认已完成集成后设置；正常路径不存在“集成失败却已经 accepted”。`integration_conflict` 是事件，不是 attempt 状态；失败时 attempt 仍为未接受状态，继续占用路径。`rework`、`submitted`、已机械验收但未集成的 attempt 也继续占用。已回收、工作区已移除，以及没有线程的 revoked attempt 沿用原有释放规则；带旧线程的 revoked attempt 仍占用。未发现该新增 accepted 例外会直接放开两个尚在执行的 attempt。
3. **任务页投影**：起始补丁的 `taskHistory.ts:31` 有冲突时展示“路径重叠”、任务和路径；放行时展示原理由及通过状态。无冲突时返回空，包括只有 `not_counted` 的检查。读取了 `task_history` 后端和 `TaskRecord.tsx` 的消费路径；没有完成 Electron 界面的实机显示检查。
4. **说明一致性**：起始补丁的 SKILL.md、`a2a help` 和 README 均描述跨任务重叠由执行主控判断、带理由放行及 accepted 不占路径。原有“不传 overlap_reason”位于同一任务改卡、撤销旧 attempt、回收后重派的流程；结合上下文，未确认它与跨任务放行规则直接矛盾。角色卡中未找到额外禁止跨任务重叠放行的条款。候选漂移后未继续审查新说明。

## EVIDENCE：检查、命令与结果

### 已提供的证据

- `evidence/red-head.json`：记录在 `accepted_attempt_holds_no_paths` 上因 `path_overlap` 失败，符合修前缺陷。文件自身的状态为 `INCOMPLETE`，不能称整套测试通过；`revision` 为 null，未独立证明它绑定的完整修前源码版本。
- `evidence/green.json`：记录 PASS，共 15 项检查，含 accepted 未回收后认领成功、`not_counted`、进行中重叠拒绝清单、空白理由拒绝和理由入事件。测试经真实后台/socket/原生 CLI，模型接口为脚本化假服务；没有真实模型回合。
- `evidence/mutant.json`：`accepted-still-counted` 变异在同一个业务断言 `accepted_attempt_holds_no_paths` 失败，错误为重叠拒绝，属于有效反例，不是依赖缺失或测试崩溃。
- `evidence/green-01-test-keyerror.json`：保留了 `KeyError: 'task'`，这是测试自身故障。当前测试第 436 行读取 `status` 的 `task.current_attempt`，与接口形状一致；后续 green 已通过对应断言。该异常记录不能替代行为红态。
- `evidence/history_check.ts` 与输出：使用 green 场景的真实事件检查一次无理由拒绝、一次带理由放行，输出两条“路径重叠”且理由正确。原脚本只过滤重叠步骤，单靠它不能证明干净检查没有产生其他噪音；本轮另做了空冲突输入检查。

### 本轮检查

在 `/private/tmp/t197-review1` 执行，所有新增产物均保存在本目录：

```sh
python3 /Users/luckye/.agents/skills/project-map/scripts/project_map.py status --root /Users/luckye/Documents/Code/a2a
node independent-check.ts > independent-check.json 2> independent-check.stderr.log
python3 rerun.py > rerun-green.log 2>&1
```

- 地图状态：开始和结束均为 Problems 0、Stale living docs 0，命令退出 0；输出分别保存为 `project-map-start.txt`、`project-map-end.txt`。这不代表所有说明已经人工验收通过。
- `independent-check.ts`：退出 0，输出 PASS，覆盖 19 个状态/路径/理由场景及 5 个历史展示场景。使用独立指定的未创建路径、不同任务名、多个冲突任务和新的中文理由，预期来自 ticket 和既有回收契约，不从实现结果生成。它直接调用路径检查及历史投影，使用真实 Git/SQLite，属于隔离逻辑证据，不是完整入口验收。由于载入的是活动工作区源码，且后来确认候选漂移，结果不能绑定为起始快照的最终通过证据。
- `rerun.py`：不改仓库测试代码，以 `runpy` 运行 `workbench/tests/test_t131_parallel_workers_e2e.py`，仅把 Python 临时目录和 `TMPDIR` 指向本目录 `runtime/`。退出 1；`rerun-green.json` 状态为 INCOMPLETE，只通过启动两名 worker、无理由重叠拒绝、两名 worker 同时运行这 4 项，随后等待 T-1 交付超时。两名 worker 的 submit 工具结果均为退出 71：`sandbox-exec: sandbox_apply: Operation not permitted`。因此未到本次 T-197 的新增断言，不能把超时归因于 T-197，也不能把本轮称为绿态复跑。完整日志、JSON 和隔离现场均保留；测试 finally 已停止隔离后台，`daemon.pid` 已移除。
- 候选核对：使用 `git rev-parse HEAD`、`git status --short`，以及 `git diff --` 限定到 `change.diff` 涉及的六个文件。Python `subprocess.check_output` 保存起始和观察 diff，并用字节相等比较确认漂移；`diff -u candidate-start.diff candidate-observed.diff > candidate-drift.diff` 返回 1，表示存在差异。

上述重跑脚本会拒绝覆盖已有结果；复验应使用新结果路径/新的审查目录，保留本次失败现场。

## COUNTEREXAMPLE

- 已提供的“accepted 继续占路径”变异被业务断言拒绝；可以支撑这项特定回归检查具备检错能力。
- 本轮新增空理由、Unicode 空白、不同路径、多冲突任务和干净事件输入检查，均得到预期结果。未进行额外源码变异；未证明所有可能的坏实现都会失败。

## LIMITATIONS

- 总体结论因冻结候选失效而为 INCOMPLETE；未追审 T-198，也未更改仓库、测试、分支、提交或既有证据。
- 原有 green、red、mutant 的完整源码版本绑定不足以在候选漂移后自动延续验收结论。本轮未重新成功取得完整入口的绿态。
- 本轮未动态制造真实集成失败/崩溃恢复，也未验证 Electron 渲染与真实模型理解。集成失败仍占用的判断来自已读状态转换和隔离状态输入；不外推为恢复流程全部通过。
- 审查范围限于 T-197 及其直接调用、状态语义、展示和证据。检索时不存在的候选文件路径已改从真实模块位置读取，不据此作产品缺陷判断。
- 后续需要的是冻结快照上的独立重审及可运行环境中的入口复验；目前没有已确认、可直接交付实现者修补的 T-197 业务代码问题。

结论：需修复
