---
id: T-118
title: 不限制原生 CLI 版本；普通终端不继承 agent 会话标记；窗格恢复不回放；渲染进程退出后窗口自恢复
type: build
status: closed
blocked_by: []
claimed_by:
supersedes:
ready: yes
ready_by: executor
ready_rev: 1
---

## What to build

用户 2026-10-21 原话：“都由你来修吧，然后不要限制版本，我既然选择用各家原生cli 了,那肯定要更新版本的对吧.”“b.不要限制版本,理由如上 然后修两个缺陷,还有深色模式这个软件现在变这样了”。本票由主控直接实现，不派发 worker，不伪造门禁记录。

1. 版本：Claude 主控启动、Codex worker/reviewer 启动、窗格恢复只记录实际 `--version`，不再按版本拒绝（原 `controller_version_mismatch`、`codex_version_mismatch`、`restore_version_mismatch`）。
2. 普通终端复制编排后台环境时，只去掉运行中的 Claude Code / Codex 会话给子进程设的运行时标记（实测清单见 `panes.ts` 的 `agentSessionMarkers`），保留 `CLAUDE_CODE_OAUTH_TOKEN`、`CLAUDE_CODE_USE_BEDROCK` 等用户配置。现场：编排后台由 Claude Code 会话启动，终端里的 claude 提示 “Transcript saving is off — inherited CLAUDE_CODE_CHILD_SESSION marker”，对话不存盘，`/resume` 找不到。
3. 窗格恢复从 `pty.raw` 第 0 字节重放，整段 TUI 动画在界面上快放。改为追上实时末尾前隐藏终端，只显示“正在恢复终端内容…”。
4. 用户截图的空白窗口：测试版从 Enchanted 终端里启动，原 Enchanted 退出时其 GPU、网络服务、后台收到 SIGTERM，渲染进程消失，主进程没有重建。改为 `render-process-gone` 时重新加载（先等切换、新建、关闭窗格完成，关闭最多等 10 秒；重载后 10 秒内再次崩溃不再重载）。渲染进程的定时刷新向主进程校正窗格集合，清掉失效的缩放与状态。与深色模式无关。

非目标：从普通终端指定主控、Claude worker（另议）；T-116 夹具不稳定。

## Acceptance

- [x] 普通终端环境：真实 daemon+zsh。修前（3070bbe1a）标记全部继承；按前缀过滤的变异误删 `CLAUDE_CODE_OAUTH_TOKEN`、`CLAUDE_CODE_USE_BEDROCK`；修后只去掉运行时标记。`workbench/tests/test_t118_shell_env_e2e.py`。
- [x] 版本：Claude 主控（test_t091_claude_version.mjs，修前与“加回比较”的变异均失败）、Codex worker（test_t112_execution.mjs，修前报 codex_version_mismatch）、恢复（test_t096_restore.mjs，修前少恢复一个窗格；去掉运行时版本更新的变异失败）。`run_t108_real.py` 审计断言改为比对独立 `--version`，需真实登录，本票未运行。
- [x] 打包测试版真实界面（ui-test-12，连跑 3 次）：约 2MB 整屏重绘后重新加载，恢复期间零个可见中间帧，最后一屏正确；Page.crash 后窗口与窗格自恢复；丢失回执的关闭（被放大窗格）由定时同步收敛，剩余窗格可见；深色截图正常。旧版 ui-test-05 同一脚本：6 个可见中间帧、崩溃不恢复；ui-test-09/11 分别在同步、放大清理一步失败。
- [x] 独立只读审查：第 1～5 轮 NO_GO，逐条修复；第 6 轮 PASS。

只有代码检查或局部探针、没有真实入口证据的边界：小积压重连、无 launch 后绑定、空输出／读取错误、导航／新建／关闭超过 10 秒期间崩溃、连续崩溃、外部 SIGTERM、恢复版本的界面展示、正常登录最终审计。

证据：`evidence/2026-10-21-batch19/T-118/`（RESULTS.md；审查完整日志归档 /Volumes/WD-Elements/a2a-evidence/2026-10-21-batch19/T-118/）。

## Resolution

2026-10-21 主控直接实现（用户“都由你来修吧”）。版本只记录不比较；普通终端去掉运行时会话标记；恢复时隐藏回放、追平并绘制后再显示；渲染进程退出后重新加载，窗格集合由主进程定时校正。六轮 Codex gpt-6.1-sol high 只读审查，最后一轮 PASS。未覆盖边界见上方与 RESULTS.md。
