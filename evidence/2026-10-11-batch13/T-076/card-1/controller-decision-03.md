# T-076-1 执行主控决定 03：outside-real-03 期限过短，批准最后一次真实运行（2026-10-11）

## 核对结果
- outside-real-03 观察到 1 个主 turn。run 使用 `--wait-seconds 100`，在 worker 实现夹具任务的过程中触发了 `run_deadline`，后台随即停止了 pane。事件中只有 turn_start_signal，没有 Stop；夹具仓库里也没有 worker 的提交。原因是夹具设定的期限远短于一个实现型回合实际需要的时间，属于夹具错误。
- 隔离 home 已删除，未留下残留进程。
- 真实回合累计 **1/3**。

## 批准
- 允许最后一次运行 real-two-turns，最多使用 2 个主 turn（第 2 个和第 3 个），用完即达到本卡上限 3。**之后不再追加。**
- 期限要按实际任务时长来定：`--wait-seconds` 至少 900；或者把夹具任务改小，例如只改一个文件、只要求一次提交。两种做法都要保证回执回合也能在期限内完成。
- 如果这次仍然没有走到“提交 → submit → 回执回合 → run/reclaim”的边界，就停下来，把尾注和多回合两项在 RESULTS 里如实标为 INCOMPLETE，不再要求更多回合。
- 预算记录中给 outside-real-03 追加一条核账：reserved=2，actual=1。
