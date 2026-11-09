---
id: T-250
title: 第二个面板“改动”（照 herdr-gitview）：分组文件列表、暂存与提交、diff
type: build
status: done
blocked_by: [T-249]
claimed_by:
supersedes:
ready: yes
ready_by: ideation
ready_rev: 1
---

## 来由

用户原话见 [T-249](T-249-git-graph-panel.md)（2026-11-07）。本票用 T-249 的面板位，是它的第二个使用者。

## 要做的

按 [herdr-gitview](https://github.com/ChmaraX/herdr-gitview)（MIT，Copyright (c) 2026 Adam Chmara；它的 diff 渲染改编自 herdr-reviewr，也是 MIT；借鉴代码时保留两者的版权声明）的功能做。原 mod 的 Rust 引擎不搬，git 调用由工作台主进程按 argv 执行（不经 shell），读操作带 `-c diff.autoRefreshIndex=false`：

- 文件列表：改动分成冲突、已暂存、未暂存三组，可切平铺或目录树；每个文件和总计显示 +/- 行数。
- 暂存、取消暂存、丢弃（丢弃先确认）、提交：提交框在底部，Enter 提交，Shift+Enter 换行；没有已暂存文件时按原 mod 用 `git add -A` 后提交。
- diff：选中文件在面板旁显示 diff，带语法高亮（跟随主题明暗）、词级强调、可折叠的上下文；Markdown 与图片可预览，改动的图片显示前后对比。
- 范围切换：未提交改动 / 与基线分支比较（基线按原 mod 的 `detect_base` 规则：在 HEAD 祖先里找距离最近的本地或远程分支，带主干名候选；可在面板里固定基线）。提交历史只列本分支的。
- 审阅备注：在 diff 里选几行写备注，可把一批备注发给聚焦的 agent 会话。发送和用户在该终端里打字走同一条输入路径，输入记录照常保存；目标是受管 worker 时照常记为人工介入。
- 键盘：j/k 或方向键移动（diff 跟着走），s/u/x 暂存、取消暂存、丢弃，c 写提交说明，t 平铺或目录树，w 切范围，l 历史，J/K 上下一个文件，? 列出全部按键。鼠标：单击选中，双击用系统默认编辑器打开，点文件夹展开或折叠，拖选 diff 行。
- 刷新：本地仓库监视文件变化；自己的写操作之后立即刷新，并忽略自己写操作带来的那一批文件事件。
- 跟随目录和受管 worktree 只读规则与 T-249 相同：跟随门禁 worktree 时暂存、丢弃、提交不可用。

## Acceptance

- [ ] 端到端测试经真实入口（Enchanted Test 或独立数据目录的 Electron）：夹具仓库含已暂存、未暂存、未跟踪、冲突各至少一个文件。面板分组和 +/- 行数与 `git status --porcelain=v2 -z`、`git diff --numstat`、`git diff --cached --numstat` 一致（期望值从 git 读）。
- [ ] 从界面暂存、取消暂存、丢弃、提交各一次，每次之后 `git status` 与 `git log -1` 的变化与预期一致；丢弃先出现确认框，取消时仓库不变。
- [ ] 基线比较：夹具里从 `main` 分出 `feature` 并提交两次，基线识别为 `main`，列出的文件与 `git diff $(git merge-base HEAD main) --name-status` 一致。
- [ ] 审阅备注发到一个普通终端（终端里跑 `cat` 之类能回显的程序），终端收到的文字与备注一致，输入记录里有这条。
- [ ] 测试对已知坏的实现失败（如分组或行数故意算错的变异版本判红）。
- [ ] 独立验收：Codex `gpt-6.1-terra` 新开会话，用 Computer Use 和常规测试逐条核对，写验收报告。
- [ ] 正在运行的 Enchanted 不受影响（同 T-249 的核对）；构建缓存与夹具用完即清。

## 不做

不做 nvim 集成（用系统默认编辑器）；不做远程机器；不搬原 mod 的 Rust 引擎和独立标签页模式（cmd-g 开单独标签）；不 push；不替换 /Applications。

## 执行与授权

分工（2026-11-08 改，用户原话，Claude Code 会话 `local_e9998522-d926-46a1-aac9-eda70d24d2b9`）：

> 先装新版,然后你自己启动软件继续,这次用 opus5.5 extra 当主控,然后 astra extra 当 worker 和 reviewer

执行主控 Claude Code `claude-opus-5-5` xhigh；worker 与 reviewer 都是 Codex `gpt-6-astra` xhigh，不开 Fast。验收同 [T-249](T-249-git-graph-panel.md)：Codex `gpt-6.1-terra` 用 Computer Use 与常规测试验收；“文稿”授权框可代点，规则见 T-249。

## 当前状态

2026-11-09，PASS（范围见下）。由 Claude Code 会话 `8be1abdd-5af9-4023-bff8-cbc0f40d9a84` 直接实现，没有经门禁派发。用户原话：

> 不用 codex 了,你自己做完这些部分结束

端到端测试绿态 23 项通过；分组、行数两个变异都判红。证据见 `evidence/2026-11-09-batch35/T-250/RESULTS.md`。

没有完成的验收项：
- Terra 独立验收：按用户这次的要求没有做。
- 输入记录：普通终端的打字本来就不写 `user_inputs`，所以改为核对备注的记法与打字相同。
