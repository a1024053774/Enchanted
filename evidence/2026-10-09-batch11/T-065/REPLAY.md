# T-065 重放

交付状态为 INCOMPLETE：一次独立审查 FAIL，修复后不自行追审，待执行主控看 review-repair.diff.patch。审查冻结版本为 9654e1c63 / e18fead，交付修复版为 7a3a13249。版本与运行绑定见 candidate-binding.json、fork-commit.txt；原始输出不覆盖，重放一律用新 label。ticket-contract-review.md 仅含 What / Acceptance / 说明，不含 Resolution。

环境：macOS arm64；Node 24.13.1 和 Bun 1.4.2 经 fork 的 `a2a/scripts/bun`；固定 Chromium Headless Shell 在外置盘 `playwright-t063/chromium_headless_shell-1234`。所有数据库、夹具 Git repo 和 profile 均在 `/Volumes/WD-Elements/dev-cache/synara/instances/t065-*`。provider 禁用，没有模型调用。

## 三组当前候选运行

| 运行 | 几何场景 / 面板控件组 | 原始命令 |
| --- | --- | --- |
| 3 条待决定问题 | 13 / 7 | toolbar-final01-ui-command.json |
| 真正空问题列表，无面板 | 12 / 0 | toolbar-no-panel01-ui-command.json |
| 15 条待决定问题 | 13 / 7 | toolbar-many01-ui-command.json |

三组 exit 0；JSON 含运行前完整 revision 与 dirty diff、每个元素的矩形、6 对相交面积、viewport、DPR、输入哨兵、滚动和控件命中结果。candidate-binding.json 逐字核对测试源码与最终提交一致。截图含原文、加长中文、往返尺寸、窄列、问题列表滚动，以及三个 125% 模拟尺寸。

125% 用 0.8 CSS viewport + DPR 1.25 模拟，按 controller-decision-01.md 如实限定为 device-metrics；并非真实菜单缩放。当前截图经 CDP Page.captureScreenshot 保存，1280×720 缩放场景的 PNG 也为 1280×720。toolbar-many01-ui-125percent-1280x720-open-button-*.png 对应同名 JSON 的 panel-controls 控件序号，可核对发送答复、打包与取消按钮完整显露。

## 用新标签重放

先检查 8077/8078 的 IPv4/IPv6 listeners 没有其他实例。启动器自动核对 dry-run home 是本轮 root，再启动真实服务端/Vite；保存 argv、PID、lstart。停止器只停启动记录中身份吻合的两个服务。

```sh
python3 evidence/2026-10-09-batch11/T-065/start-isolated.py replay-open
python3 evidence/2026-10-09-batch11/T-065/run-command.py replay-open-ui ./a2a/scripts/bun run node /Users/luckye/Documents/Code/a2a/evidence/2026-10-09-batch11/T-065/ui-probe.mjs /Users/luckye/Documents/Code/a2a/evidence/2026-10-09-batch11/T-065 /Volumes/WD-Elements/dev-cache/synara/instances/t065-replay-open replay-open-ui
python3 evidence/2026-10-09-batch11/T-065/stop-isolated.py replay-open
```

无面板：启动与 probe 最后都加 `no-panel`，并换新 label。15 条问题：启动与 probe 最后都加 `many`。上述模式只改外部夹具的初始问题数据，不修改生产显示逻辑。UI 压力输入直接改变展示文案和会话列宽度，产品没有语言切换或宽度拖动功能。

## 红态、失败与检查

已知坏源码 e94a0efc3 的 red01-ui/red02-ui 在实现前失败；主控批准前的局部候选 green01-ui 在最短窗口的 125% 模拟失败。输出、截图和命令原样保留。原脚本见 ui-probe-blocked.mjs；red01 未关闭禁用 provider 提示，red02 与候选通过产品按钮关闭该夹具提示。

重放 e94a0efc3：启动最后加 `baseline`，probe 最后加 `red`。Vite 的测试 source loader 加载保存的 ChatView、IssuePanel、TaskWindow、IssueNotifications；不在共享 checkout 换源码、切 branch、改 dist 或链接依赖。最初 red01/red02 执行时只有通知文件与指定基线有差异，见 baseline-diff.patch；它已被 loader 覆盖。

green02-ui 的失败为重复截图标签 EEXIST；no-panel01-ui 的失败为将 400px 窄列错判成宽裕空间。两个对应脚本快照 ui-probe-green02.mjs / ui-probe-no-panel01.mjs 与失败输出保留。宽裕空间检查仍在正常 1600×1050 无面板及中文场景运行，要求三个次要元素均可见；未取消此检查。

相关套件与全 workspace 检查的 exact argv / exit 在 related-tests03、browser-tests03、typecheck03、lint03、fmt-check03 的 *-command.json，原样输出在同名 .log。浏览器选中 5 个测试通过，208 个按过滤条件未跑；lint 有 877 warnings、0 errors。原始日志的空白不清洗。没有启动耗时对照、桌面 rebuild、产品真实模型调用或发布。

## 工具栏反事实与一次审查

acceptance-review-raw.txt 是唯一一次审查的原始 FAIL，元数据见 acceptance-review-metadata.json。修复后的三个矩阵不会把该 FAIL 升级为 PASS。reviewed-candidate-binding.json 与 fork-reviewed-diff.patch 保留审查候选；candidate-binding.json 绑定交付修复版。

重放工具栏坏版本：启动最后加 reviewed，probe 最后也加 reviewed，并使用新 label。Vite 只加载保存的 reviewed-ChatView.tsx（9654e1c63），其他源码与该版本相同；不换共享源码。toolbar-counterfactual02-ui-command.json 是原始 exact 命令，exit 1，只有三条 toolbar buttons overlap，排除了屏幕阅读器标签和空 Range 的测试误报。修复后的 toolbar-final01-ui / toolbar-no-panel01-ui / toolbar-many01-ui 用同一版 oracle 全部 exit 0。

当前 oracle 记录实际绘制的文字、工具栏按钮的 pair 面积与完整边界；clip-path: inset(50%) 的既有屏幕阅读器标签单独保留在原始 JSON，空 span 不当作文字。脚本快照 ui-probe-reviewed.mjs、ui-probe-before-empty-range-filter.mjs 及所有误报/真实失败均保留。
