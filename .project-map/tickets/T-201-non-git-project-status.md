---
id: T-201
title: 非 Git 目录的项目在侧栏露出原始 git 报错
type: build
status: closed
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

- [x] 修前版本经真实入口：非 Git 目录的侧栏状态含原始命令报错；修后显示“不是 Git 仓库”之类的一句话。
- [x] Git 仓库读取真的出错时（例如目录被删）仍显示原因，不被这句话盖掉。

通用：先在真实入口留红态再修根因；不写 ~/.claude、~/.codex 等全局配置；独立审查。

## 不做

禁止添加非 Git 目录；在非 Git 目录里建任务。

## Resolution

2026-10-27 PASS。根因：侧栏把 git 读状态的原始报错原样显示。修法：`sidebar.ts` 的 `gitFacts` 在目录存在、没有 `.git`、git 报 not a git repository 时写“不是 Git 仓库”；git 对 HEAD 写坏的真仓库也报同一句话，所以以“没有 `.git`”为准，坏仓库与被删目录仍如实显示原因。真实 Electron 入口的端到端测试：修前版本 a3ae46cf2 显示原始命令报错，修后通过；变异体“只看报错文字”在坏仓库那项失败。agy 独立审查结论“可合并”，无问题。位于上层 Git 仓库内的普通子目录会显示上层仓库状态，不在本票范围。见 [RESULTS](../../evidence/2026-10-27-batch28/T-201/RESULTS.md)、[审查](../../evidence/2026-10-27-batch28/T-201/review-1.md)。
