# T-122 探针 03：新 worktree 里的信任对话框

2026-10-21，Claude Code 2.1.306。交互模式启动（`--permission-mode dontAsk --setting-sources local --strict-mcp-config`），15 秒内读屏幕，不发提示词、不调用模型。

重跑：`python3 trust_probe.py <新目录>`

| 启动目录 | 结果 |
| --- | --- |
| `/private/tmp/t122-probe/fresh-*`（不在任何已信任目录下） | 出现 “Do you trust this folder?”，默认选中 “No, exit” |
| `/Users/luckye/Documents/.t122-trust-probe-*/a/b`（用户已信任 `/Users/luckye/Documents`） | 不出现，直接进输入界面（目录用后已删除） |

结论：信任按父目录继承，没有跳过它的启动参数；信任记录在 `~/.claude.json`，a2a 不得写。a2a 的 worktree 在数据目录 `<数据目录>/worktrees/<项目>` 下，不在用户信任过的目录里，所以 Claude worker 启动必遇此框。

用户 2026-10-21 的决定（AskUserQuestion 选项原文）：“后台代按确认 (Recommended)”——只对 a2a 自己新建的 worktree、worker 刚启动且还没收到任务时出现的这个对话框，后台代按 “Yes, I trust this folder” 并记一条事件；信任记录由 Claude 自己写，a2a 不直接写；识别失效时 worker 停在这一屏并报错。

另：探针 01～03 期间用户本周 Claude 额度到 90%；真实入口验收的 worker 用 Haiku（用户选项原文：“Haiku (Recommended)”）。
