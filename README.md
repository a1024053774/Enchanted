# Herdr A2A

`coop.py` 是单机受管理交付入口。它用 Python 3.9 标准库、SQLite、Git 和已安装的 Herdr，把 task、attempt、submit、acceptance 和 integration 记录在磁盘上。冻结 CLI 契约见 [执行规格](.project-map/specs/managed-delivery-2026-10-06.md)。

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

`integrate` 先持久记录 intent，再用 `git update-ref refs/a2a/integration M G` 做 CAS。集成头变化会拒绝并使旧验收失效。成功进入 accepted；重复调用不再写引用。若中断发生在引用更新后、记账前，重放仅在引用仍为 M 时补记；其他状态返回 `needs_reconciliation`，交由主控核对。

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

`observe` 仅记录绑定 pane 的真实状态，不改变业务成功状态。`reclaim` 核对原 pane/terminal、shell、agent 名称、PID 和已记录 native session；在关闭前撤销非终态任务的有效 attempt。目标已不存在时用权威 pane 清单核对。身份冲突或未知前台进程会拒绝，不关闭父 pane 或其他 pane。

## 证据与限制

`state/state.sqlite3` 保存任务、历史 attempt、验收记录及按序追加事件；`tasks/` 保存输入快照，`worktrees/` 和 `verification/` 保存执行与验证目录。Git、Herdr 和 oracle 子进程均使用 argv，不通过 shell 拼接。失败、超时和未知状态留在记录中，工作区保留供诊断；本切片没有自动清理、租约或后台重试。

本地 CLI 独立验收：

```sh
python3 -B acceptance/test_coop_e2e.py
```

该套件使用独立临时 repo 和 CLI 子进程。实现 worker 的结果见 [build-result.json](evidence/2026-10-06-managed-01/build-result.json)，expected-red 见 [build-red.json](evidence/2026-10-06-managed-01/build-red.json)。真实 Herdr/Codex dispatch、交付和回收，以及 known-bad 检查由主控单独执行；CLI 通过不能替代这些外部边界证据。

真实入口检查使用独立分页夹具：

```sh
python3 -B acceptance/live_herdr.py --parent-pane LIVE_PARENT_ID --output NEW_OUTPUT_DIRECTORY
```

首次启动新 Git 夹具可能等待 Codex 目录信任。程序会暂停并保留绑定，不自动批准。
主控核对夹具并完成已授权的目录信任后，先用 `reclaim` 撤销旧 attempt、回收 pane，
再指定 `--fixture-repo /absolute/inspected-fixture` 和新的输出目录重跑。测试会核对夹具仍为
干净的原始输入；旧失败产物不覆盖。它等待显式 submit，检查未验收集成被拒，再执行
独立 oracle、CAS 集成、重复调用以及受管引用的独立代码回读。
