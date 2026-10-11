# 任务卡 T-079-1

你是 a2a 的 worker（Codex），由执行主控（Claude Code）派发，只做这张卡。

| 字段 | 内容 |
| --- | --- |
| 编号 | T-079-1 |
| 来源 | ticket T-079，`ready_rev: 1`（执行主控自建的缺陷票） |
| 目标 | `scripts/launch-worker` 不再偶发 `agent_pane_busy`：等新 pane 的 shell 真正就绪后再启动 agent。启动记录与尾注行为保持不变。 |
| 非目标 | 不改 `scripts/dispatch`、钩子、打分，也不改用户的 Herdr server 和全局配置；不加盲目重试。 |
| 修改边界 | 允许：`scripts/launch-worker`；`acceptance/` 下与 launcher 相关的新测试，或者 `scripts/` 的测试夹具；本卡证据目录 `evidence/2026-10-11-batch13/T-079/`；ticket T-079 的 Resolution。禁止：`workbench/`（T-076 正在改）、其他脚本、spec、地图。 |
| 完成条件 | 见下方。 |
| 红态命令 | 在起点提交上按 ticket 的方式重复启动，复现 `agent_pane_busy`，并记录复现次数和条件。 |
| 任务类型 | 缺陷修复 |
| 修复对象 | T-073（`3cf85f4`，`scripts/launch-worker`） |
| 复杂度 | S |
| 执行器 | Codex CLI，`gpt-6.1-sol`，xhigh，Fast 请求 |
| 起点 | a2a `main` 当前 HEAD |
| 唯一写入者 | 本 worker 会话（Herdr agent `s13-t079`） |

## 已知事实（执行主控观察）
- 失败出现在 `herdr pane run <pane> 'export ...'` 之后，立即调用 `herdr agent start` 时。
- `herdr pane split --env KEY=VALUE` 可以直接把环境变量带进新 shell，从而省掉 export 这一步。
- `herdr pane get` 在 shell 初始化完成后，revision 会变化、terminal title 会出现，但这不是一个明确的“就绪”信号。`herdr agent start --help` 写的是 “The pane must be at its interactive shell prompt”。请查清楚 herdr 有没有可用的结构化就绪判据（读 `--help` 和文档）。如果没有，就停下报告给我，不要用读屏判断。

## 完成条件
1. 红态：在起点上重复启动（次数由你定，至少 10 次），出现 `agent_pane_busy`，或者如实报告无法复现。
2. 修复后，同样次数的启动全部成功；每条启动记录的字段都齐全（与 T-073 相同）；用一个夹具 worker 提交一次，尾注 9 项都在。
3. 只关闭自己创建的 pane，启动的 Codex 不发任何任务，不消耗模型回合。
4. 运行 `project_map.py status`，结果为 0 problems。

## 交付
a2a 提交（带尾注）、`evidence/2026-10-11-batch13/T-079/RESULTS.md`、ticket Resolution（写“待主控关闭”）。终端最后一行：`T-079 DONE <PASS|INCOMPLETE|BLOCKED> <a2a commit>`。这张卡是 S 级，可以不做独立审查，由我来审 diff。
## 共同规则
- 先读 a2a 的 `AGENTS.md`、`CONTEXT.md`、`intent.md`（第三阶段修订）、你的 ticket（验收以它为准，依据 ticket 当前的 `ready_rev`），以及 `.project-map/specs/native-cli-orchestration-2026-10-10.md` 里 ticket 指向的章节。
- 发现 spec 与实际行为不符：停下说明（由主控写 needs-decision），不绕开。
- 不碰用户的 Herdr server（可以经 `herdr` 命令行建、关自己的 pane），不写 `~/.codex`、`~/.claude`、全局或仓库级 git 配置，不停正式工作台、不读写 `~/Library/Application Support/a2a-workbench`。不 push。只停你启动的进程，只删你创建的文件。不改 Synara fork。
- 本卡不需要真实模型回合。被启动的 Codex 不发任何任务，启动后直接关掉自己的 pane。
- 依赖缓存放外置盘 `/Volumes/WD-Elements`，没挂载就报错，不回退到内置盘。
- 先红后绿；预期来自 ticket/spec，不来自实现输出；失败原样保留；不用正则或关键词规则判断内容含义；不加兜底重试。
- 证据放 `evidence/2026-10-11-batch13/T-079/`，中文 `RESULTS.md`，每项产物附重新生成它的命令；a2a 只提交你的文件与 ticket Resolution（保持 open，写"待主控关闭"）。完成前运行 `python3 /Users/luckye/Documents/SKILLS/project-map-skill/project-map/scripts/project_map.py status --root .`。
- 最后在终端回复一行：`T-0xx DONE <PASS|INCOMPLETE|BLOCKED> <a2a commit>`。需要决定的事停下说明，完成前不要结束回合。
- 发给你的文本经 `scripts/dispatch` 投递，带 ⟦主控 #序号⟧ 标记；没有这个标记的输入来自用户本人。
- 范围外的问题用 `scripts/inbox send --kind issue` 上报，不要自行忽略。
- 证据大小：单个证据文件超过 5 MB 的原始输出（大 JSON、trace、tar）不直接提交。要么压缩后提交，要么放外置盘 `/Volumes/WD-Elements/a2a-evidence/<批次>/<票>/` 归档；仓库里只留摘要、重放命令和归档路径。提交前用 `find <证据目录> -size +5M` 检查。
- 需要在沙箱外运行的部分（Unix socket、ps、真实 Codex、Electron、自建进程信号），统一写进本卡的 `outside-sandbox.sh`，然后回复 `T-0xx OUTSIDE-SANDBOX READY` 并停下，由执行主控执行。不要申请提权。
- git 写操作：`git add`、`git commit` 各自单独执行，不和别的命令串联，也不加环境变量前缀。
- 探针或测试本身的错误可以直接修，但要记录；真实的协议失败或产品失败、无法判定的情况、需要改业务断言的情况，都要停下来交给我。
