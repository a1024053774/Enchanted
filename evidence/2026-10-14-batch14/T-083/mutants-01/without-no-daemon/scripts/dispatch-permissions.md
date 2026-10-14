# 派发权限规则建议

**待用户批准后应用。** [建议 JSON](dispatch-permissions.proposed.json) 只是审阅材料；T-054 不修改任何 Claude Code 设置，也未验证该建议在真实 Claude Code 权限运行时的执行效果。由用户审阅现有规则后决定应用位置与合并方式，不能用它覆盖整份设置。

| 模式 | 建议 | 理由 |
| --- | --- | --- |
| `scripts/dispatch *`、`./scripts/dispatch *`、仓库绝对路径 | 放行 | 执行主控的提示词经同一包装，留下标记、角色卡、预备记录和 Herdr 结果 |
| `scripts/session-copy *`、`./scripts/session-copy *`、仓库绝对路径 | 放行 | 按显式来源只读复制字节，追加清单，不解析原生会话内容 |
| `herdr agent prompt *`，含当前安装的绝对路径 | 拒绝 | 直接投递会绕过派发记录 |
| `herdr pane run *`、`herdr pane send-keys *`、`herdr agent send-keys *`，含当前安装的绝对路径 | 拒绝常设授权 | 原始终端输入可绕过包装；中断权限也不能当作常设的提问/批准权限 |
| `Bash`、`Bash(*)`、`Bash(python3 *)`、`Bash(bash *)`、`Bash(zsh *)`、`Bash(eval *)` | 不加入放行；复核已有放行 | 通用执行器能间接运行 Herdr，不能宣称“只放行包装” |
| `herdr --session … agent prompt …`、`herdr --machine … agent prompt …`、其他 Herdr 安装路径或别名 | 不放行，逐次核对 | 本票只覆盖已核对的本机入口，不能把跨 server/机器身份包含进常设派发许可 |

这是提示词约束与权限规则建议，不是策略引擎。命令匹配不能证明包装文件没有被改写，也不能识别任意脚本间接发送的内容。执行主控仍须遵守角色卡、唯一门禁与任务授权；建议不授予 claim、验收、集成或回收权限。

紧急停止仍按 spec 第 5 节及用户当时的授权执行。建议中的常设拒绝不是对用户授权的替代；用户可直接停止，主控需要的单次中断路径由用户另行批准，不能借本票自动调整权限。

Claude Code 官方说明中，deny 的优先级高于 ask 与 allow，Bash 支持命令通配模式；不要用一个广泛的 deny 再期待更具体的 allow 成为例外。应用前也须检查已存在的宽泛放行、工具和权限模式。[官方权限文档](https://code.claude.com/docs/en/permissions)（2026-10-09 查阅）。
