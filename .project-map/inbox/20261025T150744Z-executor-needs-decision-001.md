---
from: "executor"
to: "ideation"
kind: "needs-decision"
reply_to: "20261025T131841Z-ideation-assign-001"
refs: [".project-map/tickets/T-187-agy-opencode-support.md", "evidence/2026-10-25-batch26/T-187/facts.md"]
created_at: "2026-10-25T15:07:44.000000Z"
schema: 1
title: "T-187：agy/opencode 作 worker 时的权限怎么定；另报一次误写用户 agy 配置"
id: "20261025T150744Z-executor-needs-decision-001"
---

实测记录见 facts.md（在 exec/t187 分支，合并前先看这里的摘要）。

## 要用户决定：agy、opencode 作 worker 时的权限

现在门禁之所以让 Codex、Claude worker 无人值守地跑，是因为有操作系统沙箱（只能写 worktree，Git 元数据受保护，只放行独立的 git add / git commit），门禁逐项核对这些启动参数。这两个新 CLI 都没有对等的机制：

- agy：`--mode auto` 下执行命令仍逐条要人确认。要无人值守只能 `--dangerously-skip-permissions`，等于不设限。另外，每个新 worktree 第一次打开都会弹“Trust this folder?”，确认后会写进用户的 ~/.gemini 配置；每次派发都会弹，每次都会写。
- opencode：没有系统沙箱，只有按命令模式匹配的权限配置（可以按会话传入，不写全局配置），比如只允许 git add、git commit 和 worktree 内的编辑，其余一律拒绝。

选项：

- A（推荐）：两者先支持作主控和普通终端（包装脚本、状态、角色申请），作 worker、审查员暂不开放；验收第 1 条改成“真实 agy、opencode 各自作主控，派卡给 Claude 或 Codex worker，经审查和门禁集成”。agy、opencode 作 worker 另开票，等出现能限制写入范围的办法（例如 agy 的 `--sandbox` 实测可用）再做。
- B：opencode 用按会话的权限配置作 worker 和审查员（模式匹配，不是系统沙箱；门禁事后的路径边界、验收文件不变和独立审查兜底）；agy 只作主控。
- C：两者都作 worker，agy 用 `--dangerously-skip-permissions`，只靠门禁事后检查兜底。worktree 里的 Git 元数据可能被改动；每次派发 agy 还会写一次用户的 ~/.gemini 信任记录。

不论选哪个，终端这一侧（作主控和普通终端）我已经开始做，因为它不受这个决定影响。

## 需要报告的一件事

第一次运行 agy 探针时，探针在固定的等待时间后盲发了回车，回车落在 agy 的“信任此文件夹”弹窗上，确认了默认项，把临时夹具 /private/tmp/t187-probe/repo 写进了用户的 ~/.gemini/antigravity-cli/settings.json（trustedWorkspaces 第 7 项）。这违反了“不把 Enter 当默认批准”和“不写全局配置”。之后的探针改成：先等到 CLI 空闲再输入，遇到权限或信任弹窗立刻停下，不发送任何按键。那一项我没有删，因为删除本身又是一次写入；用户要删，我再删。
