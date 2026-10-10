---
id: T-074
title: 先核实两个事实：Codex 的"等确认"信号，往窗格注入文字是否稳定
type: build
status: open
blocked_by: []
claimed_by:
supersedes:
ready: yes
ready_by: ideation
ready_rev: 1
---

## What to build

[spec](../specs/native-cli-orchestration-2026-10-10.md) 第 12 节切片 S1 的第 0 步，单独成票。第 13 节的风险 R6、R7 由执行主控负责，结论可能让方向停下，所以先于 tracer bullet（[T-075](T-075-tracer-bullet-daemon-gate-pane.md)）核实。只出事实报告与探针，不写产品代码。

- **R6**：Codex CLI（固定版本）在等用户确认（命令批准、补丁批准等）时，有没有能被外部程序拿到的结构化信号，例如 `notify`、hooks、OSC 序列、rollout 记录里的事件。Claude Code 对应的 hooks 与 OSC 7501 一并核实一次。
- **R7**：在 node-pty 托管的 zsh 窗格里运行交互式 Claude Code 与 Codex，从外部往 PTY 写一行带 `⟦主控 #序号⟧` 标记的文字再回车，CLI 能否稳定把它当作一条新的用户消息，包括 CLI 正在运行回合时、空闲时、正在等确认时。

## Acceptance

- [ ] 每个结论标 observed / measured / inferred / unknown，附原始输出、CLI 版本、启动 argv 和重放命令。
- [ ] R6：至少触发一次真实的等确认状态（Codex 一次，Claude 一次），记下外部程序收到了什么、在什么时刻收到；没有信号就写"未找到"并列出查过的途径，不改用读屏或正则。
- [ ] R7：两家各至少 10 次注入，覆盖空闲、回合进行中、等确认三种状态；记成功次数、失败的样子（丢字、拼进上一条、被当作确认的回答等）。设计成功率门槛之前先把原始次数报上来，门槛由构思主控与用户定。
- [ ] 注入的文字在写入前登记（spec 第 6 节），探针能把登记与 CLI 实际收到的对上。
- [ ] 结论写成 `findings/` 下的中文报告，报告里写明对 T-075 的影响：可以按 spec 做、要改设计、或要停下。
- [ ] 任一项不通过：停下写 `needs-decision` 交构思主控，不硬做、不加兜底重试，不开始 T-075。

## 说明

- 失败方式清单（处理方式写进 RESULTS）：CLI 启动时的更新提示或信任目录提示挡住输入；注入时 CLI 正在渲染导致字符交错；中文与标记字符的编码；多行文字被拆成几条消息；粘贴模式（bracketed paste）开关不同；等确认时注入的文字被当作确认的回答（这是危险情况，必须单独记）。
- 真实模型调用：Codex 按 AGENTS.md 用隔离 `CODEX_HOME`，turn 数尽量少；Claude Code 用不写 `~/.claude` 的方式启动（例如独立的配置目录与 `--settings`），认证方式拿不准时先停下问，不动用户的全局配置。启动参数里固定 `check_for_update_on_startup=false`。
- 探针代码放证据目录，不进产品目录；node-pty 可以在证据目录里临时装，依赖缓存放外置盘（AGENTS.md 构建规则）。
- 与 [T-073](T-073-herdr-period-task-card-trailers-scoring.md) 改的文件不重叠，可以并行。
- 授权来源：用户 2026-10-10 在会话"a2a-构思主控"确认切法（逐字："确认"），在此之前在会话"新思路构思"说："确认，写完文档后，你这边就不用了，全权交给构思主控去安排执行主控安排子 agent 去做。"`ready_by: ideation`，`ready_rev: 1`。

## Resolution
