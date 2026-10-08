# 在线读取 thread 列的异常（2026-10-08）

跨项目成员和门禁项目不一致请求已分别返回 HTTP 400、`thread_project_mismatch` / `gate_project_mismatch`，完整输入输出先保存到 `cross-project-01.json`。

随后使用 Python sqlite3 只读连接隔离 Synara 的 `home/dev/state.sqlite` 并执行 `PRAGMA table_info(projection_threads)`，约 5 秒后返回 `sqlite3.OperationalError: database is locked`。原 traceback 留在 worker 工具输出；没有生成列快照，不补称为成功。该数据库由仍在运行的 Synara 持有；接下来只停本次启动的进程组后取列快照，再重启同一 home 并从 HTTP 回读归属，不绕过锁。
