# T-078 #187：09B 前置产品切片交接

已先保存修改前真实红态：两个 preset 共享六个角色路径，第三根被 `invalid_controller_turn_limit` 拒绝，证据 `09b-profile-red-02/results.json`。本轮未启动任何 CLI/API/目标。

产品切片已完成并局部 PASS：

- `claudeLaunch` 在同一 broker/state/repo 下按 `roles/<preset>/` 推导 HOME、config、tmp、shell、requests、hooks、user-data、debug；旧 root 共享路径不再创建或 fallback，state/repo 根校验保留。
- Claude hook signal 接受 1～6 根，7 根仍拒绝。
- P1 generator、launch continuation、settings 与 hook 读回已同步。
- 09B profile red→green、6 根预算反例、profile08/auth/role prompt/预算和单角色 slice1 relay22、permission3、entry6、empty17 均 PASS；模型、CLI、API、UI 均 0。

请以原启动身份运行：

```sh
sh /Users/luckye/Documents/Code/a2a-wt-t078/evidence/2026-10-11-batch13/T-078/commit-09b-pre.sh
```

脚本固定 HEAD `d63611ea24212922e62fd8c690ce923748d481c3`、task/session、暂存区和 allowlist；第一提交冻结产品与证据，第二提交冻结 source freeze、运行记录和 RESULTS。失败即停，不重试，不启动服务，不删除根或 slot。

下一段才实现共库双角色 fake API／逐阶段 driver／独立 oracle：使用实际登记完整正文、实际 stop/request/inbox ID 和全局 dispatch.seq；先取红再绿及反例，另交可执行 launch 包审阅。当前 09B/09C 实跑、独立 reviewer 与 launch 仍 INCOMPLETE／NO_GO。

T-078 09B-PRE READY
