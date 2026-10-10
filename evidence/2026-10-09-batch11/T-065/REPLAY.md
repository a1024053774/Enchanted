# T-065 重放

本轮是 BLOCKED 局部候选，不是通过交付。全部原始失败保留；重放必须使用新的 label，禁止覆盖已存在文件。

本轮 fork 基线见 binding.json，候选完整版本见 fork-commit.txt。运行环境为 macOS arm64，Node/Bun 仅经 fork 的 `a2a/scripts/bun`，profile 与隔离数据库均在 `/Volumes/WD-Elements/dev-cache/synara/instances/t065-*`。固定浏览器沿用 T-063：`playwright-t063/chromium_headless_shell-1234`。没有真实模型调用。

## 原始命令与输出

`*-command.json` 保存完整 argv、cwd、开始/结束时间与退出码；同名 `.log` 保存原样 stdout/stderr。

| 运行 | 原始记录 | 结果 |
| --- | --- | --- |
| 已知坏源码 | red01-ui-command.json、red02-ui-command.json | exit 1，输入区在首屏外 |
| 局部候选的打开面板矩阵 | green01-ui-command.json | exit 1，仅最短窗口的 125% 模拟失败 |
| 相关单元套件 | related-tests01-command.json | exit 0 |
| 固定浏览器的既有套件 | browser-tests01-command.json | exit 0 |
| 全 workspace 检查 | typecheck01-command.json、lint01-command.json、fmt-check01-command.json | exit 0 |

## 新标签示例

先核对 8077/8078 的 IPv4/IPv6 listener 没有其他实例。隔离启动器保存 `*-dry-run.log`、进程身份和 `*-launch.json`；只停止自己启动且身份吻合的服务。测试不得在共享 checkout 换源码或构建桌面产物。

```sh
python3 evidence/2026-10-09-batch11/T-065/start-isolated.py replay-red baseline
python3 evidence/2026-10-09-batch11/T-065/run-command.py replay-red-ui ./a2a/scripts/bun run node /Users/luckye/Documents/Code/a2a/evidence/2026-10-09-batch11/T-065/ui-probe.mjs /Users/luckye/Documents/Code/a2a/evidence/2026-10-09-batch11/T-065 /Volumes/WD-Elements/dev-cache/synara/instances/t065-replay-red replay-red-ui red
python3 evidence/2026-10-09-batch11/T-065/stop-isolated.py replay-red
```

预期红态拒绝：1280×900、至少 3 条待决定问题时，输入区必须完整在首屏内，测试检测到其在首屏外。Vite 的仅测试 source loader 加载保存的 `e94a0efc3` ChatView 和 IssueNotifications；后者是开工 HEAD 与指定坏版本的唯一其他源码差异，见 baseline-diff.patch。server 与其他 tracked source 在这两个版本相同。测试不修改共享源码、dist 或依赖目录。

候选矩阵将 label 换成 `replay-candidate`，启动时不传 baseline，UI probe 最后参数省略（默认 matrix）。真实无面板夹具用启动末尾参数 `no-panel`，probe 末尾也传 `no-panel`；该路径已准备，但本轮在 blocking 问题出现后未运行，不能当成证据。

## 独立期望与诊断限制

期望来自 ticket 的 Acceptance 和说明。机械 oracle 检查整个输入区在 landing 与 viewport 内，点击坐标命中编辑器、输入哨兵成功且未滚动，4 个元素的 6 对相交面积均为 0，可见次要内容无裁切。中文文案、400px 会话列和滚动长问题正文是外部布局压力输入。

125% 用 CSS viewport 1024×576、DPR 1.25 模拟 1280×720 的浏览器布局，尚未证明真实菜单缩放。该场景截图被 Playwright 的原 viewport 捕获影响，不能用它证明缩放画布，使用 JSON 的实际 viewport/几何输出定位空间不足。后续完成验收须补独立的真实缩放或明确的验收范围决定。

所有运行中的 provider 均禁用。通过产品按钮关闭禁用提示，是夹具对正常空态的准备动作；red01 未关闭提示，red02 与候选均关闭，不能用相异提示状态替代反事实。
