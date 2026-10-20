T-110 / a1：写测试摘要时 shell 无法创建 heredoc 临时文件，报 no space left on device。df 显示内置盘 /System/Volumes/Data 为 100%，剩余约 116 MiB。已核对首轮 /private/tmp/t110-outside-01.json 所记 native/daemon 进程均退出且没有清理错误，仅移除该轮私有副本 /private/tmp/t110-native-ue2ucgj4/candidate/workbench/node_modules（约 206 MiB 可再生依赖），没有移除原始运行、日志、源码或失败结果。其后约剩 320 MiB。

当前源码 worktree 的依赖和其他任务未动。建议执行主控核对内置盘容量后再运行完整复验；本 worker 不清理其他任务或用户目录。空间问题不作为业务红态。
