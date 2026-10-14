# T-081 run-02 诊断与 run-03 待批交接

状态：**INCOMPLETE**。第 7 项尚无能力成功或拒绝的结果；按主控 #174，已消耗 **1/3**。本轮只读诊断、修测试脚本和生成审批材料，未启动新的 Codex、PTY 或 daemon，未提交、submit、改产品或清理 home。full-04 的受控矩阵 PASS 保留，不替能力观察背书。

## run-02 实际观察

原件保留在 [capability-run-02](capability-run-02/run.json)。只读诊断及逐条 SQL、命令清单在 [诊断结果](capability-run02-diagnosis-02/run.json)，可读终端片段在 [pty-text.txt](capability-run02-diagnosis-02/pty-text.txt)。原始 PTY 为 `capability-run-02/traces/0787d56c-abbe-4a64-97e0-5f31bda76316/pty.raw`，2,909 字节。

PTY 显示 v0.162.1、`[Pasted Content 2774 chars]`、`Waiting for startup`，随后进入 **Folder access**。界面原文包括：

```text
Note: You’re in a subdirectory of a Git project. Trusting will apply to the repository root:
/private/tmp/t081-capability-01/run-02/repo
Trust this folder?
1. Trust and continue
2. Quit
```

最后是停止时的 `zsh:1: warning: 1 jobs SIGHUPed`。本轮未向这个界面发送额外 Enter 或确认。文本视图仅移除终端控制序列，未模拟光标布局；某些词之间没有空格，以原始 PTY 为准。

隔离 home 的 SQLite 以 `mode=ro` 连接，查询范围只含线程元数据和日志聚合，不读取 `auth.json`、日志正文、令牌或账号字段，也不导出整个数据库：

| 来源 | 实际结果 | 可以得出的结论 |
| --- | --- | --- |
| `state_5.sqlite`（含现存 WAL） | `threads` 为 0 条 | 没有可读回的原生线程记录 |
| `logs_2.sqlite`（含现存 WAL） | 65 条；带 `thread_id` 的条目为 0 | 记录是启动范围的证据，不能作为命令回执 |
| 原生 session 文件与结果文件 | 无 `sessions/`；无 `probe-results.json` | 没有可提取的工具调用或退出状态 |
| 编排事件 | 各一次 `turn_submit_intent`、`turn_submitted`；没有 `pane_idle` 或 `native_record` | 产品记录了终端发送动作，尚无原生完成证据 |
| 引用读回 | repo main=G `4de60dac7fd4b9baebd5c5cb177267673f398d77`；隐藏 T 引用仍在；裸仓库无 refs | 保留观察到的引用状态，不据此补造执行结果 |
| 正常退出 | daemon 79995、shell 80088、Codex 80090 已确认退出 | 本次脚本停止与进程退出已完成 |

两条命令均记为 **INCOMPLETE：未发现执行回执**，`exit_code=null`、`refusal_text=null`。不能写成权限拒绝或退出 0。回合计数依主控裁定保持消耗 1，不因 SQLite 无线程而扣回。

启动材料的问题是只为父目录 `/private/tmp/t081-capability-01` 配置了信任；界面要求的是本次 Git 仓库根 `run-02/repo`。因此先修测试的精确信任配置，没有证据要求修改产品。OpenAI Docs 对 [`projects.<path>.trust_level`](https://learn.chatgpt.com/docs/config-file/config-reference) 的定义是指定项目或 worktree 的信任状态；本次所需根路径直接来自保存的界面，不从文档推测。

复查命令（必须使用新的输出目录；原始目录不覆盖；归档后从指针读取日志）：

```sh
python3 -B workbench/tests/diagnose_t081_capability_run02.py --output evidence/2026-10-14-batch14/T-081/capability-run02-diagnosis-next
```

首次诊断的展示断言把光标定位形成的词间隔当成连续空格，得到 AssertionError；原失败片段和说明保留在 `capability-run02-diagnosis-01/`。修正展示断言后另存 diagnosis-02，没有重启真实回合。

## 超限文件：外置归档脚本，交主控运行

只归档 `capability-run-02/commands.jsonl`，实际 **5,027,291 字节**。脚本为 [archive_t081_capability_run02.py](../../../workbench/tests/archive_t081_capability_run02.py)，本轮未执行真实归档。

```sh
python3 -B workbench/tests/archive_t081_capability_run02.py
```

固定目标：`/Volumes/WD-Elements/a2a-evidence/2026-10-14-batch14/T-081/capability-run-02/commands.jsonl`。必须真实挂载，无内置盘回退、无符号链接路径、无覆盖或自动重试。过程是独占创建外置原始文件 → fsync → 完整顺序逐字节读回比较（包括 EOF 与 5,027,291 字节）→ 本地指针及目录持久化 → 仅删除已验证一致的本地副本。其余 run-02 原件不动；失败保留现场。

指针为 `capability-run-02/commands.jsonl.external.json`，含外置路径、字节数、验证方式和时间。主控核对外置原件及指针后，run-03 才允许继续。脚本不压缩、不使用摘要、不访问 home。

## 轮询修正与离线证据

旧 `CommandLog` 为每次轮询同时保存原始 stdout 和完整 JSON，319 次 `pane_status` 加 319 次 `orchestration_events` 反复写入相同事件。本次只改能力运行脚本的轮询记录，其他受控矩阵和断言不变。

新 [PollEvidence](../../../workbench/tests/capability_poll_evidence.py) 仍经真实 CLI 查询；只保留初始状态、状态变化和每 30 秒一次采样。事件按 seq 完整保存一次。证据卷上限为 1,000,000 字节，达到上限前另开一卷；超大单条、乱序、命令失败等情况停止并报告。关键派发、release、停止及最终快照仍完整保存，不减少业务检查。

离线检查在 [capability-run03-check-01](capability-run03-check-01/green-final/run.json)：

| 检查 | 结果与范围 |
| --- | --- |
| 旧实现红态 | `red/run.json`：exit 1，`POLL-EVIDENCE-SIZE`；引用 run-02 真实超限原件 |
| 同一批 638 次响应回放 | `green-final/run.json`：exit 0；11 个事件完整且不重复；含变化和采样；21,028 字节 |
| 分卷边界 | 用 512 字节卷上限迫使 20 卷写入；内容完整，各卷未超限 |
| 外置归档逻辑 | 本地小夹具 262,403 字节逐字节一致、指针读回、已有目标拒绝覆盖；没有写外置盘或移动原件 |
| argv 审计 | `audit-allowed/` 允许原 argv、文本；`audit-rejected/` 在 PTY spy 前拒绝 tier 变化；禁用两处 argv 对比的 `audit-red-02/` 出现业务失败 `AUDIT-BLOCK-BEFORE-SPAWN` |

第一个归档小文件检查因测试 TMPDIR 的 `/var` 符号链接被路径保护拒绝，保留 `green/`；将小夹具路径规范化后使用 green-02；补齐归档目录持久化后同一检查仍通过，最终保留 green-final。第一个 argv 变异只关掉 record 比对，shell 比对仍拒绝；结果保留 `audit-red/`，不计作红态。有效反事实是明确关闭两处同一 argv 边界检查的 audit-red-02。所有 spy 的真实 Codex 回合数均为 0。

精确离线重跑命令（输出目录需新的）：

```sh
python3 -B workbench/tests/check_t081_capability_run03.py --mode legacy --output evidence/2026-10-14-batch14/T-081/check-next/red
python3 -B workbench/tests/check_t081_capability_run03.py --mode candidate --output evidence/2026-10-14-batch14/T-081/check-next/green
```

这些证据只证明记录器和审计边界，不证明真实信任提示已消失或第 7 项通过。独立验收仍由主控后续安排，不以同一作者的静态检查代替。

## run-03 完整材料：等待第 2 回合重新批准

新任务 `T-081-CAP-03`，新根 `/private/tmp/t081-capability-01/run-03/`，新输出 `capability-run-03/`。复用现存 home，不清理或重新复制 auth。旧 run-01、run-02 的仓库、state 和记录保留。

| 待审材料 | 路径 |
| --- | --- |
| 运行脚本 | [run_t081_capability_turn.py](../../../workbench/tests/run_t081_capability_turn.py) |
| 第一条完整提示词（实值路径及 G/T） | [FIRST-TURN.template.md](capability-review-03/FIRST-TURN.template.md) |
| 两条原文命令 | [ROLE-BODY.md](capability-review-03/ROLE-BODY.md) |
| Codex / zsh 完整 argv 与回合上限 | [launch-policy.first-turn.pending.json](capability-review-03/launch-policy.first-turn.pending.json) |
| 三个 CLI hooks 与 Git hooksPath 内容 | [hook-contents.json](capability-review-03/hook-contents.json) |
| 启动配置、任务卡 | [launch-config.pending.json](capability-review-03/launch-config.pending.json)、[task-card.pending.json](capability-review-03/task-card.pending.json) |
| 信任配置的逐字前后文本 | [home-trust.before.toml](capability-review-03/home-trust.before.toml)、[home-trust.after.toml](capability-review-03/home-trust.after.toml) |
| home 来源、预算、动态身份字段 | [review-metadata.json](capability-review-03/review-metadata.json) |

待批配置只更换信任路径，保留 CLI 自动写入的 TUI 检测标记；仅在新的批准运行内写入，先保存旧配置并读回。当前 home 未改变：

```toml
[projects."/private/tmp/t081-capability-01/run-03/repo"]
trust_level = "trusted"

[tui]
screen_reader_detection_done = true
```

新批准须覆盖这个配置变更、三个 CLI hooks、Git hooksPath 本次启用及一次第 2 回合。提议引用 **`T-081 controller-decision-03 capability-turn-2`**。该字符串目前只是待批标识，不能代替主控批准。准备材料中 approved=false、启动授权字段仍为 null。本轮没有创建 run-03 夹具。

批准后运行（当前不执行）：

```sh
python3 -B workbench/tests/run_t081_capability_turn.py --approval-ref 'T-081 controller-decision-03 capability-turn-2' --output evidence/2026-10-14-batch14/T-081/capability-run-03 --turn-timeout 600
```

脚本先核对归档、旧进程退出/端点、home 已知目录、空线程表、两条规则及现有配置，再创建独立仓库与裸仓库，应用本次精确信任项。产品真实入口仍生成原 argv：`gpt-6.1-sol`、xhigh、`service_tier="default"`、workspace-write、-a never；argv 和首条文本在 spawn/queue 前严格比对。仅四类 UUID 字段在产品认领时分配，随后逐字核对，不放宽检查。

最终脚本、链接、编码与地图状态证据在 `capability-run03-final-check-02/`。前一收尾检查发现 home 比初始 prepare 多了 CLI 自动写入的 TUI 标记，因此在配置一致性断言处停止；`capability-run03-final-check-01/` 保留，不当作真实回合失败，也未改 home。待批材料现以只读诊断保存的实际前配置为准，后配置保留相同标记。

真实回合最长 600 秒，超时或失败正常停止，不重试，不追加 Enter 或回合。仍要求产品匹配 Stop/idle/task_complete、原生终端工具回执、仓库/裸仓库 refs 和 PID 退出；不足则 INCOMPLETE。run.json 区分已消耗预算与已完成观察；发送结果未知时不写成消耗 0。home cleanup 仍需另批；现有 cleanup 脚本只检查最初 state，后续清理前还须覆盖各 run 的 PID 记录，本轮不运行。

T-081 RUN-02-DIAG READY
