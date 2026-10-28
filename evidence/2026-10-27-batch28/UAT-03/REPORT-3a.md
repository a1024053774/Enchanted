INCOMPLETE：本轮未能建立主控，因而没有完成任务、worker、审查与集成的端到端验证；Claude 启动无输出的责任归属尚未确定。

## 产品页声明逐条检查

| 声明 | 结果与证据 |
| --- | --- |
| 四种官方 CLI 在交互终端运行，均可当主控、worker、审查员 | 部分能用：Claude 三次启动均无交互输出；Codex 显示界面但请求排队未得到响应；OpenCode 要求连接且无可用集成；agy 显示信任提示，按边界退出。未验证四种角色。`13-both-stalled.png`、`15-opencode-blocked.png`、`16-agy-trust.png` |
| 侧栏 agent 树、分支和领先落后数、折叠与状态汇总 | 部分能用：两个项目显示 `main · 无上游`，可以切换，普通终端在项目下显示。无上游因此未验证领先/落后数；没有主控树，未验证折叠汇总。`09-split.png` |
| 项目视图每张票一格，显示门禁状态和 agent | 没试：没有建立主控或任务。 |
| 任务页上下布局、完整记录、打开 worker、普通终端和窗格菜单 | 部分能用：项目普通终端的菜单可向右分屏、放大及还原，普通终端输入未出现在记录页；任务页与 worker 场景未试。`09-split.png`、`10-records-after-shell.png`、`11-maximize.png` |
| 项目终端申请并批准主控，身份随终端结束 | 没试：没有 CLI 成功产生申请。 |
| 原生提问的侧栏黄色、通知、点选答复和记录 | 没试：没有可工作的主控。 |
| 流程页泳道、回线、折叠 | 部分能用：空状态可打开，说明一票一泳道；无任务，未验证泳道与回线。`06-flow-empty.png` |
| 问题页上报、阻塞卡只有用户关闭、发送答复 | 部分能用：页面显示上述说明和空状态；无问题卡，未验证答复或关闭。 |
| 记录页记录输入、答复和审批，worker 介入可按任务筛选 | 部分能用：普通终端执行 `echo ordinary-terminal-check` 后记录仍为空；没有 worker、审批或任务，未验证完整消息、Esc 和筛选。`09-split.png`、`10-records-after-shell.png` |
| 指标页模型使用、一次到位率、打回原因、注意力、打分与 unknown | 部分能用：四个区域及解释可见，均为无数据；说明“看不到的记为 unknown”，未产生实际 unknown 数据行。说明较具体，但无法验证计算。`04-metrics.png` |
| 回看页列出主控、会话、worker 打分，建议需批准 | 部分能用：空状态及建议区可见；没有会话或建议可验证。`05-reflect.png` |
| 按角色设置模型、思考强度、Fast，影响之后会话；浅深色切换 | 部分能用：Worker 改为 `claude-haiku-5-5`、`medium`、Fast 并保存；浅色和深色可切换。未成功派发新会话，不能验证参数生效或旧会话不受影响。`02-settings-dark.png`、`03-settings-light.png` |
| 交付门禁核对 worktree HEAD、分支、Git 配置与钩子 | 没试：没有交付。 |
| 全部检查通过才集成到工作分支，不 push | 没试：没有交付或集成；本轮未 push。 |

## 问题清单

### 1. Claude 在项目终端反复启动无输出（严重；归因未确定）

- 复现：打开 `/private/tmp/uat3/repos/todo-cli`，新建终端，运行 `claude --model claude-haiku-5-5`。约 39 秒无输出后 Ctrl+C，再次运行；关闭窗口，按任务给定命令重开后第三次运行。
- 期望：显示 Claude 交互界面，或给出可操作的明确失败原因，以便申请主控。
- 实际：三次均未出现 Claude 界面；侧栏显示 `Claude Code` / `未知`。应用提示原文：`2.1.312 启动后还没有任何输出。如果它本该有输出（例如 claude、codex 启动后会画出界面），可能在等 macOS 的权限弹窗（例如“想访问‘文稿’文件夹”），弹窗可能被其他窗口挡住了，请移开其他窗口找一找；sleep 这类本来就不输出的命令不用管。有输出后这条提示自动消失。` 第二次等待超过一分钟，重开后的第三次也等待约一分钟。未看到实际权限弹窗，不能断定是应用、CLI、网络或环境的原因。最后 Ctrl+C 中断。
- 截图：`08-claude-no-output.png`、`13-both-stalled.png`、`14-reopen-claude.png`。

### 2. Codex 的主控请求停在排队状态（严重；归因未确定）

- 复现：在 todo-cli 的第二个普通终端运行 `codex`，跳过更新，在 `Hooks need review` 处选择不信任继续；请求它申请执行主控，并再次发送英文请求。
- 期望：CLI 响应并申请主控，或者明确报告无法处理的原因。
- 实际：界面显示 `Queued follow-up inputs`，英文请求停在队列中，等待约一分钟未见答复或申请。第一条中文用键入方式发送，画面只显示 ASCII 片段，不能确认其完整内容；英文通过粘贴发送并可见。未信任钩子，不能断定等待是否由此、CLI 或环境造成。Ctrl+C 后显示 `Shutting down...`，未独立核实进程退出。
- 截图：`12-codex-hooks.png`、`13-both-stalled.png`。

## 阻挡和未完成

- OpenCode 的提示为 `Connect an integration to send prompts`，弹窗为 `No integrations available`。按边界未连接或登录。`15-opencode-blocked.png`
- agy 显示 `Do you trust the contents of this project?`；按要求没有替它信任，选择 `No, exit`。`16-agy-trust.png`
- 没有主控申请、任务、worker 或交付，因此未做人工介入编辑/Esc、提问答复、问题卡、审查协议、集成后测试、门禁篡改检查和新设置生效检查。前两轮报告中的问题本轮未系统复测。
- 目录选择时误将历史路径 `/private/tmp/uat/repos/landing-page` 加入项目列表；没有进入其终端或修改该仓库。两个指定夹具均已添加并切换。未改系统设置、登录、授权或 push。
- 测试报告和截图保存在 `/private/tmp/uat3/ui-check/`。Worker 设置仍为本轮测试值，外观为浅色。OpenCode 窗格停在未发送的提示词，未连接服务。
