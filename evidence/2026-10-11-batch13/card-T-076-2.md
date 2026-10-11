# 任务卡 T-076-2

你是 a2a 的 worker（Codex），由执行主控（Claude Code）派发，只做这一张卡。T-076-1 已经完成（`42e2b8ed`、`d95f4171`），内容包括尾注写实际模型、多回合身份、后台停止、一致性检查器和五类变异体。

| 字段 | 内容 |
| --- | --- |
| 编号 | T-076-2 |
| 来源 | ticket T-076，`ready_rev: 1` |
| 目标 | 实现 ticket T-076 What to build 的第 1～4 项：(1) 红态检查和规则式检查；(2) 打回回写，同一 attempt 连续 3 次打回后停止自动回写；(3) 独立审查会话，后台新开只读的 reviewer，结论绑定候选提交号，门禁核对会话的独立性；(4) 集成和放弃命令带打分，缺少执行主控必填项时拒收，`records/scores.jsonl` 的格式与之对齐。 |
| 非目标 | T-077 的 worktree 命名、清理、R8（另一个 worker 在 `exec/t077` 分支上做，只预留衔接）；T-078 的主控窗格和收件箱；改存储结构。 |
| 修改边界 | 允许：主 checkout 中的 `workbench/src/`、`workbench/hooks/`、`workbench/tests/`、`workbench/README.md`；本卡证据目录 `evidence/2026-10-11-batch13/T-076/card-2/`；ticket T-076 的 Resolution。禁止：`acceptance/test_*.py` 的断言（如果和新契约冲突，按 T-075-2 / T-077 的先例交白名单）、`scripts/`（Herdr 期的 `scripts/score` 只能读，不能改；格式对齐通过后台导入或校验完成）、spec、地图、全局配置。 |
| 完成条件 | 见 ticket T-076 的 Acceptance，逐条对应，包括正例：第一次打回 → 自动回写 → 修好后重交 → 审查判为可合并 → 带打分集成；以及六类反例。 |
| 红态命令 | 每项新行为都要先在起点上失败。 |
| 任务类型 | 后端逻辑 |
| 修复对象 | — |
| 复杂度 | L |
| 执行器 | Codex CLI，`gpt-6-astra`，xhigh，Fast 请求。选用理由：门禁检查串、回写协议、审查会话的独立性核对和打分接口相互交织，属于复杂任务。 |
| 起点 | a2a `main` 的当前 HEAD（开工时写进 RESULTS） |
| 唯一写入者 | 本 worker 会话（Herdr agent `s13-t076-2`），工作目录为主 checkout `/Users/luckye/Documents/Code/a2a` |

## 先交计划，停下等我
写 `card-2/PLAN.md`，内容包括：
1. 检查串的顺序与接口：路径、完成条件、红态、规则式检查、尾注；规则式检查从哪里读项目配置。
2. 回写协议：`⟦门禁 #序号⟧` 的格式、登记、按空闲注入、3 次上限，以及停止后怎么上报。
3. 审查会话：
   - 启动参数怎么设，包括 Codex 只读沙箱，以及它怎么交付结论（参照卡 3 的 B 通道）；
   - 结论的数据结构；
   - 门禁怎么核对“这个审查会话不是写入会话、是为本次新开的、结论绑定的提交号和候选一致”；
   - “需修复”的清单怎么写回 worker。
4. 打分参数和拒收规则，与 `records/scores.jsonl` 怎么对齐（字段映射）。
5. 与 T-077 的衔接点：R8 重验时沿用审查结论的条件、验收与审查用 worktree 的命名，以及预计冲突的位置。
6. 已有 8/9/18 和 T-075/T-076-1 的断言里，会和新契约冲突的部分，按白名单格式列出，等我批准。
7. 红态与反例清单；真实回合预算，worker 和 reviewer 合计上限 8 个（都用 `gpt-6.1-sol` xhigh Fast），写清每个回合的用途；需要在沙箱外运行的项。

写完回复 `T-076 PLAN READY`，然后停下等我。

## 审查与交付
- 做一次 fresh-context 只读独立审查（这是本卡自己的交付审查，和产品里的审查会话是两回事）；审查发现的问题，先拿到红态再修，修复部分的 diff 交我审。
- 交付：a2a 提交（带尾注）、`card-2/RESULTS.md`、ticket Resolution（写清 T-076 每条验收项的证据位置，保持 open）。
- 终端最后一行：`T-076 DONE <PASS|INCOMPLETE|BLOCKED> <a2a commit>`。
## 共同规则
- 先读 a2a 的 `AGENTS.md`、`CONTEXT.md`、`intent.md`（第三阶段修订）、你的 ticket（验收以它为准，依据 ticket 当前的 `ready_rev`），以及 `.project-map/specs/native-cli-orchestration-2026-10-10.md` 里 ticket 指向的章节。
- 发现 spec 与实际行为不符：停下说明（由主控写 needs-decision），不绕开。
- 不碰用户的 Herdr server（可以经 `herdr` 命令行建、关自己的 pane），不写 `~/.codex`、`~/.claude`、全局或仓库级 git 配置，不停正式工作台、不读写 `~/Library/Application Support/a2a-workbench`。不 push。只停你启动的进程，只删你创建的文件。不改 Synara fork。
- 真实 Codex 调用：/tmp 下隔离 CODEX_HOME，只复制 auth.json，只信任夹具根，只有 git add/commit 两条规则，产品启动参数安装的会话 hook 与尾注 hook 由执行主控逐次批准（见 PLAN 审批），不复制用户 hook，用完删整个 home；启动参数带 `-c 'service_tier="fast"'` 和 `check_for_update_on_startup=false`。turn 数尽量少，实际用量写进 RESULTS。本卡 worker 与 reviewer 合计上限 8 个主 turn。
- 依赖缓存放外置盘 `/Volumes/WD-Elements`，没挂载就报错，不回退到内置盘。
- 先红后绿；预期来自 ticket/spec，不来自实现输出；失败原样保留；不用正则或关键词规则判断内容含义；不加兜底重试。
- 证据放 `evidence/2026-10-11-batch13/T-076/card-2/`，中文 `RESULTS.md`，每项产物附重新生成它的命令；a2a 只提交你的文件与 ticket Resolution（保持 open，写"待主控关闭"）。完成前运行 `python3 /Users/luckye/Documents/SKILLS/project-map-skill/project-map/scripts/project_map.py status --root .`。
- 最后在终端回复一行：`T-0xx DONE <PASS|INCOMPLETE|BLOCKED> <a2a commit>`。需要决定的事停下说明，完成前不要结束回合。
- 发给你的文本经 `scripts/dispatch` 投递，带 ⟦主控 #序号⟧ 标记；没有这个标记的输入来自用户本人。
- 范围外的问题用 `scripts/inbox send --kind issue` 上报，不要自行忽略。
- 证据大小：单个证据文件超过 5 MB 的原始输出（大 JSON、trace、tar）不直接提交。要么压缩后提交，要么放外置盘 `/Volumes/WD-Elements/a2a-evidence/<批次>/<票>/` 归档；仓库里只留摘要、重放命令和归档路径。提交前用 `find <证据目录> -size +5M` 检查。
- 需要在沙箱外运行的部分（Unix socket、ps、真实 Codex、Electron、自建进程信号），统一写进本卡的 `outside-sandbox.sh`，然后回复 `T-0xx OUTSIDE-SANDBOX READY` 并停下，由执行主控执行。不要申请提权。
- git 写操作：`git add`、`git commit` 各自单独执行，不和别的命令串联，也不加环境变量前缀。
- 探针或测试本身的错误可以直接修，但要记录；真实的协议失败或产品失败、无法判定的情况、需要改业务断言的情况，都要停下来交给我。
