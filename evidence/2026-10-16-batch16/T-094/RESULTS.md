# T-094-1：启动失败诊断（2026-10-17）

状态：INCOMPLETE。已取得真实红态和命令入口夹具的红绿对照；真实绿态、真实半成功反例与独立审查尚未完成。

绑定：task T-094 / attempt a1 / worker s16-t094；启动记录 `launch-efca9e180a594c2e98ec594874eaf253`；session `1f06c59c-a447-47e4-8075-9a7571db35d3`；规格 T-094 ready_rev 1；基线 `61786370428c3ec5f894ea60acccf2695d54c2dc`。任务书未给 fence、门禁 state 或 submit 参数，worker 不推测这些身份。

## 诊断与改动

真实 red-01 由执行主控运行，Herdr client/server 均为 0.9.4，Codex CLI 0.163.0。5 次逻辑启动、5 次真实 agent start、0 个模型回合；前三次成功，后两次失败。5 个自建 pane 均由探针关闭；主控确认隔离 CODEX_HOME 已删除。原件位置见 `red-01.archive.json`，精简结果见 `red-01-summary.json`。

两次失败分别为 `wF:p5A` / `launch-6f6f69df7f824b8ab594c41704e4fff5` 和 `wF:p5B` / `launch-c995dbfe0426468bb726f8edc6d1114b`。Herdr 返回 `agent_pane_busy`，start 调用耗时分别为 0.01128 秒与 0.01114 秒。这两次失败不是 30 秒等待超时。原启动记录丢失了这一错误身份，只有 CalledProcessError 字符串。

紧邻 start 前，process-info 报告 shell 独占前台组；再前一条仍有 `kiro-cli init zsh post --rcfile zprofile`。可确认：独立的 shell 快照通过，并不保证随后的 Herdr start 接受该 pane。不能据此断言是稀疏 Git 状态慢、具体哪个前台进程再次出现，或 Herdr 检测状态尚未更新。

[Herdr v0.9.4 的 start_agent](https://github.com/herdrdev/herdr/blob/v0.9.4/src/app/agents.rs) 既检查终端 agent 状态，也重新检查 shell 是否可用；[CLI 就绪等待](https://github.com/herdrdev/herdr/blob/v0.9.4/src/cli/agent.rs) 区分 busy、超时、名称丢失和首屏阻断。这些是源码事实；red-01 无法反推命中了 server 内哪一个 TargetBusy 分支。本票不改 Herdr、不改 zsh，也不增加启动重试或时限。

`scripts/launch-worker` 现将失败命令、退出码、stdout、stderr、错误码、失败阶段和完整 start argv 写入启动记录。start 失败后，只读观察本次 pane 的进程和 agent 注册状态，分别记录 `outcome=started_unregistered`、`started_not_ready`、`started_unconfirmed` 或 `unknown`；未启动的明确拒绝记录 `not_started`。查询失败保留诊断，不将未知注册状态当作名称缺失。

按主控 #57 的修订，入口不关闭失败 pane：记录 `pane_disposition=retained_for_controller` 和 pane id，交主控处置。复现探针仍会关闭自己创建的 pane。半成功保留 `phase=failed` 的拒收语义，同时带独立 outcome；不会被现有提交尾注入口当作成功启动。未改动范围外的启动记录校验器、acceptance/、地图、全局配置或 Herdr server。

## 验证与限制

- `python3 -B scripts/test_launch_worker_failure.py --launcher evidence/2026-10-16-batch16/T-094/launch-worker.parent --report .../contract-final-red-01.json -v`：旧实现拒绝不了诊断/分类缺陷；失败日志保留。
- `python3 -B scripts/test_launch_worker_failure.py --report .../contract-final-green-01.json -v`：6 个场景全部通过。夹具显式替换 Herdr/Codex，不连接 socket，不证明真实 Herdr 时序。pane id 每次使用新的随机输入；每次仅一次 start；所有场景均断言入口不关闭 pane。
- `python3 -B acceptance/test_launcher_shell_ready_e2e.py --artifacts /tmp/t094-existing-launcher-contract-01`：6 个场景全部通过，用时 70.800 秒，结果见 `existing-contract-01.txt`。验收文件未修改；原始夹具与命令日志待主控运行 outside-green.sh 归档。
- `project_map.py status --root .`：0 problems、0 stale living docs；最终交付前再保存一次结果。

`outside-green.sh` 供主控执行：先在同一稀疏 worktree 连续启动 5 次，要求全部成功或失败记录有可读身份；再运行一次半成功反例。反例由边界注入器在探针自建 pane 内用 `pane run` 真实启动 Codex，等待观察到真实 Codex 前台进程和空名称，再向入口返回明确注入的名称错误。它证明分类，不冒充原始竞态的自然复现；不会发送任何模型提示。两组原件都直接写外置盘，每次自建 pane 都在 finally 中关闭。

按 behavioral-acceptance-review 的独立性要求，最终验收须由主控另开干净只读 reviewer 会话。worker 的测试和诊断不能代替该结论。此前自动关闭方案的日志保留为历史证据，已在 TEST-PLAN.md 标明不适用于修订后的候选。
