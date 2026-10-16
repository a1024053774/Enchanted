# 第五轮编排失败与进程来源核对

2026-10-16。整体 INCOMPLETE：两条失败的事件链已核对；尖峰负载的具体责任进程尚不能从既有资料确定。没有修改 acceptance、产品、测试期限或重试策略。

本轮候选 `a74adeddc5494474472560a150f5ac33ab4a502e`。ready、focused、coop 8、recovery 9 通过；run 18 为 16 通过、1 failure、1 error、0 skip，后续组未运行。原件 `/Volumes/WD-Elements/a2a-evidence/2026-10-16-batch16/T-090/green-regression-05/run/`，紧凑读回 `run-observed-05.json`。

## 两条失败与 worker_boundary 无关的现有证据

`test_transient_tool_activity_keeps_same_thread_owner`：自己的 run `84c19199-2373-44c7-80b0-bb1049036103` 以 wait_seconds=8 运行，于 18:24:52.830Z 以 run_deadline 结束，持久 phase=verifying。该 phase 是最后保存的 run 阶段，不代表 review 尚未创建：review_requested 已在 18:24:51.829Z 绑定实际 worker HEAD／原分支／空 status，随后后台已启动审查。review_result 在 18:24:56.923Z 入库，review_reclaimed 在 18:24:59.401Z，显式 integrated 在 18:25:04.390Z。最后 task accepted、review passed，但 attempt reclaimed=false、cleanup=null；没有自动 reclaim 或 attempt ref 创建命令。因此 ref 缺失仍是自己的 run 先 deadline、随后显式集成却未自动回收的连带现象，不能当作 ref 已创建后丢失。

该场景的 helper-joins 在独立线程夹具中只给 read 响应增加 `active_tools=["transient-shell-command"]`；它不会真的启动一个 shell/tool 子进程。审查结果与回收均成功，保存事件没有 review_lifecycle_failed、review_protocol_failed 或 review_worker_workspace_changed。

`test_unknown_identity_cannot_succeed_or_close_replaced_worktree`：原 error 为 5 秒 prompt 观察窗口超时，后续自己的 run `864e6350-2e80-4df6-bd6a-e0cf146c629f` 在 waiting_submit 以 identity_conflict 暂停。该错误码必须如实列出：它来自原负例主动把 workspace 改为 `/unknown/replaced-worktree` 的 identity-changed 场景，不是 worker_boundary 拒收。candidate 仍为空，没有 verify 或 review，也没有 worker_boundary 快照。不能把预期身份反例的处理当作 T-090 审查边界回归；原方法仍为 error，不能补称反例验收通过。

## 测试是否并发启动大量 daemon／PTY

只读查阅本轮 artifacts、commands、边界日志、Git router 与 quality driver 日志，结果见 `run-process-design-05.json`：

- runner 使用普通 unittest.TestSuite，逐方法执行，没有测试线程池或跨方法并行启动。18 个真实 daemon 的 started～confirmed_exited 区间不重叠，已记录的同时存活 daemon 峰值为 1，18 个均退出 0。
- 部分原方法有意在一个 daemon 内保留一个异步 run 客户端，再用另一个 CLI 测 operation_busy／重复 run 或读取状态；这属于方法内并发，不等于 18 方法并行。原清理会等待或处理本方法持有的客户端，再结束该 daemon。
- 测试宿主在调用 serve 前安装 installControlledPTY，替换该宿主进程内的 node-pty.spawn，并替换 reviewer 的 processInfo；spawn 只返回内存 terminal、写合成原生记录和审计，不执行真实 zsh/Codex/PTY。9 条 stub spawn 审计不能当成 9 个真实 PTY 进程。worker 原生线程服务也是 Python 夹具，不运行模型。没有 tsx 启动路径，Node 26.5 直接运行 TypeScript。
- 但测试自身确有频繁的真实 fork/exec：本组 commands 记录 722 次调用，含 389 条 fixture Git、291 条随后 exec 为 Node 的 a2a_gates.py 客户端、36 条 ps；quality driver 另有 133 条 Node CLI 命令。原线程边界服务有 319 次 Python 调用（其中 read 229）；daemon Git router 记录 815 个不同 PID，它先运行 Python 后以同 PID exec Git。另有 oracle/pager 子进程，以上并非所有启动的总数。

这些是整组累计调用数，不是同时运行或同时消耗 CPU 的数量。可以排除“18 个测试并行／daemon 累积未收／真实 PTY 或模型群起”这几种解释，不能排除测试自身短进程启动、Node 运行时线程或 I/O 开销的贡献。

## 哪些进程把负载推到 58

主控 #16／#10 给出的摘要数值为本地 14:20=1.78、14:23=3.16、14:24=22.68、14:25=58.68。本轮 daemon 序列从 18:23:02Z 开始，前 15 个方法至 18:24:33Z 结束；transient 从 18:24:34Z～18:25:09Z，unknown-identity 从 18:25:09Z～18:25:25Z，确与尖峰窗口重叠。

但目前提供的原件没有该窗口按 PID 的 CPU／线程状态快照。生命周期、启动次数和 uptime 都不能事后确定谁占用 CPU，不能据此断言是测试自身，也不能继续断言是其他项目构建。本会话尝试只读 ps 格式探针时被沙箱以 Operation not permitted 拒绝；没有升级或绕过，宿主上实际 ps 格式和采样仍待验证。该当前探针即使成功也不能补出历史 CPU 用量。

主控已更正之前将 03／04 全归因于其他构建的判断：旧负载数值及“当时由主控转述其他项目”的来源记录保留，但具体责任进程均改为未确认。不能把这些转述当作已测得的唯一原因。原始负载日志待主控放入证据；本轮仅保留明确来源的 `load-report-05.json`。

## 三版本原 run 18 串行对照

```sh
python3 -B /Users/luckye/Documents/Code/a2a-wt-t090/evidence/2026-10-16-batch16/T-090/compare-recovery.py --suite run --sample-processes --label run-three-versions-01 --version main-before-T082 --version main-T082 --version T090
```

三个点固定为 main-before-T082 `271ac55d82d0e20067e03e2fa4a990e55ef7b434`、main-T082 `0e6c2b833f6da64243f71d670ea45bb9116fda4d`、本轮实际失败候选 T090 `a74adeddc5494474472560a150f5ac33ab4a502e`。T090 别名本次明确更新到 a74；历史 18dd 的对照原件不重写，且已核对二者 workbench/acceptance diff 为 0。

每个版本完整运行同 18 个原方法，共 54 次方法执行，版本之间串行；只覆盖方法选择／证据采集 runner，历史产品、验收、adapter、driver、宿主保持原字节。内部 2／3／5／8／12 秒等原期限均不动。18 方法组的外层诊断看守为 600 秒，与 run-host.py 现有值相同，不传给原方法；超时保留 PID、源码和原始输出，停止剩余版本，不发额外信号或重试。

父诊断进程另外约每 5 秒记录 ps/uptime：PID、PPID、进程组、状态、ps 报告的 %CPU／CPU time、进程名、是否观察到以当前测试 runner 为祖先。没有采集命令参数或环境变量，也不操作任何用户进程。监控本身的 PID 及每次采样用时均记录，短命进程可能漏采；不把“未采到”解释为不存在。该观测会有自身开销，结果不用于声称可靠性或性能改善。采样是新实验时的记录，不能回填 -05 或冒称当时已有独立监控。

实际运行前先在宿主验证 ps/uptime 可用，否则不启动测试。采样不完整时仍保存原测试结果，但诊断整体保持 INCOMPLETE，不替代 CPU 结论。原始快照与所有输出直接写本票外置盘的 `run-three-versions-01/`，源码仍在 /tmp；确认各 daemon 退出及 PID 消失，再运行下一版本。复制归档核对文件数、字节数后才清理本次目录。顶层 PASS 仅表示采集完整，product_status 始终 INCOMPLETE。
