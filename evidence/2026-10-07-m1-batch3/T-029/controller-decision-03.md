# T-029 主控决定之三（2026-10-07）：Git 提交在沙箱中的真实边界

## 主控探针（证据）
在临时仓库 + worktree（`/private/tmp/claude-501/-Users-luckye-Documents-Code-a2a/a506ddfd-0254-4caa-86fb-bb0e6a9d0cbf/sbx`）中用 `codex sandbox -P :workspace` 运行 `git add f`：
- 无额外可写根：`fatal: Unable to create '.../repo/.git/worktrees/wt/index.lock': Operation not permitted`。
- 加 `sandbox_workspace_write.writable_roots=["<repo>/.git"]` 后：同样报错。
- 对照：同一沙箱内向 `<repo>/.git/probe.txt` 写普通文件成功（/tmp 本就可写）。
结论（observed）：Codex 沙箱专门保护 worktree 的 Git 元数据，`--add-dir <git common dir>` 不能让 worker 提交。模型给出的拒绝理由属实。

## 生产路径为什么能提交（observed）
用户 `~/.codex/rules/default.rules` 含 `prefix_rule(pattern=["git", "add"], decision="allow")` 与 `prefix_rule(pattern=["git", "commit"], decision="allow")`。worker 使用用户正常 Codex 配置时，这两类命令在沙箱外执行、无需审批；隔离 home 不带规则，因此每次提交都弹审批。

## 决定
1. 回退上一轮加入的 Git common dir `--add-dir`：它不能解决问题，属于没有证据支持的改动。保留"红态"记录作为证据。
2. 下一次隔离 CODEX_HOME 中，额外放入一个 rules 文件，**只含**上述两条 prefix_rule（git add、git commit），逐字与用户原文一致；不复制用户其他规则、config 或 hooks。这复现生产路径的真实行为，不扩大权限。其余隔离 home 许可沿用 controller-decision.md 第 2 条。
3. 当前 attempt `a4107e835c8a4b17aec0fea46f1a87f2`：UI 上只按一次 Esc 拒绝，确认 agent idle 后经 `coop.py reclaim --attempt` 回收，保留 worktree 与证据。
4. 新 attempt、新输出目录、显式 submit 期限做真实 run。若仍出现权限对话，停下报告。
5. 把"无人值守 run 依赖 worker 的 Codex 允许 git add / git commit"写进结论，供主控写入 README 前提条件；worker 不改 README。
