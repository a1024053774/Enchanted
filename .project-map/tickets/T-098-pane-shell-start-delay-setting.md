---
id: T-098
title: pane 里 shell 就绪后再等一个可设置的启动延时才输入命令（软件设置里的下拉框）
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

背景（执行主控 issue `20261018T020010Z`，blocking）：新 pane 里 oh-my-zsh 初始化时弹出 "Would you like to update? [Y/n]"，T-094 的"前台连续 1500ms 只剩 shell"判据被骗过（前台只有 zsh 自己），codex 命令被打进提问；这次首字母 `c` 被吞掉，若首字母是 `y` 或回车就会替用户应答。

用户 2026-10-18 裁定（逐字，会话"a2a-构思主控"，AskUserQuestion 的自由作答）："尽量还是跑和我一样的 zsh 吧，或者你看我的 zsh 启动要加载那个时间能优化吗？不能优化的话， 就设个启动延时？这个延时最好在软件设置里有个下拉框能手动改，比如 2s,3s 的"。据此：pane 继续跑用户的 zsh（"窗格里跑用户的 zsh"约束不变）；不改成 `zsh -f` 或命令式启动。

1. 软件设置里加"pane 启动延时"下拉框，选项如 无、1s、2s、3s、5s；设置持久保存，默认值执行时按本机 zsh 实测定（构思主控的测量：本机 `zsh -i -c exit` 约 0.7 s，首次/高负载可到 1.7 s 以上）。
2. 启动命令的时序：T-094 的就绪判据（前台连续 1500ms 只剩 shell）照旧，**之后**再等所选延时才输入命令；两者都满足才输入。
3. 延时只降低被提问骗过的概率，不是消除：文档与设置旁的说明要如实写这一点。更换已知提问源（用户自己的 `~/.zshrc`）是用户的事，不由本票改。
4. 启动后核对 pane 回显（执行主控现行做法）保持，不因本票放宽。

## Acceptance

- [ ] 红态：当前 `main` 上没有该设置；用夹具 zsh（启动中弹出 `[Y/n]` 提问并延迟若干秒）复现命令被提问吞掉的首字符，保留读屏原件。
- [ ] 绿态：延时大于夹具提问窗口时命令完整到达 shell；设置重启后保留；下拉选项与存储值一致。
- [ ] 反例：延时选"无"时仍复现被吞（证明延时才是起作用的因素，不是巧合）；非法设置值被拒绝、不静默回落成默认。
- [ ] 文案如实说明"降低概率不是消除"。
- [ ] 不改用户的 `~/.zshrc`、`~/.claude`、`~/.codex`；不改 Herdr。
- [ ] `project_map.py status` 0 problems。

## 说明

- 构思主控据用户上述原话建票并标就绪。写入范围预期：`workbench/src/`、`workbench/app/`、`workbench/tests/`、`scripts/launch-worker`（若 Herdr 期启动器同样适用，执行时判断，两处不分叉）。
- 本机 `~/.zshrc` 的 oh-my-zsh 更新模式（第 38 到 40 行）都是注释状态，默认会提问；改成 `zstyle ':omz:update' mode reminder`（或 `disabled`/`auto`）可消除这个已知提问源，**是用户自己文件里的改动，需用户同意**，未做。

## Resolution

2026-10-18 关闭，**未实现**（决定类收尾，无运行证据）：用户在构思主控提示改 `~/.zshrc` 后说（逐字，会话"a2a-构思主控"）："改成只提醒不问，那这样的话就不用加延时了，T-098 关闭"。构思主控已把 `~/.zshrc` 第 40 行改为 `zstyle ':omz:update' mode reminder`（改前备份在 `/private/tmp/claude-501/memsample/zshrc.bak-20261018`），并用 `zsh -i -c` 读回 mode=reminder。

边界（如实）：这消除的是 oh-my-zsh 更新提问这一个**已知**提问源，不是"前台只剩 shell 不等于 shell 在等命令"这个一般缺陷；其他会在初始化阶段弹出的提问仍可能吞掉启动命令。执行主控每次启动后核对 pane 回显的做法保持。issue `20261018T020010Z` 为 blocking，由用户的这句话作为处置依据，由执行主控按处置流程引用。

