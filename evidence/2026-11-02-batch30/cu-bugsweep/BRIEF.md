# 任务书：用 Computer Use 实测 Enchanted 工作台，找缺陷（2026-11-02）

你是测试员，只找问题、记问题，不改代码。用户的原话：“让 codex 用 6.1 terra 的 computer use 再测试软件找找 bug. 对我所设想的那些功能.”

## 要测的程序

- 已按当前 HEAD（`2b3b12dac`）打好包：`/private/tmp/a2a-build-cu-test-20261102/Enchanted.app`。不要用 `/Applications/Enchanted.app`（旧版，而且连着用户自己的数据）。
- 用隔离数据目录启动，路径要短（后台 socket 有长度限制）：

  ```bash
  open -n /private/tmp/a2a-build-cu-test-20261102/Enchanted.app --args --state /private/tmp/a2a-cu/state --user-data /private/tmp/a2a-cu/ui
  ```

- 测试项目：`/private/tmp/a2a-cu/project`（一次性的 Git 仓库，可以随便改）。需要更多项目就在 `/private/tmp/a2a-cu/` 下新建。

## 用户设想的功能（逐项实测，规格见仓库 `intent.md`“期望结果：切换”、`workbench/README.md`、`CONTEXT.md`）

1. 界面层级：项目 → 任务 → agent 会话；一个项目多个任务，一个任务多个 agent；侧边栏、窗格标题栏、历史折叠与“清理”“回收”。
2. 项目终端：打开项目终端，里面是用户的 zsh；`a2a help` 能用；在终端里启动 Claude Code 或 Codex。
3. 主控角色申请：在项目终端的 CLI 里经 `a2a request` 申请主控，在界面里批准或拒绝；没批准的会话不能用主控命令；关掉终端角色结束。
4. 受管任务全流程：任务卡生成、派发 worker、worker 交付、门禁检查串（路径边界、完成条件、提交尾注等）、独立审查员会话、验收打分、集成到项目工作分支、回收。worktree 命名与清理。
5. 问题面板：worker 经 `issue` 提问、主控提问在面板上出现，能在面板上回答；15 分钟未处理进“等你决定”。
6. 用户输入记录：在受管 worker 窗格里直接打字发出，算人工介入，记录只留最终发出的那句（T-229 刚改过，重点看 ↑ 调历史、回车后接着打字、Esc 打断后再发）。
7. 记录页、复盘（手动跑一次）、指标页的四个视图（含模型使用分类）。
8. 执行设置：按角色改 CLI、模型、强度后，新派发的会话用上新设置。
9. 通知、关掉窗口再打开（后台常驻，agent 不受影响）、窗口重载后窗格重新接上。
10. agy、opencode 作 worker 或审查员（本机装了就测，没装就记“未测”）。

## 花费与模型

- 在 Enchanted 里起 Claude Code 会话时选 `claude-haiku-5-5`；起 Codex 会话用默认设置即可。能用小任务（例如给 `src/calc.py` 加一个 `sub` 函数和测试）就不要用大任务。

## 边界

- 只操作你自己启动的那个 Enchanted 窗口，以及它里面的终端。不碰用户的其他应用、Finder 之外的系统界面、`/Applications/Enchanted.app`、用户自己的 Herdr 或 hc（pid 87319、87320、87407 及其他非本次启动的 hc 进程）。
- 不改 a2a 仓库的源码、ticket 或地图；只在 `evidence/2026-11-02-batch30/cu-bugsweep/` 下写文件。
- 不 push，不登录，不改系统设置或隐私授权。遇到需要这些的，停下写进报告。
- 不写 `~/.claude`、`~/.codex` 的全局配置。

## 第二轮补充（2026-11-02，第一轮只测到一半）

- 授权：用户原话“他要是让授权,你帮我点同意就行”。所以 Enchanted 里的 CLI 弹出的目录信任框（只限 `/private/tmp/a2a-cu/` 下的目录）、Codex 的“Hooks need review”钩子信任框、Enchanted 界面里的角色申请批准，都直接选同意，记下是哪一个框、什么时间。这是用户本人的授权，不算你违反上面“不写全局配置”的那条。系统设置、macOS 隐私授权、登录密码仍然不碰，遇到就停。
- 不要再用临时 `CODEX_HOME`：Enchanted 里的 Codex 本来就用用户的 `~/.codex`（产品行为，T-127），照原样启动。
- **启动 Enchanted 只准用上面那条带 `--state`、`--user-data` 的命令**。第一轮用不带参数的 `open` 误打开了用户真实的数据目录，不能再发生；每次启动后先核对 `ps` 里后台的 state 路径是 `/private/tmp/a2a-cu/state`，不是就立刻退出并写进报告。
- 输入要核对：第一轮在复盘的模型框输入 `claude-haiku-5-5` 后变成了 `iku-5-5`。这次在同一个框重新输入，核对字段值；如果能复现字符丢失，把它当作缺陷记录（写清是产品吞字，还是 Computer Use 打字造成的，分不清就写“疑问”）。
- 第一轮的疑问“Claude Code 在项目终端里三分钟没出界面”：这次重试，看清是不是在等目录信任框或其他提示。
- 第一轮的 `BUGS.md` 保留，第二轮写到 `BUGS-r2.md`，截图仍放 `shots/`。现场 `/private/tmp/a2a-cu/` 里已有的项目和终端可以接着用。
- 优先把第 4 项（一张小任务卡从派发跑到集成，含审查和打分）、第 5、6 项跑通，这是用户最在意的闭环。

## 交付

写 `evidence/2026-11-02-batch30/cu-bugsweep/BUGS.md`，中文。每个问题一节：

- 标题（一句话写清现象）；
- 严重程度：阻断 / 严重 / 一般 / 轻微；
- 对应上面第几项功能；
- 复现步骤（从启动起，别人照做能复现）；
- 期望（依据：规格或 README 里的哪一句）与实际；
- 截图路径（存到 `evidence/2026-11-02-batch30/cu-bugsweep/shots/`，截图里不要出现账号邮箱）；
- 复现了几次。

最后一节列出每项功能的结论：通过 / 有问题 / 未测（写原因）。不确定是不是 bug 的，写成“疑问”，不要算作通过或失败。

测完退出 Enchanted（菜单退出，或在终端里结束本次启动的后台进程），保留 `/private/tmp/a2a-cu/` 现场不删。
