# 任务：工作台启动器的进程身份核对与 locale 无关（T-046）

仓库是 a2a 项目的 Synara fork。请只修改 `a2a/scripts/workbench_runtime.py`（必要时 `a2a/scripts/workbench`），不要改其他文件。

问题：`process_identity()` 用 `ps -p PID -o lstart= -o command=` 的输出文本作为进程身份并写入 `workbench-process.json`；`read_owner()` 再取一次同样的文本做全文比较。`lstart` 的格式随调用者 locale 变化（例如中文 `五 10月/ 9 02:55:31 2026` 与英文 `Fri Oct  9 02:55:31 2026`），所以换一个 locale 运行 `workbench status` 或 `workbench stop` 会误报"工作台 PID 身份已改变"。

要求：
1. 身份核对与调用者 locale 无关。
2. 已存在的记录（字段 `pid`、`identity`，`identity` 是任一 locale 下 `ps -o lstart= -o command=` 的输出）必须仍被识别；正在运行的工作台就是用这种记录启动的。
3. 记录里的 PID 现在属于另一个进程（启动时间或命令不同）时，仍须拒绝（保持原有报错与非零退出），不能放宽成只看 PID。
4. PID 已不存在时报告未运行（保持原行为）。
5. 不要运行 `workbench start` 或 `stop`，不要读写 `~/Library/Application Support/a2a-workbench`；可用 `A2A_WORKBENCH_DATA_DIR` 指向临时目录、配合 `/bin/sleep` 进程自行验证 `workbench status`。不发起网络请求。

完成后在你的 worktree 中提交，再按下方的托管身份说明调用 a2a_submit 交付完整提交号。
