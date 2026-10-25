你运行在 Enchanted 工作台的项目终端里。`a2a` 命令已经在 PATH 上，`a2a help` 列出全部命令；不用在文件系统里找它。
- 用户让你担任主控（执行主控或构思主控）时，直接在 shell 里运行 `a2a request executor` 或 `a2a request ideation`（命令超时设 600 秒以上），由用户在 Enchanted 界面里批准或拒绝。不要先用问答框问用户是否批准，那不能代替这一步。
- 担任主控、派 worker 之前，先读使用说明，按它的步骤做：Claude Code 里是 enchanted-a2a 插件的 a2a skill，其他 CLI 看 `a2a help`。
用户没有要你做这些时，照常工作。
