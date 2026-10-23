---
id: T-133
title: 界面显示用户输入记录与人工介入
type: build
status: closed
blocked_by: []
claimed_by:
supersedes:
ready: yes
ready_by: executor
ready_rev: 1
---

## What to build

来源：用户 2026-10-22 逐字：“107 吧多 worker 做出来，早期的调研票关掉，然后还缺的都做”。 切换条件里的“用户输入记录”：门禁的 `user_inputs` 表已记下用户在窗格里亲手打的字、面板答复等（T-050 语义），受管 worker 窗格里的输入记为人工介入；界面只有一个标签，看不到记录。

- 按项目、任务、会话列出用户输入：时间、形态（键入、面板答复、审批等，按库里已有的字段）、目标会话与角色、文本；落在受管 worker 窗格里的标“人工介入”。
- 只读，不改库；派发与注入的文字不出现在这里（记录器已跳过已登记的注入）。

## Acceptance

- [x] 真实 Electron：夹具里用户在主控终端和受管 worker 窗格各打一段字、在面板答复一条；视图列出三条，worker 那条标人工介入，内容与库读回一致；后台注入的派发文字不出现。修前没有这个视图。
- [x] 截图与复现命令入证据。

## 不做

不做含义标注与抽取（MAP“Not yet specified”）；不改记录器。

## Status

2026-10-22：INCOMPLETE。记录页、人工介入标记、受管窗格与面板答复已做，并经端到端与独立审查（`evidence/2026-10-22-batch20/T-133-T-134/`，代码与 T-134 同批）。缺验收第一条中的“主控终端”：项目终端的输入只转发、不记录。补上需要用户定方案：A 只记已批准主控 CLI 提交的整句（CLI 自己的提交钩子，经每会话启动参数传入）；B 记批准后的全部键入；C 不记。

## 用户决定（2026-10-22）

用户逐字（在本 session 对“项目终端里的输入怎么记”A/B/C 三选一的回复）：“1.T-133 A 2.可以 3.把“有未答复的问题上报”显示成它 具体是什么意思? 4.要修 5.显示出来吧 6.默认关闭,可以手动开启,然后软件要有一个Reflect 页面,能够展示曾经启动过的主控,以及它下面启动的执行主控,worker 之类的,因为有主控打分嘛,这个打分也要在每个员工里显示出来,以后这个 Reflect 界面就是用于复盘的,把启动复盘的设置之类的相关的都挪到这个界面,先不用送到构思主控,在这个设置界面可以选由哪个 cli 的哪个模型的哪个 effort 来执行复盘.”。第 1 条“T-133 A”选 A。

方案 A：只记已批准主控 CLI 提交的整句。用 CLI 自己的提交钩子，经每会话的启动参数传入，不写全局配置。

- Claude Code：项目终端的 `claude` 包装脚本已经给本会话加载 Enchanted 插件（`--plugin-dir`），钩子放进插件。
- Codex：包装脚本加 `-c hooks.UserPromptSubmit=…`。先用探针确认在用户真实的 `~/.codex` 下是否会弹出钩子信任、是否会写用户配置；会写的话停下报告，不用 `--dangerously-bypass-hook-trust` 绕过。
- 后台只在该终端持有已批准角色时记录；没批准的会话、普通终端都不记。

## 方案 A 实现（2026-10-22）

- **Claude Code 一侧：INCOMPLETE。** 代码复审没有阻碍项；ticket 层面不关，原因是 Codex 一侧未完成。
  - **代码**：`36fa74f6a`～`c24d58955`（候选 1）、`fbf68c404`（候选 2）。
  - **测试修正**：`1c61918ee`、`cb6e7d75c`。
  - **做法**：插件钩子 `a2a hook`。后台只在终端持有已批准角色、且会话是角色申请里的那个原生会话时记录：提交的整句记为 `controller-terminal` 渠道的消息，对它提问的答复记为答复。
  - **证据**：`evidence/2026-10-22-batch20/T-133-T-107/`。
    - 候选 1：green 10 项 PASS。
    - 候选 2：green-02 11 项 PASS，新增 `three_kinds_in_one_view`：主控终端提交、面板答复、受管窗格键入出现在同一次运行的同一视图。首个 green 因测试没处理门禁锁占用而失败，原样保留。
    - 变异“没批准也记”失败。
  - **独立审查**：review-01 INCOMPLETE（2 条 P2、2 条 P3）。review-02 INCOMPLETE，理由只是下面的 Codex 与 T-107 #3，另有 2 条 P3：
    - 检查没逐条比对 worker 两行的显示文本。不改：green-02 的记录页读回文本正确；主控终端行的文本已逐条检查。
    - 终端父级没匹配到角色时进“未归属”。符合票面“关系不明进未归属”，不改。
- **Codex 一侧：BLOCKED，等用户定。** 探针（`codex-hook-probe/RESULTS.md`）：
  - 经 `-c` 传入的钩子会弹出信任提示；
  - 信任后 Codex 把 `hooks.state` 写进 `CODEX_HOME/config.toml`，在用户真实环境里就是 `~/.codex/config.toml`；
  - 经 `-c` 预填的信任不生效。
  - 按决定停下，没有用 `--dangerously-bypass-hook-trust`。

## 用户决定：Codex 一侧（2026-10-22）

用户逐字（在本 session 对“Codex 钩子 A/B/C”与“T-107 #3 一/二”两问的回复）：“1. A 2. 一二都要.”第 1 条选 A：Codex 主控也记录，用户在自己的 Codex 里信任一次 Enchanted 的钩子，由 Codex 自己把信任写进 `~/.codex/config.toml`；a2a 不写用户配置，不用 `--dangerously-bypass-hook-trust`。接法依据 `evidence/2026-10-22-batch20/T-133-T-107/codex-hook-probe/RESULTS.md` 的 probe-04～06。

## Resolution

2026-10-22 关闭，PASS。

- **Claude Code 一侧**（方案 A）：
  - 代码 `36fa74f6a`～`c24d58955`、`fbf68c404`；
  - 证据 `evidence/2026-10-22-batch20/T-133-T-107/candidate-1`、`candidate-2`；
  - 同一次运行里，记录页列出主控终端提交、面板答复、受管窗格键入三种；
  - 审查 review-01、02 没有阻碍项。
- **Codex 一侧**（用户定 A）：
  - 代码 `af838d77e`、`d0c006ee1`；
  - 证据 `candidate-3`（NO_GO：一个变异存活、一处测试错误）与 `candidate-4`（PASS）；
  - candidate-4 的 Codex green 14 项 PASS，修前 `d0f89b48a` 与 3 个变异失败，审查 PASS（1 条 P2、3 条 P3，处理见 RESULTS）。
  - 包装脚本经 `-c` 传入三个钩子；用户在 Codex 里信任一次，信任由 Codex 写进用户配置，a2a 不写。
  - 用户自己 `hooks.json` 的钩子照常运行；用户对 `request_user_input_async` 的答复记为“问题：答复”。
- **已知边界**：
  - 没有在用户真实的 `~/.codex` 里跑过：信任要用户亲手点；
  - 默认沙箱下 `a2a request` 能否运行没有验证；
  - Plan 模式下的同步提问不记；
  - Codex 被 Esc 中断后一直显示“运行中”。
