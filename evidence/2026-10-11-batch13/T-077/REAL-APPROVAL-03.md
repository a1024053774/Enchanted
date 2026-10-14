# T-077 REAL-APPROVAL-03：显式 default 与 r3 预算决定材料

2026-10-13，回应主控 #83。**INCOMPLETE，r3 未启动**。候选 `2e2291acfee0e9b4f20c7ff952a5484c4262e20b` 包含 relay 修复及显式 `-c service_tier="default"`。worker 换为 s13-t077s，续接同一原生会话；提交尾注已记录 gpt-6.1-sol / xhigh 与新 launch。

执行主控的无模型 tier 探针已证明 default 能覆盖用户全局 priority，副本为 `controller-tier-probe-2026-10-13.md`。本卡没有读取或修改用户全局配置。生产启动参数、速度请求记录和相关测试/README 已同步；最小 argv 检查在旧候选先失败，在新代码 4 项通过，零外部进程、零真实回合。`default-tier-red-01.json`、`default-tier-green-01.json` 保留原结果。

## 预算账与最小选项

原卡 4 回合已用完。用户后来批准额外最多 4；r2 虽只观察到 1，但保守占位 2，主控 #83 明确要求不释放。**最多剩余 2**。完整原场景需要两次启动，每次工作+回执 2 回合，共 4；缺口为 **2**，不能按当前预算启动完整闭环。

| 选项 | 回合与能证明的内容 | 不能证明的内容 |
| --- | --- | --- |
| A：再申请 2 回合，完整重演（推荐） | 剩余 2 加新批 2，r3 共 4。真实旧 worker 交付 C1/回执，结束原生会话；真实 Git 冲突触发新 attempt；同 home 中新 worker 整理 C2/回执，verify/integrate/reclaim 与历史日志隔离读回 | 通过前不能宣称 T-077 完成；近额弹窗风险仍需面对并留证据，default 参数本身不修复该问题 |
| B：只用当前剩余 2，第一阶段部分验证 | 仅一个真实 worker 的工作+回执。若成功，可证明显式 default 的真实启动、sol/xhigh 工作、请求文件→Stop→relay→submit、正确身份及回执回合开始/完成 | 无第二 worker 的真实冲突整理/重交，不能证明旧会话结束后的完整替换闭环、跨 attempt 编号复用、同 home 两个真实根日志隔离或 C2 集成；T-077 仍 INCOMPLETE |

请执行主控选择是否为 A 再向用户申请 2 回合，或接受 B 的部分证据。不得释放 r2 的未开始回合来凑数；不得把自动回执合并成零回合或改交付协议来压预算。若选 B，结束后应清理新实例，不保留现场等待一个尚未获批的第二启动。

当前机器计划 `real-plan-03.json` 明确 `remaining_authorized_turns=2`、`full_scenario_required_turns=4`、`turn_limit=2`、`execution_authorized=false`。两个公开 launch 的准确 argv 都列在下方；第 2 次仅供 A 获额外预算后的审阅，不获当前预算授权。选择 A 后必须另存获批预算版本，把实验 turn_limit 改为 4，并分别取得两次启动审批；本文件与当前计划保持历史原文。

## 新实例与隔离配置

新根 `/private/tmp/t077-cf-20261013-r3`；task `T-077-12`，project `T077-real-r3`。隔离 home 为 `/private/tmp/t077-cf-20261013-r3/codex-home`，请求目录仍由生产 Panes 分配到 attempt 专属 `/tmp`，不进入候选。旧 r1/r2 实例、账本和失败证据不改。

只复制 auth.json（0600，不输出、不归档）；不复制用户 config、hook、skills 或 rollout。生成的 config 只信任夹具 Git 根：

```toml
[projects."/private/tmp/t077-cf-20261013-r3/repo"]
trust_level="trusted"
```

只有两条 allow 规则，无其他规则：

```python
prefix_rule(pattern=["git", "add"], decision="allow")
prefix_rule(pattern=["git", "commit"], decision="allow")
```

三个 Codex hook 均经本 launch 的唯一 CLI signal 入口，timeout=10；Git 尾注 hook 只经环境 core.hooksPath。测试 host 仍只预分配公开 launch UUID、检查完整 argv/cwd/环境，token 独立随机；真实运行仍用生产 Panes/Gates/PTY，没有旁路门禁或修改存储。

启动请求为 sol / xhigh / default；实际模型、强度和原生身份须从 rollout 与提交尾注读回。tier 请求记录不冒充供应商实际 tier。A 选项须保留原 home 的旧 rollout，不删改日志，第二次前后逐字节核对，验证新 cwd 与新 UUID；最后归档 Git/SQLite/两份 rollout，确认进程退出后删整个自建 home，auth 不进归档。

## 两个候选启动的准确命令

下面只是审批材料，未授权执行。第二次启动需要新增预算决定及单独审批。

### Launch 1

公开 ID：`e9cf7727-772d-41db-bd76-e71ffc2d7e93`，worktree：`/private/tmp/t077-cf-20261013-r3/state/worktrees/T077-real-r3/T-077-12-a1`。

Codex argv：

```sh
'/Users/luckye/.codex/packages/standalone/releases/0.162.1-aarch64-apple-darwin/bin/codex' '--no-daemon' '--no-alt-screen' '-C' '/private/tmp/t077-cf-20261013-r3/state/worktrees/T077-real-r3/T-077-12-a1' '-a' 'never' '--sandbox' 'workspace-write' '-m' 'gpt-6.1-sol' '-c' 'model_reasoning_effort="xhigh"' '-c' 'service_tier="default"' '-c' 'check_for_update_on_startup=false' '-c' 'tui.notifications=false' '-c' 'sandbox_workspace_write.network_access=false' '-c' 'features.network_proxy=false' '-c' 'hooks.UserPromptSubmit=[{hooks=[{type="command",command="'\''/opt/homebrew/Cellar/node/26.5.0/bin/node'\'' '\''/Users/luckye/Documents/Code/a2a-wt-t077/workbench/src/gates/cli.ts'\'' '\''--state'\'' '\''/private/tmp/t077-cf-20261013-r3/state'\'' '\''signal'\'' '\''--launch'\'' '\''e9cf7727-772d-41db-bd76-e71ffc2d7e93'\''",timeout=10}]}]' '-c' 'hooks.Stop=[{hooks=[{type="command",command="'\''/opt/homebrew/Cellar/node/26.5.0/bin/node'\'' '\''/Users/luckye/Documents/Code/a2a-wt-t077/workbench/src/gates/cli.ts'\'' '\''--state'\'' '\''/private/tmp/t077-cf-20261013-r3/state'\'' '\''signal'\'' '\''--launch'\'' '\''e9cf7727-772d-41db-bd76-e71ffc2d7e93'\''",timeout=10}]}]' '-c' 'hooks.PermissionRequest=[{hooks=[{type="command",command="'\''/opt/homebrew/Cellar/node/26.5.0/bin/node'\'' '\''/Users/luckye/Documents/Code/a2a-wt-t077/workbench/src/gates/cli.ts'\'' '\''--state'\'' '\''/private/tmp/t077-cf-20261013-r3/state'\'' '\''signal'\'' '\''--launch'\'' '\''e9cf7727-772d-41db-bd76-e71ffc2d7e93'\''",timeout=10}]}]' '--dangerously-bypass-hook-trust'
```

外层 zsh argv：

```sh
'/bin/zsh' '-f' '-i' '-c' ''\''/Users/luckye/.codex/packages/standalone/releases/0.162.1-aarch64-apple-darwin/bin/codex'\'' '\''--no-daemon'\'' '\''--no-alt-screen'\'' '\''-C'\'' '\''/private/tmp/t077-cf-20261013-r3/state/worktrees/T077-real-r3/T-077-12-a1'\'' '\''-a'\'' '\''never'\'' '\''--sandbox'\'' '\''workspace-write'\'' '\''-m'\'' '\''gpt-6.1-sol'\'' '\''-c'\'' '\''model_reasoning_effort="xhigh"'\'' '\''-c'\'' '\''service_tier="default"'\'' '\''-c'\'' '\''check_for_update_on_startup=false'\'' '\''-c'\'' '\''tui.notifications=false'\'' '\''-c'\'' '\''sandbox_workspace_write.network_access=false'\'' '\''-c'\'' '\''features.network_proxy=false'\'' '\''-c'\'' '\''hooks.UserPromptSubmit=[{hooks=[{type="command",command="'\''\'\'''\''/opt/homebrew/Cellar/node/26.5.0/bin/node'\''\'\'''\'' '\''\'\'''\''/Users/luckye/Documents/Code/a2a-wt-t077/workbench/src/gates/cli.ts'\''\'\'''\'' '\''\'\'''\''--state'\''\'\'''\'' '\''\'\'''\''/private/tmp/t077-cf-20261013-r3/state'\''\'\'''\'' '\''\'\'''\''signal'\''\'\'''\'' '\''\'\'''\''--launch'\''\'\'''\'' '\''\'\'''\''e9cf7727-772d-41db-bd76-e71ffc2d7e93'\''\'\'''\''",timeout=10}]}]'\'' '\''-c'\'' '\''hooks.Stop=[{hooks=[{type="command",command="'\''\'\'''\''/opt/homebrew/Cellar/node/26.5.0/bin/node'\''\'\'''\'' '\''\'\'''\''/Users/luckye/Documents/Code/a2a-wt-t077/workbench/src/gates/cli.ts'\''\'\'''\'' '\''\'\'''\''--state'\''\'\'''\'' '\''\'\'''\''/private/tmp/t077-cf-20261013-r3/state'\''\'\'''\'' '\''\'\'''\''signal'\''\'\'''\'' '\''\'\'''\''--launch'\''\'\'''\'' '\''\'\'''\''e9cf7727-772d-41db-bd76-e71ffc2d7e93'\''\'\'''\''",timeout=10}]}]'\'' '\''-c'\'' '\''hooks.PermissionRequest=[{hooks=[{type="command",command="'\''\'\'''\''/opt/homebrew/Cellar/node/26.5.0/bin/node'\''\'\'''\'' '\''\'\'''\''/Users/luckye/Documents/Code/a2a-wt-t077/workbench/src/gates/cli.ts'\''\'\'''\'' '\''\'\'''\''--state'\''\'\'''\'' '\''\'\'''\''/private/tmp/t077-cf-20261013-r3/state'\''\'\'''\'' '\''\'\'''\''signal'\''\'\'''\'' '\''\'\'''\''--launch'\''\'\'''\'' '\''\'\'''\''e9cf7727-772d-41db-bd76-e71ffc2d7e93'\''\'\'''\''",timeout=10}]}]'\'' '\''--dangerously-bypass-hook-trust'\''; exec /bin/zsh -f -i'
```

UserPromptSubmit / Stop / PermissionRequest 完整命令（各 timeout=10）：

```sh
'/opt/homebrew/Cellar/node/26.5.0/bin/node' '/Users/luckye/Documents/Code/a2a-wt-t077/workbench/src/gates/cli.ts' '--state' '/private/tmp/t077-cf-20261013-r3/state' 'signal' '--launch' 'e9cf7727-772d-41db-bd76-e71ffc2d7e93'
```

Git hook 环境：

```text
CODEX_HOME=/private/tmp/t077-cf-20261013-r3/codex-home
GIT_CONFIG_COUNT=1
GIT_CONFIG_KEY_0=core.hooksPath
GIT_CONFIG_VALUE_0=/Users/luckye/Documents/Code/a2a-wt-t077/workbench/hooks/
```

Git prepare-commit-msg（git commit -m）完整命令：

```sh
'/Users/luckye/Documents/Code/a2a-wt-t077/workbench/hooks/prepare-commit-msg' '/private/tmp/t077-cf-20261013-r3/repo/.git/worktrees/T-077-12-a1/COMMIT_EDITMSG' 'message'
```

### Launch 2

公开 ID：`9b06963e-5718-4286-9dd3-921591a3b339`，worktree：`/private/tmp/t077-cf-20261013-r3/state/worktrees/T077-real-r3/T-077-12-a2`。

Codex argv：

```sh
'/Users/luckye/.codex/packages/standalone/releases/0.162.1-aarch64-apple-darwin/bin/codex' '--no-daemon' '--no-alt-screen' '-C' '/private/tmp/t077-cf-20261013-r3/state/worktrees/T077-real-r3/T-077-12-a2' '-a' 'never' '--sandbox' 'workspace-write' '-m' 'gpt-6.1-sol' '-c' 'model_reasoning_effort="xhigh"' '-c' 'service_tier="default"' '-c' 'check_for_update_on_startup=false' '-c' 'tui.notifications=false' '-c' 'sandbox_workspace_write.network_access=false' '-c' 'features.network_proxy=false' '-c' 'hooks.UserPromptSubmit=[{hooks=[{type="command",command="'\''/opt/homebrew/Cellar/node/26.5.0/bin/node'\'' '\''/Users/luckye/Documents/Code/a2a-wt-t077/workbench/src/gates/cli.ts'\'' '\''--state'\'' '\''/private/tmp/t077-cf-20261013-r3/state'\'' '\''signal'\'' '\''--launch'\'' '\''9b06963e-5718-4286-9dd3-921591a3b339'\''",timeout=10}]}]' '-c' 'hooks.Stop=[{hooks=[{type="command",command="'\''/opt/homebrew/Cellar/node/26.5.0/bin/node'\'' '\''/Users/luckye/Documents/Code/a2a-wt-t077/workbench/src/gates/cli.ts'\'' '\''--state'\'' '\''/private/tmp/t077-cf-20261013-r3/state'\'' '\''signal'\'' '\''--launch'\'' '\''9b06963e-5718-4286-9dd3-921591a3b339'\''",timeout=10}]}]' '-c' 'hooks.PermissionRequest=[{hooks=[{type="command",command="'\''/opt/homebrew/Cellar/node/26.5.0/bin/node'\'' '\''/Users/luckye/Documents/Code/a2a-wt-t077/workbench/src/gates/cli.ts'\'' '\''--state'\'' '\''/private/tmp/t077-cf-20261013-r3/state'\'' '\''signal'\'' '\''--launch'\'' '\''9b06963e-5718-4286-9dd3-921591a3b339'\''",timeout=10}]}]' '--dangerously-bypass-hook-trust'
```

外层 zsh argv：

```sh
'/bin/zsh' '-f' '-i' '-c' ''\''/Users/luckye/.codex/packages/standalone/releases/0.162.1-aarch64-apple-darwin/bin/codex'\'' '\''--no-daemon'\'' '\''--no-alt-screen'\'' '\''-C'\'' '\''/private/tmp/t077-cf-20261013-r3/state/worktrees/T077-real-r3/T-077-12-a2'\'' '\''-a'\'' '\''never'\'' '\''--sandbox'\'' '\''workspace-write'\'' '\''-m'\'' '\''gpt-6.1-sol'\'' '\''-c'\'' '\''model_reasoning_effort="xhigh"'\'' '\''-c'\'' '\''service_tier="default"'\'' '\''-c'\'' '\''check_for_update_on_startup=false'\'' '\''-c'\'' '\''tui.notifications=false'\'' '\''-c'\'' '\''sandbox_workspace_write.network_access=false'\'' '\''-c'\'' '\''features.network_proxy=false'\'' '\''-c'\'' '\''hooks.UserPromptSubmit=[{hooks=[{type="command",command="'\''\'\'''\''/opt/homebrew/Cellar/node/26.5.0/bin/node'\''\'\'''\'' '\''\'\'''\''/Users/luckye/Documents/Code/a2a-wt-t077/workbench/src/gates/cli.ts'\''\'\'''\'' '\''\'\'''\''--state'\''\'\'''\'' '\''\'\'''\''/private/tmp/t077-cf-20261013-r3/state'\''\'\'''\'' '\''\'\'''\''signal'\''\'\'''\'' '\''\'\'''\''--launch'\''\'\'''\'' '\''\'\'''\''9b06963e-5718-4286-9dd3-921591a3b339'\''\'\'''\''",timeout=10}]}]'\'' '\''-c'\'' '\''hooks.Stop=[{hooks=[{type="command",command="'\''\'\'''\''/opt/homebrew/Cellar/node/26.5.0/bin/node'\''\'\'''\'' '\''\'\'''\''/Users/luckye/Documents/Code/a2a-wt-t077/workbench/src/gates/cli.ts'\''\'\'''\'' '\''\'\'''\''--state'\''\'\'''\'' '\''\'\'''\''/private/tmp/t077-cf-20261013-r3/state'\''\'\'''\'' '\''\'\'''\''signal'\''\'\'''\'' '\''\'\'''\''--launch'\''\'\'''\'' '\''\'\'''\''9b06963e-5718-4286-9dd3-921591a3b339'\''\'\'''\''",timeout=10}]}]'\'' '\''-c'\'' '\''hooks.PermissionRequest=[{hooks=[{type="command",command="'\''\'\'''\''/opt/homebrew/Cellar/node/26.5.0/bin/node'\''\'\'''\'' '\''\'\'''\''/Users/luckye/Documents/Code/a2a-wt-t077/workbench/src/gates/cli.ts'\''\'\'''\'' '\''\'\'''\''--state'\''\'\'''\'' '\''\'\'''\''/private/tmp/t077-cf-20261013-r3/state'\''\'\'''\'' '\''\'\'''\''signal'\''\'\'''\'' '\''\'\'''\''--launch'\''\'\'''\'' '\''\'\'''\''9b06963e-5718-4286-9dd3-921591a3b339'\''\'\'''\''",timeout=10}]}]'\'' '\''--dangerously-bypass-hook-trust'\''; exec /bin/zsh -f -i'
```

UserPromptSubmit / Stop / PermissionRequest 完整命令（各 timeout=10）：

```sh
'/opt/homebrew/Cellar/node/26.5.0/bin/node' '/Users/luckye/Documents/Code/a2a-wt-t077/workbench/src/gates/cli.ts' '--state' '/private/tmp/t077-cf-20261013-r3/state' 'signal' '--launch' '9b06963e-5718-4286-9dd3-921591a3b339'
```

Git hook 环境：

```text
CODEX_HOME=/private/tmp/t077-cf-20261013-r3/codex-home
GIT_CONFIG_COUNT=1
GIT_CONFIG_KEY_0=core.hooksPath
GIT_CONFIG_VALUE_0=/Users/luckye/Documents/Code/a2a-wt-t077/workbench/hooks/
```

Git prepare-commit-msg（git commit -m）完整命令：

```sh
'/Users/luckye/Documents/Code/a2a-wt-t077/workbench/hooks/prepare-commit-msg' '/private/tmp/t077-cf-20261013-r3/repo/.git/worktrees/T-077-12-a2/COMMIT_EDITMSG' 'message'
```

## 停止条件与本轮入口

沿用原场景的停止边界：参数/身份不符、权限或限流换模窗口、model/effort/tier 设置漂移、超出已批回合、900 秒总等待超时、交付失败、未形成预期冲突、旧日志变化或验收/集成失败，保存现场并停。不得换模型、补 Enter、重发任务或释放失败预留。r2 已证明终端写回车不等于新 native turn；不能用 busy 自报代替回执开始的证据。显式 default 只解决速度覆盖，不消除此前的近额换模弹窗风险。

A 的第 1 次正常结束仍停在第 2 次审批前：确认两个原生回合完成及空闲，核对领导者后仅结束该自建 CLI，保留本次后台/原 shell/home。第 2 次经原门禁确认 ended 后换 attempt，整串重验并集成。B 没有第二阶段，两个回合完成后归档并清理。失败时只停自建后台；无法确认退出则保留 home 并上报。

本轮只提供无模型的准备复验入口，真实执行入口在预算/选项决定后固定，当前不复用 r2 的 launcher 或 ledger：

```sh
bash /Users/luckye/Documents/Code/a2a-wt-t077/evidence/2026-10-11-batch13/T-077/outside-sandbox.sh r3-plan-check-01
```

该入口只对生产 Panes 的命令渲染、请求记录、token 和审批边界做模拟检查；不启动 Codex、Unix socket、真实 PTY 或复制 auth，不能替代实际 default 生效或冲突验收。计划重现生成命令（新输出文件不得已存在）：

```sh
python3 -B evidence/2026-10-11-batch13/T-077/prepare-real-plan-03.py --output /tmp/t077-r3-plan-replay.json --launches-from evidence/2026-10-11-batch13/T-077/real-plan-03.json
```

完整 T-077 真实冲突验收、独立审查和最终交付仍未完成。本轮新增真实回合 0，READY 后等待执行主控决定。
