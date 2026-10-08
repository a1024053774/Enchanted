# T-036 交付记录（2026-10-07）

**INCOMPLETE，待主控关闭。** 主控 Claude Code（`wF:pM`）；执行 worker 为主控启动的 `s1-t036`（`wF:pX`）。fork 本地候选为 `5cae1072db94ccd1af20ef161481163484aecfe5`，基线 `7cb0ac0a3d5232e90ab2db1fb7eb9ee696d1af73`，未 push。当前只证明交付契约；恢复的中断场景与 Git 回读反例尚未证明。

## 四项验收

| 条件 | 结论 | 命令与证据 |
| --- | --- | --- |
| 交付 8 项与先验红态 | PASS | `python3 -B evidence/2026-10-07-synara-batch1/T-036/run-acceptance.py frozen-delivery test_coop_e2e.py`；冻结候选 8/8。原 CLI 对 `--state … create` 返回 exit 2：[契约红态](red-delivery-entry-fixed/command.json)、[冻结绿态](frozen-delivery/command.json)、各自 `trace.json` |
| 恢复 9 项 | INCOMPLETE | `…/run-acceptance.py candidate-recovery-01 test_recovery_e2e.py`；2 项操作锁检查通过，7 项原夹具在注入前拒绝。没有实际 SIGKILL：[原始结果](candidate-recovery-01/command.json)、[SQLite/Git/命令快照](candidate-recovery-01/trace.json)。该轮早于最终冻结；不把它称为冻结版本的恢复验收 |
| fence 与 Git 回读 mutant | INCOMPLETE | `…/run-mutant.py fence test_coop_e2e.py entry-fixed` 的原套件在错 fence 的 `0 != 1` 业务断言失败：[结果](mutant-fence-test_coop_e2e-entry-fixed/command.json)。`…/run-mutant.py readback test_recovery_e2e.py entry-fixed` 只有夹具错误：[结果](mutant-readback-test_recovery_e2e-entry-fixed/command.json)；它不能证明 Git 回读 mutant 被抓住。两份完整错误实现与差异保存在 [mutants](mutants/) |
| CLI 差异记录、不改预期 | PASS（记录） | 下表记录原生运行差异；未修改 `acceptance/test_coop_e2e.py`、`acceptance/test_recovery_e2e.py` 或 oracle。只新增薄转接脚本，原样转交参数 |

## CLI 与运行时差异

| 项目 | 原因与影响 | 处理建议 / 状态 |
| --- | --- | --- |
| 中断前的入口身份核对 | `test_recovery_e2e.py:201` 要求 `ps` 含 `COOP_SCRIPT` 的 Python 路径。`os.execv` 保持 PID，但最终进程为 `bun …/packages/a2a-gates/src/cli.ts --state … COMMAND --task …`，路径已改变。夹具先拒绝、没有发信号，因此 7 项恢复及 Git 回读反例缺少业务证据 | [proposed-native-identity.diff](proposed-native-identity.diff) 只参数化进程入口路径，保留 PID 活跃检查、state/task 限制和所有业务断言。提议只用于证据副本，不改原文件；**等待主控批准，尚未执行** |
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
| 冻结独立审查、串行全仓复核 | INCOMPLETE，正在保存最终结果 | 完成后只补记证据，不改变冻结代码 |

当前暂停的是恢复夹具身份核对的后续推进。主控最小决定是批准所列证据副本差异，随后重跑冻结恢复套件与 readback mutant；也可保持 T-036 open，交下一轮处理。未触碰用户 Herdr、用户配置或 Synara 数据；未 push、未执行真实模型调用、未删除现场。原验收自身释放了本次创建的屏障和 CLI；临时仓库、worktree 和失败记录保留。
