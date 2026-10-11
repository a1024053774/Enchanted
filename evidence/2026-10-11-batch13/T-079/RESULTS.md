# T-079-1：启动前等待 shell 就绪

2026-10-11，worker `s13-t079`，T-079 `ready_rev: 1`。**PASS，待主控关闭。** 真实红态 10 次复现 2 次失败，真实绿态 10/10 成功；适配后的 T-073 旧套 7/7、新套 6/6 通过，起点反事实 1/1 按预期失败；收尾地图复查为 0 problems、0 stale，退出 0。

起点为 `ffe7ecb85e9e224d5917183b48754f15ac0c5ba6`。代码候选为 `8ab5177d09dcb25f57a50ad2166dc0006ea99ce3`，只包含 `scripts/launch-worker` 与新增 launcher 测试；提交带齐 9 项尾注，见 [candidate-commit.txt](candidate-commit.txt)。本报告和完整证据随收尾提交交付；该提交可用 `git log -1 --format=%H -- evidence/2026-10-11-batch13/T-079/RESULTS.md` 定位。保留所有主控日志和其他 worker 的改动。

夹具候选为 `d8446fc982aed0309e7d4892760cbe4e69b694eb`，只适配旧、新测试的环境来源，见 [fixture-commit.txt](fixture-commit.txt)。launcher 与 `8ab5177d` 的完整文件字节相同。两套完整测试已针对新夹具重新取得结果；当前交付的 launcher、两个测试及运行脚本均与被验证的归档源码相同。

交付身份：task `T-079-1`，attempt `a1`，受管 session `95c66d36-5763-4a23-a44a-44d67b864f22`，启动记录 `launch-cabfe480b27d4a4a9dd93d74df3e7096`，原生会话 `01a12a7a-da98-7de1-b9be-c7ec1149e58b`。依据为本任务卡、T-079 `ready_rev: 1` 与 native-cli-orchestration 规格第 5、8 节；旧夹具修改的授权逐字记录在逐 hunk 说明中。

## 已核对的就绪能力

- observed：本机 Herdr CLI、红态运行中的 server 均为 `0.9.3`，server protocol 为 22、compatible 为 true；Codex CLI 为 `0.162.1`。见红态的 `server.json` 与 `commands.jsonl`。
- observed：`pane split --env KEY=VALUE` 支持给新 shell 注入环境。`pane process-info` 提供 shell PID、前台进程组及前台进程列表；`pane get` 没有 shell 就绪字段。
- observed：[官方 CLI 文档](https://raw.githubusercontent.com/herdrdev/herdr/v0.9.3/docs/next/website/src/content/docs/cli-reference.mdx)将可用 shell 定义为 shell 占有前台，且没有其他前台命令、编辑器或 agent。
- observed：上游 `v0.9.3` 的 [macOS 实现](https://github.com/herdrdev/herdr/blob/v0.9.3/src/platform/macos.rs#L416)调用 [available_pane_shell_from_job](https://github.com/herdrdev/herdr/blob/v0.9.3/src/platform/mod.rs#L367)。它要求前台进程组等于 shell PID、前台进程列表仅含该 PID，且进程名属于支持的 shell；[process-info 的实现](https://github.com/herdrdev/herdr/blob/v0.9.3/src/app/api/panes.rs#L519)暴露同一组进程事实。
- inferred：可以按以上结构化字段等待 Herdr 定义的可用 shell，不依赖标题、revision 或读屏。不把进程事实扩大解释成已收到某个 shell prompt 事件；Herdr 没有暴露这样的事件。
- measured：执行主控执行真实红态 10 次、绿态 10 次，分别为 2 次 `agent_pane_busy` 和 10/10 成功；两次运行的 pane 均已关闭，隔离 home 已删除。没有向这些 Codex 发送任务。
- measured：适配后的旧、新完整测试与反事实均符合预期。夹具验证证明尾注与启动记录的纯契约，真实 Herdr 时序另有红绿证据；供应商实际使用的 tier 未测量，只记录 Fast 请求。

能力原始记录：[herdr-capabilities.json](herdr-capabilities.json)，包括本机 help、schema 与上游函数原文。重新生成到新文件，避免覆盖原证据：

```sh
python3 -B evidence/2026-10-11-batch13/T-079/inspect-capabilities.py /tmp/t079-herdr-capabilities-new.json
```

## 红态结果与退出码

**PASS（缺陷复现）：** [red-20261011T104147Z-175b51](red-20261011T104147Z-175b51/summary.json) 在起点提交完成 10 次启动：第 8、10 次报 `agent_pane_busy`，另外 8 次正常启动。第 8 次的 `processes.json` 显示 zsh 与 `kiro-cli init zsh post --rcfile zprofile` 同处 shell 前台进程组，证实必须核对列表里没有初始化助手；第 10 次失败后的快照只剩 shell，说明事后采样不替代启动当时的状态。原始失败、runner、启动记录和夹具归档均保留。

`commands.jsonl` 的 58 条命令里，只有两次 launcher 返回 1，和各自的真实 `agent_pane_busy` 一致；10 次 pane close 与最终地图检查都返回 0。隔离 home 删除记录存在。

**已查明整体工具退出 1 的原因：外层 zsh 的通配符检查失败。** 主控原始 Bash 调用与返回已从其 a2a 会话记录提取到 [red-exit-source.json](red-exit-source.json)，仅保留本次调用与对应结果。原命令为：

```sh
echo HERDR_ENV=${HERDR_ENV:-unset}; bash evidence/2026-10-11-batch13/T-079/outside-sandbox.sh red 2>&1 | tail -5; ls -d /tmp/a2a-t079-codex-home-* 2>/dev/null
```

探针删除隔离 home 后，最后的 glob 没有匹配。zsh 在调用 `ls` 前就报 `(eval):1: no matches found: /tmp/a2a-t079-codex-home-*`，外层工具返回 1。这个 1 是额外目录检查的失败，不是探针设计的红态返回，也不是 cleanup 失败。原调用通过管道且没有单独捕获 Bash 脚本退出码，不能将外层工具的码冒充脚本码；归档 runner 没有按 busy 次数设置非零返回。

在本 worker 创建的空临时目录里复现同一 zsh glob 行为，结果也是 1、stdout 为空、stderr 为 `no matches found`，见 [red-exit-reproduction.json](red-exit-reproduction.json)。没有查看或删除其他 home。本次没有通过新的真实启动来调查这个调用层问题；红态失败原样保留。

重放（目标文件须不存在）：

```sh
python3 -B evidence/2026-10-11-batch13/T-079/inspect-red-exit.py /tmp/t079-red-exit-source-new.json
python3 -B evidence/2026-10-11-batch13/T-079/inspect-red-exit.py --reproduce /tmp/t079-red-exit-reproduction-new.json
```

## 修复与夹具检查

- 环境直接随 `pane split --env` 传入，删除旧的 `pane run export` 路径。
- 按已核对的 Herdr 判据等待：pane 身份相符、shell 占有前台组、列表只剩支持的 shell。每次查询受剩余期限约束；总上限 30 秒，未知状态、查询挂起均不会无限等。
- 只调用一次 `agent start`。查询错误、身份不符、超时或 agent 启动失败沿用 failed 记录并保留 pane；没有读屏、盲目重试或自动关闭。
- 启动记录字段和 Codex argv 保持原契约。新增测试通过真实 launcher 与 Git 入口运行，用明确标识的假 Herdr/Codex 边界，不连 socket、不产生模型回合。

**PASS（夹具）：** [fixture-candidate-green01/summary.json](fixture-candidate-green01/summary.json) 的 6 项全部通过：延迟 shell 就绪后启动与提交；未知状态 30 秒超时；状态查询挂起 30 秒超时；查询错误不重试；pane 身份不符拒绝；agent start 失败不重试。第一项还核对完整环境、记录字段不变，以及夹具 worker 提交的 9 项尾注；提交文本保存在该项证据目录中。

**PASS（反事实）：** [fixture-baseline-red01/summary.json](fixture-baseline-red01/summary.json) 将同一个新测试放到起点 launcher 上，因未等待而报 `agent_pane_busy`，退出 1。预期来自任务卡、Herdr 外部契约与 T-073 的独立尾注 oracle，未导入 launcher 的判据或常量。

重放命令（输出目录须不存在）：

```sh
python3 -B acceptance/test_launcher_shell_ready_e2e.py --artifacts /tmp/t079-fixture-baseline-new --launcher /tmp/a2a-t079-baseline-304nduej/repo/scripts/launch-worker --case test_delayed_shell_then_commit
python3 -B acceptance/test_launcher_shell_ready_e2e.py --artifacts /tmp/t079-fixture-candidate-new
git show -s --format='%H%n%B' 8ab5177d09dcb25f57a50ad2166dc0006ea99ce3
```

旧 T-073 全套最初因夹具不适配而未运行，上报 `20261011T105016Z-worker:s13-t079-issue-001` 的原始正文继续保留。当前会话 `⟦主控 #5⟧` 已批准纳入本票，只改假 Herdr 与 `managed_env`。逐 hunk 说明见 [fixture-hunks.md](fixture-hunks.md)，固定版本的源码比对证明所有业务断言与辅助方法原文不变。新测试也仅同步其环境文件的写入格式；后续完整复跑取得新夹具的绿态与反事实，未用适配前结果替它背书。

## 真实绿态

**PASS（真实启动与记录）：** [green-20261011T105319Z-896a7f/summary.json](green-20261011T105319Z-896a7f/summary.json) 绑定代码候选 `8ab5177d09dcb25f57a50ad2166dc0006ea99ce3`，10/10 全部 started，busy=0；逐条启动记录、argv 与身份检查通过。10 次 pane close 均为 0，隔离 home 删除记录存在。该结论只覆盖本次固定版本与 10 次场景，不宣称长期可靠性。

重放命令仍为 `bash evidence/2026-10-11-batch13/T-079/outside-sandbox.sh green`，固定同一生产候选并新建证据目录；本次不重复运行。

## 完整测试结果

**PASS：** [tests-20261011T110739Z-8b3a1a/summary.json](tests-20261011T110739Z-8b3a1a/summary.json) 固定 `d8446fc982aed0309e7d4892760cbe4e69b694eb`。执行主控在沙箱外运行，worker 核对原始命令、stdout/stderr、套件 summary、提交文本和归档源码：

- T-073 旧套：7 项全部通过，退出 0，failures=0、errors=0；包含原项目钩子传递失败、`--no-verify` 尾注、amend/rebase/merge、原生身份替换、打分并发与损坏记录等原有断言。
- T-079 新套：6 项全部通过，退出 0，failures=0、errors=0；包含未知状态与挂起查询的有界超时、不重试、身份拒绝和完整环境/尾注。
- 起点反事实：1 项因真实 launcher 在明确的 Herdr 边界夹具中提早调用 start 而失败，退出 1，failures=1、errors=0，原始协议错误为 `agent_pane_busy`。这是预期红态，不是测试环境错误。
- 夹具 worker 的 Git 提交带齐 9 项尾注，原文在 `T-079/test_delayed_shell_then_commit/message-*.txt`；T-073 的原有尾注断言也全部通过。没有真实模型回合或额外真实 pane。
- 版本查询专用空隔离 home 已删除，有独立删除记录；最终地图命令退出 0。

重放由执行主控从自己的 Herdr pane 运行，会创建新证据目录：

```sh
bash evidence/2026-10-11-batch13/T-079/outside-sandbox.sh tests
```

`tests` 固定夹具候选 `d8446fc982aed0309e7d4892760cbe4e69b694eb`，在私有源码副本中运行 T-073 旧套 7 项、T-079 新套 6 项，并用新夹具对起点 launcher 再跑一次预期红态。它保存完整 stdout/stderr、退出码、各套原有原始证据和 summary；任一失败停止，不调整断言。没有创建真实 agent pane，不产生模型回合；只有旧套的版本查询使用真实 `codex --version`，为它设置空隔离 home，结束后删除，不复制凭据或全局配置。

已有 red/green/tests 的 runner 均已归档，原始失败与中间结果保留。任务卡为 S 级，允许不另开独立 reviewer，由执行主控审 diff；本 worker 没有把自审写成独立审查通过。ticket 保持 open，Resolution 写“待主控关闭”，最终验收与关闭由执行主控办理。

## 已执行的检查

- PASS：shell 与内嵌 Python 语法检查。探针准备时修正了仓库根目录的相对定位，并依据 `--help` 修正 `status server --json` 的输出读取方式；这些修正发生在真实探针执行前，没有红态运行被覆盖。
- tests 运行器静态核对时统一 resolve 冻结源码路径，避免 macOS 的 `/tmp` 与 `/private/tmp` 别名令反事实命令匹配失败；修正发生在复跑前，没有修改业务断言或覆盖运行结果。
- PASS：收尾地图复查为 0 problems、0 stale，退出 0，见 [project-map-final-02.txt](project-map-final-02.txt)。此前第一次收尾检查曾因并行 T-076 的 workbench 覆盖文件与 README 不同步而退出 1；失败原文见 [project-map-final.txt](project-map-final.txt)，已上报 blocking issue `20261011T111416Z-worker:s13-t079-issue-001`。本 worker 未改 workbench 或地图，也未关闭该 issue；复查恢复正常的事实随报告交主控处置，原失败和[问题正文](final-map-issue.md)继续保留。
- PASS：批准范围与逐 hunk 检查；红态外层 glob 退出 1 的来源与独立复现已核明。
- PASS：适配后的两套完整测试与反事实、真实启动红绿态、记录与尾注条件均完成。证据目录没有超过 5 MB 的单个文件；归档夹具以 tar.gz 保存，没有新增 gitlink。
- 限制：真实启动证据为同一环境下的 10 次红态、10 次绿态，不据此宣称长期可靠性；没有新增真实模型回合、性能或成本实验；原红态调用没有单独捕获脚本退出码，其外层 glob 失败来源已核明。

重新生成语法检查与地图检查的命令：

```sh
bash -n evidence/2026-10-11-batch13/T-079/outside-sandbox.sh
python3 -B -c 'import ast; from pathlib import Path; s=Path("evidence/2026-10-11-batch13/T-079/outside-sandbox.sh").read_text(encoding="utf-8"); ast.parse(s.split("<<\x27PY\x27\n",1)[1].rsplit("\nPY",1)[0])'
python3 /Users/luckye/Documents/SKILLS/project-map-skill/project-map/scripts/project_map.py status --root .
find evidence/2026-10-11-batch13/T-079 -size +5M
```
