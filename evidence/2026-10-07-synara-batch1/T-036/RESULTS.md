# T-036 交付记录（2026-10-07）

**INCOMPLETE，仅余针对性独立复核与收尾；待主控关闭。** 主控 Claude Code（`wF:pM`）；执行 worker 为主控启动的 `s1-t036`（`wF:pX`）。fork 修正候选为 `26cb210a99fc74a43ef341278c6ef4e19ab0565e`（[绑定记录](corrected-candidate.json)），基线 `7cb0ac0a3d5232e90ab2db1fb7eb9ee696d1af73`，未 push。该候选现已经批准的同一副本入口证明交付 8/8、恢复 9/9、两个业务反例。全仓失败与旧候选异常继续保留。

## 四项验收

| 条件 | 结论 | 命令与证据 |
| --- | --- | --- |
| 交付 8 项与先验红态 | PASS | `python3 -B evidence/2026-10-07-synara-batch1/T-036/run-acceptance.py corrected-candidate-delivery test_coop_e2e.py`；修正候选 8/8。原 CLI 对 `--state … create` 返回 exit 2：[契约红态](red-delivery-entry-fixed/command.json)、[修正候选绿态](corrected-candidate-delivery/command.json)、各自 `trace.json` |
| 恢复 9 项 | PASS | 批准副本单独 9/9：[结果](native-recovery-green/command.json)；同一组合入口交付 8+恢复 9 共 17/17：[结果](native-combined-green/command.json)、[完整 trace](native-combined-green/trace.json)。该轮针对冻结修正候选，真实 SIGKILL 只向各夹具创建并核对的 CLI PID 发出 |
| fence 与 Git 回读 mutant | PASS（反例被抓住） | 同一组合入口：错 fence 在 `0 != 1` 业务断言失败：[结果](mutant-fence-corrected-native-suite/command.json)；忽略回读在 CAS 前恢复、外部 X、引用删除 3 个恢复场景为 BUSINESS_RED：[结果](mutant-readback-corrected-native-suite/command.json)、[业务断言](mutant-readback-corrected-native-suite/trace.json)。无 setup/import/夹具错误充数。完整错误实现与 diff 在 [mutants](mutants/) |
| CLI 差异记录、不改预期 | PASS（记录） | 下表记录原生运行差异；未修改 `acceptance/test_coop_e2e.py`、`acceptance/test_recovery_e2e.py` 或 oracle。只新增薄转接脚本，原样转交参数 |

## CLI 与运行时差异

| 项目 | 原因与影响 | 处理建议 / 状态 |
| --- | --- | --- |
| 中断前的入口身份核对 | `test_recovery_e2e.py:201` 要求 `ps` 含 Python 的 `COOP_SCRIPT` 路径。`os.execv` 保持 PID，但最终进程为 `bun …/cli.ts --state … COMMAND --task …`。原夹具拒绝且没有信号：[原记录](candidate-recovery-01/command.json) | 主控在 `controller-decision-01.md` 明确批准证据副本。[完整 diff](native-acceptance/complete.diff) 只有入口路径参数化的两行，仍检查活跃 Popen PID、原生 CLI 路径、state/task 和信号结果。原文件和业务断言未改。独立复核须逐行确认 |
| 原生 thread 的 submit | `dispatch` 的 attempt 仍核对 MCP caller、thread、turn、worktree 与运行状态；运行时无关的 `claim` 没有 thread，CLI 只接受其已分配 attempt/session/fence/spec | 对应冻结的本地受管合同；没有把原生 attempt 降级为 CLI 身份。T-036 未调用模型、未运行原生 thread 闭环 |
| 传输与状态输入 | 新 CLI 接受冻结的 `--state ABS_DIR COMMAND …`；已有 URL+JSON 形式保留为原生生命周期的 HTTP 传输。两者汇入同一核心。核心 DB 仍为 `state.sqlite3`，旧事件表只增加 attempt 列 | 不新增业务状态入口；本次对上游既有接入点的改动只有 `packages/contracts/src/a2aGates.ts`，扩展命令、记录与结果类型 |
| 路径及数字边界 | 本地 CLI 的 state 需绝对路径。整数解析限制为 JS safe integer；非法语法返回 2；业务拒绝返回 1 且 `ok=false,error`。HTTP 请求沿用 schema 校验 | 未声称 argparse 的所有帮助、巨大整数和错误文案逐字一致；冻结套件使用的合法输入、业务代码与退出码已验证 |

## 实现与证据边界

目标是以一个 Deep modules 核心隐藏存储、锁、Git 与 oracle；Ubiquitous language 沿用 task、attempt、session_id、fence、spec_rev。Tracer bullet 是 Python 转接 → TypeScript CLI → 同一门禁核心 → SQLite/Git/oracle。没有新增运行依赖。

核心补齐 create 的冻结副本、独立 claim、submit 校验、revoke/revise、验证记录表、中断状态保留、新 detached worktree 与合并候选、验收超时、原集成意图的 CAS/读回恢复、操作锁、status/events。状态变更只在 `packages/a2a-gates/src/core.ts`。fork 的文件清单与规格绑定见 [frozen-candidate.json](frozen-candidate.json)。未改 server、web 或运行时选择；新原生会话、完整 run 编排与 M1 切换不在此验收结论内。

`command.json` 保存确切 argv、环境选择、完整 stdout/stderr、退出码与临时现场路径；`trace.json` 来自原验收脚本，包含每个 CLI/Git 命令、task 和 attempt 身份、原始输出。主控启动配置来自批次 `launch-argv.txt`，请求 `gpt-6.1-sol`、xhigh、fast，不把配置当供应商实际 tier。未取得本 worker 的受管 attempt/fence，不编造身份。

首次转接路径错误保存在 `red-delivery/`、`red-recovery/`，只计夹具失败；修正后才取得契约红态。首轮 candidate 的较大 events JSON 被 Bun 管道输出截断，保存在 `candidate-delivery-01/`；CLI 等待输出回调完成后同套件转绿，见 `candidate-delivery-02/` 与最终 `frozen-delivery/`。反例首次从临时目录无法解析 workspace package 的记录原样保留；改用 package 的实际依赖目录后，fence 反例才取得业务红态。

## 检查与交接

| 检查 | 结论 | 证据 |
| --- | --- | --- |
| `run typecheck` | PASS | [final-typecheck.log](final-typecheck.log) |
| `run lint` | PASS | [final-lint.log](final-lint.log) |
| `run windows-runtime:check`、`run migrations:check` | PASS；不代表 Windows 运行验收 | [进程边界](final-windows-runtime.log)、[迁移检查](final-migrations.log) |
| `run fmt:check` | NO_GO；仅报告范围外原有 `.grok/settings.json` | [final-fmt-check.log](final-fmt-check.log)；没有改该文件 |
| `run test` | NO_GO；scripts 三项 5 秒超时，其他 workspace 被 Turbo 中止 | [final-workspace-test.log](final-workspace-test.log)。三个失败文件的单独复核 PASS：[affected-scripts-retest.log](affected-scripts-retest.log)，不替代全仓失败 |
| 独立审查 | 首次 FAIL，已修复其 P1；修复范围的针对性复核尚未完成 | [首次报告](acceptance-review-first.md)，审查者另外重跑原交付套件 8/8；修正候选不借用首次结论 |
| 串行入口的全仓复核 | NO_GO；scripts 4 项超时，其他 workspace 被中止 | [final-workspace-test-serial.log](final-workspace-test-serial.log)。原失败未覆盖；随后修正候选还需最后一轮范围内检查 |

## 独立审查发现的历史回收缺陷

首次审查冻结 `5cae1072d` 后发现 P1：`revoke A → claim B → reclaim --attempt A` 对尚未回收的历史 A 返回 `stale_attempt`。该问题属 T-036 的冻结契约。先运行 `…/run-fork-check.py history-contract-idle-red run --cwd packages/a2a-gates test`，[红态](history-contract-idle-red.log) 明确在合法历史回收应成功的业务断言上失败；未修复实现前保存。

修复仍走同一个受锁 reclaim 路径：选择指定历史记录并核对其绑定，业务 task 只在 current_attempt 匹配时改变；历史重放、外来 task 和仍工作执行者继续受保护。事件绑定实际回收的 attempt。`26cb210a9` 的 [针对性检查](corrected-candidate-core-test.log) 通过，原交付套件与同版本 fence mutant 也重新运行。检查使用真实 Git/SQLite 和受控 thread 替身，只证明所有权作用域，不称为真实原生会话验收。该新测试此前对错误候选失败；未从实现输出提取预期。

## 批准副本的复现与红态

主控决定原样留在本目录 `controller-decision-01.md`，由主控自己提交；worker 的提交不包含该文件。只复制恢复脚本，其 helper 仍是原 `acceptance/test_coop_e2e.py`。`native-suite.py` 只选取原交付 8 项和恢复副本 9 项，不增删场景、预期或断言。确切环境与 argv 见每轮 `command.json`，基本命令为：

```sh
PYTHONPATH=/Users/luckye/Documents/Code/a2a/acceptance COOP_NATIVE_ENTRY=/Users/luckye/Documents/Code/synara/packages/a2a-gates/src/cli.ts python3 -B evidence/2026-10-07-synara-batch1/T-036/run-acceptance.py UNIQUE_LABEL /Users/luckye/Documents/Code/a2a/evidence/2026-10-07-synara-batch1/T-036/native-acceptance/native-suite.py
PYTHONPATH=/Users/luckye/Documents/Code/a2a/acceptance python3 -B evidence/2026-10-07-synara-batch1/T-036/run-mutant.py fence-corrected /Users/luckye/Documents/Code/a2a/evidence/2026-10-07-synara-batch1/T-036/native-acceptance/native-suite.py UNIQUE_SUFFIX
PYTHONPATH=/Users/luckye/Documents/Code/a2a/acceptance python3 -B evidence/2026-10-07-synara-batch1/T-036/run-mutant.py readback-corrected /Users/luckye/Documents/Code/a2a/evidence/2026-10-07-synara-batch1/T-036/native-acceptance/native-suite.py UNIQUE_SUFFIX
```

实现前的原脚本红态已经保留。授权后，同一副本组合入口又对 `7cb0ac0` 的缺失 CLI 取到 [反事实红态](mutant-baseline-native-suite/command.json)，不是补称为实现前运行。副本的独立 9 项绿态、完整 17 项绿态、两个 mutant 均保留，信号、SQLite/Git 快照与业务断言未丢弃。原文件在转接入口下拒绝注入的结果不是产品恢复失败，也不算恢复通过。

未触碰用户 Herdr、用户配置或 Synara 数据；未 push、未执行真实产品模型调用、未删除现场。原验收自身释放了本次创建的屏障和 CLI；临时仓库、worktree 和失败记录保留，归档不登记 gitlink。针对性独立复核结束后只补记报告，不再改冻结代码。
