# T-239 结果（2026-11-02）

结论：**PASS**。候选：基于 HEAD `635eb1bbc` 的未提交改动（`candidate.diff` 为审查对象，`candidate-2.diff` 加上审查后的注释收窄与 README 一句）。

## 根因

项目终端的输出记录 `traces/<launch>/pty.raw` 是原样字节。终端输出停在半个 UTF-8 字符上时后台重启、接回终端，`Panes.attachShell` 的 paint 处理在记录里追加重绘的 `ESC c`，记录里就留下 `e4 b8 1b 63` 这样的字节。界面窗格用 `fatal: true` 的 TextDecoder 流式解码：终端还在时，打开窗格先让它重绘并跳到新偏移，不经过旧字节；终端已不在的历史窗格从偏移 0 回放，读到这里就抛 `TypeError` 并停止读取，顶部显示“窗格未连接”。程序直接打印无效字节（如 0xff）时，实时窗格同样抛错停住。

## 改了什么

`workbench/app/renderer.tsx` 的两处窗格解码器去掉 `fatal: true`：无效字节显示为替换字符 U+FFFD 并继续读取，与一般终端相同；流式解码不变，跨块的正常字符照常拼接。记录末尾的半个字符留在解码器里，等后续字节。`workbench/README.md` 加一句说明。新测试 `workbench/tests/test_t239_pane_invalid_utf8_e2e.py`。

## 证据（命令：`bash evidence/2026-11-02-batch30/T-239/run-all.sh`，仓库根目录）

| 项 | 结果 |
| --- | --- |
| `red-baseline.json/png`（修前 `635eb1bbc`） | 失败于 `replayed_history_no_decode_error`；截图与 Computer Use 报告的现象相同（解码错误 + “窗格未连接”） |
| `red-fatal.json`、`red-fatal-after-review.json` | 变异：恢复严格解码，失败于同一检查 |
| `red-no-stream.json` | 变异：去掉流式解码，失败于 `split_characters_decoded_intact`（出现替换字符） |
| `green-1..3.json/png`、`green-4-after-review.json` | PASS，各 7 项：触发字节确实存在、历史窗格从头回放、无解码错误、回放到实时末尾、实时无效字节不报错、之后的输出照常显示、跨块中文不坏 |
| `attempt-1-prompt-marker.json` | 测试自身第一次把提示符标记写错（zsh 的 `%` 转义），保留 |
| `reg-t212-screen/run.json` | T-212 回归 PASS：真实 Electron 接回窗格，中文编号历史与 hc 逐行一致，24 次布局变化后仍一致（终端原始字节与截图按“只存状态”规则已删） |
| `reviews/REVIEW-01.md` | GPT 只读审查 PASS，无阻塞；采纳两条非阻塞：最终断言同时要求 A1、A2，注释收窄为“记录中间的无效字节” |
| `../cu-t239/REPORT.md` | Codex `gpt-6.1-terra` Computer Use 在打包应用上复验 T-239 三个场景（只重启后台、连同 core 重启后的历史窗格、实时无效字节）都通过 |

## 已知边界

- 读取起点若落在字符中间而回包元数据自洽，界面会显示替换字符而不报错；原来的严格解码也发现不了跳过整字符或 ASCII 的偏移错误，偏移由 `start_offset`/`next_offset`/`total_bytes` 核对。
- `src/claudeNotice.ts` 的启动安全提示核对仍严格解码，这是按键授权的安全路径，按设计不放宽。
- Computer Use 用的包在审查后改动之前打出；审查后只改了注释、README 与测试断言，行为相同。
