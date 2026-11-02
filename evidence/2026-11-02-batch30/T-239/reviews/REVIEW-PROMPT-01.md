# T-239 只读审查请求（第 1 轮）

你是独立审查员，只读：不改任何文件，不运行会改动仓库或用户环境的命令，不 push。结论作为你的最后一条回复（会被保存为 `reviews/REVIEW-01.md`），中文。

## 背景

- Ticket：`.project-map/tickets/T-239-history-pane-textdecoder-error-after-restart.md`。后台重启后，历史窗格报 `TypeError: Failed to execute 'decode' on 'TextDecoder': The encoded data was not valid.` 并显示“窗格未连接”。
- 根因（主控查到）：项目终端的输出记录 `traces/<launch>/pty.raw` 是原样追加的字节。终端输出停在半个 UTF-8 字符上时后台重启、接回终端，`Panes.attachShell` 的 paint 处理在记录里追加 `ESC c`（`workbench/src/panes.ts` 约 380 行；后台自己的 StringDecoder 在此重置，注释写明旧流可能留有半个字符）。界面 `workbench/app/renderer.tsx` 的窗格读取用 `fatal: true` 的 TextDecoder 流式解码：
  终端还在时，打开窗格先让它重绘、跳到新 paint 的偏移并重置解码器，不经过旧字节；终端已不在的历史窗格从偏移 0 回放，读到“半个字符 + ESC c”就抛错、停止读取。程序直接打印无效字节（如 0xff）时，实时窗格同样抛错停住。
- 候选（未提交，基于 HEAD `635eb1bbc`）：`evidence/2026-11-02-batch30/T-239/candidate.diff`——两处解码器去掉 `fatal: true`，无效字节显示为 U+FFFD 并继续读取（与一般终端的做法相同）。新测试 `workbench/tests/test_t239_pane_invalid_utf8_e2e.py`。

## 证据

`evidence/2026-11-02-batch30/T-239/`：`red-baseline.json/png`（修前 `635eb1bbc`，失败于 `replayed_history_no_decode_error`，截图与 CU 报告的现象相同）、`red-fatal.json`、`red-no-stream.json`（两个变异）、`green-1..3.json/png`、`attempt-1-prompt-marker.json`（测试自身第一次写错提示符标记的失败尝试）、回归 `reg-t212-screen/run.json`（T-212 真实 Electron 中文历史逐行对照与 24 次布局变化，PASS）、`run-all.sh`、`run-all.log`。

## 请重点看

1. 根因判断是否成立；修在界面解码这一层是否合适，还是应在后台写记录时处理（例如不把半个字符写进记录、或给界面 paint 偏移）。比较两种做法的取舍，指出若只改界面会漏掉的情形。
2. 去掉 `fatal` 后是否会掩盖真正的问题：偏移错位（读取起点在字符中间）这类缺陷原先会被抛错暴露，现在是否还有别的检查兜住（看 `start_offset`/`next_offset`/`total_bytes` 的核对）。
3. 测试是否抓住对应坏实现：变异是否失败在对应检查上；场景 A 是否真的经过“半个字符 + ESC c”且从头回放（`history_only_pane`）。
4. 项目里其他读取 `pty.raw` 或窗格输出并严格解码的地方（Electron 主进程、门禁 CLI、复盘导入等）有无同样问题。

每条意见标明：阻塞 / 非阻塞，给出文件与行号、失败场景。最后给结论：PASS（无阻塞意见）或 NO_GO。
