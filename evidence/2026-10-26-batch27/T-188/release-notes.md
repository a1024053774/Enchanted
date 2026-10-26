Enchanted 0.1.5：支持 Antigravity CLI（agy）与 opencode。现在 Claude Code、Codex、agy、opencode 四种 CLI 都可以当主控、worker 和审查员。

- 项目终端里的 agy 与 opencode：直接敲 `agy` 或 `opencode`，就和 Claude Code、Codex 一样经包装脚本接入。开局就知道 `a2a` 怎么用，你让它当主控时它会运行 `a2a request` 申请，你在界面里批准。它们没有按会话的钩子，侧栏状态取自它们自己报给终端的信号（运行中、空闲、等你回答）；权限确认、登录时显示“未知”，不猜。
- agy 与 opencode 作 worker 和审查员：任务卡的 `executor.cli` 可以写 `agy` 或 `opencode`。两者都用你本机的安装、你自己的 HOME 和已登录的账号：agy 以 `--dangerously-skip-permissions` 运行，opencode 以 `--auto` 运行，都靠门禁事后检查兜底。门禁照常检查路径边界、验收文件不被改动、独立审查和提交尾注。审查员的 checkout 用文件权限设为只读。这两种 CLI 报不出每个回合实际用的模型和思考强度，交付记录和提交尾注里写 `unknown`。
- Git 元数据守护：交付时门禁核对 worktree 的 HEAD、分支与标签、Git 配置和钩子没有被 worker 改动，改了就拒收。对所有 CLI 都生效。
- 没接入检测：以 `node …/cli.js` 这类方式启动的 CLI 也能认出来；在一个 CLI 里再启动另一个 CLI 时，`a2a request` 记的是离它最近的那一个。

升级提醒：

- agy 作主控：请用 `agy --dangerously-skip-permissions` 启动。不加的话，agy 跑每条命令都要你在终端里确认，包括 `a2a request`。
- agy 的目录信任：agy 作 worker 或审查员时，会对每个新的任务目录问一次是否信任。Enchanted 核对画面上的目录和选项之后替你选“信任”，于是你的 `~/.gemini/antigravity-cli/settings.json` 里 `trustedWorkspaces` 每个任务目录多一条，其他设置不动。这是 Enchanted 唯一会写的全局配置。你自己在项目终端里第一次在某个目录启动 agy 时，它也会按自己的规则问一次，由你确认。
- Codex：钩子命令与 0.1.4 相同，0.1.4 里已经信任过的不会再问；第一次用的话 Codex 会弹一次钩子信任框，由你本人确认。
- 换版后 macOS 会收回 Enchanted 访问“文稿”等文件夹的授权（本包是 ad-hoc 签名，每个版本都算新的应用）。终端里的 CLI 读这些目录时会停下来等系统弹窗，弹窗可能被别的窗口挡住，请本人允许一次。

已知限制：

- agy、opencode 当主控时，你对它们说的话和对提问的答复不记入用户输入（这两种 CLI 没有按会话的钩子）。
- 后台重启后不恢复 agy、opencode 的受管窗格。
- 应用内主控写的完成条件仍可能偏弱或写错；门禁会如实拒收，需要主控修卡重派。
- “启动即失败可回收”只在模拟的启动失败上验证过。
- 只支持 macOS（Apple 芯片）；CLI 支持 Claude Code、Codex、agy、opencode 四种。

安装包适用于 macOS arm64（Apple Silicon）。解压后将 `Enchanted.app` 放入“应用程序”。

本包使用 ad-hoc 签名，未经 Apple 公证。首次打开如被系统拦截，可在访达中右键选择“打开”；必要时运行：

```sh
xattr -dr com.apple.quarantine /Applications/Enchanted.app
```

使用前先安装并登录至少一种支持的 CLI。bundle id 与后台数据目录保持不变。
