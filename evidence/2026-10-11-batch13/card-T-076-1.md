# 任务卡 T-076-1

你是 a2a 的 worker（Codex），由执行主控（Claude Code）派发，只做这一张卡。T-076 分两张卡串行做：
- **本卡**：补上 S1 留下的缺口；
- T-076-2：质量串主体，包括红态与规则式检查、打回回写、独立审查会话、打分。

| 字段 | 内容 |
| --- | --- |
| 编号 | T-076-1 |
| 来源 | ticket T-076，`ready_rev: 1` |
| 目标 | 补上 T-075 留下的四个缺口：(1) 受管 worker 提交里的 `A2A-Model`、`A2A-Effort` 写实际值，与启动记录一致，不再是 unknown；(2) 回执或打回带来新回合后，run 与 reclaim 仍能核对身份，伪造的别的会话仍被拒；(3) 一项一致性检查：用事件重建状态，与状态表比对，并如实报告结果；(4) T-075 卡 4 计划里的五类产品变异体，各自在业务断言上失败。 |
| 非目标 | 不做红态与规则式检查、打回回写、独立审查会话、打分（T-076-2）；不做 worktree 命名与清理（T-077）；不做主控窗格（T-078）；一致性检查发现不一致时不改存储（停下报告，另外切片）；不改 `acceptance/` 断言。 |
| 修改边界 | 允许：`workbench/src/`（门禁核心、窗格、钩子、后台中与上述四项直接相关的部分）、`workbench/hooks/`、`workbench/tests/`、`workbench/README.md`；本卡证据目录 `evidence/2026-10-11-batch13/T-076/card-1/`；ticket T-076 的 Resolution。禁止：`acceptance/test_*.py` 的断言、`scripts/`（T-079 正在改 `scripts/launch-worker`）、spec、地图、全局配置、Synara fork。 |
| 完成条件 | 见下方。 |
| 红态命令 | 每一项都要先在起点提交上取得失败：尾注里出现 unknown；回执回合之后 reclaim 报 identity_conflict；一致性检查器不存在；五个变异体各自没有被现有测试抓住，或者测试不存在。 |
| 任务类型 | 缺陷修复 |
| 修复对象 | T-075（`75492f6b`）的已知缺口 1、2、3、5 |
| 复杂度 | M |
| 执行器 | Codex CLI，`gpt-6.1-sol`，xhigh，Fast 请求（默认模型） |
| 起点 | a2a `main` 当前 HEAD（开工时写进 RESULTS） |
| 唯一写入者 | 本 worker 会话（Herdr agent `s13-t076-1`） |

## 依据
- T-075 的 Resolution 和完成报告 `20261011T094922Z-executor-report-001`；
- 问题上报 `20261011T052530Z`（多回合）和 `20261011T042856Z`（状态表）；
- `evidence/2026-10-10-batch12/T-075/card-4/PLAN.md` 第 8 节的五类变异体；
- spec 第 8、9 节。

## 先交计划，停下等我
写 `card-1/PLAN.md`，说明以下几点：

1. **尾注的取值来源。** 建议在启动时把启动记录里的模型和强度写进会话环境，让钩子在沙箱里也能拿到，不需要连接后台。还要写明“最近一轮的实际模型”和“请求的模型”怎样区分。
2. **多回合身份。** 把“原生会话与领导进程身份”和“本次交付绑定的回合”拆成两件事，写出 run 与 reclaim 各自核对哪一项；先取红态。不得删掉或放宽身份检查，伪造会话的反例必须保留。
3. **一致性检查。**
   - 写明检查器放在哪里、怎么用事件重建状态、比较哪些表。
   - 已知的嫌疑点要逐一核对：attachment creating 没有对应事件；saveAttachment 与 attached 事件不在同一事务；memberships 和 session_presets 在另一个库里，不经过 save()。
   - 结果只报告，不修存储。
4. **五类变异体**：每一类分别改什么、对应哪一条业务断言、在哪个入口上跑。
5. **需要在沙箱外运行的项**，以及真实 Codex 回合预算。尾注这一项至少需要 1 个真实回合，本卡上限 3 个。

写完回复 `T-076 PLAN READY`，然后停下。

## 完成条件（我写好的）
1. 一次真实的受管 worker 提交，尾注里的 `A2A-Model`、`A2A-Effort` 与启动记录一致。执行主控会用 `git log -1 --format=%B` 读回比对。
2. 多回合：红态测试在起点上失败；在候选上，回执回合之后 run 与 reclaim 都能通过，伪造的别的会话仍然被拒。
3. 一致性检查在一个完整交付的夹具库上运行，输出逐表结果（一致，或者不一致及原因）。
4. 五个变异体都在业务断言上失败，不是在环境层面失败。
5. 8/9/18 用 `workbench/tests/run_daemon_acceptance.py` 跑三套，全部通过；`acceptance/` 的断言 diff 为空。
6. `project_map.py status` 0 problems。

## 审查与交付
- 一次 fresh-context 只读独立审查；发现的问题先取红态再修，修复部分的 diff 交给我审。
- 交付：a2a 提交（带尾注）、`card-1/RESULTS.md`、ticket Resolution（写“T-076-1 完成，待 T-076-2”，保持 open）。
- 终端最后一行：`T-076 DONE <PASS|INCOMPLETE|BLOCKED> <a2a commit>`。
## 共同规则
- 先读 a2a 的 `AGENTS.md`、`CONTEXT.md`、`intent.md`（第三阶段修订）、你的 ticket（验收以它为准，依据 ticket 当前的 `ready_rev`），以及 `.project-map/specs/native-cli-orchestration-2026-10-10.md` 里 ticket 指向的章节。
- 发现 spec 与实际行为不符：停下说明（由主控写 needs-decision），不绕开。
- 不碰用户的 Herdr server（可以经 `herdr` 命令行建、关自己的 pane），不写 `~/.codex`、`~/.claude`、全局或仓库级 git 配置，不停正式工作台、不读写 `~/Library/Application Support/a2a-workbench`。不 push。只停你启动的进程，只删你创建的文件。不改 Synara fork。
- 真实 Codex 调用：/tmp 下隔离 CODEX_HOME，只复制 auth.json，只信任夹具根，只有 git add/commit 两条规则，无 hook，用完删整个 home；启动参数带 `-c 'service_tier="fast"'` 和 `check_for_update_on_startup=false`。turn 数尽量少，实际用量写进 RESULTS。本卡上限 3 个主 turn，被测会话用 `gpt-6.1-sol` xhigh Fast。
- 依赖缓存放外置盘 `/Volumes/WD-Elements`，没挂载就报错，不回退到内置盘。
- 先红后绿；预期来自 ticket/spec，不来自实现输出；失败原样保留；不用正则或关键词规则判断内容含义；不加兜底重试。
- 证据放 `evidence/2026-10-11-batch13/T-076/card-1/`，中文 `RESULTS.md`，每项产物附重新生成它的命令；a2a 只提交你的文件与 ticket Resolution（保持 open，写"待主控关闭"）。完成前运行 `python3 /Users/luckye/Documents/SKILLS/project-map-skill/project-map/scripts/project_map.py status --root .`。
- 最后在终端回复一行：`T-0xx DONE <PASS|INCOMPLETE|BLOCKED> <a2a commit>`。需要决定的事停下说明，完成前不要结束回合。
- 发给你的文本经 `scripts/dispatch` 投递，带 ⟦主控 #序号⟧ 标记；没有这个标记的输入来自用户本人。
- 范围外的问题用 `scripts/inbox send --kind issue` 上报，不要自行忽略。
- 证据大小：单个证据文件超过 5 MB 的原始输出（大 JSON、trace、tar）不直接提交。要么压缩后提交，要么放外置盘 `/Volumes/WD-Elements/a2a-evidence/<批次>/<票>/` 归档；仓库里只留摘要、重放命令和归档路径。提交前用 `find <证据目录> -size +5M` 检查。
- 需要在沙箱外运行的部分（Unix socket、ps、真实 Codex、Electron、自建进程信号），统一写进本卡的 `outside-sandbox.sh`，然后回复 `T-0xx OUTSIDE-SANDBOX READY` 并停下，由执行主控执行。不要申请提权。
- git 写操作：`git add`、`git commit` 各自单独执行，不和别的命令串联，也不加环境变量前缀。
- 探针或测试本身的错误可以直接修，但要记录；真实的协议失败或产品失败、无法判定的情况、需要改业务断言的情况，都要停下来交给我。
