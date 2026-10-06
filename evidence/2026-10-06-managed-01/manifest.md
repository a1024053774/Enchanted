# Run: managed-2026-10-06-01

状态：PASS（T-006 限定范围）。结论与原始记录索引见 [RESULTS.md](RESULTS.md)；原失败及初审记录保留。

## 起点与分工

- 项目：/Users/luckye/Documents/Code/a2a；规范与 fixture 基线 commit：8ce7c7e。
- T-005 已关闭：真实 Herdr API 与独立分页 oracle 已确认。
- T-006 实现：a2a-build，独占 coop.py / README.md。
- T-006 独立验收：a2a-check，独占 acceptance/test_coop_e2e.py。
- 只读观察：a2a-monitor，独占本目录 monitor-*。
- 主控：本会话；负责规范、现场原始记录、live_herdr.py、复核和本地提交。
- 实现/验收请求 gpt-6.1-sol xhigh Fast；monitor 请求 gpt-6.1-sol high。
  启动 argv 与 UI 可核对，服务端实际履行 tier 无法由终端 UI 独立证明。

## 已发生的现场异常

Herdr client 0.9.3、server 0.9.1，protocol 22 相容；server_binary_stale 仍为 true。
不重启用户 server。继承环境里的 w6:pQ 已过期，权威 live a2a pane 为 wF:p1。

第一轮三个新进程的 agent start 返回 idle，但后续 pane 显示 Codex 0.160.0 到
0.160.1 的更新过程并退出。没有任务产物，不能记作任务执行成功。
原始 start/prompt、agent_not_found、pane 输出均在 commands.jsonl。
第二次启动固定 check_for_update_on_startup=false（仅此次进程参数，中央主控管理该实验版本）。
首次出现当前项目目录信任界面；主控依据用户对该项目本地编辑执行的明确授权、已知文件清单，
只确认了本项目目录信任，没有扩大工具权限。之后读取真实任务输入界面才重新投递。
请求级失配不通过“重发直到成功”掩盖；两个启动轮次均保留。

## 证据边界

commands.jsonl 是主控记录器输出的 argv/时刻/exit/stdout/stderr；monitor-* 为独立采样。
build-red/check-* 是各自检查记录，不能代替最终固定版本验收。
live fixture 位于 .runtime，仍保留原始坏 starter；最终 live run 使用新隔离目录。
没有可靠性提升、模型记忆鲁棒性提升或成本收益的结论。

复现本地验收：python3 -B acceptance/test_coop_e2e.py。
复现真实入口：python3 -B acceptance/live_herdr.py --parent-pane LIVE_PANE --output NEW_OUTPUT_DIRECTORY。
两条命令都必须指向指定候选版本；当前已完成最终验收，完整复现参数及限制见 RESULTS.md。
