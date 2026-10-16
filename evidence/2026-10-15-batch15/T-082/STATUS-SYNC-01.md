# T-082 独审 02：launch-policy 状态字段修复

状态：**INCOMPLETE，等待 OUTSIDE-13 绿态**。只处理主控 #58 的 P3；时间顺序待决项由上层处理，不改变验收条件。未改产品门禁或审计锚点，真实回合保持 2/4。

修前红态已在 `status-sync-01/` 保留：先逐字核对 OUTSIDE-12 的 `candidate-source.tar.gz` 中 runner 与修改前当前文件相同，再运行新增检查读取该次最终报告、stdout 及实际 exit 0。检查 exit 1，精确指出 `report.product_status` 和 `stdout.product_status` 均应为 PASS、实际为 INCOMPLETE。原报告和输出未修改。完整命令、退出码、归属及原始检查结果见 `red.command.json`、`red.stdout.json`。

修复：`status` 保持权威字段，在全部归档、源码变更和大文件检查完成后，统一将其值赋给 `product_status`，随后保存报告并打印摘要。成功和失败收尾均经过该处，不再分别维护两份状态。

`check_t076_phase_report.py` 从进程退出码确定应有状态，再读取最终 `run.json` 和 stdout；两个字段都必须与该状态一致。它不从报告自身推导应有退出码。

主控命令：

```sh
bash evidence/2026-10-15-batch15/T-082/OUTSIDE-COMMANDS-13.sh
```

新输出为 `outside-command-13-01/` 起递增，含三段：旧报告一致性检查按预期失败；修后 launch-policy 成功路径的报告/摘要/exit 一致；受控错误 Node 版本的前置失败路径报告/摘要/exit 一致。后者只检查失败收尾，不作为 default tier 的业务红态。

夹具在外置盘，正常停止后归档删除；请求目录依据停止前读回和 host_exit=0 清理。没有停止收据时保留现场，末尾打印输出路径及退出码。本次完整成功绿态待主控运行，不复用旧 PASS 代替修后结果。
