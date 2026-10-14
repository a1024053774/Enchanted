# T-081 结果表

状态：NO_GO

| 案例 | 状态 | 预期 | 实际拒收码/结果 | 事件位置 | 工作分支是否不动 | 集成状态 |
| --- | --- | --- | --- | --- | --- | --- |
| 6a | 待裁定 |  |  |  | 未执行 | 未执行 |
| 7 | 待逐次批准 |  |  |  | 未执行 | 未执行 |
| probe_launch | NO_GO | 拒收伪造身份 | {'baseline': {'verify_error': None, 'state': 'reviewing', 'integrated': True}, 'candidate': {'verify_error': None, 'state': 'reviewing', 'integrated': True}} | /Users/luckye/Documents/Code/a2a-wt-t081/evidence/2026-10-14-batch14/T-081/full-01/probe_launch-pair.json observations.*.events | {'baseline': False, 'candidate': False} | {'baseline': 'accepted', 'candidate': 'accepted'} |

正例执行数：0
误拒绝数：None
原始事件与命令输出位置见 run.json 的 steps 与逐案 observation.json。
6a 待裁定；真实 Codex 回合为 0；未运行项不计通过。
