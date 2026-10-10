# 任务卡 T-074-1

你是 a2a 的 worker（Codex），由执行主控（Claude Code）派发，只做这张卡。

| 字段 | 内容 |
| --- | --- |
| 编号 | T-074-1 |
| 来源 | ticket T-074，`ready_rev: 1` |
| 目标 | 用探针核实 R6、R7 两个事实并写成报告。R6：Codex（和 Claude Code）等用户确认时，外部程序能不能拿到结构化信号。R7：从外部往 node-pty 托管的 zsh 窗格注入带 `⟦主控 #序号⟧` 的一行文字，两家 CLI 能否稳定当作一条新用户消息。结论决定 T-075 能否按 spec 做。 |
| 非目标 | 不写产品代码；不定成功率门槛（由构思主控和用户定）；不改用读屏或正则判断状态；不做 T-075。 |
| 修改边界 | 允许：本卡证据目录 `evidence/2026-10-10-batch12/T-074/`（探针代码、临时装的 node-pty；依赖缓存放外置盘）；`findings/` 下新增一份中文报告；ticket Resolution。禁止：产品目录、`scripts/`、`~/.codex`、`~/.claude`、全局配置、Synara fork。 |
| 完成条件 | 见下方"完成条件"。 |
| 红态命令 | —（事实核实，不适用） |
| 任务类型 | 调研 |
| 修复对象 | — |
| 复杂度 | M |
| 执行器 | Codex CLI，`gpt-6.1-sol`，xhigh，Fast 请求 |
| 起点 | a2a `main` 当前 HEAD（开工时写进 RESULTS） |
| 唯一写入者 | 本 worker 会话（Herdr agent `s12-t074`） |

## 两道闸
1. **Codex 部分先做。** 用隔离 CODEX_HOME（见共同规则）。被测的 Codex 跑在你自己用 node-pty 起的 zsh 里，不是 Herdr pane。
2. **Claude Code：在第一次真实启动之前停下。** 交互式 Claude Code 需要认证；ticket 要求不写 `~/.claude`，"认证方式拿不准时先停下问"。T-059 已经调查过认证路径，见 `evidence/2026-10-09-batch11/T-059/needs-decision-04.md`，可以直接引用，不必重查。Codex 部分做完后，写一份 needs-decision，说明 Claude 部分需要的认证方式选项和预计 turn 数，然后交 BLOCKED。认证由用户定，我经构思主控转达。只读 `--help` 和不调用模型的探针可以先做。

## 完成条件（我写好的，交付前跑一遍并保存输出）
1. R7 的原始注入记录存成 `T-074/r7-injections.jsonl`，一次注入一行，至少包含这些字段：`cli`、`state`（`idle`/`running`/`awaiting_approval`）、`registered_text`（写入前登记的文字）、`registered_at`、`observed_text`（CLI 实际收到的，取自 rollout 或会话记录，不取自屏幕）、`outcome`（`ok`/`lost`/`merged`/`taken_as_approval`/`other`）。下面的命令能跑通，并对 Codex 打印三种状态各自的次数，合计不少于 10：
   `python3 -c "import json,collections;c=collections.Counter((r['cli'],r['state'],r['outcome']) for r in map(json.loads,open('evidence/2026-10-10-batch12/T-074/r7-injections.jsonl')));[print(*k,v) for k,v in sorted(c.items())]"`
2. R6 每个结论都标 observed/measured/inferred/unknown，附原始输出、CLI 版本、启动 argv 和重放命令。至少真实触发一次 Codex 的等确认状态，记下外部程序收到了什么、什么时刻收到。没有信号就写"未找到"并列出查过的途径。
3. `findings/` 下的报告写明对 T-075 的影响：可以按 spec 做、要改设计、还是要停下。"等确认时注入的文字被当作确认的回答"单独列出。
4. `python3 /Users/luckye/Documents/SKILLS/project-map-skill/project-map/scripts/project_map.py status --root /Users/luckye/Documents/Code/a2a` 没有 problems。

ticket 里的失败方式清单逐条写进 RESULTS 的处理方式。任一项不通过就停下写 needs-decision，不加兜底重试。

## 交付
a2a 提交 + `T-074/RESULTS.md` + ticket Resolution（保持 open，写"待主控关闭"）+ 终端一行 `T-074 DONE <PASS|INCOMPLETE|BLOCKED> <a2a commit>`。这是事实报告，不另开独立审查，由我核对原始记录。
## 共同规则
- 先读 a2a 的 `AGENTS.md`、`CONTEXT.md`、`intent.md`（第三阶段修订）、你的 ticket（验收以它为准，依据 ticket 当前的 `ready_rev`），以及 `.project-map/specs/native-cli-orchestration-2026-10-10.md` 里 ticket 指向的章节。
- 发现 spec 与实际行为不符：停下说明（由主控写 needs-decision），不绕开。
- 不碰用户的 Herdr server（可以经 `herdr` 命令行建、关自己的 pane），不写 `~/.codex`、`~/.claude`、全局或仓库级 git 配置，不停正式工作台、不读写 `~/Library/Application Support/a2a-workbench`。不 push。只停你启动的进程，只删你创建的文件。不改 Synara fork。
- 真实 Codex 调用：/tmp 下隔离 CODEX_HOME，只复制 auth.json，只信任夹具根，只有 git add/commit 两条规则，无 hook，用完删整个 home；启动参数带 `-c 'service_tier="fast"'` 和 `check_for_update_on_startup=false`。turn 数尽量少，实际用量写进 RESULTS。
- 依赖缓存放外置盘 `/Volumes/WD-Elements`，没挂载就报错，不回退到内置盘。
- 先红后绿；预期来自 ticket/spec，不来自实现输出；失败原样保留；不用正则或关键词规则判断内容含义；不加兜底重试。
- 证据放本批目录 `evidence/2026-10-10-batch12/T-0xx/`，中文 `RESULTS.md`，每项产物附重新生成它的命令；a2a 只提交你的文件与 ticket Resolution（保持 open，写"待主控关闭"）。完成前运行 `python3 /Users/luckye/Documents/SKILLS/project-map-skill/project-map/scripts/project_map.py status --root .`。
- 最后在终端回复一行：`T-0xx DONE <PASS|INCOMPLETE|BLOCKED> <a2a commit>`。需要决定的事停下说明，完成前不要结束回合。
- 发给你的文本经 `scripts/dispatch` 投递，带 ⟦主控 #序号⟧ 标记；没有这个标记的输入来自用户本人。
- 范围外的问题用 `scripts/inbox send --kind issue` 上报，不要自行忽略。
