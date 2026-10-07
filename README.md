# a2a

a2a 研究怎样让多 agent 协作不依赖模型持续记住操作手册。项目分两部分：

- **协作门禁（首轮，已完成）**：`coop.py` 运行在已安装的 Herdr 上，用程序约束认领、交付、独立验收和集成。用法见下文。
- **Muster 工作台（第二阶段，开发中）**：自建的 GPUI 多 agent 工作台。它以 Herdr 0.9.3 引擎的硬分叉取代 Herdr CLI：每个项目一个窗口，任务是标签页，任务里的多个 pane 供 agent 分工。目标与范围见 [intent.md](intent.md)，设计与任务顺序见 [M1 spec 与初步任务书](.project-map/specs/workbench-m1-2026-10-06.md)。
  - 引擎源码在 `muster/engine/`（来源与许可见其中的 NOTICE 和 LICENSE），正由 T-027 验收，尚不能替代 Herdr 日常使用；桌面应用 Muster.app 尚未开始。构建只经下文的 `scripts/build`。

文档入口：[项目地图](.project-map/MAP.md)、[术语表](CONTEXT.md)、[项目规则](AGENTS.md)、[开发发现](findings/README.md)。

## Rust 构建：外置盘入口

Muster 引擎、Muster.app 和 T-025 探针统一经仓库内的 `scripts/build` 调用 Cargo。在仓库根目录运行，例如：

```sh
./scripts/build build --locked --manifest-path muster/Cargo.toml
MUSTER_BUILD_SLOT=worker-t027 ./scripts/build test --locked --manifest-path muster/Cargo.toml
```

入口默认检查 `/Volumes/WD-Elements` 是独立于仓库所在内置文件系统的真实挂载点，随后固定 Rust 1.96.1 与 Zig 0.16.0，并设置下表的路径。缺盘、普通目录冒充挂载点、缓存路径经符号链接逃出该卷或 Zig 缺失时，在启动 Cargo 前报错。`MUSTER_BUILD_VOLUME` 仅供明确指定另一外置挂载点或模拟缺盘；不自动创建挂载点。

| 内容 | `/Volumes/WD-Elements/dev-cache/a2a/` 下的路径 |
| --- | --- |
| Cargo registry、git 与元数据（`CARGO_HOME`） | `cargo-home/`，所有 worker 共享 |
| 编译输出与中间产物（`CARGO_TARGET_DIR`、`CARGO_BUILD_TARGET_DIR`、`CARGO_BUILD_BUILD_DIR`） | `target/<slot>/` |
| Zig 全局缓存（`ZIG_GLOBAL_CACHE_DIR`） | `zig-cache/global/`，所有 worker 共享 |
| Zig 本地缓存（`ZIG_LOCAL_CACHE_DIR`） | `zig-cache/local/<slot>/` |
| 构建临时目录（`TMPDIR`） | `tmp/<slot>/` |
| 子进程的 npm 缓存（`npm_config_cache`） | `npm-cache/` |
| Zig 发布包与安装目录（`ZIG`） | `toolchains/zig-aarch64-macos-0.16.0/zig` |

`<slot>` 默认是 `default`，可用 `MUSTER_BUILD_SLOT` 设置单个目录名。多个 worker/worktree 各用固定且不同的 slot，以免 Cargo 的同 target 锁让构建串行等待；同一个 worktree 的重复构建继续使用同一 slot，保留增量产物。共享 registry/git 与 Zig 全局缓存节省下载和磁盘空间，独立 target 会增加总占用。

本项目迁移整个 `CARGO_HOME`，让 registry/git 也留在外置盘；不复制用户的凭据或全局配置，不迁移已有 Rust 安装。挂盘且依赖已缓存时可加 `--offline`；缺盘时仍报错。直接执行 `cargo`、`zig build` 或 IDE 自己的构建命令会绕过入口，必须改为调用 `scripts/build`。入口拒绝 Cargo 的 `--target-dir`、`--artifact-dir` 和 `--config`，避免命令行覆盖受管路径；`cargo run/test` 的 `--` 后参数原样交给程序或测试。

Zig 已在本机按 T-026 安装。其他 macOS arm64 机器先确认已有 Rust 1.96.1，再从 [Zig 官方发布索引](https://ziglang.org/download/index.json) 核对 `0.16.0`。安装时在子 shell 中先检查挂载，然后把官方包下载、解压到外置盘：

```sh
(
  set -eu
  python3 -c 'from pathlib import Path; import os; p=Path("/Volumes/WD-Elements"); assert p.is_mount() and p.stat().st_dev != os.stat(".").st_dev, "external volume not mounted"'
  muster_tools=/Volumes/WD-Elements/dev-cache/a2a/toolchains
  mkdir -p "$muster_tools"
  curl -fL https://ziglang.org/download/0.16.0/zig-aarch64-macos-0.16.0.tar.xz -o "$muster_tools/zig-aarch64-macos-0.16.0.tar.xz"
  tar -xf "$muster_tools/zig-aarch64-macos-0.16.0.tar.xz" -C "$muster_tools"
  "$muster_tools/zig-aarch64-macos-0.16.0/zig" version
)
```

不改 `~/.zshrc`、`~/.cargo/config.toml` 或全局 Git 配置。Enchanted 保持冻结；以后并入工作台时，其 Rust 构建使用同一入口，npm 的独立构建入口也须先做相同挂载检查再设置外置盘缓存。测量、缺盘反例与适用边界见 [T-026 证据](evidence/2026-10-06-m1-batch1/T-026/RESULTS.md)。

## 协作门禁：coop.py

`coop.py` 是单机受管理交付入口。它用 Python 3.9 标准库、SQLite、Git 和已安装的 Herdr，把 task、attempt、submit、acceptance 和 integration 记录在磁盘上。冻结 CLI 契约见 [执行规格](.project-map/specs/managed-delivery-2026-10-06.md)、[恢复契约](.project-map/specs/recovery-2026-10-06.md) 和 [自动运行契约](.project-map/specs/supervised-run-2026-10-06.md)。

这是同一用户下可信协作者的流程门禁。worker 仍拥有该用户的磁盘和进程权限，worktree、随机 session 和 oracle 快照都不是安全沙箱。程序不更新用户工作分支，也不 push。

## 本地闭环

所有调用使用 `python3 coop.py --state ABS_DIR COMMAND ...`。`--state`、repo、oracle 和 instructions 都必须是绝对路径；commit 必须是完整 SHA。成功输出一个含 `ok=true` 的 JSON 对象，退出 0；拒绝输出 `ok=false,error`，退出 1；语法错误退出 2。

```sh
python3 coop.py --state /absolute/state create \
  --task example --repo /absolute/git-repo --base FULL_BASE_SHA \
  --oracle /absolute/oracle.py --instructions /absolute/instructions.txt
python3 coop.py --state /absolute/state claim --task example --owner worker
```

`create` 冻结任务输入并复制 oracle 和 instructions。`refs/a2a/integration` 不存在时以 base 初始化；已存在时必须等于 base。`claim` 原子分配 attempt/session/fence/spec_rev，并在 state 下创建独立 detached worktree。worker 只在返回的 workspace 工作，创建本地 commit，保持 worktree 干净，再用 claim 返回的精确身份交付：

后续任务以 `git rev-parse refs/a2a/integration` 得到的受管集成头作为 base；用户工作分支不会自动移动。

```sh
python3 coop.py --state /absolute/state submit --task example \
  --attempt ATTEMPT_ID --session SESSION_ID --fence FENCE \
  --spec-rev SPEC_REV --commit FULL_CANDIDATE_SHA
python3 coop.py --state /absolute/state verify --task example
python3 coop.py --state /absolute/state integrate --task example
python3 coop.py --state /absolute/state status --task example
python3 coop.py --state /absolute/state events --task example
```

`submit` 只进入 submitted。同身份同候选可以重交，已冻结候选不能被不同 commit 替换。旧 attempt/session/fence/spec、非基线后代、HEAD 不匹配或脏 worktree 都被拒绝。

`verify` 从集成头 G 和候选 C 构造 M，在新的 detached worktree 执行 `python3 -I -B SNAPSHOT_ORACLE CANDIDATE_DIRECTORY`，超时为 60 秒。oracle 退出 0 才进入 verified；非零返回 `oracle_failed`，仍可查询完整输出。验收记录绑定 task、attempt/session/fence/spec、G/C/M 和 oracle 路径。验证目录保留，不修改 worker 的工作区。

`verify`、`integrate` 与 `reclaim` 共用本任务的操作锁，在 SQLite 初始化前取得锁。活跃执行者持锁时，竞争调用立即返回 `operation_busy`。当前 macOS/POSIX 平台使用 `fcntl.flock`；锁由操作进程持有，子进程不继承，进程退出自动释放。锁文件保留，不根据 PID 判断所有权；`status`、`events` 等命令不取得操作锁。

验收进程中断后，重新调用 `verify` 会先核验当前 attempt/session/fence/spec 和候选，将旧 verification 保留并标为 interrupted，追加 `verification_interrupted` 事件。原候选、oracle、worktree 和 command_intent 保留；缺失的旧 stdout/stderr/exit 标为未知。新 verification 使用新 ID 和独立 worktree，完整重跑冻结 oracle；孤儿 oracle 的结束不能使它通过。已撤销或过期的候选不能恢复。

`integrate` 先持久记录 intent，再用 `git update-ref refs/a2a/integration M G` 做 CAS。建立 intent 前集成头变化会拒绝并使旧验收失效。成功进入 accepted；重复调用不再写引用。中断后重放须核验当前资格，以及 intent 与 verification 的身份、候选、G/C/M 和 ID 绑定。引用仍为 G 时继续同一 intent 的 CAS；已为 M 时只补记 accepted，不再次写 Git，遗失的原命令输出与退出码仍标未知。引用为第三值或不存在时返回 `needs_reconciliation`，保留 intent 和证据，交由主控核对；CAS 失败或成功后回读无法确认 M 时也保留待核对状态。

`verify` 和 `integrate` 可加 `--attempt ATTEMPT_ID`。它们在事务边界核对当前 attempt，不匹配返回 `stale_attempt`；accepted 的幂等返回也先核对。省略时仍由 controller 明确操作当前任务。

```sh
python3 coop.py --state /absolute/state revoke --task example --reason 'retry after diagnosis'
python3 coop.py --state /absolute/state revise --task example --spec-rev 2
```

`revoke` 和递增的 `revise` 使当前执行、候选和验收失效，保留历史及 worktree。accepted 不能撤销。未核对的 integration intent 也不能撤销。`revise` 由 controller 使用，真实验收要求变化仍需人工方向门禁。

## Herdr 生命周期

主控须在 `HERDR_ENV=1` 的 Herdr 环境内运行。先从权威清单取得 live 父 pane，使用当前服务器的句柄；不使用继承的 pane ID 或 UI 焦点。

```sh
herdr pane list
herdr agent list
python3 coop.py --state /absolute/state dispatch --task example \
  --parent-pane LIVE_PARENT_ID --name unique-worker
python3 coop.py --state /absolute/state observe --task example
python3 coop.py --state /absolute/state reclaim --task example
```

`dispatch` 自行 claim，在 attempt worktree 创建 no-focus pane，启动 Codex 0.160.1、`gpt-6.1-sol`、xhigh、`service_tier="fast"`、`check_for_update_on_startup=false`、`--no-alt-screen`，为 submit 提供 state 的可写目录。不同 CLI 版本会拒绝。启动 argv、版本输出、Herdr 原始响应、pane/terminal、shell/agent PID 和可观察 native session 都保留。Fast 是请求配置，不是供应商实际 tier 的证明。

启动被识别为 blocked/unknown 或未确认 interactive ready 时暂停，不自动回答或重发。确认 ready 后仅投递一次任务摘要和精确 submit 命令；部分副作用未知时保留绑定，拒绝重复 dispatch。`idle`、`done` 和 prompt 投递成功都不推进业务验收。

`observe` 仅记录绑定 pane 的真实状态，不改变业务成功状态。dispatch 将 Codex 前台进程组领导者的 PID 保存到 `agent_pids`。run 与 reclaim 核对同一组领导者的 Codex 身份、原 pane/terminal、shell、agent 名称和已记录 native session；正常辅助进程的增减不算身份变化，组领导者改变则拒绝，即使旧 PID 仍在进程清单中。`reclaim` 在关闭前撤销非终态任务的有效 attempt。目标已不存在时用权威 pane 清单核对。身份冲突或未知前台进程会拒绝，不关闭父 pane 或其他 pane。

`reclaim --attempt ATTEMPT_ID` 精确选择该 task 的历史 attempt，只回收它绑定的 pane；仅当它仍是 current_attempt 时才撤销业务状态。已回收的同一历史 attempt 可无副作用重放。其他 task、未知 attempt 或不确定身份会拒绝。

## 自动运行

主控先用 `create` 注册任务及独立 oracle，再调用：

```sh
python3 coop.py --state /absolute/state run --task example \
  --parent-pane LIVE_PARENT_ID --name unique-worker --wait-seconds 300
```

`run` 自动 dispatch，等待该 attempt 的显式 submit，再用原有门禁 verify、integrate 并核对回收自己的 pane。`--wait-seconds` 必须为正整数，只约束成功投递后等待 submit 的阶段，按单调时钟计量；启动、oracle 和 Herdr 子进程各自仍有原超时，不构成完整运行的总时限。没有 submit 的 idle/done 不会推进，程序不重发 prompt、不编造候选、不答复权限请求。

相同 task 的活跃 run 互斥，第二个立即返回 `run_busy`。run 在分派、验收/集成和回收阶段取得同一操作锁；等待 submit 时释放操作锁，允许 controller 核对、撤销或替换 attempt。旧 run 发现替换后返回 `run_superseded`，最多核对清理自己的历史 pane。blocked、未知身份或未知外部副作用会暂停并保留现场；可核对的等待超时和 oracle 拒绝会尝试回收自己的 pane，保留候选及 worktree。

成功返回 exit 0、`ok=true`、`task.state=accepted` 和 `run.outcome=completed`，并已确认自己的 pane 回收。失败返回 exit 1、`ok=false,error`；已创建的 run 收据仍在顶层 `run` 中。无 submit 到期返回 `run_deadline`，oracle 拒绝返回 `oracle_failed`。已集成但回收失败返回 `run_reclaim_failed`，收据 outcome 为 `integrated_reclaim_failed`，task 仍保持 accepted；其他失败的回收错误记录在 `cleanup_failure`，不掩盖原失败。

收据仅记录协调阶段与 run/attempt/session/fence/spec 身份，task 的成功事实仍来自原状态。`events --task example` 可读回 `run_started`、`run_bound`、阶段变化及 `run_finished`；最终事件将 `run_id` 与最终 `outcome` 持久关联。无变化的等待观察不重复保存完整快照。run 进程中断不会自动重新投递，已有身份、输入和事件保留，由 controller 使用现有核对入口处理。

## 证据与限制

首轮范围已通过：[受管交付](evidence/2026-10-06-managed-01/RESULTS.md)、
[验收/集成中断恢复](evidence/2026-10-06-recovery-01/RESULTS.md)、
[自动运行](evidence/2026-10-06-run-01/RESULTS.md)。自动运行包含一次真实 Codex 交付及独立引用读回；
隔离编排负例与真实模型证据分别记录，不延伸为跨 CLI 或长期收益。

`state/state.sqlite3` 保存任务、历史 attempt、验收记录及按序追加事件；`tasks/` 保存输入快照，`worktrees/` 和 `verification/` 保存执行与验证目录，`locks/` 保存任务操作锁和 run 互斥锁文件。Git、Herdr 和 oracle 子进程均使用 argv，不通过 shell 拼接。失败、超时和未知状态留在记录中，工作区保留供诊断；没有 worktree 自动删除、租约或后台重试。验收/集成中断恢复通过再次调用原 `verify` / `integrate` 命令进行。

本地 CLI 独立验收：

```sh
python3 -B acceptance/test_coop_e2e.py
python3 -B acceptance/test_recovery_e2e.py
python3 -B acceptance/test_run_e2e.py
```

三个套件分别为交付8项、恢复9项和编排18项。恢复使用真实中断及 Git/SQLite；编排负例的 Herdr/Codex 是替身。另有真实自动运行与独立审查，具体候选、原始结果和适用范围见上方报告。当前检查不证明第二 CLI、完整 run 进程恢复或长期收益。

只调用一次产品 run 的真实验收入口为：

```sh
python3 -B acceptance/live_run.py --parent-pane LIVE_PARENT_ID \
  --fixture-repo /absolute/inspected-fixture --output NEW_OUTPUT_DIRECTORY
```

真实入口检查使用独立分页夹具：

```sh
python3 -B acceptance/live_herdr.py --parent-pane LIVE_PARENT_ID --output NEW_OUTPUT_DIRECTORY
```

首次启动新 Git 夹具可能等待 Codex 目录信任。程序会暂停并保留绑定，不自动批准。
主控核对夹具并完成已授权的目录信任后，先用 `reclaim` 撤销旧 attempt、回收 pane，
再指定 `--fixture-repo /absolute/inspected-fixture` 和新的输出目录重跑。测试会核对夹具仍为
干净的原始输入；旧失败产物不覆盖。它等待显式 submit，检查未验收集成被拒，再执行
独立 oracle、CAS 集成、重复调用以及受管引用的独立代码回读。
