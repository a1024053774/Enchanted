---
id: T-075
title: tracer bullet：编排后台、门禁、Codex worker 窗格、最小 Electron 窗口跑通一次交付
type: build
status: open
blocked_by: [T-074]
claimed_by:
supersedes:
ready: yes
ready_by: ideation
ready_rev: 2
---

## What to build

[spec](../specs/native-cli-orchestration-2026-10-10.md) 第 12 节切片 S1（第 0 步已拆到 [T-074](T-074-pane-signal-and-injection-facts.md)）。穿过每一层跑通一条最薄的、留在生产路径上的完整路径，之后的切片在它上面加宽：

1. **编排后台**：常驻进程，脱离调用者的进程组；对外一个本地命令行入口，主控、worker 和界面都经它。
2. **门禁进后台**：从 fork 的 `packages/a2a-gates` 搬进来，替换两处 Synara 依赖；契约不变，加上 T-070 同意的改动中本切片需要的三项：路径边界检查、提交尾注核对、集成目标改为项目工作分支。搬完后 fork 的门禁不再作入口，`acceptance/entry/a2a_gates.py` 改指新位置，不保留两套路径。
3. **任务卡**：命令生成与校验（缺字段、完成条件不是命令就拒收），存进后台库，门禁在任务注册时快照。
4. **一个 Codex worker 窗格**：node-pty 托管、窗格里跑用户的 zsh，带启动记录与 spec 第 5 节的环境变量（提交带尾注）；派发文字以 `⟦主控 #序号⟧` 写进窗格并登记。
5. **一次交付**：认领、交付、机械检查（路径、完成条件、尾注）、验收、CAS 集成到夹具仓库的工作分支，不 push。
6. **原始事件入库**：spec 第 8 节清单里本切片涉及的事件全记，只追加。
7. **最小 Electron 窗口**：从 fork 搬组件与样式（保留 MIT 声明），显示一个项目、一个任务、一个窗格（xterm.js）和门禁状态。

## Acceptance

- [ ] 检查面（用户 2026-10-10 确认）：从编排后台的命令行入口发起，驱动真实窗格里的真实 Codex worker（隔离 `CODEX_HOME`，turn 数尽量少），对夹具仓库走完整个门禁。证据：命令与输出、从库里读回的事件、Git 引用读回、Electron 截图。
- [ ] 正例：上面一次交付集成成功，工作分支从 G 前进到 M，事件齐全，候选提交带本 attempt 的尾注。
- [ ] 反例，各自在真实入口上被拒且留下事件：改了任务卡禁止路径；完成条件命令失败；候选里有别的任务的尾注；没有尾注的提交记为人工介入并标"推断：缺尾注"；过期 fence 或旧 attempt 交付。
- [ ] 门禁移植重新证明：交付 8 项、恢复 9 项、编排 18 项场景在新位置重新取得红态、绿态与反例；旧实现的通过结论不替新实现背书。
- [ ] 后台常驻：关掉 Electron 窗口后 worker 窗格照常跑，重开窗口能重新接上；后台重启后按恢复语义处理进行中的 attempt。
- [ ] 窗格状态只来自结构化信号（按 T-074 的结论），拿不到的显示"未知"，不读屏。
- [ ] 外置盘未挂载时构建报错，不回退到内置盘；工作台数据目录在内置盘，路径在 RESULTS 写明。
- [ ] 不写 `~/.claude`、`~/.codex`；不改用户的 Herdr server 与正式工作台数据目录 `~/Library/Application Support/a2a-workbench`。
- [ ] 每项保留产物与重新生成的命令；`project_map.py status` 0 problems。

## 说明

- 本票不做（后续切片）：独立审查会话、红态检查与规则式检查、打回回写（S2）；worktree 命名清理与冲突回写（S3）；主控窗格、收件箱进库、唤醒（S4）；面板、通知、设置页（S5）；复盘与指标视图（S6）。路径检查与尾注核对要做，因为它们属于门禁本身。
- 新目录名、数据目录路径、Electron 与 node-pty 版本由执行主控定，记进 RESULTS；新目录建议 `workbench/`。
- 体量大：执行主控可以拆成几张任务卡串行做，同一文件只给一个写入者；不必再拆票。目标、验收或设计级的问题停下写 `needs-decision`。
- worker 窗格按 spec 第 6 节"批准与派发分开"一条启动：审批设为不问，派发用 bracketed paste 后单独回车（T-074 实测）。
- T-074 的结论要求改设计时，本票等构思主控出 `revise` 再开工。
- 风险 R8（主控常直接提交 `main` 导致 CAS 反复落空）在本切片只用夹具仓库，不处理上限，留给 S3。
- 授权来源：用户 2026-10-10 在会话"a2a-构思主控"确认切法与检查面（逐字："确认"），在此之前在会话"新思路构思"说："确认，写完文档后，你这边就不用了，全权交给构思主控去安排执行主控安排子 agent 去做。"`ready_by: ideation`，`ready_rev: 1`。

## Resolution

T-075-1：门禁迁移、隔离验收和一次 fresh-context 独立审查均 PASS；收尾状态 INCOMPLETE，仅剩执行主控已接管的 CONTEXT.md stale。保持 open，待后续卡、待主控关闭。

- 源码候选：`4d81efcacdaa6f8d9cf2b6127130fd7f0f0ac754`，自动 `A2A-*` 尾注已核对；来源固定为 `49cae984f22924de006e0f8358cb447eb881aaf6`。
- 新门禁位于 `workbench/`，Node 26.5 原生 TypeScript；验收入口改到新位置，不依赖 fork 门禁。按主控决定删除旧 HTTP 转接，保留 GateRuntime 边界，未改 T-075-2 的三项契约。
- 三套红态已保存；最终交付 8/8、恢复 9/9、隔离编排 18/18 全过，CAS 补充正例 1/1 全过。fence、CAS 期望旧值、操作锁三个变异体均因业务断言失败；旧交付套对 CAS 变异体误过的记录保留。
- 审查原文及重现命令见 [RESULTS](../../evidence/2026-10-10-batch12/T-075/RESULTS.md)；独立审查对上述候选给出 PASS，无需修复项。此结论不证明真实窗格、模型、后台或 Electron 可用。
- 地图检查为 0 problems、1 stale，退出 1；按执行主控决定 01 由主控更新术语表及 Verified，worker 未越界修改。完成该收尾后可将本卡记为“T-075-1 完成，待后续卡”。
