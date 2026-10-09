失败现场归档（未重试）：

- 启动 argv：`python3 - <<'PY' ...`；脚本内实际首次启动 argv 为  
  `['/Users/luckye/Documents/Code/a2a/scripts/bun', 'run', '/Users/luckye/Documents/Code/a2a/evidence/2026-10-09-batch11/T-056/server-fixture-30.ts']`
- cwd：`/Users/luckye/Documents/Code/a2a`
- exit_code：工具结果未单独保留；未捕获 `FileNotFoundError`，Python 进程应为 `1`。
- stdout：无脚本输出。
- stderr：`FileNotFoundError: [Errno 2] No such file or directory: '/Users/luckye/Documents/Code/a2a/scripts/bun'`，调用栈为 `<stdin>` 第 24 行的 `subprocess.Popen`。

已创建现场：

- `tempfile.mkdtemp(prefix='a2a-t056-gap-audit-')` 创建的临时根目录；具体绝对路径未打印，未保留。
- 该根目录下已创建：`home/`、`codex/`、`claude/`、`repo/`、`server-1.log`。
- 服务未启动，因此未创建 `ready.json`、SQLite 状态库、控制请求/结果或 RPC 输出文件。
- 未修改候选仓库、既有证据或目标工作区。
