# T-037 交付记录（2026-10-08）

**PASS（仅限 T-037 五项与主控补充的记录故障处理），待主控关闭。全仓测试与全仓 fmt 为 NO_GO；M1 为 INCOMPLETE。** 候选 `fa3fc3352805d00e41c454fa6f810807528de3a9`，基线 `a9cc30c395af9ffd51476a1841d80bca66568993`。只提交本 ticket 归属文件，未 push。T-038 的工作保留在它的 worktree；a2a ticket 保持 open。

## 验收与边界

| 条件 | 当前结论与证据 |
| --- | --- |
| 原 18 项移植 | PASS，18/18，当前候选结果见 `final-run-03/`；冻结前原 CLI 缺失 run 的红态见 `run-contract-red/` 与 `missing-run-direct-red.json`。原验收文件未改 |
| done 无 submit 反例 | PASS（业务反例被抓住），同候选错误实现见 `mutant-done-final-03/` 与 `mutants/mutant-done-final-03/`；须以没有 submit 而实际 oracle/集成/accepted 的业务断言判红，不能只看 exit 1 |
| 忽略 expected attempt 反例 | PASS（业务反例被抓住），同候选见 `mutant-attempt-final-03/`；须核对过期 guard 的实际状态、oracle、Git 引用/reflog改变 |
| 交付 8 项、恢复 9 项 | PASS，17/17，沿 T-036 的相同组合副本入口；当前候选见 `final-delivery-recovery-03/`。原 helper、oracle 和恢复业务预期不改，PID 核对保留 T-036 批准的原生 CLI 路径 |
| 人工介入 | `human-input-final-03.log`、`native-service-final-03.log`：真实 decider/engine、client schema、服务订阅与门禁事件；用户输入绑定原 attempt，agent/automation/assistant/非受管输入排除，回放去重 |
| 18 项差异与时间输入 | [逐项说明](acceptance-differences.md)、[完整 diff](run-boundary-copy.diff)、[实测](timing-observations.json)。仅第 8/10 项输入预算和外部屏障调整，经主控决定 02 批准；2 秒 deadline 与 3 秒 busy 拒绝预期保持 |

核心使用同一受锁 request 路径编排 dispatch → 显式 submit → verify → integrate → reclaim。run 有独立的 OS 释放锁，只绑定其创建的 attempt/thread；verify/integrate/reclaim 都带原 attempt。dispatch 的 detached worktree 从当时的权威集成头创建；Synara 原生 thread 的模型为 Codex `gpt-6.1-sol`，请求 xhigh/fastMode，环境与 runtimeMode 明确。实际 provider session 的 cwd/provider/turn、thread shell 和 attempt 共同核对；归档前后核对停止、归档及原身份。自然语言完成、空闲或 done 不交付。

状态变更仍由一个 Deep modules 核心负责。Tracer bullet 为生产 CLI 解析 → 同一核心 → 受控 thread 服务 → 真实 SQLite/Git/独立分页 oracle → 归属回收。Ubiquitous language 沿用 task、attempt、session_id、fence、spec_rev。无新运行依赖；不改 T-036 导出与原字段，不保留第二套编排。

## 主控审阅中的人工记录故障

主控问题与答复见 [审阅记录](controller-note-01.md)、[答复](observer-failure-resolution.md)，批准范围见 [决定 03](controller-decision-03.md)。该故障可由有效用户输入触达：真实 SQLite 写锁导致记录失败，旧候选的 fiber 结束，只有日志知道，后续 create 仍成功。[修复前红态](observer-failure-red.log)完整保留。

新候选由核心保存服务实例内的订阅状态；`status`、`events`、既有门禁 GET 继续读取并显示 failed、源事件和原因。全部 10 个改变状态的命令拒绝，专用错误为 `human_input_observer_failed`。逐命令分类、reclaim 拒绝理由和接口见 [observer-status.md](observer-status.md)。GET 改动限主控分配的那几行；membership/OPTIONS 未碰。

[完整故障探针](observer-failure-check.ts)经真实 engine、SQLite 写锁与实际 loopback GET，检查全部变更命令、原 task/attempt/事件前缀不变及两条遗漏消息的回放；当前候选原始结果为 `observer-failure-final-03.log`。状态不是落盘的成功证据：写入故障也可能阻止最终 run 收据；保留旧持久阶段并返回非完成。修存储后新服务实例先回放，不能由旧实例自行重置 failed。不自动重试或跳过消息。

给正在运行的 oracle 注入已知记录失败时，结果回调还曾抛错并悬空请求；[红态](inflight-observer-red.log)与[夹具 PID 终止](inflight-red-termination.json)保留。回调现在 reject 原错误，由统一出口保留失败状态；当前候选见 `inflight-observer-final-03.log`，旧验证阶段保留供原恢复入口核对。

## 其他保留的失败与修复

- 受管 provider cwd 与 thread worktree 不符仍发出 stop：`native-provider-cwd-red-valid-input.log` 记录实际 stop 请求；改为实际 provider 身份核对后，同信号转绿。
- 原生 Refusal 被改为未知并丢原观察：`runtime-refusal-red.log`；保留原错误码/细节后，同信号转绿。
- 首次证据转接的 Effect 路径、client schema 名称、原生模型 instanceId 比较和 unmanaged create 字段错误，均保留。它们属于夹具问题，不计业务红态。
- 首轮核心测试 30 秒超时与原 8/12 秒夹具预算失败保留。没有提高核心测试超时或 5 秒 prompt 观察窗口；后续顺序执行取得通过才计入证据。
- 旧候选 `a493421` 的全仓检查被本次修复取代。只对本 ticket 已启动的 Turbo 发出 SIGINT，保留清单与身份核对。其 exit 0 但报告 **0/7 successful**，为 INCOMPLETE，不算全仓通过；不能给新候选背书。

## 验证与版本绑定

当前候选阶段记录追加于 `final-verification-03.jsonl`。每个 `command.json` / 检查 JSON 保存精确 argv、cwd、环境、输出、退出码；验收 trace 保留实际 task/attempt/fence、Git/SQLite回读、信号与外部边界原始请求/响应。源码、原规范、原验收、转接器按 [冻结清单](frozen-candidate-03.json)绑定。主控持续写的 controller-poll.log、launch-argv.txt、panes.txt、T-038 文件和原有 .grok 不在冻结源码声明内。

| 检查 | 结论与证据 |
| --- | --- |
| 最终核心测试 | PASS，`final-core-test-03.log`；此前 30 秒超时保留 |
| 最终 lint / typecheck | PASS，`final-lint-03.log`、`final-typecheck-03.log` |
| Windows 静态边界 / 迁移检查 | PASS，`final-windows-runtime-03.log`、`final-migrations-03.log`；不证明 Windows 运行 |
| 全仓 fmt | NO_GO，仅原有 `.grok/settings.json`；`final-fmt-check-03.log`。归属外不修复，自己的格式检查通过 |
| 全仓 test，顺序执行 | NO_GO，37 分 29 秒，服务端 3 个失败文件 / 4 项失败，7853 项通过、27 项 skipped；Turbo 其余 workspace 中止，0/7 successful。`final-workspace-test-03.log`、对应 JSON；不是全仓通过 |
| 范围外失败复核 | GitCore 的 pull 阻塞说明与 CheckpointReactor 的 ACK 场景各单例 PASS，分别见 `gitcore-failure-retest-03.log`、`checkpoint-failure-retest-03.log`。不改判首次失败 |
| CodexTextGeneration 复核 | NO_GO，两个隔离假 CLI 的认证失败/进程清理场景仍失败，见 `textgeneration-failure-retest-03.log`。实际错误为 ChildProcess.exitCode 读取 Unknown，不能得到预期的进程组信号/认证错误说明。测试及生产文件与基线无差异，未定位到 T-037；建议主控另行分派此进程边界问题，不在本 ticket 改动 |
| fresh-context 独立审查 | 限定 T-037 PASS，见 [审查](acceptance-review-03.md)、[来源](review-provenance-03.json)。create 单独检查，另外 9 个命令在 blocked 数组；共 10 个变更命令。审查未覆盖全仓、UI 或真实模型 |

全仓未通过的范围外修复未执行；上述结果不用于发布或 M1 完成声明。候选源码冻结后没有再修改。证据目录的 diff whitespace 检查会报告原始日志、快照和 verbatim Markdown 空白；原样保留，详情见 `evidence-whitespace-check.json`。旧 manifest 克隆时继承了时间字段，原记录保留；本轮明确的时间与源码字节核对见 `freeze-binding-03.json`。

本 ticket 只证明隔离编排与本地真实 engine/存储/GET；没有真实 Codex app-server 模型调用，不证明模型理解、供应商实际 tier、真实 provider 启停、沙箱/Git 权限、T-038 界面显示、M1 真实闭环或切换。真实模型调用与切换仍由 T-039/T-040 负责。

主控为 Claude Code `wF:pM`；worker 为 s2-t037，观察到的 live pane 为 `wF:pY`、terminal `term_65d4bcf49703bc9`、Codex 原生会话 `01a1198d-50be-78c1-82ca-a0160b3682a6`。本 worker 未获提供受管 attempt/fence，保持未知，不编造。配置来源为批次启动 argv，实际 tier 未验证。版本与 skill 来源见 `versions-and-skills.json`、`runtime-versions-03.json`。完整夹具归档见 `retained-fixtures.tar.gz` 与 `retained-fixtures.json`；原目录未删，归档内的 Git repo/worktree 不登记 gitlink。


## 复现与交接

在 `~/Documents/Code/synara` 保持该冻结版本、外置盘挂载时，从 a2a 仓库执行；label 必须全新以保留旧记录：

```sh
PYTHONPATH=/Users/luckye/Documents/Code/a2a/acceptance COOP_SCRIPT=/Users/luckye/Documents/Code/a2a/evidence/2026-10-07-synara-batch2/T-037/native-entry.py python3 -B evidence/2026-10-07-synara-batch2/T-037/run-acceptance.py UNIQUE_RUN_LABEL /Users/luckye/Documents/Code/a2a/evidence/2026-10-07-synara-batch2/T-037/test_run_native_e2e.py
PYTHONPATH=/Users/luckye/Documents/Code/a2a/acceptance COOP_NATIVE_ENTRY=/Users/luckye/Documents/Code/synara/packages/a2a-gates/src/cli.ts python3 -B evidence/2026-10-07-synara-batch2/T-037/run-acceptance.py UNIQUE_DELIVERY_LABEL /Users/luckye/Documents/Code/a2a/evidence/2026-10-07-synara-batch1/T-036/native-acceptance/native-suite.py
PYTHONPATH=/Users/luckye/Documents/Code/a2a/acceptance python3 -B evidence/2026-10-07-synara-batch2/T-037/run-mutant.py done-no-submit UNIQUE_MUTANT_LABEL
PYTHONPATH=/Users/luckye/Documents/Code/a2a/acceptance python3 -B evidence/2026-10-07-synara-batch2/T-037/run-mutant.py ignore-expected-attempt UNIQUE_MUTANT_LABEL
```

原生服务、故障与异步证明使用 `run-fork-check.py UNIQUE_LABEL <本目录相应 .ts 绝对路径>`；完整命令保存在每轮 JSON。没有新建真实模型 home、安装 hook、修改用户 Codex/Synara 数据或操作用户 Herdr server。只终止本次核对过的旧候选 Turbo 与悬空夹具 CLI，诊断与结果保留。

主控可据此关闭 ticket，但不得复用此局部通过结论为 T-038、T-039、M1 或范围外进程问题背书。
