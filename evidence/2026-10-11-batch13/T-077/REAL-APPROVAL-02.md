# T-077 REAL-APPROVAL-02：已修冲突场景的普通速度复验

状态：**INCOMPLETE，第二实例尚未启动，新增 0/4，原已用 4/4，累计 4/8**。用户授权 `20261012T015257Z-ideation-answer-001` 批准额外 2～4 回合；本次计划和上限均为新增 4。候选 `f6bc3ed99c87e6ea20eaf144b6a073266a5decb2` 包含 relay 修复 `da44c673`，并移除 Fast 参数。主控 #77 要求准备，下面两次启动仍分别等待本次明确批准。

## 场景与预算

将真实冲突整理与同一 home 的历史记录隔离合为一个场景。attempt 1 的真实 worker 在现有 summarize(values) 返回字典中添加 mean_ms，显式交付 C1，并确认回执。独立夹具随后从原基线提交 G：同一返回字典增加 unit=ms，另改 worker 禁止写的 host-policy.txt。两边预期形成真实 Git 内容冲突。

核对第一个 worker 的两个回合已完成、窗格空闲及领导者身份后，仅向该自建 Codex 领导者发 SIGTERM。Panes 必须确认已知领导者退出、进程树仅剩原 shell。第一阶段停止在第二次审批前，保留本次后台、原 shell 和隔离 home；结果为 INCOMPLETE / awaiting_second_launch_approval，exit 0 只表示到达审批边界。

第二次获批后，经原 attempt 的 verify 触发真实冲突。门禁保存冲突、关闭归档原 pane、新建 attempt 2。新 worker 从 G 自行整理并显式重交 C2，确认回执后，再经 verify/integrate/reclaim。独立 oracle 检查空数组、零值、负数和非整数均值，同时核对 unit=ms 与 host-policy.txt 原字节。程序不替 worker 写 C1/C2。

现有 B 通道每次显式交付产生一个独立回执回合，所以预计每次启动 **2 个主 turn**（工作、回执），合计 **4 个，上限 4**。不另开模型探针。产品 turn_limit=4；每次启动前预留 2，第二次要求第一阶段已明确完成两回合。不自动重试、不释放失败预留，不增开第三个 attempt。

## 命令如何提前固定

测试 host 仅在 Panes.createThread 的异步上下文内预分配两个公开 launch UUID，以便提前给出完整 hook 命令。能力 token 独立随机；attempt/session/fence 和原生 UUID 继续由真实门禁、CLI 产生。PTY spawn 前核对完整 shell argv、cwd 和选定的会话环境，不符或缺本次批准文件就停止。host 调用生产 serve 的默认 Panes/Gates，PTY、Git、socket、CLI 与模型均为真实实现。

这一测试输入控制方式须由本次审批一并确认。`no-fast-green-01.json` 已核对生产命令渲染、token 独立性、未批准第二次及拒绝第三次启动，4 项通过；该检查替换了版本响应与 PTY，没有执行 Codex，不是实际启动证据。`real-oracle-offline-01.json` 的独立已知好坏函数检查也为 4 项通过。

隔离 CODEX_HOME 为 `/private/tmp/t077-cf-20261012-r2/codex-home`。只从用户 ~/.codex 复制 auth.json，权限 0600，不输出或归档内容。唯一信任项是夹具 Git 根 `/private/tmp/t077-cf-20261012-r2/repo`；worktree 归属于该 Git 根。另生成以下配置，不复制用户配置、hook、skills 或旧 rollout：

```toml
[projects."/private/tmp/t077-cf-20261012-r2/repo"]
trust_level="trusted"
```

只有两条 allow 规则：

```python
prefix_rule(pattern=["git", "add"], decision="allow")
prefix_rule(pattern=["git", "commit"], decision="allow")
```

实际 Model/Effort 必须从根 turn_context 和提交尾注读回为 gpt-6.1-sol / xhigh。不传 service_tier 参数，不使用 Fast；启动记录的 service_tier_requested 为 null。隔离配置不包含速度设置。

## Launch 1

`8ee0b73a-c031-46ed-8dd6-5e6490029781`

Worktree: `/private/tmp/t077-cf-20261012-r2/state/worktrees/T077-real-r2/T-077-11-a1`

Codex argv:

```sh
'/Users/luckye/.codex/packages/standalone/releases/0.162.1-aarch64-apple-darwin/bin/codex' '--no-daemon' '--no-alt-screen' '-C' '/private/tmp/t077-cf-20261012-r2/state/worktrees/T077-real-r2/T-077-11-a1' '-a' 'never' '--sandbox' 'workspace-write' '-m' 'gpt-6.1-sol' '-c' 'model_reasoning_effort="xhigh"' '-c' 'check_for_update_on_startup=false' '-c' 'tui.notifications=false' '-c' 'sandbox_workspace_write.network_access=false' '-c' 'features.network_proxy=false' '-c' 'hooks.UserPromptSubmit=[{hooks=[{type="command",command="'\''/opt/homebrew/Cellar/node/26.5.0/bin/node'\'' '\''/Users/luckye/Documents/Code/a2a-wt-t077/workbench/src/gates/cli.ts'\'' '\''--state'\'' '\''/private/tmp/t077-cf-20261012-r2/state'\'' '\''signal'\'' '\''--launch'\'' '\''8ee0b73a-c031-46ed-8dd6-5e6490029781'\''",timeout=10}]}]' '-c' 'hooks.Stop=[{hooks=[{type="command",command="'\''/opt/homebrew/Cellar/node/26.5.0/bin/node'\'' '\''/Users/luckye/Documents/Code/a2a-wt-t077/workbench/src/gates/cli.ts'\'' '\''--state'\'' '\''/private/tmp/t077-cf-20261012-r2/state'\'' '\''signal'\'' '\''--launch'\'' '\''8ee0b73a-c031-46ed-8dd6-5e6490029781'\''",timeout=10}]}]' '-c' 'hooks.PermissionRequest=[{hooks=[{type="command",command="'\''/opt/homebrew/Cellar/node/26.5.0/bin/node'\'' '\''/Users/luckye/Documents/Code/a2a-wt-t077/workbench/src/gates/cli.ts'\'' '\''--state'\'' '\''/private/tmp/t077-cf-20261012-r2/state'\'' '\''signal'\'' '\''--launch'\'' '\''8ee0b73a-c031-46ed-8dd6-5e6490029781'\''",timeout=10}]}]' '--dangerously-bypass-hook-trust'
```

外层 zsh argv：

```sh
'/bin/zsh' '-f' '-i' '-c' ''\''/Users/luckye/.codex/packages/standalone/releases/0.162.1-aarch64-apple-darwin/bin/codex'\'' '\''--no-daemon'\'' '\''--no-alt-screen'\'' '\''-C'\'' '\''/private/tmp/t077-cf-20261012-r2/state/worktrees/T077-real-r2/T-077-11-a1'\'' '\''-a'\'' '\''never'\'' '\''--sandbox'\'' '\''workspace-write'\'' '\''-m'\'' '\''gpt-6.1-sol'\'' '\''-c'\'' '\''model_reasoning_effort="xhigh"'\'' '\''-c'\'' '\''check_for_update_on_startup=false'\'' '\''-c'\'' '\''tui.notifications=false'\'' '\''-c'\'' '\''sandbox_workspace_write.network_access=false'\'' '\''-c'\'' '\''features.network_proxy=false'\'' '\''-c'\'' '\''hooks.UserPromptSubmit=[{hooks=[{type="command",command="'\''\'\'''\''/opt/homebrew/Cellar/node/26.5.0/bin/node'\''\'\'''\'' '\''\'\'''\''/Users/luckye/Documents/Code/a2a-wt-t077/workbench/src/gates/cli.ts'\''\'\'''\'' '\''\'\'''\''--state'\''\'\'''\'' '\''\'\'''\''/private/tmp/t077-cf-20261012-r2/state'\''\'\'''\'' '\''\'\'''\''signal'\''\'\'''\'' '\''\'\'''\''--launch'\''\'\'''\'' '\''\'\'''\''8ee0b73a-c031-46ed-8dd6-5e6490029781'\''\'\'''\''",timeout=10}]}]'\'' '\''-c'\'' '\''hooks.Stop=[{hooks=[{type="command",command="'\''\'\'''\''/opt/homebrew/Cellar/node/26.5.0/bin/node'\''\'\'''\'' '\''\'\'''\''/Users/luckye/Documents/Code/a2a-wt-t077/workbench/src/gates/cli.ts'\''\'\'''\'' '\''\'\'''\''--state'\''\'\'''\'' '\''\'\'''\''/private/tmp/t077-cf-20261012-r2/state'\''\'\'''\'' '\''\'\'''\''signal'\''\'\'''\'' '\''\'\'''\''--launch'\''\'\'''\'' '\''\'\'''\''8ee0b73a-c031-46ed-8dd6-5e6490029781'\''\'\'''\''",timeout=10}]}]'\'' '\''-c'\'' '\''hooks.PermissionRequest=[{hooks=[{type="command",command="'\''\'\'''\''/opt/homebrew/Cellar/node/26.5.0/bin/node'\''\'\'''\'' '\''\'\'''\''/Users/luckye/Documents/Code/a2a-wt-t077/workbench/src/gates/cli.ts'\''\'\'''\'' '\''\'\'''\''--state'\''\'\'''\'' '\''\'\'''\''/private/tmp/t077-cf-20261012-r2/state'\''\'\'''\'' '\''\'\'''\''signal'\''\'\'''\'' '\''\'\'''\''--launch'\''\'\'''\'' '\''\'\'''\''8ee0b73a-c031-46ed-8dd6-5e6490029781'\''\'\'''\''",timeout=10}]}]'\'' '\''--dangerously-bypass-hook-trust'\''; exec /bin/zsh -f -i'
```

UserPromptSubmit / Stop / PermissionRequest（各 timeout=10）：

```sh
'/opt/homebrew/Cellar/node/26.5.0/bin/node' '/Users/luckye/Documents/Code/a2a-wt-t077/workbench/src/gates/cli.ts' '--state' '/private/tmp/t077-cf-20261012-r2/state' 'signal' '--launch' '8ee0b73a-c031-46ed-8dd6-5e6490029781'
```

Git hook 环境：

```text
GIT_CONFIG_COUNT=1
GIT_CONFIG_KEY_0=core.hooksPath
GIT_CONFIG_VALUE_0=/Users/luckye/Documents/Code/a2a-wt-t077/workbench/hooks/
```

Git prepare-commit-msg 完整命令（git commit -m）：

```sh
'/Users/luckye/Documents/Code/a2a-wt-t077/workbench/hooks/prepare-commit-msg' '/private/tmp/t077-cf-20261012-r2/repo/.git/worktrees/T-077-11-a1/COMMIT_EDITMSG' 'message'
```

Hook 源文件：`/Users/luckye/Documents/Code/a2a-wt-t077/workbench/hooks/hook.py`

## Launch 2

`99e53bb5-3349-429c-9b43-ab423c80447a`

Worktree: `/private/tmp/t077-cf-20261012-r2/state/worktrees/T077-real-r2/T-077-11-a2`

Codex argv:

```sh
'/Users/luckye/.codex/packages/standalone/releases/0.162.1-aarch64-apple-darwin/bin/codex' '--no-daemon' '--no-alt-screen' '-C' '/private/tmp/t077-cf-20261012-r2/state/worktrees/T077-real-r2/T-077-11-a2' '-a' 'never' '--sandbox' 'workspace-write' '-m' 'gpt-6.1-sol' '-c' 'model_reasoning_effort="xhigh"' '-c' 'check_for_update_on_startup=false' '-c' 'tui.notifications=false' '-c' 'sandbox_workspace_write.network_access=false' '-c' 'features.network_proxy=false' '-c' 'hooks.UserPromptSubmit=[{hooks=[{type="command",command="'\''/opt/homebrew/Cellar/node/26.5.0/bin/node'\'' '\''/Users/luckye/Documents/Code/a2a-wt-t077/workbench/src/gates/cli.ts'\'' '\''--state'\'' '\''/private/tmp/t077-cf-20261012-r2/state'\'' '\''signal'\'' '\''--launch'\'' '\''99e53bb5-3349-429c-9b43-ab423c80447a'\''",timeout=10}]}]' '-c' 'hooks.Stop=[{hooks=[{type="command",command="'\''/opt/homebrew/Cellar/node/26.5.0/bin/node'\'' '\''/Users/luckye/Documents/Code/a2a-wt-t077/workbench/src/gates/cli.ts'\'' '\''--state'\'' '\''/private/tmp/t077-cf-20261012-r2/state'\'' '\''signal'\'' '\''--launch'\'' '\''99e53bb5-3349-429c-9b43-ab423c80447a'\''",timeout=10}]}]' '-c' 'hooks.PermissionRequest=[{hooks=[{type="command",command="'\''/opt/homebrew/Cellar/node/26.5.0/bin/node'\'' '\''/Users/luckye/Documents/Code/a2a-wt-t077/workbench/src/gates/cli.ts'\'' '\''--state'\'' '\''/private/tmp/t077-cf-20261012-r2/state'\'' '\''signal'\'' '\''--launch'\'' '\''99e53bb5-3349-429c-9b43-ab423c80447a'\''",timeout=10}]}]' '--dangerously-bypass-hook-trust'
```

外层 zsh argv：

```sh
'/bin/zsh' '-f' '-i' '-c' ''\''/Users/luckye/.codex/packages/standalone/releases/0.162.1-aarch64-apple-darwin/bin/codex'\'' '\''--no-daemon'\'' '\''--no-alt-screen'\'' '\''-C'\'' '\''/private/tmp/t077-cf-20261012-r2/state/worktrees/T077-real-r2/T-077-11-a2'\'' '\''-a'\'' '\''never'\'' '\''--sandbox'\'' '\''workspace-write'\'' '\''-m'\'' '\''gpt-6.1-sol'\'' '\''-c'\'' '\''model_reasoning_effort="xhigh"'\'' '\''-c'\'' '\''check_for_update_on_startup=false'\'' '\''-c'\'' '\''tui.notifications=false'\'' '\''-c'\'' '\''sandbox_workspace_write.network_access=false'\'' '\''-c'\'' '\''features.network_proxy=false'\'' '\''-c'\'' '\''hooks.UserPromptSubmit=[{hooks=[{type="command",command="'\''\'\'''\''/opt/homebrew/Cellar/node/26.5.0/bin/node'\''\'\'''\'' '\''\'\'''\''/Users/luckye/Documents/Code/a2a-wt-t077/workbench/src/gates/cli.ts'\''\'\'''\'' '\''\'\'''\''--state'\''\'\'''\'' '\''\'\'''\''/private/tmp/t077-cf-20261012-r2/state'\''\'\'''\'' '\''\'\'''\''signal'\''\'\'''\'' '\''\'\'''\''--launch'\''\'\'''\'' '\''\'\'''\''99e53bb5-3349-429c-9b43-ab423c80447a'\''\'\'''\''",timeout=10}]}]'\'' '\''-c'\'' '\''hooks.Stop=[{hooks=[{type="command",command="'\''\'\'''\''/opt/homebrew/Cellar/node/26.5.0/bin/node'\''\'\'''\'' '\''\'\'''\''/Users/luckye/Documents/Code/a2a-wt-t077/workbench/src/gates/cli.ts'\''\'\'''\'' '\''\'\'''\''--state'\''\'\'''\'' '\''\'\'''\''/private/tmp/t077-cf-20261012-r2/state'\''\'\'''\'' '\''\'\'''\''signal'\''\'\'''\'' '\''\'\'''\''--launch'\''\'\'''\'' '\''\'\'''\''99e53bb5-3349-429c-9b43-ab423c80447a'\''\'\'''\''",timeout=10}]}]'\'' '\''-c'\'' '\''hooks.PermissionRequest=[{hooks=[{type="command",command="'\''\'\'''\''/opt/homebrew/Cellar/node/26.5.0/bin/node'\''\'\'''\'' '\''\'\'''\''/Users/luckye/Documents/Code/a2a-wt-t077/workbench/src/gates/cli.ts'\''\'\'''\'' '\''\'\'''\''--state'\''\'\'''\'' '\''\'\'''\''/private/tmp/t077-cf-20261012-r2/state'\''\'\'''\'' '\''\'\'''\''signal'\''\'\'''\'' '\''\'\'''\''--launch'\''\'\'''\'' '\''\'\'''\''99e53bb5-3349-429c-9b43-ab423c80447a'\''\'\'''\''",timeout=10}]}]'\'' '\''--dangerously-bypass-hook-trust'\''; exec /bin/zsh -f -i'
```

UserPromptSubmit / Stop / PermissionRequest（各 timeout=10）：

```sh
'/opt/homebrew/Cellar/node/26.5.0/bin/node' '/Users/luckye/Documents/Code/a2a-wt-t077/workbench/src/gates/cli.ts' '--state' '/private/tmp/t077-cf-20261012-r2/state' 'signal' '--launch' '99e53bb5-3349-429c-9b43-ab423c80447a'
```

Git hook 环境：

```text
GIT_CONFIG_COUNT=1
GIT_CONFIG_KEY_0=core.hooksPath
GIT_CONFIG_VALUE_0=/Users/luckye/Documents/Code/a2a-wt-t077/workbench/hooks/
```

Git prepare-commit-msg 完整命令（git commit -m）：

```sh
'/Users/luckye/Documents/Code/a2a-wt-t077/workbench/hooks/prepare-commit-msg' '/private/tmp/t077-cf-20261012-r2/repo/.git/worktrees/T-077-11-a2/COMMIT_EDITMSG' 'message'
```

Hook 源文件：`/Users/luckye/Documents/Code/a2a-wt-t077/workbench/hooks/hook.py`


## 同一 home 的实测

第一阶段结束原 CLI 后，完整保存旧根 rollout 的字节和路径；它仍留在同一个 home/sessions 中。第二阶段启动前、完成 C2 后及回收前，逐字节核对旧文件不变，不计算哈希。新 launch 采集的根 session_meta 必须只含新 UUID，cwd 等于 a2；旧 UUID 不得成为新 launch 身份。两个原生会话及两套受管身份均入记录。

测试期间不删改旧日志。最终确认自建进程退出后，先把两份原始 rollout 和相关 Git/SQLite 现场归档，再按隔离规则删除整个自建 home；auth.json 不进归档。

## 停止条件

启动参数不符、权限等待、身份异常、额外回合、该次工作/回执超过 900 秒、显式提交失败、未形成预期冲突、旧日志变化、路径/尾注/完成条件/集成失败，都保存现场并停止。不修改权限、不重发任务、不补 Enter，不把失败重试成通过。

失败时只对已核对的自建后台执行 daemon_stop，并核对 PID、端点和已知子进程退出；无法确认时保留 home 并上报，不接管其他进程。第一阶段正常暂停留下的后台和原 shell 是第二次审批后原门禁替换所需的现场，须保持。

## 执行命令

先只批准第 1 次启动、该次两个回合以及确认空闲后的 SIGTERM/暂停步骤，再由执行主控运行：

```sh
T077_REAL_APPROVAL='<本次启动的主控批准引用>' bash /Users/luckye/Documents/Code/a2a-wt-t077/evidence/2026-10-11-batch13/T-077/outside-sandbox.sh real-recheck-01
```

读回第一阶段后，另批准第 2 次启动与该次两个回合，再运行：

```sh
T077_REAL_APPROVAL='<第二次启动的主控批准引用>' bash /Users/luckye/Documents/Code/a2a-wt-t077/evidence/2026-10-11-batch13/T-077/outside-sandbox.sh real-recheck-02
```

第一阶段不自动运行第二阶段。输出为 `real-conflict-02/attempt-1`、`attempt-2`，新增预算写入独立的 `real-turn-budget-02.jsonl`，旧 4 回合记录与旧失败不变；已有执行目录或不符的预算记录会拒绝再次启动。源码、脚本和计划在两次审批间保持不变。第二实例的 task 为 T-077-11，project 为 T077-real-r2；不复用旧实例根或旧 ledger。

完整机器可读命令在 `real-plan-02.json`，包括外层 shell 的完整 argv。本轮证明已实现的 S3 和机械检查；T-076-2 的审查会话尚未合入，不伪造审查通过。真实场景通过后再做本卡的一次 fresh-context 只读独立审查。
