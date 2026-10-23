# 任务卡 T-147（T-121 断言随裁定 B 更新）

先读 `evidence/2026-10-23-batch23/COMMON.md`、`.project-map/tickets/T-147-t121-assertion-after-decision-b.md`、`evidence/2026-10-23-batch23/merge-1/run-20261023T151510Z/NOTE.md`。

| 字段 | 内容 |
| --- | --- |
| 编号 | T-147-1 |
| 来源 | T-147 ready_rev 1（ready_by executor）；用户裁定见 ticket |
| 目标 | 只改 `workbench/tests/test_t121_role_request_e2e.py:515` 一处：关闭终端后该主控仍在 `sidebar_snapshot` agents 里、`state == 'ended'`；身份拒绝的检查保留。 |
| 非目标 | 产品代码；其他断言、检查名、超时；其他验收文件。 |
| 修改边界 | 允许：`workbench/tests/test_t121_role_request_e2e.py` 第 515 行附近（经用户授权）、`evidence/2026-10-23-batch23/T-147/**`。禁止其他一切。 |
| 验收文件（oracle_paths） | `workbench/tests/test_t121_role_request_e2e.py`（本卡授权的那一处除外） |
| 红态命令 | 起点 2e36efb7c6edccb59f543aff325a1cf141d463ac 上原测试失败 `sidebar_drops_closed_controller`；改后在 045e8cfb1（`--revision 045e8cfb1`，关闭主控会从侧栏消失的旧行为）新断言必须失败。 |
| 任务类型 | 缺陷修复（验收文件随裁定更新） |
| 复杂度 | XS |
| 执行器 | Codex `gpt-6.1-sol`，`model_reasoning_effort="high"`，`service_tier="default"` |
| 起点 | 2e36efb7c6edccb59f543aff325a1cf141d463ac（main） |
| 唯一写入者 | Herdr agent `b23-t147`，worktree `/Users/luckye/Documents/Code/a2a-wt-t147`，分支 `exec/t147` |

## 完成条件与交付

1. 改动 diff 只碰那一处；RESULTS.md 写前后对照。
2. RUN-OUTSIDE-01.sh：候选上 T-121 绿；`--revision 045e8cfb1` 新断言红（旧行为）；可选再加一个变异（侧栏把已关闭主控标 running）被拒。
3. `git add --sparse` 提交，交付时说 DELIVERED <提交号>。沙箱起不了 Electron 的部分由执行主控在沙箱外跑。
