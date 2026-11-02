---
id: T-236
title: 项目终端里启动 Claude Code 没有任何输出：它的全屏渲染器在 Enchanted 终端里起不来
type: build
status: open
blocked_by: []
claimed_by:
supersedes:
ready: yes
ready_by: executor
ready_rev: 1
---
## What to build

2026-11-02 Computer Use 实测发现（`evidence/2026-11-02-batch30/cu-bugsweep/BUGS.md`、`BUGS-r2.md`，截图 `shots/r2-claude-no-output.png`）：在隔离的 Enchanted（HEAD `2b3b12dac` 打包）项目终端里运行 `claude --model claude-haiku-5-5`，3 次都是 5～7 分钟只显示命令行、没有界面也没有报错，进程还在。

主控随后在 Claude Code 桌面应用的普通终端里，用同一个插件目录启动 Claude，Claude 先打印：上次在这台机器上 fullscreen renderer 没能启动完成，这次改用 classic renderer，下次还会再试 fullscreen。所以无输出就是全屏渲染器在 Enchanted 终端（私有 hc core + xterm.js）里启动卡住。复盘那次 Claude 有界面，是因为它是紧接着失败之后的那次启动，自动退回了经典渲染器。

推测（未核实）：全屏渲染器启动时向终端发了某个查询（设备属性、尺寸、键盘协议等），hc 或 xterm.js 这一层没有回应。要查清是哪个查询、该由哪一层回应，修在根因处；不靠让用户改 Claude 的 `/tui` 设置（那会写 `~/.claude`）。

## Acceptance

- [ ] 先写下可能出错的方式。
- [ ] 修前红态：项目终端里 Claude 首次启动无输出，记下终端收到但没回应的序列。
- [ ] 修后：项目终端连续多次启动 Claude（每次都走全屏渲染器）都出界面；受管 worker、复盘窗格同样。
- [ ] 独立审查（GPT 只读，新开干净会话）无未处理的阻塞意见。

## Resolution

（未开始）
