# T-029 主控决定之二（2026-10-07）：Git 暂存权限

## 判定
不批准这次 `git add -- pager.py` 对话，也不批准"记住该命令前缀"。不在 UI 上回答 Yes。

## 根因（主控只读核对）
- 当前 attempt 的 worktree：`git rev-parse --git-dir` 为 `/private/tmp/t029-2uoclfw5/fixture/.git/worktrees/b102c2a0ec3b447f8a022c1c042d2b13`，common dir 为 `/private/tmp/t029-2uoclfw5/fixture/.git`。
- `coop.py` 启动 Codex 时只给 `-C <workspace> --add-dir <state root>`（coop.py 第 687 行附近），没有给任务仓库的 Git 目录写权限，所以沙箱拒绝写 index.lock。
- 首轮能提交，推断是因为用户 ~/.codex 的规则允许 git 命令；隔离 home 不带用户规则，暴露了这个缺口。这是 dispatch 合同缺陷：受管契约要求 worker 创建本地 commit 并以完整 SHA 交付，无人值守的 run 不能依赖每次提交都有人批准。

## 要求
1. 当前 attempt `b102c2a0ec3b447f8a022c1c042d2b13`：在 UI 上选 No 或按 Esc 拒绝（只做这一个拒绝动作，不选其他选项），然后经 `coop.py reclaim --attempt b102c2a0ec3b447f8a022c1c042d2b13` 核对、撤销并回收；保留 worktree、状态和证据。
2. 修正 dispatch：额外把**该任务仓库**的 Git common dir 作为可写目录交给 Codex（只此一个目录，不放宽沙箱模式、不加通用规则、不复制用户 rules），并在运行记录中保存实际 argv。先用现有入口拿到红态（无该目录时提交被拒或出现权限对话），再改并拿到绿态。不得为通过而修改 oracle 预期。
3. 新的隔离 CODEX_HOME 许可沿用 controller-decision.md 第 2 条（只复制 auth.json、只信任已核对的夹具根目录、不装 hook、结束后删除）；本决定不增加任何新的 trust 或权限。
4. 用新 attempt、新输出目录、显式 submit 等待期限做真实 run，完整走 submit、独立 oracle、CAS 集成、回收。再遇到任何权限对话，停下报告。
