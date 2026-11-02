审查对象：HEAD `635eb1bbc7fbfb68142ea253680047ff73b383d9` 加 `candidate.diff`，以及新增 T-239 测试。未修改文件，未启动会写入环境的端到端测试。

1. **非阻塞：根因成立，修在显示层合适。**  
   [panes.ts:380](/Users/luckye/Documents/Code/a2a/workbench/src/panes.ts:380) 在 paint 时重置后台解码器，并向原始记录追加 `ESC c`，因此记录确实可能出现 `e4 b8 1b 63`。只读探针确认：严格解码抛出 `TypeError`，候选解码得到 `�` 后继续处理重置序列。  
   [renderer.tsx:307](/Users/luckye/Documents/Code/a2a/workbench/app/renderer.tsx:307) 保留流式解码、只取消 `fatal`，是符合原始字节记录契约的最小修复。后台过滤半字符需要缓冲或改写记录，会影响实时性和字节偏移；给历史窗格提供 paint 偏移可以跳过坏前缀，但不能解决程序直接打印 `0xff`，也不能覆盖已有历史记录。

2. **非阻塞：偏移检查仍有效，但不能证明字符边界正确。**  
   [renderer.tsx:389](/Users/luckye/Documents/Code/a2a/workbench/app/renderer.tsx:389) 仍检查 launch、请求起点、返回长度、总长度单调性及越界；[panes.ts:1005](/Users/luckye/Documents/Code/a2a/workbench/src/panes.ts:1005) 按实际文件位置读取。普通缺块、错序和缩短仍会报错。  
   但若读取起点本身错误，回包元数据又保持自洽，例如从“中”的第二个字节开始，检查仍通过，界面显示替换字符；只读探针已确认这一点。[renderer.tsx:380](/Users/luckye/Documents/Code/a2a/workbench/app/renderer.tsx:380) 对 paint 偏移也只检查整数和不倒退。因此不能宣称“偏移错位全部有检查兜住”。这不阻塞本修复：原来的严格解码也不能发现跳过完整字符或 ASCII 的偏移错误。

3. **非阻塞：测试抓住了对应坏实现，有一处断言可加强。**  
   [测试:175](/Users/luckye/Documents/Code/a2a/workbench/tests/test_t239_pane_invalid_utf8_e2e.py:175) 先确认记录末尾是半字符，再确认重启后存在 `e4 b8 1b 63`；随后结束夹具终端，核对 `history_only_pane`。结合界面游标初始化为 0、历史窗格不可写的路径，场景 A 确实从头回放，没有经 resize 跳过坏字节。  
   修前及 `fatal` 变异均失败于 `replayed_history_no_decode_error`；`no-stream` 变异失败于 `split_characters_decoded_intact`，观察到一个替换字符，均为对应业务断言失败。三次绿态覆盖历史回放、实时无效字节及正常中文跨块解码。  
   小缺口是 [测试:210](/Users/luckye/Documents/Code/a2a/workbench/tests/test_t239_pane_invalid_utf8_e2e.py:210) 最终只断言 A2；`shown()` 超时后返回 buffer，因此 A1 缺失仍可能通过。建议最终断言同时要求 A1、A2。

4. **非阻塞：另有严格解码输出的路径，应保留其不同用途。**  
   [claudeNotice.ts:17](/Users/luckye/Documents/Code/a2a/workbench/src/claudeNotice.ts:17) 仍严格解码窗格输出，调用点是 [panes.ts:1946](/Users/luckye/Documents/Code/a2a/workbench/src/panes.ts:1946) 的启动安全提示核对。无效或截断字节会使按键授权失败；这是安全核对路径，本候选没有解决它，也不应顺带放宽。它不适用于本次历史 shell 回放场景。  
   Electron 主进程透传 base64，门禁 CLI 输出 JSON；`nativeLink` 读取原始记录时使用 Node 的容错 UTF-8 解码。复盘导入读取报告及建议文件，不严格解码 `pty.raw`。在这些入口中未发现另一条会导致同类历史窗格停读的严格解码路径。

5. **非阻塞：文件末尾的半字符仍不会显示替换字符。**  
   [renderer.tsx:393](/Users/luckye/Documents/Code/a2a/workbench/app/renderer.tsx:393) 始终使用 `stream: true`，到达记录末尾没有 flush。若已结束的历史恰好以半字符结尾、后面没有 `ESC c` 或其他字节，尾字节会一直留在解码器中。只读探针确认该行为。这是既有边界，不影响本次已复现故障，但“所有不完整 UTF-8 都显示 U+FFFD”的表述需要收窄。

证据方面，已核对红绿截图，并独立比较 T-212 保存的两组编号中文记录：分别为 474 行和 494 行，xterm 与 hc 顺序一致，xterm 中没有替换字符。未重新运行端到端测试；`run-all.log` 首次调用因证据文件已存在而拒绝运行，不能描述为整段脚本一次成功。项目状态检查仍报告 README stale，需由主控在收尾时处理。

**结论：PASS。无阻塞意见；通过范围限于本次 T-239 候选修复。**