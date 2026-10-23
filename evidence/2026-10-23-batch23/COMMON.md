# batch23 公共约定（T-138～T-146，执行主控 2026-10-23）

本批次所有任务卡共用。来源：提交 ebbae7bd0 的 ticket，ready_by ideation，ready_rev 1；用户 2026-10-23 逐条裁定的原话写在各 ticket 里。

## 工作方式（Herdr 期）

- 你在自己的 worktree 和分支 `exec/<卡号>` 上工作，起点 `ebbae7bd0`。只在这个 worktree 里写。`workbench/node_modules` 是主 checkout 依赖的副本，不提交，不改。
- 提交：用普通 `git commit`，不手写 `A2A-*` 尾注（钩子自动加）。不 push，不合并 main，不 rebase 到别的分支，不碰主 checkout（`/Users/luckye/Documents/Code/a2a`）的工作区。
- 交付 = 在你的分支上提交 + 写 `evidence/2026-10-23-batch23/<卡号>/RESULTS.md`（改了什么、每条验收的证据、红态与变异、已知局限），然后回合结束时说 “DELIVERED <提交号>”。“我做完了”不是交付；执行主控会在沙箱外复跑、交独立审查，通过后才由执行主控集成到 main。
- 证据：小文本摘要入仓库；大的原始输出（夹具目录、截图以外的大文件、日志 > 5 MB）不入仓库，按 T-088 写 `*.archive.json` 清单，归档由执行主控做。截图（png）可以入仓库。

## 测试

- 真实入口优先：参照 `workbench/tests/test_t137_reflect_e2e.py` 与 `workbench/tests/scripted_claude.py`（真实后台、门禁、真实 Electron 经 CDP、真实 Claude Code CLI 加本地脚本化 Messages 接口）。驱动真实 Claude 的模型用 `claude-haiku-5-5`。
- 每个新 e2e 测试：先在文件头写“失败方式”清单再写代码；提供 `--summary <新路径>`（不覆盖旧证据）、`--revision <提交>`（在修前版本上跑，必须失败 = 红态）、`--mutant <名>`（已知坏实现，必须失败）。期望值来自 ticket 与用户原话，不读被测代码的输出来定。
- 你的沙箱可能起不了 Electron、后台或连本机端口。起不了时不要申请越权：把要跑的命令写成 `evidence/2026-10-23-batch23/<卡号>/RUN-OUTSIDE-NN.sh`（zsh，`set -u`，每次输出写新文件名），提交后在回合末尾说 “RUN-OUTSIDE-NN 请主控运行”。执行主控在沙箱外跑完，把结果路径发回给你。
- 已有回归：交付前列出你改动可能影响的已有 e2e，写进 RUN-OUTSIDE 一起跑。
- 测试中启动的后台服务必须脱离调用者进程组（start_new_session）。Electron 从内置盘运行。不写 `~/.claude`、`~/.codex` 等全局配置。

## 上报

- 范围外的问题、验收条件看起来有缺陷、ticket 与代码不符：`scripts/inbox send --from worker:<你的 agent 名> --to triage --kind issue --title "..." --body-file <文件> [--blocking] [--ref file:路径#L行号]`（在你的 worktree 里运行即可）。默认不阻塞，上报后继续。
- 目标、验收、设计级的取舍不要自己定：上报并在 RESULTS.md 写明，停在那一项。
