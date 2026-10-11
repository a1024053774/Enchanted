# 任务卡 T-075-5

你是 a2a 的 worker（Codex），由执行主控（Claude Code）派发，只做这张卡。T-075 已经完成卡 1～4，最终候选为 `7bcfe7d9`，执行主控的验收在 `be3ca531`。现在只差 T-075 验收项的第 4 条。

| 字段 | 内容 |
| --- | --- |
| 编号 | T-075-5 |
| 来源 | ticket T-075，以当前的 `ready_rev` 为准 |
| 目标 | 交付 8 项、恢复 9 项、编排 18 项这三套场景，要在最终的门禁入口（经常驻后台访问的 CLI）上重新取得红态、绿态与反例。做完后，T-075 验收第 4 条在最终候选上有当前证据。 |
| 非目标 | 不改 `acceptance/` 下任何断言或预期；不让产品 CLI 隐式拉起后台；不改门禁契约（锁、fence、CAS、恢复语义）；不做 S2～S5 的内容；不碰界面。 |
| 修改边界 | 允许：`workbench/tests/` 下新增的适配与运行器；`acceptance/entry/` 下的入口文件（只能改入口选择与参数传递，不能改断言）；本卡证据目录 `evidence/2026-10-10-batch12/T-075/card-5/`；ticket T-075 的 Resolution。如果必须改产品代码（例如 socket 放在哪里），先写进 PLAN，等我批准后再改。禁止：`acceptance/test_*.py` 里的断言、`scripts/`、spec、Synara fork、全局配置。 |
| 完成条件 | 见下方。 |
| 红态命令 | 在 `7bcfe7d9` 上，用 `evidence/2026-10-10-batch12/T-075/run-acceptance.py` 跑三套（执行主控已经跑过，证据在 `card-4/executor-final-{coop,recovery,run}-01`）：35/35 失败，失败原因是 `Unix socket path exceeds 103 bytes`。这是入口或生命周期层面的红态，不算业务红态。 |
| 任务类型 | 测试 |
| 修复对象 | — |
| 复杂度 | M |
| 执行器 | Codex CLI，`gpt-6.1-sol`，xhigh，Fast 请求（默认模型） |
| 起点 | a2a `main` 当前 HEAD（开工时写进 RESULTS） |
| 唯一写入者 | 本 worker 会话（Herdr agent `s12-t075-5`） |

## 已知事实
- T-075-3 之后，CLI 只能经后台的 Unix socket 工作；后台没起来时会明确报错，不会自动拉起。旧套件在每个测试里给的 `--state` 都是长临时路径，既不启动后台，也超出 socket 路径 103 字节的上限。
- 恢复套件会在真实操作的中途终止执行门禁操作的进程。现在门禁操作在后台进程里执行，只杀 CLI 客户端，门禁操作不会被中断。所以恢复类场景能不能在不改断言的前提下迁过来，要先查清楚。
- 卡 4 已经有 `workbench/tests/test_daemon_recovery_e2e.py`（真实后台的 recovery 5/5），可以拿来参考。

## 先交计划，停下等我
写 `card-5/PLAN.md`，内容包括：
1. 适配方式：例如测试专用的入口，按 `--state` 起一个隔离后台并管理它的生命周期，socket 放在短路径上。说明它为什么不算“产品隐式拉起后台”，以及测试是否仍直接读 state 目录下的 SQLite。
2. 三套里每一项怎么在新入口上跑：哪些照原样就能过；哪些要把屏障、故障注入的对象从 CLI 换成后台。逐项列出来。
3. 不改断言就做不到的项，单独列出来，说明原因，交给我决定，不要硬改。
4. 红态、绿态和至少 3 个变异体（fence、CAS 期望旧值、操作锁）在新入口上怎么做。
5. 需要在沙箱外运行的部分。

写完回复 `T-075 PLAN READY` 后停下。

## 完成条件（我写好的）
1. 用你的适配运行器在当前候选上跑三套，结果是 8/8、9/9、18/18 通过（如有我批准的例外，另行列出），`acceptance/` 的断言 diff 为空：`git diff 7bcfe7d9 -- acceptance/test_coop_e2e.py acceptance/test_recovery_e2e.py acceptance/test_run_e2e.py` 输出为空。
2. 每个变异体都让对应测试在业务断言上失败，而不是在环境或入口上失败。
3. 运行 `python3 /Users/luckye/Documents/SKILLS/project-map-skill/project-map/scripts/project_map.py status --root .`，结果为 0 problems。

## 沙箱外、审查与交付
- 沙箱外运行照旧：写 `card-5/outside-sandbox.sh`，回复 `T-075 OUTSIDE-SANDBOX READY`，由我执行。
- git 写操作单独执行，不加前缀。
- 做一次 fresh-context 只读独立审查；审查发现问题时，先做红态再修复，修复 diff 交给我审。
- 交付：a2a 提交（带尾注）、`card-5/RESULTS.md`、ticket Resolution（补充第 4 条的当前证据，保持 open，由我关闭）。终端最后一行写 `T-075 DONE <PASS|INCOMPLETE|BLOCKED> <a2a commit>`。
- 本卡不需要真实 Codex 回合。如果确实需要，先停下问我。
## 共同规则
- 先读 a2a 的 `AGENTS.md`、`CONTEXT.md`、`intent.md`（第三阶段修订）、你的 ticket（验收以它为准，依据 ticket 当前的 `ready_rev`），以及 `.project-map/specs/native-cli-orchestration-2026-10-10.md` 里 ticket 指向的章节。
- 发现 spec 与实际行为不符：停下说明（由主控写 needs-decision），不绕开。
- 不碰用户的 Herdr server（可以经 `herdr` 命令行建、关自己的 pane），不写 `~/.codex`、`~/.claude`、全局或仓库级 git 配置，不停正式工作台、不读写 `~/Library/Application Support/a2a-workbench`。不 push。只停你启动的进程，只删你创建的文件。不改 Synara fork。
- 本卡不用真实 Codex 被测会话。
- 依赖缓存放外置盘 `/Volumes/WD-Elements`，没挂载就报错，不回退到内置盘。
- 先红后绿；预期来自 ticket/spec，不来自实现输出；失败原样保留；不用正则或关键词规则判断内容含义；不加兜底重试。
- 证据放 `evidence/2026-10-10-batch12/T-075/card-5/`，中文 `RESULTS.md`，每项产物附重新生成它的命令；a2a 只提交你的文件与 ticket Resolution（保持 open，写"待主控关闭"）。完成前运行 `python3 /Users/luckye/Documents/SKILLS/project-map-skill/project-map/scripts/project_map.py status --root .`。
- 最后在终端回复一行：`T-0xx DONE <PASS|INCOMPLETE|BLOCKED> <a2a commit>`。需要决定的事停下说明，完成前不要结束回合。
- 发给你的文本经 `scripts/dispatch` 投递，带 ⟦主控 #序号⟧ 标记；没有这个标记的输入来自用户本人。
- 范围外的问题用 `scripts/inbox send --kind issue` 上报，不要自行忽略。
