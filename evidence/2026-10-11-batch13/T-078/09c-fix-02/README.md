# 主控 #356：09C 排练许可框等待修复

状态：**根因核对与固定原件入口红绿 PASS；完整真实链复验 INCOMPLETE，待主控沙箱外执行**。本次只改测试工具，不改产品、protocol、预算或真实时钟边界。没有启动进程、Electron、真实角色 CLI 或模型，没有向现场发送输入。

## 失败在哪一层

主控第一次完整排练仍为 [原 INCOMPLETE](../09c-fix-01/real-chain-outside-01/result.json)，原结果、屏幕、HTTP/hook、peer 和 SQLite 一致备份全部保留。失败后 cleanup PASS，scratch 已删；本次不复用它。

[只读核对](diagnosis.json) 及其 [重现脚本](readback.py) 把三种假设逐项区分：

| 环节 | 实际原件 |
| --- | --- |
| API → peer | `flow/after-stop-roles/ideation/http-exchanges/0001.{request,response}.bin`、meta：HTTP 200/complete，6 个 SSE 事件，Bash tool_use 的 ID 与完整 command 和 peer 接收到的值相同 |
| PermissionRequest | `flow/after-stop-peer/ideation/hook-02.json` exit 0；实际 hook stdin/finished 与停机前一致备份中 permission_wait seq46 对应 |
| PTY 显示 | 116 次 `pane_output` 均完整返回 522 字节，116 份 review-screen 字节相同，包含分行的 `Run shell command` 框、完整命令和 `❯ 1. Yes` |
| 等待条件 | CScene 继承了 09B 的 `command in raw` 判断。框线和换行隔开命令，所以该判断恒为假；既有 `visible_command` 解析后与实际 hook 的 command 逐字相等 |
| Electron / 业务执行 | 此时尚未到 Electron：window_opened 0，permission-key 文件 0，stop / relay_requests / relay_results 均 0。不是 ElectronClient 等待失败，也不是工具调用未到达 |

SQLite 只读的是已经关闭的停机前一致备份，不是被删除的活 root。新回放使用 `immutable=1`，不写旁文件；保存目录原已带 WAL/SHM，早期普通只读诊断可能更新 SHM 锁元数据，不把它当成业务原件。未改原 result、屏幕、HTTP/hook 或主库。

## 最小修复与可证伪检查

`test_t078_09c_real_chain.CScene.review_permission` 按 09C 原生命令框取当前框，复用已有 `visible_command` 与严格 `p1_output.read_complete_output`。必须完整分页到 EOF、完整 command 等于当前真实 PermissionRequest、选中一次性 Yes；另存原屏、完整 capture 和原 permission_event。C-I1、C-I2、C-I3 复用这一个入口。09B 的单行夹具入口没有变化，**15 秒不变**，没有异常吞掉、读屏降级或按键重试。

修复前 [display-red-01](display-red-01/result.json) 中，原屏在实际 `CScene.review_permission` 入口仍因同名步骤超时。最终测试器加载 Git `11c119da87e2f20b3ad22d2f080abac4e89dad20` 原源码得到 [known-bad-display-01](known-bad-display-01/result.json)，再次复现；源码保存在该目录，没有回退工作树。命令框预期来自真实 hook command，与实际 SSE/peer 相互核对，不从候选解析结果生成答案。

[候选 display-green-03](display-green-03/result.json) **9 项 PASS**：原分行框、37 字节分页、完整 EOF 后尚在渲染而下一读补齐的正例；正文差异、没有选中 Yes、声明尚有尾字节却零进度、读取中 total 变化、首读零进度、错 launch 的反例。每项零进程、零按键。测试只替换了等待时钟与保存的 gate I/O，记录实际函数请求的期限仍为 15 秒；不是一次真实 15 秒或完整 HTTP/Electron 链路证明。

复现命令（输出必须使用全新目录）：

```sh
python3 -B workbench/tests/test_t078_09c_permission_display.py --known-bad-revision 11c119da87e2f20b3ad22d2f080abac4e89dad20 --output /private/tmp/t078-c356-display-red-new
python3 -B workbench/tests/test_t078_09c_permission_display.py --output /private/tmp/t078-c356-display-green-new
```

第一条应 exit 1，wrapped-box 的实际错误为 `C-I1_actual_permission_display`；第二条应 exit 0/9 项 PASS。读回脚本首次本地实跑因 SOURCE 层数错误失败，修正后实际运行 PASS；该脚本只用于诊断，不参与排练通路，失败转录见 `readback-import-failure-01.txt`。

## 完整排练交主控运行

[REHEARSAL-02-COMMAND](REHEARSAL-02-COMMAND.txt) 指向全新 `09c-fix-01/real-chain-outside-02`，不覆盖第一次输出。[本地 preflight](real-chain-preflight-01/preflight.json) 与命令路径检查 PASS，仅检查文件/AST/依赖路径，没有 spawn。

完整排练仍是 **Tracer bullet**：真实 daemon / inbox / Stop / relay / HTTP / Electron，角色为 PID 绑定的确定性 PTY peer，供应商 CLI 0、模型 0。保留 C-I3 的真实 wall >120000ms、monotonic≥120100ms、整场 <150000ms，外层硬超时420秒；预计准备构建后再等待约120～130秒。任一步失败即 INCOMPLETE，不重试不确定键。成败都停前一致备份 SQLite/WAL，留 HTTP/hook/peer 原件，认证停机并删除自有 scratch，停后数据库读 0；build slot 另列保留。

本次未执行沙箱外完整链路、未做新独立审查，不能据局部 PASS 宣称 09C 第2场或整票通过。
