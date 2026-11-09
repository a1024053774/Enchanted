# 交接：侧栏 Codex 接手执行主控（2026-11-09）

这份说明由 Claude Code 会话 `8be1abdd-5af9-4023-bff8-cbc0f40d9a84` 写，不是用户本人写的。引号里的才是用户原话。

## 用户原话

2026-11-09，上述 Claude Code 会话（用户先停掉了 Codex 桌面会话 `01a1bc43-9071-7321-8f8e-3d5dfad42a09`）：

> 那个对话我让他停了,现在你在你侧边栏终端开 codex 安排他做.用 astra medium fast

你就是这个 Codex：`gpt-6-astra`，effort medium，Fast。这只是你自己的设置。worker 与审查员仍是 `gpt-6-astra` xhigh、`service_tier` default，依据是用户 2026-11-08 的原话：

> 先装新版,然后你自己启动软件继续,这次用 opus5.5 extra 当主控,然后 astra extra 当 worker 和 reviewer

两个面板最后的独立验收仍由 `gpt-6.1-terra` 用 Computer Use 加常规测试完成。Enchanted 设置里 worker、审查员都已是 astra xhigh、不开 Fast；派发时仍显式传 model 与 effort，并核对启动 argv。

用户对前任 Codex 主控说过、现在仍有效的话（会话记录 `~/.codex/sessions/2026/11/08/rollout-2026-11-08T12-45-10-01a1bc43-9071-7321-8f8e-3d5dfad42a09.jsonl`，时间为 UTC）：

- 2026-11-08T17:45Z：
  > 修复现在 enchanted故障并继续, 主线是完成主要的两个面板的任务以及 bug 修复
- 2026-11-08T17:53Z（同一条消息里的三项界面问题已开为 T-260、T-261、T-262）：
  > 需要的权限都允许你点,比如 mac 的隐私经常弹出是否允许 enchanted 访问文稿这种,这个问题一般出现在新构建 app 时
- 2026-11-09T00:44Z：
  > 以后再遇到这种合入我同意,不用等我,然后我截图中提到的几个问题也要开票修复
- 2026-11-09T00:50Z：
  > 还有这种你都要去点,不能因为这个卡住进度
- 2026-11-09T01:02Z：
  > 现在又弹出来,你要有办法识别到,比如某项卡住了,然后你就知道是这里没授权

上一份交接是 `evidence/2026-11-08-controller-switch/executor-handoff.md`。它的边界仍有效，但有三处被本文件取代：主控模型；“不读操作员凭据”；“T-249 集成前交用户批准”。最后一条由上面 00:44Z 的原话覆盖：那句话是用户批准合入同样需要所有者批准的 T-259 之后说的。

## 你的角色与门禁身份

你是执行主控。派发、验收、审查、集成、回收一律只经 Enchanted 门禁，不用 Herdr，不另起隐藏的 Codex 去写代码。

你在 Claude 桌面应用的侧栏终端里运行，不在 Enchanted 的终端里，走不了 `a2a request executor`。沿用前任主控的做法：

- 从 `~/Library/Application Support/Enchanted/desktop-connection.json` 读 `credential`；
- 设好环境变量 `ELECTRON_RUN_AS_NODE=1`、`A2A_OPERATOR_CREDENTIAL`；
- 运行 `/Applications/Enchanted.app/Contents/MacOS/Enchanted /Applications/Enchanted.app/Contents/Resources/app/src/gates/cli.ts --state <正式后台数据目录> <命令> …`。

完整写法见会话记录 2026-11-09T00:46:39Z 起的调用。凭据不写进任何日志、证据或提交。

## 现状（2026-11-09 约 14:05Z，只读核对）

- 正式版 `/Applications/Enchanted.app` 0.1.6，后台 PID 34137，装到 T-265（06:33Z）为止。本地 main 上已集成、还没安装的有 T-262（`5ba4e68e9`）。没有 push。
- **T-266-1**：审查结束后回收时读到半截 JSON，根因是进程查询的超时竞态。状态 `claimed`，attempt `334ba6bb…`，worker launch `6efa6e15…`（astra xhigh），worktree `~/Library/Application Support/a2a-orchestrator/worktrees/a2a/T-266-1-a1`。
  - worker 在 14:00:53Z 报了阻塞问题 #2：请主控在 worktree 外运行 `/usr/bin/python3 evidence/2026-11-09-batch35/T-266/worker/run-external-checks.py`，再把 `worker/external-*.json` 回传给它。前任已停，这条没人回。
  - 同一条还附了两个范围外发现：`test_t093_process_snapshot.py:65` 失败；旧诊断脚本请求不存在的 `pane_release`。另外 `workbench/README.md` 显示 stale，要在收尾时核对。
- **T-249-1（Git 图）**：`verified`，候选 `63304e0fc`。审查员 astra xhigh 判“可合并”，没有发现问题；Terra 已做完真实窗口验收。还没集成。
- **T-249-2**：收紧 Terra 观察比对工具的父提交哈希校验。attempt 已 `upgraded`，复审判“可合并”，但审查结论转交门禁时报 `Unexpected end of JSON input`（就是 T-266 那个缺陷），门禁记录没落下。
- **T-250（改动面板）**：门禁里还没注册，一行代码没写。
- **T-260-1**：`ready`，修前红态在 `ed6ad716b`。**T-261-1**：`ready`。**T-264**：票已开，没注册。
- `/private/tmp/t249-outside-9iitgp1b/` 下还有一个 Enchanted Test（PID 451）和它的 hc core 在跑，是 T-249 验收留下的。确认没人在用后正常退出并清理。
- 主目录有历史日志等未提交改动和大量未跟踪证据，都保留，不要动。

## 要做的，按顺序

1. **回 T-266 的 #2。** 在 worktree 外跑它要的脚本，按它给的路径回传结果（`answer_issue`）。范围外的两项另开票或记下，不在 T-266 里改。T-266 交付后照常验收、审查、集成。
2. **立即集成 T-249-1。** 审查与真实窗口验收都已通过，用户已同意合入不用等。T-249-2 不挡这次集成：它改的是验收材料的检查工具，复审已判“可合并”，等 T-266 装好后再补完它的门禁记录。如果读票发现 Acceptance 明文要求比对工具先落地才能集成，就停下来写明哪一条，不要自己判。
3. **Codex 名额一空，就注册并派发 T-250**，按票的 Acceptance 写任务卡。
4. **再做 T-260、T-261、T-264**，在名额内并行，文件不重叠。
5. **安装。** 等没有受管 worker 在回合中时，用标准打包命令打包、安装、重启后台，一次带上已集成的改动（至少 T-262、T-266、T-249）。旧包留作回退。T-250 做完后再装一次，并交 Terra 验收。
6. **每次集成后核对 evidence。** 按稀疏 checkout 规则检查 `evidence/` 有没有被删。

## 这次要改掉的做法

前任接手的 20 小时里，有 11 小时没在干活，主线推进很慢。照下面做：

- **有已授权的活就不要结束回合。** 你是用 `codex exec` 启动的，回合一结束进程就退出，没人能马上叫醒你。只有全部做完，或者卡在只有用户能做的事上，才结束；结束时第一行写状态词，写明卡在哪里。
- **等长任务时，自己每隔几分钟查一次状态。** 不要结束回合去等。
- **用户已经同意的事不要再问。** 包括合入、安装、重启后台、Enchanted 的权限弹框。
- **已过审查与验收的产品，不因完善测试工具或证据而推迟集成。** 工具改进另开任务，排在后面。
- **测试驱动或探针自己出错时，同一个问题最多再试两次。** 还不行就记下来，换条路或上报，不要一轮一轮地修驱动。
- **证据按任务状态变化提交**，不要每一步都提交一个 `docs:`。任何审查进行期间，都不向 main 提交，也不新建或移动 Git 引用，否则审查回收时会以 `review_shared_refs_changed` 暂停。
- **卡住时按这个顺序查：**
  1. CLI 额度（终端出现 “Usage limit reached”）；
  2. 受管会话的 6 回合上限；
  3. macOS“访问文稿”弹框；
  4. 最后才是代码问题。
- **macOS 系统弹框 Computer Use 点不了**：工具禁止操作 `com.apple.UserNotificationCenter`。遇到时在输出里写一行 `需要用户点允许：<哪个应用，卡在哪一步>`，同时继续做不依赖它的事；父会话会转告用户。
- **界面操作用短调用。** 前任有一次 Computer Use 点击挂了 2 小时，直到用户打断才恢复。

## 边界

- 只集成到本地 main，不 push。
- 同时最多 3 个 Codex 会话，你自己算一个；worker、审查员、验收员都算在内。
- 不碰用户自己的 Herdr 及其 core。不写 `~/.claude`、`~/.codex` 的全局配置。
- 不改冻结的 `acceptance/**` 和 `REVIEW.md`。
- 主目录是稀疏 checkout：不 checkout、不 switch、不 `sparse-checkout reapply`，一律用 `git -C`；合入后核对 `evidence/`，被删的按 AGENTS.md 恢复。
- 构建缓存、临时构建目录、测试夹具用完就清，证据只留文本。
- 目标、范围、验收条件或权限要变时，停下写明原因。工作台出了新缺陷就开票；能绕开的，先继续别的任务。
- 状态只用 PASS、INCOMPLETE、BLOCKED、NO_GO；结束时加 Works、No regression、Risk / undo 三行。回复用中文。

## 汇报

每个任务的状态变化，都往 `evidence/2026-11-09-controller-switch/STATUS.md` 追加一行：UTC 时间、任务、状态、下一步。这个文件不用每次都提交。
