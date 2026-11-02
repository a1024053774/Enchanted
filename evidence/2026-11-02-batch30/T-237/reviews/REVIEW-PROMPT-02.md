# T-237 只读审查请求（第 2 轮）

你是独立审查员，只读：不改任何文件，不运行会改动仓库或用户环境的命令，不 push。结论作为你的最后一条回复（会被保存为 `reviews/REVIEW-02.md`），中文。

## 背景

- Ticket：`.project-map/tickets/T-237-stale-retrospective-shows-running.md`。复盘的 CLI 退出、或后台重启后它的终端已不在，Reflect 页那一行仍一直显示“进行中”。
- 第 1 轮结论 NO_GO，意见见 `reviews/REVIEW-01.md`（5 条阻塞、若干非阻塞）。
- 第 2 轮候选（未提交，基于 HEAD `82e747f4a`）：`evidence/2026-11-02-batch30/T-237/r2/candidate.diff`。涉及 `workbench/src/daemon.ts`、`panes.ts`、`hc.ts`、`retrospective.ts`、`workbench/app/RetrospectiveSections.tsx`、`workbench/README.md`、`workbench/tests/scripted_claude.py`（`source_tree` 加 `copy`），新测试 `workbench/tests/test_t237_retrospective_end_e2e.py`。

## 第 2 轮怎么处理第 1 轮的阻塞意见

1. 未恢复 / 恢复失败的终端：`Panes.shellFront` 只在 `shell_closed` 有记录时判 `gone`；没有窗格（未恢复、`shell_exit_unconfirmed`）判 `unknown`；后台恢复期间（`recovering`）整轮不做结束判断。
   同时发现：core 随后台一起没了、重新启动后，旧代码 `hc.find` 对找不到的终端直接抛错，恢复永远走不到 shell PID 退出核对，终端只能是 unconfirmed；
   这一轮改为找不到或不再 live 都返回 null，由恢复的 PID 核对确认 shell 已退出后才写 `shell_closed`（`hc.ts`、`panes.ts` 恢复处注释）。
   请特别看这一改动是否会把仍在运行的终端误记为关闭（PID 复用、同地址不同 launch 标签的终端等）。
2. 作业控制关闭：前台判断改为“shell 所在终端的前台进程组（shell 行的 tpgid）里有 shell 以外的进程”→ program；除 shell 外没有进程 → prompt；只有其他组的进程 → unknown（`background_only`）。
3. 检查出错：查询失败返回 `unknown`（`process_query_failed`，带 `process_query` 诊断）；`retrospectives.noteEndCheck` 在进入 unknown 或原因改变时记 `end_check_unknown`，回到已知时记一条 `end_check_known`，不每分钟重复；Reflect 页在“进行中”后写明无法确认的原因。
   `shellFront` 自身只在 launch 记录不存在或不是 shell 时抛错（launch 记录不删除，复盘的 launch 总是 `startRetrospective` 建的 shell），所以 daemon 里不再为它包 catch：这种不变量被破坏时整轮检查失败、经已有的 `retrospective_tick_failed` 暴露。请判断这一取舍。
4. 重叠检查：`await` 之后同步再查该复盘仍未结束、未导入，才记录。
5. 界面验收：测试最后起真实 Electron（经 DevTools 协议）读 Reflect 页各行的 `data-run-state` 与文字；已结束后补写报告 → 已完成。

## 证据

`evidence/2026-11-02-batch30/T-237/r2/`：`green-1..3.json`（及截图 `green-*.png`）、`red-baseline.json`（修前 `82e747f4a`）、`red-<变异>.json`（11 个变异，各自对应的失败方式见测试文件 `MUTANTS` 注释）、`v1/`（移除 daemon 里一个不可达 catch 前的整套结果，含中途失败的 attempt-*.json）、回归 `reg-*.json/log`、`run-all.sh`、`run-all.log`。

## 请重点看

1. 第 1 轮 5 条阻塞是否真的解决，测试能否抓住对应的坏实现（看变异是否失败在对应检查上，而不是别处）。
2. `hc.find` 的改动对 T-212 恢复语义（“只有程序真的没了才走续接”）有无副作用。
3. `noteEndCheck` 的去重与优先级是否和 README、界面一致。
4. 测试里的故障注入（在源码副本里替换 `processSnapshot.py`、弄坏 E 终端凭据）是否只影响夹具；`pkill -f <夹具目录>` 是否只会杀本夹具的进程。
5. 有没有新的会把仍在运行的复盘误判结束、或让已结束的复盘一直“进行中”的情形。

每条意见标明：阻塞 / 非阻塞，给出文件与行号、失败场景。最后给结论：PASS（无阻塞意见）或 NO_GO。
