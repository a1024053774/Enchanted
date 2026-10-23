---
id: T-140
title: 项目额外目录：项目设置里添加其他目录，worker 可写，像 Codex 的 add-dir
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

来源：用户 2026-10-23 在本 session 逐字（第 3 条）：“3.可写,不要太重,不然只读的话,比如我想在我博客的文件夹发个博客,他就没办法写”

现状：项目只有一个 `repo`（`store.openedProjects`、daemon `project_open`），无“编辑项目”；worker 只能写自己的 worktree 与请求目录。

1. 项目行菜单加“编辑项目”：显示主目录，列出额外目录，可添加、移除（目录选择器）；保存为追加式事件，不覆盖旧记录。
2. 受管 worker/reviewer/monitor 启动时带上额外目录：Claude 用 `--add-dir` 加沙箱 `filesystem.allowWrite`，Codex 加可写根目录。
3. **可写**（用户裁定）。门禁只集成项目主仓库的提交，额外目录里的改动不进门禁的审查与集成；这一点在界面和角色卡里写明，worker 交付说明里要列出它改了哪些额外目录。
4. 用户的项目终端不受影响。

不做：额外目录的独立门禁、Git worktree 隔离、只读模式。

## Acceptance

- [ ] 真实 Electron + 真实 worker：项目加一个外部目录（夹具），worker 在其中创建文件成功；未添加的外部目录写入失败。Claude 与 Codex 各一次。
- [ ] 移除目录后新启动的 worker 写不进去。
- [ ] 红态：修前 worker 写外部目录被沙箱拒绝。

## 不做

范围外的问题经问题上报，不顺手改。

## Resolution

