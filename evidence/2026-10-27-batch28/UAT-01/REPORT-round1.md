NO_GO：试用发现影响使用的问题，且主控与 worker 的完整交付链路未能验证。

## 问题清单

### 1. 非 Git 目录仍被加入项目列表（严重）

- 复现：点击“打开项目目录”，选择 `/private/tmp/uat/repos/not-a-repo`，点击“打开”。
- 期望：按本次任务要求拒绝非 Git 项目，并给出可理解的提示，不将它当作可用项目加入列表。
- 实际：目录出现在列表并成为当前项目，仍可新建终端；侧栏显示 `无法读取 Git：Error: Command failed: git -C /private/tmp/uat/repos/not-a-repo status --porcelain=v2 --branch --untracked-files=no fatal: not a git repository (or any of the parent directories): .git`，视觉上只显示截断部分。
- 截图：`05-non-git.png`。

### 2. 明显无效的派发设置被保存（一般）

- 复现：设置 → 主控派发的默认模型，选择 Worker，将模型填为 `not-a-real-model`、思考强度填为 `banana`，点击“保存”。
- 期望：对明显无效的强度给出校验反馈，或至少明确无法校验并提醒用户派发可能失败。
- 实际：显示 `已保存，下次启动生效`，未见警告。未能启动 worker，因此没有验证这些值对派发的实际影响。测试后已将 Worker 值恢复为 `gpt-6.1-sol` / `high`。
- 截图：`08-invalid-settings.png`。

### 3. 安静运行的 sleep 被提示可能在等待系统权限（一般）

- 复现：在项目终端执行 `sleep 300`，等待数秒。
- 期望：安静运行的命令不应被当作疑似权限弹窗；若提供通用提示，应明确不能判断原因。
- 实际：显示 `sleep 启动后还没有任何输出。它可能在等 macOS 的权限弹窗（例如“想访问‘文稿’文件夹”），弹窗可能被其他窗口挡住了，请移开其他窗口找一找。有输出后这条提示自动消失。` 此命令正常情况下本就不会输出，提示容易让用户误查权限。
- 截图：`13-sleep-warning.png`。

### 4. 中文目录名显示为 project（一般）

- 复现：打开 Git 目录 `/private/tmp/uat/repos/我的 项目`。
- 期望：项目列表和标题使用可辨认的目录名“我的 项目”。
- 实际：侧栏和标题显示 `project`，路径本身显示正确。多个中文目录可能难以区分；本次没有测试多个同名显示项。
- 截图：`06-chinese-project.png`。

### 5. Claude 在项目终端两次启动均长时间无输出（严重，归因待查）

- 复现：在 notes-cli 终端执行 `claude --model claude-haiku-5-5`；等待约两分钟，中断，再次执行并等待数分钟；关闭窗口后按指定命令重开并查看该终端。
- 期望：出现 Claude 的可交互界面，或显示明确的启动失败原因。
- 实际：终端始终无 Claude 输出，侧栏显示 `Claude Code` / `未知`，顶部提示 `2.1.311 启动后还没有任何输出。它可能在等 macOS 的权限弹窗（例如“想访问‘文稿’文件夹”），弹窗可能被其他窗口挡住了，请移开其他窗口找一找。有输出后这条提示自动消失。` 未确认是应用、CLI、环境或权限造成，也未看到具体权限弹窗。最终以 Ctrl+C 中断。
- 截图：`04-claude-start.png`；重开后项目与终端列表见 `14-reopen.png`。

## 顺利完成或观察到的事

- 首次界面提示“打开一个目录，在里面开终端”，无需查文档即可找到起点。`01-first.png`
- 成功加入 notes-cli、landing-page 和含中文及空格的 Git 路径；重复打开 landing-page 后列表仍只有一个该项目。`07-projects.png`
- 在 macOS 目录选择器中输入不存在的路径并回车后没有加入项目，随后取消；选择器本身没有显示明确错误。`11-nonexistent.png`
- notes-cli 终端输出 `seq 1 20000` 到末尾；中文粘贴 `echo 中文粘贴测试` 正确回显，`sleep 100` 可用 Ctrl+C 中断。`03-long-output.png`、`04-claude-start.png`
- 同一项目可新建两个终端并分屏；普通 shell 右键的“复制深度链接”禁用并解释原因。`10-context.png`
- 浅色和深色界面均可显示；测试后切回深色。`08-invalid-settings.png`、`13-sleep-warning.png`
- 项目仍有运行中终端时，移除操作被拦下，提示 `这个项目还有 1 个运行中的终端。先关掉它们再移除。` `12-remove-running.png`
- Cmd+W 关闭窗口后，用指定 `open -n ... --state /private/tmp/uat/state --user-data /private/tmp/uat/ui` 命令重开；项目和终端条目仍可见，Claude 终端仍显示无输出提示。这里只验证了窗口重开后的界面，未独立核实后台进程生命周期。`14-reopen.png`
- 现有仓库 `python3 -m unittest -v` 报 `Ran 1 test` / `OK`；该基线测试没有证明两个已知缺陷已修复。`17-baseline-tests.png`
- 终端执行 `exit` 后显示 `终端已结束 · 只读`，并出现历史条目。`18-exit.png`

## 未完成、阻挡及限制

- BLOCKED：Codex 出现 `Trust this folder?`，并说明 `Your trust decision will be saved.`；agy 出现 `Do you trust the contents of this project?`。按任务边界均未选择信任，分别退出。`09-codex-trust.png`、`16-agy-trust.png`
- BLOCKED：OpenCode 接受输入后要求 `Connect an integration to send prompts`，对话框显示 `No integrations available`；未进行连接或登录。`15-opencode-integration.png`
- INCOMPLETE：由于 Claude 无输出，其他 CLI 遇到上述边界，未能让 AI 申请主控，未测试拒绝、批准、待批关终端，也未创建任务卡、派发 worker、人工介入、审查或集成。没有修复 notes-cli 的两个已知问题，也没有新的修复提交；不能把现有单项测试通过视为交付验证。
- INCOMPLETE：未验证可用会话的深度链接复制、不同角色的设置、双击与完整菜单栏键盘导航；尝试拖动窗口但未成功取得窄窗口，未完成窄屏检查。
- 本次首次目录选择时误打开了已有的 `/private/tmp/t190/beta` 条目；未操作该项目文件。测试只使用 Enchanted Test，未选择信任或登录，未 push。测试中启动的 Claude 和 sleep 已用 Ctrl+C 中断。
