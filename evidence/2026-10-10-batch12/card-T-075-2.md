# 任务卡 T-075-2

你是 a2a 的 worker（Codex），由执行主控（Claude Code）派发，只做这张卡。T-075 拆成 4 张卡串行做：
1. 门禁搬到 `workbench/`（已完成：`4d81efc`、`5fb7009`）；
2. **本卡**：三项契约改动和任务卡命令；
3. 编排后台和 Codex 窗格，跑通一次真实交付；
4. 最小 Electron 窗口。

| 字段 | 内容 |
| --- | --- |
| 编号 | T-075-2 |
| 来源 | ticket T-075，`ready_rev: 2` |
| 目标 | 门禁做到三件事：交付时检查路径边界和提交尾注；集成落到项目工作分支；任务卡可以用命令生成和校验，存进库里，门禁在任务注册时给它拍快照。之后，执行主控能用一张校验过的任务卡注册任务；越界改动、带别的任务尾注的提交、完成条件失败都会在门禁上被拒，并留下事件；通过的交付会让工作分支从 G 前进到 M。 |
| 非目标 | 不做编排后台、窗格、真实 Codex（T-075-3），也不做 Electron（T-075-4）。不做独立审查会话、红态检查、规则式检查、打回回写、集成和放弃时的打分（S2）。不做 worktree 命名与清理、冲突回写（S3）。不改 Synara fork。 |
| 修改边界 | 允许：`workbench/`（门禁源码、任务卡命令、测试）；`acceptance/` 下与三项契约改动直接相关的断言，以及新增的测试；本卡证据目录 `evidence/2026-10-10-batch12/T-075/card-2/`；ticket T-075 的 Resolution。禁止：`acceptance/` 中与本卡契约改动无关的断言、`scripts/`、`.project-map/specs/`、Synara fork、全局配置。 |
| 完成条件 | 见下方“完成条件”。 |
| 红态命令 | 新增的反例测试在起点提交上运行必须失败，在候选上必须通过。 |
| 任务类型 | 后端逻辑 |
| 修复对象 | — |
| 复杂度 | L |
| 执行器 | Codex CLI，`gpt-6-astra`，xhigh，Fast 请求 |
| 起点 | a2a `main` 当前 HEAD（开工时写进 RESULTS） |
| 唯一写入者 | 本 worker 会话（Herdr agent `s12-t075-2`，经 `scripts/launch-worker` 启动） |

## 规格依据（先读）
- spec 第 2、3、8 节；ticket T-070 Resolution 的 D22、D23、D33；ticket T-072 Resolution 的 D26。
- 本卡只做以下三项冻结契约改动：
  - 路径检查（D8）；
  - 核对提交尾注（D26）；
  - 集成目标改为项目工作分支，取代“不更新任何用户工作分支”（D33）。
- 其余冻结契约不动：锁、fence、CAS、attempt 绑定、中断恢复。

## 先交计划，停下等我
这张卡会改冻结契约和已有验收断言，所以先不要写代码。先在证据目录写 `PLAN.md`，写清以下几点：
1. **任务卡怎么替代现有的 `--oracle` 和 `--instructions`**：完成条件是命令，要说明它怎么在合并结果 M 的 worktree 里运行，以及快照怎么保证注册后不能再改。不保留两套入口；如果必须有过渡，写明理由。
2. **尾注核对规则**：
   - “本 attempt 的尾注”按哪些字段判定；
   - 没有尾注的提交，怎么记成“人工介入，action 形态的用户输入，来源为‘推断：缺尾注’”，并说明它不阻止集成；
   - 带别的任务尾注的提交，直接拒收。
3. **集成到工作分支**：
   - 在工作分支当前头 G 上合并候选，得到 M；
   - CAS 把分支从 G 推到 M；
   - 分支被某个 worktree 检出时，在那个 worktree 里快进；
   - 会覆盖未提交改动时，拒收并留下事件，不 stash，也不 reset；
   - `refs/a2a/integration` 怎么处理（不保留两个集成目标）。
4. **已有 8、9、18 项断言**：哪些因为上面三项改动要改。逐条列出旧断言、新断言和对应的规格句子，其余断言一律不动。
5. **新反例清单**：在门禁的真实 CLI 和真实 Git 上，各自被拒并留下事件：
   - 改了任务卡禁止的路径；
   - 完成条件命令失败；
   - 候选里有别的任务的尾注；
   - 有一个没带尾注的提交（被记为人工介入，标“推断：缺尾注”，集成照常）；
   - fence 过期或交付旧 attempt。
   正例：工作分支从 G 前进到 M，事件齐全。
6. **任务卡命令**：命令名、模板字段（spec 第 2 节的 13 个字段）、校验规则（缺字段拒收、完成条件不是命令拒收、任务类型只能取 8 个值之一）、版本怎么存。

写完在终端回复一行 `T-075 PLAN READY`，然后停下。我审过计划、写好执行主控决定之后，你再动手。

## 完成条件（我写好的，交付前跑一遍并保存输出）
1. 新反例和正例全部按计划通过；每个红态在起点提交上失败、在候选上通过，两边的输出都保存。
2. 用 T-075-1 的 runner 跑三套已有测试，在候选上全部通过。改过的断言要与计划第 4 点的清单逐条一致，用 `git diff <起点> -- acceptance/` 核对。
3. 至少 3 个变异体，各自让对应的测试失败：
   - 去掉路径检查；
   - 尾注核对放过别的任务的尾注；
   - 集成时不检查快进或不检查未提交改动。
4. `python3 /Users/luckye/Documents/SKILLS/project-map-skill/project-map/scripts/project_map.py status --root .` 输出 0 problems。

## 沙箱外运行
需要在沙箱外跑的验收（例如要用 ps 的恢复套件），做法同 T-075-1 的决定 02：
- 把命令写进 `card-2/outside-sandbox.sh`；
- 在终端回复一行 `T-075 OUTSIDE-SANDBOX READY`，然后停下，由我来执行；
- 不要申请提权，也不要联网。如果需要新依赖，先停下问我。

## 审查与交付
- 实现完成后，做一次 fresh-context 的只读独立审查，原文存进证据目录。
- 审查发现的问题，先拿到红态再修复；修完不再追审，由我审修复部分的 diff。
- 交付物：
  - a2a 提交（带尾注）；
  - `card-2/RESULTS.md`；
  - ticket Resolution 写“T-075-2 完成，待后续卡”，ticket 保持 open。
- 终端最后一行：`T-075 DONE <PASS|INCOMPLETE|BLOCKED> <a2a commit>`。
## 共同规则
- 先读 a2a 的 `AGENTS.md`、`CONTEXT.md`、`intent.md`（第三阶段修订）、你的 ticket（验收以它为准，依据 ticket 当前的 `ready_rev`），以及 `.project-map/specs/native-cli-orchestration-2026-10-10.md` 里 ticket 指向的章节。
- 发现 spec 与实际行为不符：停下说明（由主控写 needs-decision），不绕开。
- 不碰用户的 Herdr server（可以经 `herdr` 命令行建、关自己的 pane），不写 `~/.codex`、`~/.claude`、全局或仓库级 git 配置，不停正式工作台、不读写 `~/Library/Application Support/a2a-workbench`。不 push。只停你启动的进程，只删你创建的文件。不改 Synara fork。
- 本卡不需要真实 Codex 被测会话。
- 依赖缓存放外置盘 `/Volumes/WD-Elements`，没挂载就报错，不回退到内置盘。
- 先红后绿；预期来自 ticket/spec，不来自实现输出；失败原样保留；不用正则或关键词规则判断内容含义；不加兜底重试。
- 证据放 `evidence/2026-10-10-batch12/T-075/card-2/`，中文 `RESULTS.md`，每项产物附重新生成它的命令；a2a 只提交你的文件与 ticket Resolution（保持 open，写"待主控关闭"）。完成前运行 `python3 /Users/luckye/Documents/SKILLS/project-map-skill/project-map/scripts/project_map.py status --root .`。
- 最后在终端回复一行：`T-0xx DONE <PASS|INCOMPLETE|BLOCKED> <a2a commit>`。需要决定的事停下说明，完成前不要结束回合。
- 发给你的文本经 `scripts/dispatch` 投递，带 ⟦主控 #序号⟧ 标记；没有这个标记的输入来自用户本人。
- 范围外的问题用 `scripts/inbox send --kind issue` 上报，不要自行忽略。
