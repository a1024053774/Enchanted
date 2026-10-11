# 任务卡 T-075-3

你是 a2a 的 worker（Codex），由执行主控（Claude Code）派发，只做这张卡。T-075 拆成 4 张卡串行做：
1. 门禁搬进 `workbench/`（已完成）；
2. 三项契约改动和任务卡命令（已完成，`1273b17`、`3386c4c`、`1eb748c`）；
3. **本卡**：编排后台、Codex worker 窗格，跑通一次真实交付；
4. 最小 Electron 窗口和常驻行为（关掉窗口再重开能接上、后台重启后的恢复）。

| 字段 | 内容 |
| --- | --- |
| 编号 | T-075-3 |
| 来源 | ticket T-075，`ready_rev: 2` |
| 目标 | 编排后台作为常驻进程运行，脱离调用者的进程组，对外只有一个本地命令行入口；门禁运行在后台里。后台用 node-pty 托管一个 zsh 窗格，在里面以“不问”模式启动真实的交互式 Codex worker，带启动记录和 spec 第 5 节的环境变量，提交时自动带尾注。派发文本以 `⟦主控 #序号⟧` 写入窗格，写之前先登记。从后台的命令行入口出发，对夹具仓库走完认领、派发、交付、机械检查、验收、CAS 集成，工作分支从 G 前进到 M。本切片涉及的原始事件全部入库，只追加。 |
| 非目标 | 不做 Electron 界面（T-075-4）；不处理后台重启后的恢复（T-075-4）；不做独立审查会话、红态与规则式检查、打回回写、打分（S2）；不做 worktree 命名清理与冲突回写（S3）；不做主控窗格、收件箱入库、唤醒（S4）；不支持 Claude（本卡只做 Codex）。 |
| 修改边界 | 允许：`workbench/`（后台、命令行入口、窗格、库、钩子目录、测试、README）；本卡证据目录 `evidence/2026-10-10-batch12/T-075/card-3/`；ticket T-075 的 Resolution。禁止：`acceptance/` 已有断言、`scripts/`、`.project-map/specs/`、Synara fork、全局配置、`~/.codex`、`~/.claude`，以及正式工作台数据目录 `~/Library/Application Support/a2a-workbench`。 |
| 完成条件 | 见下方“完成条件”。 |
| 红态命令 | 在起点提交上，后台入口和窗格命令都不存在，下面完成条件里的端到端命令必须失败。 |
| 任务类型 | 后端逻辑 |
| 修复对象 | — |
| 复杂度 | L |
| 执行器 | Codex CLI，`gpt-6-astra`，xhigh，Fast 请求 |
| 起点 | a2a `main` 当前 HEAD（开工时写进 RESULTS） |
| 唯一写入者 | 本 worker 会话（Herdr agent `s12-t075-3`） |

## 执行主控已定的事项
- **数据目录**：产品默认路径为 `~/Library/Application Support/a2a-orchestrator`，放在内置盘，与正式工作台的 `a2a-workbench` 分开。本卡的所有验证都用 `/tmp` 下新建的隔离数据目录，不创建、也不写入默认路径。
- **node-pty**：执行主控已经装好 `node-pty@1.1.0`（官方源，自带 darwin-arm64 预编译），见 `c9c4d91`。因为安装时加了 `--ignore-scripts`，`prebuilds/darwin-arm64/spawn-helper` 原本没有执行位，我已经手动 `chmod 755` 补上；不补的话会报 `posix_spawnp failed`。请在 README 里写明这件事，并让后台启动时检查 spawn-helper 是否可执行，不可执行就直接报错，不自动去修。还需要别的依赖时，先停下问我。
- **运行时**：Node 26，沿用 T-075-1 的类型剥离方式。
- **worker 窗格启动**（spec 第 5、6 节和 T-074 的结论）：
  - Codex 用 `-a never`，沙箱为 workspace-write，带 `-m`、`-c model_reasoning_effort`、`-c service_tier="fast"`、`-c check_for_update_on_startup=false`；
  - 回合结束信号用每会话的 `-c notify=...` 或 Stop hook，只记录事件，不做判断；
  - 状态只认这些结构化信号，拿不到时显示“未知”，不读屏；
  - 注入用 bracketed paste，之后单独回车；在窗格空闲时才写；
  - 所有写入都经过后台。
- **钩子目录**：后台自己提供一个 git 钩子目录，写出 spec 第 8 节规定的 9 项尾注，通过 `GIT_CONFIG_*` 环境变量指向它。可以参考 `scripts/git-hooks/`，但不要改它；工作台的启动记录存在库里，不写 `records/launches.jsonl`。
- **worker 怎么交付**：交付必须经过后台的命令行入口。worker 在 Codex 沙箱里能不能连上后台的本地入口（例如 Unix socket），先做探针。连不上就停下写 needs-decision，不要放宽沙箱，也不要绕路。
- **真实 Codex 验收**：
  - 用 `/tmp` 下隔离的 CODEX_HOME：只复制 `auth.json`，只信任夹具根目录，只加 `git add`、`git commit` 两条 allow 规则；需要的 hook 只经每会话参数传入，用完把整个 home 删掉；
  - 被测 Codex 用 `gpt-6-astra` xhigh Fast，**最多 10 个主 turn**，用到上限就停下报告；
  - 注意：Codex 本周额度只剩约 21%，请尽量少用。

## 先交计划，停下等我
先写 `card-3/PLAN.md`，内容包括：
- 模块划分：后台、入口、窗格、库、门禁接线；
- 进程模型：怎样常驻、怎样脱离进程组、入口怎样连上后台、数据目录怎样布局；
- 库表：只追加的事件和启动记录；
- 窗格的启动参数与环境变量；
- 派发的登记与注入；
- 状态信号；
- 沙箱可达性探针；
- 端到端正例与反例清单：在后台入口上重跑 T-075-2 的反例，越界路径、完成条件失败、外来尾注、缺尾注、fence 过期或旧 attempt，各至少一条，都可以用脚本提交，不必用真实 Codex；
- 真实 Codex 回合预算；
- 需要在沙箱外运行的项。

写完回复一行 `T-075 PLAN READY`，然后停下。

## 完成条件（我写好的，交付前跑一遍并保存输出）
1. 从后台命令行入口出发，真实 Codex worker（在 node-pty 托管的 zsh 里）对夹具仓库完成一次交付并集成。工作分支从 G 前进到 M，候选提交带本 attempt 的 9 项尾注。证据包括：命令与输出、从库里读回的事件（启动记录、派发登记、回合开始与结束、门禁每项检查、改动行数与文件数、尾注）、Git 引用读回。
2. 第 1 条的 G 和 M 要从夹具仓库里用 `git rev-parse` 独立读回，并与库里的集成事件比对。
3. 在后台入口上，每个反例都被拒，并留下事件。
4. 后台进程确实脱离了调用者的进程组：调用命令结束后，后台仍在运行（用 ps 读回 pgid 和 sid）。
5. `python3 /Users/luckye/Documents/SKILLS/project-map-skill/project-map/scripts/project_map.py status --root .` 输出 0 problems。

## 沙箱外运行、审查与交付
- **沙箱外运行**：照旧把命令写进 `card-3/outside-sandbox.sh`，回一行 `T-075 OUTSIDE-SANDBOX READY` 后停下，由我执行。真实 Codex 窗格的启动大概率也要在沙箱外跑，请把它写进这个脚本。
- **探针或测试本身的错误**：可以直接修，但要记录修了什么，并换新标签重跑，不用停下来等我（同 T-075-2 决定 03）。
- **独立审查**：只做一次 fresh-context 的只读独立审查。审查发现问题时，先拿到红态再修；修复部分的 diff 由我来审。
- **交付内容**：a2a 提交（带尾注）、`card-3/RESULTS.md`、ticket Resolution（写“T-075-3 完成，待后续卡”，保持 open）。终端最后一行：`T-075 DONE <PASS|INCOMPLETE|BLOCKED> <a2a commit>`。
## 共同规则
- 先读 a2a 的 `AGENTS.md`、`CONTEXT.md`、`intent.md`（第三阶段修订）、你的 ticket（验收以它为准，依据 ticket 当前的 `ready_rev`），以及 `.project-map/specs/native-cli-orchestration-2026-10-10.md` 里 ticket 指向的章节。
- 发现 spec 与实际行为不符：停下说明（由主控写 needs-decision），不绕开。
- 不碰用户的 Herdr server（可以经 `herdr` 命令行建、关自己的 pane），不写 `~/.codex`、`~/.claude`、全局或仓库级 git 配置，不停正式工作台、不读写 `~/Library/Application Support/a2a-workbench`。不 push。只停你启动的进程，只删你创建的文件。不改 Synara fork。
- 真实 Codex 调用：见上文“真实 Codex 验收”。
- 依赖缓存放外置盘 `/Volumes/WD-Elements`，没挂载就报错，不回退到内置盘。
- 先红后绿；预期来自 ticket/spec，不来自实现输出；失败原样保留；不用正则或关键词规则判断内容含义；不加兜底重试。
- 证据放 `evidence/2026-10-10-batch12/T-075/card-3/`，中文 `RESULTS.md`，每项产物附重新生成它的命令；a2a 只提交你的文件与 ticket Resolution（保持 open，写"待主控关闭"）。完成前运行 `python3 /Users/luckye/Documents/SKILLS/project-map-skill/project-map/scripts/project_map.py status --root .`。
- 最后在终端回复一行：`T-0xx DONE <PASS|INCOMPLETE|BLOCKED> <a2a commit>`。需要决定的事停下说明，完成前不要结束回合。
- 发给你的文本经 `scripts/dispatch` 投递，带 ⟦主控 #序号⟧ 标记；没有这个标记的输入来自用户本人。
- 范围外的问题用 `scripts/inbox send --kind issue` 上报，不要自行忽略。
