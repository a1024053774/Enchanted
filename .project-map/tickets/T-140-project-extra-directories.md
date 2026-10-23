---
id: T-140
title: 项目额外目录：项目设置里添加其他目录，worker 可写，像 Codex 的 add-dir
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

来源：用户 2026-10-23 在本 session 逐字（第 3 条）：“3.可写,不要太重,不然只读的话,比如我想在我博客的文件夹发个博客,他就没办法写”

现状：项目只有一个 `repo`（`store.openedProjects`、daemon `project_open`），无“编辑项目”；worker 只能写自己的 worktree 与请求目录。

1. 项目行菜单加“编辑项目”：显示主目录，列出额外目录，可添加、移除（目录选择器）；保存为追加式事件，不覆盖旧记录。
2. 受管 worker/reviewer/monitor 启动时带上额外目录：Claude 用 `--add-dir` 加沙箱 `filesystem.allowWrite`，Codex 加可写根目录。
3. **可写**（用户裁定）。门禁只集成项目主仓库的提交，额外目录里的改动不进门禁的审查与集成；这一点在界面和角色卡里写明，worker 交付说明里要列出它改了哪些额外目录。
4. 用户的项目终端不受影响。

不做：额外目录的独立门禁、Git worktree 隔离、只读模式。

## Acceptance

- [x] 真实 Electron + 真实 worker：项目加一个外部目录（夹具），worker 在其中创建文件成功；未添加的外部目录写入失败。Claude 与 Codex 各一次。
- [x] 移除目录后新启动的 worker 写不进去。
- [x] 红态：修前 worker 写外部目录被沙箱拒绝。

## 不做

范围外的问题经问题上报，不顺手改。

## Resolution

2026-10-23 关闭，PASS。

- 代码：`708f30e08`（项目设置“额外目录”、`project_settings_saved` 事件、启动记录 `extra_directories`、Claude `--add-dir`/沙箱 allowWrite/Edit 权限、Codex 可写目录、门禁按启动记录核对审查员参数），合并 `82de91333`。
- 验收（执行主控沙箱外，`evidence/2026-10-23-batch23/T-140/outside-03-20261023-064800-130165/`）：真实 Electron + 真实 Claude（claude-haiku-5-5 脚本化接口）与 Codex worker 在额外目录写入成功、未添加目录写入失败、移除后新 worker 写不进；修前红态与变异失败；T-137、T-131、T-127 回归通过。
- 合并后回归（`merge-1/run-20261023T122101Z`、`run-20261023T125644Z`）：T-140 e2e 两次通过。
- 独立审查：agy gemini-3.8-flash-high review-agy-01 PASS（P2 一条经核对代码不成立）。
- 已知边界：普通 Codex worker 的 `/tmp`、`$TMPDIR` 默认可写，移除额外目录撤不掉，转 T-141 处理。
