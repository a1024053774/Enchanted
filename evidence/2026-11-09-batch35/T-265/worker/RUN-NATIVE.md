# T-265 真实交互 Codex 外部验证

由主控核对以下 argv 后，在 worker 沙箱外运行。没有安装 hook，不启动 Claude、额外 agent、后台、hc 或 Electron，不接触正式实例。

从本 attempt 的 worktree 执行一条命令：

```sh
python3 workbench/tests/test_t265_review_cli_e2e.py --codex /Users/luckye/.local/bin/codex --node /opt/homebrew/Cellar/node/26.5.0/bin/node --summary /Users/luckye/Documents/Code/a2a/evidence/2026-11-09-batch35/T-265/controller/native-materials-01.json
```

工作目录：`/Users/luckye/Library/Application Support/a2a-orchestrator/worktrees/a2a/T-265-1-a1`。已有 summary 或 artifacts 目录时拒绝覆盖；人工决定是否用新编号，不自动重试。

原生命令为 `codex --no-daemon --no-alt-screen -C <隔离候选副本> -a never --sandbox workspace-write -m gpt-6-astra`，配置强度 xhigh、service_tier default、关闭启动更新与模型切换提示、网络访问 true、`writable_roots=[]`，排除 `/tmp` 与 TMPDIR 自动写根。完整参数列表在 `native-plan.json`；每次实际 argv 和材料目录身份写入 `*-artifacts/{parent,candidate}-launch.json`。该探针不接 MCP、不加 hooks；不会证明 Stop/review_submit 生命周期。

脚本在 `/private/tmp/t265-cli-*` 下为父版和候选分别准备 CODEX_HOME，只复制用户 `~/.codex/auth.json`。配置只描述本次候选副本为 untrusted；只在看见 Folder access / Open restricted 时选择 1，不确认其他提示。仅写入 `git add`、`git commit` 两条 allow prefix_rule，探针本身没有 Git 写操作。HOME 也隔离；不改用户全局配置。

父版输入来自基线 `80a6304225cdd567737362dd045dabf97a625c56` 的真实 `createReview`，由原生 PTY bracketed paste 投递；必须观察到 1048576 字符上限拒绝，且没有原生 task_started。候选输入来自本 worktree 的同一方法，必须短于 4096 字符，并指向原字节完整材料。

候选真实 CLI 需要按材料内指令运行独立 Python 探针，读取全部 UTF-8 字节，回报字节数、字符数、55000 条 diff、50000 条 verification、头中尾三处随机标记；尝试以只写方式打开材料必须被沙箱拒绝，且不改变内容。脚本从输入独立计算期望，检查 CLI 原生 task_started/task_complete、工具调用记录、结果文件以及原材料字节。探针由 CLI 工具执行，宿主不执行它。最长每个实例 240 秒。

结果路径：`native-materials-01.json` 与旁边的 `native-materials-01-artifacts/`，后者含父版/候选实际启动记录、原生终端拒绝或输出、原生关键事件与工具结果。没有 auth.json 或完整 CODEX_HOME。把结果路径及结论答复到本 task 即可；worker 回读后补最终 RESULTS、提交并 submit。

清理在脚本 finally 中：只终止 forkpty 创建的自有进程组，记录目录/文件数/字节数后删除整个隔离夹具（含两份凭据）。不使用 ps 或按进程名称杀进程。如果脚本被外部强杀，先根据本次 summary/launch 路径核对自有子进程已经退出，再删除对应 `/private/tmp/t265-cli-*`；不得通配删除其他实例。保留所有终端与 JSON 文本证据。
