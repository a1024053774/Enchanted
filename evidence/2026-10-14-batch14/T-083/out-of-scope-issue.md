状态：INCOMPLETE（交执行主控判断；不阻塞 T-083）

`intent.md:98` 的 worker 配置仍为 `Fast service tier`；`.project-map/templates/task-card.md:18` 仍要求“worker 请求 Fast”。它们与 AGENTS.md、T-083 引用的用户决定及当前启动器默认策略不一致，可能让后续派发再次采用旧期望。

建议由有文档写入权限的主控核对并同步这两处；T-083 不改文档、地图或任务卡。此报告保存在本票允许的证据目录，未写入共享收件箱；`report-issue.sh` 交主控执行。
