# T-094-1：启动失败诊断（2026-10-17）

状态：INCOMPLETE。真实红态、修复后的可读失败诊断和真实半成功分类已有证据；间歇 `agent_pane_busy` 的具体根因尚未证实，独立审查尚未完成。green-01 的启动结果为 4 次成功、1 次失败，不能记为全部启动成功。本次只补充证据与报告，生产代码仍为已测试的 `515b814574e533226a6e63d12eff908fee38058a`。

绑定：task T-094 / attempt a1 / worker s16-t094；启动记录 `launch-efca9e180a594c2e98ec594874eaf253`；session `1f06c59c-a447-47e4-8075-9a7571db35d3`；规格 T-094 ready_rev 1；基线 `61786370428c3ec5f894ea60acccf2695d54c2dc`。任务书未给 fence、门禁 state 或 submit 参数，worker 不推测这些身份。

## 诊断与改动

真实 red-01 由执行主控运行，Herdr client/server 均为 0.9.4，Codex CLI 0.163.0。5 次逻辑启动、5 次真实 agent start、0 个模型回合；前三次成功，后两次失败。5 个自建 pane 均由探针关闭；主控确认隔离 CODEX_HOME 已删除。原件位置见 `red-01.archive.json`，精简结果见 `red-01-summary.json`。

两次失败分别为 `wF:p5A` / `launch-6f6f69df7f824b8ab594c41704e4fff5` 和 `wF:p5B` / `launch-c995dbfe0426468bb726f8edc6d1114b`。Herdr 返回 `agent_pane_busy`，start 调用耗时分别为 0.01128 秒与 0.01114 秒。这两次失败不是 30 秒等待超时。原启动记录丢失了这一错误身份，只有 CalledProcessError 字符串。

紧邻 start 前，process-info 报告 shell 独占前台组；再前一条仍有 `kiro-cli init zsh post --rcfile zprofile`。可确认：独立的 shell 快照通过，并不保证随后的 Herdr start 接受该 pane。不能据此断言是稀疏 Git 状态慢、具体哪个前台进程再次出现，或 Herdr 检测状态尚未更新。

[Herdr v0.9.4 的 start_agent](https://github.com/herdrdev/herdr/blob/v0.9.4/src/app/agents.rs) 既检查终端 agent 状态，也重新检查 shell 是否可用；[CLI 就绪等待](https://github.com/herdrdev/herdr/blob/v0.9.4/src/cli/agent.rs) 区分 busy、超时、名称丢失和首屏阻断。这些是源码事实；red-01 无法反推命中了 server 内哪一个 TargetBusy 分支。本票不改 Herdr、不改 zsh，也不增加启动重试或时限。

`scripts/launch-worker` 现将失败命令、退出码、stdout、stderr、错误码、失败阶段和完整 start argv 写入启动记录。start 失败后，只读观察本次 pane 的进程和 agent 注册状态，分别记录 `outcome=started_unregistered`、`started_not_ready`、`started_unconfirmed` 或 `unknown`；未启动的明确拒绝记录 `not_started`。查询失败保留诊断，不将未知注册状态当作名称缺失。

按主控 #57 的修订，入口不关闭失败 pane：记录 `pane_disposition=retained_for_controller` 和 pane id，交主控处置。复现探针仍会关闭自己创建的 pane。半成功保留 `phase=failed` 的拒收语义，同时带独立 outcome；不会被现有提交尾注入口当作成功启动。未改动范围外的启动记录校验器、acceptance/、地图、全局配置或 Herdr server。

### agent_pane_busy 的当前处理与依据

入口在调用 start 之前沿用原有的 shell 检查，最多等 30 秒：shell 必须独占前台进程组。通过检查后只调用一次 `herdr agent start`。收到 `agent_pane_busy` 后，入口不再等待或重新启动；它保存原始错误、只读查询该 pane 的进程和注册状态、写入失败结果、以 Herdr 原退出码 1 返回，并将 pane 留给主控。两次诊断查询各有 5 秒上限，这些是取证，不是等待 shell 就绪或重试启动。

依据是任务卡允许“失败时记录带可读原因”，同时禁止盲目重试与单纯加长时限。现有进程快照不是对下一次 API 调用的就绪保证，也不足以支持另加一个可靠的等待条件。因此保留 Herdr 的拒绝并将它明确暴露；本候选没有消除间歇启动失败，也没有证明延长等待可以解决它。Herdr CLI 自己的就绪处理仍由原版本负责，探针记录的一次 CLI 调用不等于只有一次 server 内部请求。

## 主控 #59 回传原件的核对

主控在沙箱外运行 `outside-green.sh`，脚本 rc 0；worker 随后直接读取外置盘上的 `identity/records/launches.jsonl`、`herdr.jsonl` 和 `run.json`，确认启动记录原件与探针保存的快照逐字段一致。核对命令为 `python3 -B evidence/2026-10-16-batch16/T-094/check-recorded-green.py`；结果见 `recorded-green-check-01.txt`，精简数据与原件清单见 `green-01-summary.json`、`unregistered-01-summary.json` 及同名 `*.archive.json`。重放只读核对时加 `--output <不存在的新目录>`，原始记录与已有摘要均保留。

| 原件 | 启动事实 | 记录核对 |
| --- | --- | --- |
| green-01 第 1、3、4、5 次 | rc 0，`phase=started` | 4 次启动成功 |
| green-01 第 2 次 | rc 1，`phase=failed`；`wF:p5D`；`launch-ff2ef727627a415baaf3f278e62515fe` | `error_code=agent_pane_busy`，`outcome=not_started`，原始 stderr 已保存 |
| unregistered-01 | rc 1，`phase=failed`；`wF:p5H`；`launch-431cd36ffa9e44e1a6c9067ac44671af` | `outcome=started_unregistered`；真实 Codex 进程存在，agent 名称缺失；成功启动消费入口拒收 |

green-01 第 2 次的 `herdr_stderr` 包含 `agent target pane wF:p5D is not an available shell`；`error_code` 与原始 Herdr 输出一致。`launch.stderr` 末尾仍有 CalledProcessError 的退出码文本，但同一行前面已打印 `错误=agent_pane_busy，结果=not_started`，完整输出前部也有原始 Herdr JSON；启动记录并非只剩退出码。该次 start CLI 调用耗时 2.02456 秒，仍未达到 30 秒。失败后入口取证捕获到同一前台组中的 `conda shell.posix activate base` 及子 shell，后续探针观察又只剩 zsh。这支持“shell 快照可能处于初始化过渡”的推断，不能证明 Herdr 在确切拒绝时刻命中了哪个检查分支，更不能证明稀疏 Git 提示符是根因。

因此，green-01 不满足“全部启动成功”分支；它提供了“失败时带可读原因”分支的真实证据，失败的那次仍按失败计数。unregistered-01 是明确标注的故障注入：一个真实 `pane run` 启动 Codex，未调用真实 `agent start`；边界返回注入的 `agent_name_not_found`。入口观察到 PID 65114 的 Codex 和缺失的名称，写成独立半成功结果。它证明分类，不是自然出现的名称丢失故障或原始竞态的根因证明。

两组共 6 次逻辑启动、5 次真实 agent start、1 次未命名 Codex 启动、0 个模型回合；每次探针均只关闭自己 split 返回的 pane，6 次 close 均 rc 0。主控确认 wF 没有残留的自建 pane。启动入口本身保留 pane 的行为与主控 #57 的修订一致。

## 验证与限制

- `python3 -B scripts/test_launch_worker_failure.py --launcher evidence/2026-10-16-batch16/T-094/launch-worker.parent --report .../contract-final-red-01.json -v`：旧实现拒绝不了诊断/分类缺陷；失败日志保留。
- `python3 -B scripts/test_launch_worker_failure.py --report .../contract-final-green-01.json -v`：6 个场景全部通过。夹具显式替换 Herdr/Codex，不连接 socket，不证明真实 Herdr 时序。pane id 每次使用新的随机输入；每次仅一次 start；所有场景均断言入口不关闭 pane。
- `python3 -B acceptance/test_launcher_shell_ready_e2e.py --artifacts /tmp/t094-existing-launcher-contract-01`：6 个场景全部通过，用时 70.800 秒，结果见 `existing-contract-01.txt`。验收文件未修改；原始夹具与命令日志已归档，见 `existing-contract-01.archive.json`（15 文件 / 103147 字节）。边界测试完整输出见 `contract-details-01.archive.json`（5 文件 / 178556 字节）；历史摘要中的 pending 路径是归档前的记录，原件没有覆盖。
- `project_map.py status --root .`：0 problems、0 stale living docs；本轮最终结果见 `project-map-status-02.txt`。

`outside-green.sh` 已执行完毕，原件全部保留在外置盘。无需为本次仅补充报告的提交再次启动 Codex 或重复测试；后续重放须换用新的 label 和归档目录，避免覆盖历史原件。

按 behavioral-acceptance-review 的独立性要求，最终验收须由主控另开干净只读 reviewer 会话。worker 的测试和诊断不能代替该结论。此前自动关闭方案的日志保留为历史证据，已在 TEST-PLAN.md 标明不适用于修订后的候选。
