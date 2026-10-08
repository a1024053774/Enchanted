# Spec: 首个受管理交付闭环（2026-10-06）

状态：执行规格；在已接受 intent 和用户“开始按规划分配执行”的授权范围内细化。
承接 [原设计记录](herdr-a2a.md)、[T-005](../tickets/T-005-first-seam-and-baseline.md)。
目标只覆盖本地可信但会犯错的 coding worker，不提供同一系统用户下的恶意隔离。

## Tracer bullet 与边界
一个任务从真实 Herdr 分派，经过独立 Git worktree、持久 attempt、固定候选、
外部 oracle 验收，最终写入本地受管引用。重放旧身份、漏交付或自然语言完成不推进任务。
采用 Python 3.9 标准库 + SQLite + Git + 已安装 Herdr，零新运行依赖。Herdr 保持终端运行时，
该目录实现可直接运行的外部扩展入口 coop.py；不升级/重启用户 server，也不改上游。
这是最小可撤销切片的工程选择；其他 CLI 仅记录 capability contract，不预制抽象适配器。
Deep modules：一个小 CLI 隐藏事务、Git 候选和 Herdr 协调；避免逐字段透传的空包装。
Ubiquitous language 使用 CONTEXT 中的 task / attempt / submit / acceptance / integration。

## CLI contract v1（冻结给实现者和独立验收者）
入口：`python3 coop.py --state ABS_DIR COMMAND ...`。
输出一个 JSON 对象。成功 exit 0、含 ok=true；拒绝 exit 1、含 ok=false,error（稳定代码）。
语法错误可 exit 2。DB 为 state/state.sqlite3；events 命令读取按序追加事件。
所有 ID/路径输入需检查；Git/Herdr/验收一律 argv 调用，不 shell 拼接。

- `create --task ID --repo ABS_GIT_REPO --base FULL_SHA --oracle ABS_PY --instructions ABS_TEXT`
  注册不可变任务输入；初始 spec_rev=1；复制 oracle 到 state 自有路径，验收绑定该快照；
  集成引用为 refs/a2a/integration，初始为空时以 base 创建；存在时必须与 base 一致。
  repo/commit/oracle/instructions 先核验。拒绝覆盖同名任务。返回 task 字段。
- `claim --task ID --owner LABEL`：原子建立唯一 attempt，分配随机 attempt_id 和 session_id、
  递增 fence，返回 attempt 对象（attempt_id,session_id,fence,spec_rev,workspace,base_commit）。
  在 state/worktrees 下准备独立 Git worktree；失败持久记录，不覆盖旧目录。
  owner 是标签，不能自行声明有效 session；session_id 是协调层创建的运行身份，
  与 Herdr native_session 观察字段不同。不是操作系统安全身份。
- `revoke --task ID --reason TEXT`：撤销当前 attempt，使候选/验收失效，task 回 ready；
  留下旧 attempt、worktree 和事件。已 accepted 不允许撤销或伪造从未集成。
- `revise --task ID --spec-rev N`：只接受递增版本，撤销当前执行和候选，保留历史。
  已 accepted 拒绝。仅 controller 操作；真实验收需求变更仍遵守人工方向门禁。
- `submit --task ID --attempt ID --session ID --fence N --spec-rev N --commit FULL_SHA`：
  精确匹配当前身份/版本；拒绝 stale_attempt、stale_session、stale_fence、stale_spec。
  候选必须是完整 commit SHA、属于此 repo、为基线后代、等于分配 worktree 的 HEAD，
  且 worktree 干净。仅 submitted 状态，绝不 accepted。同身份同 commit 重交可幂等，
  不同 commit 重交不得偷偷替换已入库候选。失败写事件，不改变合法 task/attempt。
- `verify --task ID`：只处理当前 submitted 候选。从当前集成头 G 与候选 C 构造
  合并候选 M（可快进则 C），在独立 detached worktree 执行
  `python3 -I -B SNAPSHOT_ORACLE CANDIDATE_DIRECTORY`（有超时）。
  stdout/stderr/exit 与 G/C/M/spec/attempt/oracle 路径持久关联。
  非零结果返回 oracle_failed，task 不得 accepted；成功 task=verified。
  不允许 worker 上传 passed=true 或用 Herdr idle/done 代替验证。
  同步单机验收串行即可，不引入后台任务框架。未知/中断保留为需核对状态。
- `integrate --task ID`：仅接受当前 verified 候选；先持久 integration intent
  (G,M,verification)，再 `git update-ref refs/a2a/integration M G`。
  基线变化返回 integration_conflict，不更新引用，也不复用旧验收。
  成功后 task=accepted。重放不得重复副作用；若上次中断在 Git 更新后、记账前，
  引用仍 M 可核对补记；若引用未知，返回需要核对而不是盲重试。
  不更新任何用户工作分支，不 push。
- `status --task ID`：返回 task 对象，含 state,current_attempt,candidate_commit,verification。
  `events --task ID` 返回 events 数组，包含序号、时刻、类型、task/attempt、细节。
- `dispatch --task ID --parent-pane LIVE_ID --name UNIQUE_NAME`：
  程序 claim，创建自己的 pane（cwd=attempt worktree，no-focus），启动 Codex
  gpt-6.1-sol xhigh，显式 service_tier=fast，--no-alt-screen。
  记录 pane/terminal 身份、原始 Herdr response 和原生 session（若可观察）。
  自动生成当前任务摘要、精确 submit 命令并发送一次 prompt；不把 wait 返回当交付。
  任何部分副作用未知时保留记录、拒绝重复 dispatch；不自动改用其他 pane。
- `observe --task ID`：只记录已绑定 pane 的真实状态，不修改业务成功状态。
- `reclaim --task ID`：核对当初创建的 pane/terminal/agent 身份再关闭；
  不碰父 pane、其他用户 pane；保留 worktree/候选/证据。
  如 task 未终态则先撤销有效 attempt。不存在目标时应通过权威清单核对，不能猜测。

## 验收：独立于实现的外部输入
分页夹具见 fixtures/pagination/CONTRACT.md，oracle 已先验地验证参考通过和坏实现失败。
CLI 门禁验收使用独立临时 Git repo 与多个 CLI 子进程，不 import coop.py。
至少覆盖并发认领只有一个成功、revoke 后旧身份拒绝、错 session/fence/spec 拒绝、
新进程读取持久状态、未 verify 不能 integrate、坏候选 oracle_failed 不改变集成引用、
合法候选通过并恰好集成一次、验收后引用变化拒绝、事件保留所有拒绝。
真实 Herdr/Codex run 另外保留启动/投递/状态/交付/验收原始记录；模拟 Herdr 不能证明这一层。
Known-bad gate mutant 必须被行为断言拒绝，不能只因导入/环境错误报红。
CLI 测试可由 root 运行；实现者不得修改冻结契约或 acceptance 预期以刷绿。

## 运行与观察限制
先单个产品任务，开发最多两个 worker + 一个只读 monitor。观察每次有界采样，不 busy-poll。
一次 wait 超时只表示等待结束；有新文件/命令进展时继续，不强行中断正在完成的工作。
无进展才查阻塞/权限，并保存现场后处置。模型权限对话不得默许越过审批。
无数值费用上限时不自动扩大并发或重复大量模型运行。
本地 SQLite、Git 和同一用户权限保证受管入口正确性，不声称恶意 worker 不能绕过磁盘权限。

## 后续范围
消息持久邮箱、全生命周期 hook、心跳/租约、第二 CLI 和多任务组合集成在后续切片。
首轮实际运行是经验采集；收益需后续独立对照。
