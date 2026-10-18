---
id: T-094
title: 缺陷：launch-worker 在稀疏 worktree 里间歇启动失败（herdr agent start 退出 1，无错误身份）
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

执行主控 issue `20261017T104229Z-executor-issue-001`（非阻塞）：2026-10-17 在 `a2a-wt-t089` 里用 `scripts/launch-worker` 启动 Codex，5 次失败 3 次，启动记录 phase failed，错误只有 `herdr agent start ... returned non-zero exit status 1`，stderr 未保存。失败的 launch：`launch-5c71733a…`（Codex 起来了但没被命名）、`launch-aadd73d0…`、`launch-c1327128…`（约 2 秒失败，pane 停在 shell）；换新 pane 重试 2 次成功。同期 `a2a-wt-t091`、`a2a-wt-t078` 没有失败；手动 `herdr agent start --timeout 60000` 成功。

执行主控的推测（未证实）：该 worktree 里 zsh 提示符的异步 git 状态很慢，shell 未就绪 herdr 就开始启动，或超过 30 秒默认时限。

1. 先复现并定位：保存 herdr 的 stderr；在 `a2a-wt-t089` 同类稀疏 worktree 里重复启动，区分"shell 未就绪""超时""herdr 自身错误"。
2. 修根因：失败要有可读的错误身份，不能再只剩退出码 1；"Codex 起来了但没被命名"这类半成功状态要明确记为哪一种，不留悬空 pane。
3. 不加盲目重试，不靠加长时限掩盖；是否等 shell 就绪由定位结果决定。

## Acceptance

- [ ] 红态：在能触发失败的 worktree 里复现，保留 herdr 的 stderr 与启动记录。
- [ ] 绿态：同一条件下连续多次启动全部成功，或失败时记录带可读的原因。
- [ ] 反例：半成功状态（进程已起、未命名）被记为独立结果，不记成"成功"也不记成笼统的 failed。
- [ ] 不改 Herdr server，不影响用户正在使用的 Herdr。
- [ ] `project_map.py status` 0 problems。

## 说明

- 来源：用户 2026-10-17 说（逐字，会话"a2a-构思主控"）："launch-worker 启动失败要开缺陷票"。已标就绪（见下）。Herdr 期工具，日常派发改走工作台后可能停用，由执行主控判断优先级。

## 就绪

用户 2026-10-17 说（逐字，会话"a2a-构思主控"）："开1，2， 用fast，快重制了，是我改的"，构思主控据此标就绪（`ready_rev: 1`）。

## 裁定（2026-10-17）

执行主控 needs-decision `20261017T200327Z`：两条受保护旧验收与现状冲突——`test_launcher_shell_ready_e2e` 写死 process-info 恰好调 5 次（锁的是旧的提前放行细节），`test_herdr_traceability_e2e` 写死 Codex 0.162.1（本机已 0.163.0，main 上也已失败）。用户选"A: 两条都修订成断言行为 (Recommended)"，选项原文："第1条改成断言“前台连续 1500ms 只剩 shell 才算就绪”的行为，不再锁调用次数；第2条改为核对实际记录的版本等于启动时 --version 的输出（和 T-091 处理 Claude 版本的方式一致）。修订后仍要对旧实现取红态、对新实现取绿态。"

