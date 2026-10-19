---
id: T-104
title: 工作台：不调用模型的普通 zsh 窗格
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

来源同 T-103。现状：主进程只接受主控或当前 worker 的 launch（`main.ts:27`）；`panes.ts` 只有起 Claude 主控和起 Codex worker/reviewer 两条通路；界面里没有新建窗格的入口。AGENTS 第三阶段约束写明"窗格里跑用户的 zsh"，产品里目前没有这条路。

用户的方向：窗格是各家原生 CLI 的交互终端，也包括用户自己的 zsh，a2a 只做编排。

语义由构思主控定（用户未逐条确认，执行主控有硬冲突再上报）：
1. 普通 shell 窗格属于**项目**（cwd 为项目工作目录，也可选任务的 worktree 目录），不绑定 attempt，不是受管 worker，不经门禁认领/交付；它只是用户的终端。
2. 记录：窗格创建与关闭作为事件追加到现有事件流，角色记为 `shell`；窗格里的输入**不**当作对 agent 的用户输入，也不触发"人工介入"（它不是受管 worker 会话）。不采集输入内容到事件流（不是 agent 对话，避免记录密码等）。
3. 启动：用户登录 shell 的 zsh，不传模型相关参数，不写 `~/.zshrc` 等全局配置；环境变量只带项目号。
4. 界面：窗格栏有"新建终端"入口；关闭窗格结束其子进程（沿用现有窗格关闭与重开恢复的语义，普通 shell 不做自动续接，恢复后显示"已结束"）。
5. 同一窗口里这类窗格与 agent 窗格并存，不混淆标识。

## Acceptance

- [x] 红态：当前无入口、主进程拒绝。绿态：真实 Electron，点"新建终端"出现可输入的 zsh，`echo` 与 `pwd` 正确，cwd 为项目目录。
- [x] 反例：该窗格输入不进入 agent 的输入记录；关闭后子进程确实结束（进程核对）；重启后台后该窗格显示"已结束"而不是被重新拉起。
- [x] 事件流里有创建/关闭事件，无输入内容。
- [x] 不动门禁与受管 worker 窗格的"直接输入记为人工介入"语义；`project_map.py status` 0 问题。

## 不做

不做多标签管理、会话持久化、shell 主题。

## Resolution

2026-10-19，执行主控。PASS。exec/t104 以 `--no-ff` 合入 main（754c6ba3e），没有 push。

- 后台（worker s17-t104）：
  - shell_start 和 shell_close 只允许 operator；
  - 起的是登录 zsh（`/bin/zsh -l -i`），只注入 A2A_PROJECT，剔除继承的 A2A_*、GIT_CONFIG_*、CODEX_THREAD_ID；
  - 事件流记录创建和关闭，角色为 shell；
  - 关闭时核对子进程确实退出；后台重启后显示“已结束”，不会被重新拉起。
- 界面：“新建终端”按钮；cwd 取所选任务的 repo，renderer 不能传路径。
- 第一段与 T-103 在 daemon.ts、gates/cli.ts 上的合并冲突，已在 edd469f6b 中解决，两边的命令都保留。
- 独立审查 01 判 NO_GO：
  1. shell 每次输入都会写一条请求元数据；执行主控按 ticket“避免记录密码”的意图裁定不记。我给第一轮任务书写的“只有创建和关闭事件”比 ticket 原文严，已在第二轮任务书里更正：布局和进程诊断事件可以保留。
  2. “重启后自动拉起 shell”的变异没被测试抓住。
  两项都在 45c127b5a 修好。
- 独立审查 02（s17-t104-r2）：PASS。审查记下一条边界：operator 通过 CLI 新建终端时，cwd 不受项目目录限制，这是明确保留的受信管理接口；界面这条路径没有越权口子。
- 审查附带的可选复验，在候选的 git archive 副本上失败了，原因是测试读回的竞态：断言时 env 输出还没读完，并没有多出来的变量（REPLAY-DIAGNOSIS-28.md）。31d86330b 只改了测试的同步方式，精确断言保持不变。
- 后台套件连跑两次（sync-30-01、sync-30-02），都 PASS：
  - known-bad、metadata、privacy、input-events、restart 五个变异全部被拒；
  - 四个现有回归全部通过。
  真实 Electron 界面 ui-01 PASS，截图在外置盘 T-104/ui-01。合入后 main 上的 test_t091_pane_ipc.mjs 结果 PASS。
- 第一段修改了两个现有回归夹具（test_pane_dispatch_state.ts、test_conflict_panes.ts）。它们在基线上本来就失败，断言没有改，第一轮审查已核实。
