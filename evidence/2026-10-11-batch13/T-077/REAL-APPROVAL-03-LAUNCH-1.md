# T-077 r3 Launch 1：最终逐次审批材料

2026-10-13，回应主控 #85。**INCOMPLETE，未启动**。用户 answer `20261013T144758Z-ideation-answer-001` 原话："A 再批 2 回合，完整重演 (Recommended)"。答复副本在同目录；要求 sol/xhigh/default，再不通过就停下报告、不自动追加。

预算已另存为 `real-plan-03-approved.json`：turn_limit=4，原卡实际用 4、r2 保守占位 2，r3 剩余 2 加新批 2，共 4，累计保守上限 10。旧 `real-plan-03.json` 的 2 回合版本、旧 ledger 和失败均不变。本次只申请 **Launch 1 的 2 个回合**（工作、回执）、空闲核对后的原生领导者 SIGTERM，以及到第二次审批前的暂停步骤；**Launch 2 尚未获本次启动审批**。

固定产品提交 `2e2291acfee0e9b4f20c7ff952a5484c4262e20b`，包含 relay 的 launch+request_id 修复及显式 default 覆盖。每阶段核对 HEAD 与 workbench/acceptance/worker role 零差异，发现变更即拒绝；不更换账号、模型或权限。

## 实例、输入和隔离

新根 `/private/tmp/t077-cf-20261013-r3`，task T-077-12，project T077-real-r3。隔离 home `/private/tmp/t077-cf-20261013-r3/codex-home`；从用户 home 仅复制 auth.json，0600，不输出、不归档；生成配置只信任夹具 Git 根。只生成两条 allow 规则，不复制用户 config/hook/skills/rollout：

```toml
[projects."/private/tmp/t077-cf-20261013-r3/repo"]
trust_level="trusted"
```

```python
prefix_rule(pattern=["git", "add"], decision="allow")
prefix_rule(pattern=["git", "commit"], decision="allow")
```

真实 worker 在独立夹具 src/summary.py 的返回字典增加 mean_ms，保留原字段；空列表为 None，其余为 total_ms/count，只做一次提交。通过生产请求文件 B 通道，用 request_id=delivery 显式交付 C1，然后真实回执回合只确认收到。独立 oracle 原文沿用 r1/r2，启动前仍用已知坏 baseline 检出缺 mean_ms 的业务失败；不由模型自报替代门禁。

两个回合均完成、窗格 idle、队列空且没有写入时，再核对原生领导者与原生 UUID，提交并发 G（unit=ms 及禁止 worker 改的 host-policy.txt），仅 SIGTERM 该已核对的自建 Codex 领导者，保留 shell；Panes 须确认领导者已结束、原 shell 仍在。记录旧 rollout 全部字节后，暂停到第二次审批前。成功到达此边界仍是 INCOMPLETE / awaiting_second_launch_approval，exit 0 不代表整票通过。

第二阶段将另交审批：经旧 attempt verify 形成真实内容冲突、生产门禁换新 attempt，真实 worker 在同一 home 自行整理 C2，仍以 delivery 重交，再 verify/integrate/reclaim；旧日志逐字节不变，新 UUID/cwd 归属正确，host 内容和提交引用独立读回。本次不自动运行它。

## Launch 1 完整命令

公开 launch：`e9cf7727-772d-41db-bd76-e71ffc2d7e93`。worktree：`/private/tmp/t077-cf-20261013-r3/state/worktrees/T077-real-r3/T-077-12-a1`。

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

Git 尾注 hook 环境：

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

源文件：`/Users/luckye/Documents/Code/a2a-wt-t077/workbench/hooks/hook.py`。

测试 host 仍仅预分配公开 launch UUID；能力 token 由生产第二次 UUID 调用独立产生，不固定、不写进计划。PTY 前检查外层 argv、cwd 和已列环境，缺少本 launch 的批准文件、参数不符或第三个 attempt 都不能到达 spawn。后台使用生产 serve/Panes/Gates 和真实 PTY。该测试输入控制方式需包含在这次审批中。

## 停止、预算与清理

新 runner `run-real-conflict-03.py` 仅写 `real-turn-budget-03.jsonl`。预留每次 2、最多 4；先核对 r2 原有占位仍为 2，不释放或修改它。本次不提供重试：阶段目录已存在、ledger 不符、第一阶段未成功或缺第二次审批都不能再次启动。

参数、原生身份、权限或模型/强度/tier 异常，超过预算、900 秒总等待、显式交付失败、日志变化或后续冲突/验收/集成失败，都保存现场并停下报告。新增 runner guard 只核对结构化 turn_context / thread_settings_applied：model 必须 sol、effort 必须 xhigh，设置中的 service_tier 必须 default；发现 r2 一样的 luna/medium 漂移立即退出，不等 900 秒、不补 Enter、不选菜单、不重发任务。这是测试停止条件，不是产品弹窗处理修复，也不保证在漂移发生前阻止产品写回车。

第一阶段正常暂停保留隔离 home、后台与原 shell，供第二次经原门禁替换。失败则只停自建后台、确认 endpoint/PID 与所观察子进程退出，先归档 Git/SQLite/rollout，再删整个自建 home，auth 不归档；无法确认退出则保留 home 并上报。再不过就停，不自动追加回合。

## 本次批准后的运行命令

```sh
T077_REAL_APPROVAL='<本次 r3 Launch 1 的主控批准引用>' bash /Users/luckye/Documents/Code/a2a-wt-t077/evidence/2026-10-11-batch13/T-077/outside-sandbox.sh real-r3-launch-01
```

产物 `real-conflict-03/attempt-1/`；budget journal `real-turn-budget-03.jsonl`。host 的准确启动 argv 由 runner 写入 `real-conflict-03/host-process.json`，使用 approved plan、control/launch-config.json 与 control/ready.json。第二阶段必须另有审批引用，本次不授权。

准备检查：`r3-launch-approved-offline-01.json` 的生产命令渲染/审批边界 4 项 PASS；`r3-runner-offline-01.json` 的预算与原生漂移停止检查 4 项 PASS，包含 r2 原始漂移反例。全部 0 个真实回合、0 个真实进程。原有 oracle 及产品没有新增变化。准备检查不是实际启动或冲突验收证据。

重现命令（本 worker worktree，新输出文件不得已存在）：

```sh
node evidence/2026-10-11-batch13/T-077/check-real-launch-approved-03.ts evidence/2026-10-11-batch13/T-077/real-plan-03-approved.json /tmp/t077-r3-approved-render.json
```

本次申请的是具体 Launch 1；尚未安装真实 hook、复制 auth 或启动真实 Codex。审批前停止等待。
