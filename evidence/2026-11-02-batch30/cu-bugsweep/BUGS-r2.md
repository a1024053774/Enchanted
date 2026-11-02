# Enchanted Computer Use 第二轮排查（2026-11-02）

**结论：INCOMPLETE。** 没有取得主控身份，也没有完成用户最关心的任务卡到集成闭环、问题收发或人工介入验证。发现一项复盘状态问题，另有两个启动疑问；不能把 CLI 或网络等待直接归因于工作台。

测试对象为 `/private/tmp/a2a-build-cu-test-20261102/Enchanted.app`，后台报告版本 `2b3b12dacc0e4e6661ff415409742f4833481cb3`。两次打开均使用任务书指定的 `open -n ... --args --state /private/tmp/a2a-cu/state --user-data /private/tmp/a2a-cu/ui`；每次打开后以 `ps` 核实后台 state，均为隔离路径。项目为 `/private/tmp/a2a-cu/project`。时间为美国东部时间（EST）。用 Computer Use 操作工作台和其中的终端。

## 已退出的复盘在后台重启后仍显示“进行中”

- 严重程度：一般；功能 7。
- 复现步骤：按上述隔离参数启动应用并打开测试项目的 Reflect。第一轮于 06:02 启动 Claude 复盘，目录信任框选择退出，第一轮结束时停止了隔离后台及 CLI；第二轮重新启动同一隔离状态目录，打开 Reflect，查看 06:02 那行。
- 期望：记录应反映该次复盘已经退出或状态未知，不能显示仍在进行；`workbench/README.md` 的复盘说明要求在终端运行会话并在产出后导入报告。实际：06:02、模型 `iku-5-5` 的记录仍为“进行中”，报告为 `—`。本轮 `ps` 只看到新启动的 `claude-haiku-5-5` 复盘进程，没有该旧模型进程。用户可能因此误以为旧复盘仍会完成。
- 截图：[r2-reflect-status.png](shots/r2-reflect-status.png)。观察到 1 个旧记录；跨本次页面切换和隔离后台重启仍存在，未另造第二次中断复现。

## 疑问：项目终端的 Claude Code 两次启动长时间没有界面

- 严重程度：待确认；功能 2、3。按隔离参数启动，新建项目终端，运行 `claude --model claude-haiku-5-5`，单独选中该终端观察；另新建终端重复。第一次超过 7 分钟、第二次超过 5 分钟仍只显示命令，无目录信任框或错误。后台提示“启动后还没有任何输出”。两个 Claude 进程均存在。截图：[r2-claude-no-output.png](shots/r2-claude-no-output.png)。本轮观察 2 次；第一轮另有 1 次。
- 期望：`workbench/README.md` 的项目终端流程允许启动原生 CLI 并申请角色。实际未能看到交互界面。本轮另一个由复盘启动的 Claude 确实显示目录信任框，批准后进入界面，因此不能把项目终端的无输出直接解释为正在等待同一信任框；也没有证据排除 CLI、网络、环境或被遮挡的系统提示。未操作系统设置或隐私弹窗，暂不能确认产品根因。

## 疑问：Codex 已进入界面，但主控申请指令一直排队

- 严重程度：待确认；功能 2、3。新建项目终端运行 `codex`，跳过更新提示，信任隔离项目目录并信任钩子后，在输入框发送“请在此隔离测试项目申请执行主控角色，使用 a2a request；获批准后先告知我，不要操作其他项目。”画面显示 `Queued follow-up inputs`，数分钟没有申请或响应；用 ↑ 取回并再次发送后出现两条排队项，仍无响应。截图：[r2-codex-queue.png](shots/r2-codex-queue.png)。一次会话，重复提交一次。
- 期望：`workbench/README.md` 的项目终端流程允许 CLI 接受请求并发起角色申请。实际没有观察到申请。队列由 Codex 自身显示，未排除 CLI 启动、模型服务或环境问题，不足以认定 Enchanted 缺陷。

## 本轮操作和停点

- 约 06:13：Codex 的 Folder access 框对 `/private/tmp/a2a-cu/project` 选 Trust and continue；随后对“Hooks need review / 4 hooks are new or changed”选 Trust all and continue。约 06:14：手动复盘的 Claude 对同一隔离项目目录的信任框选 Yes。约 06:16：Antigravity 对同一隔离目录的信任框选 Yes。均按第二轮授权；未出现角色申请批准框。没有使用临时 `CODEX_HOME`。
- 复盘模型框选中全部后输入 `claude-haiku-5-5`，无障碍树读回完整值，启动后的记录也显示该值；本次未复现第一轮丢字。复盘终端经信任框后显示 Haiku 5.5，运行约六分钟仍未产生报告，结束测试时停止；不能说复盘通过。
- OpenCode 启动后发送请求，显示“Connect an integration to send prompts / No integrations available”，未登录或配置集成。截图：[r2-opencode-integration.png](shots/r2-opencode-integration.png)。Antigravity 进入 Gemini 3.8 Flash，收到申请指令后数分钟显示运行中，未见申请或答复。两者均未作为 worker 或审查员测试。
- 窗口重载后，运行中的 Antigravity 窗格内容与状态接回；关闭窗口再按指定隔离参数打开，原后台 PID 仍在，复盘终端及其运行画面接回。这只证明该次重连，不证明 agent 任务成功或通知可用。
- 测试结束通过菜单快捷键退出隔离 UI，停止本轮隔离后台、私有 core 与其 CLI；`ps` 核实指定进程已退出。保留 `/private/tmp/a2a-cu/`。未动用户 Herdr/core，未修改项目源码、ticket 或地图。截图未保存账号邮箱。

## 各项功能结论

1. **未测**：普通终端多窗格可见；多个任务、多个 agent、历史折叠、清理和回收未验证。
2. **未测完整**：第一轮已见 zsh 与 `a2a help`；本轮 Codex、agy 可进入界面，Claude 存在上述疑问，未完成交互。
3. **未测完整**：第一轮未批准主控命令被拒；本轮未收到申请，批准、拒绝和终端关闭后失效未测。
4. **未测**：没有获批主控，未生成任务卡或派发，也未验证门禁、独立审查、打分、集成和 worktree 清理。
5. **未测**：问题页为空；未提交、回答或验证 15 分钟转移。
6. **未测**：没有受管 worker，未验证 ↑、连续输入和 Esc 后发送的人工介入记录。
7. **有问题**：旧复盘记录仍显示进行中；新复盘未完成。指标四个视图可见但均无数据，模型分类正确性未测；记录页未取得实际任务数据。
8. **未测**：设置页可见角色、模型和强度，但未派发新会话核验生效。
9. **未测完整**：重载与关闭后重开观察到终端接回；未验证任务持续完成或通知。
10. **未测**：OpenCode 无可用集成；agy 主控尝试未获得回应，均未派为 worker 或审查员。

项目地图结束检查：Problems 0、Stale living docs 0。第一轮报告保留。
