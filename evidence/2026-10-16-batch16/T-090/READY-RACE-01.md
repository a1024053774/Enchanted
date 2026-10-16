# 首轮绿态的 ready 竞态诊断

2026-10-16。根因定位 PASS；候选业务验收仍为 INCOMPLETE。

目标：区分真实启动失败与测试 ready 发布竞态，保留失败现场并修正测试工具。非目标：不改 `daemon.ts`、门禁语义、业务断言、超时或验收协议，不盲目重跑失败用例。

## 已观察到的证据

原件 `/Volumes/WD-Elements/a2a-evidence/2026-10-16-batch16/T-090/green-regression-01/focused/`，候选 `0bcc5ab66deaa5cae69b17672ebb2d2ae3d641c2`。`unittest.txt` 显示 setUp 在 `daemon_acceptance_adapter.py:242` 解析已存在的 ready 文件时发生 JSONDecodeError（line 1 column 1），业务方法未执行。以下读取来自其 `fixtures.tar.gz`，未打开停机 SQLite。

- `daemon-lifecycle.jsonl`：15:31:34.871402Z 启动受控宿主 PID 46589；15:31:43.498879Z 保存实时状态读回；15:31:46.254960Z 确认宿主退出，`process_exit=0`；随后记录 `daemon_stopped`。
- 宿主 `host-01.stderr` 和 `host-01.stdout` 都为空。
- 状态读回的 `orchestration_events` seq 1 在 15:31:40.778Z 记录 `daemon_started`，PID=46589；说明已完成 `serve` 启动，不只是看到了一个遗留 ready 文件。
- 归档后的 `host-01.ready.json` 是完整 JSON，PID=46589，root、gate、argv 与启动记录一致。
- `stop_daemon()` 在停止前通过真实 CLI 的 `daemon_status`、PID 文件、ps 和被持有的 Popen 对象核对宿主身份，之后发送 `daemon_stop`，确认退出 0。没有启动失败或 daemon 异常退出的证据。
- `daemon_acceptance_host.ts` 在 `await serve(...)` 后用 `writeFileSync(final, ..., {flag:"wx"})` 发布 ready；读取方只等 `ready.exists()`，随后立即 `json.loads`，存在从创建空文件到写完内容之间的窗口。
- T-090 后续 T-082 场景使用的 `quality_chain_host.ts` 有相同直接写入方式，故在本次相关范围内一起修正。其他未运行宿主若有同模式，交主控另行分配，不顺手扩展。

推断：本次异常符合消费者观察到 writer 已创建、尚未写完的 ready 文件。没有捕获瞬时读取字节，不能断言空文件或其他部分内容是哪一种。确定性探针把 writer 暂停在真实文件已打开、内容未写入的窗口，直接验证 ready 名称是否提前可见，结果见下文。

`daemon.ts` 只提供 `serve` 和自己的 PID/IPC 通知；这个 ready JSON 属于测试宿主。因此可在既有 `workbench/tests/` 边界内修复，无需改范围外产品文件。

source checkout 位于外置盘是本 worker 的脚本错误；项目规则要求源码 checkout 留内置盘，后续改到 `/tmp`。但失败的 ready、state 和运行夹具本来就在 `/private/tmp/s3f-lpmafq64/`，没有对照证据证明外置盘 I/O 导致该竞态，不把相关性写成原因。旧目录保持原样。

## 最小修法与验证条件

在 ready 的同目录以独占方式写完临时文件，再用硬链接一次性发布最终名称；最终文件预先存在时必须失败且不改写旧内容。失败保留临时文件，不回退到非原子写入。两个实际调用方共用同一测试工具函数，不增加读重试或超时。

该文件系统小步骤需隔离验证，失败方式先列出：最终名称在内容写完前可见；完成后内容不全或身份值串用；已有 ready 被覆盖；临时文件创建/写入/发布失败被当作成功；已知坏实现仍能通过。探针使用真实 Node 子进程与真实文件系统，暂停底层写入并让外部观察者检查最终名称，再检查完整 JSON 和冲突保留。预期值来自独立输入；对照坏实现恢复原直接写 final 的行为，必须在“提前可见”断言失败，不能把进程或导入错误当作检出。

主控后续用新 label 完整重跑，仍从 focused 开始，再跑 8/9/18、T-082 和反例/变异。原失败证据不得覆盖。

## 确定性文件系统探针

worker 在沙箱内运行普通文件系统测试（不是受控后台/PTY 宿主）：

```sh
node workbench/tests/test_ready_file.ts /Users/luckye/Documents/Code/a2a-wt-t090 /tmp/t090-ready-local-01
```

退出码 0，五项 PASS。原直接写 final 的已知坏实现：暂停时 final 已存在，完整写入及正常退出后，仍被同一“完整内容之前 final 不可见”条件判为 contract_failure。候选实现：暂停时 final 不存在，发布后完整 JSON 与独立 nonce 输入一致。另验证 pending 清理、已有 ready 内容不变且明确 EEXIST、创建 pending 失败时不发布 final 并保留现场。

摘要 `ready-file-local-01.json`；原报告 `/private/tmp/t090-ready-local-01/run.json`，夹具 `/private/tmp/t090-ready-feirgO`。两者均保留，交主控下次宿主命令按 T-088 归档；主控命令还会归档已确认停止的旧失败夹具 `/private/tmp/s3f-lpmafq64`。未覆盖旧外置盘目录。

此探针证明文件系统发布步骤和已知坏实现检出，不代替实际宿主与业务整组复验。后续绿态阶段会重新运行同一探针，原始报告直接进外置盘。
