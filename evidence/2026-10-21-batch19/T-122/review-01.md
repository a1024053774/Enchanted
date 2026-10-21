# T-122 独立审查 01（候选 c952a9d46，父 7a8a6f74f）

审查者：本 session 新开的只读审查子会话（Claude，干净上下文），2026-10-21。探针脚本见 `review-01-probe/`，现场原在 `/private/tmp/t122-rv/`（用 claude-haiku-5-5 `-p` 模式，按 `claudeArgv` 生成的 worker、reviewer 参数原样复现）。以下是报告要点，按原报告的编号与严重程度记录。

**总体结论：需修复。**

## 发现

1. **高：worker 的 shell 沙箱可写整个主仓库 `.git`。** `allowWrite` 含 `--git-common-dir`（panes.ts 的 `gitMetadata`）。沙箱里 `git update-ref refs/heads/main HEAD` 退出 0，main 被移到 worker 提交；能新建分支、写 `.git/worktrees/x-note`。`.git/config`、`.git/hooks/*` 被强制拒。另：`git -c core.hooksPath=/dev/null commit` 或 `commit-tree` 可做无尾注提交，门禁推断为用户本人提交。建议：只给 objects、本 worktree 的 gitdir、本 attempt 分支的 ref 与 reflog；submit 时比对共享 ref；e2e 加 `update-ref main` 必须被拒的反例。
2. **中高：启动目录里的 `.claude/settings.local.json` 会被加载，钩子在沙箱外执行。** 一次性副本里放该文件，reviewer 启动后其 SessionStart 钩子在沙箱外建文件，额外 `Edit` 规则让 Write 写出副本。worker 直接写它被拒，但可经 `git hash-object`/`update-index --skip-worktree` 把它提交进候选而工作区仍干净。建议：启动目录存在该文件时拒绝启动，或复制副本时剔除；路径检查默认 deny。
3. **中：任务卡的 `executor.model/effort` 被忽略。** Claude 卡不显式传 model 时以 worker 设置（出厂 Codex `gpt-6.1-sol`）启动 claude。CLI 判定应统一用 attempt 绑定的卡。
4. **中低：Claude 沙箱可写 `$TMPDIR`（`/tmp/claude-501`，用户所有 Claude 会话共用）。** 与“只写一次性副本”不符；Codex reviewer 显式排除 /tmp 与 TMPDIR。
5. **中低：信任框识别失败或 SessionStart 不来时，worker 静默停在 unknown，无失败事件。** 建议加启动期限，超时记失败并上报。
6. **中低：hook.py 把请求的 effort 写进 `A2A-Effort` 尾注**，与同文件“请求值不是观测事实”的注释相反；实际强度与请求不同时合法交付会被 `trailer_identity_mismatch` 打回。
7. **低：代按信任可能在失败后重新触发**（失败把 state 置回 unknown 且 active 为空时，输出里出现那行字就会按键）。建议启动完成后永久关闭。
8. **低：reviewLaunch 的 Claude 边界只核对形状**：不拒 `--add-dir`、`--dangerously-skip-permissions`、`--mcp-config`、`--plugin-dir`，不查 settings 的 hooks/env/excludedCommands，重复参数可覆盖。建议白名单或整串相等。
9. **低：Claude reviewer 忽略 reviewer 执行设置**（D24 写“默认同模型，项目设置可换”）。
10. **低：`claudeTurnFacts` 稳健性**：半写入的末行 JSON 解析抛错；`<synthetic>` 条目被当作观测模型；`/clear` 后会话号改变走到 `unsupported_hook`。
11. **测试与证据**：`user-settings-loaded`、`reviewer-shell-writable` 只被 argv/门禁字符串断言抓到，缺行为证据；缺 Bash 写外、ref 移动、“收到任务后不再代按”、submit 处 provider 变异、观测模型与请求模型可区分的反例；e2e 不是真实入口；产品配置没有 Codex worker；`regress-t112-native-02～04` 当时未入库；质量链 8 个 harness_error 只说明没变差。

## 审查者核实无问题的点

Write/Edit 写外与 `..` 被拒；Bash 写外被拒；`.git/config`、hooks 被拒；Write/Bash 写 `.claude/settings.local.json` 被拒；沙箱内连 Unix socket 被拒（worker 拿到 capability 也连不上 control.sock）；网络被拒；hook.py 的 GIT_CONFIG 检查失败即拒；代按只在选中 Yes 时回车；会话唯一性、submit 的 provider 核对、prompt_id 绑定一致；`inbox_ready` 的 realpath 一致；Codex 路径不变，regress-t112-native-04 PASS；红态与 8 个变异失败点与声称一致。

## 未能核实

交互模式下的沙箱与 TMPDIR 是否与 `-p` 一致；打包版里 Electron 运行 `cli.ts` 与 `zsh -lic` 找 claude；`--setting-sources local` 下用户 CLAUDE.md、skills、插件的影响；自动压缩后的会话号；ref 移动在真实集成时 CAS 是否察觉。
