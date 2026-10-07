# T-029 common dir 声明后仍有 Git 权限请求（2026-10-07）

状态：BLOCKED。worker 没有选择任何选项或输入 Enter；第二份主控决定要求“再遇到任何权限对话，停下报告”。

当前请求仍为 `git add -- pager.py`，理由为“沙箱阻止创建当前 worktree 的 Git index.lock”。原始 UI 为 `final-runtime-03/w1-p2.txt`，最新状态/实际前台进程 argv 在 `handoff-live-scene.json`；完整启动 argv 和 Git 路径在 `git-permission-boundary.json`。

这次实际启动参数已经严格包含两项 --add-dir：`/Users/luckye/Documents/Code/a2a/.runtime/final-runtime-01-live_run/state` 和 `/private/tmp/t029-2uoclfw5/fixture/.git`。当前 worktree Git dir 为 `/private/tmp/t029-2uoclfw5/fixture/.git/worktrees/a4107e835c8a4b17aec0fea46f1a87f2`。没有放宽 sandbox、添加 approval rule、复制用户 config/rules/hooks 或批准对话。参数声明回归已绿，但真实无人值守提交仍被审批 UI 阻断，不能称完整缺陷已修复。UI 的理由是模型提供的说明，现有材料没有独立保存普通沙箱 Git 尝试的退出码/原始 stderr；不能仅凭它断定内核拒绝写入。SDK/系统目录策略与模型是否提前请求沙箱外执行，均须进一步核对，不猜测新的绕过方案。

- 冻结候选：`09a576b37f0e3f303cdb70f389a3da76cfedb1fd`，外置盘构建、8/9/18、fence mutant、idle 回收红/绿检查通过。
- 原 attempt `b102c2a0ec3b447f8a022c1c042d2b13` 已只按一次 Esc 拒绝请求，确认 idle 后经 CLI reclaim；原 dirty worktree 保留。
- 引擎会话：`a2a-t029-10ybn2y_`，server PID `70518`，最新仍 running。
- 当前 task=`automatic-pagination`，attempt=`a4107e835c8a4b17aec0fea46f1a87f2`，session_id=`b2ef4629f17f4280aa6dc2a43cca6e67`，fence=3，spec_rev=1。
- pane=`w1:p2`，terminal=`term_65d3914f65c692`，agent=blocked。task=claimed，run=paused，未 commit/submit/verify/integrate/reclaim 当前 attempt。
- 隔离 home `/tmp/t029-codex-60ak760p` 的 auth/信任配置已删除且未重建。首次删除后，仍 blocked 的 Codex 后台重建了 cache/skill/plugin 目录；已按同一删除许可再次清理，见 isolated-home-after-cleanup.json、isolated-home-final-removal.json。最新删除检查 absent=true；活跃客户端可能再次写缓存，最终收尾须在获准结束该客户端后核对。用户配置字节未变，归档不含 auth 副本。

请主控先核对 tool call 是否主动指定沙箱外执行、是否有普通沙箱 Git 尝试及其真实退出结果，再核对实际目录声明，再决定后续修正和当前 pane 的拒绝/回收步骤。此记录不请求把 Git 对话默认视为已批准，也不据此增加任何目录、权限、规则或 model 重试。当前 server/pane/dirty worktree 与全部失败证据保留；fresh-context 独立审查仍待完整真实 run。
