# 主控 #322：停机后 SQLite 复核失败与无信号收尾

状态：修复与纯检查 PASS；余步 dry-run/删除 INCOMPLETE，worker 未执行。主控已完成原清理的停止部分，不能重跑原清理脚本。

实际原件 `09b-a14-cleanup-01/result.json` 为 BLOCKED：daemon_stop exit 0，API 48453/48454 各一次 SIGTERM，九进程在原源码的退出断言处均已确认缺失，随后 `redactor.collect(owner)` 查询 SQLite 报 OperationalError('unable to open database file')。主控也独立确认九进程退出，root 保留。错误表明停机后读库依赖不成立；仅凭此 traceback 不进一步断定是主库、WAL、锁还是文件可见性触发。

修复发生在本次正式执行之后；before-cleanup-09b-a14.py 与 before-redact-a14-scene.py 是修改前源码字节副本，且与此前 file-check-03 的源码副本逐字一致。原 BLOCKED 结果、已签 approval、脱敏摘要和外置归档不改写。

精确行为改动：

1. 原停机前 `summary == redactor.collect(owner)` 保留，新增保存 pre_stop_summary 与 pre_stop_scene_matches_archive。
2. 原停机后 `redactor.collect(owner) == summary and redactor.verify_archive(archived) == summary` 改为 verify_archive_after_stop：只将 tar 的成员类型/字节与停机前摘要比较，不打开现场数据库。
3. 新增独立 finish 脚本，仅接受本次 #322 的固定 root、九 PID、签字、daemon_stop 成功与两次原 API 信号回执，以及这一次 SQLite 错误；两次只读 ps 必须确认全部缺失，socket/pid 文件不存在，再复核原外置归档和本地已归档摘要，才删固定 root。

finish 脚本没有 signal/kill/daemon_stop 调用，也不调用 collect/SQLite；只有 ps 子命令。若 PID 存在、回执/签字/归档不符、root 身份不符，BLOCKED，不执行其他恢复动作。slot 不动。正式命令与可选只读 dry-run 见上级 09B-A14-CLEANUP-FINISH-COMMAND.txt；输出均用新目录。

`09b-a15-file-check-04` 保留实际错误字符串，模拟停机后数据库不可用：旧表达式精确报同一 OperationalError；新 archive-only helper 在同一不可用数据库条件下通过；归档内容被改变仍拒绝。另校验真实已保存的 #322 回执、重复信号负例，以及 finish AST 中没有 signal/daemon/collect 调用。该检查没有访问 A-14 root、探测 PID 或删除文件，不替代主控实际收尾。

A-15 的纯文件、身份、脱敏、逐键观测与旧 nonce/M5 反例同批再次通过，所用修复源码已在测试开始前保存并在结束逐字核对。A-15 仍不启动；材料冻结只进行文件生成与 Git 提交。
