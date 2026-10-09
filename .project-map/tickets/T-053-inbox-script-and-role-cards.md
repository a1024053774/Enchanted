---
id: T-053
title: 收件箱脚本：写、列、确认条目，列出时打印角色卡
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

Herdr 期两个主控之间的交接靠文件完成，格式和"哪些条目还没确认"不能靠模型记。做一个命令行入口 `scripts/inbox`（Python 3 标准库，无依赖）：

- `send --from FROM --to TO --kind KIND [--reply-to ID] [--ref REF]... [--title TEXT] [--blocking] (--body TEXT | --body-file PATH)`：按 [spec](../specs/controller-split-user-input-2026-10-09.md) 第 5 节的格式，在 `.project-map/inbox/` 写一条条目（一条一个文件，原子写入）。参数名以 `.project-map/roles/` 里角色卡的写法为准；如需改名，同步改角色卡并在 RESULTS 说明。
- `list --role ROLE`：先打印该角色在 `.project-map/roles/` 下的角色卡，再按时间升序列出收件人为该角色、且还没有该角色发出的 `ack` 的条目；问题上报按 spec 第 4 节的规则标出状态。`ROLE` 取 `ideation`、`executor`，以及只用于呈现的 `user`（"等你决定"的清单）。
- `ack --role ROLE --id ID`：写一条确认条目。
- `ready`：列出已获授权可执行的 ticket。

没有编辑或删除条目的命令。角色卡文件已由构思主控写好，本票只读取。

## Acceptance

- [ ] 红态在先：入口不存在时，下面的端到端用例失败；保存失败输出与重放命令。
- [ ] 并发：20 个进程在同一秒内各执行一次 `send`，恰好得到 20 个文件、20 个互不相同的 id，无丢失、无覆盖；写入中途被杀不留下半截条目。
- [ ] 未确认判定：夹具覆盖——收件人已确认、未确认、收件人不同、同一条被两个角色各确认一次、确认来自非收件人（不算确认）、`reply_to` 指向不存在的条目。`list` 的输出与按 spec 第 5 节手写推导的清单逐条一致；确认后该条不再列出，原文件字节不变。
- [ ] 只追加：不存在编辑或删除命令；用已存在的 id 再次 `send` 被拒绝（退出码 1），原文件不变；`--ref`、`--body-file` 指向不存在的文件或含路径穿越时被拒绝，且不留下文件。
- [ ] 问题上报的派生状态：用注入的时钟验证——无处置且在判断期内显示"待判断"，超过判断期显示"等你决定"，`blocking` 的不经"待判断"；`disposition` 的 `close`、`dismiss`、`forward`、`snooze`、`reopen`、`delivered` 各自得到 spec 第 4 节规定的状态。判断期长度取 spec 里的常量，不在多处写死。
- [ ] `ready`：夹具含至少 12 个 ticket——缺 `ready` 字段、`ready: no`、缺 `ready_by` 或 `ready_rev`（列为不合规，不算就绪）、依赖未解决、已认领、已关闭、superseded、out-of-scope、`decide` 类型、正常就绪的 build/task/research 等。输出与按 spec 第 5 节手写推导的清单一致。
- [ ] 角色卡缺失时 `list` 报错退出 1，不静默跳过；上次会话副本超过 7 天时 `list` 多打印一行提醒（见 spec 第 3 节），没有任何会话副本记录时不提醒。
- [ ] 在本仓库真实的 `.project-map/` 上运行 `ready` 与 `list`，git 工作区前后一致。
- [ ] 已知坏实现被抓住：至少两个 mutant（文件名只用秒级时间戳；`ack` 不校验发送者）在上述用例上失败，保存记录。

## 说明

- 失败方式清单（实现与测试都对照它，处理方式写进 RESULTS）：并发同名；半截写入；同一条重复确认；确认来源伪造；`reply_to` 悬空；front matter 损坏的条目（跳过并在输出里列出，退出码非 0）；时钟回拨；非 UTF-8 正文；极长正文。
- 本票与 [T-054](T-054-dispatch-wrapper-and-session-copy.md)、[T-055](T-055-issue-report-tracer-bullet.md) 互不依赖，可并行。本票改动集中在 a2a 仓库的 `scripts/`，与 T-055 的 fork 改动没有共同文件。
- 授权来源：`ready_by: ideation`，`ready_rev: 1`。

## Resolution
