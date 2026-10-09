---
id: T-053
title: 收件箱脚本：写、列、确认条目，列出时打印角色卡
type: build
status: closed
blocked_by: []
claimed_by: s8-t053
supersedes:
ready: yes
ready_by: ideation
ready_rev: 1
---

## What to build

Herdr 期两个主控之间的交接靠文件完成，格式和"哪些条目还没确认"不能靠模型记。做一个命令行入口 `scripts/inbox`（Python 3 标准库，无依赖）：

- `send --from FROM --to TO --kind KIND [--reply-to ID] [--ref REF]... [--title TEXT] [--blocking] (--body TEXT | --body-file PATH)`：按 [spec](../specs/controller-split-user-input-2026-10-09.md) 第 5 节的格式，在 `.project-map/inbox/` 写一条条目（一条一个文件，原子写入）。参数名以 `.project-map/roles/` 里角色卡的写法为准；如需改名，同步改角色卡并在 RESULTS 说明。
- `list --role ROLE`：先打印该角色在 `.project-map/roles/` 下的角色卡，再按时间升序列出收件人为该角色、且还没有该角色发出的 `ack` 的条目；问题上报按 spec 第 4 节的规则标出状态。`ROLE` 取 `ideation`、`executor`，以及只用于呈现的 `user`（"等你决定"的清单）。
- `ack --role ROLE --id ID`：写一条确认条目。
- `ready`：列出已获授权可执行的 ticket。

没有编辑或删除条目的命令。角色卡文件已由构思主控写好，本票只读取。

## Acceptance

- [x] 红态在先：入口不存在时，下面的端到端用例失败；保存失败输出与重放命令。
- [x] 并发：20 个进程在同一秒内各执行一次 `send`，恰好得到 20 个文件、20 个互不相同的 id，无丢失、无覆盖；写入中途被杀不留下半截条目。
- [x] 未确认判定：夹具覆盖——收件人已确认、未确认、收件人不同、同一条被两个角色各确认一次、确认来自非收件人（不算确认）、`reply_to` 指向不存在的条目。`list` 的输出与按 spec 第 5 节手写推导的清单逐条一致；确认后该条不再列出，原文件字节不变。
- [x] 只追加：不存在编辑或删除命令；用已存在的 id 再次 `send` 被拒绝（退出码 1），原文件不变；`--ref`、`--body-file` 指向不存在的文件或含路径穿越时被拒绝，且不留下文件。
- [x] 问题上报的派生状态：用注入的时钟验证——无处置且在判断期内显示"待判断"，超过判断期显示"等你决定"，`blocking` 的不经"待判断"；`disposition` 的 `close`、`dismiss`、`forward`、`snooze`、`reopen`、`delivered` 各自得到 spec 第 4 节规定的状态。判断期长度取 spec 里的常量，不在多处写死。
- [x] `ready`：夹具含至少 12 个 ticket——缺 `ready` 字段、`ready: no`、缺 `ready_by` 或 `ready_rev`（列为不合规，不算就绪）、依赖未解决、已认领、已关闭、superseded、out-of-scope、`decide` 类型、正常就绪的 build/task/research 等。输出与按 spec 第 5 节手写推导的清单一致。
- [x] 角色卡缺失时 `list` 报错退出 1，不静默跳过；上次会话副本超过 7 天时 `list` 多打印一行提醒（见 spec 第 3 节），没有任何会话副本记录时不提醒。
- [x] 在本仓库真实的 `.project-map/` 上运行 `ready` 与 `list`，git 工作区前后一致。
- [x] 已知坏实现被抓住：至少两个 mutant（文件名只用秒级时间戳；`ack` 不校验发送者）在上述用例上失败，保存记录。

## 说明

- 失败方式清单（实现与测试都对照它，处理方式写进 RESULTS）：并发同名；半截写入；同一条重复确认；确认来源伪造；`reply_to` 悬空；front matter 损坏的条目（跳过并在输出里列出，退出码非 0）；时钟回拨；非 UTF-8 正文；极长正文。
- 本票与 [T-054](T-054-dispatch-wrapper-and-session-copy.md)、[T-055](T-055-issue-report-tracer-bullet.md) 互不依赖，可并行。本票改动集中在 a2a 仓库的 `scripts/`，与 T-055 的 fork 改动没有共同文件。
- 授权来源：`ready_by: ideation`，`ready_rev: 1`。

## Resolution

2026-10-09，worker：**PASS；保持 open，待主控关闭**。依据 `ready_rev: 1`。

实现 `scripts/inbox`（Python 3 标准库）与真实 CLI 端到端测试。最终代码提交 `a4d502407e5d593300f84b2b82f899d0624f0949`（首刀 `251ce27694d28aef54079ab8c1bc691e7d5a4b0b`）；fork none；角色卡只读，无参数改名。

12/12 用例通过；20 进程同秒发送、实际短写后 SIGKILL、手写未确认清单、14 个 ready 夹具、处置时限、只读真实地图、两个 mutant 均有原始证据。唯一 fresh-context 审查对首刀为 FAIL，发现答复字段、类型引用和时区三项遗漏；新增用例先红后绿，原独立探针逐字重放 13/13，保留原 FAIL，不上调旧结论。

报告与重放命令：[RESULTS](../../evidence/2026-10-09-batch8/T-053/RESULTS.md)；独立审查：[REVIEW](../../evidence/2026-10-09-batch8/T-053/REVIEW.md)；完整版本绑定：[final-candidate](../../evidence/2026-10-09-batch8/T-053/final-candidate.json)。T-054 清单对接为 `evidence/*/sessions/manifest.jsonl` 的 `cutoff_at`；只用夹具验证，实际联合运行待 T-054。真实 ready 因旧 ticket 缺就绪字段退出 1，三种角色 list 退出 0，前后工作区与地图字节一致。

2026-10-09 执行主控决定 01 补验收：**PASS；仍待主控关闭**。代码 `8e260461f32e49c3b1bce50bedeceb4fad38aa8a`：只检查 open 的就绪字段，完全没有字段的旧 open ticket 列“未标就绪”，部分缺字段才报“不合规”。两个新用例先红后绿，14/14 通过；真实仓库由 52 行不合规、退出 1 变为 5 行未标就绪、0 行不合规、退出 0，3 条 READY 保留；每次只读运行前后 Git 状态和地图字节一致。[补验收报告](../../evidence/2026-10-09-batch8/T-053/decision-01-RESULTS.md) 保留全部输出与重放命令；fork none。

**执行主控关闭（2026-10-09）：PASS，依据 ready_rev 1。** 代码 `a4d5024`、`8e26046`，证据 `a868e01`、`e82dfff`，见 [交付记录](../../evidence/2026-10-09-batch8/T-053/RESULTS.md)。最终套件 12/12；两个 mutant（秒级文件名、ack 不校验发送者）被抓住；独立审查首轮 FAIL（信封遗漏三项）修复后重验。执行主控在真实仓库运行 `ready` 发现 52 行旧 ticket 的"不合规"噪声，按 [决定 01](../../evidence/2026-10-09-batch8/T-053/controller-decision-01.md) 改为只检查 open ticket、并区分"未标就绪"，先红后绿；现输出为 3 条 READY 与 5 条协议前的未标就绪任务。执行主控已用 `scripts/inbox ack` 写入实际条目。遗留：ack 也被列为未确认（spec 缺陷），由 T-060 处理。
