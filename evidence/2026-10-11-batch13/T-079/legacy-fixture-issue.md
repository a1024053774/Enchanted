# T-073 旧假 Herdr 需要适配新 launcher

观察：`acceptance/test_herdr_traceability_e2e.py:51–60` 的假 Herdr 只实现 split、run、agent start。split 没有保存 `--env`，也没有 `pane process-info` 分支；任何未实现的命令返回 2。`managed_env` 在第 97–101 行只读取旧 export 夹具文件。

影响：T-079 修复移除 export，并等待结构化 process-info。旧测试直接运行会被夹具拒绝，不能据此判断 launcher 的新行为。这是测试边界夹具过时，尚未运行该旧命令，没有将它算成产品红态。生产入口不保留旧路径。

本卡允许修改 `scripts/launch-worker`、新增 launcher 相关测试及本卡证据；没有允许改现有 T-073 测试。因此本 worker 未修改旧文件。新测试 `acceptance/test_launcher_shell_ready_e2e.py` 复用 T-073 的夹具 Git 仓库与独立尾注 oracle，提供新版假 Herdr；候选 6 项检查已通过，起点版本会因过早启动而失败。

建议：由执行主控确认是否将旧测试夹具适配纳入本票（只改其假 Herdr 和环境读取），或另交测试维护任务。此问题不阻塞本卡同样 10 次真实绿态探针；最终报告必须列出旧全套命令未运行的事实。
