---
id: T-094
title: 缺陷：launch-worker 在稀疏 worktree 里间歇启动失败（herdr agent start 退出 1，无错误身份）
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

执行主控 issue `20261017T104229Z-executor-issue-001`（非阻塞）：2026-10-17 在 `a2a-wt-t089` 里用 `scripts/launch-worker` 启动 Codex，5 次失败 3 次，启动记录 phase failed，错误只有 `herdr agent start ... returned non-zero exit status 1`，stderr 未保存。失败的 launch：`launch-5c71733a…`（Codex 起来了但没被命名）、`launch-aadd73d0…`、`launch-c1327128…`（约 2 秒失败，pane 停在 shell）；换新 pane 重试 2 次成功。同期 `a2a-wt-t091`、`a2a-wt-t078` 没有失败；手动 `herdr agent start --timeout 60000` 成功。

执行主控的推测（未证实）：该 worktree 里 zsh 提示符的异步 git 状态很慢，shell 未就绪 herdr 就开始启动，或超过 30 秒默认时限。

1. 先复现并定位：保存 herdr 的 stderr；在 `a2a-wt-t089` 同类稀疏 worktree 里重复启动，区分"shell 未就绪""超时""herdr 自身错误"。
2. 修根因：失败要有可读的错误身份，不能再只剩退出码 1；"Codex 起来了但没被命名"这类半成功状态要明确记为哪一种，不留悬空 pane。
3. 不加盲目重试，不靠加长时限掩盖；是否等 shell 就绪由定位结果决定。

## Acceptance

- [x] 红态：在能触发失败的 worktree 里复现，保留 herdr 的 stderr 与启动记录。
- [x] 绿态：同一条件下连续多次启动全部成功，或失败时记录带可读的原因。
- [x] 反例：半成功状态（进程已起、未命名）被记为独立结果，不记成"成功"也不记成笼统的 failed。
- [x] 不改 Herdr server，不影响用户正在使用的 Herdr。
- [x] `project_map.py status` 0 problems。

## 说明

- 来源：用户 2026-10-17 说（逐字，会话"a2a-构思主控"）："launch-worker 启动失败要开缺陷票"。已标就绪（见下）。Herdr 期工具，日常派发改走工作台后可能停用，由执行主控判断优先级。

## 就绪

用户 2026-10-17 说（逐字，会话"a2a-构思主控"）："开1，2， 用fast，快重制了，是我改的"，构思主控据此标就绪（`ready_rev: 1`）。

## 裁定（2026-10-17）

执行主控 needs-decision `20261017T200327Z`：两条受保护旧验收与现状冲突——`test_launcher_shell_ready_e2e` 写死 process-info 恰好调 5 次（锁的是旧的提前放行细节），`test_herdr_traceability_e2e` 写死 Codex 0.162.1（本机已 0.163.0，main 上也已失败）。用户选"A: 两条都修订成断言行为 (Recommended)"，选项原文："第1条改成断言“前台连续 1500ms 只剩 shell 才算就绪”的行为，不再锁调用次数；第2条改为核对实际记录的版本等于启动时 --version 的输出（和 T-091 处理 Claude 版本的方式一致）。修订后仍要对旧实现取红态、对新实现取绿态。"

## Resolution

2026-10-17，执行主控按门禁验收 **PASS**，合入 main（不 push）。冻结候选 `3096bef9a2f0b3b0db739a51ad662dad3f0bdd83`（exec/t094，worker s16-t094，launch-efca9e180a594c2e98ec594874eaf253，service_tier fast，按用户本期放宽办理）；之后 `cd75a7ce2` 只补审查记录。

- **根因（已证实）**：在 pane 收到 agent_pane_busy 的那一刻采样前台进程，看到的是用户 zsh 初始化中的 conda（`conda shell.zsh hook` / `conda shell.posix activate base`），不是主控先前猜测的 git 提示符，那个推测已撤回。launch-worker 一看到"前台只有 shell"就立即放行，而 conda 随后又派生子进程，Herdr 判定 pane 不是可用 shell。
- **修法**：就绪条件改为"前台连续 1500 毫秒只剩 shell"，总期限 30 秒，超时报出最后一次采样的前台 argv；不重试；失败的 pane 保留；"进程已起但未命名"记为独立结果 started_unregistered；herdr 的 stderr 与错误码写进启动记录。主控否决了"往 pane 写回执命令"，因为它会写进用户的 shell 历史。已知局限：shell 初始化中途如果空闲超过 1500 毫秒，仍可能误判（已写进 README/RESULTS）。
- **证据**：red-01（5 次中 2 次 busy，只有退出码）→ busy-01（前台采样为 conda）→ busy-02（10 次全部成功）。外置盘 `a2a-evidence/2026-10-16-batch16/T-094/`。
- **受保护验收修订**（用户裁定 A，见上方"裁定"）：只改了两个文件中的两条断言。第 1 条改为断言稳定窗口的行为，旧实现上取得红态。第 2 条改为核对记录的版本等于启动时 `--version` 的输出：旧实现本来就记录得正确，所以红态由"记录错误版本"的变异体取得（主控裁定，reviewer 认为成立）。其余断言未放宽。
- **独立审查**：reviewer s16-t094-rev（launch-12a0935dfbd548d0a2b04fe815a73ac0）`independent-review-01.md` **PASS**。三个变异（跳过稳定窗口、超时时不报 argv、半成功记成成功）都被业务断言拒绝；主控在沙箱外重放 REVIEW-OUTSIDE-01.sh，rc 0。
- 打分 `score-39c41d2b9a7e4e109c6012393cf06e26`（边界 2、工程 3）。
- 未覆盖：Herdr 把 worker 的提问面板报成 working 这个问题另开了 T-095（未就绪）。
