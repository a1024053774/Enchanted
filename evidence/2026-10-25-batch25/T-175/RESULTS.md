# T-175 结果：终端中文、表格与 powerline 字形

## 状态：INCOMPLETE（待 agy 审查）

## 根因与改动

L02（中文字间多空隙、中文表格边框不齐、p10k 分隔符成方块）的根因是终端用 xterm 的 DOM 渲染器：它把一整段文字放进一个 span，按西文字宽调字距，宽字符和全角标点的实际字形宽度与两格不一致，行内位置逐字累积偏差；它也不自绘制表符和 powerline 字形，用户没装 Nerd 字体时就显示缺字方块。用户平时用的 Terminal.app（Herdr 跑在其中）按格子逐字摆放。

- 加 `@xterm/addon-webgl` 0.19.0：逐格绘制，制表符、色块和 powerline 分隔符由渲染器自绘（`customGlyphs` 默认开）。GPU 上下文丢失时按插件文档卸载，xterm 回到 DOM 渲染器。
- 加 `@xterm/addon-unicode11` 0.9.0 并启用 Unicode 11 宽度表（`allowProposedApi`），与 CLI 计算宽度的规则一致。两个插件与现有 `@xterm/addon-fit` 0.11.0 同批发布（2025-12-22），无运行依赖。
- 设置页新增“终端字体”：逗号分隔的回退列表，默认 `"SF Mono", Menlo, "PingFang SC", monospace`；回车或离开输入框即应用于本窗口所有终端并重新计算列数，存于本窗口（与“外观”同一方式），重启保留；可“恢复默认”。

## 验收

测试：`workbench/tests/test_t175_terminal_glyphs_e2e.py`，真实 Electron、后台、node-pty、zsh；终端里 `cat` 一个夹具文件（表格按夹具自己的宽度规则补空格：East Asian Wide/Fullwidth 记两格，与 xterm 无关），零模型调用；像素从 CDP 截图读取。

| 运行 | 结果 |
| --- | --- |
| `--revision 8f36d6495`（修前 main，`red-main-02.json`） | 红：表格右边框各行 x = 653/400/653/665/659/665/653（应同列）；U+E0B0 左右边缘填充都是 0.69（缺字方块）。单行纯中文结束位置正确（修前也过） |
| 修后 `green-01.json` | PASS 5/5：右边框 7 行同为 642；纯中文 24 格；E0B0 左缘实、右缘空（实心三角）；改成 Helvetica 后列数立即变少；改成自定义列表后重启窗口仍是该值 |

`red-main-01-first-check-only.json` 是改成“先记全部像素检查”之前的红态，只到第一项。`setup-error-01/`：测试环境问题（worktree 里新装的 node-pty 缺执行位、缺 Electron 二进制）和测试自身的行号偏移，均未到达断言，保留原样。

回归：WebGL 画在 canvas 上，终端文字不再出现在 DOM 的 `.xterm-rows`。`test_t145_mouse_reports_e2e.py` 原来从 DOM 等就绪行，改为从 PTY 记录等、再确认窗格可见，回归 PASS（`regression-t145-01.json`）。`test_t167_codex_start_e2e.py` 只把 DOM 屏幕尾部记作观察、不参与判定，今后该字段为空。

截图对照：`shots/red-glyphs.png`（边框断开、全角逗号后多空隙、分隔符成方块）、`shots/green-glyphs.png`。

复跑：`cd workbench/tests && python3 test_t175_terminal_glyphs_e2e.py --summary <新路径> [--revision <rev>]`

## 没做

- 没在用户真实的 p10k 提示符下复看（用户的 zsh 配置在其 HOME，测试用隔离 HOME）；分隔符与色块已覆盖。Nerd 图标（如分支图标 U+E0A0）仍取决于用户安装的字体，可在“终端字体”里加。
