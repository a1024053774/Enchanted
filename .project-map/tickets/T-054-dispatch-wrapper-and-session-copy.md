---
id: T-054
title: 派发包装、派发日志与会话副本
type: build
status: open
blocked_by: []
claimed_by: s9-t054
supersedes:
ready: yes
ready_by: ideation
ready_rev: 1
---

## What to build

Herdr 期要做到两件事：一是把"执行主控发给 worker 的文本"和"用户亲手打的字"在记录里分开；二是保住会被清理的原生会话文件。做两个入口：

- `scripts/dispatch`：执行主控发给 worker/reviewer/monitor 的每段文本都经它。它在文本前加标记 `⟦主控 #序号⟧`，对该 agent 在本批的第一条提示词附上对应的角色卡，把时间、目标、角色、发出的全文和 Herdr 的退出码追加进该批的 `evidence/<批次>/dispatch.jsonl`，再调用 `herdr agent prompt`，原样返回其输出与退出码。不重试，不改写 Herdr 的错误。
- `scripts/session-copy`：把指定的 Codex 原生会话文件（worker）和 Claude 对话文件（构思主控、执行主控）中"上次复制之后新增的字节段"复制进 `evidence/<批次>/sessions/`，并写清单（会话 id、来源路径、起止字节、截止时间、大小）。只复制，不解析内容。副本不进 git，清单进 git。

另给出一份只放行包装的权限规则建议，写成文件，待用户批准后才应用。设计见 [spec](../specs/controller-split-user-input-2026-10-09.md) 第 3、6 节。

## Acceptance

- [ ] 红态在先：入口不存在时，下面的用例失败；保存失败输出与重放命令。
- [ ] `dispatch` 经真实入口，对一个明确标注为替身的 `herdr` 命令（记录收到的参数与文本，可按用例返回成功、`agent_blocked`、非零退出）覆盖：序号在并发下不重复；本批第一条提示词附角色卡，后续不附；日志里的全文与替身收到的文本逐字一致；Herdr 失败时日志记退出码、包装返回同一退出码、不重试；文本含多行、引号、`⟦⟧` 本身时不被破坏。
- [ ] 下一次真实派发用包装发出首条提示词，保存日志作为真实入口证据；不改动用户的 Herdr server。
- [ ] `session-copy`：夹具覆盖——首次复制、追加后再次复制（只复制新增字节，起点等于上次终点）、来源变短（拒绝并报告，不覆盖已有副本）、来源缺失、同一会话跨两个批次接续。清单的范围首尾衔接、无重叠无空洞；`git check-ignore` 与 `git status` 证明副本被忽略、清单被跟踪。
- [ ] 权限规则建议文件列出要放行和要拒绝的命令模式及理由，标明"待用户批准后应用"；本票不修改任何 Claude Code 设置。
- [ ] 已知坏实现被抓住：忘记加标记的 mutant、覆盖日志而非追加的 mutant、复制时重叠一段字节的 mutant，保存记录。
- [ ] 不解析会话内容，不对文本做模式匹配来判断来源；来源只认标记与日志。

## 说明

- 失败方式清单（处理方式写进 RESULTS）：`herdr` 不在 PATH；agent 名不存在；日志目录不存在；并发追加交错；磁盘写满；来源文件被轮转或截断；清单被手工改坏。
- 从 agent 定位其 Codex 原生会话文件的方式由本票查明并写入 RESULTS（`herdr agent get` 的输出、Codex 会话目录），不要凭记忆写死路径。Claude 对话文件在 `~/.claude/projects/<项目目录>/<会话 id>.jsonl`，按默认保留期会被清理，所以复制要在保留期内做（spec 第 3 节）。
- 本票可以修改 `.gitignore` 以忽略 `evidence/**/sessions/`。
- 与 [T-053](T-053-inbox-script-and-role-cards.md)、[T-055](T-055-issue-report-tracer-bullet.md) 互不依赖，可并行。
- 授权来源：`ready_by: ideation`，`ready_rev: 1`。

## Resolution

2026-10-09，worker `s9-t054` 交付，**INCOMPLETE（整票），待主控关闭**。

- 已实现 `scripts/dispatch`、`scripts/session-copy` 与共用的持久追加操作；权限建议文件只供审阅，未修改任何 Claude Code 设置。
- 六项入口缺失红态保留；完整 CLI/文件系统契约 8/8 PASS；忘记标记、覆盖日志、重叠复制三个 mutant 均被拒绝。只读复制当前 worker 的 Codex 与执行主控的 Claude 原生会话；副本忽略、清单提交。
- [中文交付与用法](../../evidence/2026-10-09-batch9/T-054/RESULTS.md)、[反例记录](../../evidence/2026-10-09-batch9/T-054/counterexamples-01.json)。冻结候选版本与 fresh-context 审查随证据提交。
- 冻结候选 `b32fbc8375bb9d757d93a2e6b8d91439a2afcd2f` 的 [独立审查](../../evidence/2026-10-09-batch9/T-054/independent-review.md) 返回 INCOMPLETE（真实派发证据未完成）；未确认行为违规或结构绕过，worker 本地范围可判 PASS。
- 任务书明确由执行主控在交付后完成“下一次真实派发”；worker 没有向真实 pane 发送文本。该验收项未完成，不关闭 ticket，不把替身 PASS 上调为整票 PASS。
