# T-258 新基线真实入口验证

**PASS（本次红绿场景）；整票 INCOMPLETE，独立审查与集成尚未完成。**

父版本为 `172b2f17566f923b2e0be8f7d21fc0b189b83fa2`，已含 T-259。候选为门禁受理的 `9d6883239d2757e8899d1894999837c1e0b61617`，task `a2a+T-258-1`、attempt `7043f6b6-95a1-403d-a487-4587e2c02d62`、spec/fence 4。旧候选的通过结论未计入本次结果。

两个运行使用同一份 T-258 驱动、实际 Codex 0.167.0、隔离后台/socket/PTY、隔离 CODEX_HOME 和本地 Responses 驱动。合法 MCP initialize 等待使原生身份晚于生产 120 秒期限出现，随后释放同一进程。没有修改生产期限、重发输入、伪造 rollout/Stop 或修改正式数据库。该场景验证运行时契约，不评估模型能力。

- 父版退出 1，`defect_reproduced=true`：原生完成后仍残留 native_session_unbound，交付与回收受阻。8 项业务断言均判红；前提满足，不是环境错误。
- 候选退出 0，8 项通过：工作中拒绝回收；submit 和 issue 各受理一次；错误 session 请求拒绝一次；请求不重复执行；真实回执 Stop 复用结果；原生完成后空闲；完成 attempt 可回收。
- 两个测试的自有后台、私有 core 和夹具清理均成功。正式后台和用户 core 未被测试停止；旧主控退出是用户另行授权的执行权交接，不是探针清理。

精确命令、版本、时间、原始启动 argv、断言及清理结果见 `e2e-parent-newbase-01-summary.json`、`e2e-candidate-newbase-01-summary.json`。完整输出在同目录去掉 `-summary` 的 JSON 中保留。父版驱动来自旧 review worktree，候选驱动来自当前 a4；两个驱动与指定历史源逐字节相同，产品输入则分别由 `--revision` 固定。

**Works**：真实入口对当前父版判红、对冻结候选判绿，8 项业务检查对应 T-258 原验收。

**No regression**：worker 在新基线取得 T-257 104 项、原生来源 13 项通过；门禁将重跑完成条件，并安排独立审查。未声称全套通过。

**Risk / undo**：本地 Responses 驱动不证明供应商模型稳定性；审批弹窗仍可能阻塞原生进程。候选尚未安装，当前安装版仍为 T-259 2083f72；保留旧包与全部失败摘要。
