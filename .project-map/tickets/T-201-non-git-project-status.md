---
id: T-201
title: 非 Git 目录的项目在侧栏露出原始 git 报错
type: build
status: open
blocked_by: []
claimed_by:
supersedes:
ready: no
ready_by:
ready_rev:
---

## What to build

来源：真实用户式试用第 1 轮（[RESULTS](../../evidence/2026-10-27-batch28/UAT-01/RESULTS.md) 发现 3）。打开 `/private/tmp/uat/repos/not-a-repo` 后，侧栏副标题是被截断的 `无法读取 Git：Error: Command failed: git -C … status … fatal: not a git repository …`。

普通目录可以作为项目开终端（首屏就是“打开一个目录，在里面开终端”），这一点不变；侧栏对“不是 Git 仓库”给出一句话状态，其余读取失败照旧如实显示原因。

## Acceptance

- [ ] 修前版本经真实入口：非 Git 目录的侧栏状态含原始命令报错；修后显示“不是 Git 仓库”之类的一句话。
- [ ] Git 仓库读取真的出错时（例如目录被删）仍显示原因，不被这句话盖掉。

通用：先在真实入口留红态再修根因；不写 ~/.claude、~/.codex 等全局配置；独立审查。

## 不做

禁止添加非 Git 目录；在非 Git 目录里建任务。

## Resolution
