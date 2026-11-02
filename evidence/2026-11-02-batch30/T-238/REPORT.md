# T-238 调查报告（2026-11-02）

**结论：INCOMPLETE。** 旧现场中 Codex 排队及 agy 长时间运行的原因没有查清，不能判断二者是否同因，也不能确认或排除 Enchanted 缺陷。本次在同一应用包和 CLI 版本上建立新项目后，没有复现：Codex 收到主控申请指令后运行了 `a2a request executor`、获批并回复；agy 对简单指令给出了回复。普通终端里两者也回复了简单指令。这些正例只证明当时的路径可用，不能解释旧现场或证明故障不会再发生。

## 复验步骤与结果

时间为美国东部时间 EST。应用包为 `/private/tmp/a2a-build-cu-test-20261102/Enchanted.app`，后台报告代码版本 `2b3b12dacc0e4e6661ff415409742f4833481cb3`；Codex 0.164.0，agy 1.4.12、Gemini 3.8 Flash high。

1. 在 `/private/tmp/a2a-t238/project` 执行 `git init`，以简报原样指定的 `open -n /private/tmp/a2a-build-cu-test-20261102/Enchanted.app --args --state /private/tmp/a2a-t238/state --user-data /private/tmp/a2a-t238/ui` 启动。`ps` 显示 UI PID 69594，后台 PID 69918 的参数含 `/private/tmp/a2a-t238/state`，私有 core PID 69920。打开该项目并新建终端。
2. 输入 `codex`，以 Escape 跳过更新提示。启动时曾较早发送一次指令，画面没有显示；待界面加载后重新发送“请在此隔离测试项目申请执行主控角色，使用 a2a request；获批准后先告知我，不要操作其他项目。”本次显示为已提交，而非旧截图中的排队。Codex 执行 `a2a help` 和 `a2a request executor`。08:34:47 在工作台批准执行主控申请；后台记录申请已确认，Codex 最终回复已获批。没有出现 Codex 目录或钩子信任框，故本轮没有对它们点同意。
3. 第二项目终端运行 `agy --dangerously-skip-permissions`。08:34:47 左右对 `/private/tmp/a2a-t238/project` 的目录信任框选 Yes；输入“请回复：测试正常。不要操作文件。”后台记录 08:35:01 working、08:35:06 done，消息为“测试正常。”这是简单问答，并非旧现场的角色申请指令，不能替代该场景的复现。
4. 在本工具提供的独立伪终端、同一项目目录中运行同版本 CLI。`codex` 原样启动报 `daemon executable not found ... rerun ... --no-daemon`；使用 `codex --no-daemon`，跳过更新提示，发送简单英文回复指令后输出 `test successful.`，约 7 秒完成。输入自动化将指令重复了一次，最终作为一条消息提交。`agy --dangerously-skip-permissions` 在独立伪终端启动，约 08:35 对同一目录的信任框选 Yes，同样的简单英文指令得到 `test successful.`。这个对照不包含 Enchanted 的包装参数，也不测试角色申请；Codex 多了 `--no-daemon`，不是严格同参数对照。

## 直接证据与边界

- 本次 Codex 会话 JSONL：`~/.codex/sessions/2026/11/02/rollout-2026-11-02T08-33-56-01a19c77-74ff-72c2-941b-cbb97dfe041d.jsonl`。其中 UTC 13:34:15.862 有 SessionStart 注入的工作台说明，13:34:15.994 有用户指令，13:34:21.570 有助手回应，13:34:51.825 有获批回复，13:34:52.057 为 `task_complete`。这证明本次会话通过了启动上下文和模型响应，不证明旧会话也通过了。
- 本次 `ps -axo pid,ppid,state,wchan,etime,command` 显示 core 69920 → holder 71025 → zsh 71026 → Codex 71259；Codex 子进程包括 71674 `terminalCli.ts mcp codex`，状态 `S`。同一时点未见 `session-context` 或 `hook` 子进程。MCP 进程长期存在符合服务进程的形态，单凭存在或睡眠状态不能认定它卡住。`lsof -nP -a -p 71674` 显示标准输入输出为管道；`lsof -nP -a -p 71259 -i` 显示多个到 `198.18.0.x:443` 的已建立连接及本地连接，不能单凭这些连接判定模型请求的目的地或等待状态。
- 本次后台 `sqlite3 -readonly /private/tmp/a2a-t238/state/state.sqlite3` 查询 `orchestration_events`：序号 43 `role_requested`，53 `role_request_decided`（approved=true），57 `role_request_confirmed`，66 为 Codex Stop 钩子 `terminal_turn`，67 为 Codex done；68、69 为 agy working 和 done。审批前的首句钩子未在此事件摘录中单独证明，不能仅凭最终完成声称它的每个内部步骤均正常。
- 旧后台只读查询：`sqlite3 -readonly /private/tmp/a2a-cu/state/state.sqlite3` 的 `orchestration_events` 中，Codex 终端 t5 在 UTC 11:13:25、11:14:37、11:15:27、11:19:51 报 idle；agy t8 在 11:17:06、11:19:39、11:19:45 报 working。旧截图确实显示 Codex 的 `Queued follow-up inputs`。这些记录不说明 Codex 队列所等待的具体资源，也不能把 agy 的 working 等同于网络故障。
- `~/.codex/log/` 只见较早的 `codex-login.log`，没有找到能解释旧次等待的 Codex 日志。按会话元数据的 cwd 查找当日 JSONL，未找到 cwd 为 `/private/tmp/a2a-cu/project` 的旧 Codex 会话；搜索到的同名文本出现在调查者自身会话中，不能当作旧 CLI 的会话证据。旧进程已经退出，无法取得其当时进程树、`lsof` 或现场堆栈。因此无法在 MCP、SessionStart、UserPromptSubmit、模型请求与其他原因之间作出有证据的选择。

## 根因与建议

尚未定位文件或逻辑，也没有足够证据给出修法。不要据本次成功就关闭故障或修改包装脚本。下一次出现排队时，应在原进程仍存活时记录终端 PID 及子进程、进程状态、打开的管道和网络连接、实际会话 JSONL 与后台事件，并记录队列出现与启动信任框确认的时间；同时在普通终端用相同 CLI、模型和尽可能相同的环境做对照，再根据可复现的阻塞点确定修复位置。不要把 TCP 已建立或一个常驻 MCP 进程当作请求成功或卡住的证明。

## 清理、限制与操作记录

本次误调用按名称选择应用的操作启动了 `/Applications/Enchanted.app`（UI PID 70018，后台 PID 70330，使用用户默认 state），违反简报只使用隔离应用的限制。发现后未在该窗口执行项目操作；已停止这次误启动的 UI 和后台。该启动可能触及默认 state，未审计其全部副作用，不能声称完全无影响。没有操作用户的 Herdr 或既有 hc。没有保存含账号邮箱的截图。

结束时停止了本次隔离 UI、后台、私有 core、两个项目终端 CLI 和普通终端对照进程；以 `ps -p 69594,69918,69920,71025,71026,71259,71673,71674,71675,72487,72513,72753,70018,70330,72927 -o pid,ppid,state,command` 复核，仅返回表头；按隔离路径及本次 core socket 搜索也无匹配进程。保留 `/private/tmp/a2a-t238/`。项目地图结束检查为 Problems 0、Stale living docs 0。未修改源码、ticket 或地图。
