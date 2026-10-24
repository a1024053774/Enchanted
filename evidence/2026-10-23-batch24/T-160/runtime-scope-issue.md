T-160 的同一次交付恢复需补一个任务卡未列出的运行时文件：workbench/src/panes.ts。

源码诊断（尚未进行新的真实 Codex 复现）：Claude Stop 完成时（约 1522 行）会把会话置为 idle；Codex Stop 完成时（约 1555 行）若 pane.failed 已设则置为 unknown。daemon.ts 解析 reviewer 输出失败后会设置 pane.failed=invalid_review_result。readThread（约 1696 行）将 state 非 idle 解释为 running，stopThread（约 1708 行）要求 idle。因此只改 core.ts 的恢复门禁可以恢复 Claude，却无法核对并回收完成 Stop 的 Codex reviewer；放过所有 unknown 也不正确。

建议授权 panes.ts 的最小修改：仅当失败为 reviewer 协议解析失败、匹配 Stop 的转交和信任检查已全部完成时，记录这一个原生回合已结束的 idle 事实。pane.failed 仍保留，其他 unknown/permission/转交错误仍拒绝；实际停止归档和新开审查仍只经 core.ts 唯一门禁。补本票独立回归，不能将该静态诊断当作真实 Codex 验收。

当前继续准备已授权的 Claude 恢复、绿态/变异脚本与真实 haiku 3 次脚本，不修改 panes.ts，等待范围裁定。
