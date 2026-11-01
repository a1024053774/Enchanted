# T-212 agy 第二轮审查：主控逐条核对（2026-10-31）

对照冻结的审查副本 `/Users/luckye/Documents/Code/a2a-review/T-212-r2` 和主控复跑原始输出核对。agy 的结论只在代码或原始输出能对上时采用。

## 两条发现

| 发现 | agy 定级 | 核对结果 | 处理 |
| --- | --- | --- | --- |
| 1a：`ResizeObserver` 触发 resize 时读取循环正在等 `pane_output`，读回的块越过重绘偏移，下一轮抛“重绘偏移无效” | 阻塞 | **不成立**。`candidate/workbench/app/renderer.tsx:386` 已有 `if (sizePending) continue;`，块读回后先丢弃，游标不前进。重绘偏移是后台写入 reset 时的 trace 大小，不会小于已读到的位置。agy 的修改建议 2 就是这一行。 | 不采用 |
| 1b：写块期间来了 resize，读到末尾时（`renderer.tsx:397-401`）仍会揭开窗格、结束“恢复中”，随后新的重绘在用户眼前重放 | 阻塞 | **成立，定为非阻塞**。只影响外观：新重绘仍从 reset 开始，内容正确。`resize()` 不唤醒 `delay()` 一事，最多多等 100 ms（`renderer.tsx:331-335`），不是缺陷。 | 第六轮修：有改尺寸请求在途时不揭开窗格 |
| 2a：`paint` 处理写 trace 失败会 `recordFailure(pane, "shell_trace_failed")`，但 `resizeShell` 仍返回旧偏移 | 非阻塞 | **描述不实**。候选里没有 `shell_trace_failed`，`panes.ts:340-343` 的 paint 处理也没有 try/catch。实际问题更大：`statSync`/`appendFileSync` 抛错会经 `hc.ts` 的 accept 回调一路抛到 socket `data` 处理，`socket.destroy` 掉整条 hc 连接，所有项目终端一起记为 `hc_connection_lost`。同文件 `data` 处理对同类错误只记该窗格失败。 | 第六轮修：paint 写 trace 失败只记该窗格失败；`resizeShell` 遇到失败时拒绝返回偏移 |
| 2b：`renderer.tsx:135` 的 `resize` 类型仍写 `Promise<void>` | 非阻塞 | **成立**。仓库没有 tsc 检查（`workbench/package.json` 无 typecheck 脚本），只是声明过时。 | 第六轮顺手改 |

## 引用核对

逐字对不上的引用（不采用）：

- “主控复跑 `r4-mismatched-01` 的 `xterm_size` 为 cols 123、rows 19”，以及“`--mismatched-screen` 下把容器改为 900px × 350px（第 463–464 行）”：实际是 159×49、cursorY 48（`controller/r4-mismatched-01/run.json`），测试第 463–464 行只断言 `rows < 120`，没有改容器尺寸。123×19 是 worker 的运行中缩小补测 `round4-live-resize-01` 的数值。
- 验收条目 2 写的 `pid: 27774`、`shell_pid: 27770`、472 行，以及 `pid: 28477`、474 行：实际 `r4-mismatched-01` 为 pid 39841、shell_pid 39838、491 行；`r4-screen-01` 为 502 行。
- 变异复跑写的 `hc_lines: 461`、`xterm_lines: 460`、缺 `编号-000460-中文`：实际是 503、502、缺 `编号-000501-中文`（`controller/r4-mutant-no-reattach-01/run.json`）。

核对属实的部分：

- 第一轮意见 1、3、4a、4b、5 的处理，以及主控未采用部分的理由。
- 根因说明，`hc.ts` 新旧 channel 切换中旧 DATA、CLOSE 都不进 trace，`lost`、`detach` 用 `Set` 去重。
- 证据边界扫描的数字：413 个文件、80 个状态根、50 个 token、负例两项。
- 用户 default core 进程 87319、87320、87407 前后不变。

## 验收条目

agy 把条目 2、4 判为 INCOMPLETE，理由是第五轮要改的三处和上面的 1b。主控同意这两条要等第五、六轮改完复验。其余条目 agy 判 PASS，主控以自己的复跑和 worker 原始输出为准，不以 agy 的数值为据。
