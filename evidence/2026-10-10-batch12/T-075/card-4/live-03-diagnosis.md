# live-03 夹具诊断

状态：INCOMPLETE。原 `outside-live-03/` 保留；本轮真实回合 1，累计 2/4。主控 #43 允许下一轮最多再用 1 个，累计最多 3/4。

已证明：offline-trace PASS；首窗截图有真实 Codex TUI；关闭窗口后同一 shell／Codex PID 仍在；trace 从窗口退出后的 13,158 字节增长到重开前 17,358 字节；补回 `[0, 17358)` 与原 trace 完全相同。它覆盖关窗期间新增内容。后台重启尚未执行。

失败点有直接收据：`lifecycle/window-reopened-driver.jsonl` 的第二次 inspect 已读到 `offset=18661`，超过当时固定比对终点 17358，但 terminal 是 44 个换行，strip 后为空。`lifecycle.jsonl` 同时记录字节比对通过。因此本次不是尚未到达原比对终点；CLI 最后一条查询 `--offset 13158` 是独立差量读回，不能代表窗口游标。

xterm 6 源码给出更具体的解释：`AccessibilityManager._renderRows` 从 `CoreBrowserTerminal.buffer` 读取文字，后者直接返回 `buffers.active`；并未固定读取普通缓冲区。该 DOM 的 `TimeBasedDebouncer` 刷新阈值为 1000 ms，可能晚于 term.write 回调和窗口字节游标更新。日志中的新窗口在首次 load 后很快检查并关闭，符合文本层刷新滞后的机制。最终根因仍由修复后的真实入口复验确认，不把源码推断当作新的绿态。

修复限夹具：驱动收到后台原样返回的一批输出，若 next_offset 等于 total_bytes，就记下该次高水位 H，暂缓下一次输出请求；不截取、改写或补造字节，不停止后台或 PTY。客户端从这个时点开始等待 `窗口游标 == H` 且当前激活屏幕的文字非空；比对实际收到的全部 `[0,H)` 与 trace 后恢复取数。超时仍失败，不能用固定延时宣称补回完成。

离线夹具先在普通屏幕写一条专用文本，再进入备用屏幕写跨块中文，检查只读到备用屏幕；退出备用屏幕后须读到保存的普通屏幕。这验证无障碍文本跟随当前激活屏幕，而非仅凭一个非空字符串推断。新的高水位控制不进入产品 main、preload 或 renderer。

隔离检查先列失败方式：旧 offset 判据仍可能接受空文字；补回越过固定 H 时被误认为相等；等待时追着变化的 H 跑；发生断言或超时时没有释放取数屏障。用保存的失败 inspect 和明确标注的本地协议模拟检查这些控制条件；模拟不能证明 Electron 渲染，真实屏幕检查交主控。

命令：

```sh
python3 -B workbench/tests/test_electron_checkpoint.py --recorded evidence/2026-10-10-batch12/T-075/card-4/outside-live-03/lifecycle/window-reopened-driver.jsonl --known-bad /private/tmp/a2a4src-y43b2oof/source/workbench/tests/electron_client.py --output evidence/2026-10-10-batch12/T-075/card-4/checkpoint-client-01
```
