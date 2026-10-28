NO_GO：主路径最终通过重派完成，但审查连续两次因协议错误中断，交付后的补充提交两次被拒绝，深度链接复制也未产生可用链接。

## 问题清单

### 1. 审查两次因输出协议无效而暂停（严重）

- 复现：T-1 的第一轮 worker 交付 a30e31d，执行主控启动验收和审查；问题页出现阻塞后点击“为同一次交付新开审查”。第二次审查再次失败。
- 期望：审查员能以门禁接受的格式交付结论；失败时能恢复并完成审查。
- 实际：问题页两次显示 `审查结论协议无效，已停止` 和 `审查输出不是可直接解析的 JSON 对象。代码围栏、前后说明或 JSON 语法错误都会被拒绝。 这次输出被拒绝，当时任务因此暂停。原文保留如下。` 重开后再次出现同样问题。两条卡片都标为“问题 1”，增加区分难度。界面给出了重开按钮和原文，但普通用户难以判断为何生成的内容不符合协议。后续回收旧 attempt、重派后，新候选的审查通过；根因未独立确认。
- 截图：`18-review-error.png`、`19-repeat-review-error.png`。

### 2. 已交付后人工补充的工作无法重新提交（严重）

- 复现：worker 首次交付 a30e31d 后，在其窗格输入“请确保错误时不修改已有笔记，谢谢。”worker 增强测试并尝试重新交付 efabe43；之后在新回合再补越界测试并交付 1ac08fd。
- 期望：界面清楚说明已交付后的介入如何成为新的可审候选，或提供有效的重新交付路径。
- 实际：两次都被拒绝，回执显示 `交付：门禁没有受理（stale_turn）`；最初候选仍是 a30e31d。主控建议在新回合重交，但实际仍被拒绝。最终回收旧 attempt 并重派新 worker 才完成，旧分支与记录保留。未确认 stale_turn 的内部根因。
- 截图：`13-intervention.png`、`20-stale-turn.png`、`21-integrated.png`。

### 3. “复制深度链接”复制的是说明文字（一般）

- 复现：右键 T-1 受管 worker 行，选择“复制深度链接”，在普通终端运行 `pbpaste`。
- 期望：剪贴板包含可用于返回会话的深度链接。
- 实际：复制的是 `Claude Code 会话 4f845989-eedf-4ab3-9bc1-5de18dee907d，记录 /Users/luckye/.claude/projects/-private-tmp-uat-state-worktrees-notes-cli-T-1-a1/4f845989-eedf-4ab3-9bc1-5de18dee907d.jsonl`，没有 URL 或可直接打开的链接。没有测试该文本在其他程序中的特殊解析。
- 截图：`15-deeplink-menu.png`、`17-clipboard.png`。

### 4. 关闭待审批终端时出现底层错误（一般）

- 复现：第二个 Claude 申请构思主控，在申请待批时点击该终端的关闭按钮。
- 期望：终端结束、待批申请撤销，并以可理解方式显示结果。
- 实际：申请条幅消失，终端变为只读、已结束，但窗格顶部显示 `输入尚未确认，已停止发送：Error: Error invoking remote method 'a2a:resize': Error: Window is not available for input`。没有明确的“申请已取消”提示；未独立查询后台申请状态。
- 截图：`05-pending.png`、`06-close-pending-error.png`。

### 5. 任务卡门禁拒绝只显示机器代码（一般）

- 复现：主控创建 T-1，第一次派发时验收文件指向未跟踪的 notes.json；打开任务卡。
- 期望：说明哪个文件不符合要求以及用户或主控下一步应做什么。
- 实际：时间线显示 `门禁拒绝 未通过 dispatch：oracle_not_found`，任务卡中没有解释代码含义。主控自行排查并改用已跟踪文件后继续，普通用户仅看该页面难以知道原因。
- 截图：`11-task.png`。

## 顺利完成和观察

- Claude 在项目终端使用 `claude --model claude-haiku-5-5` 启动；自然语言请求后自行找到主控申请方式。第一次拒绝后 Claude 明确报告被拒绝；第二次批准后执行主控生效。`01-request.png`、`02-rejected.png`、`03-approved.png`
- 第二个 Claude 申请执行主控时，因角色已占用收到 `role_taken`；改申请构思主控后出现待批条幅。`04-role-taken.png`、`05-pending.png`
- 创建 T-1 任务卡并派发 worker；窗格明确提示“在此窗格输入会记录为人工介入”。消息和回车分别被记录为人工介入。`11-task.png`、`12-worker.png`、`16-intervention-record.png`
- 任务进行中关闭窗口并按指定命令重开后，同一 worker 窗格重新显示，任务变为已交付；重开后观察到 worker 继续处理介入内容并提交，支持后台持续运行的观察。`14-reopen.png`、`15-deeplink-menu.png`
- 第二次尝试的候选 428a6bd 通过门禁验收和审查并集成到 `enchanted/notes-cli`，没有 push；`main` 保持在 ede9bf2。为直接验证，已在普通终端把项目工作目录切到集成分支。`21-integrated.png`、`22-verification.png`
- 普通终端 `git --no-pager log --oneline` 显示 428a6bd；`python3 -m unittest -v` 显示 `Ran 4 tests`、`OK`；`python3 notes.py done 99` 输出 `error: note number out of range: 99`，`python3 notes.py add` 输出 `error: add requires non-empty text`，两者提示符均显示退出状态 1。`22-verification.png`
- 流程、问题、记录、指标页均可打开；流程页能展开任务阶段，记录页显示审批、介入和门禁回执，指标页注明未覆盖的数据。旧 attempt 会显示在“未归属”区域并给出原因。`08-issues.png`、`09-records.png`、`10-metrics.png`、`23-flow-integrated.png`、`24-flow-expanded.png`

## 未完成及限制

- 两条旧审查协议问题仍在问题页，标记为等待用户决定；它们属于已回收的旧 attempt。未人为关闭，以保留现场。主控生成了反馈草稿，但未向外发送。
- 未测试 Codex 或 agy 重派：Claude worker 可启动；仅在首次交付和审查受阻后回收并重派了 Claude。没有遇到登录或系统隐私授权框。
- 初始申请是执行主控；由于该角色已占用，待批关闭场景使用构思主控。未独立核验关闭后的后台申请记录。
- 主控最初自行在 `/private/tmp/claude-501/.../scratchpad` 写入验收草稿，超出了本轮只在 `/private/tmp/uat/` 写文件的边界；发现后立即要求其限定路径。主控随后报告已迁移并删除该草稿，但本次未独立核验外部路径的残留。该偏差不能视为符合边界。
- 第一轮已报告的问题见 `/private/tmp/uat/ui-check/REPORT.md`，本轮没有系统复测它们。本轮没有修改系统设置、选择 Codex 或 agy 信任、登录、付款或 push。
