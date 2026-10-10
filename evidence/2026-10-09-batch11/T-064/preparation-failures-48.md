# T-064 真实边界补证的准备失败

以下是工具回执摘录及定位说明，不冒充已保存的原始 stdout 文件。产品原始日志、配置回执、实际 API 请求和 SQLite 现场仍保留；每次换新 label，没有覆盖失败产物。执行 argv、工具 session 与退出值见 `real-run-receipts-48.json`。

| 执行 | 退出 | 失败位置与影响 |
| --- | --- | --- |
| claude-probe34 | 1 | `Fixture(root)` 先于 ready.json，FileNotFoundError；未启动产品或 CLI，未创建认证目录 |
| claude-probe35 | 1 | 设置 API 成功返回 roles/catalog/changes，没有 ok 字段；驱动误断言 `changed.get('ok')`，未启动 CLI |
| claude-probe36 | 1 | 用第二个 SQLite 连接读 live runtime journal，实际应用采用 exclusive 锁，驱动只得到 DatabaseError；已发生真实 CLI 的 checked raise 和 unchecked submit permission。停服务后从真实数据库另存最小探针记录，探针边界 PASS，驱动退出仍是 1 |
| claude-good37 | 1 | 改为精确只读 state.sqlite 后明确得到 `sqlite3.OperationalError: database is locked`；没有将锁等待改成实现 fallback。证据驱动改由应用的真实 SQL owner 导出 native journal |
| claude-good38 | 1 | 权限断言 PASS 后直接 reclaim，门禁按 run_blocked 拒绝运行中的会话。原拒绝保留，随后改为先结束 owned turn 再回收 |
| claude-good39 | 1 | 驱动发出的 decline 缺 lifecycleGeneration，被原编排门禁隔离；45 秒内 CLI 未结束，原始请求仍待批准。另一次补发命令时服务已清理，因此 control 超时；没有发送 accept 或 acceptForSession |

最终 `claude-good40` / `claude-bad41` 和 `codex-good44` / `codex-bad45` 驱动均退出 0；pending 请求保持未批准，以实际 native interruption 清理，再经 reclaim 回收。状态 NO_GO 的坏候选由不读取驱动 verdict 的同一 `provider-contract-46.py` 退出 1 拒绝，两个好候选退出 0。没有为这些驱动修复改动生产代码。

归档检查又发现首次 Codex 实际 native home 在外置盘；认证来源在 /tmp 不等于实际 CODEX_HOME 在 /tmp。保留、上报并修正夹具后，codex-good53/bad54 各再用一个 turn，累计 4/4；同一合同断言好候选退出 0、坏候选退出 1，完整驱动均退出 0。来源与实际 home 均删除。最后一次机械审计首次运行先检查了尚未生成的自身 JSON 链接，退出 1；改为成品生成后核对该链接，不涉及产品或合同断言。

其他准备回执：第一次用 Python stdin 起草 stop 说明遭 Non-UTF-8 SyntaxError，未创建文件；随后通过 UTF-8 patch 创建。首次 inbox 的 fork 绝对路径引用被“越出项目”检查拒绝，随后引用本项目证据文件成功。首次终态 SQL 查询假设 orchestration_events 有 thread_id，查询失败、未写成品；改为保存整个隔离实例的小型 journal 后成功。均为证据驱动/治理准备失败，不作为产品红态。

Claude 的 SDK 对 bypassPermissions 发出 canUseTool shadowed 警告；实际 synara override 后真实 canUseTool/request 与 MCP 结果已出现。保留警告，不用方法可用性代替工具边界。Claude 输入来自本机假 API；没有用户 Claude 凭据或真实 Claude 模型请求。
