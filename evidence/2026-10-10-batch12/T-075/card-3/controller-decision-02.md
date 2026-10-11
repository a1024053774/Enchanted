# T-075-3 执行主控决定 02：Unix socket 被沙箱拒绝之后（2026-10-11）

## 我核对过的 outside-probe-01 结果
- `host`：PASS。后台确实脱离了调用者的进程组。
- 真实 Codex 用了 1 个主 turn（累计 1/10）。窗格这一段全部走通：派发登记、M3 注入、UserPromptSubmit 和 Stop 两个 hook 都收到、状态回到空闲、执行主控首次 release。
- 被测 Codex 在 workspace-write 沙箱里执行 CLI，被拒：`connect EPERM .../state/control.sock`。它只试了一次，没有重试，没有提交。
- 两个 hook 都连上了后台（hook_received 2）。说明 Codex 本身发起的 hook 不受这个沙箱限制；被拒的是模型在沙箱里运行的命令。这一点按 observed 记录。
- 探针脚本最后在 `source.backup(dest)` 处崩溃，报 `unable to open database file`，原因是之前已经把 state.sqlite3 拷到了同一个位置。这一崩溃导致隔离 CODEX_HOME 没有被删除。**执行主控已经删掉了 `/tmp/a2a-t0753-hz27kh8k/codex-home`**（之前确认过没有存活进程）。请修好这个探针缺陷：清理放进 finally，并且不管备份成功与否都要执行；备份不要覆盖已存在的文件。RESULTS 里要如实写这件事。

## 下一步（本卡继续，不停）
1. **只做探针，暂不进产品**：Codex 0.162.1 二进制里有 `network.allow_unix_sockets` 配置项，对应 seatbelt 规则 `(allow network-outbound (remote unix-socket (subpath ...)))`。在夹具里用每会话 `-c` 只放行后台的那一个 socket 路径，`network_access` 保持关闭，用新标签再跑一次可达性探针，最多 1 个真实 turn。需要核实三件事：
   - 这项配置单独设置能否生效，还是必须同时开启托管网络代理；
   - 生效之后，其他 socket 和网络是否仍然被拒（自己建一个夹具 socket 做对照）；
   - git 钩子在沙箱里运行时，能否同样连上后台。
   不生效或必须连带放宽其他限制时，如实报告，不要换别的办法。
2. **能用脚本做的部分照常推进**：后台入口上的反例、派发与状态、库表、尾注钩子（钩子只读环境变量能取到的事实；需要向后台查询的部分等第 1 项的结论）。
3. **不要把放行 socket 写进产品默认启动参数**。这项改动给受管 worker 增加了一项沙箱权限，执行主控已经交给构思主控请用户决定（选项：A 只放行后台 socket；B worker 在 worktree 里写交付请求文件，由不受沙箱限制的 Stop hook 转交后台；C 其他）。决定之前，产品代码里交付路径的这一段留空，用明确报错占位。
4. **补一个缺口**：`panes.ts:122` 写 `pty.raw` 失败时只设了 `pane.failed`，没有写事件。请补一条事件，比如 `trace_write_failed`；如果写事件也失败，按 daemon 里已有的 `event_write_failed` 方式处理。
5. 跑完第 1、2 项后，照旧回复 `T-075 OUTSIDE-SANDBOX READY`。真实 turn 累计上限仍是 10。
