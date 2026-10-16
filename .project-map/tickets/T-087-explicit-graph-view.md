---
id: T-087
title: 把 ticket 生命周期与门禁检查串画成一张显式的图（只作展示，不新增执行引擎）
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

用户 2026-10-15 看到"Graph Engineering"（把 Agent 循环、确定性程序、人工审批组织成显式执行图：节点是能力，边是路由与依赖，结构化状态沿边传递并在关键边界持久化），认为和 a2a 现在做的很像，要求为"把隐式的图画显式"开一张 ticket。概念来源只有用户转述的一句话，原文未核对。

本票交付一张**从真实来源推出来的**图，不是设计稿：

- 节点分三类，沿用现有说法：确定性步骤（门禁检查串里的每一关、四个门禁点 claim/submit/acceptance/integration）、agent 会话（worker、reviewer、monitor、两个主控）、人工决定点（T-004 停止条件、授权引用）。
- 边取自：ticket 的 `blocked_by`/`ready`/`ready_by`、收件箱条目类型、任务卡检查串顺序、门禁的拒收码与恢复路径。
- 持久化边界：标出哪些边上状态落库或落盘（CAS、fence、attempt 绑定、launch 记录），哪些边没有持久化。
- 每个节点和每条边写明来源（文件:行 或 ticket），查不到来源的不画实线，标成"隐式/靠主控判断"。这一类就是本票的主要发现：现在由主控凭判断完成的路由。

## Acceptance

- [x] 图的每个节点与边都有来源引用；抽查由不写图的会话完成（至少门禁检查串的顺序与拒收码对照 `workbench/src/gates/`，不读图作者的说明）。
- [x] 单列"隐式边"清单：哪些路由只靠主控判断，各自出错时的后果，以及 T-081（误拒）、T-082（完成条件够不够格）各覆盖了其中哪几条、没覆盖哪几条。
- [x] 产物是一份带图的文档加生成它的命令或脚本；来源变化后图能重新生成并 diff，不是手画一次。
- [x] `project_map.py status` 0 problems；没有 stale living doc。

## 不做

- 不做通用图执行器、不做策略引擎、不让图去驱动派发（见 `feedback-prompt-first-permissions`：提示词管判断，脚本管事实）。
- 不改工作台界面、不改 `workbench/src/`；是否把图放进工作台任务视图，等图出来、用户看过后另开票。
- 不把"Graph Engineering"写进 `CONTEXT.md`。术语处理见下。

## 术语（未决，本票内决定）

"节点"会同时指"门禁检查的一关"和"一个 agent 会话"，违反统一术语（同一概念不并列两个名字、一个词不指两样东西）。先用现有词（门禁检查、agent 会话、人工决定点）作图；图画完后，如果确实需要"节点/边"作总称，再在本票里一次定下含义并更新 `CONTEXT.md`，不在代码和文档里各自发明。

## 说明

- 来源：用户 2026-10-15 对话，构思主控建票；2026-10-16 用户说（逐字，会话"a2a-构思主控"）："T-088 的六条细节和 T-087开工"，构思主控据此标就绪（`ready_rev: 1`）。这张是只读分析，不改产品代码；Codex 并行上限 3 仍有效，由执行主控安排。
- 写入范围（预期）：新文档与生成脚本放 `findings/` 或 `.project-map/` 下，由执行时定；不碰 `workbench/`。

## Resolution

2026-10-16，执行主控。

PASS。产物 [findings/ticket-gates-graph-2026-10-16.zh-CN.md](../../findings/ticket-gates-graph-2026-10-16.zh-CN.md) 与生成脚本 `findings/generate_t087_graph.py`（`--check` 做来源引用存在性检查；main 上重生成与提交全文一致，68 条连接、241 行来源索引）。12 条隐式边单列，含后果与 T-081/T-082 覆盖/未覆盖。来源抽查由三个不写图的 fresh Codex 会话完成：01 NO_GO（未知结果暂停、审查协议暂停、model unknown 例外）、02 NO_GO（R2 统一 issue 断言）、03 PASS（`evidence/2026-10-16-batch16/T-087/source-spot-check-0{1,2,3}.md`）。合入 main 8cd707878；打分 score-b90a6e539f1f4fc2b8d6966f9f7fd3cc。

术语：图里用现有词（门禁检查、agent 会话、人工决定点）和一般说法"点/连接"，不需要"节点/边"总称，CONTEXT.md 不改。是否把图放进工作台任务视图，按"不做"一节等用户看过后另开票。
