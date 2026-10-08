# a2a

a2a 研究怎样让多 agent 协作不依赖模型持续记住操作手册。

工作台基于 Synara 的 fork（[`a1024053774/synara`](https://github.com/a1024053774/synara)，起点 v1.0.1-beta.2），按“项目 → 任务 → agent 会话”组织。原生门禁在 fork 的服务端实现；fork 单独 clone，本仓库保管规范、门禁契约、验收场景与证据。目标与 M1 见 [intent.md](intent.md)，切换进度见 [T-040](.project-map/tickets/T-040-switchover.md)。

旧运行源码与 Rust 构建入口已删除。历史实现保存在 Git 历史和日期证据中。工作台专用数据目录、启动器及首次日常派发由 T-040 的其余部分交付；A 部分的隔离验收不代表这些工作已经完成。

文档入口：[项目地图](.project-map/MAP.md)、[术语表](CONTEXT.md)、[项目规则](AGENTS.md)、[开发发现](findings/README.md)。

## 原生门禁入口

门禁核心位于相邻 checkout `../synara/packages/a2a-gates/`。需要已安装依赖的 fork 和挂载的 `/Volumes/WD-Elements`；Bun、Node、缓存与构建统一经 fork 的 `a2a/scripts/bun`。缺盘时入口报错，不回退到内置盘。构建与环境约束见 [T-034](.project-map/tickets/T-034-synara-fork-builds.md)。

本仓库的 `acceptance/entry/a2a_gates.py` 原样转交 CLI 参数，用 `os.execv` 进入 fork 的原生 CLI，不包含门禁业务逻辑。所有业务状态变更仍由同一门禁核心负责。冻结契约见 [受管交付](.project-map/specs/managed-delivery-2026-10-06.md)、[恢复](.project-map/specs/recovery-2026-10-06.md) 和 [自动运行](.project-map/specs/supervised-run-2026-10-06.md)。

这是同一用户下可信协作者的流程门禁。worktree、随机 session 和 oracle 快照不是安全沙箱。门禁不更新用户工作分支，也不 push。

## 本地交付与恢复

从 a2a 仓库调用 `python3 acceptance/entry/a2a_gates.py --state ABS_DIR COMMAND ...`。state、repo、oracle、instructions 必须是绝对路径，commit 使用完整 SHA。成功输出 `ok=true`，退出 0；业务拒绝输出 `ok=false,error`，退出 1；语法错误退出 2。

```sh
python3 acceptance/entry/a2a_gates.py --state /absolute/state create \
  --task example --repo /absolute/git-repo --base FULL_BASE_SHA \
  --oracle /absolute/oracle.py --instructions /absolute/instructions.txt
python3 acceptance/entry/a2a_gates.py --state /absolute/state claim \
  --task example --owner worker
python3 acceptance/entry/a2a_gates.py --state /absolute/state submit \
  --task example --attempt ATTEMPT_ID --session SESSION_ID --fence FENCE \
  --spec-rev SPEC_REV --commit FULL_CANDIDATE_SHA
python3 acceptance/entry/a2a_gates.py --state /absolute/state verify \
  --task example --attempt ATTEMPT_ID
python3 acceptance/entry/a2a_gates.py --state /absolute/state integrate \
  --task example --attempt ATTEMPT_ID
python3 acceptance/entry/a2a_gates.py --state /absolute/state status --task example
python3 acceptance/entry/a2a_gates.py --state /absolute/state events --task example
```

`create` 冻结 oracle 和 instructions；受管集成引用为 `refs/a2a/integration`。后续任务以该引用的完整提交号作为 base。`claim` 原子分配 attempt、session_id、fence、spec_rev，并创建独立 detached worktree。worker 只在返回的 workspace 中工作和提交，保持 worktree 干净，再交付 claim 返回的精确身份。

`submit` 只进入 submitted，不代表通过。旧身份、脏 worktree、HEAD 不匹配或替换已冻结候选会被拒绝。`verify` 在新的 detached worktree 中完整执行冻结的独立 oracle，退出 0 才进入 verified。`integrate` 记录 intent 后用 Git CAS 更新受管引用；成功后独立回读确认，重复调用不再写引用。

验收、集成与回收共用任务操作锁。竞争调用返回 `operation_busy`；进程退出释放锁不代表验收成功。中断后再次调用原 `verify` / `integrate`：验收使用新的 verification 和 worktree 重跑，集成只恢复原 intent。受管引用变成第三值或被删除时返回 `needs_reconciliation`，保留现场，由主控核对。旧输出、退出码和未知结果不会补写成成功。

`verify`、`integrate` 的 `--attempt` 在事务边界核对当前身份，accepted 的幂等返回也先核对。撤销和规格修订保留历史、候选与 worktree：

```sh
python3 acceptance/entry/a2a_gates.py --state /absolute/state revoke \
  --task example --reason 'retry after diagnosis'
python3 acceptance/entry/a2a_gates.py --state /absolute/state revise \
  --task example --spec-rev 2
```

真实验收条件改变仍需主控决定；accepted 或尚未核对的 integration intent 不能撤销。

## 工作台派发与自动运行

带原生 agent 会话的 `dispatch`、`run`、`reclaim` 经运行中的 Synara 服务调用，使用该服务自己的门禁状态目录。不能把本地 `--state` 调用当作已经接入原生 thread 服务。CLI 的 HTTP 传输示例（服务 URL、owner 凭据和 task 必须来自主控核对的当前实例）：

```sh
../synara/a2a/scripts/bun ../synara/packages/a2a-gates/src/cli.ts \
  http://127.0.0.1:PORT \
  '{"command":"run","task":"example","runtimeMode":"approval-required","wait_seconds":300}'
```

调用时环境中须有 `A2A_GATE_BEARER`。MCP 的 `a2a_submit` 与 HTTP、CLI 一样汇入同一门禁核心；受管 worker 通过 MCP 显式交付。主控使用的专用工作台启动器和 CLI 包装见 T-040 其余部分的交付。

`run` 自动分派，等待其原 attempt 的显式 submit，再验收、集成、停止并归档自己的 agent 会话。必须显式给出正整数 `wait_seconds`；它只约束投递后等待 submit 的阶段，不是整个 run 的总期限。空闲、结束或模型自述不会交付。活跃 run 互斥；旧 run 不会接管替换 attempt。权限等待、身份冲突、未知外部副作用会暂停并保留现场，不自动回答或重发。

原生运行身份核对 thread、turn 与 worktree。回收带指定 attempt 时只处理该任务绑定的历史会话，不能撤销或回收新执行者。成功收据要求 task 为 accepted 且自己的会话已回收；收据记录协调结果，不替代业务验收。受管会话中的人工输入记录为人工介入；记录故障可从 status/events 和界面核对，并阻止进一步状态变更。

## 隔离验收与证据

三个套件分别保持交付 8、恢复 9、编排 18 项。真实 CLI、Git、SQLite、独立分页 oracle 保留；编排的原生 thread 服务是外部替身，不能证明真实 provider、模型、实际服务 tier 或长期收益。

在 fork `d3b5bcc61cc212572f38e01139e1b9af2196b820` 与外置盘挂载时，从 a2a 根目录执行下面的记录入口。每次 label 必须全新；命令、版本、完整输出、trace 与临时 Git/worktree 现场保存在独立目录，不覆盖旧记录。

```sh
python3 -B evidence/2026-10-08-batch4/T-040-A/run-check.py UNIQUE_DELIVERY candidate delivery
python3 -B evidence/2026-10-08-batch4/T-040-A/run-check.py UNIQUE_RECOVERY candidate recovery
python3 -B evidence/2026-10-08-batch4/T-040-A/run-check.py UNIQUE_RUN candidate run
```

`acceptance/test_coop_e2e.py` 默认选择原生门禁入口；恢复的中断注入仍核对本次创建的 Popen PID、原生 CLI 路径、state 和 task。直接调用恢复 suite 时，环境中的 `COOP_NATIVE_ENTRY` 须为 fork 内 `packages/a2a-gates/src/cli.ts` 的绝对路径。编排 suite 默认使用 `acceptance/entry/native-entry.py` 的受控 thread 边界；同目录的 TypeScript 转接器只把外部 thread 服务替换为夹具。

本次删除前后结果与不存在入口的反例见 [T-040 A](evidence/2026-10-08-batch4/T-040-A/RESULTS.md)。原生移植记录见 [T-036](evidence/2026-10-07-synara-batch1/T-036/RESULTS.md)、[T-037](evidence/2026-10-07-synara-batch2/T-037/RESULTS.md)；真实模型闭环见 [T-039](evidence/2026-10-07-synara-batch2/T-039/RESULTS.md)。各证据只证明其绑定的代码版本和范围。
