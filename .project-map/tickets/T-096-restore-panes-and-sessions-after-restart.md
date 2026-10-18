---
id: T-096
title: 工作台重启后恢复之前打开的窗格与对应会话（按记录的启动参数续接，不用裸 resume）
type: build
status: closed
blocked_by: []
claimed_by:
supersedes:
ready: yes
ready_by: ideation
ready_rev: 1
---

## What to build

用户 2026-10-17 说（逐字，会话"a2a-构思主控"）："重启后继续之前对话打开的面板与相应的会话这个是应该的，不然我每次都要重新打开，手动输 resume 很麻烦"。

机器或工作台重启后，用户之前打开的窗格与其 agent 会话应自动回来：窗格按"项目 → 任务 → agent 会话"的归属重新排好，每个会话按**启动记录里保存的完整 argv** 续接原会话。

背景（事实）：2026-10-17 机器重启后，Herdr 自动用不带参数的 `codex resume` 恢复了 worker（PID 7209），模型、思考强度、沙箱都没有记录；执行主控关掉它，改用 `launch-worker --resume` 重接（launch-97cdf0bc…）。本票要让工作台的恢复路径不重蹈这个问题。

1. 工作台保存"当前打开的窗格集"：每个窗格的 task、role、launch id、session id、窗格位置；写入时机明确（窗格创建/关闭时落盘，不靠退出时钩子）。
2. 重启后恢复：对每个窗格按启动记录的 argv（含模型、思考强度、沙箱、service tier）续接原 session；CLI 实际版本与记录不符、启动记录缺 argv、session 已不存在的，**明确报错并保留该窗格为"未恢复"**，不静默换配置或开新会话。
3. 恢复本身不产生模型回合；用户输入前不调用模型。
4. 沿用 T-091 的多窗格与 T-093 的 profile 记录，不另造一套状态。

## Acceptance

- [x] 红态：当前 `main` 上重启后窗格集为空、不会自动续接（读回现状）。
- [x] 绿态：用假 API 起三个窗格，杀掉整个后台与 Electron，重启后三个窗格回来，各自进程身份、task、role、launch 与 argv 与重启前记录一致；模型回合 0。
- [x] 反例（每个在真实入口失败并保留现场）：启动记录缺 argv；CLI 版本与记录不符；session 已不存在；某窗格恢复失败不影响其余窗格，且不被记成"已恢复"。
- [x] 不得用裸 `resume` 或默认配置补位；恢复后的 argv 与记录逐字段相等。
- [x] 不改 Herdr，不写 `~/.claude`、`~/.codex`。
- [x] `project_map.py status` 0 problems。

## 说明

- 构思主控据用户上述原话建票并标就绪（用户说"这个是应该的"，未单独说"开工"；若不对请撤回）。无真实模型回合，不触及 T-004 停止条件。
- 写入范围预期：`workbench/src/`、`workbench/app/`、`workbench/tests/`、本票证据。

## 裁定（2026-10-18）

执行主控 needs-decision：受管 worker 续接原会话后拿到新的 shell 与 leader PID，门禁 `checkThread()`（core.ts:2485）要求 PID 与绑定时完全相同且无重绑定入口，恢复后的 worker 交付会被拒。用户选"B: 只恢复主控窗格，worker 需重新认领 (Recommended)"，选项原文："主控窗格自动回来（这是你每天要用的）；worker 窗格恢复后标为“未恢复”，重启中断的任务按现有的中断恢复语义 reclaim 后开新 attempt。不改门禁，风险最低。代价：重启时正在跑的 worker 不会无缝续上，要重新认领。"

据此范围收窄：本票只恢复主控窗格并按记录的启动参数续接；worker 窗格恢复后显示"未恢复"，不自动续接、不重绑定、不改门禁语义。Acceptance 中三窗格恢复一条改为"两个主控窗格恢复、worker 窗格显示未恢复且其 attempt 状态未被改动"。

## Resolution

2026-10-18，执行主控按门禁验收 **PASS**（按用户裁定 B 的收窄范围），合入 main，不 push。冻结候选 `17a8ec8f20b97b732ad561c4fa02213a4f0e23f7`（exec/t096）；之后的 `ef8bcd32d` 只补审查记录，并按审查 02 的 P3 修订 README。

- **产品**：窗格集在创建、关闭时落盘，能区分"从未保存"和"已保存的空集"。主控窗格重启后按启动记录里的完整 argv 续接原会话；启动时实际核对 CLI 版本，argv 逐字段相等。worker 窗格显示"未恢复"，不启动、不重绑定，门禁 attempt 不变，不改 `workbench/src/gates/`。只有能证明已经死掉的旧端点才允许重启。缺 argv、版本不符、session 不存在时，该窗格明确报错并保持"未恢复"，不影响其余窗格，也不会出现 `pane_restored`。
- **真实运行**（真实 daemon、Electron、Claude 2.1.302，假 API，模型回合 0）：red-b-05（main 的死端点阻止重启，属真实红态）；tracer-b-05；three-b-01；no-argv-b-02；version-b-02；no-session-b-01；isolation-b-01；empty-reopen-b-01（关闭全部窗格后重开，界面为空，不会重新加入 worker）。原件在外置盘 `a2a-evidence/2026-10-16-batch16/T-096/`。早先失败的各轮原件保留：-01～-04 是 runner 缺陷，no-argv-b-01 是主控截屏过早，version-b-01 是窗口身份核对失败。
- **初始化按键**（主题、须知、信任目录）每个主控 6 键，加一次空队列就绪放行，全部由执行主控逐屏批准，key 记录与批准文件一一对应。用配置跳过初始化屏另由 T-099 处理（未就绪）。
- **独立审查**：01（launch-e85f83034c434d1598e0f71d7f61b999）NO_GO，查出关闭最后一格后重开会把 worker 加回来；修复后 02（launch-19aa7b10ff5d4947a7e238c29a0e83dd）**PASS**，三个变异均被业务断言拒绝；P3 README 矛盾已在合入前修正。
- **过程**：worker 首轮发现门禁 `checkThread()` 要求 PID 不变、没有重绑定入口，因此停下上报（needs-decision `20261018T020829Z`），用户裁定 B。期间两次请求提权，均被主控拒绝，改为写成脚本交主控运行。
- 打分 `score-7b0c0185dcf94382b789b904093cd7fb`（边界 3、工程 2）。
