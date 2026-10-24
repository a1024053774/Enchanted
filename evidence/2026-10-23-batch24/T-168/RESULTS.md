# T-168 只读审查窗格文字重叠：结果

- 写入者：执行主控（Claude Code），按构思主控 answer 20261024T070244Z-ideation-answer-001 转述的用户决定：“让执行主控修,然后做完每个票让 agy 审查”。
- 基线：main `a808c1137`。真实 Electron、后台、门禁与受控 PTY；模型请求 0。
- 逐项结果见 `CHECKS.json`；运行目录已按 T-088 归档，清单见 `*.archive.json`。

## 根因

窗格的 `resize()` 总是把 xterm 拉伸到容器大小，但只有可写窗格才把新尺寸发给 PTY。只读窗格（审查员、历史 attempt）的 PTY 停在启动时的 160×45，xterm 却是容器大小（本机夹具 154×42，T-164 截图中更宽）。CLI 按 PTY 的列数计算相对重绘（上移若干行、清屏、重画），落在另一宽度的 xterm 上就会擦掉别的行或留下残行；回放与实时输出都一样。只读窗格没有输入凭据，也不应改变被查看程序的终端尺寸。

## 修改

- `workbench/src/panes.ts`：在线窗格的状态带上 PTY 实际尺寸 `size`。
- `workbench/app/renderer.tsx`：只读窗格的 xterm 用 PTY 的行列，不按容器适配；可写窗格不变。
- `workbench/app/style.css`：只读窗格可滚动，打开时停在最新的行。
- `workbench/README.md` 一句说明。

## 证据

| 项 | 命令 | 结果 |
| --- | --- | --- |
| 红态 | `test_t168_readonly_size_e2e.py`，修前源码 | red-3、red-4：视图 154 列、PTY 160 列，回放段与实时段都留下残行、行序断开（`red_reproduced=true`） |
| 红态前的测试脚本问题 | 同上 | red-1：`pane_output` 的 `max_bytes` 超限（KeyError），未到判定；red-2：样式行用了 `\n`，夹具 PTY 不转换换行，行成阶梯状，判定不成立；改为 `\r\n` 后重跑为 red-3/4。原记录保留 |
| 绿态 | 同上，修后 | green-1/2/3 PASS：视图 160×45 与 PTY 一致，两段文字不重叠，最新的行可见，PTY 尺寸未变，只读无焦点无错误 |
| 已知坏实现 | `--mutant readonly-fits-view` | 只在两段文字重叠上失败 |
| 已知坏实现 | `--mutant readonly-resizes-pty` | 文字仍重叠（只读窗格没有凭据，调 PTY 被拒），并出现输入错误 |
| 回归 | `RUN-REGRESSION-01.sh` | build、T-161、T-139/T-143 视图、T-143 焦点、T-139 布局与选择、T-091 IPC 全部 PASS |

注：red-3/4 运行时测试还没有“最新的行可见”这一项；该项在 green 与两个变异运行中都有。

## 未覆盖

- 已结束 attempt 的历史窗格（没有在线 PTY）没有尺寸可用，仍按容器适配；其回放按当时的 PTY 宽度产生，宽度不同仍可能错位。T-164 的现场是在线审查员，属于已修路径。
- 未用真实 Claude CLI 复验；受控 PTY 输出的是与 TUI 相同类型的相对重绘序列。

状态：待 agy 独立审查。
