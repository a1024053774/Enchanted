# T-256 现场记录（2026-11-08）

读 `state.sqlite3` 的 `launch_records`，任务 `a2a+T-249-1`，attempt `6bab2eb9-0d63-4bb1-b325-f70fa6df2d2b`：

| 启动记录 | 角色 | CLI | 模型 | 强度 | 速度 |
| --- | --- | --- | --- | --- | --- |
| `f36d7d22-41a2-4819-ba48-36ebda96a99a` | worker | Codex | `gpt-6-astra` | `xhigh` | default |
| `60d51e63-8e38-40e9-be26-bec893fb5505` | reviewer | Codex | `gpt-6.1-sol` | `high` | default |

工作台没有保存过 `execution_settings_saved`（查询结果为空），所以审查员取的是出厂设置 `workbench/src/executionSettings.ts` 的 `codexFactory`。
